# Sprint 5 (Cycle-002 Sprint 2) — Security & Quality Audit

**Sprint:** Pipeline Engine
**Global ID:** sprint-5
**Date:** 2026-03-01
**Auditor:** Paranoid Cypherpunk Auditor

---

## Verdict: APPROVED - LETS FUCKING GO

All 7 tasks (T2.1-T2.7) pass security and quality audit. 67 tests across 5 test files cover the critical paths. No secrets in code, no injection vectors, no information disclosure, thread safety handled correctly.

---

## Security Audit

### 1. Secrets & Credentials

**PASS** - No hardcoded secrets.

- SEC EDGAR: `user_agent` loaded from config dict, raises `ValueError` if empty (line 54-58 of `sec_edgar.py`). No hardcoded email addresses.
- ECB: No auth required. No credentials anywhere.
- No API keys, tokens, passwords, or Bearer headers in any Sprint 5 file.
- Companies House collector (Sprint 1, not in scope) correctly loads `api_key` from config.
- `CANONICAL_HEADER_ALLOWLIST` in `canonical.py` explicitly **excludes** `Authorization`, `Cookie`, and `X-Request-Id` from receipt hashing. This means credentials are never committed to evidence hashes. Correct design.

### 2. Input Validation

**PASS** - Adequate validation at trust boundaries.

- `SECEdgarCollector.build_request()`: Validates `search_query` is non-empty (line 73-74). Date parameters and form_type are passed through to SEC API as-is. Since these are query parameters to a trusted government API (EFTS), not SQL or shell commands, this is acceptable. No SSRF risk: `BASE_URL` is hardcoded to `https://efts.sec.gov`.
- `ECBDataCollector.build_request()`: Validates both `dataflow` and `series_key` are non-empty (line 64-67). URL is constructed as `{BASE_URL}/{dataflow}/{series_key}` (line 69).

**NOTE (advisory, non-blocking):** The ECB collector builds the URL path from user-supplied `dataflow` and `series_key` without sanitizing path separators. An attacker supplying `dataflow = "../../../admin"` could potentially reach unintended ECB endpoints. However: (a) the ECB API is public and read-only, (b) `httpx.Client` does not resolve `..` in URLs before sending, (c) the ECB server would reject malformed paths, (d) `follow_redirects=True` in BaseCollector is a standard pattern for API clients following legitimate redirects. Risk is negligible for a read-only OSINT pipeline. If this pipeline ever gains write capabilities or targets internal services, sanitize URL path components.

### 3. Error Handling & Information Disclosure

**PASS** - No sensitive information leaked.

- `SEC extract()`: Returns generic `{"error": "HTTP {status_code}"}` or `{"error": "Invalid JSON response"}`. No stack traces, no internal paths, no server details leaked to the structured extract.
- `ECB extract()`: Same pattern. Clean error returns with zero internal details.
- `CollectionRunner.run()`: Catches `Exception` from futures (line 137) and logs via `logger.error`. The error is logged server-side, not returned to callers. Callers see `result = None` which becomes a generic `GapReport` with `"Collection thread failed"`.
- `run_sequential()`: Same pattern. `str(exc)` goes into `GapReport.error_detail`, which could theoretically contain internal details. This method is explicitly documented as "for debugging/testing." Acceptable.
- No raw exception stack traces in any returned model.

### 4. Thread Safety

**PASS** - Correct parallel execution pattern.

- `CollectionRunner.run()` uses `ThreadPoolExecutor` with `as_completed()` (lines 124-145). Each collector runs independently on its own `collect()` call. No shared mutable state between threads.
- Worker count correctly handles edge case: `min(self.max_workers, len(active)) if active else 1` (line 123). The `if not active: return` early exit at line 90-96 means `active` is never empty when reaching the thread pool. Belt-and-suspenders.
- `self.collectors` dict is built in `__init__` and never mutated during `run()`. The `active` dict is a fresh copy (`dict(self.collectors)` or comprehension). No dict mutation during iteration.
- `results` dict is only written inside the `as_completed` loop (sequential writes from the completion callback thread). No concurrent writes to the same key.
- Timeout handling: Catches both `TimeoutError` (builtin) and `concurrent.futures.TimeoutError` (Python 3.9 compat) at line 140. Unfinished futures are cancelled at line 151.
- `summary` object is only modified in the main thread (after thread pool completes). No concurrent access to the summary.

### 5. Code Quality

**PASS** - Clean, well-structured code.

- All modules use `from __future__ import annotations` for PEP 604 union syntax support.
- Pydantic v2 patterns throughout. No v1 `Config` classes, no `.dict()` calls, uses `.model_dump(mode="json")`.
- Scorer clamps composite to `[0.0, 1.0]` (line 156). `CriterionScore.score` has Pydantic `ge=0.0, le=1.0` constraint.
- Bundle hash uses `canonical_json` (RFC 8785) + `sha256_hex` for determinism. Bundles are sorted by `bundle_id` before hashing (line 160-161).
- Empty bundle edge case handled: `sha256_hex("")` produces a valid 64-char hex hash (line 166).
- UUID generation for `oracle_id` uses `uuid.uuid4()` (cryptographically random). Good.
- `__init__.py` avoids circular imports by not re-exporting engine classes. Documented in docstring.
- Logging uses `%s` formatting (not f-strings), which is the correct pattern for lazy evaluation.

### 6. Architecture Alignment

**PASS** - Matches SDD and Composed Oracle Spec v2.

- **Three-stage pipeline**: Collection (Stage 1) -> Corroboration (Stage 2) + Counter-Signal (Stage 2b) -> Scorer (Stage 3). Exactly matches SDD.
- **Independence dedup**: Corroboration engine deduplicates by `independence_upstream_id` before counting groups (lines 67-76 of `corroboration.py`). This is the critical invariant from Spec v2 section 2.1.
- **Gap vs Absence (Concern 2)**: Counter-signal checker distinguishes `SIGNAL_ABSENCE` (checked=True, evidential) from `INTELLIGENCE_GAP` (checked=False, uncertainty). Lines 132-167 of `counter_signal.py`.
- **Timeout Gap Production (Concern 6)**: Collection runner catches timeout, produces `GapReport` with `GapKind.INTELLIGENCE_GAP` for unfinished sources. Lines 147-167 of `collection_runner.py`.
- **5 criteria with correct weights**: source_coverage(0.20), receipt_validity(0.15), corroboration_met(0.30), counter_signal_clear(0.15), confidence_weighted(0.20). Sum = 1.00. Matches SDD section 2.2.5.
- **11 counter-signal classes**: All declared and tested. Matches the committed list from the Spec.
- **Registry values**: SEC and ECB collectors use actual registry `source_id`, `independence_upstream_id`, and `resolution_role` values, not sprint plan estimates. Correct.

### 7. Test Coverage Analysis

**PASS** - 67 tests across 5 files cover all critical paths.

| Test File | Count | Coverage Assessment |
|-----------|-------|-------------------|
| `test_collection_runner.py` | 13 | Parallel, timeout, filtering, gaps, sequential, close, empty collectors |
| `test_corroboration.py` | 10 | Upstream dedup, shared upstream exclusion, time window, group counting, role filter, evaluate_all |
| `test_counter_signal.py` | 11 | All 11 classes, pass/fail matrix, GapKind handling, multi-class, auto-discover |
| `test_scorer.py` | 16 | Per-criterion, composite, custom weights, hash determinism, coverage %, output assembly |
| `test_collectors.py` | 17 | SEC init/build/extract/collect, ECB init/build/extract/collect, mock HTTP |

**Key tests verified:**
- Timeout produces `INTELLIGENCE_GAP` (not swallowed silently)
- Bundle hash is deterministic (same inputs = same hash)
- Different bundles produce different hashes
- Missing required source produces gap report
- `allow_gap` propagation works end-to-end
- SEC requires User-Agent (fails without it)
- Invalid JSON responses handled gracefully
- Rate limiting (429) and server errors (500) mapped correctly
- All tests use `httpx.MockTransport` -- zero live API calls

---

## Advisory Findings (Non-Blocking)

### A1: ECB URL Path Construction (Low Risk)

**File:** `osint_pipeline/collectors/ecb_sdmx.py` line 69
**Issue:** `url = f"{self.BASE_URL}/{dataflow}/{series_key}"` -- user-supplied values interpolated into URL path without sanitization.
**Risk:** Negligible. ECB API is public read-only. `httpx` does not resolve `../` in URL paths. The ECB server rejects malformed paths.
**Recommendation:** Consider adding a regex check for `dataflow` (alphanumeric + underscore only) and `series_key` (alphanumeric + dots + colons) in a future hardening pass. Not blocking.

### A2: `follow_redirects=True` in BaseCollector (Low Risk)

**File:** `osint_pipeline/collectors/base.py` line 171
**Issue:** HTTP client follows redirects. If a government API were compromised, it could redirect to a malicious host.
**Risk:** Low. All `BASE_URL` values are hardcoded HTTPS government endpoints. SSRF risk is near zero in a read-only pipeline.
**Recommendation:** Consider adding a redirect callback or hostname allowlist in a future hardening pass. Not blocking.

### A3: `str(exc)` in Sequential Mode Error Detail

**File:** `osint_pipeline/engine/collection_runner.py` line 249
**Issue:** `error_detail=str(exc)` could include internal paths or connection strings in the `GapReport`.
**Risk:** Low. This method is documented as debugging-only. `GapReport` stays within the pipeline, not returned to end users.
**Recommendation:** No action needed unless `GapReport` is ever serialized to external consumers.

---

## Conclusion

The Sprint 5 Pipeline Engine implementation is **clean, correct, and secure**. The three-stage pipeline architecture is faithfully implemented. All critical invariants from the Composed Oracle Spec v2 are enforced (independence dedup, gap vs absence distinction, timeout gap production). The 67 tests provide thorough coverage of all happy paths and error paths. No secrets in code, no injection vulnerabilities, no information disclosure. Thread safety is correctly implemented.

The three advisory findings are all low-risk and non-blocking. They represent future hardening opportunities, not current vulnerabilities.

**APPROVED - LETS FUCKING GO**
