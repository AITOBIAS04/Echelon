# PRD — Cycle-023: Production Database Unification + Railway Hardening

**Cycle:** cycle-023
**Date:** 9 March 2026
**Depends on:** Cycle-022 (Investigation Templates), all shipped cycles 017–021
**Sprints:** 3 (0–2)
**Builder:** Loa (backend only)

---

## 1. Problem Statement

The deployed backend on Railway is running with a split-brain database architecture that renders 7 of 15 frontend surfaces non-functional (500 Internal Server Error).

### 1.1 Two Separate Database Layers

The codebase has two independent database systems that were never unified:

- **Old layer** (`backend/core/database.py`): Hardcoded `sqlite:///./database.db`, sync SQLAlchemy. Used by `main.py` startup (`Base.metadata.create_all`), the `/health` endpoint, the old `/token` and `/users/me` auth flow, and the `SessionLocal` dependency.
- **New layer** (`backend/database/connection.py` + `backend/database/config.py` + `backend/database/models.py`): Async PostgreSQL via `asyncpg`, reads `DATABASE_URL` from env. Used by all Cycle 017–021 routes (agents, theatres, certificates, scenario packs, investigations, world-monitor, analytics, verification, positions).

On Railway, the old layer creates an ephemeral SQLite file (passes `/health` check), while the new layer attempts to connect to PostgreSQL which doesn't exist. Result: all Cycle 017–021 endpoints crash with 500.

### 1.2 USE_MOCKS Inconsistency

`USE_MOCKS` defaults to `"true"`. Only `butterfly_routes.py` and `paradox_routes.py` implement mock fallback. All other route files hit the async DB directly — no mock safety net. This is why butterfly/paradox return 200 (mock data) while theatre/agents/certificates return 500.

### 1.3 Auth Layer is Entirely Disconnected

`auth_routes.py` exists with `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/me` — but:

- It is **never registered** in `main.py`. Frontend calls all three on every session → 404.
- It uses an **in-memory** `USERS = {}` dict — no database backing at all.
- Its field assumptions (`hashed_password`, `play_money_balance`) do **not** match the existing `User` model in `backend/database/models.py`, which uses `password_hash`, `balance_usdc`, `balance_echelon`, and `id: String(50)` (not int).

**Reconciliation required:** Loa must reconcile `auth_routes.py` field names against the **existing** `User` model in `models.py` — not invent a new schema. The existing model is the source of truth because it already participates in relationships with `Agent`, `UserPosition`, `WatchlistItem`, and `PrivateFork`.

Additionally:
- `investigation_routes.py` import may fail silently on Railway (import chain depends on modules that may not resolve).

### 1.4 Both Deploy Entrypoints Skip Migrations

Two active deploy configs exist — both bypass Alembic:

- **`railway.toml`** runs `uvicorn backend.main:app` directly (no migrations).
- **`nixpacks.toml`** also runs `uvicorn backend.main:app` directly (no migrations).
- **`start.sh`** (which runs `alembic upgrade head` before starting) is never invoked by either.

Even if PostgreSQL were attached, neither entrypoint creates tables via Alembic. **Both files must be updated as a pair** — Railway may use either depending on deployment mode.

---

## 2. Goals

| # | Goal | Success Criterion |
|---|------|-------------------|
| G1 | Single database layer | All routes use PostgreSQL via `backend/database/connection.py`. Old SQLite layer either deleted or reduced to a thin re-export shim (no direct SQLite usage). No file creates or queries SQLite. |
| G2 | Railway PostgreSQL operational | `DATABASE_URL` env var from Railway Postgres plugin consumed correctly. All 15 surfaces return non-500 responses. |
| G3 | Migrations run on deploy | **Both** `railway.toml` and `nixpacks.toml` start commands run `alembic upgrade head` before `uvicorn`. |
| G4 | Auth flow functional | `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/me` all registered and DB-backed. Auth routes reconciled against the **existing** `User` model in `backend/database/models.py` (field names: `password_hash`, `balance_usdc`, `balance_echelon`, `id: String(50)`). Frontend auth cycle completes. |
| G5 | Health endpoint honest | `/health` checks PostgreSQL, not ephemeral SQLite. |
| G6 | USE_MOCKS removed from codebase | `USE_MOCKS` env var, all checking code in `dependencies.py`, and mock fallback paths in `butterfly_routes.py` / `paradox_routes.py` are **deleted**. All routes use real DB unconditionally. No mock mode remains for any environment. |

---

## 3. Non-Goals

- Frontend changes (Alexander handles those separately)
- New feature work — this cycle is strictly infrastructure unification
- Seed data population beyond what the existing seeders already handle
- PostgreSQL provisioning on Railway (Tobias provisions manually; Loa wires the code)

---

## 4. Scope

### 4.1 Remove Old Database Layer

This is a **coordinated startup-path replacement**, not just deleting one file. The old layer is wired into main.py startup, the health endpoint, auth endpoints, and `start.sh`. All must be addressed together.

**Delete or shim** `backend/core/database.py`:
- Preferred: delete entirely once all imports are migrated.
- Acceptable: reduce to a thin shim that re-exports from `backend.database.connection` (if test files or dev scripts still need it as a transitional step). The shim must **not** create any SQLite engine or session.

**Remove from main.py:**
- Line 34 import of `SessionLocal, engine, Base, User as DBUser` from `core.database`
- Line 150 `Base.metadata.create_all(bind=engine)` (the old SQLite create_all)
- Old `/token` endpoint (~line 1540) using sync `SessionLocal`
- Old `/users/me` endpoint (~line 1584) using sync `SessionLocal`
- Old sync `get_db()` function that yields `SessionLocal()`

**Remove from start.sh:**
- Old `core.database` initialization logic (line ~35)

**User model:** A `User` model **already exists** in `backend/database/models.py` (line 78) with the correct async schema: `id: String(50)`, `username`, `email`, `password_hash`, `tier`, `balance_usdc`, `balance_echelon`, `wallet_address`, `created_at`, `updated_at`, plus relationships to Agent, UserPosition, WatchlistItem, PrivateFork. **Do not recreate or modify** — use as-is.

### 4.2 Register Missing Routers in main.py

Add to the router registration block:
```python
# Auth router
try:
    from backend.api.auth_routes import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth router included")
except Exception as e:
    print(f"❌ Failed to include Auth router: {e}")
```

### 4.3 Fix Health Endpoint

Replace `SessionLocal()` with async session from `backend.database.connection`:
```python
@app.get("/health")
async def health_check():
    try:
        from backend.database.connection import async_session_maker
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    ...
```

### 4.4 Fix Both Deploy Entrypoints

Both deploy configs must run migrations before the app starts. **Update as a pair:**

`railway.toml`:
```toml
[deploy]
startCommand = "sh -c 'cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port \"$PORT\"'"
```

`nixpacks.toml`:
```toml
[start]
cmd = "cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

### 4.5 Remove USE_MOCKS Entirely

**End state:** The `USE_MOCKS` env var, the checking code in `dependencies.py`, the `_EmptyRepo` stubs, and the mock-conditional branches in `butterfly_routes.py` and `paradox_routes.py` are all **deleted**. All routes hit the real database unconditionally. No mock mode remains for any environment (dev or production).

### 4.6 Auth Routes Database Backing (Model Reconciliation Required)

`auth_routes.py` currently uses in-memory `USERS = {}` dict. For production, this must persist to PostgreSQL via the **existing** `User` model in `backend/database/models.py`.

**Critical reconciliation points:**
- auth_routes uses `hashed_password` → model field is `password_hash`
- auth_routes generates `USR_NNNN` string IDs → model `id` is `String(50)`, compatible but ID generation logic must produce UUIDs or similar
- auth_routes references `play_money_balance` → model has `balance_usdc: Float` and `balance_echelon: int` (no `play_money_balance`)
- auth_routes `tier` field matches model `tier: String(20)`

Loa must rewrite `auth_routes.py` to use the model's actual field names and types. Do **not** modify the model to match auth_routes — the model is already in production with relationships and migrations.

---

## 5. Risk

| Risk | Mitigation |
|------|------------|
| Old code elsewhere still imports `backend.core.database` | Grep all imports; refactor or alias |
| Alembic migrations fail on Railway PostgreSQL | Test migrations locally against PostgreSQL first |
| Auth routes depend on modules that may not exist on Railway | Wrap in try/except consistent with other router registrations |
| Removing old `/token` endpoint breaks existing auth flows | Old flow used `OAuth2PasswordRequestForm` — new auth_routes uses email/password JSON. Frontend already calls `/api/v1/auth/login`, not `/token`. |

---

## 6. Acceptance Criteria

### Backend (curl / local test)
1. `python -c "from backend.core.database import ..."` either raises ImportError (deleted) or returns shim with no SQLite (gutted)
2. `alembic upgrade head` succeeds against Railway PostgreSQL
3. `/health` returns `"database": "ok"` by checking PostgreSQL
4. `/api/v1/auth/register` creates a user in PostgreSQL (using existing `User` model field names)
5. `/api/v1/auth/login` returns JWT token
6. `/api/v1/auth/me` returns user info with valid token
7. All 7 previously-500 endpoints return non-500 (200 with empty data or appropriate response)
8. `USE_MOCKS` env var, checking code, and mock fallback branches are **deleted** from codebase (grep returns zero results)
9. Both `railway.toml` and `nixpacks.toml` run `alembic upgrade head` before `uvicorn`

### Frontend smoke check (post-deploy, browser)
10. `/theatres` loads without 500/console errors
11. `/investigations` loads without 500/console errors
12. `/scenario-packs` loads without 500/console errors
13. `/certificates` loads without 500/console errors
14. `/verify` loads without 500/console errors
15. Auth flow: register → login → `/me` returns user data → subsequent page loads maintain session
