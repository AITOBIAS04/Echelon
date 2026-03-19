# Sprint 126 (cycle-039 sprint-2) — Implementation Report

## Goal
Make external theatre runs invokable through a first-class trigger/scheduling surface.

## Files Modified

| File | Change | Lines Added |
|------|--------|-------------|
| `backend/services/external_theatre_operations_service.py` | Added `trigger_run()` and `trigger_all_active()` with idempotence + active-state guards | ~100 |
| `tests/test_external_theatre_operations.py` | Sprint 2 tests: 3 classes, 10 new tests | ~170 |

## Tasks Completed

1. **Internal trigger method** — `trigger_run()` with stable scheduler-facing signature: takes `theatre_slugs`, `construct_json_map`, optional `event_keys`/`scope_keys`/`certificate_id`. Returns `(run_record, status)` tuple where status is `"started"`, `"duplicate"`, or `"failed"`.
2. **Manual trigger path** — `trigger_all_active()` convenience method scans all active theatres. Same service boundary as `trigger_run()`.
3. **Idempotence enforcement** — Three guards before execution: (a) all theatres must be registered, (b) all must be active, (c) no IN_PROGRESS run for the same theatre set. Duplicate detection is order-independent per store's `has_active_run()`.
4. **Invocation tests** — 10 tests across 3 classes: `TestTriggerRun` (4 tests: success, unregistered rejection, inactive rejection, missing JSON), `TestTriggerIdempotence` (3 tests: duplicate returns active, completed allows new trigger, order-independent), `TestTriggerAllActive` (3 tests: success, no theatres, missing JSON).

## Design Decisions

- **ValueError for guard violations**: `trigger_run()` raises ValueError for unregistered, inactive, or missing construct.json. These are caller errors, not operational failures.
- **Tuple return**: `(run_record, status_string)` enables callers to distinguish started vs duplicate vs failed without inspecting run internals.
- **Duplicate returns existing run**: Per SDD 2.4 — "return the active run record or a stable duplicate-run status." We return the existing active run with status `"duplicate"`.
- **No public API routes**: Per SDD 2.4 — "Do not add public or admin API routes in V1." Both methods are internal service calls.

## Test Results

```
35 passed in 0.16s
```
