# SDD — Cycle-022: Investigation Template Infrastructure

**Cycle:** cycle-022
**Date:** 8 March 2026
**PRD:** grimoires/loa/prd_022.md
**Design input:** Cycle-018 ScenarioPackTemplate pattern, Signal Scanner domain filter table, live OSINT master registry (`backend/core/osint_registry.py` + source modules)

---

## 1. Architecture Overview

Cycle 022 promotes investigation templates from a frontend static array to a backend-owned, seeded, queryable model — the same pattern established by Scenario Pack templates in Cycle 018.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       CYCLE 022 ADDITIONS                          │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │ InvestigationTemplate│  │ Frontend Wire-Up    │                  │
│  │ Model + Seeder      │  │                     │                  │
│  │                     │  │ Wizard fetches API  │                  │
│  │ 4 genesis templates │  │ DomainFilter aligned│                  │
│  │ domain filter refs  │  │ template_id in      │                  │
│  │ source manifest     │  │ create payload      │                  │
│  │ policy metadata     │  │                     │                  │
│  └──────────┬──────────┘  └──────────┬──────────┘                  │
│             │                        │                              │
│  ┌──────────▼────────────────────────▼──────────────────────────┐  │
│  │              Existing Foundations From 017/018/019/021        │  │
│  │  DomainFilter enum | DOMAIN_FILTER_SOURCE_GROUPS             │  │
│  │  OSINT registry | Investigation model | Certificate builder  │  │
│  │  ScenarioPackTemplate pattern (model + seeder + API)         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.1 Data Flow

**Template consumption (wizard)**

```text
Wizard Step 2: Template Selection
  -> GET /api/v1/investigation-templates/ (frontend fetches)
  -> user selects template
  -> GET /api/v1/investigation-templates/{id} (frontend fetches detail)
  -> template defaults populate wizard state (domain filters, stop condition, inquiry class)
  -> user may override any default
  -> POST /api/v1/investigations/ includes template_id
```

**Investigation creation with template**

```text
POST /api/v1/investigations/ with template_id
  -> validate template_id exists and is ACTIVE
  -> apply template defaults for any field the user did not explicitly override
  -> resolve source IDs from live registry via DOMAIN_FILTER_SOURCE_GROUPS
  -> snapshot resolved sources into committed_sources_json (immutable)
  -> persist template_id on investigation record
  -> domain_filters_json uses backend DomainFilter enum values
  -> normal investigation creation flow continues
```

**Certificate provenance**

```text
Certificate builder reads investigation.template_id + investigation.committed_sources_json
  -> adds template_id, template_name, committed_sources to certificate metadata JSON
  -> this is a targeted addition of new keys to the existing metadata structure
  -> auditable chain: template -> committed sources (snapshot) -> domain filters -> evidence -> certificate
```

**Important:** The committed source manifest is a point-in-time snapshot frozen at investigation creation. If the OSINT registry or template defaults change later, the investigation record preserves exactly which sources were committed. This is the auditable anchor — not the mutable template row.

---

## 2. Sprint 0 — Schema + Migration + Contract Freeze

### 2.1 InvestigationTemplate Model

**New model in:** `backend/database/models.py`

```python
class InvestigationTemplate(Base):
    """Backend-owned investigation template — seeded, queryable, auditable."""
    __tablename__ = "investigation_templates"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inquiry_class: Mapped[str] = mapped_column(
        String(30), default="INVESTIGATIVE",
        comment="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY"
    )

    # Domain filter defaults — list of DomainFilter enum string values
    domain_filters_json: Mapped[list] = mapped_column(JSON, default=list)

    # Default source IDs from OSINT registry, pre-selected for this template
    default_sources_json: Mapped[list] = mapped_column(JSON, default=list)

    # Stop condition defaults
    default_stop_condition: Mapped[str] = mapped_column(
        String(30), default="OUTCOME_RESOLUTION",
        comment="OUTCOME_RESOLUTION | EVIDENCE_THRESHOLD | SPONSOR_DEFINED"
    )
    default_time_window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Policy-derived metadata
    requires_legal_review: Mapped[bool] = mapped_column(Boolean, default=False)
    min_corroboration_groups: Mapped[int] = mapped_column(Integer, default=2)

    # Lifecycle
    template_status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE",
        comment="ACTIVE | DRAFT"
    )
    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 2.2 Investigation Model Extension

Add `template_id` FK and `committed_sources_json` to the existing `Investigation` model:

```python
# On Investigation model — both nullable for backward compatibility
template_id: Mapped[Optional[str]] = mapped_column(
    String(100),
    ForeignKey("investigation_templates.id"),
    nullable=True,
    index=True,
)
template: Mapped[Optional["InvestigationTemplate"]] = relationship()

# Immutable snapshot of resolved source IDs at creation time
committed_sources_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
```

`committed_sources_json` is populated at investigation creation from the live OSINT registry. It is never updated after creation — it is the auditable record of which sources were committed when the investigation was opened.

### 2.3 Migration

Single Alembic migration:

1. Create `investigation_templates` table
2. Add `template_id` column to `investigations` table with FK constraint
3. Add `committed_sources_json` column to `investigations` table (JSON, nullable)
4. All operations are non-destructive — existing investigations remain valid with `template_id = NULL` and `committed_sources_json = NULL`

### 2.4 Response Schema Contract

Freeze before implementation:

```python
class InvestigationTemplateListItem(BaseModel):
    template_id: str
    name: str
    description: str | None
    inquiry_class: str
    template_status: str
    domain_filter_count: int
    requires_legal_review: bool

class InvestigationTemplateListResponse(BaseModel):
    templates: list[InvestigationTemplateListItem]
    total: int

class InvestigationTemplateDetail(BaseModel):
    template_id: str
    name: str
    description: str | None
    inquiry_class: str
    domain_filters: list[str]
    default_sources: list[str]
    default_stop_condition: str
    default_time_window_days: int | None
    requires_legal_review: bool
    min_corroboration_groups: int
    template_status: str
    is_seeded: bool
    created_at: datetime
```

---

## 3. Sprint 1 — Seeder + API Endpoints

### 3.1 InvestigationTemplateSeeder

**New file:** `backend/services/investigation_template_seeder.py`

Pattern: follows `scenario_template_seeder.py` exactly.

Responsibilities:

- define 4 genesis templates with full metadata
- derive `default_sources` from `DOMAIN_FILTER_SOURCE_GROUPS` mapping + live OSINT master registry (`backend/core/osint_registry.py` and source modules) — NOT from `backend/osint/sources.json` which is only a partial runtime subset (v0.4.0, 4 sources)
- derive `requires_legal_review` from source policy metadata in the live registry
- idempotent — skip existing templates on re-seed
- called during app startup or via management command

Genesis template definitions:

```python
INVESTIGATION_TEMPLATES = [
    {
        "id": "blank",
        "name": "Blank Investigation",
        "description": "Start with a neutral bounded-inquiry shell and select every constraint directly.",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": [],
        "default_stop_condition": "OUTCOME_RESOLUTION",
        "default_time_window_days": None,
        "min_corroboration_groups": 2,
    },
    {
        "id": "corporate_due_diligence",
        "name": "Corporate Due Diligence",
        "description": "Bias toward registries, filings, legal coverage, and identity/provenance checks.",
        "inquiry_class": "INSPECTION",
        "domain_filters": ["corporate_and_entity", "court_and_legal", "property_and_land"],
        "default_stop_condition": "EVIDENCE_THRESHOLD",
        "default_time_window_days": 90,
        "min_corroboration_groups": 3,
    },
    {
        "id": "market_event",
        "name": "Market Event Analysis",
        "description": "Prepare for event-driven evidence, counter-signals, and fast routing pressure.",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": ["finance_and_markets", "geopolitical_and_conflict"],
        "default_stop_condition": "OUTCOME_RESOLUTION",
        "default_time_window_days": 30,
        "min_corroboration_groups": 2,
    },
    {
        "id": "regulatory_action",
        "name": "Regulatory Action Tracking",
        "description": "Center the investigation on policy, regulatory filings, and formal status changes.",
        "inquiry_class": "SCRUTINY",
        "domain_filters": ["corporate_and_entity", "court_and_legal"],
        "default_stop_condition": "SPONSOR_DEFINED",
        "default_time_window_days": 180,
        "min_corroboration_groups": 2,
    },
]
```

Source derivation logic:

```python
def _derive_default_sources(domain_filters: list[str]) -> list[str]:
    """Map domain filters → source groups → source_ids from live OSINT master registry.

    Sources are resolved from backend/core/osint_registry.py (OSINTRegistry.scan_all()
    or equivalent source enumeration), NOT from backend/osint/sources.json which is
    only a partial runtime subset.
    """
    source_groups = set()
    for df in domain_filters:
        groups = DOMAIN_FILTER_SOURCE_GROUPS.get(DomainFilter(df), [])
        source_groups.update(groups)
    # Resolve source_ids from live master registry where source_group in source_groups
    registry = OSINTRegistry()
    all_sources = registry.get_all_sources()  # or equivalent enumeration method
    return [s.source_id for s in all_sources if s.source_group in source_groups]

def _derive_legal_review(source_ids: list[str]) -> bool:
    """True if any default source carries requires_legal_review in the live registry."""
    registry = OSINTRegistry()
    all_sources = registry.get_all_sources()
    return any(
        getattr(s, "requires_legal_review", False)
        for s in all_sources
        if s.source_id in source_ids
    )
```

**Note:** The exact method to enumerate sources from `OSINTRegistry` depends on the current API surface. The seeder should use whatever enumeration method the live registry exposes — the key constraint is that it must NOT fall back to `backend/osint/sources.json`.

### 3.2 API Router

**New file:** `backend/api/investigation_template_routes.py`

```python
templates_router = APIRouter(prefix="/api/v1/investigation-templates", tags=["investigation-templates"])

@templates_router.get("/", response_model=InvestigationTemplateListResponse)
async def list_investigation_templates(
    inquiry_class: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List investigation templates, optionally filtered."""

@templates_router.get("/{template_id}", response_model=InvestigationTemplateDetail)
async def get_investigation_template(
    template_id: str,
    db: Session = Depends(get_db),
):
    """Get full template detail."""
```

Registration: add `templates_router` to the FastAPI app alongside existing investigation routes.

---

## 4. Sprint 2 — Investigation Create Integration + Certificate Provenance

### 4.1 Create Endpoint Extension

Modify `POST /api/v1/investigations/` to accept optional `template_id`:

```python
class InvestigationCreateRequest(BaseModel):
    theatre_id: str | None = None
    construct_id: str | None = None
    inquiry_class: str | None = None
    template_id: str | None = None        # NEW
    domain_filters: list[str] | None = None
    stop_condition: str | None = None
    stop_config: dict | None = None
```

Behavior when `template_id` is provided:

1. Validate `template_id` exists in `investigation_templates` table and status is `ACTIVE`
2. If `inquiry_class` not explicitly provided → use template's `inquiry_class`
3. If `domain_filters` not explicitly provided → use template's `domain_filters_json`
4. If `stop_condition` not explicitly provided → use template's `default_stop_condition`
5. If `stop_config` not explicitly provided and template has `default_time_window_days` → populate `stop_config.time_window_days`
6. Resolve source IDs from the live OSINT registry for the final domain_filters (whether from template defaults or user overrides)
7. Snapshot the resolved source IDs into `committed_sources_json` on the investigation record — this is immutable after creation
8. Persist `template_id` on investigation record

If `template_id` is invalid or references a `DRAFT` template → return 400.

If `template_id` is `None` → existing behavior unchanged. `committed_sources_json` is still populated if `domain_filters` are provided (the snapshot is useful regardless of template usage). Backward compatible.

### 4.2 Domain Filter Value Alignment

The investigation record's `domain_filters_json` must store backend `DomainFilter` enum string values. No frontend-invented IDs should reach the database.

Validation at create time:

```python
VALID_DOMAIN_FILTERS = {df.value for df in DomainFilter}

for df in request.domain_filters:
    if df not in VALID_DOMAIN_FILTERS:
        raise HTTPException(400, f"Invalid domain filter: {df}")
```

### 4.3 Certificate Provenance

Extend the certificate builder's metadata assembly to include template and source provenance. The current certificate model stores metadata as a JSON blob — the addition is new keys in that JSON, not a table-level schema change.

```python
# In certificate metadata assembly
metadata = existing_metadata_assembly(...)

# Add template provenance (targeted key additions)
if investigation.template_id:
    metadata["template_id"] = investigation.template_id
    metadata["template_name"] = investigation.template.name if investigation.template else None

# Add committed source manifest (always, if present — useful with or without template)
if investigation.committed_sources_json:
    metadata["committed_sources"] = investigation.committed_sources_json
```

This is a targeted addition of new keys to the existing metadata JSON structure. Certificates for investigations without a template or committed sources remain unchanged — the keys are simply absent.

**Note:** If the certificate builder computes a canonical hash over the metadata, the hash payload must be updated to include these new keys. This is a deliberate change — the hash should reflect the committed provenance chain. The builder must sort/canonicalize the new keys consistently.

---

## 5. Sprint 3 — Frontend Wire-Up

### 5.1 Template API Client

**New file or extend:** `frontend/src/api/investigationTemplates.ts`

```typescript
export async function fetchInvestigationTemplates(params?: {
  inquiry_class?: string;
  status?: string;
}): Promise<InvestigationTemplateListResponse> { ... }

export async function fetchInvestigationTemplate(
  templateId: string
): Promise<InvestigationTemplateDetail> { ... }
```

### 5.2 Template Hook

**New file:** `frontend/src/hooks/useInvestigationTemplates.ts`

TanStack Query hook wrapping the template list endpoint. Stale time appropriate for seeded data (long — templates change rarely).

### 5.3 Wizard Step 2 Refactor

In `CreateInvestigationWizard.tsx`:

- Remove the static `TEMPLATES` array
- Replace with `useInvestigationTemplates()` hook call
- On template selection, fetch detail via `fetchInvestigationTemplate(id)`
- Populate wizard state from template defaults:
  - `inquiry_class` from template
  - `domain_filters` from template (using backend enum IDs)
  - `stop_condition` from template
  - `stop_config.time_window_days` from template if present
- User can still override any field after template selection

### 5.3.1 Signal-Origin Launch Context Preservation

The current wizard supports deterministic prefill from Signal Map, World Monitor, and theatre jump-offs via URL search params (`signal_category`, `signal_class`, `theatre_id`). The existing `inferTemplate()` function (lines 168–185) maps these params to template IDs using frontend heuristics.

This must not regress. The replacement:

- Replace `inferTemplate()` with a mapping table that resolves signal-origin params against the backend template list (fetched from the API, not hardcoded IDs)
- The mapping logic:
  - `signal_category` containing `regulatory` or `signal_class === 'regulatory_clearance'` → `regulatory_action` template
  - domain filters containing `finance_and_markets` → `market_event` template
  - domain filters containing `corporate_and_entity` or `court_and_legal` → `corporate_due_diligence` template
  - fallback → `blank` template
- The key difference: the mapping resolves against the fetched template list (matching by `template_id`), not against a hardcoded local array. If a template ID is not found in the API response (e.g., it was removed or set to DRAFT), the fallback is `blank`.
- Non-template fields (theatre_id, construct_id, signal-specific domain filters) continue to be populated directly from URL params — they are not affected by this change.

### 5.4 DomainFilterSelector Alignment

In `DomainFilterSelector.tsx`:

- Replace the 9 frontend-invented `DOMAIN_CATEGORIES` entries with entries derived from the backend `DomainFilter` enum values
- Map each backend enum value to an appropriate label, description, icon, and source examples
- The `DomainFilterId` type becomes the backend enum value set

Alignment mapping:

| Backend DomainFilter | Frontend label | Replaces |
|---------------------|---------------|----------|
| `corporate_and_entity` | Corporate & Entity | `corporate_registry` |
| `finance_and_markets` | Finance & Markets | `financial_filings` |
| `maritime` | Maritime | `supply_chain` (partial) |
| `airspace` | Airspace | (new) |
| `geopolitical_and_conflict` | Geopolitical & Conflict | `geopolitical` |
| `cyber_threat` | Cyber Threat | (new) |
| `property_and_land` | Property & Land | (was implicit) |
| `court_and_legal` | Court & Legal | `litigation` |
| `satellite_and_earth_observation` | Satellite & Earth Obs | `technical` (partial) |

The frontend categories `regulatory`, `media_news`, `social_sentiment` do not have backend DomainFilter equivalents. They are removed. If any of those concepts are needed, they should be proposed as backend `DomainFilter` additions in a future cycle.

### 5.5 Create Investigation Call

Update `createInvestigation()` in `frontend/src/api/investigation.ts`:

```typescript
export async function createInvestigation(body: {
  theatre_id?: string;
  construct_id?: string;
  inquiry_class?: string;
  template_id?: string;        // NEW
  domain_filters?: string[];
  stop_condition?: string;
  stop_config?: Record<string, unknown>;
}): Promise<InvestigationSummary> { ... }
```

### 5.6 Inquiry Class Alignment

The wizard's inquiry class options must match the backend enum:

```typescript
const INQUIRY_CLASSES = [
  { value: 'INVESTIGATIVE', label: 'Investigative' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'SCRUTINY', label: 'Scrutiny' },
  { value: 'SURVEY', label: 'Survey' },
  { value: 'COUNTERFACTUAL', label: 'Counterfactual' },
] as const;
```

When a template is selected, its inquiry class is pre-selected but can be overridden.

---

## 6. Test Strategy

Target categories:

- template model validation tests
- migration tests (table creation, FK constraint, committed_sources_json column)
- seeder idempotency tests
- seeder source derivation from live registry (not sources.json) tests
- seeder legal review derivation tests
- template list endpoint tests (filtering by inquiry_class and status)
- template detail endpoint tests
- investigation create with valid template_id
- investigation create with invalid template_id (400)
- investigation create with DRAFT template (400)
- template defaults applied correctly
- explicit user overrides take precedence over template defaults
- committed_sources_json snapshot populated at creation time
- committed_sources_json immutable after creation (not affected by later registry changes)
- certificate metadata includes template_id + template_name + committed_sources
- certificate hash includes provenance keys when present
- domain filter enum validation on create
- signal-origin prefill resolves correctly against backend template list
- backward compatibility: create without template_id still works

---

## 7. Out of Scope

- template CRUD (create/update/delete APIs)
- new investigation templates beyond the existing four
- new domain filters or source groups
- visual redesign of the wizard
- investigation toolset changes
- new OSINT source integrations
- changes to evidence, claims, drift, or stop-condition schemas
