# Sprint 2 (Global 44) — Implementation Report

**Sprint:** sprint-2 (global: 44)
**Cycle:** cycle-017 (Policy Surface)
**Task:** TAO Flow Metrics
**Date:** 2026-03-06

## Summary

Built windowed capital flow aggregation for timelines. Computes net inflow over 24h and 7d windows from TRADE and MIRROR_TRADE wing flaps. Integrated into game loop at 60s cadence. Surfaced via API and frontend with feature-flagged badges.

## Tasks Completed

### Task 2.1: TaoFlowAggregator Service

**New file:** `backend/services/tao_flow_aggregator.py`

- `TaoFlowAggregator` class with two methods:
  - `compute_for_timeline(session, timeline_id, now)` — windowed SUM of TRADE + MIRROR_TRADE `volume_usd` for 24h and 7d windows
  - `compute_all(session)` — iterates active timelines, computes flow, persists to `net_inflow_24h`, `net_inflow_7d`, `flow_updated_at`
- Uses `func.coalesce(func.sum(...), 0.0)` for zero-safe aggregation
- Leverages existing `ix_wing_flaps_timeline_time` composite index for efficient windowed queries

### Task 2.2: Game Loop Integration

**Modified:** `backend/worker/game_loop.py`

- Added `TaoFlowAggregator` import and instance
- Added `tao_flow` entry to `self.intervals` (60s cadence) and `self.last_run`
- Added `_tao_flow_task` method that calls `compute_all` and logs update count
- Positioned before genesis task in `_run_due_tasks`

### Task 2.3: API Response Extensions

**Modified:** `backend/mechanics/butterfly_engine.py`

- Added `net_inflow_24h` and `net_inflow_7d` pass-through in `get_timeline_health_async` (line 699-700)
- Uses `getattr(timeline, 'net_inflow_24h', 0.0) or 0.0` for safe defaults
- Schema fields already existed from Sprint 0 (`butterfly_schemas.py:158-159`)

### Task 2.4: Frontend Flow Badges

**Modified files:**
- `frontend/src/pages/WorldMonitorPage.tsx` — `FlowBadge` component on timeline cards
- `frontend/src/components/marketplace/MarketCard.tsx` — inline flow badge on market cards
- `frontend/src/types/index.ts` — added `net_inflow_24h?`, `net_inflow_7d?` to Timeline interface
- `frontend/src/types/marketplace.ts` — added `net_inflow_24h?`, `net_inflow_7d?` to Market interface

Badge behavior:
- Green (`emerald-500`) for positive inflow
- Red (`red-500`) for negative inflow
- Grey (`neutral-500`) for zero
- Formatted: `+$1.2k` / `-$567` / `$0`
- Tooltip shows exact value
- Gated behind `isEnabled('CYCLE_017_TAO_FLOW')`

## Tests

**File:** `backend/tests/test_c017_sprint2_tao_flow.py` — 6 tests

| # | Test | Status |
|---|------|--------|
| 1 | 24h window mixed trades — correct net | PASS |
| 2 | 7d window computation | PASS |
| 3 | Zero trades returns (0.0, 0.0) | PASS |
| 4 | Game loop has tao_flow at 60s cadence | PASS |
| 5 | TimelineHealth schema has flow fields | PASS |
| 6 | compute_all updates timelines | PASS |

**Regression check:** 18/18 cycle-017 tests passing (4 Sprint 0 + 8 Sprint 1 + 6 Sprint 2)

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/services/tao_flow_aggregator.py` | NEW | 96 |
| `backend/worker/game_loop.py` | MODIFIED | +17 |
| `backend/mechanics/butterfly_engine.py` | MODIFIED | +2 |
| `backend/tests/test_c017_sprint2_tao_flow.py` | NEW | 190 |
| `frontend/src/pages/WorldMonitorPage.tsx` | MODIFIED | +25 |
| `frontend/src/components/marketplace/MarketCard.tsx` | MODIFIED | +18 |
| `frontend/src/types/index.ts` | MODIFIED | +4 |
| `frontend/src/types/marketplace.ts` | MODIFIED | +2 |
| `grimoires/loa/ledger.json` | MODIFIED | sprint-2 registered |
