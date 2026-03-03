APPROVED - LETS FUCKING GO

# Security Audit — Sprint 21 (Cycle-011 Sprint-1): Evidence Pipeline Core + WorldMonitor Collector

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-03
**Verdict**: APPROVED (0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW findings)

---

## Scope

All source files in `backend/osint/` (10 source modules, 6 test modules, 4 fixture JSON files, 1 registry JSON).

### Files Audited

| File | Lines | Type |
|------|-------|------|
| `backend/osint/__init__.py` | 40 | Package init |
| `backend/osint/canonical.py` | 72 | Canonical hashing |
| `backend/osint/models/__init__.py` | 2 | Subpackage init |
| `backend/osint/models/evidence.py` | 54 | Evidence models |
| `backend/osint/models/registry.py` | 182 | Registry loader |
| `backend/osint/collectors/__init__.py` | 2 | Subpackage init |
| `backend/osint/collectors/base.py` | 100 | BaseCollector ABC |
| `backend/osint/collectors/worldmonitor.py` | 329 | WM collector |
| `backend/osint/engine/__init__.py` | 2 | Subpackage init |
| `backend/osint/engine/collection_runner.py` | 167 | Collection runner |
| `backend/osint/sources.json` | 84 | Registry data |
| `backend/osint/tests/conftest.py` | 109 | Test fixtures |
| `backend/osint/tests/test_canonical.py` | 144 | Canonical tests |
| `backend/osint/tests/test_receipt.py` | 90 | Receipt tests |
| `backend/osint/tests/test_models.py` | 163 | Model tests |
| `backend/osint/tests/test_worldmonitor.py` | 263 | Collector tests |
| `backend/osint/tests/test_collection_runner.py` | 233 | Runner tests |
| `backend/osint/tests/test_registry_loader.py` | 212 | Registry tests |
| `backend/osint/tests/fixtures/*.json` | 193 | Mock responses |

---

## Security Checklist

| # | Category | Verdict | Notes |
|---|----------|---------|-------|
| 1 | Secrets / Hardcoded Credentials | **PASS** | Zero API keys, tokens, passwords, or secrets anywhere. `base_url` defaults to `localhost:8080`. No auth headers. No credential stores. Grep for `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL` returned zero hits. |
| 2 | Code Injection (eval/exec/subprocess) | **PASS** | Zero instances of `eval()`, `exec()`, `subprocess`, `os.system()`, `__import__()`, `compile()`, `pickle`, `yaml.load`, `marshal`, `shelve`. All code uses safe stdlib operations only. |
| 3 | Input Validation | **PASS (with note)** | External JSON is parsed with `json.loads()` (safe). `json.load()` for registry file. `MeasureType` enum validated with `try/except ValueError` fallback. Registry validation checks 5 enum constraints. See MEDIUM-1 for `base_url` concern. |
| 4 | Auth / Access Control | **PASS** | No authentication or access control logic present (out of scope for evidence collection layer). HTTP calls carry no auth headers by design (self-hosted WM fork). |
| 5 | Data Privacy / PII | **PASS** | No PII processing. Data is geopolitical OSINT (country instability indices, maritime anomalies, market snapshots). No user data, emails, names, or IP addresses in source or fixtures. |
| 6 | Error Handling / Info Disclosure | **PASS (with note)** | Error messages include exception type and message (`f"Connection error: {exc}"`). This could leak internal stack details if `exc` contains sensitive info. In practice, urllib/asyncio exceptions contain only network-level details (host, port, error code). See LOW-1. |
| 7 | Dependency Safety | **PASS** | Source imports: `hashlib`, `json`, `asyncio`, `time`, `urllib.request`, `urllib.error`, `dataclasses`, `datetime`, `typing`, `abc`, `enum` -- all stdlib. Test imports add `pytest`, `unittest.mock`, `tempfile`, `os`, `pathlib` -- all stdlib or test-only. Zero new runtime dependencies. |
| 8 | Path Traversal / File I/O | **PASS (with note)** | `RegistryLoader.__init__` takes a `registry_path: str` and passes it directly to `open()`. The path is not validated against traversal attacks. However, the path is always derived from `Path(__file__).parent / "sources.json"` in production code and test fixtures. External callers providing arbitrary paths is a theoretical concern. See MEDIUM-2. |
| 9 | Integer Overflow | **PASS** | Numeric operations: `time.monotonic() * 1000` (float), `int(timestamp.timestamp())` (for ID generation), `measure.get("value", 0.0)`. All are standard Python float/int ops with no overflow risk. |
| 10 | Race Conditions | **PASS** | Async code uses `asyncio.gather()` which is cooperative (single-threaded event loop). `run_in_executor()` delegates to thread pool but each call is independent (no shared mutable state between threads). `RegistryLoader` is stateless after `__init__`. `CollectionRunner` does not modify shared state during `collect()`. |
| 11 | Supply Chain | **PASS** | All imports verified: `backend.osint.*` (internal), `backend.schemas.worldmonitor_api_contract` (internal API contract), stdlib modules. No third-party packages. No dynamic imports. No `__import__()`. |
| 12 | HTTP Security | **PASS (with notes)** | Uses `urllib.request.urlopen()` with explicit `timeout` parameter. Default `base_url` is `http://localhost:8080` (local, no TLS). No certificate validation concern for localhost. No auth headers sent. See specific concerns below for SSRF and response size analysis. |

---

## Specific Security Concerns Investigated

### 1. SSRF via `base_url` (MEDIUM-1)

**File**: `backend/osint/collectors/worldmonitor.py`, line 44, line 119
**Analysis**: `WorldMonitorConfig.base_url` defaults to `http://localhost:8080` and is concatenated with endpoint paths on line 119: `url = f"{self._config.base_url}{self._endpoint}"`. There is no URL validation or allowlist. A caller who constructs `WorldMonitorConfig(base_url="http://internal-service:9200")` could direct requests to arbitrary internal services.
**Mitigation**: The `WorldMonitorConfig` is a `@dataclass` created by application code, not from user input. The `base_url` is set at collector construction time, not per-request. In the current architecture, only the `CollectionRunner` instantiates collectors, and it receives them pre-configured. No user-controllable path leads to arbitrary `base_url` values.
**Verdict**: MEDIUM -- theoretical SSRF if the config surface is ever exposed to untrusted input. Not exploitable in current architecture. Recommend adding URL scheme validation (`http`/`https` only) and optional hostname allowlist when the config surface expands.

### 2. JSON Deserialization Safety

**File**: `backend/osint/collectors/worldmonitor.py`, line 198
**Analysis**: `json.loads(raw_payload)` is safe for deserialization. Python's `json` module does not execute code during deserialization (unlike `pickle`, `yaml.load`, or `marshal`). The parsed dict is accessed via `.get()` with defaults throughout `_build_bundle()`. No type coercion attacks are possible.
**Verdict**: PASS -- no deserialization risk.

### 3. Canonical Hash Collision

**File**: `backend/osint/canonical.py`, lines 38-53
**Analysis**: Uses SHA-256 (`hashlib.sha256`), which has 256-bit collision resistance. Finding two different payloads with the same hash requires approximately 2^128 operations (birthday attack). This is computationally infeasible. The canonical form (`json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)`) is deterministic -- same dict always produces same string. The bytes-based `compute_content_hash` hashes raw wire bytes, eliminating re-serialization variance.
**Verdict**: PASS -- SHA-256 collision resistance is sufficient.

### 4. Async Resource Leaks

**File**: `backend/osint/collectors/worldmonitor.py`, lines 163-185 and 301-329; `backend/osint/engine/collection_runner.py`, lines 87-106
**Analysis**:
- `_do_http_post`: Uses `with urllib.request.urlopen(...)` context manager, ensuring the connection is closed even on exception. The `run_in_executor` call is wrapped in `asyncio.wait_for(timeout)`. On timeout, `asyncio.wait_for` cancels the future, but the thread pool thread may still be running the sync `urlopen` call. However, `urlopen` has its own `timeout` parameter set to the same value, so the socket-level timeout will fire independently.
- `health_check`: Same pattern as `_do_http_post`. Uses `with` context manager for `urlopen`.
- `CollectionRunner.collect`: Uses `asyncio.gather(*tasks)` without `return_exceptions=True`. If a task raises, `gather` will cancel remaining tasks. However, each task is wrapped in `_collect_with_timeout` which catches all exceptions, so `gather` will never see an unhandled exception. No leaked tasks.
**Verdict**: PASS -- minor theoretical thread leak on timeout (thread pool thread may outlive the cancelled future), but the socket timeout provides a hard upper bound. Not exploitable.

### 5. Registry File Path Traversal (MEDIUM-2)

**File**: `backend/osint/models/registry.py`, line 94, line 101
**Analysis**: `RegistryLoader.__init__(registry_path: str)` passes `registry_path` directly to `open(self._path, "r", encoding="utf-8")`. No path validation, no `os.path.realpath()`, no directory restriction. If a caller passes `"../../../../etc/passwd"`, it would attempt to read that file.
**Mitigation**: In current usage, the path is always derived from code-level constants (`Path(__file__).parent / "sources.json"` in conftest.py, and production code will use similar patterns). No user input reaches this path. However, the API does not enforce this.
**Verdict**: MEDIUM -- path traversal is theoretically possible but not exploitable in current architecture. Recommend adding `os.path.realpath()` normalization and directory validation when the registry path becomes configurable.

### 6. HTTP Response Size Bounds

**File**: `backend/osint/collectors/worldmonitor.py`, line 180
**Analysis**: `resp.read()` reads the entire HTTP response body into memory with no size limit. A malicious or compromised WorldMonitor server could return a multi-gigabyte response body, causing OOM.
**Mitigation**: The WorldMonitor is a self-hosted fork (`AITOBIAS04/worldmonitor`), running on the same host or trusted network. The `timeout_s` parameter provides a wall-clock limit (default 30s), which indirectly bounds the amount of data that can be transferred. At typical local network speeds (100 MB/s), 30s = ~3 GB theoretical max. In practice, OSINT responses are kilobytes.
**Verdict**: LOW-2 -- theoretical OOM from unbounded `resp.read()`. Not exploitable with trusted self-hosted WM. Recommend adding `resp.read(max_bytes)` limit when WM moves to remote/untrusted deployment.

---

## Findings Summary

| ID | Severity | Title | File | Exploitable Now? |
|----|----------|-------|------|------------------|
| MEDIUM-1 | MEDIUM | No URL validation on `base_url` (theoretical SSRF) | `worldmonitor.py:44,119` | NO |
| MEDIUM-2 | MEDIUM | No path validation on `registry_path` (theoretical traversal) | `registry.py:94,101` | NO |
| LOW-1 | LOW | Error messages may leak internal exception details | `worldmonitor.py:137-146` | NO (network-level info only) |
| LOW-2 | LOW | Unbounded `resp.read()` (theoretical OOM) | `worldmonitor.py:180` | NO (trusted self-hosted WM) |
| LOW-3 | LOW | Unbound `duration_ms` if `retry_count < 0` | `worldmonitor.py:157` | NO (negative retry_count not used) |

All findings are **non-blocking**. None are exploitable in the current architecture. They represent hardening opportunities for future sprints when the system moves from self-hosted localhost to remote/untrusted deployment.

---

## Observations (Non-Findings)

### 1. HTTP over plaintext (INFORMATIONAL)
Default `base_url` is `http://localhost:8080` -- no TLS. Acceptable for same-host communication. When WM moves to remote deployment, this must change to HTTPS with certificate validation.

### 2. No rate limiting (INFORMATIONAL)
The collector has no client-side rate limiting. The `retry_delay_s` provides backoff between retries, but there is no per-second or per-minute request cap. Not needed for self-hosted WM, but required before connecting to external APIs.

### 3. Thread pool executor is default (INFORMATIONAL)
`loop.run_in_executor(None, _sync_post)` uses the default thread pool executor. This is fine for the current 3-collector setup but could become a bottleneck if dozens of collectors run concurrently. Consider a bounded `ThreadPoolExecutor` for production scale.

### 4. `asyncio.get_event_loop()` deprecation (INFORMATIONAL)
Lines 169 and 309 use `asyncio.get_event_loop()` which is deprecated in Python 3.10+ when called without a running loop. Both call sites are inside `async` methods (always have a running loop) and target Python 3.9.6. Replace with `asyncio.get_running_loop()` when upgrading.

### 5. Hash invariant is tautological for WorldMonitorCollector (DESIGN)
`BaseCollector._enforce_hash_invariants()` re-verifies hashes that `WorldMonitorCollector._build_success_result()` just computed. This is by design -- the invariant catches bugs in future subclass collectors, not this specific implementation. Acceptable architecture.

---

## Test Coverage Verification

| Suite | Tests | Status |
|-------|-------|--------|
| test_canonical.py | 16 | ALL PASS |
| test_receipt.py | 5 | ALL PASS |
| test_models.py | 8 | ALL PASS |
| test_worldmonitor.py | 17 | ALL PASS |
| test_collection_runner.py | 7 | ALL PASS |
| test_registry_loader.py | 15 | ALL PASS |
| **Sprint 21 Total** | **68** | **ALL PASS (0.17s)** |

### Regression

| Suite | Tests | Status |
|-------|-------|--------|
| backend/market/ | 97 | ALL PASS |
| backend/engines/ | 145 | ALL PASS |
| **Regression Total** | **242** | **ALL PASS (0.29s)** |

### Test Quality Assessment

- All HTTP calls mocked -- no real network I/O in any test
- Error paths covered: timeout, HTTP 500, connection refused, malformed JSON
- Retry logic tested: flaky-then-success, all-retries-exhausted
- Partial failure tested: 1-of-3 fail, all-3-fail
- Boundary tests: empty dict, empty bytes, deeply nested JSON
- Cross-verification: re-exported functions match API contract originals
- Registry validation: invalid enum values, empty fields detected
- Alignment tests: all 3 WM sources verified against PRD Section 4.6

### Coverage Gaps (Non-Blocking)

1. No test for `_do_http_post` with a real `urllib.request.Request` (always mocked at a higher level) -- acceptable since we don't want real HTTP in tests
2. No test for `health_check` returning HEALTHY or DEGRADED (only tests UNAVAILABLE via real connection failure) -- acceptable for Sprint 1
3. No test for negative `retry_count` -- edge case noted in LOW-3

---

## Code Quality Verification

| Check | Result |
|-------|--------|
| `from __future__ import annotations` in all 18 .py files | PASS |
| No bare `except:` statements | PASS |
| No `eval()`, `exec()`, `subprocess`, `pickle` | PASS |
| No hardcoded credentials | PASS |
| No new runtime dependencies (stdlib only) | PASS |
| No modifications to `backend/market/` | PASS |
| No modifications to `backend/engines/` | PASS |
| All public functions have docstrings | PASS |
| All function signatures have type hints | PASS |
| Consistent snake_case naming | PASS |

---

## Final Verdict

**APPROVED**. The implementation is clean, well-architected, and thoroughly tested. 68 tests (3.4x the 20-test target) with zero failures. All 20 acceptance criteria verified by independent review. No CRITICAL or HIGH severity findings. The 2 MEDIUM findings (SSRF via base_url, path traversal via registry_path) are theoretical concerns not exploitable in the current self-hosted architecture. They represent hardening opportunities for future deployment scenarios.

The evidence collection layer is secure for its intended operational context (self-hosted WorldMonitor on localhost). When the deployment model changes to remote/untrusted endpoints, the MEDIUM findings should be addressed.
