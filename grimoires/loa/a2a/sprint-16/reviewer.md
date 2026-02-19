# Sprint 16 (cycle-027 sprint-3) — Implementation Report

## Oracle Adapters

**Status**: COMPLETE
**Files Created**: 4
**Tests**: 12 passed, 0 failed

## Task Completion

### 3.1 — OracleAdapter ABC ✅

`verification/src/echelon_verify/oracle/base.py`:
- Abstract `invoke(ground_truth, follow_up_question) -> OracleOutput` method
- `from_config()` factory dispatches to HTTP or Python adapter
- Raises `ValueError` for unknown oracle type

### 3.2 — HTTP Oracle Adapter ✅

`verification/src/echelon_verify/oracle/http_adapter.py`:
- POSTs JSON body with PR data (id, title, description, diff_content, files_changed) + follow_up_question
- Parses JSON response into `OracleOutput`
- Handles: timeout, HTTP 4xx/5xx, malformed JSON responses
- Custom headers from `OracleConfig.headers`
- Records `latency_ms` in output
- On failure: returns `OracleOutput` with `metadata.error` set (no raise)

### 3.3 — Python Oracle Adapter ✅

`verification/src/echelon_verify/oracle/python_adapter.py`:
- Dynamically imports `config.module` and gets `config.callable` at init
- Calls with dict payload (PR data + follow_up_question)
- Wraps sync callables in `asyncio.to_thread()`, supports async callables via `inspect.iscoroutinefunction()`
- Handles: `ImportError`, `AttributeError`, runtime exceptions
- Records `latency_ms`, returns `metadata.error` on failure

### 3.4 — Tests ✅

12 tests across 3 test classes:

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestOracleAdapterFactory` | 3 | HTTP creation, Python creation, unknown type |
| `TestHttpOracleAdapter` | 5 | Success, timeout, HTTP error, malformed JSON, custom headers |
| `TestPythonOracleAdapter` | 4 | Sync callable, nonexistent module, nonexistent callable, runtime error |

Test fixture: `mock_oracle_sync()` and `mock_oracle_error()` defined in test module.

## Files Created

```
verification/src/echelon_verify/oracle/base.py           (35 lines)
verification/src/echelon_verify/oracle/http_adapter.py   (116 lines)
verification/src/echelon_verify/oracle/python_adapter.py (105 lines)
verification/tests/test_oracle_adapters.py               (176 lines)
```
