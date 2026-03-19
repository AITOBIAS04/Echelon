# Sprint 125 (cycle-039 sprint-1) — Implementation Report

## Goal
Build the operations service as a composition layer over 038b + 038c.

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backend/services/external_theatre_operations_service.py` | Composition layer: register/unregister, execute_run (038b→038c→persist), registry updates | ~210 |

## Files Modified

| File | Change | Lines Added |
|------|--------|-------------|
| `tests/test_external_theatre_operations.py` | Sprint 1 tests: 3 classes, 11 new tests | ~250 |

## Tasks Completed

1. **Operations service as composition layer** — `ExternalTheatreOperationsService` wraps the registry store and delegates to `prepare_external_theatres()` (038b) and `scan_candidates()` (038c). No duplication of orchestration or scan logic.
2. **Register/unregister external theatres** — `register_theatre()` and `unregister_theatre()` proxy to store with service-level API.
3. **Persist run records with spec_hash** — `execute_run()` creates IN_PROGRESS run, calls 038b→038c, builds summary, completes/fails the run record. `spec_hash` computed from SHA-256 of construct.json content.
4. **Service tests** — 11 tests across 3 classes covering registration, unregistration, successful runs, paradox detection, no-candidate runs, failure handling, spec hash determinism, feedback snapshot persistence, registry updates, and run store retrieval.

## Design Decisions

- **Composition, not reimplementation**: The service calls `prepare_external_theatres()` and `scan_candidates()` directly. No orchestration or classification logic is duplicated.
- **Feedback snapshot**: Builder feedback from 038b is extracted into a flat list of dicts for persistence. The original `BuilderFeedbackReport` structure is preserved per-construct with readiness and items.
- **Registry auto-update**: After a successful run, the service updates `last_prepared_at`, `last_scanned_at`, and `latest_summary` on matching registry entries.
- **Spec hash**: Combined hash of per-theatre construct.json hashes, using SHA-256 via the store's `compute_spec_hash()`.
- **Error isolation**: If 038b or 038c throws, the run is marked FAILED with error summary. No partial state leaks.

## Test Results

```
25 passed in 0.13s
```
