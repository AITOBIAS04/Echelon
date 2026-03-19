# Sprint 3 (Global 111) — Implementation Report

## Cycle 038: Cross-Theatre Paradox Detection
## Sprint: API Routes + TREMOR Fixture + Regression

---

## Summary

Sprint 3 delivers the API surface for cycle 038's cross-theatre paradox detection system. Four new route modules expose 18 endpoints total, registered in `main.py` with try/except guards. A TREMOR end-to-end fixture validates the full pipeline (anchor → link → scan → detect), and a regression suite confirms backward compatibility.

---

## Tasks Completed

### T3.1: FactAnchor API Routes ✅

**Files:** `backend/api/fact_anchor_routes.py` (new, ~190 lines)

5 endpoints on `/api/v1/fact-anchors`:
- `POST /` — Create/get anchor (idempotent via `get_or_create`)
- `GET /` — List anchors (filter by type/source, paginated)
- `GET /{anchor_id}` — Detail with links
- `POST /{anchor_id}/link` — Link theatre (triggers scanner if ≥2 theatres)
- `GET /{anchor_id}/paradoxes` — Paradoxes for anchor

Auth required on POST endpoints. Public reads. Follows existing FastAPI patterns with `Depends(get_db)` and `Depends(get_current_user)`.

### T3.2: CoherenceGroup + CrossTheatreParadox + OracleConsistency Routes ✅

**Files:**
- `backend/api/coherence_group_routes.py` (new, ~150 lines) — 5 endpoints
- `backend/api/cross_theatre_paradox_routes.py` (new, ~190 lines) — 5 endpoints
- `backend/api/oracle_consistency_routes.py` (new, ~95 lines) — 3 endpoints

CoherenceGroup routes: CRUD + scope overlap scan trigger.

CrossTheatreParadox routes: List/detail + state transition endpoints (acknowledge/resolve/dismiss) with `VALID_TRANSITIONS` map enforcing OPEN→ACKNOWLEDGED→RESOLVED/DISMISSED. Terminal states have no outbound transitions. 409 on invalid transitions.

OracleConsistency routes: Record response (idempotent), check consistency, divergence history.

### T3.3: TREMOR End-to-End Fixture ✅

**File:** `backend/tests/test_038_sprint3_routes.py` — `TestTREMORFixture` class (4 tests)

Exercises the full detection pipeline:
1. FactAnchor created from USGS event and linked
2. Settlement divergence detected (M6.2 vs M5.8) with scanner mock
3. Oracle consistency check (delta=0.4 triggers inconsistency)
4. Provisional upgrade produces INFO severity (not MATERIAL)

### T3.4: Regression Suite ✅

**File:** `backend/tests/test_038_sprint3_routes.py` — `TestRegression` class (3 tests)

Validates backward compatibility:
1. ParadoxEngine still importable
2. ParadoxRiskEvaluator produces correct assessments
3. `is_material_delta` works without `cross_theatre_exposure` key

### T3.5: Router Registration in main.py ✅

**File:** `backend/main.py` (modified)

4 routers registered with try/except guards (matching existing pattern):
- `fact_anchor_router`
- `coherence_group_router`
- `cross_paradox_router`
- `oracle_consistency_router`

---

## Test Results

```
74 passed, 0 failed (all 4 sprint test files)
```

Sprint-3 specific: 17/17 pass
- T3.1 route imports: 3/3
- T3.2 route imports: 7/7 (including transition validation)
- T3.3 TREMOR fixture: 4/4
- T3.4 regression: 3/3

### Test Environment Note

Route import tests (T3.1, T3.2) require real fastapi — must run with venv Python (`.venv/bin/python3`). Test file includes sys.modules cleanup to handle cross-contamination when run after earlier sprint test files that mock fastapi.

---

## Files Changed

| File | Status | Lines |
|------|--------|-------|
| `backend/api/fact_anchor_routes.py` | NEW | ~190 |
| `backend/api/coherence_group_routes.py` | NEW | ~150 |
| `backend/api/cross_theatre_paradox_routes.py` | NEW | ~190 |
| `backend/api/oracle_consistency_routes.py` | NEW | ~95 |
| `backend/main.py` | MODIFIED | +20 |
| `backend/tests/test_038_sprint3_routes.py` | NEW | ~300 |

---

## Design Decisions

1. **Try/except router registration**: Matches existing main.py pattern. Prevents one bad router from blocking the entire app.

2. **State transition validation**: `VALID_TRANSITIONS` dict at module level. Terminal states (RESOLVED, DISMISSED) absent from dict = no outbound transitions. 409 Conflict on invalid transition attempts.

3. **Auth boundaries**: POST/write endpoints require auth (`Depends(get_current_user)`). GET/read endpoints are public. Consistent with existing route patterns.

4. **sys.modules cleanup in tests**: Sprint-3 route tests clean up mocked fastapi entries from earlier test files to ensure real APIRouter registration. Required for cross-file test runs.

---

## Acceptance Criteria Status

- [x] FactAnchor routes: 5 endpoints, correct prefix, POST paths exist
- [x] CoherenceGroup routes: 5 endpoints including scan trigger
- [x] CrossTheatreParadox routes: 5 endpoints with state transitions
- [x] OracleConsistency routes: 3 endpoints
- [x] All routers registered in main.py
- [x] TREMOR fixture exercises full pipeline
- [x] Regression suite confirms backward compatibility
- [x] 74/74 tests pass across all sprint files
