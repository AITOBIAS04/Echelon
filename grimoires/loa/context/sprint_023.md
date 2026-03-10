# Sprint Plan — Cycle-023: Production Database Unification + Railway Hardening

**Cycle:** cycle-023
**Date:** 9 March 2026
**PRD:** grimoires/loa/prd_023.md
**SDD:** grimoires/loa/sdd_023.md

---

## Sprint 0: Grep Sweep + User Model

**Goal:** Map every `backend.core.database` import, add User model to async layer, create Alembic migration.

### Tasks

1. **Grep sweep**: Find all files importing from `backend.core.database`. Document each consumer and its replacement path.

2. **Add User model to `backend/database/models.py`**: Add the `User` class with fields: id, username, email, hashed_password, play_money_balance, wallet_address, tier. Must use `Mapped[]` / `mapped_column()` syntax consistent with existing models.

3. **Create Alembic migration `c023_user_model.py`**: New migration that creates the `users` table via the async Base. Depends on `c022_investigation_templates`.

4. **Verify migration chain**: Run `alembic upgrade head` locally against a test PostgreSQL to confirm all migrations apply cleanly.

### Exit criteria
- `c023_user_model.py` exists and applies cleanly
- `User` model importable from `backend.database.models`
- Complete list of files needing `core.database` import changes

---

## Sprint 1: Database Layer Unification

**Goal:** Remove old SQLite layer entirely. Rewire main.py and all consumers to async PostgreSQL.

### Tasks

1. **Delete `backend/core/database.py`** (or gut it to re-export from async layer if other core modules depend on it being importable).

2. **Rewrite main.py database initialization:**
   - Remove: `from backend.core.database import SessionLocal, engine, Base, User as DBUser`
   - Remove: `Base.metadata.create_all(bind=engine)`
   - Add: `from backend.database.connection import init_db, close_db, async_session_maker`
   - Add startup event calling `await init_db()`
   - Add shutdown event calling `await close_db()`

3. **Fix `/health` endpoint**: Replace `SessionLocal()` with `async_session_maker()` session + `await session.execute(text("SELECT 1"))`.

4. **Remove old auth endpoints from main.py:**
   - Remove `/token` endpoint (~line 1540)
   - Remove `/users/me` endpoint (~line 1584)
   - Remove `/users/me/simulations` endpoint (~line 1589)
   - Remove the old sync `get_db()` that yields `SessionLocal()`

5. **Register auth router in main.py:**
   ```python
   try:
       from backend.api.auth_routes import router as auth_router
       app.include_router(auth_router)
       print("✅ Auth router included")
   except Exception as e:
       print(f"❌ Failed to include Auth router: {e}")
   ```

6. **Fix all remaining `backend.core.database` imports** (seed_data.py, test files, any other consumers found in Sprint 0 grep sweep).

7. **Test locally**: Start the server with `DATABASE_URL` pointing to local PostgreSQL. Verify `/health`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me` all work.

### Exit criteria
- No file imports from `backend.core.database`
- Server starts cleanly with `DATABASE_URL` env var
- `/health` checks PostgreSQL
- Auth endpoints functional

---

## Sprint 2: Auth Routes + Railway Config + Validation

**Goal:** Make auth_routes.py production-ready, update Railway config, validate end-to-end.

### Tasks

1. **Rewrite `auth_routes.py` to use database:**
   - Replace `USERS = {}` in-memory dict
   - `register`: Create `User` in DB via async session
   - `login`: Query `User` by email, verify password, return JWT
   - `/me`: Already works via `get_current_user` dependency (reads JWT)
   - Add proper error handling (duplicate email, invalid credentials)

2. **Update `railway.toml` start command:**
   ```toml
   [deploy]
   startCommand = "sh -c 'cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port \"$PORT\"'"
   ```

3. **Update `nixpacks.toml` start command** to match:
   ```toml
   [start]
   cmd = "cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
   ```

4. **Add `psycopg2-binary` to requirements.txt** if not already present (needed for Alembic sync migrations).

5. **Document required Railway env vars** in a `DEPLOY.md` or update existing README:
   - `DATABASE_URL` (auto-set by Railway Postgres plugin)
   - `USE_MOCKS=false`
   - `JWT_SECRET_KEY` (generate with secrets module)
   - `ENVIRONMENT=production`

6. **Full validation against local PostgreSQL:**
   - `alembic upgrade head` — all migrations apply
   - Start server with `USE_MOCKS=false`
   - Hit all 15 surface endpoints — none return 500
   - Register → Login → `/me` flow completes
   - `/health` returns `"database": "ok"`

### Exit criteria
- All acceptance criteria from PRD §6 pass
- Railway deploy config updated
- Auth flow works end-to-end against PostgreSQL
- No 500 errors on any registered endpoint (empty data is fine)

---

## Pre-Deploy: Tobias Manual Steps

Before or during Loa's cycle, Tobias provisions Railway infrastructure:

1. **Railway dashboard → Add PostgreSQL plugin** to the project
   - This auto-injects `DATABASE_URL` into the service env
2. **Railway dashboard → Set env vars:**
   - `USE_MOCKS` = `false`
   - `JWT_SECRET_KEY` = (generate: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`)
   - `ENVIRONMENT` = `production`
3. **Push Loa's code** → Railway auto-deploys → `alembic upgrade head` runs → all surfaces come alive

---

## Post-Deploy Verification

Run through the 12-point checklist in SDD §6 against the live Railway URL.
