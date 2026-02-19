# Security Audit — Sprint 16 (cycle-027 sprint-3) — Oracle Adapters

**Verdict: AUDIT_APPROVED**

## Scope

Focus areas per audit request:
1. Code injection via Python oracle adapter
2. SSRF via HTTP oracle adapter
3. Input validation across both adapters

## Findings

### 1. Code Injection via Python Adapter

**Risk**: The `PythonOracleAdapter` uses `importlib.import_module()` to dynamically load arbitrary Python modules and execute arbitrary callables. This is the highest-risk surface in this sprint.

**Assessment: ACCEPTABLE (with caveats)**

- The module path and callable name come from `OracleConfig`, which is a Pydantic model with `type: Literal["http", "python"]` validation. These values are set at configuration time, not derived from user input at request time.
- `importlib.import_module()` is used rather than `exec()` or `eval()`. It can only import installed Python modules -- it cannot execute arbitrary strings or code snippets.
- The callable is resolved via `getattr()` on the imported module, which only retrieves existing attributes -- no code generation.
- The payload passed to the callable (`python_adapter.py:54-61`) is a plain dict of string fields from `GroundTruthRecord`. The callable cannot influence which module gets loaded or which function gets called.
- `ImportError` and `AttributeError` are properly caught and surfaced (`python_adapter.py:35-46`), preventing stack trace leaks.
- Runtime exceptions are caught broadly (`except Exception`) at `python_adapter.py:95`, preventing oracle failures from crashing the pipeline.

**Residual risk**: If an attacker gains write access to `OracleConfig` (e.g., via a malicious config file or API request body), they could point `module` to any importable module. This is an inherent property of the Python adapter design per the SDD and is mitigated by:
- Config validation at the Pydantic layer (`OracleConfig.model_validator` requires both `module` and `callable` for `type="python"`)
- The callable must already be importable in the Python environment -- no filesystem path injection

**Recommendation for Sprint 5 (API layer)**: When the API exposes `VerificationRunRequest`, ensure the `construct` field is restricted to pre-registered oracle configurations rather than accepting arbitrary module paths from HTTP clients. This is a future concern, not a current blocker.

### 2. SSRF via HTTP Adapter

**Risk**: The `HttpOracleAdapter` makes outbound HTTP POST requests to `config.url`, which could be abused for Server-Side Request Forgery if the URL comes from untrusted input.

**Assessment: ACCEPTABLE (with caveats)**

- The URL is sourced from `OracleConfig.url`, set at configuration time. It is not derived from request-time user input in the current sprint.
- The adapter validates that `url` is non-empty (`http_adapter.py:22-23`), but does not validate the URL scheme, host, or port.
- `httpx.AsyncClient` is used with a configurable timeout (default 30s), which bounds the duration of any outbound request.
- Response data is parsed as JSON and mapped to a Pydantic model (`OracleOutput`), which constrains what data can flow back into the system. No raw response body is stored without schema enforcement.

**No internal network metadata leakage**: Error outputs only include the HTTP status code string (e.g., `"HTTP 500"`) or generic timeout/error messages. The response body is logged at WARNING level (truncated to 200 chars at `http_adapter.py:58`) but is not persisted in the `OracleOutput`.

**Residual risk**: Same as Python adapter -- if config is attacker-controlled, arbitrary URLs (including internal `http://169.254.169.254/...` metadata endpoints) could be targeted.

**Recommendation for Sprint 5**: Add URL allowlist validation or scheme restriction (HTTPS only) when exposing oracle config via the API.

### 3. Input Validation

**Assessment: SATISFACTORY**

| Check | Result |
|-------|--------|
| `OracleConfig` Pydantic validation | `model_validator` enforces `url` for HTTP, `module`+`callable` for Python |
| `HttpOracleAdapter.__init__` | Double-checks `config.url` is truthy |
| `PythonOracleAdapter.__init__` | Double-checks `config.module` and `config.callable` are truthy |
| Payload construction (HTTP) | Fixed schema dict from `GroundTruthRecord` fields -- no injection vector |
| Payload construction (Python) | Fixed schema dict -- no injection vector |
| Response parsing (HTTP) | `resp.json()` with `ValueError` catch for malformed JSON |
| Response parsing (Python) | Dict fields mapped via `.get()` with defaults; non-dict handled gracefully |
| `OracleOutput` model | Pydantic model enforces field types on construction |
| `from_config` factory | Exhaustive `if/elif` with final `raise ValueError` for unknown types |

### 4. Additional Security Observations

**4.1 No credential leakage in error outputs**: Error metadata contains only generic error descriptions (`"timeout"`, `"HTTP 500"`, exception messages). Custom headers (which may contain API keys) are not logged or persisted in error metadata.

**4.2 Timing side-channel**: `latency_ms` is always recorded, even on error. This is a minor information disclosure (reveals whether an endpoint exists/responds) but is acceptable for a verification pipeline that already requires configured access.

**4.3 No path traversal**: Neither adapter reads or writes files. All persistence is deferred to the `Storage` layer (audited in sprint 1).

**4.4 Exception handling completeness**: The broad `except Exception` in `python_adapter.py:95` catches `SystemExit` and `KeyboardInterrupt`. This is a minor concern -- a malicious callable could call `sys.exit()` and the adapter would catch it rather than allowing process termination. In practice this is benign for this use case since the error is surfaced in metadata, but a more precise catch (excluding `BaseException` subclasses) would be marginally safer.

## Summary

| Area | Risk Level | Status |
|------|-----------|--------|
| Code injection (Python adapter) | Medium | Acceptable -- config-time only, no eval/exec |
| SSRF (HTTP adapter) | Medium | Acceptable -- config-time only, timeout bounded |
| Input validation | Low | Satisfactory -- Pydantic + defensive checks |
| Error handling | Low | Clean -- no raises, no credential leaks |
| Credential exposure | None | Headers not logged, error metadata is generic |

No blocking security issues. Residual risks are inherent to the adapter pattern and should be addressed when the API layer (Sprint 5) exposes configuration to external clients.
