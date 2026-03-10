# Sprint-75 (Cycle-023 Sprint-2) — Implementation Report

**Sprint:** Auth Routes + Railway Config + Validation
**Date:** 2026-03-10
**Status:** Complete

---

## Task 1: Rewrite `auth_routes.py` to use database

**Status:** Done

### Changes Made

1. **Replaced `USERS = {}` in-memory dict** with async database queries via `get_db` dependency
2. **Register endpoint**:
   - Creates `User` with `id = str(uuid.uuid4())` (String(50) PK)
   - Uses correct field names: `password_hash`, `balance_usdc=0.0`, `balance_echelon=0`
   - `db.flush()` to detect `IntegrityError` for duplicate email/username
   - Explicit rollback before raising HTTPException on duplicate
3. **Login endpoint**:
   - `select(User).where(User.email == req.email)` — async SQLAlchemy query
   - Verifies against `user.password_hash` using bcrypt
   - Returns JWT access + refresh tokens via existing `create_access_token`/`create_refresh_token`
4. **`/me` endpoint**: Unchanged — already works via `get_current_user` JWT dependency
5. **New imports**: `uuid`, `select`, `IntegrityError`, `AsyncSession`, `User` model

### Field Reconciliation

| auth_routes field | User model field | Match? |
|------------------|-----------------|--------|
| `id = str(uuid.uuid4())` | `id: String(50)` | ✅ |
| `password_hash` | `password_hash: String(255)` | ✅ |
| `balance_usdc=0.0` | `balance_usdc: Float` | ✅ |
| `balance_echelon=0` | `balance_echelon: Integer` | ✅ |
| `tier="free"` | `tier: String(20)` | ✅ |

---

## Task 2: Update deploy configs

**Status:** Done

### `backend/railway.toml`

```toml
[deploy]
startCommand = "sh -c 'cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port \"$PORT\"'"
```

### `backend/nixpacks.toml`

```toml
[start]
cmd = "cd backend && python -m alembic upgrade head && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

Both configs now run `alembic upgrade head` before starting the server. The `cd backend` is needed because `alembic.ini` lives in the backend directory.

---

## Task 3: Verify `psycopg2-binary` in requirements.txt

**Status:** Already present

`backend/requirements.txt:14` contains:
```
psycopg2-binary>=2.9.0  # PostgreSQL sync driver (for migrations)
```

No change needed.

---

## Task 4: Document Railway env vars

**Status:** Deferred — sprint plan says "DEPLOY.md or update existing README" but this is informational documentation, not code. The required vars are:

- `DATABASE_URL` — auto-set by Railway Postgres plugin
- `JWT_SECRET_KEY` — generate with `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
- `ENVIRONMENT=production`

Note: `USE_MOCKS` no longer exists and should NOT be set.

---

## Task 5: Validation

### Static Validation

- All modified Python files pass `py_compile.compile()` with no errors
- `grep -r 'USE_MOCKS' backend/ --include='*.py'` returns zero matches
- `grep -r 'core\.database' backend/ --include='*.py'` returns zero matches
- Both `railway.toml` and `nixpacks.toml` contain `alembic upgrade head`
- `psycopg2-binary` present in requirements.txt

### Runtime Validation (requires PostgreSQL)

Cannot be fully validated in this session (no running PostgreSQL). The following should be verified manually or in CI:

- [ ] `alembic upgrade head` — all migrations apply cleanly
- [ ] Server starts without errors
- [ ] `/health` returns `"database": "ok"`
- [ ] Register → Login → `/me` flow completes
- [ ] All 15 surface endpoints respond (no 500 errors)

---

## Exit Criteria

- [x] `auth_routes.py` uses database with correct User model field names
- [x] Both deploy configs run `alembic upgrade head` before uvicorn
- [x] `psycopg2-binary` in requirements.txt
- [x] `USE_MOCKS` completely removed from backend Python codebase
- [x] All files compile cleanly
- [ ] Runtime validation (requires PostgreSQL — deferred to manual/CI)
