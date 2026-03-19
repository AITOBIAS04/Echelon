# Sprint 127 (cycle-039 sprint-3) — Implementation Report

## Goal

Add builder-facing status reporting surface with readiness derivation per SDD 2.5.

## Files Modified

| File | Change | Lines Added |
|------|--------|-------------|
| `backend/services/external_theatre_operations_service.py` | Added `get_status_report()`, `list_status_reports()`, `_rollup_feedback()`, `_derive_readiness()` | ~110 |
| `tests/test_external_theatre_operations.py` | Sprint 3 tests: 4 classes, 12 new tests | ~200 |

## Tasks Completed

1. **Per-theatre status report** — `get_status_report(slug, recent_run_limit=5)` composes registry state + recent runs + feedback rollup + readiness into `ExternalTheatreStatusReport`. Returns `None` for nonexistent theatres.
2. **Bulk status listing** — `list_status_reports(active_only=True, recent_run_limit=3)` delegates to `get_status_report()` per theatre; supports active-only or all-theatre filtering.
3. **Feedback rollup** — `_rollup_feedback()` returns the most recent completed run's `feedback_snapshot`. Simple V1 approach consistent with progressive tier pattern.
4. **Readiness derivation** — `_derive_readiness()` implements 3-state machine: READY (active + completed + no paradox), DEGRADED (active + completed + paradox), BLOCKED (inactive, failed, no runs, or in-progress).
5. **Reporting tests** — 12 tests across 4 classes: `TestGetStatusReport` (3 tests: successful run report, nonexistent theatre, no runs), `TestReadinessDerivation` (5 tests: READY, DEGRADED, blocked-inactive, blocked-no-runs, blocked-failed), `TestFeedbackRollup` (2 tests: completed run feedback, empty no runs), `TestListStatusReports` (2 tests: active-only filtering, all includes inactive).

## Design Decisions

- **Composition over duplication**: `get_status_report()` reuses store methods (`get_by_slug`, `list_runs`) and Sprint 3 helpers (`_rollup_feedback`, `_derive_readiness`). No new store methods needed.
- **Readiness as derived state**: Not persisted — computed fresh from registry + latest run. Prevents stale readiness when runs complete or paradox state changes.
- **Simple feedback rollup**: Returns most recent completed run's snapshot rather than cross-run aggregation. Matches SDD 2.5's V1 scope.
- **No public API routes**: Per SDD 2.4 — these are internal service methods. Builder-facing surface will be exposed via API routes in a future cycle.
- **`_make_inputs` test helper**: Extracted to reduce boilerplate for Sprint 3 tests that need `ExternalTheatreInput` lists.

## Test Results

```
47 passed in 0.17s
```
