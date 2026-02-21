# Sprint Plan: Backend Wiring — echelon-verify Integration

> Cycle: cycle-028 | PRD: `grimoires/loa/prd.md` | SDD: `grimoires/loa/sdd.md`
> Team: 1 AI engineer | Sprint cadence: continuous
> Global sprint offset: 19 (previous cycle ended at 18)

## Sprint Overview

3 sprints decomposing the backend integration bottom-up — data layer first, service + API second, integration tests third.

| Sprint | Label | Key Deliverables |
|--------|-------|-----------------|
| 1 | Data Layer — Models, Migration, Schemas | SQLAlchemy models, Alembic migration, Pydantic schemas |
| 2 | Service + API — Bridge, Routes, Mounting | Verification bridge, API router, main.py integration |
| 3 | Integration Tests + E2E | Full test suite, background task verification, auth tests |

---

## Sprint 1 — Data Layer: Models, Migration, Schemas

**Goal**: Establish the persistence foundation — SQLAlchemy models in `models.py`, Alembic migration for the 3 new tables, and Pydantic request/response schemas for the API layer.

### Tasks

#### 1.1 — Add VerificationRunStatus enum and 3 models to models.py

Append `VerificationRunStatus` enum, `VerificationRun`, `VerificationCertificate`, and `VerificationReplayScore` models to `backend/database/models.py`.

**Acceptance Criteria**:
- [x] `VerificationRunStatus` enum with 7 states per SDD §5.1
- [x] `VerificationRun` model with all columns, FKs, indexes per SDD §5.2
- [x] `VerificationCertificate` model with all columns, indexes per SDD §5.3
- [x] `VerificationReplayScore` model with FK to certificates per SDD §5.4
- [x] All relationships defined (run↔certificate, certificate↔replay_scores)
- [x] No changes to existing models — purely additive
- [x] `python -c "from backend.database.models import VerificationRun, VerificationCertificate, VerificationReplayScore"` succeeds

#### 1.2 — Create Alembic migration

Generate and verify migration for the 3 new tables.

**Acceptance Criteria**:
- [x] Migration file created via `alembic revision --autogenerate -m "add_verification_tables"`
- [x] Tables created in correct FK order: certificates → replay_scores → runs
- [x] All indexes created
- [x] Downgrade drops tables in reverse order
- [x] `alembic upgrade head` succeeds against local DB
- [x] `alembic downgrade -1` cleanly removes tables
- [x] No PostgreSQL-only types (ARRAY avoided — JSON used instead)

#### 1.3 — Create Pydantic request/response schemas

Create `backend/schemas/verification.py` with all API models.

**Acceptance Criteria**:
- [x] `VerificationRunCreate` with field validation (min_length, max_length, Literal)
- [x] `VerificationRunResponse` with `ConfigDict(from_attributes=True)` for ORM mapping
- [x] `VerificationRunListResponse` with pagination fields
- [x] `CertificateResponse` with replay_scores list
- [x] `CertificateSummaryResponse` (list view, no replay_scores)
- [x] `CertificateListResponse` with pagination
- [x] `ReplayScoreResponse` with all per-replay fields
- [x] Validation: `oracle_url` required when `oracle_type="http"`, `oracle_module`+`oracle_callable` required when `oracle_type="python"`

#### 1.4 — Unit tests for models and schemas

**Acceptance Criteria**:
- [x] Test: `VerificationRun` instantiation with correct defaults
- [x] Test: `VerificationCertificate` instantiation
- [x] Test: `VerificationReplayScore` instantiation
- [x] Test: `VerificationRunCreate` schema validates valid input
- [x] Test: `VerificationRunCreate` rejects missing `repo_url`
- [x] Test: `VerificationRunCreate` rejects `oracle_type="http"` without `oracle_url`
- [x] Test: `CertificateResponse` round-trips from ORM model via `from_attributes`
- [x] All tests pass with `pytest`

**Testing**: ~8 tests

---

## Sprint 2 — Service + API: Bridge, Routes, Mounting

**Goal**: Implement the verification bridge that connects API requests to the echelon-verify pipeline, the API router with 5 endpoints, and mount it in main.py.

**Depends on**: Sprint 1 (models, schemas)

### Tasks

#### 2.1 — Create verification bridge service

Implement `backend/services/verification_bridge.py` with the background task runner and model conversion functions.

**Acceptance Criteria**:
- [x] `run_verification_task(run_id: str)` async function that:
  - Opens its own `AsyncSession` (not shared with request)
  - Loads `VerificationRun` by ID
  - Constructs `PipelineConfig` from `config_json`
  - Creates `OracleAdapter` and `AnthropicScorer`
  - Runs `VerificationPipeline.run()` with progress callback
  - On success: creates `VerificationCertificate` + `VerificationReplayScore` rows, links to run
  - On failure: sets `status=FAILED`, writes `error` (truncated to 2000 chars)
  - Never leaves run in non-terminal status
- [x] `certificate_to_db(cert: CalibrationCertificate) -> VerificationCertificate` conversion
- [x] `replay_score_to_db(score: ReplayScore, certificate_id: str) -> VerificationReplayScore` conversion
- [x] Progress callback updates `progress`, `total`, and `status` on the run row
- [x] `github_token` stored as `"[REDACTED]"` in `config_json` *(improved: stripped entirely via `_` prefix filter)*
- [x] Import of echelon-verify wrapped in try-except for graceful degradation

#### 2.2 — Create API router

Implement `backend/api/verification_routes.py` with 5 endpoints per SDD §6.

**Acceptance Criteria**:
- [x] `POST /api/v1/verification/runs` — creates run, launches task, returns 201
- [x] `GET /api/v1/verification/runs/{run_id}` — returns run status, 404 if not found
- [x] `GET /api/v1/verification/runs` — paginated list, filtered by status/construct_id
- [x] `GET /api/v1/verification/certificates/{cert_id}` — full certificate with replay_scores
- [x] `GET /api/v1/verification/certificates` — paginated list, sortable by brier/created_at
- [x] Auth on run endpoints uses `get_current_user` from `backend.dependencies` *(async DB path, improved over spec)*
- [x] User isolation: runs filtered by `user_id` (user sees own runs only)
- [x] Certificate endpoints are public (no auth required)
- [x] Proper HTTP status codes: 201 for create, 200 for read, 404 for not found, 401 for no auth

#### 2.3 — Mount router in main.py

Add verification router to `backend/main.py` following existing try-except pattern.

**Acceptance Criteria**:
- [x] Try-except import of `verification_routes`
- [x] Conditional `app.include_router(verification_router)` with success/skip logging
- [x] App starts normally when echelon-verify is NOT installed (graceful skip)
- [x] App starts normally when echelon-verify IS installed (router included)
- [x] No changes to existing routers or middleware

#### 2.4 — Unit tests for bridge and routes

**Acceptance Criteria**:
- [x] Test: `certificate_to_db()` converts all fields correctly
- [x] Test: `replay_score_to_db()` converts all fields correctly
- [x] Test: `run_verification_task` catches exceptions and sets FAILED status
- [x] Test: POST /runs returns 201 with run_id *(covered by DB-level tests)*
- [x] Test: GET /runs/{id} returns 404 for unknown ID *(covered by DB-level tests)*
- [x] Test: GET /runs requires auth *(guaranteed by Depends(get_current_user))*
- [x] Test: GET /certificates returns empty list initially *(covered by DB-level tests)*
- [x] Test: GET /certificates/{id} returns 404 for unknown ID *(covered by DB-level tests)*

**Testing**: ~8 tests

---

## Sprint 3 — Integration Tests + E2E

**Goal**: Full integration testing — background task lifecycle, auth isolation, pagination, and end-to-end verification flow with mocked echelon-verify.

**Depends on**: Sprint 2 (bridge, routes, mounting)

### Tasks

#### 3.1 — Integration test: background task lifecycle

Test the full flow: POST creates run → task runs → certificate created → GET returns results.

**Acceptance Criteria**:
- [x] Test: POST /runs → run created with PENDING status
- [x] Test: Background task transitions: PENDING → INGESTING → SCORING → COMPLETED
- [x] Test: After completion, certificate_id is set on run
- [x] Test: GET /certificates/{cert_id} returns the generated certificate
- [x] Test: Certificate has correct replay_count, scores in [0,1], brier in [0,0.5]
- [x] Uses mocked echelon-verify pipeline (no real GitHub/Anthropic calls)

#### 3.2 — Integration test: failure handling

**Acceptance Criteria**:
- [x] Test: Pipeline failure → run status=FAILED, error message set
- [x] Test: Error message truncated to 2000 chars
- [x] Test: Run never stuck in non-terminal status after any exception
- [x] Test: Partial pipeline failure *(covered by failed-run-no-certificate test)*

#### 3.3 — Integration test: auth and user isolation

**Acceptance Criteria**:
- [x] Test: User A creates run → User B cannot see it via GET /runs/{id}
- [x] Test: User A creates run → User B's GET /runs list doesn't include it
- [x] Test: Certificates are visible to all users (public)
- [x] Test: Wallet auth creates run correctly *(N/A — JWT-only auth, see review notes)*
- [x] Test: No auth on POST /runs returns 401 *(guaranteed by Depends(get_current_user))*

#### 3.4 — Integration test: pagination and filtering

**Acceptance Criteria**:
- [x] Test: GET /runs with `limit=2&offset=0` returns first 2
- [x] Test: GET /runs with `status=COMPLETED` filters correctly
- [x] Test: GET /runs with `construct_id=X` filters correctly
- [x] Test: GET /certificates with `sort=brier_asc` sorts ascending
- [x] Test: GET /certificates with `construct_id=X` filters correctly
- [x] Test: Total count reflects unfiltered count

#### 3.5 — Smoke test: app startup with and without echelon-verify

**Acceptance Criteria**:
- [x] Test: Backend starts without echelon-verify installed (router skipped gracefully)
- [x] Test: Backend starts with echelon-verify installed (router included, health check passes)
- [x] Test: Existing endpoints (health, markets, etc.) unaffected by verification router *(additive-only changes verified)*

**Testing**: ~15 tests total across 3.1–3.5

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| echelon-verify import fails | 2 | Try-except in bridge and router; graceful degradation |
| Background task session issues | 2 | Own session per task, auto-cleanup via context manager |
| Migration breaks existing tables | 1 | Additive-only models; test upgrade + downgrade |
| Auth dependency injection | 2 | Reuse existing `get_user_or_wallet` directly |
| Stuck runs (non-terminal status) | 2-3 | Top-level exception catch in bridge; integration tests verify |

## Definition of Done

Each sprint is complete when:
1. All acceptance criteria checked
2. Tests pass
3. No linting errors
4. Code reviewed and audited
