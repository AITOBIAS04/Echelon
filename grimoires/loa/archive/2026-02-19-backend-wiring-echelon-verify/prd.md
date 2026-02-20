# PRD: Backend Wiring — echelon-verify Integration

> Version: 1.0 | Author: AI Engineer | Date: 2026-02-19

## 1. Problem Statement

The `echelon-verify` package (cycle-027) is a standalone verification pipeline that scores community oracle constructs against GitHub ground truth. It currently operates as an independent CLI/API service with its own filesystem-based storage (`data/` JSONL files) and in-memory job tracking.

**The gap**: echelon-verify is not integrated into the Echelon backend. Verification runs are ephemeral (lost on restart), certificates live only on the local filesystem, and there is no way for the frontend to trigger or display verification results through the existing API.

This cycle wires echelon-verify into the FastAPI backend — adding SQLAlchemy models for persistence, API routes for triggering and querying verification, and async task execution for long-running pipeline jobs.

> Sources: backend/main.py (router pattern), backend/database/models.py (ORM conventions), verification/src/echelon_verify/ (pipeline interfaces)

## 2. Goals & Success Metrics

### Goals

1. **Persist verification data in PostgreSQL** — verification runs, replay scores, and calibration certificates survive restarts and are queryable via SQL.
2. **Expose verification API** — frontend and external consumers can trigger verification runs, poll status, and retrieve certificates through the existing FastAPI app.
3. **Async task execution** — verification pipeline runs as a background `asyncio.create_task()`, not blocking the API response and not coupled to the game loop.
4. **Follow existing backend patterns** — use the same SQLAlchemy 2.0 Mapped syntax, router mounting with try-except, hybrid auth via `get_user_or_wallet`, and Alembic migration flow.

### Success Metrics

| Metric | Target |
|--------|--------|
| Verification run persistence | Runs survive backend restart |
| Certificate queryability | Certificates retrievable by ID, by construct, with pagination |
| API response time (trigger) | < 200ms for POST /verify (returns job ID immediately) |
| Pipeline execution | Runs asynchronously without blocking other API requests |
| Auth integration | Protected endpoints use existing `get_user_or_wallet` dependency |
| Migration | `alembic upgrade head` creates verification tables cleanly |

## 3. User Context

### Primary User: Frontend Application

The Echelon frontend needs to:
- Trigger a verification run for a given oracle construct + GitHub repo
- Poll verification progress (X of Y replays completed)
- Display completed certificates (composite score, Brier, per-metric breakdown)
- List all certificates for a construct or across the platform

### Secondary User: Platform Operators

Operators need to:
- Query verification history via SQL for analytics
- Inspect failed runs and partial certificates
- View verification job status across all users

## 4. Functional Requirements

### FR-1: SQLAlchemy Models

Add three models to `backend/database/models.py`:

#### FR-1.1: `VerificationRun` model

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | String(50) | PK | UUID4 |
| `user_id` | String(50) | FK → users.id, index | Who triggered it |
| `construct_id` | String(255) | index | Oracle being verified |
| `repo_url` | String(500) | not null | GitHub repo URL |
| `status` | Enum | not null | PENDING, INGESTING, INVOKING, SCORING, CERTIFYING, COMPLETED, FAILED |
| `progress` | Integer | default 0 | Replays completed |
| `total` | Integer | default 0 | Total replays |
| `error` | Text | nullable | Error message on failure |
| `certificate_id` | String(50) | FK → certificates.id, nullable | Links to result |
| `config_json` | JSON | not null | PipelineConfig snapshot |
| `created_at` | DateTime | not null | |
| `updated_at` | DateTime | not null, onupdate | |

Indexes: `(status)`, `(user_id, created_at)`, `(construct_id)`

#### FR-1.2: `VerificationCertificate` model

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | String(50) | PK | UUID4 (= certificate_id from echelon-verify) |
| `construct_id` | String(255) | index | Oracle construct |
| `domain` | String(50) | not null | Always "community_oracle" |
| `replay_count` | Integer | not null | Number of successful replays |
| `precision` | Float | not null | [0, 1] |
| `recall` | Float | not null | [0, 1] |
| `reply_accuracy` | Float | not null | [0, 1] |
| `composite_score` | Float | not null | [0, 1] |
| `brier` | Float | not null | [0, 0.5] |
| `sample_size` | Integer | not null | |
| `ground_truth_source` | String(500) | not null | Repo URL |
| `commit_range` | String(255) | not null | |
| `methodology_version` | String(20) | not null | Prompt version |
| `scoring_model` | String(100) | not null | Claude model used |
| `raw_scores_json` | JSON | nullable | Individual ReplayScore array |
| `created_at` | DateTime | not null | |

Indexes: `(construct_id, created_at)`, `(brier)`

#### FR-1.3: `VerificationReplayScore` model

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | String(50) | PK | UUID4 |
| `certificate_id` | String(50) | FK → certificates.id, index | Parent certificate |
| `ground_truth_id` | String(255) | not null | PR ID |
| `precision` | Float | not null | |
| `recall` | Float | not null | |
| `reply_accuracy` | Float | not null | |
| `claims_total` | Integer | not null | |
| `claims_supported` | Integer | not null | |
| `changes_total` | Integer | not null | |
| `changes_surfaced` | Integer | not null | |
| `scoring_model` | String(100) | not null | |
| `scoring_latency_ms` | Integer | not null | |
| `scored_at` | DateTime | not null | |

Index: `(certificate_id)`

### FR-2: Alembic Migration

- Create a migration that adds `verification_runs`, `verification_certificates`, and `verification_replay_scores` tables.
- Migration must be reversible (downgrade drops tables).
- Compatible with both PostgreSQL (production) and SQLite (development/testing).

### FR-3: API Routes

Create `backend/api/verification_routes.py` with router prefix `/api/v1/verification`.

#### FR-3.1: `POST /api/v1/verification/runs`

Trigger a new verification run.

- **Auth**: Required (`get_user_or_wallet`)
- **Request body**: `{ repo_url, construct_id, oracle_config, limit?, min_replays? }`
- **Response**: `{ run_id, status: "pending", created_at }`
- **Behavior**: Creates `VerificationRun` in DB, launches `asyncio.create_task()` for pipeline, returns immediately.

#### FR-3.2: `GET /api/v1/verification/runs/{run_id}`

Get status of a verification run.

- **Auth**: Required
- **Response**: `{ run_id, status, progress, total, error?, certificate_id?, created_at, updated_at }`
- **Auth check**: User can only see their own runs (or admin sees all).

#### FR-3.3: `GET /api/v1/verification/runs`

List verification runs for current user.

- **Auth**: Required
- **Query params**: `status?`, `construct_id?`, `limit=20`, `offset=0`
- **Response**: Paginated list of runs.

#### FR-3.4: `GET /api/v1/verification/certificates/{cert_id}`

Get a specific certificate with full details.

- **Auth**: None (certificates are public)
- **Response**: Full certificate data including individual replay scores.

#### FR-3.5: `GET /api/v1/verification/certificates`

List certificates.

- **Auth**: None (certificates are public)
- **Query params**: `construct_id?`, `limit=20`, `offset=0`, `sort=brier_asc`
- **Response**: Paginated list of certificates (without individual scores for list view).

### FR-4: Background Task Execution

The verification pipeline must run as an async background task:

- Use `asyncio.create_task()` — same pattern as the game loop startup.
- The task receives the `VerificationRun.id` and constructs the pipeline internally.
- Progress updates write directly to the `verification_runs` row (`progress`, `total`, `status`).
- On completion: create `VerificationCertificate` + `VerificationReplayScore` rows, link certificate to run.
- On failure: set `status = FAILED`, write error message.
- A DB session is created per-task (not shared with the request session).

### FR-5: echelon-verify Bridge

Create a thin bridge layer that:

- Constructs `PipelineConfig` from API request params
- Creates `OracleAdapter` and `ScoringProvider` from config
- Wraps the `VerificationPipeline.run()` call
- Converts `CalibrationCertificate` (Pydantic) → `VerificationCertificate` (SQLAlchemy)
- Converts `ReplayScore` (Pydantic) → `VerificationReplayScore` (SQLAlchemy)

This bridge keeps echelon-verify decoupled from SQLAlchemy.

## 5. Non-Functional Requirements

### NFR-1: Database Compatibility

Models must work with both PostgreSQL (production via asyncpg) and SQLite (local dev). Avoid PostgreSQL-only types (like `ARRAY`) — use `JSON` for array-like data.

### NFR-2: No Game Loop Coupling

Verification runs are triggered via API only. The game loop (`backend/worker/game_loop.py`) is not modified and does not interact with verification.

### NFR-3: Graceful Degradation

If echelon-verify is not installed, the verification router should fail to import gracefully (try-except pattern in `main.py`), and the rest of the app continues normally.

### NFR-4: Auth Consistency

Use the existing `get_user_or_wallet` dependency for protected endpoints. Do not introduce a new auth mechanism.

### NFR-5: Existing Test Compatibility

Changes to `backend/database/models.py` must not break existing tests. New models are additive only.

## 6. Scope

### In Scope

- SQLAlchemy models for verification persistence
- Alembic migration
- API routes mounted in main.py
- Background async task execution via `asyncio.create_task()`
- Bridge layer between echelon-verify Pydantic models and SQLAlchemy models

### Out of Scope

- Game loop integration
- Frontend UI for verification
- Rate limiting on verification endpoints (can be added later)
- WebSocket for real-time progress updates (polling via GET is sufficient)
- Multi-tenant isolation (all certificates are public for now)
- Scheduler for periodic re-verification

## 7. Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| echelon-verify import fails in backend context | Medium | High | Try-except on router import; bridge layer isolates dependency |
| Long-running tasks exhaust DB connections | Low | Medium | Create session per-task, close on completion |
| SQLite doesn't support all PostgreSQL features | Low | Medium | Avoid ARRAY type, use JSON instead |
| Pipeline failure leaves run in RUNNING state | Medium | Medium | Catch all exceptions in task, always set terminal status |

### Dependencies

- `echelon-verify` package (cycle-027) must be installed in the backend's Python environment
- `ANTHROPIC_API_KEY` must be set for scoring
- GitHub token needed for private repos (passed per-request)
