# Security Audit — Sprint 15

**Cycle**: c027 / Sprint 2 (sprint-15)
**Scope**: Ground Truth Ingestion — `verification/src/echelon_verify/ingestion/github.py`
**Test file**: `verification/tests/test_ingestion.py`
**Auditor**: Claude Opus 4.6
**Date**: 2026-02-19
**Verdict**: **AUDIT_REJECTED**

---

## Executive Summary

The GitHub ingestion client is well-structured with proper async context management, rate limit handling, and diff truncation. However, the audit identifies **3 HIGH**, **2 MEDIUM**, and **2 LOW** severity findings. Two HIGH findings (SSRF and token leakage) are blocking and must be remediated before approval.

---

## Findings

### SEC-15-001 | SSRF via Unconstrained `repo_url` | HIGH | BLOCKING

**File**: `verification/src/echelon_verify/ingestion/github.py:23-37`
**Also**: `verification/src/echelon_verify/config.py:11-19`

**Description**: The `_parse_repo` function accepts `repo_url` via regex but the regex is more permissive than intended. The pattern `(?:https?://github\.com/)?([^/]+)/([^/.]+?)(?:\.git)?/?$` will accept bare `owner/repo` shorthand, which is then interpolated into the path of requests to `https://api.github.com`. While the `base_url` is hardcoded to `api.github.com` (which prevents full-URL SSRF), the `owner` and `repo` segments are injected directly into path strings at lines 161, 211, and 220:

```python
f"/repos/{self._owner}/{self._repo}/pulls"
f"/repos/{self._owner}/{self._repo}/pulls/{pr_number}"
```

An attacker-controlled `repo_url` value like `../../orgs/victim-org/members?per_page=100#/fake` could attempt path traversal. While httpx normalizes most path traversal attempts, the `owner` segment has no allowlist validation (only `[^/]+` in the regex). Crucially, the `IngestionConfig` Pydantic model performs **zero validation** on `repo_url` -- it is a bare `str` field with no constraints.

**Additionally**, the regex accepts `http://` (not just `https://`), meaning a configuration with `http://github.com/...` would be accepted without warning, though the `base_url` override mitigates actual plaintext transit.

**Remediation**:
1. Add a Pydantic `field_validator` on `repo_url` in `IngestionConfig` that rejects values not matching `^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$` or `^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?/?$`.
2. Validate `self._owner` and `self._repo` against `^[a-zA-Z0-9_.-]+$` inside `_parse_repo` after regex extraction.
3. Remove `http://` acceptance from the regex (enforce `https` only).

**Test gap**: `TestParseRepo` (lines 68-86) tests happy paths and one invalid input, but does **not** test path traversal payloads, URL-encoded characters in owner/repo, or `http://` scheme acceptance.

---

### SEC-15-002 | GitHub Token Exposed in Logs and Error Messages | HIGH | BLOCKING

**File**: `verification/src/echelon_verify/ingestion/github.py:90-91`
**Also**: `verification/src/echelon_verify/config.py:15`

**Description**: The `github_token` is set as a Bearer token in the httpx client headers at construction time:

```python
if config.github_token:
    headers["Authorization"] = f"Bearer {config.github_token}"
```

This creates several exposure risks:

1. **Logging**: httpx logs request headers at DEBUG level. If the application or any dependency enables DEBUG logging, the `Authorization` header (containing the full PAT/token) will appear in log output. There is no `logging.Filter` or httpx event hook to redact this header.

2. **Exception messages**: If `resp.raise_for_status()` (lines 170, 224, 226) raises an `httpx.HTTPStatusError`, the exception object contains a reference to the `request` which includes headers. Any error handler or crash reporter that serializes the exception will capture the token.

3. **Config serialization**: `IngestionConfig.github_token` is a plain `str | None` with no `repr=False`, no `SecretStr` type, and no `json_schema_extra` redaction. Calling `config.model_dump()` or `repr(config)` exposes the token in cleartext. Pydantic v2 provides `SecretStr` specifically for this purpose.

**Remediation**:
1. Change `github_token: str | None = None` to `github_token: SecretStr | None = None` in `IngestionConfig`.
2. Update the header assignment to `headers["Authorization"] = f"Bearer {config.github_token.get_secret_value()}"`.
3. Add an httpx `event_hook` or use `httpx.Auth` subclass to avoid storing the token in the default headers dict (prefer per-request auth flow).
4. Consider adding a `logging.Filter` that redacts `Authorization` headers from log output.

**Test gap**: No test validates that the token is redacted from repr/logs. No test verifies that the `Authorization` header is set correctly when a token is provided, or omitted when it is not.

---

### SEC-15-003 | Unbounded Rate Limit Backoff Enables Denial of Service | HIGH

**File**: `verification/src/echelon_verify/ingestion/github.py:255-265`

**Description**: The `_handle_rate_limit` method implements exponential backoff up to `_MAX_BACKOFF_SECONDS = 60`, iterating 5 times. However, the method is called when a 403 is received, and the only exit condition besides loop exhaustion is `datetime.now(tz=timezone.utc) >= self._rate_limit_reset`. The `_rate_limit_reset` value is parsed directly from the `x-ratelimit-reset` response header (line 236):

```python
self._rate_limit_reset = datetime.fromtimestamp(int(reset), tz=timezone.utc)
```

A malicious or compromised proxy could return a `x-ratelimit-reset` header with a far-future timestamp, causing the backoff loop to always fail the reset check and execute all 5 iterations (total sleep: 1 + 2 + 4 + 8 + 16 = 31 seconds). In `_check_rate_limit` (line 243), the same far-future reset combined with a spoofed `x-ratelimit-remaining: 0` could cause an unbounded sleep:

```python
wait = max(0, (self._rate_limit_reset - datetime.now(tz=timezone.utc)).total_seconds())
await asyncio.sleep(wait)
```

If `_rate_limit_reset` is set to, say, `2099-01-01`, this `wait` would be billions of seconds -- effectively a permanent hang with no timeout.

**Remediation**:
1. Cap the `wait` in `_check_rate_limit` to `_MAX_BACKOFF_SECONDS`: `wait = min(wait, _MAX_BACKOFF_SECONDS)`.
2. Validate parsed `x-ratelimit-reset` timestamps: reject values more than, e.g., 15 minutes in the future.
3. Add a total-time circuit breaker across the ingestion run.

**Test gap**: No test covers the rate limit backoff paths. No test simulates a 403 response to verify backoff behavior.

---

### SEC-15-004 | No Response Size Limit on HTTP Client | MEDIUM

**File**: `verification/src/echelon_verify/ingestion/github.py:92-96`

**Description**: The httpx `AsyncClient` is created with a 30-second timeout but no `max_content_length` or streaming guard. The diff endpoint (`_fetch_diff`) reads the entire response body into memory via `resp.text` (line 227). A repository with an extremely large PR diff (e.g., a binary blob committed by mistake) could cause OOM. While `_truncate_diff` caps the stored output at 100KB, truncation happens **after** the full response is already loaded into memory.

The PR listing endpoint also loads all JSON into memory via `resp.json()` (line 171) without size validation.

**Remediation**:
1. Use `httpx.AsyncClient(max_redirects=5)` (already defaults to 20, but should be explicit).
2. For diff fetching, use streaming: `async with self._client.stream("GET", ...) as resp:` and read up to `_MAX_DIFF_BYTES + buffer` before closing.
3. Alternatively, add `Content-Length` pre-check before reading the body.

---

### SEC-15-005 | Diff Content Not Sanitized Before Storage | MEDIUM

**File**: `verification/src/echelon_verify/ingestion/github.py:126`
**Also**: `verification/src/echelon_verify/models.py:23`

**Description**: The `diff_content` field in `GroundTruthRecord` is a bare `str` with no sanitization. Diff content is fetched from GitHub and stored as-is (after truncation). If this content is later rendered in a web UI or passed to another system, it could contain:

1. Embedded control characters or ANSI escape sequences.
2. Content that, when rendered as HTML, could enable stored XSS (if the downstream consumer does not escape properly).
3. Very long single lines (no per-line length cap in `_truncate_diff`).

While this is partially a downstream concern, defense-in-depth requires sanitization at the ingestion boundary.

**Remediation**:
1. Strip ANSI escape sequences and non-printable control characters (except `\n`, `\t`) from diff content before storage.
2. Add a per-line length cap in `_truncate_diff`.
3. Document that `diff_content` contains raw diff output and consumers must escape before rendering.

---

### SEC-15-006 | Broad Exception Swallowing in `ingest()` | LOW

**File**: `verification/src/echelon_verify/ingestion/github.py:137-139`

**Description**: The `except Exception` clause in the PR processing loop silently continues on any failure. While `logger.exception` logs the error, this pattern:

1. Swallows authentication errors that should halt the entire run (e.g., token revoked mid-run).
2. Swallows network configuration errors that affect all subsequent requests.
3. Makes it impossible for callers to distinguish "0 records found" from "all records failed to process".

**Remediation**:
1. Catch specific exceptions: `httpx.HTTPStatusError`, `KeyError`, `ValueError`.
2. Re-raise 401/403 errors immediately (authentication/authorization failures should not be retried per-PR).
3. Track and return error counts alongside records so callers can detect degraded ingestion.

---

### SEC-15-007 | `_etags` Dict Populated But Never Used | LOW

**File**: `verification/src/echelon_verify/ingestion/github.py:99`

**Description**: `self._etags: dict[str, str] = {}` is initialized but never read or written to elsewhere in the class. This is dead code that suggests an incomplete conditional-request implementation (HTTP `If-None-Match` / `ETag`). Dead code in security-sensitive modules is a maintenance liability; it may mislead reviewers into thinking caching is implemented when it is not.

**Remediation**: Remove the `_etags` field or complete the ETag-based caching implementation.

---

## Test Coverage Assessment

| Area | Coverage | Verdict |
|------|----------|---------|
| `_parse_repo` happy paths | Covered | PASS |
| `_parse_repo` adversarial inputs (traversal, encoding) | **Missing** | FAIL |
| `_truncate_diff` | Covered | PASS |
| `_extract_files_changed` | Covered | PASS |
| Token in headers | **Missing** | FAIL |
| Rate limit backoff (403 path) | **Missing** | FAIL |
| Pagination | Covered | PASS |
| Label filtering | Covered | PASS |
| Merged-only filtering | Covered (implicitly) | PASS |
| Error handling in `ingest()` | **Missing** | FAIL |
| Storage round-trip | Covered | PASS |
| Large diff response (OOM) | **Missing** | FAIL |

**Required test additions before approval**:
1. `test_parse_repo_path_traversal` -- verify `_parse_repo("../../../etc/passwd/x")` raises `ValueError`.
2. `test_parse_repo_url_encoded` -- verify URL-encoded characters in owner/repo are rejected.
3. `test_auth_header_set_with_token` -- verify `Authorization: Bearer <token>` is present when token is configured.
4. `test_auth_header_absent_without_token` -- verify no `Authorization` header when token is `None`.
5. `test_rate_limit_403_triggers_backoff` -- mock a 403 response and verify retry behavior.
6. `test_ingest_partial_failure_continues` -- mock one PR diff failing and verify other records still returned.

---

## Verdict

### AUDIT_REJECTED

**Blocking findings**: SEC-15-001 (SSRF/input validation), SEC-15-002 (token leakage)

These two findings represent real security risks in a production ingestion pipeline:
- SEC-15-001 allows insufficiently validated user input to influence API request paths, and the Pydantic config model provides no validation boundary.
- SEC-15-002 exposes authentication tokens through standard logging, exception handling, and model serialization pathways.

**Required for re-audit**:
1. Implement `repo_url` validation in both `IngestionConfig` (Pydantic validator) and `_parse_repo` (character allowlist on extracted owner/repo).
2. Switch `github_token` to `pydantic.SecretStr`.
3. Cap the wait time in `_check_rate_limit` to prevent unbounded sleep (SEC-15-003).
4. Add the 6 required test cases listed above.
5. Remove dead `_etags` field (SEC-15-007).

Non-blocking findings (SEC-15-004, SEC-15-005, SEC-15-006) should be addressed but do not block approval.
