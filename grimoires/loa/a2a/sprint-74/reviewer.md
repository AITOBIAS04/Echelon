# Sprint-74 (Cycle-023 Sprint-1) — Implementation Report

**Sprint:** Coordinated Startup-Path Replacement
**Date:** 2026-03-10
**Status:** Complete

---

## Task 1: Delete `backend/core/database.py`

**Status:** Done (completed in prior session)

The old sync SQLite layer with hardcoded `sqlite:///./database.db` and wrong-field-name `User` model has been removed entirely. All consumers now use `backend.database.connection`.

---

## Task 2: Rewire `backend/main.py`

**Status:** Done

### Changes Made

1. **Imports replaced**: Removed `from backend.core.database import SessionLocal, engine, Base, User as DBUser`. Added `from backend.database.connection import init_db, close_db, async_session_maker`.

2. **Startup/shutdown events added**:
   - `startup_db()` calls `init_db()` for belt-and-suspenders alongside Alembic
   - `shutdown_db()` calls `close_db()` to dispose engine

3. **Health endpoint rewritten**: Now uses `async_session_maker()` to execute `SELECT 1` against PostgreSQL instead of returning static JSON.

4. **Dead code removed** (177 lines):
   - `pwd_context`, `oauth2_scheme` (CryptContext/OAuth2PasswordBearer — no longer imported)
   - `SECRET_KEY` block (25 lines of JWT secret loading)
   - `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `BetRequest`, `MatchResult`, `BetPlacement`, `MarketBetResponse` Pydantic models
   - `get_user_or_wallet()` function (67 lines — sync JWT+wallet auth using deleted DBUser)
   - `/markets/{market_id}/bet` endpoint (109 lines — sync CPMM bet placement)

5. **Unused imports removed**: `sys`, `timedelta`, `status` (from fastapi), `validator` (from pydantic), `WalletAddressValidator`, `BetAmountValidator`, `StringSanitizer`

6. **`Annotated` import restored** to `typing` — still used by `/premium-intel` endpoint.

7. **Auth router registration** added after investigation template routes.

8. **Investigation template seeder** converted to use `DatabaseConfig.SYNC_DATABASE_URL` since old sync engine is gone.

---

## Task 3: Rewrite `backend/dependencies.py`

**Status:** Done

- Removed `USE_MOCKS` variable and all conditional branches
- Removed `_EmptyRepo` stub class
- Removed `warnings.warn` for USE_MOCKS deprecation
- Repository dependencies now unconditionally return real DB repositories
- `get_butterfly_engine()` and `get_paradox_engine()` now return `None` (routes create request-scoped engines)
- Authentication section (`get_current_user`, `get_current_user_optional`) preserved unchanged

---

## Task 4: Clean `backend/api/butterfly_routes.py`

**Status:** Done

- Removed all 7 `USE_MOCKS` conditional blocks
- `/wing-flaps` and `/timelines/health` use real database path directly
- 5 unimplemented endpoints (`/wing-flaps/recent`, `/timelines/{id}/health`, `/timelines/{id}/gravity`, `/gravity/trending`, `/ripples`, `/ripples/{id}/tree`) return empty data or 404 — consistent with pre-existing real-mode behavior

---

## Task 5: Clean `backend/api/paradox_routes.py`

**Status:** Done

- Removed all 6 `USE_MOCKS` conditional blocks
- `/active` uses real database path directly
- 5 unimplemented endpoints return 404/501 — consistent with pre-existing real-mode behavior

---

## Task 6: Clean `backend/api/osint_routes.py`

**Status:** Done

- Removed single `USE_MOCKS` conditional
- Endpoint returns empty response unconditionally (both paths were identical)

---

## Task 7: Fix `backend/start.sh`

**Status:** Done

- Removed lines 32-40: old `python -c "from backend.core.database import engine, Base; Base.metadata.create_all(bind=engine)"` block
- Replaced with comment explaining that Alembic migrations + `init_db()` on startup handle table creation

---

## Verification

- All 5 modified Python files pass `py_compile.compile()` with no errors
- `grep -r 'core\.database\|USE_MOCKS\|DBUser' backend/ --include='*.py'` returns zero matches
- Only remaining `core.database` references are in documentation files (README_DOCKER.md, IMPORT_FIX_SUMMARY.md, IMPORT_FIXES_COMPLETE.md)

---

## Exit Criteria

- [x] `backend/core/database.py` deleted
- [x] `backend/main.py` uses only async database layer
- [x] `backend/dependencies.py` — no USE_MOCKS, no _EmptyRepo
- [x] `backend/api/butterfly_routes.py` — no USE_MOCKS
- [x] `backend/api/paradox_routes.py` — no USE_MOCKS
- [x] `backend/api/osint_routes.py` — no USE_MOCKS
- [x] `backend/start.sh` — no core.database reference
- [x] All files compile cleanly
