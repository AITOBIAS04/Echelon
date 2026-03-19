# Implementation Report — Sprint 116 (Sprint 0: Schemas + Extraction Contracts)

**Cycle:** cycle-038b
**Sprint:** sprint-0 (global: 116)
**Date:** 19 March 2026

## Tasks Completed

### Task 0.1 — Create orchestration schema module

**File:** `backend/schemas/external_theatre_orchestration.py` (NEW)

Created 7 Pydantic models per SDD section 2.1:

| Model | Purpose |
|-------|---------|
| `ExternalTheatreInput` | Descriptor for a single external theatre (slug, version, raw JSON, optional path) |
| `ExternalTheatrePreparationRequest` | Full orchestration request (theatres, event_keys, scope_keys, certificate_id) |
| `ExtractionResult` | Per-theatre extraction summary (success, fixture counts, fallbacks, error) |
| `TheatrePreparationEntry` | Per-theatre result within orchestration (extraction, bundle, execution state, error) |
| `BuilderFeedbackItem` | Single feedback item (category, field, status, message) |
| `BuilderFeedbackReport` | Per-theatre builder feedback (required/optional/extraction items, readiness) |
| `ExternalTheatrePreparationResult` | Complete orchestration result (theatres, candidates, feedback, totals) |

Imports from existing 038a schemas: `TheatreScopeKey`, `ExecutedTheatreComparisonBundle`, `ComparisonCandidateSet`.

### Task 0.2 — Create test file with Sprint 0 schema tests

**File:** `backend/tests/test_038b_external_orchestration.py` (NEW)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_external_theatre_input_constructs` | Required fields accepted, `construct_json_path` defaults to None |
| 2 | `test_preparation_request_defaults` | `event_keys=[]`, `scope_keys=[]`, `certificate_id=None` defaults |
| 3 | `test_preparation_result_serializes` | Round-trip through `model_dump()` and reconstruction |
| 4 | `test_extraction_result_success_shape` | All fixture counts accessible on success=True |
| 5 | `test_extraction_result_failure_shape` | Defaults to zero counts on success=False, error populated |
| 6 | `test_builder_feedback_report_categories` | Three distinct category lists with correct item categories |
| 7 | `test_builder_feedback_readiness_states` | READY, DEGRADED, BLOCKED all accepted; default empty lists |

## Test Results

```
7 passed in 0.21s
```

## Files Changed

| File | Status |
|------|--------|
| `backend/schemas/external_theatre_orchestration.py` | NEW (7 Pydantic models) |
| `backend/tests/test_038b_external_orchestration.py` | NEW (7 tests) |

## Decisions and Deviations

None. All models match the SDD section 2.1 specification exactly. No deviations from the sprint plan.

- Used `unittest.TestCase` pattern matching `test_037e_theatre_execution.py`
- Used same DB mock preamble as existing test files for import safety
- `construct_json` is `str` (raw content, not path) per SDD decision
- All defaults match SDD field definitions
