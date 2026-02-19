# SDD: Backend Wiring — echelon-verify Integration

> Version: 1.0 | Date: 2026-02-19 | PRD: `grimoires/loa/prd.md`

## 1. Executive Summary

Wire the standalone `echelon-verify` package into the Echelon FastAPI backend. Three SQLAlchemy models persist verification data in PostgreSQL, five API routes expose verification to the frontend, and an async bridge layer runs the pipeline as a background task. No changes to the game loop or existing models.

## 2. System Architecture

```
┌─────────────────────────────────────────────────────┐
│  FastAPI Application (backend/main.py)              │
│                                                     │
│  ┌───────────────┐   ┌──────────────────────────┐   │
│  │ Existing       │   │ NEW: Verification Router │   │
│  │ Routers        │   │ /api/v1/verification     │   │
│  │ (markets,      │   │                          │   │
│  │  agents, etc.) │   │  POST /runs              │   │
│  └───────┬───────┘   │  GET  /runs              │   │
│          │            │  GET  /runs/{id}         │   │
│          │            │  GET  /certificates      │   │
│          │            │  GET  /certificates/{id} │   │
│          │            └──────────┬───────────────┘   │
│          │                       │                   │
│  ┌───────▼───────────────────────▼──────────────┐   │
│  │        SQLAlchemy 2.0 Async ORM              │   │
│  │  (connection.py — Base, async_session_maker)  │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                           │
│  ┌──────────────────────▼──────────────────────┐    │
│  │          PostgreSQL / SQLite                 │    │
│  │  verification_runs                          │    │
│  │  verification_certificates                  │    │
│  │  verification_replay_scores                 │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  NEW: Verification Bridge                    │    │
│  │  (backend/services/verification_bridge.py)   │    │
│  │                                             │    │
│  │  asyncio.create_task() ─►                   │    │
│  │    PipelineConfig → VerificationPipeline    │    │
│  │    CalibrationCertificate → DB models       │    │
│  │    Progress callback → UPDATE run row       │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                               │
└─────────────────────┼───────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │    echelon-verify       │
         │  (standalone package)   │
         │                        │
         │  VerificationPipeline  │
         │  GitHubIngester        │
         │  OracleAdapter         │
         │  AnthropicScorer       │
         │  CertificateGenerator  │
         └────────────────────────┘
```

## 3. Technology Stack

All choices follow existing backend conventions — no new dependencies beyond echelon-verify.

| Layer | Technology | Justification |
|-------|-----------|---------------|
| ORM | SQLAlchemy 2.0 (`Mapped`, `mapped_column`) | Matches `backend/database/models.py` |
| Async DB | asyncpg via `async_session_maker` | Matches `backend/database/connection.py` |
| Migration | Alembic (sync psycopg2) | Matches `backend/alembic/env.py` |
| API | FastAPI `APIRouter` | Matches existing router pattern |
| Auth | `get_user_or_wallet` dependency | Matches `backend/main.py` |
| Background tasks | `asyncio.create_task()` | Matches game loop pattern |
| Verification | `echelon-verify` package | Built in cycle-027 |

## 4. Component Design

### 4.1 New Files

| File | Purpose |
|------|---------|
| `backend/database/models.py` | Add 3 models + 1 enum (append to existing) |
| `backend/api/verification_routes.py` | API router with 5 endpoints |
| `backend/services/verification_bridge.py` | Bridge layer: API ↔ echelon-verify |
| `backend/schemas/verification.py` | Pydantic request/response models |
| `backend/alembic/versions/{hash}_add_verification_tables.py` | Migration |

### 4.2 Modified Files

| File | Change |
|------|--------|
| `backend/main.py` | Add try-except import + include_router for verification |

### 4.3 Unchanged

- `backend/worker/game_loop.py` — not touched
- `backend/database/connection.py` — not touched (reuse `Base`, `async_session_maker`, `get_session`)
- All existing models — not touched (new models are additive only)

## 5. Data Architecture

### 5.1 Enum: `VerificationRunStatus`

```python
class VerificationRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    INGESTING = "INGESTING"
    INVOKING = "INVOKING"
    SCORING = "SCORING"
    CERTIFYING = "CERTIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
```

### 5.2 Model: `VerificationRun`

Tracks a single pipeline execution.

```python
class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[VerificationRunStatus] = mapped_column(
        SQLEnum(VerificationRunStatus), default=VerificationRunStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("verification_certificates.id"), nullable=True
    )
    config_json: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    certificate: Mapped[Optional["VerificationCertificate"]] = relationship(
        back_populates="run"
    )

    __table_args__ = (
        Index("ix_verification_runs_status", "status"),
        Index("ix_verification_runs_user_created", "user_id", "created_at"),
        Index("ix_verification_runs_construct", "construct_id"),
    )
```

### 5.3 Model: `VerificationCertificate`

Stores the aggregate calibration certificate.

```python
class VerificationCertificate(Base):
    __tablename__ = "verification_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str] = mapped_column(String(50), default="community_oracle")
    replay_count: Mapped[int] = mapped_column(Integer)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    reply_accuracy: Mapped[float] = mapped_column(Float)
    composite_score: Mapped[float] = mapped_column(Float)
    brier: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    ground_truth_source: Mapped[str] = mapped_column(String(500))
    commit_range: Mapped[str] = mapped_column(String(255))
    methodology_version: Mapped[str] = mapped_column(String(20))
    scoring_model: Mapped[str] = mapped_column(String(100))
    raw_scores_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped[Optional["VerificationRun"]] = relationship(back_populates="certificate")
    replay_scores: Mapped[list["VerificationReplayScore"]] = relationship(
        back_populates="certificate"
    )

    __table_args__ = (
        Index("ix_verification_certs_construct_created", "construct_id", "created_at"),
        Index("ix_verification_certs_brier", "brier"),
    )
```

### 5.4 Model: `VerificationReplayScore`

Individual per-PR replay scores — child of certificate.

```python
class VerificationReplayScore(Base):
    __tablename__ = "verification_replay_scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    certificate_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("verification_certificates.id"), index=True
    )
    ground_truth_id: Mapped[str] = mapped_column(String(255))
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    reply_accuracy: Mapped[float] = mapped_column(Float)
    claims_total: Mapped[int] = mapped_column(Integer)
    claims_supported: Mapped[int] = mapped_column(Integer)
    changes_total: Mapped[int] = mapped_column(Integer)
    changes_surfaced: Mapped[int] = mapped_column(Integer)
    scoring_model: Mapped[str] = mapped_column(String(100))
    scoring_latency_ms: Mapped[int] = mapped_column(Integer)
    scored_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    certificate: Mapped["VerificationCertificate"] = relationship(
        back_populates="replay_scores"
    )
```

### 5.5 ER Diagram

```
users (existing)
  │
  │ 1:N
  ▼
verification_runs
  │
  │ 1:0..1
  ▼
verification_certificates
  │
  │ 1:N
  ▼
verification_replay_scores
```

## 6. API Design

### 6.1 Router Setup

```python
# backend/api/verification_routes.py
router = APIRouter(
    prefix="/api/v1/verification",
    tags=["verification"],
)
```

### 6.2 Endpoints

#### POST `/api/v1/verification/runs`

Start a new verification run.

**Auth**: Required (`get_user_or_wallet`)

**Request**:
```json
{
  "repo_url": "https://github.com/owner/repo",
  "construct_id": "my-oracle-v1",
  "oracle_type": "http",
  "oracle_url": "https://oracle.example.com/predict",
  "oracle_headers": {},
  "limit": 100,
  "min_replays": 50,
  "github_token": null
}
```

**Response** (201):
```json
{
  "run_id": "uuid4",
  "status": "PENDING",
  "created_at": "2026-02-19T16:00:00Z"
}
```

**Flow**:
1. Validate request
2. Create `VerificationRun` row with status=PENDING
3. Commit to DB
4. Launch `asyncio.create_task(run_verification_task(run_id))`
5. Return 201 with run_id

#### GET `/api/v1/verification/runs/{run_id}`

Get verification run status.

**Auth**: Required (user sees own runs only)

**Response** (200):
```json
{
  "run_id": "uuid4",
  "status": "SCORING",
  "progress": 35,
  "total": 100,
  "construct_id": "my-oracle-v1",
  "repo_url": "https://github.com/owner/repo",
  "error": null,
  "certificate_id": null,
  "created_at": "2026-02-19T16:00:00Z",
  "updated_at": "2026-02-19T16:05:00Z"
}
```

#### GET `/api/v1/verification/runs`

List verification runs for current user.

**Auth**: Required

**Query params**: `status`, `construct_id`, `limit` (default 20), `offset` (default 0)

**Response** (200):
```json
{
  "runs": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### GET `/api/v1/verification/certificates/{cert_id}`

Get certificate with replay scores.

**Auth**: None (public)

**Response** (200):
```json
{
  "id": "uuid4",
  "construct_id": "my-oracle-v1",
  "domain": "community_oracle",
  "replay_count": 87,
  "precision": 0.82,
  "recall": 0.75,
  "reply_accuracy": 0.79,
  "composite_score": 0.787,
  "brier": 0.107,
  "sample_size": 87,
  "ground_truth_source": "https://github.com/owner/repo",
  "methodology_version": "v1",
  "scoring_model": "claude-sonnet-4-6",
  "created_at": "2026-02-19T16:30:00Z",
  "replay_scores": [...]
}
```

#### GET `/api/v1/verification/certificates`

List certificates.

**Auth**: None (public)

**Query params**: `construct_id`, `limit` (default 20), `offset` (default 0), `sort` (`brier_asc` | `created_desc`)

**Response** (200):
```json
{
  "certificates": [...],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

Certificate list items exclude `replay_scores` for payload size.

## 7. Verification Bridge

### 7.1 Module: `backend/services/verification_bridge.py`

The bridge layer decouples SQLAlchemy from echelon-verify:

```python
async def run_verification_task(run_id: str) -> None:
    """Background task — runs the full echelon-verify pipeline."""
```

**Flow**:

1. Open a new `AsyncSession` via `get_session()` context manager
2. Load `VerificationRun` by ID
3. Construct `PipelineConfig` from `run.config_json`
4. Create `OracleAdapter` via `OracleAdapter.from_config()`
5. Create `AnthropicScorer` from `ScoringConfig`
6. Create `VerificationPipeline(config, oracle, scorer)`
7. Define progress callback: `UPDATE run SET progress=X, total=Y, status=PHASE`
8. Call `pipeline.run(progress=callback)`
9. On success:
   - Convert `CalibrationCertificate` → `VerificationCertificate` row
   - Convert each `ReplayScore` → `VerificationReplayScore` row
   - Link certificate to run, set `status=COMPLETED`
   - Commit
10. On failure:
    - Set `status=FAILED`, `error=str(exception)`
    - Commit

### 7.2 Model Conversion

```python
def certificate_to_db(cert: CalibrationCertificate) -> VerificationCertificate:
    """Convert echelon-verify Pydantic model to SQLAlchemy model."""

def replay_score_to_db(
    score: ReplayScore, certificate_id: str
) -> VerificationReplayScore:
    """Convert echelon-verify ReplayScore to SQLAlchemy model."""
```

### 7.3 Session Isolation

The background task creates its own session — it does NOT share the request's session. This prevents:
- Session timeout during long-running pipelines
- Transaction conflicts with other requests
- Connection pool exhaustion (one connection per active task)

### 7.4 Progress Callback

The bridge provides a progress callback to `VerificationPipeline.run()`:

```python
async def _progress_callback(completed: int, total: int) -> None:
    async with get_session() as session:
        await session.execute(
            update(VerificationRun)
            .where(VerificationRun.id == run_id)
            .values(progress=completed, total=total)
        )
```

Note: The echelon-verify progress callback is sync (`Callable[[int, int], None]`). The bridge wraps it to update the DB. Since the pipeline already runs in an async context, we use a synchronous DB update here wrapped in the event loop.

## 8. Pydantic Schemas

### 8.1 Module: `backend/schemas/verification.py`

Request/response models for the API layer, separate from both SQLAlchemy models and echelon-verify models.

```python
class VerificationRunCreate(BaseModel):
    repo_url: str = Field(..., min_length=1, max_length=500)
    construct_id: str = Field(..., min_length=1, max_length=255)
    oracle_type: Literal["http", "python"] = "http"
    oracle_url: str | None = None
    oracle_headers: dict[str, str] = {}
    oracle_module: str | None = None
    oracle_callable: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    min_replays: int = Field(50, ge=1, le=500)
    github_token: str | None = None

class VerificationRunResponse(BaseModel):
    run_id: str
    status: str
    progress: int
    total: int
    construct_id: str
    repo_url: str
    error: str | None
    certificate_id: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VerificationRunListResponse(BaseModel):
    runs: list[VerificationRunResponse]
    total: int
    limit: int
    offset: int

class CertificateResponse(BaseModel):
    id: str
    construct_id: str
    domain: str
    replay_count: int
    precision: float
    recall: float
    reply_accuracy: float
    composite_score: float
    brier: float
    sample_size: int
    ground_truth_source: str
    methodology_version: str
    scoring_model: str
    created_at: datetime
    replay_scores: list["ReplayScoreResponse"] = []
    model_config = ConfigDict(from_attributes=True)

class CertificateSummaryResponse(BaseModel):
    """List view — no replay_scores."""
    id: str
    construct_id: str
    domain: str
    replay_count: int
    composite_score: float
    brier: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CertificateListResponse(BaseModel):
    certificates: list[CertificateSummaryResponse]
    total: int
    limit: int
    offset: int

class ReplayScoreResponse(BaseModel):
    id: str
    ground_truth_id: str
    precision: float
    recall: float
    reply_accuracy: float
    claims_total: int
    claims_supported: int
    changes_total: int
    changes_surfaced: int
    scoring_model: str
    scoring_latency_ms: int
    scored_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

## 9. Router Mounting

Add to `backend/main.py` following the existing try-except pattern:

```python
# Verification API
try:
    from backend.api.verification_routes import router as verification_router
except ImportError as e:
    verification_router = None
    print(f"⚠️ Could not import Verification API router: {e}")

# ... later, after app creation ...

try:
    if verification_router:
        app.include_router(verification_router)
        print("✅ Verification router included")
    else:
        print("⚠️ Verification router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Verification router: {e}")
    import traceback
    traceback.print_exc()
```

This ensures echelon-verify's absence doesn't break the rest of the app.

## 10. Security Architecture

### 10.1 Authentication

| Endpoint | Auth | Rationale |
|----------|------|-----------|
| POST /runs | Required | Creates resource on behalf of user |
| GET /runs | Required | User sees own runs only |
| GET /runs/{id} | Required | User sees own runs only |
| GET /certificates | Public | Certificates are transparency records |
| GET /certificates/{id} | Public | Certificates are transparency records |

Auth uses the existing `get_user_or_wallet` dependency from `main.py`, which supports both JWT tokens and wallet address headers.

### 10.2 Authorization

- Users can only query their own verification runs
- Enforced by `WHERE user_id = current_user.id` in SQL queries
- No admin role check needed (no admin-specific endpoints in this cycle)

### 10.3 Input Validation

- `repo_url` validated as non-empty string, max 500 chars
- `construct_id` validated as non-empty string, max 255 chars
- `oracle_url` required when `oracle_type=http`
- `oracle_module` + `oracle_callable` required when `oracle_type=python`
- `github_token` never logged or persisted (passed to pipeline only, stored in `config_json` as `"[REDACTED]"`)

### 10.4 Secret Handling

- `github_token`: Passed through to `IngestionConfig` at runtime, stored as `"[REDACTED]"` in `config_json`
- `ANTHROPIC_API_KEY`: Read from environment by `ScoringConfig`, never stored in DB
- No new secrets introduced

## 11. Alembic Migration

### 11.1 Migration File

Generated via `alembic revision --autogenerate -m "add_verification_tables"` but hand-verified for:
- Correct FK ordering (certificates before runs, since runs references certificates)
- Index creation
- SQLite compatibility (no PostgreSQL-specific types)

### 11.2 Table Creation Order

1. `verification_certificates` (no FKs except to itself — standalone)
2. `verification_replay_scores` (FK → certificates)
3. `verification_runs` (FK → users, FK → certificates)

### 11.3 Downgrade

Drop tables in reverse order:
1. `verification_runs`
2. `verification_replay_scores`
3. `verification_certificates`

## 12. Testing Strategy

### 12.1 Unit Tests

| Test | Description |
|------|-------------|
| Model creation | Verify all 3 SQLAlchemy models instantiate with correct defaults |
| Schema validation | Pydantic schemas reject invalid input (missing fields, out-of-range) |
| Bridge conversion | `certificate_to_db()` and `replay_score_to_db()` produce correct models |

### 12.2 Integration Tests

| Test | Description |
|------|-------------|
| POST /runs | Creates DB row, returns 201 with run_id |
| GET /runs/{id} | Returns correct status for known run |
| GET /runs/{id} 404 | Returns 404 for unknown ID |
| GET /runs/{id} 401 | Returns 401 without auth |
| GET /runs (filtered) | Filters by status and construct_id |
| GET /certificates | Returns paginated list |
| GET /certificates/{id} | Returns full certificate with replay scores |
| Auth isolation | User A cannot see User B's runs |
| Background task | Pipeline runs to completion, certificate created |
| Task failure | Pipeline failure sets FAILED status with error message |

### 12.3 Test Setup

Tests use the existing backend test setup (if one exists) or an in-memory SQLite DB with `create_all()`. echelon-verify pipeline is mocked in route tests — only the bridge integration test runs the real pipeline.

## 13. Error Handling

### 13.1 API Errors

| Status | When | Response |
|--------|------|----------|
| 201 | Run created | `{ run_id, status, created_at }` |
| 200 | Success | Resource body |
| 400 | Invalid request | `{ detail: "..." }` |
| 401 | No auth / invalid token | `{ detail: "Could not validate credentials" }` |
| 404 | Unknown run_id or cert_id | `{ detail: "Not found" }` |
| 500 | Internal error | `{ detail: "Internal server error" }` (no stack trace) |

### 13.2 Background Task Errors

All exceptions in `run_verification_task` are caught at the top level:

```python
try:
    # ... pipeline execution ...
except Exception as e:
    logger.error("Verification run %s failed: %s", run_id, e, exc_info=True)
    run.status = VerificationRunStatus.FAILED
    run.error = str(e)[:2000]  # Truncate long error messages
    session.commit()
```

This ensures runs never get stuck in a non-terminal status.

## 14. Future Considerations

These are explicitly **out of scope** for this cycle but noted for future work:

- **WebSocket progress**: Real-time updates instead of polling
- **Rate limiting**: Per-user limits on concurrent verification runs
- **Scheduler**: Periodic re-verification for monitored constructs
- **Frontend UI**: Display certificates and run progress
- **Multi-tenant certificates**: Private certificates with access control
