# Sprint Plan: Theatre Template Engine

> Cycle: cycle-031 | PRD: `grimoires/loa/prd.md` | SDD: `grimoires/loa/sdd.md`
> Team: 1 AI engineer | Sprint cadence: continuous
> Global sprint offset: 25 (previous cycle ended at 24)

---

## Overview

Three sprints following a strict dependency chain:

1. **Sprint 1 — Core Engine Foundation:** State machine, canonical JSON, commitment protocol, criteria, template validation, database tables
2. **Sprint 2 — Execution Engine:** OracleAdapter contract, replay engine, resolution state machine, scoring, evidence bundles, certificates, tier assignment
3. **Sprint 3 — API Layer + Integration:** FastAPI routes, Pydantic schemas, bridge service, test fixtures, end-to-end integration tests

```
Sprint 1 (Foundation) → Sprint 2 (Engine) → Sprint 3 (API + Integration)
```

---

## Sprint 1: Core Engine Foundation

> Global ID: sprint-25 | Local ID: sprint-1
> Goal: Build the foundational components that everything else depends on — state machine, canonical JSON, commitment protocol, structured criteria, template validation, and database tables.

### Tasks

#### T1.1: Theatre State Machine
**Description:** Implement `TheatreState` enum, `VALID_TRANSITIONS` dict, and `TheatreStateMachine` class in `theatre/engine/state_machine.py`. Six states (DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED), irreversible transitions only.

**Acceptance Criteria:**
- [x] `TheatreState` enum with 6 values
- [x] `VALID_TRANSITIONS` mapping each state to its valid successors
- [x] `TheatreStateMachine.transition()` advances state or raises `InvalidTransitionError`
- [x] `TheatreStateMachine.can_transition()` returns bool
- [x] All 5 valid transitions succeed
- [x] All invalid transitions raise `InvalidTransitionError` (test every invalid pair)
- [x] `ARCHIVED` has no valid successors

**Tests:** `tests/theatre/test_state_machine.py` — all valid transitions, all invalid transitions (30 invalid pairs), edge cases (double transition, ARCHIVED terminal).

---

#### T1.2: Canonical JSON Utility
**Description:** Implement `canonical_json()`, `_normalise_value()`, and `_normalise_float()` in `theatre/engine/canonical_json.py`. Must produce RFC 8785-compliant deterministic output.

**Acceptance Criteria:**
- [x] Keys sorted lexicographically at every nesting level
- [x] No whitespace between tokens
- [x] Float normalisation: 1.0 → 1, 0.10 → 0.1, no trailing zeroes
- [x] `NaN` and `Infinity` raise `ValueError`
- [x] `null` values included (not omitted)
- [x] Arrays preserve insertion order
- [x] Round-trip determinism: `canonical_json(x) == canonical_json(json.loads(canonical_json(x)))`
- [x] UTF-8 encoding, minimal escaping

**Tests:** `tests/theatre/test_canonical_json.py` — nested dicts, floats (edge cases: 1.0, -0.0, 1e10, 0.1+0.2), null values, Unicode strings, empty containers, NaN/Infinity rejection, round-trip property test.

---

#### T1.3: Commitment Protocol
**Description:** Implement `CommitmentProtocol` (compute_hash, verify_hash) and `CommitmentReceipt` model in `theatre/engine/commitment.py`. Uses `canonical_json()` from T1.2.

**Acceptance Criteria:**
- [x] `compute_hash()` produces SHA-256 hex string (64 chars)
- [x] Composite object has exactly three keys: `dataset_hashes`, `template`, `version_pins`
- [x] Same inputs always produce same hash (deterministic)
- [x] Different inputs produce different hashes
- [x] `verify_hash()` returns True for matching, False for mismatched
- [x] `CommitmentReceipt` Pydantic model with all fields from SDD §4.2

**Tests:** `tests/theatre/test_commitment.py` — determinism (same input → same hash), sensitivity (single field change → different hash), round-trip verify, CommitmentReceipt serialisation.

---

#### T1.4: Structured Criteria Model
**Description:** Implement `TheatreCriteria` Pydantic model in `theatre/engine/models.py` with weight validation.

**Acceptance Criteria:**
- [x] `criteria_ids: list[str]` — non-empty, unique
- [x] `criteria_human: str` — freeform rubric
- [x] `weights: dict[str, float]` — keys must be subset of `criteria_ids`, values must sum to 1.0 (within 1e-6 tolerance)
- [x] Validation raises on extra weight keys
- [x] Validation raises on weight sum ≠ 1.0
- [x] Empty weights dict is valid (equal weight fallback computed at scoring time)

**Tests:** `tests/theatre/test_criteria.py` — valid criteria, extra key rejection, weight sum validation, empty weights, single criterion.

---

#### T1.5: Template Validator
**Description:** Implement `TemplateValidator` in `theatre/engine/template_validator.py`. Phase 1: JSON Schema validation against `echelon_theatre_schema_v2.json`. Phase 2: Runtime validation rules (8 rules from SDD §8.2).

**Acceptance Criteria:**
- [x] Loads schema from `docs/schemas/echelon_theatre_schema_v2.json`
- [x] Validates template structure against JSON Schema (required fields, types, enums)
- [x] Runtime rule 1: `criteria.weights` keys ⊆ `criteria.criteria_ids`
- [x] Runtime rule 2: `criteria.weights` values sum to 1.0
- [x] Runtime rule 3: Every `construct_id` in `resolution_programme` has `version_pins.constructs` entry
- [x] Runtime rule 4: Every construct in `construct_chain` has version pin
- [x] Runtime rule 5: Every `hitl_steps[].step_id` matches a resolution step with type `hitl_rubric`
- [x] Runtime rule 6: `adapter_type: "mock"` rejected when `is_certificate_run=True`
- [x] Runtime rule 7: `dataset_hashes[replay_dataset_id]` must be present
- [x] Returns list of error strings (empty = valid)
- [x] Conditional validation by `execution_path` (replay requires `product_theatre_config` + `dataset_hashes`)

**Tests:** `tests/theatre/test_template_validator.py` — valid Product template passes, valid Market template passes, each runtime rule violation caught individually, missing required fields caught.

---

#### T1.6: Database Tables + Migration
**Description:** Add 5 new SQLAlchemy tables to `backend/database/models.py` and create Alembic migration. Tables: `theatre_templates`, `theatres`, `theatre_certificates`, `theatre_episode_scores`, `theatre_audit_events`.

**Acceptance Criteria:**
- [x] All 5 tables follow existing `Mapped[]` pattern
- [x] `_generate_uuid` reused for primary key defaults
- [x] Foreign keys: theatres → theatre_templates, theatres → theatre_certificates, episode_scores → theatres, episode_scores → theatre_certificates, audit_events → theatres
- [x] Indexes match SDD §5.1 (composite and single-column)
- [x] Relationships with `back_populates` configured
- [ ] Alembic migration creates all tables *(deferred — requires DB connection)*
- [x] No modification to existing tables

**Tests:** Migration runs successfully. Table creation verified.

---

#### T1.7: Package Scaffolding
**Description:** Create the `theatre/` package directory structure with `__init__.py` files, and `theatre/fixtures/` directory for test fixture templates.

**Acceptance Criteria:**
- [x] `theatre/__init__.py` exists
- [x] `theatre/engine/__init__.py` exists
- [x] `theatre/fixtures/__init__.py` exists
- [x] All modules from T1.1–T1.5 importable from the package

**Tests:** Import smoke test.

---

### Sprint 1 Success Criteria

- All 5 valid state transitions pass, all invalid transitions rejected
- `canonical_json()` round-trip determinism confirmed across all test inputs
- Commitment hash deterministic — same inputs always produce same SHA-256
- Template validation catches all 8 runtime rule violations
- 5 database tables created via Alembic migration
- All unit tests passing

---

## Sprint 2: Execution Engine

> Global ID: sprint-26 | Local ID: sprint-2
> Goal: Build the execution machinery — OracleAdapter contract, replay engine, resolution state machine, scoring provider, evidence bundles, certificate generation, and tier assignment.
> Depends on: Sprint 1 (state machine, commitment, criteria, canonical JSON, DB tables)

### Tasks

#### T2.1: Oracle Invocation Contract
**Description:** Implement `OracleInvocationRequest`, `OracleInvocationResponse`, and `OracleInvocationMetadata` in `theatre/engine/oracle_contract.py`. Standardised request/response envelope wrapping the existing `OracleAdapter`.

**Acceptance Criteria:**
- [x] `OracleInvocationRequest` with all fields from SDD §4.5
- [x] `OracleInvocationResponse` with status enum: SUCCESS, TIMEOUT, ERROR, REFUSED
- [x] `OracleInvocationMetadata` with timeout, retry, deterministic, sanitise_input defaults
- [x] Adapter wrapper function: takes `OracleInvocationRequest`, calls underlying `OracleAdapter`, returns `OracleInvocationResponse`
- [x] Retry logic with configurable backoff
- [x] Timeout handling returns `TIMEOUT` status
- [x] Error handling returns `ERROR` status with detail

**Tests:** `tests/theatre/test_oracle_contract.py` — request/response serialisation, timeout simulation, retry logic, error wrapping.

---

#### T2.2: Theatre Scoring Provider
**Description:** Implement `TheatreScoringProvider` in `theatre/engine/scoring.py`. Scores construct outputs against committed `criteria_ids` using the underlying `ScoringProvider`.

**Acceptance Criteria:**
- [x] `score_episode()` returns `dict[str, float]` mapping criteria_id → score (0.0–1.0)
- [x] `compute_composite()` produces weighted aggregate using `TheatreCriteria.weights`
- [x] Equal weight fallback when `weights` dict is empty
- [x] Handles missing criteria gracefully (score = 0.0 for missing)

**Tests:** `tests/theatre/test_scoring.py` — weighted composite, equal weight fallback, missing criterion handling.

---

#### T2.3: Replay Engine
**Description:** Implement `ReplayEngine` in `theatre/engine/replay.py`. Orchestrates full Product Theatre execution: dataset hash verification → episode iteration → scoring → aggregation.

**Acceptance Criteria:**
- [x] Verifies dataset hash matches commitment before first episode
- [x] Processes episodes sequentially
- [x] For each episode: build request → invoke via oracle contract → record invocation → score → record score
- [x] Progress callback called after each episode
- [x] Failure rate tracked: >20% failures → cap at UNVERIFIED
- [x] TIMEOUT/ERROR episodes scored as missing (affects recall/coverage)
- [x] REFUSED episodes excluded from scoring, logged
- [x] Returns `ReplayResult` with all episode scores + aggregate + failure rate
- [x] Dataset hash mismatch → immediate failure

**Tests:** `tests/theatre/test_replay_engine.py` — successful full lifecycle (mock adapter), >20% failure cap, dataset hash mismatch rejection, REFUSED exclusion, progress callback invocation.

---

#### T2.4: Resolution State Machine
**Description:** Implement `ResolutionStateMachine` in `theatre/engine/resolution.py`. Executes pre-committed oracle programme sequence with branching and HITL support.

**Acceptance Criteria:**
- [x] Executes steps in committed order
- [x] `construct_invocation` steps invoke construct via oracle contract
- [x] `deterministic_computation` steps execute without oracle
- [x] `hitl_rubric` steps produce `PENDING_HITL` status
- [x] `aggregation` steps combine previous step outputs
- [x] `escalation_path` followed on step failure
- [x] Version pin validation: every `construct_id` has matching pin
- [x] Returns `ResolutionResult` with outcomes + audit trail

**Tests:** `tests/theatre/test_resolution.py` — linear execution, escalation path on failure, HITL pending status, version pin enforcement.

---

#### T2.5: Evidence Bundle Builder
**Description:** Implement `EvidenceBundleBuilder` in `theatre/engine/evidence_bundle.py`. Creates the auditable evidence directory for a completed Theatre.

**Acceptance Criteria:**
- [x] Creates directory structure per SDD §4.10
- [x] `write_manifest()`, `write_template()`, `write_commitment_receipt()` produce valid JSON files
- [x] `write_ground_truth()` writes JSONL
- [x] `write_invocation()` writes per-episode JSON
- [x] `write_episode_score()` appends to per_episode.jsonl
- [x] `write_aggregate_scores()` writes aggregate.json
- [x] `write_certificate()` writes certificate.json
- [x] `append_audit_event()` appends to audit_trail.jsonl
- [x] `compute_bundle_hash()` produces deterministic SHA-256 over manifest
- [x] `validate_minimum_files()` returns missing required files (empty = valid)

**Tests:** `tests/theatre/test_evidence_bundle.py` — full bundle generation, minimum files validation (missing file detected), bundle hash determinism.

---

#### T2.6: Calibration Certificate + Tier Assigner + Constraint Gate
**Description:** Implement `TheatreCalibrationCertificate` (theatre/engine/certificate.py), `TierAssigner` (theatre/engine/tier_assigner.py), and `ConstraintYieldingGate` (theatre/engine/constraint_gate.py).

**Acceptance Criteria:**
- [x] `TheatreCalibrationCertificate` Pydantic model with all fields from SDD §4.8
- [x] `TierAssigner.assign()` returns correct tier for all boundary conditions:
  - <50 replays → UNVERIFIED
  - ≥50 + full evidence → BACKTESTED
  - BACKTESTED + 3 months + attestation → PROVEN
  - >20% failure rate → UNVERIFIED regardless of replay count
  - Missing pins → UNVERIFIED
  - Disputes → UNVERIFIED
- [x] `TierAssigner.compute_expiry()` returns correct expiry dates (90 days BACKTESTED, 180 days PROVEN, None UNVERIFIED)
- [x] `ConstraintYieldingGate.resolve_review_preference()`:
  - UNVERIFIED + skip → full
  - UNVERIFIED + full → full
  - BACKTESTED + skip → skip
  - PROVEN + skip → skip

**Tests:** `tests/theatre/test_certificate.py`, `tests/theatre/test_tier_assigner.py`, `tests/theatre/test_constraint_gate.py` — all boundary conditions, expiry computation, constraint gate passthrough vs override.

---

### Sprint 2 Success Criteria

- ReplayEngine completes full lifecycle with mock adapter
- Dataset hash mismatch correctly halts execution
- >20% failure rate caps certificate at UNVERIFIED
- Resolution state machine follows escalation paths
- Evidence bundle passes minimum-file validation
- Tier assignment correct at all boundary conditions
- Constraint yielding gate blocks UNVERIFIED + skip
- All unit tests passing

---

## Sprint 3: API Layer + Integration

> Global ID: sprint-27 | Local ID: sprint-3
> Goal: Wire the engine to FastAPI — routes, schemas, background task bridge, test fixtures, and end-to-end integration tests.
> Depends on: Sprint 2 (replay engine, certificate, tier assigner, evidence bundle)

### Tasks

#### T3.1: Pydantic Request/Response Schemas
**Description:** Implement all request and response schemas in `backend/schemas/theatre.py`. Follows existing pattern from `backend/schemas/verification.py`.

**Acceptance Criteria:**
- [x] `TheatreCreate` — template_json field with model_validator
- [x] `TheatreRunRequest` — ground_truth_path override, is_certificate_run flag
- [x] `TheatreResponse` — full Theatre state view with `ConfigDict(from_attributes=True)`
- [x] `CommitmentReceiptResponse` — public receipt
- [x] `TheatreCertificateResponse` — full certificate with all fields
- [x] `TheatreCertificateSummaryResponse` — list view
- [x] `TheatreListResponse`, `CertificateListResponse`, `TemplateListResponse` — paginated
- [x] `TemplateResponse` — template metadata

**Tests:** Schema serialisation/deserialisation, ORM compatibility (`from_attributes`).

---

#### T3.2: Theatre Bridge Service
**Description:** Implement `backend/services/theatre_bridge.py`. Background task executing full Theatre lifecycle. Follows exact pattern from `verification_bridge.py`: graceful import, fresh session per task, guaranteed terminal state.

**Acceptance Criteria:**
- [x] Graceful import with `THEATRE_ENGINE_AVAILABLE` flag
- [x] `run_theatre_task(theatre_id)` background task
- [x] Fresh session per task (not shared with request)
- [x] State transitions: COMMITTED → ACTIVE → SETTLING → RESOLVED
- [x] Dataset hash verification before execution
- [x] ReplayEngine invocation with progress callback
- [x] Certificate + episode scores persisted to DB
- [x] Theatre updated with certificate_id on completion
- [x] Guaranteed terminal state (error → state remains at failure point with error message)
- [x] Error strings capped at 2000 chars

**Tests:** `tests/backend/test_theatre_bridge.py` — successful lifecycle, failure handling, graceful import when engine unavailable.

---

#### T3.3: Theatre API Routes
**Description:** Implement all 12 endpoints in `backend/api/theatre_routes.py`. Mount in `backend/main.py` with try/except pattern.

**Acceptance Criteria:**
- [x] `POST /api/v1/theatres` — validates template, creates DRAFT Theatre, returns ID + state
- [x] `POST /api/v1/theatres/{id}/commit` — generates commitment hash, transitions to COMMITTED
- [x] `POST /api/v1/theatres/{id}/run` — launches background task, transitions to ACTIVE (Replay only)
- [x] `GET /api/v1/theatres/{id}` — returns Theatre state + progress (auth: owner only)
- [x] `GET /api/v1/theatres/{id}/commitment` — returns CommitmentReceipt (public)
- [x] `POST /api/v1/theatres/{id}/settle` — manual settle (Market only, returns 400 for Replay)
- [x] `GET /api/v1/theatres/{id}/certificate` — returns certificate (public, 404 if not RESOLVED)
- [x] `GET /api/v1/theatres/{id}/replay` — RLMF export data (public, 404 if not RESOLVED)
- [x] `GET /api/v1/templates` — paginated list
- [x] `GET /api/v1/templates/{template_id}` — single template
- [x] `GET /api/v1/certificates/{certificate_id}` — single certificate (public)
- [x] `GET /api/v1/certificates?construct_id={id}` — filtered list (public)
- [x] Auth: `Depends(get_current_user)` on create/commit/run/settle/get-theatre; public on commitment/certificate/replay/templates
- [x] Router mounted in `main.py` with try/except import

**Tests:** `tests/backend/test_theatre_routes.py` — each endpoint, auth enforcement, 404 handling, pagination, state validation (can't run before commit, can't commit twice).

---

#### T3.4: Test Fixtures
**Description:** Create three Product Theatre template fixtures (Observer, Easel, Cartograph) with sample ground truth data for integration tests.

**Acceptance Criteria:**
- [x] `theatre/fixtures/product_observer_v1.json` — valid template with criteria_ids `["source_fidelity", "signal_classification", "canvas_enrichment_freshness"]`, HTTP adapter
- [x] `theatre/fixtures/product_easel_v1.json` — valid template with criteria_ids `["vocabulary_adherence", "tdr_propagation_fidelity", "downstream_compliance"]`, construct_chain (3 constructs), HITL rubric step
- [x] `theatre/fixtures/product_cartograph_v1.json` — valid template with criteria_ids `["isometric_convention_compliance", "hex_grid_accuracy", "detail_density_adherence"]`
- [x] All three pass TemplateValidator (schema + runtime rules)
- [x] Sample ground truth datasets: `observer_provenance.jsonl` (≥5 episodes), `easel_tdr_records.jsonl` (≥5), `cartograph_grid_reference.jsonl` (≥5)
- [x] Pre-computed commitment hashes for determinism verification
- [x] Mock construct responses for CI testing

**Tests:** Fixture loading, template validation, commitment hash determinism (pre-computed matches computed).

---

#### T3.5: End-to-End Integration Tests
**Description:** Integration tests covering the full lifecycle: create Theatre → commit → run → verify certificate. Uses MockOracleAdapter with `is_certificate_run=False`.

**Acceptance Criteria:**
- [x] Test: create DRAFT → commit → verify commitment hash → run with mock → check RESOLVED state → verify certificate fields
- [x] Test: Observer fixture end-to-end lifecycle
- [x] Test: Easel fixture with compositional chain (3 version pins verified in commitment)
- [x] Test: Cartograph fixture (low scores for stub skills)
- [x] Test: commitment hash reproducibility (same inputs → identical hash across runs)
- [x] Test: evidence bundle validation after completion
- [x] Test: invalid state transitions rejected at API level (e.g., run before commit)
- [x] Test: >20% failure rate produces UNVERIFIED tier

**Tests:** `tests/theatre/test_integration.py` — full lifecycle tests covering all three fixtures and edge cases.

---

### Sprint 3 Success Criteria

- All 12 API endpoints functional and tested
- Background task executes full Theatre lifecycle
- Three test fixtures pass template validation and produce certificates
- Commitment hash reproducibility verified across runs
- Evidence bundles pass minimum-file validation
- End-to-end: create → commit → run → certificate works for all three fixtures
- Auth enforcement correct (protected vs public endpoints)
- All tests passing

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| Canonical JSON divergence | 1 | Extensive float normalisation tests, round-trip property tests |
| echelon-verify import failures | 2, 3 | Graceful import pattern; MockOracleAdapter for all tests |
| Large evidence bundles | 2 | Hash references; ground_truth stored by path not inline |
| Schema backward compat | 1 | Template validation uses additive fields only |
| Background task failures | 3 | Guaranteed terminal state pattern from verification_bridge.py |

---

## Dependencies

```
T1.7 (scaffolding) ← blocks all other tasks
T1.2 (canonical_json) ← T1.3 (commitment)
T1.4 (criteria) ← T1.5 (template validator)
T1.1–T1.6 (Sprint 1) ← T2.1–T2.6 (Sprint 2)
T2.1–T2.6 (Sprint 2) ← T3.1–T3.5 (Sprint 3)
T3.1 (schemas) + T3.2 (bridge) ← T3.3 (routes)
T3.4 (fixtures) ← T3.5 (integration tests)
```
