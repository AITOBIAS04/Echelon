# SDD: MCP Server v1.0 — Status Tool, Calibrate Tool, HTTP Transport

**Cycle**: 009
**Version**: 1.0
**Date**: 2026-03-02
**PRD Reference**: `grimoires/loa/prd.md`

---

## 1. Executive Summary

Cycle-009 ships two new MCP tools (`echelon_status`, `echelon_calibrate`) and an HTTP transport layer. `echelon_status` is a stateless tool that scans the output directory to report construct verification state — tier, latest certificate, composite score, expiry, and certificate count. `echelon_calibrate` is a stateful tool that runs the full construct calibration pipeline via the existing `run_construct_calibration()` async runner and returns the certificate with a pipeline summary. The HTTP transport exposes all seven tools via JSON-RPC 2.0 at `POST /mcp`, plus a `/health` endpoint and an `/sse` stub, using Python's stdlib `http.server`. Server version bumps to 1.0.0.

---

## 2. Architecture Overview

The existing server architecture is a three-layer stack: **transport** (stdio) -> **dispatch** (JSON-RPC router) -> **tool handlers** (functions conforming to the `TOOL_DEFINITION` dict + `handle()` pattern). Cycle-009 preserves this architecture exactly and extends it along two axes:

1. **New tools**: `status` and `calibrate` modules are added to `mcp/tools/`, registered in the `TOOLS` dict in `server.py`, and dispatched through the same `handle_tools_call()` path.
2. **New transport**: `mcp/http.py` provides an HTTP transport that accepts JSON-RPC 2.0 POST requests and feeds them into the same `dispatch()` function used by stdio.

```
                    +---------------------------------------------+
                    |              MCP Clients                     |
                    +--------+--------------------------+---------+
                             |                          |
                      stdio (pipe)               HTTP POST /mcp
                      run_stdio()                MCPHttpHandler
                             |                          |
                    +--------+--------------------------+---------+
                    |              dispatch()                      |
                    |         (JSON-RPC 2.0 router)               |
                    +----+-------------+-------------+------------+
                    | initialize  | tools/list  | tools/call      |
                    +----+--------+-------------+--------+--------+
                                                         |
           +--------+--------+--------+--------+---------+--------+
           |        |        |        |        |         |        |
        verify  inspect   hash  schema_check replay  status  calibrate
        (v0.8)  (v0.8)  (v0.8)   (v0.8)    (v0.8)  (v1.0)   (v1.0)

    HTTP-only endpoints (bypass dispatch):
        GET /health  ->  {"status":"ok","version":"1.0.0","tools":7}
        GET /sse     ->  {"status":"not_implemented","available_from":"v1.3"}
```

**Key invariant**: The `dispatch()` function is the shared boundary between transports. Neither transport knows about the other. Tool handlers remain transport-agnostic — they accept a `Dict[str, Any]` arguments dict and return a `Dict[str, Any]` result dict.

**Dependency direction**: `mcp/http.py` imports `dispatch` from `mcp/server.py`. The reverse never occurs — `server.py` uses a lazy import (`from mcp.http import run_http`) only inside the `--http` CLI branch.

---

## 3. Component Design

### 3.1 `mcp/tools/status.py` — echelon_status

A stateless, file-system-reading tool that reports construct verification state by scanning the output directory for existing certificate JSON files.

#### TOOL_DEFINITION

```python
TOOL_DEFINITION = {
    "name": "echelon_status",
    "description": (
        "Query the current verification state of a construct. Returns the "
        "latest certificate, tier, composite score, expiry, and certificate count."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "construct_id": {
                "type": "string",
                "description": "Construct identifier (e.g. 'community_oracle_v1')",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory containing calibration results (default: 'output')",
            },
        },
        "required": ["construct_id"],
    },
}
```

#### handle() Signature and Logic

```python
def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
```

**Parameters**: `arguments` dict with `construct_id` (required, string) and `output_dir` (optional, string, defaults to `"output"`).

**Step-by-step logic**:

1. Extract `construct_id` from arguments. If missing or empty string, return `error_response("INPUT_MALFORMED", "Missing required field: construct_id")`.
2. Extract `output_dir`, default to `"output"`. Convert to `Path`.
3. Build certificate directory path: `Path(output_dir) / "construct_calibration" / construct_id / "certificates"`.
4. If directory does not exist or is not a directory, return a valid (non-error) response with `certificates_found: 0`, `latest_certificate: None`, `tier_summary: None`.
5. Scan directory for `*.json` files using `cert_dir.glob("*.json")`.
6. For each file, attempt `json.loads(file_path.read_text())`. If parsing fails, skip the file and continue (print a warning to `sys.stderr`). Do not crash.
7. Collect successfully parsed certificates into a list.
8. Sort by `issued_at` field (ISO 8601 string comparison). Certificates missing `issued_at` sort to the beginning (use empty string as sort key).
9. Select the last element (most recent) as `latest`.
10. Build the `tier_summary` from the latest certificate: read `replay_count`, compute `replays_needed` as `max(0, 50 - replay_count)` where 50 is `TierAssigner.BACKTESTED_MIN_REPLAYS`.
11. Return the structured response with `build_meta()`.

#### Output Schema

Success response:

```python
{
    "construct_id": str,                          # echo of input
    "certificates_found": int,                    # count of valid parsed certificates
    "latest_certificate": {                       # None if certificates_found == 0
        "certificate_id": str,
        "template_id": str,
        "composite_score": float,
        "verification_tier": str,                 # "UNVERIFIED" | "BACKTESTED" | "PROVEN"
        "issued_at": str,                         # ISO 8601
        "replay_count": int,
    },
    "tier_summary": {                             # None if certificates_found == 0
        "current_tier": str,
        "backtested_threshold": 50,               # constant from TierAssigner
        "current_replays": int,
        "replays_needed": int,                    # max(0, 50 - current_replays)
    },
    "_meta": { ... },                             # from build_meta()
}
```

#### Edge Cases

| Case | Behaviour |
|------|-----------|
| No certificates directory exists | `certificates_found: 0`, `latest_certificate: None`, `tier_summary: None`. No error. |
| Certificates directory is empty | Same as above. |
| Corrupt JSON file in certificates dir | Skip the file, print warning to stderr, continue scanning. Only valid files count. |
| Certificate missing `issued_at` | Treated as earliest in sort order (sort key: `""`). Still included in count and usable as `latest` if it is the only certificate. |
| Certificate missing other fields | Use `.get()` with defaults: `None` for strings, `0` for numeric fields, in `latest_certificate` dict. |
| `construct_id` is empty string | Return `error_response("INPUT_MALFORMED", "Missing required field: construct_id")`. |
| `construct_id` with no prior calibration | Valid response with `certificates_found: 0`. This is not an error — the construct simply has no certificates yet. |

#### Imports

```python
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.models.errors import error_response
from mcp.models.meta import build_meta
```

No `sys.path` manipulation needed. This tool reads files from the filesystem; it does not import from the pipeline, the verifier, or the theatre engine.

---

### 3.2 `mcp/tools/calibrate.py` — echelon_calibrate

A stateful tool that runs the full construct calibration pipeline via the existing async runner and returns the certificate.

#### TOOL_DEFINITION

```python
TOOL_DEFINITION = {
    "name": "echelon_calibrate",
    "description": (
        "Run the full construct calibration pipeline. Produces a calibration "
        "certificate with deterministic replay, scoring, tier assignment, "
        "and evidence bundle generation."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "construct_id": {
                "type": "string",
                "description": "Construct key from the registry (e.g. 'community_oracle_v1')",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for certificates and evidence bundles (default: 'output')",
            },
        },
        "required": ["construct_id"],
    },
}
```

#### handle() Signature and Logic

```python
def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
```

**Parameters**: `arguments` dict with `construct_id` (required, string) and `output_dir` (optional, string, defaults to `"output"`).

**Step-by-step logic**:

1. Extract `construct_id`. If missing, return `error_response("INPUT_MALFORMED", "Missing required field: construct_id")`.
2. Import `CONSTRUCTS` and `run_construct_calibration` from `scripts.run_construct_calibration` (these are imported at module level via `sys.path` setup, matching the pattern in `verify.py`).
3. Validate `construct_id` against the `CONSTRUCTS` registry dict. If unknown, return:
   ```python
   error_response(
       "INPUT_MALFORMED",
       f"Unknown construct: '{construct_id}'. "
       f"Available: {', '.join(CONSTRUCTS.keys())}"
   )
   ```
4. Extract `output_dir`, default to `"output"`. Convert to `Path`.
5. **Bridge async to sync** using `asyncio.run()`:
   ```python
   cert_path, cert_dict = asyncio.run(
       run_construct_calibration(construct_id, output_dir)
   )
   ```
6. Build `pipeline_summary` from `cert_dict` fields.
7. Run `echelon_verify` against the certificate to include the MCP verify verdict:
   ```python
   from mcp.tools import verify as mcp_verify
   verify_result = mcp_verify.handle({
       "certificate": {"mode": "inline", "value": cert_dict},
   })
   mcp_verify_verdict = verify_result.get("overall_verdict", "ERROR")
   ```
8. Return the combined response with `build_meta()`.

**Async-to-sync bridge rationale**:

The runner function `run_construct_calibration()` is `async` (declared at `scripts/run_construct_calibration.py:193`) and returns `tuple[Path, dict]` (the certificate file path and the certificate dict). The MCP tool `handle()` function is synchronous — it is called by `dispatch()` via `TOOLS[tool_name]["handler"](arguments)` at `server.py:117`.

`asyncio.run()` is the correct bridge because:
- No pre-existing event loop exists in the server thread during tool execution. The stdio transport reads blocking lines from stdin. The HTTP handler thread does not run an event loop.
- `asyncio.run()` creates a fresh event loop, runs the coroutine to completion, and tears it down. This is safe for single-threaded use.
- Available in Python 3.7+ (our minimum is 3.9).
- Alternative `asyncio.get_event_loop().run_until_complete()` is deprecated in Python 3.10+ for this use case.

#### Output Schema

Success response:

```python
{
    "certificate": dict,                          # full certificate dict from pipeline
    "pipeline_summary": {
        "construct_id": str,
        "template_id": str,
        "composite_score": float,
        "scores": dict,                           # e.g. {"precision": 0.8, "recall": 0.54, ...}
        "verification_tier": str,                 # "UNVERIFIED" | "BACKTESTED" | "PROVEN"
        "evidence_bundle_hash": str,              # SHA-256 hex
        "mcp_verify_verdict": str,                # "PASS" | "FAIL" | "WARN" | "ERROR"
    },
    "_meta": { ... },                             # from build_meta()
}
```

#### Error Handling

| Case | Error Code | Message |
|------|-----------|---------|
| Missing `construct_id` argument | `INPUT_MALFORMED` | `"Missing required field: construct_id"` |
| Unknown construct key | `INPUT_MALFORMED` | `"Unknown construct: '<key>'. Available: community_oracle_v1"` |
| Pipeline raises exception | `INTERNAL_ERROR` | The exception message string |
| `asyncio.run()` failure | `INTERNAL_ERROR` | The exception message string |
| Verify step fails | Not an error — `mcp_verify_verdict` is set to `"ERROR"` in the pipeline summary, but the overall response is still a success (the certificate was produced) |

The entire calibration + verify sequence is wrapped in a single `try/except Exception`:

```python
try:
    cert_path, cert_dict = asyncio.run(
        run_construct_calibration(construct_id, output_dir)
    )
    # ... build pipeline_summary, run verify ...
except Exception as e:
    return error_response("INTERNAL_ERROR", str(e))
```

#### Imports

```python
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.meta import build_meta

# Path setup for runner import — same pattern as verify.py, hash.py, etc.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.run_construct_calibration import CONSTRUCTS, run_construct_calibration
```

---

### 3.3 `mcp/http.py` — HTTP Transport

A minimal HTTP server using Python's stdlib `http.server` that wraps the existing `dispatch()` function behind an HTTP POST endpoint.

#### MCPHttpHandler Class

```python
class MCPHttpHandler(BaseHTTPRequestHandler):
```

Extends `http.server.BaseHTTPRequestHandler`.

**`do_POST(self)`**:

1. Check `self.path` is `/mcp`. If not, call `_send_json(404, {"error": "Not found"})` and return.
2. Read `Content-Length` header via `self.headers.get("Content-Length")`. If missing or non-integer, call `_send_json(400, {"error": "Missing or invalid Content-Length"})` and return.
3. Read request body: `self.rfile.read(content_length)`.
4. Attempt `json.loads(body)`. If parsing fails, build a JSON-RPC parse error response using `jsonrpc_error(None, -32700, f"Parse error: {e}")` and send it with status 200 (JSON-RPC errors are protocol-level, not HTTP-level).
5. Call `dispatch(message)` (imported from `mcp.server`).
6. If `dispatch()` returns `None` (the message was a notification), send a 204 No Content response with no body.
7. Otherwise, call `_send_json(200, response)`.

**`do_GET(self)`**:

1. If `self.path == "/health"`:
   - Call `_send_json(200, {"status": "ok", "version": "1.0.0", "tools": 7})`.
2. If `self.path == "/sse"`:
   - Call `_send_json(200, {"status": "not_implemented", "available_from": "v1.3"})`.
3. Otherwise:
   - Call `_send_json(404, {"error": "Not found"})`.

**`_send_json(self, status_code: int, data: dict) -> None`**:

Private helper that serialises the dict to JSON, sends the HTTP response with correct headers:

```python
def _send_json(self, status_code: int, data: dict) -> None:
    body = json.dumps(data).encode("utf-8")
    self.send_response(status_code)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)
```

**`log_message(self, format, *args)`**:

No override needed. `BaseHTTPRequestHandler` defaults to writing request logs to stderr. This is correct — stdout is reserved for the stdio transport.

#### run_http() Function

```python
def run_http(port: int = 3100) -> None:
    """Start the MCP HTTP server on the given port."""
    from http.server import HTTPServer

    server = HTTPServer(("", port), MCPHttpHandler)
    print(f"Echelon MCP HTTP server listening on port {port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
```

#### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single-threaded | Acceptable for v1.0 per PRD. Calibration takes <1 second for 12 fixture records. |
| No CORS headers | Out of scope per PRD (server-to-server use case). |
| No authentication | Out of scope per PRD. |
| stderr for all logging | Prevents contamination of stdio transport stdout. |
| Port default 3100 | Per PRD CLI specification. |
| JSON-RPC errors sent as HTTP 200 | Standard JSON-RPC 2.0 convention: protocol errors are communicated inside the JSON-RPC response, not via HTTP status codes. |
| HTTP 204 for notifications | Notifications have no JSON-RPC response. 204 No Content is the semantically correct HTTP response. |

#### Imports

```python
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

from mcp.server import dispatch, jsonrpc_error
```

The import of `jsonrpc_error` is needed for building parse error responses when the POST body is malformed JSON.

---

### 3.4 `mcp/server.py` — Updates

Four targeted modifications. No changes to `dispatch()`, `run_stdio()`, `jsonrpc_response()`, `jsonrpc_error()`, `handle_tools_list()`, `handle_tools_call()`, or `METHOD_HANDLERS`.

#### 3.4.1 Import New Tool Modules

Update the import line at line 23:

```python
# Before:
from mcp.tools import verify, inspect, hash, schema_check, replay

# After:
from mcp.tools import verify, inspect, hash, schema_check, replay, status, calibrate
```

#### 3.4.2 Register New Tools in TOOLS Dict

Add two entries after the existing five (after line 51):

```python
"echelon_status": {
    "definition": status.TOOL_DEFINITION,
    "handler": status.handle,
},
"echelon_calibrate": {
    "definition": calibrate.TOOL_DEFINITION,
    "handler": calibrate.handle,
},
```

#### 3.4.3 Version Bump in handle_initialize()

Change `serverInfo.version` from `"0.8.0"` to `"1.0.0"` at line 83:

```python
"serverInfo": {
    "name": "echelon-verifier",
    "version": "1.0.0",
},
```

#### 3.4.4 CLI Arguments for HTTP Transport

Extend the `main()` function to recognise `--http` and `--port` flags. Add a new `elif` branch before the existing `--help` branch:

```python
elif sys.argv[1] == "--http":
    port = 3100
    if "--port" in sys.argv:
        port_idx = sys.argv.index("--port")
        if port_idx + 1 < len(sys.argv):
            try:
                port = int(sys.argv[port_idx + 1])
            except ValueError:
                print(f"Invalid port: {sys.argv[port_idx + 1]}", file=sys.stderr)
                return 2
        else:
            print("--port requires a value", file=sys.stderr)
            return 2
    from mcp.http import run_http
    run_http(port)
    return 0
```

The `from mcp.http import run_http` is a **lazy import** inside the `--http` branch. This ensures the http module (and its import of `dispatch`) is only loaded when HTTP mode is explicitly requested, avoiding circular import concerns and unnecessary module loading for stdio mode.

#### 3.4.5 Updated Module Docstring

```python
"""
Echelon Verifier MCP Server — stdio and HTTP transport.

Implements MCP protocol (JSON-RPC 2.0) over stdin/stdout or HTTP.
Seven verification and calibration tools, no external SDK dependency, Python 3.9+.

Usage:
    python3 -m mcp.server                    # Start stdio server
    python3 -m mcp.server --http             # Start HTTP server on port 3100
    python3 -m mcp.server --http --port 8080 # Start HTTP server on custom port
    python3 -m mcp.server --list-tools       # Print tool definitions
    python3 -m mcp.server --call <tool> '{"arg": "val"}'  # One-shot call
"""
```

---

### 3.5 `mcp/__init__.py` — Version Bump

Replace the entire file content:

```python
"""
Echelon Verifier MCP Server — v1.0.0

Exposes 7 verification and calibration tools over MCP (stdio and HTTP transport).
Implements JSON-RPC 2.0 / MCP protocol directly — no external SDK dependency.
Compatible with Python 3.9+.

Tools:
    echelon_verify       — Full certificate + evidence bundle verification
    echelon_inspect      — Certificate summary (no verification)
    echelon_hash         — Canonical JSON hash (Echelon Canonical JSON v0)
    echelon_schema_check — Certificate schema validation
    echelon_replay       — Template/fixture structural consistency check
    echelon_status       — Construct verification state query
    echelon_calibrate    — Full calibration pipeline execution
"""

__version__ = "1.0.0"
```

### 3.6 `mcp/models/meta.py` — ENGINE_VERSION Bump

Update the `ENGINE_VERSION` constant at line 9:

```python
# Before:
ENGINE_VERSION = "0.8.0"

# After:
ENGINE_VERSION = "1.0.0"
```

This ensures the `_meta.engine_version` field in all tool responses reflects the v1.0.0 release. No other changes to this file.

---

## 4. Test Design

All new tests use `pytest`, matching the existing test style in `mcp/tests/`. Each test class follows the established patterns from `test_tools.py` and `test_server.py`.

### 4.1 `mcp/tests/test_status.py`

```python
"""Tests for mcp.tools.status — echelon_status tool."""
```

**Fixture helper**: Uses `tmp_path` (pytest built-in) to create temporary output directory structures. A helper function `_write_cert(tmp_path, construct_id, cert_dict)` writes a certificate JSON file at the expected path (`{tmp_path}/construct_calibration/{construct_id}/certificates/{template_id}.json`).

| Test | Description |
|------|-------------|
| `test_status_existing_construct` | Create a temp directory with one valid certificate JSON file at the expected path. Call `status.handle({"construct_id": "test_construct", "output_dir": str(tmp_path)})`. Assert: `certificates_found == 1`. Assert: `latest_certificate` contains correct `certificate_id`, `template_id`, `composite_score`, `verification_tier`, `issued_at`, `replay_count`. Assert: `tier_summary.current_tier` matches the certificate tier. Assert: `_meta` present. |
| `test_status_no_certificates` | Create the certificates directory but leave it empty. Call handle. Assert: `certificates_found == 0`, `latest_certificate is None`, `tier_summary is None`. |
| `test_status_missing_output_dir` | Call handle with an `output_dir` pointing to a non-existent path. Assert: `certificates_found == 0`. No error raised. Response contains `_meta`. |
| `test_status_corrupt_json_skipped` | Write one valid and one corrupt (non-JSON) `.json` file in the certificates directory. Assert: `certificates_found == 1` (corrupt file skipped). `latest_certificate` is from the valid file. |
| `test_status_missing_construct_id` | Call `status.handle({})`. Assert: `overall_verdict == "ERROR"`, `error_code == "INPUT_MALFORMED"`. |
| `test_status_multiple_certificates_returns_latest` | Write two certificate files with different `issued_at` timestamps (`2026-03-01T00:00:00` and `2026-03-02T00:00:00`). Assert: `certificates_found == 2`. `latest_certificate.issued_at` is the later timestamp. |
| `test_status_replays_needed_calculation` | Create a certificate with `replay_count: 12`. Assert: `tier_summary.replays_needed == 38` (50 - 12). Create another with `replay_count: 60`. Assert: `tier_summary.replays_needed == 0`. |
| `test_status_has_meta` | Assert `_meta` envelope is present with `engine_version` and `timestamp` fields. |

### 4.2 `mcp/tests/test_calibrate.py`

```python
"""Tests for mcp.tools.calibrate — echelon_calibrate tool."""
```

These tests run the actual calibration pipeline in deterministic fixture mode (~12 records, <1 second per test).

| Test | Description |
|------|-------------|
| `test_calibrate_known_construct` | Call `calibrate.handle({"construct_id": "community_oracle_v1", "output_dir": str(tmp_path)})`. Assert: response has `certificate` (dict), `pipeline_summary` (dict), `_meta` (dict). Assert: `pipeline_summary["construct_id"] == "community_oracle_v1"`. Assert: `pipeline_summary["composite_score"]` is a float. Assert: `certificate["certificate_id"]` is a non-empty string. |
| `test_calibrate_unknown_construct` | Call `calibrate.handle({"construct_id": "nonexistent_v99"})`. Assert: `overall_verdict == "ERROR"`, `error_code == "INPUT_MALFORMED"`. Assert: `"Available"` appears in `error_message`. |
| `test_calibrate_certificate_passes_verify` | Call calibrate to get a certificate, then call `verify.handle()` with the certificate wrapped in inline mode. Assert: verify result `overall_verdict` is not `"ERROR"`. Also assert: `pipeline_summary["mcp_verify_verdict"]` is present and is a string. |
| `test_calibrate_missing_construct_id` | Call `calibrate.handle({})`. Assert: `overall_verdict == "ERROR"`, `error_code == "INPUT_MALFORMED"`, `"construct_id"` in `error_message`. |
| `test_calibrate_deterministic` | Call calibrate twice with the same construct and two different `tmp_path` output dirs. Assert: both `certificate["composite_score"]` values are identical. Assert: both `certificate["certificate_id"]` values are identical (UUID5 is deterministic for the same construct key). |
| `test_calibrate_has_meta` | Assert `_meta` envelope is present in the response with `engine_version` and `timestamp`. |

### 4.3 `mcp/tests/test_http.py`

```python
"""Tests for mcp.http — HTTP transport."""
```

**Test server fixture**: A `pytest` fixture starts `MCPHttpHandler` on a random available port in a daemon thread, yields the base URL, then shuts down.

```python
@pytest.fixture(scope="module")
def http_server():
    """Start MCP HTTP server on a random port for testing."""
    from mcp.http import MCPHttpHandler
    from http.server import HTTPServer
    import threading

    server = HTTPServer(("127.0.0.1", 0), MCPHttpHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
```

Tests use `urllib.request` (stdlib) for HTTP requests — no external test dependencies.

| Test | Description |
|------|-------------|
| `test_health_endpoint` | `GET /health`. Assert: HTTP 200, response body parses to `{"status": "ok", "version": "1.0.0", "tools": 7}`. |
| `test_sse_stub` | `GET /sse`. Assert: HTTP 200, response body parses to `{"status": "not_implemented", "available_from": "v1.3"}`. |
| `test_mcp_endpoint_tools_list` | `POST /mcp` with body `{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}`. Assert: HTTP 200. Parse response JSON. Assert: `result["tools"]` has length 7. Assert: tool names include both `echelon_status` and `echelon_calibrate`. |
| `test_mcp_endpoint_tool_call` | `POST /mcp` with body calling `echelon_hash` with `{"content":{"mode":"inline","value":{"test":1}}}`. Assert: HTTP 200. Parse the inner text content. Assert: hash starts with `sha256:`. |
| `test_mcp_endpoint_malformed` | `POST /mcp` with body `"not json at all"`. Assert: HTTP 200 (JSON-RPC error is protocol-level). Parse response JSON. Assert: `error.code == -32700`. |
| `test_mcp_endpoint_notification` | `POST /mcp` with body `{"jsonrpc":"2.0","method":"notifications/initialized"}`. Assert: HTTP 204 (no body). |
| `test_unknown_get_path` | `GET /unknown`. Assert: HTTP 404. |
| `test_unknown_post_path` | `POST /unknown` with empty body. Assert: HTTP 404. |

### 4.4 `mcp/tests/test_server.py` — Updates

Two assertions in the existing `test_server.py` must be updated to account for the new tool count:

| Location | Change |
|----------|--------|
| `TestDispatch.test_tools_list` (line 60) | Change `assert len(tools) == 5` to `assert len(tools) == 7`. |
| `TestDispatch.test_tools_list` (lines 61-68) | Add `"echelon_status"` and `"echelon_calibrate"` to the expected names set. |

No other tests in `test_server.py` require changes. The dispatch logic is unchanged; only the tool registry has grown.

---

## 5. File Manifest

### New Files

| File | Description |
|------|-------------|
| `mcp/tools/status.py` | `echelon_status` tool — construct verification state query via certificate directory scanning |
| `mcp/tools/calibrate.py` | `echelon_calibrate` tool — full calibration pipeline execution bridging async runner to sync handle |
| `mcp/http.py` | HTTP transport — `MCPHttpHandler` class and `run_http()` function using stdlib `http.server` |
| `mcp/tests/test_status.py` | Tests for `echelon_status`: 8 tests covering existing certs, no certs, missing dir, corrupt JSON, multiple certs, replays needed |
| `mcp/tests/test_calibrate.py` | Tests for `echelon_calibrate`: 6 tests covering known construct, unknown construct, verify integration, determinism |
| `mcp/tests/test_http.py` | Tests for HTTP transport: 8 tests covering health, SSE stub, tools/list, tool call, malformed JSON, notification, unknown paths |

### Modified Files

| File | Change |
|------|--------|
| `mcp/__init__.py` | Version bump `0.8.0` -> `1.0.0`, updated docstring to list 7 tools and both transports |
| `mcp/server.py` | Import `status` and `calibrate` modules, add to `TOOLS` registry (2 entries), bump `serverInfo.version` to `1.0.0`, add `--http`/`--port` CLI handling, update module docstring |
| `mcp/models/meta.py` | `ENGINE_VERSION` constant: `"0.8.0"` -> `"1.0.0"` |
| `mcp/tests/test_server.py` | `test_tools_list`: expected tool count 5 -> 7, add new tool names to expected set |

### Unchanged Files

| File | Note |
|------|------|
| `mcp/tools/verify.py` | No modifications |
| `mcp/tools/inspect.py` | No modifications |
| `mcp/tools/hash.py` | No modifications |
| `mcp/tools/schema_check.py` | No modifications |
| `mcp/tools/replay.py` | No modifications |
| `mcp/models/errors.py` | No modifications — existing error codes (`INPUT_MALFORMED`, `INTERNAL_ERROR`) are sufficient |
| `mcp/models/inputs.py` | No modifications — new tools use plain string arguments, not mode-wrapped inputs |
| `scripts/run_construct_calibration.py` | No modifications — imported as-is by `calibrate.py` |

---

## 6. Constraints

### C-1: No New External Dependencies

HTTP server uses `http.server` and `http.server.HTTPServer` from the Python standard library. `echelon_calibrate` imports the existing `run_construct_calibration()` from `scripts/run_construct_calibration.py`. The `asyncio` module is stdlib. All imports are standard library or project-internal. No `requirements.txt` changes.

### C-2: Python 3.9+ Compatibility

- `asyncio.run()` is available from Python 3.7+.
- `Path.glob()` and `BaseHTTPRequestHandler` are stable across all 3.9+ releases.
- Type hints use `from __future__ import annotations` for forward-reference compatibility.
- Union types use `Optional[X]` (not `X | None`) for 3.9 compatibility.
- `dict` and `list` type hints in function signatures use `Dict` and `List` from `typing` (not lowercase `dict`/`list` which require 3.9+ without `__future__` annotations).

### C-3: Existing 5 Tools Unchanged

No modifications to `verify.py`, `inspect.py`, `hash.py`, `schema_check.py`, or `replay.py`. Their `TOOL_DEFINITION` dicts, `handle()` functions, and imports remain identical.

### C-4: SSE is Stub Only

`GET /sse` returns `{"status": "not_implemented", "available_from": "v1.3"}` with `Content-Type: application/json`. No `text/event-stream` content type. No event streaming. No subscription mechanism. Full SSE is deferred to v1.3.

### C-5: British Spelling in Documentation

The SDD and code comments use British English where applicable (e.g. "behaviour", "serialised", "standardised", "recognised"). Variable names, function names, and API field names remain American English for consistency with the existing codebase and JSON-RPC conventions.

### C-6: `_meta` Envelope on All New Tool Responses

Both `echelon_status` and `echelon_calibrate` include `build_meta()` in their return dicts, consistent with the existing five tools. The `_meta` envelope contains `engine_version`, `schema_versions`, and `timestamp`.

### C-7: Standardised Error Codes

New tools use the existing error codes defined in `mcp/models/errors.py`:
- `INPUT_MALFORMED` — missing required fields, unknown construct keys
- `INTERNAL_ERROR` — pipeline exceptions, async bridge failures

No new error codes are introduced.

### C-8: Determinism

`echelon_calibrate` inherits the fixed-epoch deterministic design from `run_construct_calibration()` (see `_FIXTURE_EPOCH` at `scripts/run_construct_calibration.py:46`). Given the same construct key, the pipeline produces identical `certificate_id` (UUID5), identical `composite_score`, identical `evidence_bundle_hash`, and identical `commitment_hash` across runs.

### C-9: Transport Isolation

The HTTP transport imports `dispatch()` from `server.py`, but `server.py` does not import from `http.py` at module level. The lazy import `from mcp.http import run_http` inside the `--http` CLI branch ensures the http module is only loaded when HTTP mode is explicitly requested. This prevents circular imports and unnecessary module loading for the default stdio mode.
