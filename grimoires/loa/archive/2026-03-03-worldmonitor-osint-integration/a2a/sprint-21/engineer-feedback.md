# Sprint 21 Engineer Feedback — Evidence Pipeline Core + WorldMonitor Collector

**Reviewer**: Senior Technical Lead (adversarial review)
**Cycle**: 011 (local sprint-1, global sprint-21)
**Date**: 2026-03-03
**Verdict**: APPROVED

All good.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All 68 new OSINT tests pass | PASS |
| All 242 market + engines regression tests pass | PASS |
| No modifications to `backend/market/` | PASS (git diff empty) |
| No modifications to `backend/engines/` | PASS (git diff empty) |
| `from __future__ import annotations` in all 18 .py files | PASS |
| No new runtime dependencies (stdlib only) | PASS |
| No bare excepts | PASS |
| No httpx/aiohttp/requests imports | PASS |
| Python 3.9.6 compatibility | PASS |
| API contract model alignment | PASS |
| Registry alignment (PRD Section 4.6) | PASS |

---

## Acceptance Criteria Verification

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | `canonical_json()` deterministic (sorted keys, compact, no ASCII escape) | PASS | 7 tests in `TestCanonicalJson` covering determinism, sorted keys, compact separators, unicode, nested, empty, deep nesting |
| 2 | `compute_content_hash()` and `compute_receipt_hash()` re-exports match API contract | PASS | `TestCrossVerification` asserts exact equality between re-exports and contract originals |
| 3 | `BaseCollector` enforces receipt invariants | PASS | Invariant 1 (content_hash) and Invariant 2 (receipt_hash) checked in `_enforce_hash_invariants`, converts to `success=False` on mismatch |
| 4 | WM collector calls correct endpoint per domain | PASS | `_DOMAIN_ENDPOINTS` dict verified in `test_domain_endpoint_mapping`, per-domain fetch tests verify source_id and source_group |
| 5 | WM collector produces valid `EvidenceBundle` with `HTTPTranscriptReceipt` | PASS | `test_cii_fetch_success`, `test_market_fetch_success`, `test_maritime_fetch_success` all verify bundle fields |
| 6 | WM collector handles timeout, HTTP errors, malformed responses (no raise) | PASS | `test_timeout_error`, `test_http_500_error`, `test_malformed_json`, `test_connection_error` all verify `success=False` without raise |
| 7 | WM collector retries on transient failure (configurable) | PASS | `test_retry_on_error_then_success` (flaky -> success on retry), `test_all_retries_exhausted` (3 calls = initial + 2 retries) |
| 8 | WM health check maps HealthStatus correctly | PASS | `test_health_unavailable_on_connection_error` verifies UNAVAILABLE on connection failure |
| 9 | Registry loader loads JSON, queries by source_id, group, domain | PASS | 8 query tests in `TestRegistryQueries` |
| 10 | Registry validation catches enum violations and settlement breaches | PASS | `test_invalid_source_group_detected`, `test_invalid_resolution_role_detected`, `test_empty_upstream_id_detected` |
| 11 | Collection runner executes concurrently with per-collector timeout | PASS | `test_all_three_collectors_run`, `test_timeout_produces_failure_result` |
| 12 | Collection runner handles partial failure | PASS | `test_partial_failure` (1 fail, 2 succeed, all 3 returned) |
| 13 | Collection plan derived from oracle_config | PASS | `test_build_plan_from_config`, `test_build_plan_defaults` |
| 14 | 3 WM registry entries aligned with API contract | PASS | `TestWorldMonitorAlignment` (4 tests) verifies all fields per PRD Section 4.6 |
| 15 | Mock fixtures from Pydantic v2 schemas | PASS | 4 fixture JSON files with realistic data matching contract schemas |
| 16 | All tests use mock HTTP only | PASS | No real HTTP calls; all mocked via `unittest.mock.patch` / `AsyncMock` |
| 17 | No modifications to `backend/market/` or `backend/engines/` | PASS | git diff empty for both directories |
| 18 | Scoped regression passes | PASS | 242 market+engines tests pass, 0 fail |
| 19 | Pre-existing theatre errors excluded | PASS | Not in scoped test paths |
| 20 | 20+ new Sprint 1 tests | PASS | 68 new tests (exceeds target by 48) |

---

## Complexity Analysis

| Function | Cyclomatic Complexity | Assessment |
|----------|----------------------|------------|
| `WorldMonitorCollector._fetch()` | ~8 (4 exception types x retry loop) | Acceptable. Clear control flow with retry loop and exhaustive error handling. |
| `WorldMonitorCollector._build_bundle()` | ~4 (nested .get() fallbacks) | Acceptable. Defensive parsing with sensible defaults. |
| `BaseCollector._enforce_hash_invariants()` | ~3 (2 invariant checks + null check) | Low. Clean guard-clause pattern. |
| `CollectionRunner.collect()` | ~3 (missing collector branch + gather) | Low. Clean delegation pattern. |
| `RegistryLoader.validate()` | ~6 (5 validation checks per source) | Acceptable. Linear scan with clear error accumulation. |

---

## Adversarial Concerns (non-blocking)

### 1. Unbound `duration_ms` edge case (LOW risk, non-blocking)

**File**: `backend/osint/collectors/worldmonitor.py`, line 157
**Issue**: If `WorldMonitorConfig.retry_count` is set to `-1`, `attempts = 0`, the `for` loop never executes, and `duration_ms` is unbound when referenced on line 157. `last_error` is safely initialized to `None` on line 120, but `duration_ms` has no initializer.
**Risk**: Extremely low. No production code path sets `retry_count` to a negative value, and the default is `2`. A `@dataclass` field validator could enforce `retry_count >= 0`, but this is not blocking.
**Recommendation**: Consider adding `duration_ms: float = 0.0` initializer before the loop, or a `retry_count >= 0` postcondition on `WorldMonitorConfig`. Not required for approval.

### 2. Hash invariant is tautological within WorldMonitorCollector (DESIGN, non-blocking)

**File**: `backend/osint/collectors/base.py`, lines 62-95
**Observation**: The `WorldMonitorCollector._build_success_result()` computes `content_hash = compute_content_hash(raw_payload)` and stores it in the receipt. The `BaseCollector._enforce_hash_invariants()` then re-computes `compute_content_hash(result.raw_payload)` and compares. Since both use the same function on the same bytes, the invariant is always trivially satisfied for `WorldMonitorCollector`.
**Assessment**: This is intentional architecture -- the invariant catches implementation bugs in future subclass collectors that might incorrectly construct receipts. The invariant is NOT tautological for the BaseCollector contract, only for this specific subclass. Acceptable.

### 3. `asyncio.get_event_loop()` usage (INFORMATIONAL, non-blocking)

**File**: `backend/osint/collectors/worldmonitor.py`, lines 169, 309
**Observation**: `asyncio.get_event_loop()` is deprecated in Python 3.10+ when called without a running loop. However, both call sites are inside `async` methods that will always have a running event loop, and the target runtime is Python 3.9.6. No issue.
**Recommendation**: When the project upgrades to Python 3.10+, replace with `asyncio.get_running_loop()`.

### 4. Double timeout layers (DESIGN, non-blocking)

**File**: `backend/osint/collectors/worldmonitor.py`, lines 179, 182-185
**Observation**: `_do_http_post` applies `urllib.request.urlopen(timeout=self._config.timeout_s)` for socket-level timeout AND `asyncio.wait_for(timeout=self._config.timeout_s)` for wall-clock timeout. Both use the same timeout value.
**Assessment**: Belt-and-suspenders approach. The socket timeout is per-operation (connect + read), while `asyncio.wait_for` is wall-clock for the entire executor call. In practice they provide overlapping protection. Not a bug.

### 5. Fixture `receipt_hash: null` (INFORMATIONAL, non-blocking)

**Observation**: All three mock response fixtures have `receipt_hash: null` in the receipt. This means the receipt hash invariant (Invariant 2) in `BaseCollector._enforce_hash_invariants()` is never exercised in the success-path tests, because line 81 checks `if receipt.receipt_hash is not None`. The collector DOES compute `receipt_hash` in `_build_success_result()` and stores it in the receipt, but the fixture data's receipt is overwritten by the collector's own receipt construction.
**Assessment**: The test effectively validates that the collector's self-constructed receipt passes its own invariant. The fixture receipt data is irrelevant because `_build_success_result()` builds a fresh receipt from the raw response. The invariant IS exercised via the collector's own receipt (which has `receipt_hash` set). Not a bug.

---

## Assumptions Challenged

1. **"No model duplication"**: Verified. `EvidenceBundle`, `HTTPTranscriptReceipt`, `NormalisedEvent`, `GeoPoint`, `WMDomain`, `MeasureType`, `HealthStatus`, `NormalisedMeasure` are all imported from `backend.schemas.worldmonitor_api_contract`. Zero model duplication. `CollectionResult` is the only new dataclass and it wraps (not duplicates) the Pydantic types.

2. **"stdlib only"**: Verified. Source files import only from `hashlib`, `json`, `asyncio`, `time`, `urllib.request`, `urllib.error`, `dataclasses`, `datetime`, `typing`, `abc`, `enum`. Test files additionally use `pytest`, `unittest.mock`, `tempfile`, `os`, `pathlib` -- all stdlib or test-only.

3. **"API contract alignment"**: Verified. The three mock fixtures match the `CIIResponse`, `MarketSnapshotResponse`, and `MaritimeAnomalyResponse` Pydantic schemas. Field names, nesting, types all align.

4. **"68 tests"**: Verified by independent `pytest` run: 68 passed in 0.17s.

5. **"242 regression tests"**: Verified by independent `pytest` run: 242 passed in 0.30s.

---

## Code Quality Notes

- Clean separation of concerns: models, collectors, engine, canonical hashing are all in their own modules
- Docstrings present on all public classes and functions
- Type hints on all function signatures
- Consistent snake_case naming throughout
- No dead code detected (all imports used, all functions exercised by tests)
- Test structure follows clear patterns (class-per-concern, descriptive method names)
- `conftest.py` provides well-factored shared fixtures

---

## Final Assessment

The implementation is clean, well-structured, and thoroughly tested. 68 tests is more than 3x the 20-test target. All acceptance criteria verified individually. No blocking issues found. The adversarial concerns documented above are informational only and do not require changes before Sprint 22 proceeds.
