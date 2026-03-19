# Sprint 117 (Cycle-038b Sprint 1) — Reviewer Report

**Sprint:** 1 (Global ID: 117)
**Cycle:** 038b — External Theatre Orchestration
**Focus:** Enriched Fixture Extraction
**Date:** 19 March 2026
**Builder:** Loa

---

## Summary

Sprint 1 implements the enriched fixture extractor service (`external_theatre_fixture_extractor.py`) that generates realistic `TheatreFixtureInput` from construct metadata, including BOTH passing and failing scenarios. This is a separate extraction path from the existing `theatre_fixture_loader.py` and does not modify it.

## Deliverables

### New Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/services/external_theatre_fixture_extractor.py` | Enriched fixture extraction from construct metadata | ~260 |

### Modified Files

| File | Change |
|------|--------|
| `backend/tests/test_038b_external_orchestration.py` | Added 11 Sprint 1 tests (18 total cumulative) |

## Test Results

```
18 passed in 0.23s
```

- Sprint 0 (schemas): 7 passed (no regressions)
- Sprint 1 (extraction): 11 passed (all new)

### Sprint 1 Test Breakdown

| # | Test | Status |
|---|------|--------|
| 8 | `test_tremor_enriched_settlement_pass_and_fail` | PASSED |
| 9 | `test_tremor_enriched_oracle_consistent_and_divergent` | PASSED |
| 10 | `test_tremor_enriched_calibration_multi_class` | PASSED |
| 11 | `test_tremor_enriched_functional_pass_and_fail` | PASSED |
| 12 | `test_corona_enriched_settlement_pass_and_fail` | PASSED |
| 13 | `test_corona_enriched_oracle_with_default_threshold` | PASSED |
| 14 | `test_corona_enriched_calibration_binary` | PASSED |
| 15 | `test_corona_enriched_functional_pass_and_fail` | PASSED |
| 16 | `test_extraction_missing_construct_json` | PASSED |
| 17 | `test_extraction_empty_templates` | PASSED |
| 18 | `test_extraction_malformed_metadata` | PASSED |

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| Module importable: `from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture` | MET |
| TREMOR: 5 settlement (3 pass, 2 fail), 2 oracle (1 consistent, 1 divergent), calibration multi_class, 5 functional, no fallbacks | MET |
| CORONA: 5 settlement (3 pass, 2 fail), 2 oracle (1 consistent, 1 divergent), calibration binary, 5 functional, fallbacks include oracle_threshold_defaulted | MET |
| Never raises -- returns (ExtractionResult(success=False), None) on failure | MET |
| Sprint 0 tests still pass (7) | MET |
| Sprint 1 tests pass (11 new, 18 cumulative) | MET |

## Design Decisions

1. **Even/odd pass/fail strategy**: Even-indexed templates pass, odd-indexed fail. Single template always passes. This is deterministic and guarantees at least one of each when templates > 1.

2. **Multi-class handling**: Templates with `resolution="multi_bucket"` or `"multi_class"` get bucket outcomes (`"bucket_0"`, `"bucket_2"`) rather than binary `"YES"`/`"NO"`.

3. **Oracle threshold derivation**: When `verification_checks` is empty (CORONA), threshold defaults to 0.5 and `"oracle_threshold_defaulted"` is tracked in fallbacks. When present (TREMOR), no fallback is recorded.

4. **Brier type derivation**: Scans templates for `brier_type="multi_class"` (TREMOR's aftershock_cascade has it). When no template declares brier_type (CORONA), defaults to `"binary"` with `"brier_type_defaulted"` fallback.

5. **Functional fixture strategy**: First template valid, last template invalid (if >1 templates), middle templates alternate. Single template always valid.

6. **Error handling**: The public function never raises. All internal failures are caught and returned as `ExtractionResult(success=False, error=msg)` with `fixture=None`.

## Architecture Notes

- The extractor is a pure function with no database or network dependencies
- It imports from `theatre_policy_rules.py` (037d) for data types only
- It does NOT call `parse_construct_json()` -- it receives the already-parsed `TheatreConstructMeta`
- The `_compute_expected_brier()` function matches the algorithm in `theatre_fixture_loader.py`
- Fixture dict structures match what `theatre_check_runner.py` expects (verified by reading runner dispatch code)

## Risks

None identified. The extractor is isolated, tested, and follows the existing fixture loader pattern exactly.

## Next Sprint

Sprint 2 (Global ID: 118) — Orchestrator Composition: compose extraction + check execution + bundle building + candidate generation into `prepare_external_theatres()`.
