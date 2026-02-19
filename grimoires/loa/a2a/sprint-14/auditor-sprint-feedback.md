# Security Audit — Sprint 14

**Verdict**: AUDIT_APPROVED

**Auditor**: Security Auditor (automated)
**Date**: 2026-02-19
**Scope**: `verification/src/echelon_verify/{models.py, config.py, storage.py}`, `verification/pyproject.toml`

---

## Summary

The verification pipeline introduces Pydantic v2 data models, a configuration layer with API key resolution, and a filesystem storage layer for JSONL/JSON artifacts. Overall the code demonstrates competent defensive practices: path traversal guards exist, Pydantic provides strong input validation, and atomic file writes are attempted. However, several medium-severity issues warrant attention before production deployment, and one issue around secrets handling should be prioritized.

---

## Findings

### SEC-14-001: API Keys and GitHub Tokens Stored as Plain `str` — No `SecretStr` Protection (SEVERITY: MEDIUM)

**File**: `config.py:51`, `config.py:15`, `models.py:95`

Both `ScoringConfig.api_key`, `IngestionConfig.github_token`, and `VerificationRunRequest.github_token` are typed as `str | None`. Pydantic v2 provides `SecretStr` specifically for this purpose — it redacts the value in `repr()`, `str()`, and `model_dump()` / `model_dump_json()` output.

**Risk**: If any of these models are logged, serialized to disk, or returned in API error responses (e.g., FastAPI's default validation error detail), the raw token/key value will be exposed in plaintext. Since `VerificationRunRequest` is an API request model used with FastAPI, Pydantic validation errors will include the raw `github_token` value in the 422 response body.

**Recommendation**:
```python
from pydantic import SecretStr

class ScoringConfig(BaseModel):
    api_key: SecretStr | None = None

class IngestionConfig(BaseModel):
    github_token: SecretStr | None = None
```

Callers that need the raw value use `.get_secret_value()`. This is the standard Pydantic pattern for secret fields.

---

### SEC-14-002: `read_certificate` Path Traversal via Unsanitized `cert_id` (SEVERITY: MEDIUM)

**File**: `storage.py:134-149`

```python
def read_certificate(self, cert_id: str) -> CalibrationCertificate:
    path = self._base / "certificates" / f"{cert_id}.json"
```

The `cert_id` parameter is used directly in path construction without any sanitization. While `repo_dir()` (line 38-41) includes a `..` guard and leading-`/` check, `read_certificate` does not. An attacker-controlled `cert_id` like `../../etc/passwd` would resolve outside the intended directory.

The `write_certificate` method is safe because `cert.certificate_id` is generated from `uuid4()`, but `read_certificate` accepts arbitrary caller input.

**Recommendation**: Apply the same sanitization pattern used in `repo_dir`, or validate that `cert_id` matches a UUID pattern:
```python
import re
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

def read_certificate(self, cert_id: str) -> CalibrationCertificate:
    if not UUID_RE.match(cert_id):
        raise ValueError(f"Invalid certificate ID format: {cert_id}")
    path = self._base / "certificates" / f"{cert_id}.json"
    ...
```

Alternatively, resolve the path and confirm it stays within `self._base`:
```python
resolved = (self._base / "certificates" / f"{cert_id}.json").resolve()
if not str(resolved).startswith(str(self._base.resolve())):
    raise ValueError("Path traversal detected")
```

---

### SEC-14-003: `OracleConfig` Python Mode Enables Arbitrary Code Execution (SEVERITY: MEDIUM)

**File**: `config.py:22-43`

The `OracleConfig` with `type="python"` accepts a `module` and `callable` string. While the current code only validates that these fields are non-empty, the actual import and invocation (presumably in the oracle adapter, not yet implemented in the audited files) will dynamically load and execute arbitrary Python code specified by the caller.

**Risk**: If the API accepts `OracleConfig` from untrusted input (via `VerificationRunRequest`), an attacker could specify `module="os"` and `callable="system"` to achieve arbitrary code execution. The `VerificationRunRequest` model directly embeds `OracleConfig` (line 91).

**Recommendation**:
1. Add an allowlist of permitted modules/callables.
2. Alternatively, restrict `type="python"` to server-side configuration only, not API request input. Add a validator to `VerificationRunRequest` that rejects `oracle.type == "python"`.
3. Document the trust boundary clearly.

---

### SEC-14-004: `repo_dir` Path Traversal Guard Is Incomplete (SEVERITY: LOW)

**File**: `storage.py:38-41`

```python
safe_name = repo.replace("/", "_")
if ".." in safe_name or safe_name.startswith("/"):
    raise ValueError(f"Invalid repo name: {repo}")
```

The guard checks for `..` after replacing `/` with `_`, which means `..` in the original input (without `/`) is caught. However, the check does not account for:
- Null bytes (`\x00`) which can truncate paths in some C-level filesystem APIs
- Backslash path separators (`\`) on Windows or mixed-platform deployments
- Very long directory names that could hit filesystem limits

The current guard is adequate for a Linux-only deployment receiving GitHub `owner/repo` strings, but could be hardened.

**Recommendation**: Use a stricter allowlist regex:
```python
import re
if not re.match(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$', repo):
    raise ValueError(f"Invalid repo name: {repo}")
```

---

### SEC-14-005: `append_jsonl` Atomic Write Is Not Truly Atomic (SEVERITY: LOW)

**File**: `storage.py:46-67`

The method writes to a temp file, then reads its content and appends to the target file. This is not atomic — if the process crashes between the `target.write()` and `os.unlink(tmp_path)`, the temp file remains on disk (though the `finally` block mitigates this). More critically, there is a TOCTOU window: two concurrent calls to `append_jsonl` on the same path could interleave their appends, though JSONL format is line-oriented so this would not corrupt records (each write is a complete line).

The `write_certificate` method (line 108-118) correctly uses `os.rename()` for atomic replacement, which is the right pattern.

**Recommendation**: For `append_jsonl`, consider using `fcntl.flock()` or `filelock` for concurrent access protection, or accept the current behavior as adequate for single-process use and document the limitation.

---

### SEC-14-006: No Symlink Resolution in File Operations (SEVERITY: LOW)

**File**: `storage.py` (throughout)

File operations use `Path` objects without resolving symlinks. If an attacker can create a symlink within the `base_dir` (e.g., `data/certificates -> /etc/`), subsequent writes would follow the symlink to arbitrary locations.

**Risk**: Low in practice — requires pre-existing write access to the data directory. However, defense-in-depth suggests resolving paths before I/O.

**Recommendation**: Add `.resolve()` calls and verify the resolved path remains under `self._base.resolve()` in write operations:
```python
resolved = path.resolve()
if not str(resolved).startswith(str(self._base.resolve())):
    raise ValueError("Symlink escape detected")
```

---

### SEC-14-007: `list_certificates` Uses `json.loads` Without Schema Validation (SEVERITY: LOW)

**File**: `storage.py:151-166`

```python
entries.append(json.loads(stripped))
```

Unlike `read_jsonl` which deserializes into typed Pydantic models, `list_certificates` returns raw `dict` objects from `json.loads`. If the index file is tampered with, callers receive unvalidated data.

**Recommendation**: Define a lightweight Pydantic model for index entries:
```python
class CertificateIndexEntry(BaseModel):
    certificate_id: str
    construct_id: str
    composite_score: float
    replay_count: int
    timestamp: str
```

---

### SEC-14-008: Dependency Versions Are Acceptable (SEVERITY: INFO)

**File**: `pyproject.toml`

| Dependency | Pinned | Status |
|-----------|--------|--------|
| pydantic>=2.12 | Floor only | Current as of Feb 2026 |
| httpx>=0.28 | Floor only | Current |
| anthropic>=0.74 | Floor only | Current |
| click>=8.0 | Floor only | Current |
| fastapi>=0.121 | Floor only | Current |
| uvicorn>=0.34 | Floor only | Current |
| setuptools>=68.0 | Floor only | Current |

No known CVEs for these version ranges. Using floor-only pins (`>=`) is standard for libraries but means builds are not reproducible. Consider adding a lockfile (`pip-compile`, `uv lock`, or similar) for deployment.

---

### SEC-14-009: `VerificationRunRequest.scoring` Default Assignment Bypasses Type Checking (SEVERITY: INFO)

**File**: `models.py:92`

```python
scoring: "ScoringConfig" = None  # type: ignore[assignment]
```

The `type: ignore` comment suppresses the type checker warning about assigning `None` to a non-optional field. While `model_post_init` resolves this at runtime, the pattern is fragile — if `model_post_init` is ever removed or skipped, `scoring` would be `None` at runtime despite the type annotation claiming otherwise.

**Recommendation**: Use `ScoringConfig | None = None` as the field type and handle the `None` case explicitly in downstream code, or use `Field(default_factory=ScoringConfig)`.

---

## Disposition

No HIGH-severity findings. The MEDIUM findings (SEC-14-001, SEC-14-002, SEC-14-003) represent real risks but are mitigable in the next sprint iteration:

- **SEC-14-001** (secrets as plain str) is the highest priority — it can leak credentials in API error responses.
- **SEC-14-002** (cert_id path traversal) depends on whether `read_certificate` is exposed via API with user-controlled input.
- **SEC-14-003** (python oracle RCE) depends on whether the API endpoint is exposed to untrusted callers.

**Verdict: AUDIT_APPROVED** with the expectation that SEC-14-001 and SEC-14-002 are addressed in the next sprint.
