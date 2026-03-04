# Sprint 8 Security Audit

## Verdict: APPROVED - LETS FUCKING GO

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-01
**Scope:** Cycle-004, Sprint 1 (global Sprint 8) -- OSINT Pipeline Architectural Hardening
**Files audited:** 8 (7 modified, 1 new)
**Tests verified:** 49/49 passing (37 architectural + 12 canonical)

---

## Security Review

### 1. Secrets & Credentials

**Status: CLEAN**

- No hardcoded API keys, tokens, passwords, or credentials in any modified file.
- No secrets in test fixtures. The `Authorization: Bearer token_a` / `token_b` strings in `test_different_auth_headers_same_hash` are test vectors specifically validating that auth headers are stripped from canonical form -- this is correct and intentional.
- `CANONICAL_HEADER_ALLOWLIST` in `engine/canonical.py` (line 26) is a `frozenset` containing exactly `{"accept", "content-type", "user-agent"}`. Verified that `Authorization`, `Cookie`, `Date`, `X-Request-Id`, and all other volatile headers are excluded. Two independent fetchers with different credentials produce identical canonical hashes -- confirmed via runtime verification.
- No `.env` files, no hardcoded URLs containing credentials, no base64-encoded secrets.

### 2. Input Validation

**Status: CLEAN**

- `FailureMode` is a proper `str, Enum` subclass (7 constrained values). Invalid values are rejected by the enum constructor. Verified via runtime test.
- `ReceiptMode` is a proper `str, Enum` subclass (5 constrained values). Ordering enforced via `RECEIPT_MODE_ORDER` list.
- Pydantic model validators verified:
  - `HTTPTranscriptReceipt.validate_hash_format` correctly rejects uppercase hex, non-hex characters, and wrong-length strings.
  - `EvidenceBundle.validate_content_hash` enforces 64-char lowercase hex.
  - `EvidenceBundle.confidence_score` has `ge=0.0, le=1.0` constraints enforced by Pydantic.
- `RETRIABLE_FAILURES` is a `frozenset` -- immutable, cannot be modified at runtime.
- No injection vulnerabilities: all f-strings are used for logging/error messages only, never for SQL, shell, or code execution. No `eval()`, `exec()`, `__import__()`, `pickle`, `subprocess`, or `os.system` anywhere in the modified files or the wider codebase.
- `GapReport.failure_mode` defaults to `None` and `retriable` defaults to `False` -- backward compatible, safe defaults.

### 3. Hash Integrity

**Status: CLEAN**

- **NFC normalisation**: Verified that NFC correctly collapses equivalent Unicode representations (e.g., `e` + combining acute U+0301 produces identical output to precomposed `e-acute` U+00E9). Critically, NFC does NOT introduce collisions between visually similar but distinct codepoints (Latin `a` vs Cyrillic `a` remain distinct). NFC normalisation is idempotent -- multiple applications produce the same result.
- **Float handling**: `_RFC8785Encoder` uses Python's `repr()` for shortest round-trip float representation. `0.1 + 0.2` produces `0.30000000000000004` deterministically. Negative zero produces `"-0"` per RFC 8785. NaN and Infinity are rejected with `ValueError` -- no silent corruption.
- **RFC 8785 compliance**: Keys are sorted lexicographically, no whitespace between separators, `ensure_ascii=False` (UTF-8 pass-through), no trailing newline. Bool is correctly distinguished from int (True becomes `"true"`, not `"1"` -- important since Python `bool` is a subclass of `int`).
- **Canonical URL**: Query parameters sorted by key, scheme+host lowercased, trailing slash stripped, fragment dropped. Verified via existing test `test_url_query_params_order_irrelevant`.

### 4. Error Handling

**Status: CLEAN**

- `BaseCollector.collect()` catches `httpx.TimeoutException`, `httpx.ConnectError`, and generic `Exception` with proper fallback to `_failure()` (lines 289-298). No uncaught exceptions can crash the pipeline.
- `CollectionRunner.run()` uses `ThreadPoolExecutor` as a context manager (`with ThreadPoolExecutor(...)`) -- guaranteed cleanup on exit (lines 149-192). The `FuturesTimeoutError` fix (catching both `TimeoutError` and `concurrent.futures.TimeoutError`) is a genuine Python 3.9 compatibility fix.
- Unfinished futures are explicitly cancelled (line 174) and produce gap reports. No orphaned threads.
- `BaseCollector` implements `__enter__`/`__exit__` context manager protocol and `close()` method for HTTP client cleanup (lines 356-366). `CollectionRunner.close_all()` iterates all collectors (lines 278-281).
- The `_RFC8785Encoder._encode_float()` raises `ValueError` for NaN/Infinity rather than silently producing invalid output.

### 5. Code Quality

**Status: CLEAN**

- No dead code: `FREE_SOURCE_CONFIDENCE_CAP` and `should_cap_confidence()` fully removed from `BaseCollector`. Verified via test `test_base_collector_no_confidence_cap` and `grep` search.
- Imports are clean: no unused imports in any modified file. `from __future__ import annotations` used consistently for forward references.
- Type annotations are correct throughout: `dict[str, Any]`, `ReceiptMode`, `FailureMode | None`, `frozenset[FailureMode]`, etc. Return types annotated on all public methods.
- British spelling maintained: `normalise`, `serialisation`, `canonicalised`, `artefact` used consistently in docstrings and comments.
- Module docstrings present on all files with clear documentation of purpose and spec references.
- One minor note: `AssertionError` in the standalone test runner (line 941) is correctly spelled -- verified against Python builtins.

### 6. Architecture Alignment

**Status: CLEAN**

- **Confidence capping fully removed from BaseCollector**: No `FREE_SOURCE_CONFIDENCE_CAP`, no `should_cap_confidence()`, no capping block in `collect()`. Bundle `confidence_score` from `extract()` is passed through raw (line 273 of `base.py`).
- **Scorer properly separated**: `EvidenceScorer` is a new module in `engine/scorer.py` with clear separation of concerns. Penalties are multiplicative and documented: revision_policy (3 tiers), rate_limit_instability (0.90), receipt_at_minimum (0.95), single_source_cap (0.95). Composite confidence formula `1 - product(1 - score_i)` correctly allows exceeding 0.95 with corroboration.
- **Runner-level enforcement is non-bypassable**: Receipt mode pre-check in `CollectionRunner.run()` (lines 116-141) executes before thread pool submission. Collectors that fail are excluded from dispatch -- they never get to call `collect()`. This is a second enforcement layer on top of `BaseCollector.validate_receipt_mode()`.
- **Gap reports are structured and complete**: `GapReport` now carries `gap_kind` (SIGNAL_ABSENCE vs INTELLIGENCE_GAP), `failure_mode` (7-value enum), `retriable` (bool), `freshness` (NO_DATA for absence, ERROR for gaps). `OracleCollectionSummary` has `gap_count`, `gap_sources`, `distinct_upstream_count`, `distinct_upstream_succeeded_count`, `upstream_dedup_map`, and `coverage_ratio` computed properties.

### 7. Test Coverage

**Status: COMPREHENSIVE**

All 27 new tests + 2 updated tests cover:

- **AC-1 (GapKind)**: 4 tests -- enum size, NOT_FOUND mapping, TIMEOUT mapping, NETWORK_ERROR mapping.
- **AC-2 (Upstream dedup)**: 2 tests -- alias property, empty string handling.
- **AC-3 (Receipt enforcement)**: 2 tests -- rejection of insufficient mode, pass of sufficient mode.
- **AC-4 (Scorer)**: 7 tests -- immutable no penalty, latest_only 0.80x, as_of_timestamp 0.95x, single source cap, composite exceeds 0.95, receipt at minimum penalty, old cap removed.
- **AC-5 (Canonical hash)**: 3 tests -- NFC normalisation with combining characters, 0.1+0.2 float precision, RFC 8785 test vector.
- **AC-6 (FailureMode)**: 6 tests -- enum size, GapReport fields, 5xx retriable, DNS not retriable, gap_count/gap_sources, no silent drops.
- **AC-INT (Integration)**: 3 tests -- end-to-end with 4 sources (shared upstream + timeout + 404), allow_gap=false fails, allow_gap=true recorded.

Edge cases covered:
- Null/empty upstream_id (no false dedup collisions)
- `0.1 + 0.2` float precision
- Combining characters vs precomposed Unicode
- Collectors without registry source (backward compatibility)
- Thread timeout budget exhaustion
- Shared upstream deduplication in integration test

---

## Findings

**NONE.** Zero critical, zero high, zero medium, zero low findings.

---

## Summary

This is a textbook architectural hardening sprint. Every modified file demonstrates clean separation of concerns, proper input validation, no secrets exposure, correct error handling with resource cleanup, and comprehensive test coverage. The RFC 8785 canonical JSON implementation is particularly solid -- it handles negative zero, NaN/Infinity rejection, bool/int distinction, and NFC normalisation without introducing false collisions. The scorer extraction from BaseCollector creates proper boundaries between data collection and quality assessment. The runner-level receipt mode enforcement provides defense-in-depth that cannot be bypassed by subclass overrides. All 49 tests pass. Ship it.
