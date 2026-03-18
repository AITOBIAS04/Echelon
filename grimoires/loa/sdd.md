# SDD — Cycle 037: Contract-Backed Verification Infrastructure

**Cycle:** 037
**Date:** 2026-03-18
**Builder:** Loa
**PRD:** `grimoires/loa/prd.md`

---

## 1. Architecture Summary

Cycle 037 introduces an `EvaluationContract` layer between construct registration and evaluation runs. The contract captures what a construct claims, what checks will be applied, and produces a deterministic hash that pins every run and certificate to a specific, auditable contract state.

**Data flow:**

```
construct.yaml → SpecLoader → ConstructSpec
                                    ↓
                            PolicyNormalizer
                      (flag vagueness, extract refusals, tier_cap)
                                    ↓
                              CheckPlanner
                  (claims + available assets → planned_checks[])
                                    ↓
                            ContractService.create()
              (persist EvaluationContract, compute spec_hash + contract_hash)
                                    ↓
              ConstructAdapter.create_run() — threads contract_hash into run config
                                    ↓
              ConstructCertificateBuilder.build() — adds check_plan + hashes + issuance status
```

**Unchanged components:** ConstructScorer (rubric scoring engine), all rubric definitions, TestPromptRegistry, ConstructEvidenceBundleBuilder.

---

## 2. Technology Stack

No new dependencies. All new code uses existing stack:

| Layer | Technology |
|-------|-----------|
| ORM | SQLAlchemy 2.0 (async via asyncpg) |
| Migration | Alembic |
| Validation | Pydantic v2 |
| Hashing | Python `hashlib` (SHA-256) |
| YAML parsing | `PyYAML` (already in requirements.txt) |
| API | FastAPI |

---

## 3. Data Architecture

### 3.1 New Table: `evaluation_contracts`

```sql
CREATE TABLE evaluation_contracts (
    id                       VARCHAR(36)  PRIMARY KEY,
    construct_registration_id VARCHAR(50)  NOT NULL REFERENCES construct_registrations(id),
    spec_hash                VARCHAR(128) NOT NULL,
    contract_hash            VARCHAR(128) NOT NULL,
    normalized_claims        JSON         NOT NULL,
    explicit_refusals        JSON         NOT NULL DEFAULT '[]',
    planned_checks           JSON         NOT NULL,
    tier_cap                 VARCHAR(32)  NULL,
    status                   VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
    created_at               TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at               TIMESTAMP    NOT NULL DEFAULT now()
);

-- Only one ACTIVE contract per registration
CREATE UNIQUE INDEX uq_active_contract_per_registration
    ON evaluation_contracts (construct_registration_id)
    WHERE status = 'ACTIVE';

-- Lookup by contract_hash for run validation
CREATE INDEX ix_evaluation_contracts_contract_hash
    ON evaluation_contracts (contract_hash);
```

**Status transitions:** `ACTIVE → SUPERSEDED` (one-way; never reactivated)

### 3.2 SQLAlchemy Model

File: `backend/database/models.py` — add after `ConstructRegistration`:

```python
class EvaluationContractStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"

class EvaluationContract(Base):
    """Hash-addressed evaluation contract linking registration to check plan."""
    __tablename__ = "evaluation_contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_generate_uuid)
    construct_registration_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("construct_registrations.id"), nullable=False
    )
    spec_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    contract_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    normalized_claims: Mapped[dict] = mapped_column(JSON, nullable=False)
    explicit_refusals: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    planned_checks: Mapped[list] = mapped_column(JSON, nullable=False)
    tier_cap: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE",
        comment="ACTIVE | SUPERSEDED"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index(
            "uq_active_contract_per_registration",
            "construct_registration_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )
```

### 3.3 Column Extension: `investigations`

Add `contract_hash` column to `investigations` table (nullable for backward compatibility with pre-037 runs):

```sql
ALTER TABLE investigations ADD COLUMN contract_hash VARCHAR(128) NULL;
```

Existing runs keep `contract_hash = NULL`. New runs created through 037+ code always populate it.

### 3.4 Alembic Migration

File: `backend/alembic/versions/c037_evaluation_contracts.py`

```
revision = "c037_evaluation_contracts"
down_revision = "c025_osint_signals"
```

Operations:
1. Create `evaluation_contracts` table
2. Add `contract_hash` column (nullable) to `investigations`
3. Create partial unique index on `evaluation_contracts`
4. Create index on `contract_hash`

### 3.5 JSON Field Schemas

**`normalized_claims`** — array of claim objects:
```json
[
  {
    "domain": "Design Systems",
    "original": "Design Systems",
    "is_vague": false,
    "matched_category": "design_systems"
  },
  {
    "domain": "security",
    "original": "security",
    "is_vague": true,
    "matched_category": null,
    "vagueness_reason": "broad_category"
  }
]
```

**`explicit_refusals`** — array of refusal declarations:
```json
[
  {"scope": "financial_advice", "reason": "Not licensed for financial guidance"},
  {"scope": "medical_diagnosis", "reason": "Out of domain"}
]
```

**`planned_checks`** — array of check specifications:
```json
[
  {
    "check_id": "rubric-design-systems",
    "check_type": "RUBRIC",
    "domain": "Design Systems",
    "source": "rubric_registry",
    "critical": true
  },
  {
    "check_id": "bench-humaneval",
    "check_type": "BENCHMARK",
    "domain": "code",
    "source": "r2_manifest",
    "critical": false,
    "asset_id": "humaneval"
  },
  {
    "check_id": "anchor-wcag",
    "check_type": "ANCHOR",
    "domain": "accessibility",
    "source": "anchor_mapper",
    "critical": false,
    "anchor_class": "PUBLIC_STANDARD"
  }
]
```

---

## 4. Component Design

### 4.1 SpecLoader

**File:** `backend/services/spec_loader.py`

**Purpose:** Parse construct.yaml content into a normalized `ConstructSpec` dataclass. Compute deterministic `spec_hash`.

```python
@dataclass(frozen=True)
class ConstructSpec:
    slug: str
    version: str
    domain_claims: list[str]
    refusals: list[dict]          # [{scope, reason}]
    skill_manifest: list[dict]    # [{command, domain}]
    raw_yaml: str                 # Original content for hash
    spec_hash: str                # sha256 of normalized content
```

**Key methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `load` | `(yaml_content: str) → ConstructSpec` | Parse YAML, validate required fields, normalize, compute hash |
| `compute_spec_hash` | `(yaml_content: str) → str` | SHA-256 of sorted-key canonical JSON of parsed content |

**Validation rules:**
- Required fields: `slug`, `version`, `domain_claims` (non-empty list), `skill_manifest` (non-empty list)
- Optional fields: `refusals` (defaults to `[]`)
- Rejects: missing required fields, invalid YAML syntax, empty domain_claims

**Hash computation:**
```python
def compute_spec_hash(yaml_content: str) -> str:
    parsed = yaml.safe_load(yaml_content)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
```

### 4.2 PolicyNormalizer

**File:** `backend/services/policy_normalizer.py`

**Purpose:** Validate domain claims against known precise categories. Flag vague claims. Extract refusals. Compute tier_cap.

```python
@dataclass(frozen=True)
class NormalizationResult:
    normalized_claims: list[dict]   # [{domain, original, is_vague, matched_category, vagueness_reason?}]
    explicit_refusals: list[dict]   # [{scope, reason}]
    tier_cap: Optional[str]         # None if all precise, "UNVERIFIED" if any vague
    has_vague_claims: bool
```

**Key methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `normalize` | `(spec: ConstructSpec) → NormalizationResult` | Main entry — normalize claims, extract refusals, compute tier_cap |
| `_classify_claim` | `(domain: str) → dict` | Classify single claim as precise or vague |
| `_compute_tier_cap` | `(claims: list[dict]) → Optional[str]` | `None` if all precise, `"UNVERIFIED"` if any vague |

**Vague claim detection:**

```python
KNOWN_PRECISE_DOMAINS = {
    "design_systems", "motion_design", "visual_refinement",
    "taste_compounding", "frontend_best_practices",
    "code_generation", "code_review", "testing",
    "documentation", "api_design", "data_analysis",
    "investigation", "market_analysis", "risk_assessment",
    # ... extensible
}

KNOWN_VAGUE_TERMS = {
    "security", "ai", "general", "everything", "all",
    "coding", "development", "engineering", "tech",
    # ... extensible
}
```

Classification algorithm:
1. Normalize claim to snake_case
2. If exact match in `KNOWN_PRECISE_DOMAINS` → precise
3. If any token in `KNOWN_VAGUE_TERMS` → vague, reason = `"broad_category"`
4. If no match in either → vague, reason = `"unrecognized_domain"`

### 4.3 CheckPlanner

**File:** `backend/services/check_planner.py`

**Purpose:** Given a contract's normalized claims and available assets, produce a deterministic list of planned checks.

```python
@dataclass(frozen=True)
class PlannedCheck:
    check_id: str        # e.g. "rubric-design-systems", "bench-humaneval"
    check_type: str      # RUBRIC | BENCHMARK | ANCHOR
    domain: str
    source: str          # "rubric_registry" | "r2_manifest" | "anchor_mapper"
    critical: bool       # True for RUBRIC checks (core to construct identity)
    asset_id: Optional[str] = None
    anchor_class: Optional[str] = None
```

**Key methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `plan_checks` | `(normalized_claims, slug, available_rubrics, available_assets) → list[PlannedCheck]` | Deterministic check plan |
| `compute_contract_hash` | `(spec_hash, planned_checks) → str` | SHA-256 of spec_hash + canonical checks JSON |

**Planning algorithm:**

1. **Rubric checks** — For each precise domain claim, check if `slug` has a registered rubric for that domain. If yes → add `PlannedCheck(check_type="RUBRIC", critical=True)`.

2. **Benchmark checks** — For each domain claim, call `map_dimension_anchors(domain)` from existing `construct_anchor_mapper.py`. For anchors with `anchor_class == BENCHMARK_DATASET`, check `is_r2_eligible(anchor_id)` from `eval_asset_policy.py`. If R2-eligible and asset available → add `PlannedCheck(check_type="BENCHMARK", critical=False)`.

3. **Anchor checks** — For anchors with `anchor_class == PUBLIC_STANDARD` or `DETERMINISTIC_CHECK` → add `PlannedCheck(check_type="ANCHOR", critical=False)`.

4. **Sort** by `(check_type, domain, check_id)` for determinism.

**Contract hash computation:**
```python
def compute_contract_hash(spec_hash: str, planned_checks: list[PlannedCheck]) -> str:
    checks_canonical = json.dumps(
        [asdict(c) for c in planned_checks],
        sort_keys=True, separators=(",", ":")
    )
    payload = f"{spec_hash}:{checks_canonical}"
    return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()}"
```

### 4.4 ContractService

**File:** `backend/services/contract_service.py`

**Purpose:** CRUD for EvaluationContract. Handles creation, supersession, and validation.

**Key methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_contract` | `(session, registration_id, spec, normalization, planned_checks) → EvaluationContract` | Supersede existing ACTIVE, persist new |
| `get_active_contract` | `(session, registration_id) → Optional[EvaluationContract]` | Current ACTIVE contract |
| `get_by_hash` | `(session, contract_hash) → Optional[EvaluationContract]` | Lookup by contract_hash |
| `supersede` | `(session, contract_id) → None` | Set status = SUPERSEDED |
| `validate_contract_active` | `(session, contract_hash) → bool` | Check if contract_hash belongs to ACTIVE contract |

**Contract creation flow:**

```python
async def create_contract(
    self,
    session: AsyncSession,
    registration_id: str,
    spec: ConstructSpec,
    normalization: NormalizationResult,
    planned_checks: list[PlannedCheck],
) -> EvaluationContract:
    # 1. Supersede any existing ACTIVE contract for this registration
    existing = await self.get_active_contract(session, registration_id)
    if existing:
        existing.status = "SUPERSEDED"
        existing.updated_at = datetime.utcnow()

    # 2. Compute contract_hash
    contract_hash = compute_contract_hash(spec.spec_hash, planned_checks)

    # 3. Persist new contract
    contract = EvaluationContract(
        construct_registration_id=registration_id,
        spec_hash=spec.spec_hash,
        contract_hash=contract_hash,
        normalized_claims=[asdict(c) if hasattr(c, '__dataclass_fields__') else c
                           for c in normalization.normalized_claims],
        explicit_refusals=normalization.explicit_refusals,
        planned_checks=[asdict(c) for c in planned_checks],
        tier_cap=normalization.tier_cap,
        status="ACTIVE",
    )
    session.add(contract)
    await session.flush()
    return contract
```

### 4.5 Certificate Builder Extensions

**File:** `backend/services/construct_certificate_builder.py` — extend existing

**Changes:**

1. `ScorerOutput` gains new field:
   ```python
   check_plan: Optional[dict] = None  # {total_planned, total_executed, checks[]}
   ```

2. `ConstructCertificate` gains new fields:
   ```python
   contract_hash: Optional[str] = None
   spec_hash: Optional[str] = None
   check_plan: Optional[dict] = None
   issuance_status: str = "READY"  # READY | DEFERRED | REJECTED
   remediation: Optional[dict] = None
   ```

3. New method `compute_issuance_status`:
   ```python
   def compute_issuance_status(
       self,
       planned_checks: list[dict],
       executed_check_ids: set[str],
       verdict: str,
   ) -> tuple[str, Optional[dict]]:
       """Returns (issuance_status, remediation_payload)."""
       planned_ids = {c["check_id"] for c in planned_checks}
       missing = planned_ids - executed_check_ids

       if verdict == "FAIL":
           return "REJECTED", None

       if missing:
           missing_details = []
           for check in planned_checks:
               if check["check_id"] in missing:
                   missing_details.append({
                       "check_id": check["check_id"],
                       "reason": "dataset_not_available"
                           if check.get("check_type") == "BENCHMARK"
                           else "check_not_executed",
                   })
           return "DEFERRED", {
               "status": "DEFERRED",
               "reason": "checks_unavailable",
               "missing_checks": missing_details,
               "executed_count": len(executed_check_ids),
               "planned_count": len(planned_ids),
               "recommendation": "Upload missing datasets and re-run",
           }

       return "READY", None
   ```

4. `build()` updated to accept optional `contract` parameter and populate new fields.

5. `to_certificate_json()` updated to include `contract_hash`, `spec_hash`, `check_plan`, `issuance_status`, `remediation` in output.

---

## 5. API Design

### 5.1 New Endpoints

**Contract CRUD** — added to existing `construct_routes.py`:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/constructs/{slug}/{version}/contract` | Create/refresh contract from construct.yaml |
| `GET` | `/api/constructs/{slug}/{version}/contract` | Get ACTIVE contract |
| `GET` | `/api/constructs/{slug}/{version}/contracts` | List all contracts (ACTIVE + SUPERSEDED) |

#### `POST /api/constructs/{slug}/{version}/contract`

**Request body:**
```json
{
  "yaml_content": "slug: artisan\nversion: 1.4.0\ndomain_claims:\n  - Design Systems\n  - Motion Design\nrefusals:\n  - scope: financial_advice\n    reason: Not licensed\nskill_manifest:\n  - command: /inscribe\n    domain: Design Systems\n"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "construct_registration_id": "uuid",
  "spec_hash": "sha256:abc...",
  "contract_hash": "sha256:def...",
  "normalized_claims": [...],
  "explicit_refusals": [...],
  "planned_checks": [...],
  "tier_cap": null,
  "status": "ACTIVE",
  "created_at": "2026-03-18T..."
}
```

**Error cases:**
- `404` — Registration not found
- `400` — Invalid YAML content (malformed, missing required fields)
- `409` — Contract with identical spec_hash already ACTIVE (no-op, return existing)

#### `GET /api/constructs/{slug}/{version}/contract`

**Response (200):** Same shape as POST response for ACTIVE contract.
**Error:** `404` — No ACTIVE contract exists.

#### `GET /api/constructs/{slug}/{version}/contracts`

**Response (200):**
```json
{
  "contracts": [...],
  "total": 3
}
```

### 5.2 Modified Endpoints

#### `POST /api/constructs/{slug}/{version}/runs` (create_run)

**New behavior:**
1. Fetch ACTIVE contract for registration
2. If no ACTIVE contract → `409 Conflict: "No active contract. Create contract first."`
3. If ACTIVE contract exists → thread `contract_hash` into investigation's `stop_config_json` and new `contract_hash` column

#### `POST /api/constructs/{slug}/{version}/certificate` (issue_certificate)

**New behavior:**
1. Fetch contract via `contract_hash` from investigation
2. Build `check_plan` comparing `planned_checks` against actually executed checks
3. Compute `issuance_status` (READY / DEFERRED / REJECTED)
4. Include `check_plan`, `contract_hash`, `spec_hash`, `issuance_status`, `remediation` in certificate JSON

**Updated response shape** (additions only):
```json
{
  "...existing fields...",
  "contract_hash": "sha256:...",
  "spec_hash": "sha256:...",
  "issuance_status": "READY",
  "check_plan": {
    "total_planned": 10,
    "total_executed": 10,
    "checks": [...]
  },
  "remediation": null
}
```

### 5.3 Pydantic Schema Additions

**File:** `backend/schemas/construct_schemas.py`

```python
# --- Request ---
class CreateContractRequest(BaseModel):
    yaml_content: str

# --- Response ---
class PlannedCheckSchema(BaseModel):
    check_id: str
    check_type: str  # RUBRIC | BENCHMARK | ANCHOR
    domain: str
    source: str
    critical: bool
    asset_id: Optional[str] = None
    anchor_class: Optional[str] = None

class NormalizedClaimSchema(BaseModel):
    domain: str
    original: str
    is_vague: bool
    matched_category: Optional[str] = None
    vagueness_reason: Optional[str] = None

class RefusalSchema(BaseModel):
    scope: str
    reason: str

class ContractResponse(BaseModel):
    id: str
    construct_registration_id: str
    spec_hash: str
    contract_hash: str
    normalized_claims: list[NormalizedClaimSchema]
    explicit_refusals: list[RefusalSchema]
    planned_checks: list[PlannedCheckSchema]
    tier_cap: Optional[str] = None
    status: str
    created_at: datetime

class ContractListResponse(BaseModel):
    contracts: list[ContractResponse]
    total: int

# --- Certificate extensions ---
class CheckPlanEntrySchema(BaseModel):
    id: str
    type: str  # RUBRIC | BENCHMARK | ANCHOR
    status: str  # EXECUTED | NOT_EXECUTED
    score: Optional[float] = None
    reason: Optional[str] = None

class CheckPlanSchema(BaseModel):
    total_planned: int
    total_executed: int
    checks: list[CheckPlanEntrySchema]

class RemediationSchema(BaseModel):
    status: str
    reason: str
    missing_checks: list[dict]
    executed_count: int
    planned_count: int
    recommendation: str
```

`CertificateResponse` extended with:
```python
contract_hash: Optional[str] = None
spec_hash: Optional[str] = None
issuance_status: str = "READY"
check_plan: Optional[CheckPlanSchema] = None
remediation: Optional[RemediationSchema] = None
```

---

## 6. Integration Points

### 6.1 ConstructRegistry → ContractService

After successful registration in `ConstructRegistry.register()`, the caller (route handler) creates the contract:

```python
# In POST /register route handler
registration = await registry.register(...)

# If yaml_content provided, create contract immediately
if request.yaml_content:
    spec = SpecLoader.load(request.yaml_content)
    normalization = PolicyNormalizer().normalize(spec)
    rubrics = get_rubrics(registration.slug)
    planned = CheckPlanner().plan_checks(
        normalization.normalized_claims, registration.slug, rubrics, available_assets
    )
    contract = await contract_service.create_contract(
        session, registration.id, spec, normalization, planned
    )
```

Contract creation is decoupled from registration — can be done at registration time or separately via `POST /contract`.

### 6.2 ConstructAdapter → Contract Validation

`create_run()` extended to:
1. Accept `contract_hash` parameter
2. Validate contract is ACTIVE via `ContractService.validate_contract_active()`
3. Store `contract_hash` on investigation record

```python
async def create_run(self, registration, contract_hash: str) -> Investigation:
    # Validate contract is ACTIVE
    if not await self.contract_service.validate_contract_active(
        self.db_session, contract_hash
    ):
        raise ValueError("Contract is SUPERSEDED or not found. Create new contract first.")

    investigation = Investigation(
        ...existing fields...,
        contract_hash=contract_hash,  # NEW
    )
    # stop_config_json also includes contract_hash
    investigation.stop_config_json = {
        **existing_stop_config,
        "contract_hash": contract_hash,
    }
```

### 6.3 CertificateBuilder → Check Plan Assembly

During certificate issuance (`POST /certificate`):

```python
# 1. Get contract from investigation's contract_hash
contract = await contract_service.get_by_hash(session, investigation.contract_hash)

# 2. Build check_plan by comparing planned vs executed
executed_check_ids = _determine_executed_checks(episodes, contract.planned_checks)
check_plan = _build_check_plan(contract.planned_checks, executed_check_ids, episode_scores)

# 3. Compute issuance status
issuance_status, remediation = cert_builder.compute_issuance_status(
    contract.planned_checks, executed_check_ids, verdict
)

# 4. Apply tier_cap
if contract.tier_cap and tier_ordering[tier] > tier_ordering[contract.tier_cap]:
    tier = contract.tier_cap

# 5. Build certificate with new fields
certificate = cert_builder.build(
    registration, investigation, scorer_output,
    evidence_bundle_hash, contract=contract,
    issuance_status=issuance_status, remediation=remediation,
    check_plan=check_plan,
)
```

### 6.4 Backward Compatibility

- Runs created before 037 have `contract_hash = NULL` on investigation
- Certificate issuance for pre-037 runs skips check_plan/contract fields (returns `null`)
- `POST /runs` for registrations without an ACTIVE contract returns `409`
- Existing V1 test suite passes unchanged (regression guardrail)

---

## 7. Hash Invalidation Logic

### 7.1 Spec Change Detection

When `POST /contract` is called with new `yaml_content`:
1. Compute `spec_hash` from new content
2. If ACTIVE contract exists with same `spec_hash` → return existing (409 no-op)
3. If `spec_hash` differs → supersede ACTIVE contract, create new one with new check plan

### 7.2 Check Plan Refresh

When assets change (new dataset uploaded, new rubric registered):
1. Re-run `CheckPlanner.plan_checks()` with current available assets
2. Compute new `contract_hash` from `spec_hash + new planned_checks`
3. If `contract_hash` differs from ACTIVE → supersede and create new contract
4. If `contract_hash` unchanged → no-op

### 7.3 Run Rejection on SUPERSEDED

`ConstructAdapter.create_run()` validates `contract_hash` is ACTIVE. If contract has been superseded between run creation and this call → raise `ValueError`, HTTP 409.

---

## 8. Test Architecture

All tests in `backend/tests/test_contract_*.py`:

| File | Tests | What |
|------|-------|------|
| `test_spec_loader.py` | 6 | YAML parsing, hash stability, refusal extraction, malformed rejection |
| `test_policy_normalizer.py` | 8 | Precise classification, vague detection, tier_cap, refusal normalization |
| `test_check_planner.py` | 8 | Deterministic plans, benchmark availability, anchor checks, missing datasets |
| `test_contract_service.py` | 6 | CRUD, supersession, hash computation, duplicate prevention |
| `test_certificate_integration.py` | 6 | READY/DEFERRED/REJECTED paths, remediation payload, check_plan output |
| `test_hash_invalidation.py` | 4 | Spec change → supersede, contract_hash detection, run rejection |
| `test_regression_v1.py` | 4 | Existing registration + run + certificate flow unchanged |

**Total:** ~42 tests

**Test fixtures:**
- `sample_construct_yaml` — valid artisan construct.yaml
- `vague_construct_yaml` — construct with "security", "AI" claims
- `malformed_yaml` — missing required fields
- Reuse existing `async_session` fixture from test infrastructure

---

## 9. File Manifest

### New Files

| File | Purpose |
|------|---------|
| `backend/services/spec_loader.py` | ConstructSpec dataclass + YAML parsing + spec_hash |
| `backend/services/policy_normalizer.py` | Claim classification + refusal extraction + tier_cap |
| `backend/services/check_planner.py` | Deterministic check planning + contract_hash |
| `backend/services/contract_service.py` | EvaluationContract CRUD + supersession |
| `backend/alembic/versions/c037_evaluation_contracts.py` | Migration |
| `backend/tests/test_spec_loader.py` | SpecLoader tests |
| `backend/tests/test_policy_normalizer.py` | PolicyNormalizer tests |
| `backend/tests/test_check_planner.py` | CheckPlanner tests |
| `backend/tests/test_contract_service.py` | ContractService tests |
| `backend/tests/test_certificate_integration.py` | Certificate issuance path tests |
| `backend/tests/test_hash_invalidation.py` | Hash invalidation tests |
| `backend/tests/test_regression_v1.py` | V1 regression tests |

### Modified Files

| File | Change |
|------|--------|
| `backend/database/models.py` | Add `EvaluationContract` model + `EvaluationContractStatus` enum |
| `backend/schemas/construct_schemas.py` | Add contract + check_plan schemas, extend `CertificateResponse` |
| `backend/api/construct_routes.py` | Add 3 contract endpoints, modify `create_run` + `issue_certificate` |
| `backend/services/construct_adapter.py` | Thread `contract_hash` into `create_run()` |
| `backend/services/construct_certificate_builder.py` | Add `check_plan`, `issuance_status`, `remediation` fields + `compute_issuance_status()` |

### Unchanged Files

| File | Why |
|------|-----|
| `backend/services/construct_scorer.py` | Rubric scoring engine stays as-is (PRD §3) |
| `backend/services/construct_evidence_bundle.py` | Bundle hashing unchanged |
| `backend/services/construct_anchor_mapper.py` | Used by CheckPlanner read-only, no modifications |
| `backend/services/eval_asset_policy.py` | Used by CheckPlanner read-only, no modifications |
| `backend/services/test_prompt_registry.py` | Prompt loading unchanged |
| `backend/data/construct_rubrics/*` | Rubric definitions unchanged (PRD §3) |

---

## 10. Security Considerations

- **No new auth requirements** — contract endpoints use same session auth as existing construct routes
- **YAML parsing** — `yaml.safe_load()` only (never `yaml.load()`)
- **Hash integrity** — SHA-256 with canonical JSON serialization prevents ordering attacks
- **No PII in contracts** — contracts contain domain claims and check specifications only
- **Immutable certificates** — certificate JSON references `contract_hash` + `spec_hash` immutably; verifier can check if contract is still ACTIVE but certificate content never changes

---

## 11. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| construct.yaml format varies across packs | SpecLoader validates strict schema; rejects malformed with descriptive errors |
| CheckPlanner depends on R2 manifest availability | Graceful degradation → checks marked NOT_EXECUTED → DEFERRED issuance |
| Partial unique index (`WHERE status = 'ACTIVE'`) PostgreSQL-specific | Already use PostgreSQL exclusively (Cycle 023 unified); index is standard PostgreSQL partial index |
| Hash invalidation cascading | Only ACTIVE contracts affected; historical certificates immutable |
| Vague claim false positives | Conservative allowlists; `KNOWN_VAGUE_TERMS` configurable |
