# Sprint Plan: MCP Auth & Transport Hardening + Baseline Drift Remediation

**Cycle**: 013-remediation (Gate C + Gate D)
**Sprints**: 1 (global: 28)
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` (v1.0)
**SDD**: `grimoires/loa/sdd.md` (v1.0)
**Depends on**: Cycle-013 (Agent Runtime) -- COMPLETED

---

## Cycle Overview

**Objective**: Five surgical fixes from codex baseline remediation audit. Two blocking MCP security/transport items (Gate C), three non-blocking baseline drift items (Gate D). Single sprint — all items are small enough to fit in one sprint.

**Team**: 1 AI engineer (Claude Code + Loa)

**Execution Order**: C1 → C2 → D1 → D2 → D3 → full test suite

**Regression Scope**:
```bash
python3 -m pytest --tb=short -q
```
Must remain >= 741 tests passing.

---

## Sprint 1 -- Gate C+D Remediation (Global: 28)

**Goal**: Secure the MCP server for public exposure, align HTTP transport to expected contract, clean up baseline drift.

**New Files**:
```
mcp/auth.py
mcp/tests/test_auth.py
```

**Modified Files**:
```
mcp/server.py
mcp/http.py
mcp/tests/test_http.py
backend/api/theatre_routes.py
backend/osint/sources.json
backend/osint/tests/test_registry_loader.py
grimoires/loa/context/echelon_platform_roadmap.md
grimoires/loa/context/README.md
```

---

### Task 1: C1 — MCP Auth Layer

**File**: `mcp/auth.py` (NEW), `mcp/server.py` (MODIFY)

**Acceptance Criteria**:
- [ ] `mcp/auth.py` exports `load_auth_config()`, `authenticate()`, `authorize()`, `check_rate_limit()`
- [ ] Bearer token validation: compares against configured token set from `MCP_AUTH_TOKENS` env var
- [ ] Scope enforcement: each tool in `TOOLS` registry declares `"scopes"` list
- [ ] `authorize()` checks token scopes against tool's required scopes
- [ ] Rate limiting: per-token sliding window, configurable RPM (default 60)
- [ ] Auth disabled when `MCP_AUTH_TOKENS` env var absent (dev mode)
- [ ] Missing token returns `{"error": "authentication_required", ...}`
- [ ] Wrong scope returns `{"error": "insufficient_scope", "required_scope": "...", ...}`
- [ ] Rate exceeded returns `{"error": "rate_limit_exceeded", "retry_after_seconds": N, ...}`

**Implementation Notes**:
- Add `"scopes": ["verify"]` (etc.) to each entry in `TOOLS` dict in `server.py`
- `load_auth_config()` reads `MCP_AUTH_TOKENS` env var as JSON, returns parsed config or None
- Rate limit uses `collections.deque` of timestamps per token name
- Stdio transport does NOT call auth functions

---

### Task 2: C1 — Auth Tests

**File**: `mcp/tests/test_auth.py` (NEW)

**Acceptance Criteria**:
- [ ] Test: valid token passes `authenticate()`
- [ ] Test: missing/empty auth header rejected
- [ ] Test: invalid token rejected
- [ ] Test: token with correct scope passes `authorize()`
- [ ] Test: token missing required scope rejected with scope name in error
- [ ] Test: rate limit allows requests under limit
- [ ] Test: rate limit rejects requests over limit
- [ ] Test: auth disabled when no config (dev mode passthrough)

---

### Task 3: C2 — Plain JSON HTTP Endpoints

**File**: `mcp/http.py` (MODIFY)

**Acceptance Criteria**:
- [ ] `POST /api/v1/tools/{tool_name}` route added
- [ ] Accepts plain JSON body (tool arguments directly, not wrapped in JSON-RPC)
- [ ] Returns plain JSON response (tool result directly, not wrapped in JSON-RPC)
- [ ] Auth enforced: `Authorization: Bearer <token>` header required
- [ ] Unknown tool name returns 404
- [ ] `POST /mcp` JSON-RPC endpoint unchanged and still works
- [ ] `/health` and `/sse` unchanged
- [ ] All existing `test_http.py` tests pass unchanged

---

### Task 4: C2 — Plain JSON Transport Tests

**File**: `mcp/tests/test_http.py` (MODIFY — add new test methods)

**Acceptance Criteria**:
- [ ] Test: `POST /api/v1/tools/echelon_hash` with plain JSON body returns valid hash result
- [ ] Test: `POST /api/v1/tools/echelon_status` returns valid status response
- [ ] Test: `POST /api/v1/tools/nonexistent` returns 404
- [ ] Test: missing auth header returns 401 (when auth enabled)
- [ ] All existing tests in `test_http.py` pass unchanged

---

### Task 5: D1 — Theatre Run Mock Fallback Honesty

**File**: `backend/api/theatre_routes.py` (MODIFY)

**Acceptance Criteria**:
- [ ] `run_theatre()` response includes `adapter_type` field
- [ ] `run_theatre()` response includes `local_mode` field
- [ ] When template has `adapter_type: "mock"` (or no adapter configured), response shows `"local_mode": true`
- [ ] When real adapter configured, response shows `"local_mode": false`
- [ ] Optional: `local_mode_note` field explains implications when `local_mode: true`
- [ ] Existing flow unchanged — `asyncio.create_task(run_theatre_task(...))` still called

---

### Task 6: D2 — Registry Scope Documentation

**Files**: `backend/osint/sources.json` (MODIFY), `backend/osint/tests/test_registry_loader.py` (MODIFY)

**Acceptance Criteria**:
- [ ] `sources.json` description field updated to document WM-only scope
- [ ] Reference to cycle-005 (160+ sources) and cycle-017 (planned expansion)
- [ ] `test_registry_loader.py` module docstring updated with scope explanation
- [ ] Existing tests pass unchanged

---

### Task 7: D3 — Planning Metadata Consistency Audit

**Files**: `grimoires/loa/context/echelon_platform_roadmap.md`, `grimoires/loa/ledger.json`, `grimoires/loa/context/README.md`

**Acceptance Criteria**:
- [ ] Roadmap test count updated from "513 passed" to current baseline (741+)
- [ ] Roadmap cycle-013 status accurate (3 sprints completed)
- [ ] Ledger cycle-013 entry consistent with roadmap
- [ ] README lists actual files in `grimoires/loa/context/` directory
- [ ] No contradictions between the three files
