# Security Audit: Sprint-29

> **Auditor**: Paranoid Cypherpunk Auditor
> **Sprint**: sprint-2 (global: sprint-29)
> **Cycle**: cycle-032 (Observer End-to-End Integration)
> **Date**: 2026-02-20

## Verdict: APPROVED

All implementation files pass the security audit. No CRITICAL or HIGH findings. One LOW-severity observation documented for future hardening.

---

## Files Audited

| File | Lines | Status |
|------|-------|--------|
| `scripts/run_observer_theatre.py` | 521 | PASS |
| `theatre/engine/replay.py` | 195 | PASS |
| `theatre/engine/evidence_bundle.py` | 149 | PASS |
| `theatre/engine/commitment.py` | 82 | PASS |
| `theatre/engine/canonical_json.py` | 63 | PASS |
| `theatre/engine/oracle_contract.py` | 173 | PASS |
| `theatre/integration/observer_oracle.py` | 235 | PASS |
| `theatre/integration/observer_scorer.py` | 266 | PASS |
| `tests/theatre/test_observer_integration.py` | 1720 | PASS |
| `tests/theatre/test_evidence_bundle.py` | 180 | PASS |

---

## Security Checklist

### Secrets & Credentials -- PASS

- [x] No hardcoded API keys, tokens, or passwords
- [x] API keys read from environment variables (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`)
- [x] No secrets logged or written to files (only env var names appear in error messages)
- [x] Test files use `"test-key"`, never real keys
- [x] API keys stored as private `_api_key` members, never serialised to disk

### Input Validation -- PASS

- [x] No command injection vectors (no `os.system`, `subprocess`, `eval`, `exec`)
- [x] No `__import__` abuse
- [x] JSON parsing handles malformed input via fallback in `_parse_json_response()`
- [x] Path construction uses `pathlib.Path` throughout (no string concatenation)

### Error Handling -- PASS

- [x] Exceptions don't leak sensitive information
- [x] Proper error messages (schema validation, template validation)
- [x] Graceful degradation: scorer returns 0.0 on failure, oracle retries then returns ERROR status
- [x] Follow-up question generation catches all exceptions, falls back to empty string

### Data Privacy -- PASS

- [x] Evidence bundles contain only expected PR data (titles, diffs, claims)
- [x] Certificate contains no API keys or tokens
- [x] No PII beyond PR author names (expected for verification context)

### Cryptographic Integrity -- PASS

- [x] SHA-256 used correctly for all 5 hash computations (dataset, commitment, file inventory, bundle, per-episode GT)
- [x] `canonical_json()` (RFC 8785) used for all deterministic serialisation
- [x] NaN/Infinity properly rejected in canonical_json
- [x] Boolean-before-int check handles Python's `bool subclass of int` trap
- [x] Commitment hash chain is sound: 3-key composite -> canonical_json -> SHA-256
- [x] File inventory excludes manifest.json and certificate.json (avoids circular hash dependency)
- [x] Dataset hash computed before template population (correct ordering)

### Code Quality -- PASS

- [x] No obvious bugs or logic errors
- [x] 93 integration tests with comprehensive coverage
- [x] Mock usage is correct (monkey-patching `_call_anthropic`, not masking real bugs)
- [x] No unused imports or dead code
- [x] Deep copy via `json.loads(json.dumps())` prevents mutation of template input

---

## Findings

### LOW: Episode ID filename sanitisation (Informational)

**File**: `theatre/engine/evidence_bundle.py`, line 70
**Code**: `path = self._base_dir / "invocations" / f"{episode_id}.json"`

If `episode_id` contained path traversal characters (`../`), this could write outside the bundle directory. Currently LOW risk because episode IDs originate from the internal pipeline (`GroundTruthRecord.id` produces values like `"PR-42"`), not from untrusted external input.

**Recommendation**: Add filename sanitisation when external data sources are wired in (e.g., `episode_id.replace("/", "_").replace("..", "_")`).

### INFORMATIONAL: Deprecated `datetime.utcnow()`

**Files**: `scripts/run_observer_theatre.py` (lines 288, 305), `theatre/engine/commitment.py` (line 77), `theatre/engine/oracle_contract.py` (line 50)

`datetime.utcnow()` is deprecated in Python 3.12+ in favour of `datetime.now(timezone.utc)`. Not a security issue; flagged for future cleanup.

---

## Conclusion

The sprint-29 implementation demonstrates strong security hygiene:

1. **Zero hardcoded secrets** -- all API keys from environment variables
2. **Sound cryptographic chain** -- SHA-256 over RFC 8785 canonical JSON at every hash point
3. **Comprehensive test coverage** -- 93 tests covering identity layer, RLMF export, evidence bundles, schema validation, determinism, and hashing invariants
4. **Clean error handling** -- graceful degradation throughout, no information leakage
5. **No injection vectors** -- no shell execution, no eval, no unsafe path construction

Sprint-29 is approved for completion.
