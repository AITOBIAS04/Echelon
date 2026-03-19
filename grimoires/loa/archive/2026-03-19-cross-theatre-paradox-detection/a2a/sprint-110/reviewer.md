# Sprint 2 (Global 110) Implementation Report — Scanner + Integration

**Cycle:** 038 — Cross-Theatre Paradox Detection
**Sprint:** 2 (Scanner + Integration)
**Date:** 19 March 2026
**Status:** COMPLETE — 21 tests passing, 0 regressions (57/57 full suite)

---

## Tasks Completed

### T2.1: CrossTheatreParadoxScanner — Settlement Divergence ✅

**File:** `backend/services/cross_theatre_paradox_scanner.py` (new, ~390 lines)

- Implemented `CrossTheatreParadoxScanner` class with `AsyncSession` dependency
- `scan_fact_anchor()` orchestration: fetches all links for an anchor, iterates pairs, evaluates settlement divergence + oracle inconsistency + temporal drift
- `evaluate_settlement_divergence()`: compares `metadata_json.outcome` for `settlement` link types
  - MATERIAL if both theatres active, WATCH if one superseded, None if same outcome
- Theatre ordering: `_order_theatres()` enforces lexicographic `theatre_a_id < theatre_b_id` for dedup
- Dedup: `_check_existing()` queries OPEN records with same (anchor, theatre_a, theatre_b, type)
- **Tests (5):** detects opposite outcomes, skips same, dedup works, ordering enforced, non-settlement ignored

### T2.2: CrossTheatreParadoxScanner — Oracle Inconsistency + Provisional Rule ✅

**File:** `backend/services/cross_theatre_paradox_scanner.py`

- `evaluate_oracle_inconsistency()`: queries OracleResponse for same event across theatres
  - Same source + delta > threshold → MATERIAL
  - Cross-source → WATCH
  - Provisional (automatic → reviewed) → INFO per context_038 rule
- `_is_provisional_revision()`: checks `response_type` field (automatic vs reviewed)
- `_compute_oracle_delta()`: computes max absolute delta across all numeric fields in `value_json`
- `_get_oracle_responses()`: queries OracleResponse by theatre_id + event_id
- **Tests (4):** same-source MATERIAL, cross-source WATCH, provisional INFO, within tolerance no paradox

### T2.3: CrossTheatreParadoxScanner — Scope Overlap + Temporal Drift ✅

**File:** `backend/services/cross_theatre_paradox_scanner.py`

- `scan_coherence_group()`: fetches group members + anchors, evaluates scope overlap
- `evaluate_scope_overlap()`: detects missing anchor links for group members → WATCH
- `evaluate_temporal_drift()`: compares `occurred_at` timestamps in anchor metadata
  - `> window` → INFO, `> 2x window` → WATCH, `<= window` → None
- **Tests (4):** scope gap detected, drift > window = INFO, drift > 2x = WATCH, within window = None

### T2.4: ParadoxRiskOrchestrator Extension ✅

**File:** `backend/services/paradox_risk_orchestrator.py` (modified)

- Added `compute_cross_theatre_exposure()`: counts OPEN MATERIAL+ CrossTheatreParadox records for a theatre (using `or_` for theatre_a_id/theatre_b_id)
- Added `cross_theatre_exposure: Optional[int] = None` parameter to `trigger_recompute()`
- When not provided, auto-queries via `compute_cross_theatre_exposure()`
- Added `cross_theatre_exposure` to assessment factors dict
- Floor logic: `>= 1 exposure` → minimum WATCH, `>= 3` → minimum HIGH
- Added `cross_theatre_exposure` change to `is_material_delta()`
- **Tests (3):** floor WATCH, floor HIGH, exposure change is material

### T2.5: WingFlap + WebSocket Integration ✅

**Files:**
- `backend/services/cross_theatre_paradox_scanner.py` — `_record_wingflap()` + `_broadcast_cross_theatre_paradox()`
- `backend/websockets/realtime_manager.py` — Added `broadcast_cross_theatre_paradox()` method

- `_record_wingflap()`: creates WingFlap with type `CROSS_THEATRE_PARADOX`, `stability_delta=-0.15`, `DESTABILISE` direction for each affected theatre
- Only for MATERIAL or CRITICAL severity
- `broadcast_cross_theatre_paradox()`: broadcasts `CROSS_THEATRE_PARADOX_DETECTED` to both `theatre:{id}` channels
- **Tests (3):** wingflap created for material, websocket broadcast, scan triggers wingflaps

### T2.6: FactAnchorService Scanner Wiring ✅

**File:** `backend/services/fact_anchor_service.py` (modified)

- Wired `link_theatre()`: when `should_scan=True` (>= 2 distinct theatres), calls `CrossTheatreParadoxScanner.scan_fact_anchor()`
- Collects affected theatre IDs from detected paradoxes
- Calls `trigger_recompute()` for each affected theatre with `emit_ws=True`
- Uses deferred imports to avoid circular dependency
- **Tests (2):** link triggers scanner, no scan for single theatre

---

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/services/cross_theatre_paradox_scanner.py` | Created | ~390 |
| `backend/services/paradox_risk_orchestrator.py` | Modified | +35 |
| `backend/services/fact_anchor_service.py` | Modified | +18 |
| `backend/websockets/realtime_manager.py` | Modified | +27 |
| `backend/tests/test_038_sprint2_scanner.py` | Created | ~550 |
| `backend/tests/test_038_sprint1_services.py` | Modified | +2 (patch path fix) |

**Total:** 4 production files (1 new, 3 modified), 2 test files (1 new, 1 modified)

---

## Test Results

```
57 passed in 0.27s

Sprint 0 (models):    18/18 ✅
Sprint 1 (services):  18/18 ✅
Sprint 2 (scanner):   21/21 ✅
```

### Test Coverage by Task

| Task | Tests | Pattern |
|------|-------|---------|
| T2.1 Settlement | 5 | SimpleNamespace + MockAsyncSession |
| T2.2 Oracle | 4 | SimpleNamespace + MockAsyncSession |
| T2.3 Scope/Drift | 4 | SimpleNamespace + MockAsyncSession |
| T2.4 Orchestrator | 3 | Direct function calls with mock factors |
| T2.5 WingFlap/WS | 3 | AsyncMock + patch |
| T2.6 Wiring | 2 | Patch at source module for deferred imports |

---

## Design Decisions

1. **SimpleNamespace over SQLAlchemy models in tests**: SQLAlchemy instrumented attributes cause `AttributeError` with `__new__` pattern. SimpleNamespace factory functions (`make_anchor()`, `make_link()`, etc.) provide clean test objects.

2. **Deferred imports in fact_anchor_service**: Scanner and orchestrator are imported inside `link_theatre()` to avoid circular imports. Tests patch at source module (`backend.services.cross_theatre_paradox_scanner.CrossTheatreParadoxScanner`) not at import site.

3. **Python 3.9 compatibility**: `realtime_manager.py` uses `dict | None` (3.10+ syntax). Tests mock `backend.websockets.realtime_manager` via `sys.modules` to avoid importing it.

4. **Theatre ordering for dedup**: Lexicographic `theatre_a_id < theatre_b_id` ensures the same paradox is never recorded twice with swapped theatre IDs.

5. **Provisional oracle rule**: USGS automatic → reviewed revision = INFO, not MATERIAL. Prevents routine data pipeline upgrades from triggering high-severity paradoxes.

---

## Acceptance Criteria Verification

- ✅ Settlement divergence detects opposite outcomes (MATERIAL), skips same outcomes
- ✅ Oracle inconsistency: same-source MATERIAL, cross-source WATCH, provisional INFO
- ✅ Scope overlap detected as WATCH when primary member missing link
- ✅ Temporal drift: > window = INFO, > 2x window = WATCH
- ✅ Exposure floor: >= 1 → WATCH, >= 3 → HIGH
- ✅ Exposure change triggers material delta
- ✅ WingFlap created for MATERIAL+ paradoxes (both theatres)
- ✅ WebSocket CROSS_THEATRE_PARADOX_DETECTED emitted for MATERIAL/CRITICAL
- ✅ link_theatre() triggers scanner when >= 2 theatres linked
- ✅ Full pipeline: link → scan → detect → wingflap → ws → recompute
- ✅ Zero regression across sprint-0 and sprint-1 tests
