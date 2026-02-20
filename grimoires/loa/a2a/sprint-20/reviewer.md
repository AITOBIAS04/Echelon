# Sprint 20 (cycle-028 sprint-2) — Implementation Report

## Service + API: Bridge, Routes, Mounting

### Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `backend/services/verification_bridge.py` | Created | 207 lines |
| `backend/api/verification_routes.py` | Created | 226 lines |
| `backend/main.py` | Modified | +18 (import + include_router block) |
| `backend/tests/test_verification_bridge.py` | Created | 211 lines |

### Task 2.1 — Verification bridge service

- `run_verification_task(run_id)`: async background task with session-per-task isolation
- `certificate_to_db()` / `replay_score_to_db()`: echelon-verify -> SQLAlchemy conversion
- Progress callback via `asyncio.get_running_loop().create_task()`
- Top-level exception catch guarantees terminal status (COMPLETED or FAILED)
- Error truncation to 2000 chars
- `ECHELON_VERIFY_AVAILABLE` flag via try-except import

### Task 2.2 — API router (5 endpoints)

- `POST /runs` (201) — creates run + launches asyncio.create_task()
- `GET /runs/{run_id}` — auth required, user isolation via WHERE user_id clause
- `GET /runs` — paginated with status/construct_id filters
- `GET /certificates/{cert_id}` — public, selectinload for replay_scores
- `GET /certificates` — public, sortable by brier_asc or created_desc
- Auth via `get_current_user` from `backend.dependencies` (JWT-based)

### Task 2.3 — Router mounting

- Try-except import at lines 112-117 of main.py
- Conditional include_router with logging at lines 319-329
- Follows exact same pattern as all other routers

### Task 2.4 — Unit tests

5 tests: bridge conversion (certificate, replay_score), unique ID generation, missing echelon-verify handling, response mapping.

### Test Results

5 additional tests passing (17 total cumulative).
