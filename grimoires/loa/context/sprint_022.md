# Sprint Plan — Cycle-022: Investigation Template Infrastructure

**Cycle:** cycle-022
**Date:** 8 March 2026
**PRD:** grimoires/loa/prd_022.md
**SDD:** grimoires/loa/sdd_022.md
**Sprints:** 4 (0–3)
**Total new tests:** 21
**Builder:** Loa (backend + frontend wire-up)

---

## Sprint 0: Schema + Migration + Contract Freeze (4 tests)

Define the template model, extend the investigation model, and freeze response contracts before building.

### Task 0.1 — InvestigationTemplate Model

**Files:**
- `backend/database/models.py`

**Work:**
- Add `InvestigationTemplate` model with fields:
  - `id` (String PK)
  - `name` (String)
  - `description` (Text, nullable)
  - `inquiry_class` (String, default INVESTIGATIVE)
  - `domain_filters_json` (JSON, default list)
  - `default_sources_json` (JSON, default list)
  - `default_stop_condition` (String, default OUTCOME_RESOLUTION)
  - `default_time_window_days` (Integer, nullable)
  - `requires_legal_review` (Boolean, default False)
  - `min_corroboration_groups` (Integer, default 2)
  - `template_status` (String, default ACTIVE)
  - `is_seeded` (Boolean, default False)
  - `created_at` (DateTime)

**Acceptance criteria:**
- [ ] Model class defined in `models.py`
- [ ] All fields match SDD specification

### Task 0.2 — Investigation Model Extension

**Files:**
- `backend/database/models.py`

**Work:**
- Add `template_id` column to `Investigation` model:
  - `String(100)`, FK to `investigation_templates.id`, nullable, indexed
- Add `template` relationship
- Add `committed_sources_json` column:
  - `JSON`, nullable
  - Immutable snapshot of resolved source IDs at investigation creation time

**Acceptance criteria:**
- [ ] `template_id` is nullable (backward compatible)
- [ ] `committed_sources_json` is nullable (backward compatible)
- [ ] Relationship loads template when present

### Task 0.3 — Alembic Migration

**Files:**
- `backend/alembic/versions/c022_investigation_templates.py` (new)

**Work:**
- Create `investigation_templates` table
- Add `template_id` column to `investigations` table with FK constraint
- Add `committed_sources_json` column to `investigations` table (JSON, nullable)

**Acceptance criteria:**
- [ ] Migration applies cleanly on existing database
- [ ] Rollback drops columns and table without error

### Task 0.4 — Response Schema Contract

**Files:**
- `backend/schemas/investigation_template_schemas.py` (new)

**Work:**
- Define:
  - `InvestigationTemplateListItem`
  - `InvestigationTemplateListResponse`
  - `InvestigationTemplateDetail`
- Freeze before Sprint 1 implementation

**Acceptance criteria:**
- [ ] Schemas match SDD specification
- [ ] Schema validation tests pass

### Tests (4)

| # | Test | Type |
|---|------|------|
| 1 | InvestigationTemplate model instantiates with all required fields | Unit |
| 2 | Investigation model accepts nullable template_id and committed_sources_json | Unit |
| 3 | Migration applies and rolls back cleanly (template table + both investigation columns) | Migration |
| 4 | Response schemas validate against expected payloads | Unit |

---

## Sprint 1: Seeder + API Endpoints (5 tests)

Seed the genesis templates and expose them via read-only API.

### Task 1.1 — InvestigationTemplateSeeder

**Files:**
- `backend/services/investigation_template_seeder.py` (new)
- `backend/investigation/signal_scanner.py` (read — DomainFilter, DOMAIN_FILTER_SOURCE_GROUPS)
- `backend/core/osint_registry.py` (read — live OSINT master registry for source enumeration and policy metadata)

**Work:**
- Define 4 genesis templates (blank, corporate_due_diligence, market_event, regulatory_action)
- For each template:
  - Map `domain_filters` → source groups via `DOMAIN_FILTER_SOURCE_GROUPS`
  - Resolve `default_sources` from OSINT registry entries matching those source groups
  - Derive `requires_legal_review` from source policy metadata
- Seed all 4 as `ACTIVE`, `is_seeded=True`
- Idempotent — skip existing templates on re-seed

**Acceptance criteria:**
- [ ] 4 templates created on first seed
- [ ] 0 templates created on re-seed
- [ ] `default_sources_json` populated from registry
- [ ] `requires_legal_review` derived correctly

### Task 1.2 — Template API Router

**Files:**
- `backend/api/investigation_template_routes.py` (new)
- `backend/main.py` (register router)

**Work:**
- `GET /api/v1/investigation-templates/`
  - Returns `InvestigationTemplateListResponse`
  - Filterable by `inquiry_class` (exact match)
  - Filterable by `status` (exact match, defaults to ACTIVE only)
  - Returns full list (4 seeded templates — pagination unnecessary at this scale)
- `GET /api/v1/investigation-templates/{template_id}`
  - Returns `InvestigationTemplateDetail`
  - 404 if not found

**Acceptance criteria:**
- [ ] List returns all 4 seeded templates by default
- [ ] Filtering by inquiry_class returns correct subset
- [ ] Detail returns full template with domain filters and source manifest
- [ ] 404 on invalid template_id

### Task 1.3 — Seeder Integration

**Files:**
- `backend/main.py` or appropriate startup hook

**Work:**
- Call seeder on app startup (same pattern as scenario template seeder)
- Guard with session/transaction to avoid partial seeds

**Acceptance criteria:**
- [ ] Templates are available immediately after app startup
- [ ] Startup does not fail if templates already exist

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Seeder creates 4 templates on first run | Integration |
| 2 | Seeder skips all 4 on re-run (idempotent) | Integration |
| 3 | GET /investigation-templates/ returns 4 templates | Integration |
| 4 | GET /investigation-templates/?inquiry_class=INSPECTION returns only corporate_due_diligence | Integration |
| 5 | GET /investigation-templates/corporate_due_diligence returns full detail with domain filters and sources | Integration |

---

## Sprint 2: Investigation Create Integration + Certificate Provenance (7 tests)

Wire `template_id` and `committed_sources_json` into the investigation creation path and certificate.

### Task 2.1 — Create Endpoint Extension

**Files:**
- `backend/api/investigation_routes.py`
- `backend/schemas/investigation_schemas.py`
- `backend/core/osint_registry.py` (read — live source resolution)

**Work:**
- Add `template_id: str | None` to `InvestigationCreateRequest`
- On create:
  - If `template_id` provided:
    - Validate exists and status is ACTIVE (400 otherwise)
    - Apply template defaults for fields not explicitly provided by the user
    - Persist `template_id` on investigation record
  - If `template_id` not provided:
    - Existing behavior unchanged
- Validate all `domain_filters` values against backend `DomainFilter` enum (400 on invalid)
- Resolve source IDs from the live OSINT master registry for the final `domain_filters` (whether from template defaults or user overrides) via `DOMAIN_FILTER_SOURCE_GROUPS`
- Snapshot the resolved source IDs into `committed_sources_json` on the investigation record — this is immutable after creation
- `committed_sources_json` is populated whenever `domain_filters` are provided, regardless of whether a template was used

**Acceptance criteria:**
- [ ] Investigation created with valid template_id persists it
- [ ] Template defaults populate missing fields
- [ ] Explicit user values override template defaults
- [ ] Invalid template_id returns 400
- [ ] DRAFT template_id returns 400
- [ ] Missing template_id works as before (backward compatible)
- [ ] `committed_sources_json` populated from live registry at creation time
- [ ] `committed_sources_json` populated even without template (when domain_filters provided)

### Task 2.2 — Domain Filter Validation

**Files:**
- `backend/api/investigation_routes.py`

**Work:**
- Add domain filter validation at create time:
  - Each value in `domain_filters` must be a valid `DomainFilter` enum string value
  - Reject with 400 and clear message if invalid
- This catches frontend-invented IDs that have leaked into previous investigation records

**Acceptance criteria:**
- [ ] Valid domain filter values accepted
- [ ] Invalid values rejected with 400

### Task 2.3 — Certificate Provenance Extension

**Files:**
- `backend/investigation/certificate.py`

**Work:**
- Extend the certificate builder's metadata assembly to include template and source provenance
- The current certificate model stores metadata as a JSON blob — the addition is new keys in that JSON, not a table-level schema change
- When building certificate metadata:
  - If `investigation.template_id` is not None:
    - Add `template_id` and `template_name` keys to metadata JSON
  - If `investigation.committed_sources_json` is not None:
    - Add `committed_sources` key to metadata JSON
- If the certificate builder computes a canonical hash over metadata, update the hash payload to include the new keys (deliberate change — hash should reflect committed provenance chain)
- Certificates for investigations without template or committed sources remain unchanged (keys are absent)

**Acceptance criteria:**
- [ ] Certificate metadata includes `template_id` + `template_name` when template present
- [ ] Certificate metadata includes `committed_sources` when committed sources present
- [ ] Certificate for template-less investigation is unchanged
- [ ] Certificate hash payload updated to include provenance keys when present

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | Create investigation with valid template_id persists it and applies defaults | Integration |
| 2 | Create investigation with invalid template_id returns 400 | Integration |
| 3 | Create investigation with DRAFT template returns 400 | Integration |
| 4 | Explicit user overrides take precedence over template defaults | Integration |
| 5 | `committed_sources_json` snapshot populated from live registry at creation time | Integration |
| 6 | Certificate metadata includes `template_id` + `template_name` + `committed_sources` when present | Integration |
| 7 | Certificate hash payload includes provenance keys when present | Integration |

---

## Sprint 3: Frontend Wire-Up + Alignment (5 tests)

Replace static frontend templates with API-backed data and align domain filter IDs.

### Task 3.1 — Template API Client + Hook

**Files:**
- `frontend/src/api/investigationTemplates.ts` (new)
- `frontend/src/hooks/useInvestigationTemplates.ts` (new)

**Work:**
- API client: `fetchInvestigationTemplates()`, `fetchInvestigationTemplate(id)`
- TanStack Query hook: `useInvestigationTemplates(params?)`
- Long stale time — seeded data changes rarely

**Acceptance criteria:**
- [ ] Hook returns template list from API
- [ ] Loading/error states handled

### Task 3.2 — Wizard Template-First Refactor

**Files:**
- `frontend/src/components/investigation/CreateInvestigationWizard.tsx`

**Work:**
- Remove static `TEMPLATES` array (lines 67–88)
- Replace with `useInvestigationTemplates()` hook
- Make template selection the first step in the wizard
- Render template selection as a dropdown backed by the API list
- On template selection, populate wizard state from template detail:
  - `inquiry_class` from template (if not already set)
  - `domainFilters` from template's `domain_filters` (using backend enum IDs)
  - `stopCondition` from template's `default_stop_condition`
  - `stopConfig.time_window_days` from template's `default_time_window_days`
- Replace `inferTemplate()` function (lines 168–185) with signal-origin mapping table:
  - The wizard supports deterministic prefill from Signal Map, World Monitor, and theatre jump-offs via URL search params (`signal_category`, `signal_class`, `theatre_id`)
  - New mapping resolves signal-origin params against the backend template list (fetched from API, not hardcoded IDs):
    - `signal_category` containing `regulatory` or `signal_class === 'regulatory_clearance'` → `regulatory_action` template
    - domain filters containing `finance_and_markets` → `market_event` template
    - domain filters containing `corporate_and_entity` or `court_and_legal` → `corporate_due_diligence` template
    - fallback → `blank` template
  - If a template ID is not found in the API response (e.g., set to DRAFT), fallback is `blank`
  - Non-template fields (`theatre_id`, signal-specific domain filters) continue to be populated directly from URL params
- `construct_id` is not a free-text wizard field. If present from trusted launch context, it is surfaced read-only as inherited context; otherwise it is omitted until a backend construct registry exists.
- User can still override any populated default

**Acceptance criteria:**
- [ ] Static TEMPLATES array removed
- [ ] Wizard fetches templates from API
- [ ] Template selection is the first step and is rendered as a dropdown
- [ ] Template selection populates correct defaults
- [ ] Signal-origin launch context (from Signal Map / World Monitor / theatre) prefills correct template
- [ ] User overrides still work

### Task 3.3 — DomainFilterSelector Alignment

**Files:**
- `frontend/src/components/investigation/DomainFilterSelector.tsx`

**Work:**
- Replace 9 frontend-invented `DOMAIN_CATEGORIES` with entries matching backend `DomainFilter` enum:
  - `corporate_and_entity` → Corporate & Entity
  - `finance_and_markets` → Finance & Markets
  - `maritime` → Maritime
  - `airspace` → Airspace
  - `geopolitical_and_conflict` → Geopolitical & Conflict
  - `cyber_threat` → Cyber Threat
  - `property_and_land` → Property & Land
  - `court_and_legal` → Court & Legal
  - `satellite_and_earth_observation` → Satellite & Earth Observation
- Update `DomainFilterId` type
- Update descriptions and source examples per category
- Update icon assignments

**Acceptance criteria:**
- [ ] All 9 domain filter IDs match backend enum values exactly
- [ ] Labels and descriptions are informative
- [ ] Type exports remain compatible with wizard and other consumers

### Task 3.4 — Create Call + Inquiry Class Alignment

**Files:**
- `frontend/src/api/investigation.ts`
- `frontend/src/components/investigation/CreateInvestigationWizard.tsx`

**Work:**
- Add `template_id` to `createInvestigation()` request body type
- Wizard passes selected `template_id` in the create call
- Inquiry class selector options match backend enum:
  - INVESTIGATIVE, INSPECTION, SCRUTINY, SURVEY, COUNTERFACTUAL
- Remove any frontend-only inquiry class values (MONITORING, VERIFICATION if present)

**Acceptance criteria:**
- [ ] `template_id` sent in create payload
- [ ] Inquiry class options match backend
- [ ] `npm run build` passes

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Wizard renders template list from API (mock) | Component |
| 2 | Template selection populates wizard state with correct defaults | Component |
| 3 | Signal-origin URL params prefill correct template from backend list | Component |
| 4 | Domain filter IDs in create payload match backend enum values | Component |
| 5 | `npm run build` passes with all changes | Build |

---

## Cycle 022 Summary Target

- **21 tests** (4 + 5 + 7 + 5)
- **1 new model** (InvestigationTemplate)
- **1 new column on Investigation** (`committed_sources_json` — immutable source snapshot)
- **1 new seeder** (investigation_template_seeder.py)
- **2 new API endpoints** (template list + detail)
- **1 modified endpoint** (investigation create accepts template_id, populates committed_sources_json)
- **1 migration** (template table + investigation FK + committed_sources_json column)
- Investigation templates promoted from frontend-static to backend-owned
- Domain filter IDs aligned between frontend and backend
- Inquiry class options aligned between frontend and backend
- Certificate provenance includes template_id + template_name + committed_sources for auditable chain
- Committed source manifest provides immutable point-in-time audit anchor
- Signal-origin launch context preserved (Signal Map / World Monitor / theatre jump-offs)
- Backward compatible — investigations without template_id remain valid
- Regression suite green
