# Sprint Plan: MCP Server v1.0 — Status Tool, Calibrate Tool, HTTP Transport

**Cycle**: 009
**PRD**: `grimoires/loa/prd.md`
**SDD**: `grimoires/loa/sdd.md`
**Date**: 2026-03-02

---

## Sprint Overview

Two sprints. Sprint 1 delivers the two new tools (`echelon_status`, `echelon_calibrate`) with their tests and the server registry update. Sprint 2 delivers the HTTP transport, version bump to 1.0.0, and full acceptance criteria validation.

**Team**: Single developer (AI agent)
**Approach**: Implement, test, commit per sprint. Each sprint is independently shippable.

---

## Sprint 1 — Status + Calibrate Tools

**Goal**: Add `echelon_status` and `echelon_calibrate` tools to the MCP server. Server exposes 7 tools. All existing tests pass unchanged.

### Task 1.1: Create `mcp/tools/status.py`

Implement `echelon_status` tool per SDD 3.1.

- `TOOL_DEFINITION` dict with `construct_id` (required) and `output_dir` (optional, default `"output"`)
- `handle()` function: scan certificate directory, parse JSON files, return latest certificate + tier summary
- Edge cases: missing directory (return `certificates_found: 0`), corrupt JSON (skip + warn), missing `issued_at` (sort to earliest), empty `construct_id` (return `INPUT_MALFORMED`)
- `_meta` envelope via `build_meta()`

**Acceptance**:
- [ ] `status.handle({"construct_id": "community_oracle_v1", "output_dir": "output"})` returns correct certificate data when certificates exist
- [ ] Returns `certificates_found: 0` when no certificates directory exists
- [ ] Returns `INPUT_MALFORMED` for missing `construct_id`

### Task 1.2: Create `mcp/tests/test_status.py`

8 tests per SDD 4.1.

- `test_status_existing_construct` — valid certificate, all fields correct
- `test_status_no_certificates` — empty directory
- `test_status_missing_output_dir` — non-existent path
- `test_status_corrupt_json_skipped` — one valid + one corrupt
- `test_status_missing_construct_id` — `{}` input
- `test_status_multiple_certificates_returns_latest` — two certs, latest by `issued_at`
- `test_status_replays_needed_calculation` — 12 replays -> 38 needed; 60 replays -> 0 needed
- `test_status_has_meta` — `_meta` envelope present

**Acceptance**:
- [ ] All 8 tests pass with `pytest mcp/tests/test_status.py -v`

### Task 1.3: Create `mcp/tools/calibrate.py`

Implement `echelon_calibrate` tool per SDD 3.2.

- `TOOL_DEFINITION` dict with `construct_id` (required) and `output_dir` (optional)
- `handle()` function: validate construct against `CONSTRUCTS` registry, bridge async via `asyncio.run()`, build `pipeline_summary`, run `echelon_verify` against certificate
- Return: `certificate` dict + `pipeline_summary` + `_meta`
- Error handling: `INPUT_MALFORMED` for unknown construct, `INTERNAL_ERROR` for pipeline exceptions
- `sys.path` setup for runner import (same pattern as `verify.py`)

**Acceptance**:
- [ ] `calibrate.handle({"construct_id": "community_oracle_v1"})` returns certificate + pipeline_summary
- [ ] `pipeline_summary` includes `mcp_verify_verdict`
- [ ] Unknown construct returns `INPUT_MALFORMED` with available constructs list

### Task 1.4: Create `mcp/tests/test_calibrate.py`

6 tests per SDD 4.2.

- `test_calibrate_known_construct` — runs pipeline, returns certificate + summary
- `test_calibrate_unknown_construct` — `INPUT_MALFORMED` error
- `test_calibrate_certificate_passes_verify` — calibrate then verify integration
- `test_calibrate_missing_construct_id` — `{}` input
- `test_calibrate_deterministic` — two runs produce identical output
- `test_calibrate_has_meta` — `_meta` envelope present

**Acceptance**:
- [ ] All 6 tests pass with `pytest mcp/tests/test_calibrate.py -v`

### Task 1.5: Update `mcp/server.py` — Tool Registration

Per SDD 3.4.1 and 3.4.2.

- Add `status, calibrate` to the import line
- Add `echelon_status` and `echelon_calibrate` entries to the `TOOLS` dict

**Acceptance**:
- [ ] `--list-tools` returns 7 tools
- [ ] `tools/list` JSON-RPC method returns 7 tool definitions

### Task 1.6: Update `mcp/tests/test_server.py` — Tool Count

Per SDD 4.4.

- Update `test_tools_list`: expected count 5 -> 7
- Add `echelon_status` and `echelon_calibrate` to expected names set

**Acceptance**:
- [ ] `pytest mcp/tests/test_server.py -v` — all existing tests pass
- [ ] Tool count assertion is 7

### Task 1.7: Run Full Test Suite

Run all MCP tests and verify no regressions.

**Acceptance**:
- [ ] All 17 existing tests pass unchanged
- [ ] All 14 new tests (8 status + 6 calibrate) pass
- [ ] Total: 31 tests passing

---

## Sprint 2 — HTTP Transport + Version Bump

**Goal**: Add HTTP transport at `/mcp`, `/health`, `/sse` stub. Bump version to 1.0.0 across all three locations. All 11 PRD acceptance criteria met.

### Task 2.1: Create `mcp/http.py`

Implement HTTP transport per SDD 3.3.

- `MCPHttpHandler(BaseHTTPRequestHandler)`:
  - `do_POST`: route `/mcp` to `dispatch()`, 404 for others
  - `do_GET`: `/health` -> status/version/tools, `/sse` -> stub, 404 for others
  - `_send_json` helper for consistent JSON responses
  - JSON-RPC parse errors sent as HTTP 200 with JSON-RPC error body
  - Notifications get HTTP 204
- `run_http(port=3100)`: start `HTTPServer` on given port
- Import `dispatch` and `jsonrpc_error` from `mcp.server`
- No CORS, no auth, single-threaded

**Acceptance**:
- [ ] `POST /mcp` dispatches JSON-RPC requests
- [ ] `GET /health` returns `{"status": "ok", "version": "1.0.0", "tools": 7}`
- [ ] `GET /sse` returns `{"status": "not_implemented", "available_from": "v1.3"}`
- [ ] Unknown paths return 404

### Task 2.2: Create `mcp/tests/test_http.py`

8 tests per SDD 4.3.

- `test_health_endpoint` — GET /health, verify JSON body
- `test_sse_stub` — GET /sse, verify stub response
- `test_mcp_endpoint_tools_list` — POST /mcp with tools/list, verify 7 tools
- `test_mcp_endpoint_tool_call` — POST /mcp with echelon_hash call
- `test_mcp_endpoint_malformed` — POST /mcp with invalid JSON, verify JSON-RPC error
- `test_mcp_endpoint_notification` — POST /mcp with notification, verify 204
- `test_unknown_get_path` — GET /unknown, verify 404
- `test_unknown_post_path` — POST /unknown, verify 404

Uses module-scoped fixture with `HTTPServer` on random port + daemon thread.

**Acceptance**:
- [ ] All 8 tests pass with `pytest mcp/tests/test_http.py -v`

### Task 2.3: Update `mcp/server.py` — HTTP CLI + Docstring

Per SDD 3.4.4 and 3.4.5.

- Add `--http` and `--port` CLI argument handling in `main()`
- Lazy import: `from mcp.http import run_http` inside the `--http` branch only
- Update module docstring to reflect both transports and 7 tools

**Acceptance**:
- [ ] `python3 -m mcp.server --http` starts HTTP server on port 3100
- [ ] `python3 -m mcp.server --http --port 8080` uses custom port
- [ ] Default stdio mode unchanged

### Task 2.4: Version Bump to 1.0.0

Per SDD 3.4.3, 3.5, 3.6.

- `mcp/__init__.py`: `__version__ = "1.0.0"`, updated docstring listing 7 tools
- `mcp/models/meta.py`: `ENGINE_VERSION = "1.0.0"`
- `mcp/server.py`: `serverInfo.version = "1.0.0"` (in `handle_initialize()`)

**Acceptance**:
- [ ] `python3 -c "from mcp import __version__; print(__version__)"` outputs `1.0.0`
- [ ] `_meta.engine_version` in tool responses is `"1.0.0"`
- [ ] `handle_initialize()` returns `serverInfo.version: "1.0.0"`

### Task 2.5: Full Test Suite + Acceptance Criteria

Run complete test suite. Validate all 11 PRD acceptance criteria.

**Acceptance**:
- [ ] All 17 existing MCP tests pass unchanged
- [ ] All 22 new tests pass (8 status + 6 calibrate + 8 HTTP)
- [ ] Total: 39 tests passing
- [ ] PRD AC-1: `echelon_status` returns correct tier and certificate data
- [ ] PRD AC-2: `echelon_status` returns `certificates_found: 0` for unknown construct
- [ ] PRD AC-3: `echelon_calibrate` runs pipeline and returns certificate that passes `echelon_verify`
- [ ] PRD AC-4: `echelon_calibrate` returns `INPUT_MALFORMED` for unknown construct keys
- [ ] PRD AC-5: HTTP server responds to `POST /mcp` with valid JSON-RPC
- [ ] PRD AC-6: HTTP server responds to `GET /health` with status, version, tool count
- [ ] PRD AC-7: HTTP server responds to `GET /sse` with stub
- [ ] PRD AC-8: `tools/list` returns 7 tools
- [ ] PRD AC-9: All existing 17 MCP tests pass unchanged
- [ ] PRD AC-10: All existing theatre/integration tests pass unchanged
- [ ] PRD AC-11: Server version is 1.0.0 in all three locations

---

## File Manifest

### New Files (6)

| File | Sprint | Description |
|------|--------|-------------|
| `mcp/tools/status.py` | 1 | `echelon_status` tool |
| `mcp/tests/test_status.py` | 1 | 8 status tool tests |
| `mcp/tools/calibrate.py` | 1 | `echelon_calibrate` tool |
| `mcp/tests/test_calibrate.py` | 1 | 6 calibrate tool tests |
| `mcp/http.py` | 2 | HTTP transport |
| `mcp/tests/test_http.py` | 2 | 8 HTTP transport tests |

### Modified Files (4)

| File | Sprint | Change |
|------|--------|--------|
| `mcp/server.py` | 1+2 | Sprint 1: import + register tools. Sprint 2: --http CLI + docstring + version |
| `mcp/tests/test_server.py` | 1 | Tool count 5 -> 7 |
| `mcp/__init__.py` | 2 | Version 0.8.0 -> 1.0.0, docstring |
| `mcp/models/meta.py` | 2 | ENGINE_VERSION 0.8.0 -> 1.0.0 |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| `asyncio.run()` in calibrate tool | LOW | No pre-existing event loop in either transport. Single-threaded. |
| HTTP server blocking during calibration | LOW | Calibration <1s for 12 fixture records. Single-threaded acceptable for v1.0. |
| `http.server` not production-grade | LOW | Out of scope — dev/integration server only. |
| Lazy import circular dependency | LOW | `mcp/http.py` imports from `mcp/server.py`; reverse is lazy (inside CLI branch). |
