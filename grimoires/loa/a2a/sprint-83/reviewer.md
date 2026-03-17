# Sprint 83 — Review Report

**Cycle:** cycle-025 (WorldMonitor Intelligence Contract v2)
**Sprint:** sprint-2 (local) / sprint-83 (global)
**Label:** Read Endpoints + Convergence
**Reviewed:** 2026-03-17

---

## Verdict: PASS

All 10 tests pass. All three read endpoints are implemented with correct query logic. ConvergenceScorer produces cells for multi-domain clusters.

---

## Implementation Summary

### Files Modified/Created

| File | Action | Purpose |
|------|--------|---------|
| `backend/api/osint_routes.py` | Rewritten | 3 GET endpoints: /signals, /health, /signals/summary |
| `backend/services/convergence_scorer.py` | Created | ConvergenceScorer with geo/time clustering |
| `backend/tests/test_cycle025_sprint2.py` | Created | 10 unit tests covering all 4 tasks |

### Task 1: GET /api/v1/osint/signals (3 tests)

- Queries `osint_signals` table ordered by `collected_at DESC`
- Filters: `source_group`, `investigation_id`, `since` (all optional)
- Pagination via `limit` (1-200, default 50) / `offset` (>=0)
- Returns `PaginatedSignalsResponse` with signals list + pagination metadata
- Tests: unfiltered returns signals, source_group filter narrows, investigation_id filter narrows

### Task 2: GET /api/v1/osint/health (2 tests)

- `feeds_total`: count from RegistryLoader sources dict
- `feeds_online`: distinct source_ids with signal in last hour
- `signal_latency_sec`: seconds since most recent signal (null if none)
- `escalation_queue_depth`: ACTIVE investigations count (status heuristic as specified)
- `replay_workers_active`: hardcoded 0 (no replay workers yet)
- Tests: healthy state (6 feeds, 3 online, 41s latency, 2 escalated), degraded state (0/0/null/0)

### Task 3: GET /api/v1/osint/signals/summary (2 tests)

- `total_signals`: COUNT from osint_signals
- `by_source_group`: GROUP BY source_group dict
- `counter_signals`: count of signals from sources with resolution_role="counter_signal" (registry-driven)
- `certificate_candidates`: investigations in CERTIFICATE_READY status
- `convergence_cells`: hardcoded 0 placeholder (will be populated once scorer runs in pipeline)
- Tests: empty state (all zeros), populated state (15 total, 3 groups, 3 counter, 1 candidate)

### Task 4: ConvergenceScorer (3 tests)

- Location: `backend/services/convergence_scorer.py`
- Clusters signals by `(geo_region, time_bucket)` where time_bucket = epoch_seconds // window_seconds
- Emits `ConvergenceCell` for clusters with 2+ distinct `source_group` domains
- Score formula: `domain_count / total_domains` (total from WMDomain enum: 3 domains)
- Tests: single domain no cell, two domains emits cell (score > 0, correct geo_region), empty input no cells

---

## Test Results

```
backend/tests/test_cycle025_sprint2.py::TestGetSignalsEndpoint::test_unfiltered_returns_signals PASSED
backend/tests/test_cycle025_sprint2.py::TestGetSignalsEndpoint::test_source_group_filter PASSED
backend/tests/test_cycle025_sprint2.py::TestGetSignalsEndpoint::test_investigation_id_filter PASSED
backend/tests/test_cycle025_sprint2.py::TestGetOsintHealthEndpoint::test_healthy_state PASSED
backend/tests/test_cycle025_sprint2.py::TestGetOsintHealthEndpoint::test_degraded_state_no_recent_signals PASSED
backend/tests/test_cycle025_sprint2.py::TestGetSignalsSummaryEndpoint::test_empty_state PASSED
backend/tests/test_cycle025_sprint2.py::TestGetSignalsSummaryEndpoint::test_populated_state PASSED
backend/tests/test_cycle025_sprint2.py::TestConvergenceScorer::test_single_domain_no_cell PASSED
backend/tests/test_cycle025_sprint2.py::TestConvergenceScorer::test_two_domains_emits_cell PASSED
backend/tests/test_cycle025_sprint2.py::TestConvergenceScorer::test_empty_input PASSED

10 passed in 0.61s
```

---

## Observations

1. **datetime.utcnow() deprecation**: Both osint_routes.py and tests use `datetime.utcnow()` which is deprecated in Python 3.12+. Non-blocking, consistent with existing codebase patterns.

2. **Pydantic v2 Config deprecation**: `OsintSignalResponse` uses class-based `Config` instead of `ConfigDict`. Non-blocking warning.

3. **convergence_cells hardcoded to 0**: The summary endpoint returns a placeholder. This is intentional per the sprint plan — the scorer exists but is not yet wired into the summary endpoint pipeline. Sprint 3 integration will address this.

4. **WMDomain import path**: ConvergenceScorer imports from `backend.osint.models.evidence` which re-exports from `backend.schemas.worldmonitor_api_contract`. Chain is valid but adds indirection.

5. **Path 2 isolation**: No imports from `backend/core/signal_detector.py` or `backend/core/osint_registry.py` in any sprint-2 files. Path 2 remains untouched.

---

## Exit Criteria Check

| Criterion | Status |
|-----------|--------|
| 10 tests pass | PASS |
| GET /signals returns data | PASS |
| GET /health returns data | PASS |
| GET /signals/summary returns data | PASS |
| ConvergenceScorer produces cells | PASS |
