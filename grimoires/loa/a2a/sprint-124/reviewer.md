# Sprint 124 (cycle-039 sprint-0) — Implementation Report

## Goal
Define persistent external theatre registry and run-record shapes.

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backend/schemas/external_theatre_operations.py` | Pydantic schemas: RegistryEntry, RunRecord, RunSummary, StatusReport, enums | ~120 |
| `backend/services/external_theatre_registry_store.py` | In-memory store: registry CRUD, run lifecycle, idempotence check | ~190 |
| `tests/test_external_theatre_operations.py` | Sprint 0 tests: 4 classes, 14 tests | ~230 |

## Tasks Completed

1. **Registry persistence model** — `ExternalTheatreRegistryEntry` with all SDD 2.1 fields: slug, version, construct_class, repo_path, construct_json_path, status, is_active, last_prepared_at, last_scanned_at, latest_summary
2. **Run-record persistence model** — `ExternalTheatreRunRecord` with SDD 2.2 fields: theatre_slugs, started_at, completed_at, status, spec_hash, contract_hash, preparation_summary, scan_summary, result_counts, feedback_snapshot
3. **Schemas and store** — `ExternalTheatreRegistryStore` with register/get/list/deactivate/activate + create_run/complete_run/fail_run/list_runs/has_active_run. V1 in-memory (progressive tier: V2 = DB bridge)
4. **Tests** — 14 tests across 4 classes covering schema defaults, full-field population, no-paradox as positive state, store CRUD, run lifecycle, idempotence, and filtering

## Design Decisions

- **V1 in-memory store** rather than SQLAlchemy/Alembic: consistent with 038b/038c pure-function pattern. SDD allows "JSON-backed operational model." DB bridge is a clean future swap.
- **`has_active_run()` for idempotence**: compares theatre slug sets to detect duplicate in-progress runs (PRD 2.3 contract)
- **`ExternalTheatreRunSummary.has_paradox`**: explicit boolean — no-paradox is a positive operational state, not absence (PRD 2.5)
- **`model_copy()` on all reads**: prevents accidental mutation of store state

## Test Results

```
14 passed in 0.10s
```
