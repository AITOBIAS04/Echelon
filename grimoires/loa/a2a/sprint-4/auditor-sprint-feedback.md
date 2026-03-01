# Sprint 4 (Cycle-002 Sprint 1) — Security Audit

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-01
**Verdict:** APPROVED - LETS FUCKING GO

---

## Security Checklist

### Secrets & Credentials: PASS

- **No hardcoded credentials.** API keys are passed via `config` dict at runtime (companies_house.py:65). The `config` dict is injected by the caller — no defaults that could leak.
- **Test fixtures use obvious dummy keys** (`"test_key_12345"`) — clearly not real credentials.
- **No `.env` file references, no environment variable reads** in production code. Config injection is the right pattern.
- **Authorization headers are excluded from receipt hashes** via `CANONICAL_HEADER_ALLOWLIST` (canonical.py:28-32). This prevents credential material from leaking into evidence artefacts. Two fetchers with different API keys produce identical receipt hashes. Verified by `test_different_auth_headers_same_hash`.

### Input Validation: PASS

- **Hash field validators** enforce 64-char lowercase hex (evidence.py:105-110, 189-194). Rejects uppercase, wrong-length, and non-hex input. Tested.
- **Confidence score bounds** enforced at model level via `ge=0.0, le=1.0` (evidence.py:167). Tested.
- **Company number and endpoint** validated in build_request (companies_house.py:97-114). Unknown endpoints raise ValueError. Missing company_number raises ValueError.
- **Registry version validation** (registry.py:80-85) prevents loading tampered or wrong-version registries.
- **No `eval()`, `exec()`, `__import__()`, `subprocess`, `os.system()`, `pickle.load()`** anywhere in production code. Clean.

### Injection Resistance: PASS

- **URL construction** in companies_house.py uses f-strings with `company_number` from query_context. The value is passed as a URL path segment, not interpolated into SQL or shell commands. httpx handles URL encoding.
- **No SQL, no shell commands, no template rendering.** This is a pure data pipeline with HTTP calls and Pydantic validation.
- **JSON parsing** uses `json.loads()` on raw bytes (companies_house.py:133). Malformed JSON caught with JSONDecodeError, returns confidence 0.0. No untrusted data is used for code execution.

### Cryptographic Integrity: PASS

- **SHA-256 via `hashlib.sha256`** — standard library, no custom crypto.
- **Canonical JSON delegated to theatre engine** (K-3 fix confirmed at canonical.py:21). RFC 8785 compliance with float normalisation, NaN/Infinity rejection.
- **HTTP Transcript Canonical Form** is deterministic: headers allowlisted and sorted, URL query params sorted, trailing slashes stripped, fragments dropped. Tested with 6 determinism tests.
- **Receipt hashes are deterministic** — two independent fetchers with identical inputs produce identical receipt hashes. This is the core security invariant and it's well-tested.

### Data Privacy: PASS

- **No PII in evidence bundles.** Structured extracts contain company registration data (public record), not personal data. Officer names from Companies House are already public record.
- **No logging of API keys or auth headers.** Error messages only contain HTTP status codes, not response bodies or headers.
- **Authorization header excluded from canonical form** — credential material never enters the hash chain.

### Error Handling: PASS

- **No stack traces or internal details exposed in CollectionResult.** Error messages are brief and descriptive ("HTTP 401", "Rate limited", "Request timed out").
- **Catch-all exception handler** (base.py:304-307) catches unexpected errors and returns SOURCE_ERROR with a message. No unhandled exceptions can crash the pipeline.
- **httpx exceptions properly mapped** — TimeoutException, ConnectError handled separately from generic exceptions.

### Architecture Alignment: PASS

- **All 6 K-fixes applied correctly** (K-1, K-2, K-3, K-6, K-7, K-8). Verified against SDD.
- **5 of 6 architectural concerns addressed.** Concern 6 (timeout gap production) correctly deferred to Sprint 2 (collection_runner.py scope).
- **Pydantic v2 exclusively** — no v1 patterns. `field_validator` not `validator`, `BaseModel` not `GenericModel`.
- **No circular imports.** Clean dependency chain: evidence.py <- registry.py, canonical.py <- base.py <- companies_house.py.

### Test Coverage: PASS

- **73 tests across 4 files.** All passing.
- **35 theatre regression tests** unaffected.
- **Error paths tested:** 404, 401, 429, 500, invalid JSON, empty API key, wrong hash format, wrong registry version.
- **Determinism tested:** same inputs produce same hashes, different inputs produce different hashes, header order irrelevant, auth headers excluded.
- **Mock HTTP transport** used correctly — no real network calls in tests.

---

## Summary

Clean implementation. No secrets, no injection vectors, no unsafe patterns, no information leakage. The canonical hashing layer correctly delegates to the theatre engine and excludes volatile headers. Pydantic v2 validators enforce type safety at model boundaries. Error handling is uniform and non-disclosing.

The code is ready for production use in Sprint 2 (pipeline engine).
