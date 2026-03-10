# SDD — Cycle-023: Production Database Unification + Railway Hardening

**Cycle:** cycle-023
**Date:** 9 March 2026
**PRD:** grimoires/loa/context/prd_023.md

---

## 1. Architecture Overview

Cycle 023 eliminates the dual-database architecture and makes the async PostgreSQL layer the single database path for the entire backend.

```text
BEFORE (split-brain):
┌──────────────────────────────┐    ┌──────────────────────────────┐
│  core/database.py            │    │  database/connection.py      │
│  SQLite (sync)               │    │  PostgreSQL (async)          │
│                              │    │                              │
│  Used by:                    │    │  Used by:                    │
│  - main.py startup           │    │  - agents_routes             │
│  - /health                   │    │  - theatre_routes            │
│  - /token, /users/me         │    │  - certificates              │
│  - SessionLocal dependency   │    │  - scenario_packs            │
│                              │    │  - investigations            │
│  → Returns 200 (SQLite ok)   │    │  - world_monitor             │
│                              │    │  → Returns 500 (no PG)       │
└──────────────────────────────┘    └──────────────────────────────┘

AFTER (unified):
┌──────────────────────────────────────────────────────────────────┐
│  database/connection.py — Single async PostgreSQL layer          │
│                                                                  │
│  Used by: ALL routes, /health, auth, startup                     │
│  Railway DATABASE_URL → postgresql+asyncpg://...                 │
│  Alembic manages schema, init_db() creates at startup            │
│  → All endpoints return appropriate responses                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. File Changes

### 2.1 DELETE or SHIM: `backend/core/database.py`

**Preferred:** Delete entirely once all imports are migrated.
**Acceptable:** Reduce to a thin re-export shim from `backend.database.connection` if test files or dev scripts still need it as a transitional step. The shim must **not** create any SQLite engine or session.

All production consumers must migrate to `backend.database.connection`.

**Import migration map:**

| Old import | New import |
|------------|-----------|
| `from backend.core.database import SessionLocal` | `from backend.database.connection import async_session_maker` |
| `from backend.core.database import engine` | `from backend.database.connection import engine` |
| `from backend.core.database import Base` | `from backend.database.connection import Base` |
| `from backend.core.database import User as DBUser` | `from backend.database.models import User` |
| `from backend.core.database import get_db` | `from backend.dependencies import get_db` |

### 2.2 EXISTING: `backend/database/models.py` — User Model (DO NOT MODIFY)

A `User` model **already exists** at line 78 with the correct async schema:

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(20), default="free")
    balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    balance_echelon: Mapped[int] = mapped_column(Integer, default=0)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships: agents, positions, watchlist_items, private_forks
```

**Do not modify this model.** It already has relationships with Agent, UserPosition, WatchlistItem, and PrivateFork. The auth_routes rewrite must conform to these field names (especially `password_hash`, not `hashed_password`).

### 2.3 MODIFY: `backend/main.py`

**Remove:**
- Line 34: `from backend.core.database import SessionLocal, engine, Base, User as DBUser`
- Line 150: `Base.metadata.create_all(bind=engine)`
- Lines ~1540–1600: Old `/token`, `/users/me`, `/users/me/simulations` endpoints
- Old sync `get_db()` function that returns `SessionLocal()`

**Add:**
- Import from async layer: `from backend.database.connection import init_db, close_db, async_session_maker`
- Startup event: call `await init_db()` (creates tables from async Base — belt-and-suspenders alongside Alembic)
- Shutdown event: call `await close_db()`
- Auth router registration (see §2.5)

**Fix `/health`:**
```python
@app.get("/health")
async def health_check():
    try:
        from backend.database.connection import async_session_maker
        from sqlalchemy import text
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "version": "1.0.0",
    }
```

### 2.4 MODIFY: `backend/api/auth_routes.py`

Replace in-memory `USERS = {}` with database-backed operations. **Critical:** Use the existing `User` model's field names (`password_hash`, `balance_usdc`, `balance_echelon`, `id: String(50)`).

```python
import uuid
from backend.database.models import User
from backend.dependencies import get_db

@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing user by email
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    user = User(
        id=str(uuid.uuid4()),  # String(50) primary key
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),  # NOTE: field is password_hash, not hashed_password
        tier="free",
        balance_usdc=0.0,
        balance_echelon=0,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"user_id": user.id, "message": "Registered successfully"}

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):  # NOTE: password_hash
        raise HTTPException(401, "Invalid credentials")

    token_data = TokenData(user_id=user.id, username=user.username, email=user.email, tier=user.tier)
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }
```

### 2.5 MODIFY: `backend/main.py` — Router Registration

Add auth router registration in the router block:

```python
# Include Auth router
try:
    from backend.api.auth_routes import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth router included")
except Exception as e:
    print(f"❌ Failed to include Auth router: {e}")
    import traceback
    traceback.print_exc()
```

### 2.6 MODIFY: `railway.toml` + `nixpacks.toml` (update as a pair)

**`railway.toml`:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "sh -c 'cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port \"$PORT\"'"
```

**`nixpacks.toml`:**
```toml
[phases.setup]
nixPkgs = ["python312", "gcc"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"

[variables]
PYTHON_VERSION = "3.12"
```

Railway may use either file depending on deployment mode. Both must run migrations before the app starts.

### 2.7 NEW: Alembic migration `c023_user_model.py`

Add User table to the async Base migration chain. This ensures `alembic upgrade head` creates the users table in PostgreSQL. **Note:** The User model already exists in `models.py` — this migration just needs to create the `users` table if it doesn't exist.

### 2.8 Grep Sweep: Remove All `backend.core.database` References

Search entire codebase for any remaining imports of `backend.core.database` and update to use the async layer. Known consumers beyond main.py:

- `backend/seed_data.py` — **already deleted** in cleanup commit
- `backend/test_db.py` — update or delete
- `backend/test_db_connection.py` — update or delete
- `backend/start.sh` — update old core DB init logic
- Any other test files

### 2.9 Remove USE_MOCKS Entirely

Delete all mock-related code:
- `dependencies.py`: Remove `USE_MOCKS` variable, the `_EmptyRepo` stub class, and all conditional branches
- `butterfly_routes.py`: Remove all `USE_MOCKS` checks and mock fallback branches (~16 references)
- `paradox_routes.py`: Remove all `USE_MOCKS` checks and mock fallback branches (~14 references)
- `main.py`: Remove the mock engine warning block

---

## 3. Railway Environment Variables

Required env vars (Tobias sets these in Railway dashboard):

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Auto-set by Railway Postgres plugin | `postgresql://user:pass@host:port/dbname` |
| `JWT_SECRET_KEY` | Generate with `python -c 'import secrets; print(secrets.token_urlsafe(32))'` | Required for auth; main.py raises ValueError in production without it |
| `ENVIRONMENT` | `production` | Enables production guards |

**Note:** `USE_MOCKS` is no longer needed — all mock code is deleted in this cycle. Remove from Railway env vars if previously set.

---

## 4. Migration Order

Alembic migration chain (existing + new):

```
347c30465dba_initial_tables
  → a1b2c3d4e5f6_add_verification_tables
    → c014_add_inquiry_class_columns
      → c014c_add_stop_condition_columns
        → c016_engine_coherence
          → c017_policy_surface
            → c018_scenario_packs
              → c020_replay_source_run_id
                → c021_certificate_lifecycle
                  → c022_investigation_templates
                    → c023_user_model  ← NEW
```

---

## 5. Dependency on External Actions

Before Loa can validate the cycle on Railway:

1. **Tobias:** Add PostgreSQL plugin to Railway project
2. **Tobias:** Set `USE_MOCKS=false`, `JWT_SECRET_KEY`, `ENVIRONMENT=production` in Railway env vars
3. **Loa:** Push code changes → Railway auto-deploys → `alembic upgrade head` runs → all surfaces come alive

---

## 6. Verification

### 6.1 Backend (curl against Railway URL)

| # | Check | Method |
|---|-------|--------|
| 1 | `/health` returns `"database": "ok"` | `curl` |
| 2 | `/api/v1/auth/register` creates user | `curl -X POST` with JSON body |
| 3 | `/api/v1/auth/login` returns JWT | `curl -X POST` with credentials |
| 4 | `/api/v1/auth/me` returns user with Bearer token | `curl -H "Authorization: Bearer ..."` |
| 5 | `/api/v1/agents/` returns 200 (empty list) | `curl` |
| 6 | `/api/v1/templates` returns 200 | `curl` |
| 7 | `/api/v1/certificates` returns 200 (empty) | `curl` |
| 8 | `/api/v1/scenario-pack-templates/` returns 200 | `curl` |
| 9 | `/api/v1/investigation-templates/` returns 200 (seeded) | `curl` |
| 10 | `/api/v1/investigations/` returns 200 (empty) | `curl` |
| 11 | `/api/v1/world-monitor/live` returns 200 | `curl` |
| 12 | `grep -r USE_MOCKS backend/` returns zero results | Local check |
| 13 | Both `railway.toml` and `nixpacks.toml` contain `alembic upgrade head` | Local check |

### 6.2 Frontend smoke (browser against deployed frontend)

| # | Check | Method |
|---|-------|--------|
| 14 | `/theatres` loads, no 500/console errors | Browser DevTools |
| 15 | `/investigations` loads, no 500/console errors | Browser DevTools |
| 16 | `/scenario-packs` loads, no 500/console errors | Browser DevTools |
| 17 | `/certificates` loads, no 500/console errors | Browser DevTools |
| 18 | `/verify` loads, no 500/console errors | Browser DevTools |
| 19 | Auth flow: register → login → `/me` → session persists across navigation | Browser |
