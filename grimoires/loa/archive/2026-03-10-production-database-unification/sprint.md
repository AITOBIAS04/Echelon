# Sprint Plan — Cycle-023: Production Database Unification + Railway Hardening

**Cycle:** cycle-023
**Date:** 9 March 2026
**PRD:** grimoires/loa/context/prd_023.md
**SDD:** grimoires/loa/context/sdd_023.md

---

## Sprint 0: Grep Sweep + User Model Migration

**Goal:** Map every `backend.core.database` import, verify existing User model, create Alembic migration for the users table.

### Tasks

1. **Grep sweep**: Find all files importing from `backend.core.database`. Document each consumer and its replacement path. Known: main.py, start.sh, test_db.py, test_db_connection.py. (`seed_data.py` already deleted.)

2. **Verify existing User model in `backend/database/models.py`** (line 78): The model already exists with fields `id: String(50)`, `username`, `email`, `password_hash`, `tier`, `balance_usdc`, `balance_echelon`, `wallet_address`, `created_at`, `updated_at` plus relationships. **Do not modify.** Confirm it is importable from `backend.database.models`.

3. **Create Alembic migration `c023_user_model.py`**: Creates the `users` table if not exists. Depends on `c022_investigation_templates`. The model is already defined — this migration materializes it in PostgreSQL.

4. **Verify migration chain**: Run `alembic upgrade head` locally against a test PostgreSQL to confirm all migrations apply cleanly.

### Exit criteria
- `c023_user_model.py` exists and applies cleanly
- `User` model importable from `backend.database.models` (already true — just verify)
- Complete list of files needing `core.database` import changes

---

## Sprint 1: Coordinated Startup-Path Replacement

**Goal:** Replace the old SQLite startup path with the async PostgreSQL layer. This is a coordinated replacement — main.py startup, health endpoint, auth endpoints, and start.sh all depend on the old layer and must be updated together.

### Tasks

1. **Delete or shim `backend/core/database.py`:**
   - Preferred: delete entirely once all imports are migrated.
   - Acceptable: reduce to a thin re-export shim from `backend.database.connection` (no SQLite engine/session). Use shim only if test files need a transitional bridge.

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

6. **Fix all remaining `backend.core.database` imports** (start.sh, test_db.py, test_db_connection.py, any other consumers found in Sprint 0 grep sweep).

7. **Remove USE_MOCKS entirely:**
   - `dependencies.py`: Delete `USE_MOCKS` variable, `_EmptyRepo` stubs, all conditional branches
   - `butterfly_routes.py`: Delete all `USE_MOCKS` checks and mock fallback branches (~16 refs)
   - `paradox_routes.py`: Delete all `USE_MOCKS` checks and mock fallback branches (~14 refs)
   - `main.py`: Delete mock engine warning block
   - Verify: `grep -r USE_MOCKS backend/` returns zero results

8. **Test locally**: Start the server with `DATABASE_URL` pointing to local PostgreSQL. Verify `/health`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me` all work.

### Exit criteria
- No file imports from `backend.core.database` (or shim contains no SQLite)
- `grep -r USE_MOCKS backend/` returns zero results
- Server starts cleanly with `DATABASE_URL` env var
- `/health` checks PostgreSQL
- Auth endpoints functional

---

## Sprint 2: Auth Routes + Railway Config + Validation

**Goal:** Make auth_routes.py production-ready (reconciled against existing User model), update both deploy configs, validate end-to-end including frontend smoke.

### Tasks

1. **Rewrite `auth_routes.py` to use database (model reconciliation):**
   - Replace `USERS = {}` in-memory dict
   - `register`: Create `User` in DB via async session. **Use correct field names:**
     - `password_hash` (not `hashed_password`)
     - `id = str(uuid.uuid4())` (String(50) primary key, not auto-increment int)
     - `balance_usdc=0.0`, `balance_echelon=0` (not `play_money_balance`)
   - `login`: Query `User` by email, verify against `user.password_hash`, return JWT
   - `/me`: Already works via `get_current_user` dependency (reads JWT)
   - Add proper error handling (duplicate email, invalid credentials)

2. **Update both deploy configs as a pair:**

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

3. **Add `psycopg2-binary` to requirements.txt** if not already present (needed for Alembic sync migrations).

4. **Document required Railway env vars** in a `DEPLOY.md` or update existing README:
   - `DATABASE_URL` (auto-set by Railway Postgres plugin)
   - `JWT_SECRET_KEY` (generate with secrets module)
   - `ENVIRONMENT=production`
   - (Note: `USE_MOCKS` no longer exists — do not document it)

5. **Full validation against local PostgreSQL:**
   - `alembic upgrade head` — all migrations apply
   - Start server (no USE_MOCKS flag needed — it's deleted)
   - Hit all 15 surface endpoints — none return 500
   - Register → Login → `/me` flow completes
   - `/health` returns `"database": "ok"`
   - `grep -r USE_MOCKS backend/` returns zero results
   - Both `railway.toml` and `nixpacks.toml` contain `alembic upgrade head`

### Exit criteria
- All acceptance criteria from PRD §6 pass (both backend curl and frontend smoke)
- Both Railway deploy configs updated
- Auth flow works end-to-end against PostgreSQL using existing User model field names
- No 500 errors on any registered endpoint (empty data is fine)
- `USE_MOCKS` completely removed from codebase

---

## Pre-Deploy: Tobias Manual Steps

Before or during Loa's cycle, Tobias provisions Railway infrastructure:

1. **Railway dashboard → Add PostgreSQL plugin** to the project
   - This auto-injects `DATABASE_URL` into the service env
2. **Railway dashboard → Set env vars:**
   - `JWT_SECRET_KEY` = (generate: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`)
   - `ENVIRONMENT` = `production`
   - (Note: `USE_MOCKS` no longer needed — mock code is deleted in this cycle. If it exists from before, it can be removed from Railway env vars.)
3. **Push Loa's code** → Railway auto-deploys → `alembic upgrade head` runs → all surfaces come alive

---

## Post-Deploy Verification

Run through the 19-point checklist in SDD §6 against the live Railway URL:
- §6.1: Backend curl checks (13 items — health, auth, all surface endpoints, grep/config checks)
- §6.2: Frontend smoke checks (6 items — theatres, investigations, scenario-packs, certificates, verify, auth flow)
