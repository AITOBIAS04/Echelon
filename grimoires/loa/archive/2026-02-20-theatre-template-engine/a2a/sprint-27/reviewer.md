# Implementation Report — Sprint 27 (API Layer + Integration)

> Sprint: sprint-27 (global) | sprint-3 (local)
> Cycle: cycle-031 — Theatre Template Engine
> Date: 2026-02-20

## Summary

Sprint 3 wires the Theatre Template Engine to FastAPI — implementing Pydantic schemas, a background task bridge service, 12 API endpoints across 3 routers, 3 Product Theatre template fixtures with ground truth datasets, and comprehensive integration tests covering the full lifecycle.

## Tasks Completed

### T3.1: Pydantic Request/Response Schemas ✅

**File:** `backend/schemas/theatre.py`

- `TheatreCreate` — request body with `template_json` field + `@model_validator(mode="after")` enforcing `theatre_id` and `execution_path` presence
- `TheatreRunRequest` — optional `ground_truth_path` override and `is_certificate_run` flag
- `TheatreSettleRequest` — market settlement data (Market theatres only)
- `TemplateResponse` + `TemplateListResponse` — template metadata with pagination
- `CommitmentReceiptResponse` — public commitment receipt
- `TheatreResponse` + `TheatreListResponse` — full theatre state view with pagination
- `TheatreCertificateResponse` — all certificate fields (30+ fields)
- `TheatreCertificateSummaryResponse` + `CertificateListResponse` — compact list view with pagination
- All response models use `ConfigDict(from_attributes=True)` for ORM compatibility

### T3.2: Theatre Bridge Service ✅

**File:** `backend/services/theatre_bridge.py`

- Graceful import with `THEATRE_ENGINE_AVAILABLE` flag — matches `verification_bridge.py` pattern
- `run_theatre_task(theatre_id)` async background task
- Fresh session per task via `get_session()` context manager
- State transitions: COMMITTED → ACTIVE → SETTLING → RESOLVED
- ReplayEngine invocation with async progress callback
- Certificate + episode scores persisted to DB
- Theatre updated with certificate_id on completion
- Guaranteed terminal state — outer `try/except Exception` with error string capped at 2000 chars
- Inner `try/except` around error persistence to prevent double-fault
- `_update_theatre_progress()` and `_transition_theatre_state()` helpers with fresh sessions

### T3.3: Theatre API Routes ✅

**File:** `backend/api/theatre_routes.py`

12 endpoints across 3 routers:

| # | Endpoint | Method | Auth | Router |
|---|----------|--------|------|--------|
| 1 | `/api/v1/theatres` | POST | Yes | theatre |
| 2 | `/api/v1/theatres/{id}/commit` | POST | Yes | theatre |
| 3 | `/api/v1/theatres/{id}/run` | POST | Yes | theatre |
| 4 | `/api/v1/theatres/{id}` | GET | Yes | theatre |
| 5 | `/api/v1/theatres/{id}/commitment` | GET | Public | theatre |
| 6 | `/api/v1/theatres/{id}/settle` | POST | Yes | theatre |
| 7 | `/api/v1/theatres/{id}/certificate` | GET | Public | theatre |
| 8 | `/api/v1/theatres/{id}/replay` | GET | Public | theatre |
| 9 | `/api/v1/templates` | GET | Public | templates |
| 10 | `/api/v1/templates/{id}` | GET | Public | templates |
| 11 | `/api/v1/certificates/{id}` | GET | Public | certificates |
| 12 | `/api/v1/certificates` | GET | Public | certificates |

- Template validation via `TemplateValidator` (graceful import with fallback)
- Commitment hash computation via `CommitmentProtocol`
- State enforcement: can't run before commit, can't commit twice, market-only settle
- Background task launch via `asyncio.create_task(run_theatre_task(...))`
- Audit events on create, commit, settle
- `_get_user_theatre()` helper enforces owner-only access
- Mounted in `backend/main.py` with try/except import pattern (3 routers)

### T3.4: Test Fixtures ✅

**Template fixtures** (all pass TemplateValidator — schema + 8 runtime rules):

| Fixture | File | Criteria | Adapter | Special |
|---------|------|----------|---------|---------|
| Observer | `theatre/fixtures/product_observer_v1.json` | source_fidelity, signal_classification, canvas_enrichment_freshness | mock (HTTP) | Single construct |
| Easel | `theatre/fixtures/product_easel_v1.json` | vocabulary_adherence, tdr_propagation_fidelity, downstream_compliance | mock | 3-construct chain, HITL rubric step |
| Cartograph | `theatre/fixtures/product_cartograph_v1.json` | isometric_convention_compliance, hex_grid_accuracy, detail_density_adherence | mock | Deterministic computation step |

**Ground truth datasets** (≥5 episodes each):
- `theatre/fixtures/observer_provenance.jsonl` — 5 OSINT provenance events
- `theatre/fixtures/easel_tdr_records.jsonl` — 5 TDR threat detection records
- `theatre/fixtures/cartograph_grid_reference.jsonl` — 5 hex grid rendering episodes

**Fixture loader** (`theatre/fixtures/__init__.py`):
- `load_template(name)` — loads JSON template by name
- `load_ground_truth(name)` — loads JSONL and returns `list[GroundTruthEpisode]`
- Constants for all fixture names

### T3.5: End-to-End Integration Tests ✅

**File:** `tests/theatre/test_integration.py` — 18 tests

| Test Class | Tests | Covers |
|-----------|-------|--------|
| TestObserverLifecycle | 2 | Full lifecycle, certificate field verification |
| TestEaselLifecycle | 2 | Full lifecycle, 3 version pins in commitment |
| TestCartographLifecycle | 2 | Full lifecycle, stub score presence |
| TestCommitmentReproducibility | 2 | Same inputs → same hash, different inputs → different hash |
| TestEvidenceBundle | 1 | Full bundle creation + minimum files validation |
| TestStateTransitionEnforcement | 4 | Cannot run before commit, cannot commit twice, cannot skip settling, cannot reverse |
| TestTierAssignmentIntegration | 2 | Mock run → tier, high failure rate → UNVERIFIED |
| TestResolutionProgrammeIntegration | 3 | Observer (2 steps), Easel (HITL → PENDING_HITL), Cartograph (3 steps) |

**File:** `tests/theatre/test_fixtures.py` — 23 tests

| Test Class | Tests | Covers |
|-----------|-------|--------|
| TestTemplateLoading | 3 | All 3 templates load |
| TestTemplateValidation | 7 | Schema + runtime validation, mock rejection, weight sums |
| TestGroundTruthLoading | 6 | All 3 JSONL files load, episode ID uniqueness |
| TestCommitmentHashDeterminism | 4 | Determinism per template, cross-template uniqueness |
| TestCriteriaModelCompatibility | 3 | TheatreCriteria creation from fixture data |

## Test Results

```
253 passed, 0 failed (166.34s)
```

- Sprint 1 tests: 113 (unchanged)
- Sprint 2 tests: 99 (unchanged)
- Sprint 3 tests: 41 (23 fixture + 18 integration)

## Files Created/Modified

### Created (14 files)
| File | LOC | Purpose |
|------|-----|---------|
| `backend/schemas/theatre.py` | 175 | Request/response Pydantic schemas |
| `backend/services/theatre_bridge.py` | 232 | Background task bridge service |
| `backend/api/theatre_routes.py` | 378 | 12 API endpoints across 3 routers |
| `theatre/fixtures/__init__.py` | 36 | Fixture loader module |
| `theatre/fixtures/product_observer_v1.json` | 76 | Observer template fixture |
| `theatre/fixtures/product_easel_v1.json` | 107 | Easel template fixture (compositional) |
| `theatre/fixtures/product_cartograph_v1.json` | 76 | Cartograph template fixture |
| `theatre/fixtures/observer_provenance.jsonl` | 5 | Observer ground truth (5 episodes) |
| `theatre/fixtures/easel_tdr_records.jsonl` | 5 | Easel ground truth (5 episodes) |
| `theatre/fixtures/cartograph_grid_reference.jsonl` | 5 | Cartograph ground truth (5 episodes) |
| `tests/theatre/test_fixtures.py` | 181 | 23 fixture tests |
| `tests/theatre/test_integration.py` | 374 | 18 integration tests |

### Modified (1 file)
| File | Change |
|------|--------|
| `backend/main.py` | Added theatre router imports (try/except) + router mounting (3 routers) |

## Architecture Notes

- **3-router split**: Theatre operations (`/api/v1/theatres`), templates (`/api/v1/templates`), and certificates (`/api/v1/certificates`) are separate routers for clean URL namespace and independent auth policies
- **Graceful degradation**: Both routes and bridge service handle missing engine imports — routes disable validation, bridge writes error to DB
- **Fresh sessions everywhere**: Bridge tasks never share sessions with HTTP requests, preventing long-lived transaction issues
- **Fixture quality**: All 3 templates pass both JSON Schema validation (v2.0.1) and all 8 runtime rules. Each exercises different template features: single construct (Observer), compositional chain with HITL (Easel), deterministic computation (Cartograph)
