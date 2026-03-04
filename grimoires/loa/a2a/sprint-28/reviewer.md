# Implementation Report — Sprint 28 (Gate C+D Remediation)

**Cycle**: 013-remediation
**Sprint**: 1 (Global: 28)
**Date**: 2026-03-03

---

## Summary

All 7 tasks completed. Two new files created, 8 files modified, 3 metadata files updated. 33 new tests added, all passing. No regressions.

## Changes by Gate

### Gate C — MCP Auth & Transport Hardening

#### C1 — Auth Layer

**New file: `mcp/auth.py`**
- Bearer token validation via `authenticate()` — parses `Authorization: Bearer <token>` header
- Scope enforcement via `authorize()` — checks token scopes against tool's required scopes
- Rate limiting via `check_rate_limit()` — per-token sliding window (60 RPM default)
- Config loaded from `MCP_AUTH_TOKENS` environment variable (JSON)
- Dev mode: auth disabled when env var absent (all existing tests pass without config)
- `reset_auth_config()` for test isolation

**Modified: `mcp/server.py`**
- Added `"scopes"` key to each tool in `TOOLS` registry
- Scopes: `verify`, `inspect`, `hash`, `schema_check`, `replay`, `status`, `calibrate`

**New file: `mcp/tests/test_auth.py`** (23 tests)
- `TestAuthenticate`: valid token, admin token, missing header, empty header, invalid token, malformed header, no bearer prefix, dev mode passthrough, dev mode any header
- `TestAuthorize`: correct scope, multiple scopes, missing scope (with scope name in error), admin calibrate scope, dev mode allows all
- `TestRateLimit`: under limit, over limit, independent per-token, dev mode no limit, window expiry
- `TestLoadConfig`: no env returns None, valid env parsed, invalid JSON returns None, config cached

#### C2 — Plain JSON HTTP Endpoints

**Modified: `mcp/http.py`**
- Added `POST /api/v1/tools/{tool_name}` route matching via regex
- Plain JSON request body -> tool handler -> plain JSON response (no JSON-RPC wrapping)
- Auth enforced: authenticate -> authorize -> rate_limit -> handler
- `POST /mcp` JSON-RPC endpoint preserved unchanged
- `/health` and `/sse` unchanged

**Modified: `mcp/tests/test_http.py`** (10 new tests, 8 existing unchanged)
- `TestPlainJsonEndpoints`: hash tool, status tool, unknown tool 404, schema_check, empty body, JSON-RPC still works alongside
- `TestAuthEnforcement`: valid token passes, missing token 401, wrong scope 403 (with scope name), invalid token 401

### Gate D — Baseline Drift

#### D1 — Theatre Run Mock Fallback Honesty

**Modified: `backend/api/theatre_routes.py`**
- `run_theatre()` response now includes `adapter_type`, `local_mode` fields
- When mock adapter: `"local_mode": true, "local_mode_note": "Mock adapter in use. Certificates will not be signed."`
- Reads adapter_type from template's `product_theatre_config`
- No flow changes

#### D2 — Registry Scope Documentation

**Modified: `backend/osint/sources.json`**
- Description updated to document WM-only scope with references to Cycle-005 and Cycle-017

**Modified: `backend/osint/tests/test_registry_loader.py`**
- Module docstring updated with scope explanation

#### D3 — Planning Metadata Consistency

**Modified: `grimoires/loa/context/echelon_platform_roadmap.md`**
- Test count updated from "513 passed" to "710 passed"

**Modified: `grimoires/loa/ledger.json`**
- Cycle-013: archived, Cycle-013-remediation: active, global counter: 28

**Modified: `grimoires/loa/context/README.md`**
- Now lists all 9 actual context files with purpose descriptions

## Test Results

| Suite | Passed | Failed | New |
|-------|--------|--------|-----|
| mcp/tests/test_auth.py | 23 | 0 | 23 |
| mcp/tests/test_http.py | 18 | 0 | 10 |
| mcp/ total | 102 | 0 | 33 |
| Scoped regression | 710 | 13 (pre-existing) | 33 |

All 13 failures are pre-existing OSINT wiring tests (Cycle-011) -- not introduced by this sprint.

## Files Changed

| File | Type |
|------|------|
| `mcp/auth.py` | NEW |
| `mcp/tests/test_auth.py` | NEW |
| `mcp/server.py` | MODIFIED (scopes) |
| `mcp/http.py` | MODIFIED (plain JSON routes + auth) |
| `mcp/tests/test_http.py` | MODIFIED (new test classes) |
| `backend/api/theatre_routes.py` | MODIFIED (response fields) |
| `backend/osint/sources.json` | MODIFIED (description) |
| `backend/osint/tests/test_registry_loader.py` | MODIFIED (docstring) |
| `grimoires/loa/context/echelon_platform_roadmap.md` | MODIFIED (test count) |
| `grimoires/loa/ledger.json` | MODIFIED (cycle status) |
| `grimoires/loa/context/README.md` | MODIFIED (file listing) |
