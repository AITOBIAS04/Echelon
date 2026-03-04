# Sprint 8 Implementation Report

## Summary

Implemented all 7 tasks for Cycle-004 Sprint 1 (global Sprint 8): OSINT Pipeline Architectural Hardening. Changes span 7 modified files and 1 new file across the `osint_pipeline` library. All 49 tests pass (37 in test_architectural_concerns.py, 12 in test_canonical.py). A pre-existing Python 3.9 compatibility bug in the collection runner (catching `TimeoutError` instead of `concurrent.futures.TimeoutError`) was also fixed.

## Tasks Completed

### T1: AC-1 — GapKind Semantics
- **Files modified**: `collectors/base.py`
- **Changes**: Updated `to_gap_report()` to use a `STATUS_TO_GAP_KIND` mapping dict. `CollectionStatus.NOT_FOUND` maps to `GapKind.SIGNAL_ABSENCE` with `freshness=FreshnessState.NO_DATA`. All other failure statuses default to `GapKind.INTELLIGENCE_GAP` with `freshness=FreshnessState.ERROR`. Imported `GapKind` into base.py.

### T2: AC-5 — Canonical Hash NFC + Float Precision
- **Files modified**: `engine/canonical.py`
- **Changes**: Added `import unicodedata` and `import math`. Created `_nfc_normalise_strings()` recursive function for Unicode NFC normalisation of all strings in dicts, lists, and raw strings. Created `_RFC8785Encoder` custom JSON encoder class with shortest round-trip float representation and proper handling of -0.0, NaN/Infinity rejection. Updated `canonical_json()` to apply NFC normalisation before serialisation and use the custom encoder.

### T3: AC-3 — Runner-Level Receipt Mode Enforcement
- **Files modified**: `engine/collection_runner.py`
- **Changes**: Added `registry_sources: dict[str, RegistrySource] | None = None` parameter to `__init__()`, stored as `self.registry_sources`. Added pre-check in `run()` that loops through active collectors before thread pool submission, checking `meets_receipt_minimum()` for each collector with a registry source. Failing collectors are skipped with a `GapReport` (gap_kind=INTELLIGENCE_GAP, freshness=ERROR). Added imports for `ReceiptMode`, `meets_receipt_minimum`, `RegistrySource`, `FreshnessState`. Also fixed pre-existing Python 3.9 compatibility bug by catching `FuturesTimeoutError` alongside built-in `TimeoutError`.

### T4: AC-2 — Upstream Independence Naming
- **Files modified**: `models/evidence.py`
- **Changes**: Added `distinct_upstream_succeeded_count` property on `OracleCollectionSummary` that returns `self.distinct_upstream_count`. This is a semantic alias clarifying that only succeeded bundles are counted.

### T5: AC-4 — EvidenceScorer Module
- **Files created**: `engine/scorer.py` (NEW, 115 lines)
- **Files modified**: `collectors/base.py`, `engine/__init__.py`
- **Changes**: Created `EvidenceScorer` class with multiplicative penalty model: `REVISION_PENALTY` dict (immutable=1.0, as_of_timestamp=0.95, latest_only=0.80), `RATE_LIMIT_INSTABILITY_PENALTY=0.90`, `RECEIPT_AT_MINIMUM_PENALTY=0.95`, `SINGLE_SOURCE_CAP=0.95`. Implements `score_bundle()` and `composite_confidence()` (1 - product(1 - score_i)). Removed from `BaseCollector`: `FREE_SOURCE_CONFIDENCE_CAP` class attribute, `should_cap_confidence()` classmethod, and confidence capping block in `collect()`. Exported `EvidenceScorer` from `engine/__init__.py`.

### T6: AC-6 — Timeout Gap Reports + FailureMode
- **Files modified**: `models/evidence.py`, `collectors/base.py`, `engine/collection_runner.py`, `models/__init__.py`
- **Changes**: Added `FailureMode` enum (7 values: CONNECTION_REFUSED, DNS_FAILURE, TLS_ERROR, READ_TIMEOUT, RESPONSE_TOO_LARGE, HTTP_ERROR_4XX, HTTP_ERROR_5XX) and `RETRIABLE_FAILURES` frozenset (READ_TIMEOUT, HTTP_ERROR_5XX) to evidence.py. Added `failure_mode: FailureMode | None` and `retriable: bool` fields to `GapReport`. Added `gap_count` and `gap_sources` computed properties to `OracleCollectionSummary`. Added `STATUS_TO_FAILURE_MODE` mapping to `BaseCollector` and updated `to_gap_report()` to set failure_mode and retriable. Updated runner timeout gap creation to include `failure_mode=FailureMode.READ_TIMEOUT, retriable=True`. Exported `FailureMode` and `RETRIABLE_FAILURES` from `models/__init__.py`.

### T7: AC-INT — Integration Tests
- **Files modified**: `tests/test_architectural_concerns.py`
- **Changes**: Added 27 new test functions covering all architectural concerns. Updated 2 existing tests (`test_confidence_capped_for_latest_only_revision_policy` and `test_confidence_not_capped_for_public_api_as_of_timestamp`) to use `EvidenceScorer` instead of the removed `BaseCollector.should_cap_confidence()`.

## Tests

- **New tests added**: 27
- **Existing tests updated**: 2 (rewritten to use EvidenceScorer)
- **Total tests passing**: 49 (37 architectural concerns + 12 canonical)

### New test list:
1. `test_gap_kind_enum_has_two_values`
2. `test_to_gap_report_maps_not_found_to_signal_absence`
3. `test_to_gap_report_maps_timeout_to_intelligence_gap`
4. `test_to_gap_report_maps_network_error_to_intelligence_gap`
5. `test_canonical_json_nfc_normalisation`
6. `test_canonical_json_float_precision`
7. `test_canonical_json_rfc8785_test_vector`
8. `test_runner_rejects_insufficient_receipt_mode`
9. `test_runner_passes_sufficient_receipt_mode`
10. `test_distinct_upstream_succeeded_count_alias`
11. `test_null_upstream_id_counts_independently`
12. `test_scorer_immutable_no_penalty`
13. `test_scorer_latest_only_080_penalty`
14. `test_scorer_as_of_timestamp_095_penalty`
15. `test_scorer_single_source_capped_095`
16. `test_scorer_composite_exceeds_095`
17. `test_scorer_receipt_at_minimum_penalty`
18. `test_base_collector_no_confidence_cap`
19. `test_failure_mode_enum_values`
20. `test_gap_report_failure_mode_and_retriable`
21. `test_5xx_produces_retriable_gap`
22. `test_dns_failure_not_retriable`
23. `test_gap_count_and_gap_sources`
24. `test_no_silent_source_drops`
25. `test_allow_gap_false_intelligence_gap_fails`
26. `test_allow_gap_true_intelligence_gap_passes`
27. `test_end_to_end_pipeline_integration`

## Files Modified

| File | Lines | Action |
|------|-------|--------|
| `collectors/base.py` | 366 | Modified (GapKind mapping, FailureMode mapping, removed confidence cap) |
| `engine/canonical.py` | 237 | Modified (NFC normalisation, RFC 8785 float encoder) |
| `engine/collection_runner.py` | 281 | Modified (registry_sources param, receipt mode pre-check, FuturesTimeoutError fix) |
| `engine/scorer.py` | 115 | **New** (EvidenceScorer class) |
| `engine/__init__.py` | 8 | Modified (export EvidenceScorer) |
| `models/evidence.py` | 326 | Modified (FailureMode enum, GapReport fields, OracleCollectionSummary properties) |
| `models/__init__.py` | 23 | Modified (export FailureMode, RETRIABLE_FAILURES) |
| `tests/test_architectural_concerns.py` | 948 | Modified (27 new tests, 2 updated tests) |
| **Total** | **2304** | |

## Bonus Fix

Fixed a pre-existing Python 3.9 compatibility bug in `collection_runner.py` where `TimeoutError` was caught but Python 3.9's `concurrent.futures` raises `concurrent.futures._base.TimeoutError` (a separate class). Now catches both via `from concurrent.futures import TimeoutError as FuturesTimeoutError`.
