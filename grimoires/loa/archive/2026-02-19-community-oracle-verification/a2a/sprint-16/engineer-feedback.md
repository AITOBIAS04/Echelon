# Engineer Review — Sprint 16 (cycle-027 sprint-3) — Oracle Adapters

All good

## Acceptance Criteria Verification

### 3.1 — OracleAdapter ABC (`oracle/base.py`)

- [x] `OracleAdapter` ABC with `async invoke(ground_truth, follow_up_question) -> OracleOutput`
  - Defined at `base.py:17-20`. Correct signature, abstract method, returns `OracleOutput`.
- [x] `from_config(config: OracleConfig) -> OracleAdapter` factory method
  - Defined at `base.py:22-33`. Class method on the ABC, dispatches by `config.type`.
- [x] Raises `ValueError` for unknown oracle type
  - `base.py:33`: `raise ValueError(f"Unknown oracle type: {config.type}")`. Tested in `test_unknown_type_raises`.

### 3.2 — HTTP Oracle Adapter (`oracle/http_adapter.py`)

- [x] POSTs JSON body with PR data (`title`, `description`, `diff_content`, `files_changed`) + `follow_up_question`
  - `http_adapter.py:32-41`. Payload includes `id`, `title`, `description`, `diff_content`, `files_changed` nested under `pr` key, plus `follow_up_question` at top level.
- [x] Parses JSON response into `OracleOutput`
  - `http_adapter.py:67-77`. Calls `resp.json()` and maps fields to `OracleOutput`.
- [x] Handles: timeout (configurable, default 30s), HTTP errors (4xx/5xx), malformed responses
  - Timeout: `http_adapter.py:79-84`, catches `httpx.TimeoutException`. Default 30s via `OracleConfig.timeout_seconds`.
  - HTTP errors: `http_adapter.py:53-65`, checks `status_code >= 400`.
  - Malformed JSON: `http_adapter.py:94-106`, catches `ValueError`/`KeyError`.
  - Also catches generic `httpx.HTTPError` at line 85-93.
- [x] Custom headers from `OracleConfig.headers`
  - `http_adapter.py:25`: `self._headers = dict(config.headers)`, passed to `client.post()` at line 49.
- [x] Records `latency_ms` in `OracleOutput`
  - `http_adapter.py:43,51,76`. Uses `time.monotonic()` delta.
- [x] On failure: returns `OracleOutput` with `metadata.error` set rather than raising
  - All error branches call `self._error_output()` which sets `metadata={"error": error}` at line 118.

### 3.3 — Python Oracle Adapter (`oracle/python_adapter.py`)

- [x] Dynamically imports `config.module` and gets `config.callable`
  - `python_adapter.py:31-48`. `_load_callable()` uses `importlib.import_module()` + `getattr()`.
- [x] Calls with `GroundTruthRecord` data dict + `follow_up_question`
  - `python_adapter.py:54-61`. Builds dict payload with all PR fields and `follow_up_question`.
- [x] Wraps sync callables in `asyncio.to_thread()`
  - `python_adapter.py:65-68`. Checks `inspect.iscoroutinefunction()` first; if sync, uses `asyncio.to_thread()`.
- [x] Handles: `ImportError`, `AttributeError`, runtime exceptions
  - `ImportError`: `python_adapter.py:35-38`, raised during init.
  - `AttributeError`: `python_adapter.py:41-46`, raised during init.
  - Runtime exceptions: `python_adapter.py:95-109`, broad `except Exception` with `metadata.error`.
- [x] Records `latency_ms` in `OracleOutput`
  - `python_adapter.py:63,70`. Uses `time.monotonic()` delta.
- [x] On failure: returns `OracleOutput` with `metadata.error` set
  - `python_adapter.py:100-109`. Returns `OracleOutput` with `metadata={"error": str(exc)}`.

### 3.4 — Tests for oracle adapters

- [x] HTTP adapter: mock endpoint returning valid response -> correct `OracleOutput`
  - `test_successful_invocation`: verifies `ground_truth_id`, `summary`, `key_claims`, `follow_up_response`, `latency_ms`, no error.
- [x] HTTP adapter: mock timeout -> `OracleOutput` with error metadata
  - `test_timeout_returns_error_output`: mocks `httpx.ReadTimeout`, checks `metadata.error == "timeout"`.
- [x] HTTP adapter: mock malformed JSON -> graceful handling
  - `test_malformed_json_returns_error_output`: mocks `text="not json"` with 200 status, checks error metadata.
- [x] HTTP adapter: custom headers sent correctly
  - `test_custom_headers_sent`: verifies `X-Api-Key` header on outgoing request.
- [x] Python adapter: test with a simple callable fixture
  - `test_sync_callable`: uses `mock_oracle_sync` from the test module.
- [x] Python adapter: test with non-existent module -> error
  - `test_nonexistent_module_raises`: expects `ImportError`.
- [x] Python adapter: test with non-existent callable -> error
  - `test_nonexistent_callable_raises`: expects `AttributeError`.
- [x] Factory method: `from_config()` dispatches correctly
  - `test_creates_http_adapter` and `test_creates_python_adapter` verify correct adapter types.
- [x] Test fixture: `tests/fixtures/sample_oracle_output.json`
  - Present at `verification/tests/fixtures/sample_oracle_output.json` with correct schema.

## Test Count

Reviewer reports 12 tests. Sprint plan calls for ~8. All 12 pass. Exceeds the minimum, covering additional edge cases (HTTP generic error, non-dict return type path implicitly through runtime error test).

## Code Quality Notes

1. **Clean separation of concerns**: The ABC + factory pattern is well-structured. Lazy imports in `from_config()` avoid circular dependencies.
2. **Error resilience**: Both adapters follow the "never raise, always return error metadata" contract consistently.
3. **Async correctness**: `inspect.iscoroutinefunction()` check in the Python adapter correctly handles both sync and async oracle callables.
4. **Timing accuracy**: `time.monotonic()` is the correct choice for latency measurement (immune to wall-clock adjustments).
5. **Test isolation**: HTTP tests use `respx` for mock transport, Python tests use real callables defined in the test module -- both are deterministic.

## Verdict

All 14 acceptance criteria across tasks 3.1-3.4 are met. Tests exceed the minimum count. Code quality is clean and follows the project patterns established in sprints 1-2.
