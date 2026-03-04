# PRD: MCP Auth & Transport Hardening + Baseline Drift Remediation

**Cycle**: 013-remediation (Gate C + Gate D)
**Version**: 1.0
**Date**: 2026-03-03
**Predecessor**: Cycle-013 (Agent Runtime — completed, defines current baseline)
**Source**: `grimoires/loa/context/codex_baseline_remediation_013.md` v2

---

## 1. Problem Statement

Cycle-013 completed the Agent Runtime (four-tier intelligence, 6 archetypes, ADK wrapper, autonomous E2E). The codebase baseline now stands at 741+ tests passing. However, the codex baseline remediation audit (v2) identifies two blocking gates and three non-blocking drift items that must be resolved before the MCP server can be exposed publicly and before the tracked baseline is clean for Cycle-014.

**Gate C** (blocking for public MCP exposure):
- C1: The MCP server dispatches tools with zero authentication, zero scope enforcement, and zero rate limiting. Any caller can invoke any tool.
- C2: The HTTP transport uses JSON-RPC via `POST /mcp`, but the expected public contract is plain JSON per-tool endpoints. External consumers will integrate against the wrong shape.

**Gate D** (non-blocking, baseline hygiene):
- D1: The `/theatres/{id}/run` endpoint silently falls back to mock adapter without indicating this to the caller.
- D2: The OSINT runtime registry is intentionally scoped to 3 WM sources, but this scoping decision is undocumented.
- D3: Planning metadata files have residual inconsistencies between roadmap, ledger, and context README.

> Sources: codex_baseline_remediation_013.md:62-88

---

## 2. Vision

After this remediation cycle, the MCP server has a security layer suitable for public exposure: bearer token validation, per-tool scope enforcement, and basic rate limiting. The HTTP transport exposes plain JSON endpoints that external consumers can integrate against directly. The codebase baseline is clean — no silent mock fallbacks, intentional scoping decisions are documented, and planning metadata is internally consistent.

This is a surgical remediation, not a feature cycle. No new capabilities are added. The existing 741+ test baseline must remain intact with new tests added for the security and transport layers.

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

1. **Bearer token validation** — MCP server rejects unauthenticated requests with clear error.
2. **Scope enforcement** — Each tool declares required scopes; auth layer rejects calls missing the required scope.
3. **Rate limiting** — Per-token, per-minute rate limiting prevents abuse.
4. **Plain JSON endpoints** — Public-facing HTTP endpoints accept plain JSON tool input (not JSON-RPC) per tool.
5. **JSON-RPC preservation** — Internal `POST /mcp` JSON-RPC endpoint continues to work for backward compatibility.
6. **Theatre run honesty** — `/theatres/{id}/run` response indicates mock execution when mock adapter is used.
7. **Registry scope documentation** — `sources.json` and test file document the intentional WM-only scoping.
8. **Metadata consistency** — Roadmap, ledger, and context README are internally consistent.

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| Existing test baseline | >= 741 tests passing |
| New auth tests | 4+ (valid token, missing token, wrong scope, rate limit exceeded) |
| New transport tests | 2+ (plain JSON endpoint hit, valid response) |
| JSON-RPC backward compatibility | All existing mcp/tests/* pass unchanged |
| Theatre run honesty | Response includes `local_mode` field when mock adapter used |
| Registry tests | Pass unchanged |
| Metadata files | 0 contradictions between roadmap, ledger, README |

### 3.3 Regression Baseline

Full test suite:
```bash
python3 -m pytest --tb=short -q
```

Must remain >= 741 tests passing.

---

## 4. Functional Requirements

### 4.1 C1 — MCP Auth Layer (`mcp/auth.py`)

New module implementing bearer token validation, scope enforcement, and rate limiting.

**Bearer Token Validation:**
- Tokens configured via environment variable or config (e.g., `MCP_AUTH_TOKENS`)
- Token format: plain bearer token string
- Validation: compare against configured token set
- Missing or invalid token returns structured error (not silent failure)

**Scope Enforcement:**
- Each tool in the registry declares its required scopes (e.g., `["verify"]`, `["calibrate"]`, `["admin"]`)
- Token-to-scope mapping configured alongside tokens
- Auth layer checks that the token's scopes include the tool's required scope
- Out-of-scope requests return clear error with required scope named

**Rate Limiting:**
- Per-token, per-minute sliding window
- Configurable limit (default: 60 requests/minute)
- Exceeded limit returns 429-equivalent structured error
- In-memory implementation (no external store needed for v1)

**Integration Point:** Auth layer wraps `handle_tools_call()` in `mcp/server.py`. The stdio transport (used for local Claude Code integration) bypasses auth by default. HTTP transport enforces auth.

> Sources: codex_baseline_remediation_013.md:64-67

### 4.2 C2 — Plain JSON HTTP Endpoints (`mcp/http.py`)

Add per-tool REST-style endpoints alongside the existing JSON-RPC endpoint.

**Endpoint Shape:**
- `POST /api/v1/tools/{tool_name}` — accepts plain JSON body (tool arguments), returns plain JSON response
- Maps directly to `TOOLS[tool_name]["handler"](arguments)`
- Auth enforced via `Authorization: Bearer <token>` header

**Existing Endpoint Preserved:**
- `POST /mcp` — JSON-RPC endpoint continues to work unchanged
- Auth optionally enforced on JSON-RPC endpoint (configurable)

**Tool Handler Compatibility:**
- `mcp/tools/status.py` and all other handlers already accept `Dict[str, Any]` arguments and return `Dict[str, Any]` — no handler changes needed
- The HTTP layer simply unwraps the plain JSON body and calls the handler directly

**Error Format:**
- Tool errors return the existing error_response format (overall_verdict, error_code, error_message)
- HTTP-level errors (auth, rate limit, not found) return standard JSON error objects

> Sources: codex_baseline_remediation_013.md:69-72

### 4.3 D1 — Theatre Run Mock Fallback Honesty

**File:** `backend/api/theatre_routes.py`

The `/theatres/{id}/run` endpoint currently returns `{"status": "accepted"}` regardless of whether the real or mock adapter executes. The `theatre_bridge.py` already correctly sets `local_mode=True` when using mock adapter (line 144-151) and refuses certificate signing for mock data (line 210-215).

**Fix:** The run endpoint response should include adapter information so the caller knows what will execute:
- Add `adapter_type` and `local_mode` fields to the response when available
- When mock adapter is the only option, the response should indicate `"adapter": "mock", "local_mode": true`

**Note:** This is a response shape enhancement, not a flow change. The existing `theatre_bridge.py` logic is correct — mock adapter → `local_mode=True` → certificate signing refused. The fix makes the API response honest about what will happen.

> Sources: codex_baseline_remediation_013.md:79-80

### 4.4 D2 — Registry Scope Documentation

**Files:** `backend/osint/sources.json`, `backend/osint/tests/test_registry_loader.py`

Add comments documenting the intentional scope:
- `sources.json`: Add description field explaining WM-only scope
- `test_registry_loader.py`: Add docstring explaining scope and referencing cycle-005 and cycle-017

No code changes. No test changes.

> Sources: codex_baseline_remediation_013.md:82-84

### 4.5 D3 — Planning Metadata Consistency

**Files:** `grimoires/loa/context/echelon_platform_roadmap.md`, `grimoires/loa/ledger.json`, `grimoires/loa/context/README.md`

Audit all three files and ensure:
1. Roadmap shows cycle-013 as active with correct sprint status (all 3 sprints completed)
2. `ledger.json` cycle-013 entry matches the roadmap
3. `README.md` accurately reflects the context directory contents

Current state from reading:
- **Roadmap**: Shows cycle-013 as active, test count says "513 passed" — needs update to current baseline
- **Ledger**: Shows cycle-013 as active with 3 sprints completed, global counter at 27 — looks correct
- **README**: Generic description of context directory — needs update to list actual files present

> Sources: codex_baseline_remediation_013.md:86-88

---

## 5. Testing Strategy

### 5.1 New Tests

| Area | Test File | Tests |
|------|-----------|-------|
| Auth validation | `mcp/tests/test_auth.py` | valid token, missing token, wrong scope, rate limit exceeded |
| Plain JSON transport | `mcp/tests/test_http.py` (extend) | plain JSON endpoint hit, valid response, auth enforcement |

### 5.2 Regression

All existing tests must pass. No modifications to existing test files except adding new test methods to `test_http.py`.

### 5.3 Theatre Run

D1 is a response shape change. Existing theatre tests don't test the run endpoint response shape directly (the endpoint is async/background). Verify manually or add a focused test if feasible.

---

## 6. Scope Exclusions

- No token persistence (in-memory only)
- No OAuth2/OIDC — plain bearer tokens
- No HTTPS/TLS configuration (deployment concern)
- No API key rotation mechanism
- No new MCP tools
- No theatre engine modifications
- No registry expansion

---

## 7. Execution Order

1. **C1** first — auth layer (C2 depends on stable server entry point)
2. **C2** second — transport alignment (builds on C1's auth layer)
3. **D1** — run endpoint honesty
4. **D2** — comment-only (fastest)
5. **D3** — metadata audit (no code changes)

After all five: run full test suite, verify >= 741 tests passing.

---

## 8. Acceptance Criteria

### Gate C (Blocking)

- [ ] `mcp/auth.py` exists with bearer token validation, scope enforcement, and rate limiting
- [ ] Each tool in `TOOLS` registry declares required scopes
- [ ] HTTP transport enforces auth on plain JSON endpoints
- [ ] `POST /api/v1/tools/{tool_name}` accepts plain JSON and returns plain JSON
- [ ] `POST /mcp` JSON-RPC endpoint continues to work unchanged
- [ ] Test: valid token passes auth
- [ ] Test: missing token rejected with clear error
- [ ] Test: wrong scope rejected with required scope named
- [ ] Test: rate limit exceeded rejected
- [ ] Test: plain JSON endpoint returns valid tool response
- [ ] All existing MCP tests pass unchanged

### Gate D (Non-Blocking)

- [ ] `/theatres/{id}/run` response includes `local_mode` indicator when mock adapter is used
- [ ] `sources.json` description field documents WM-only scope
- [ ] `test_registry_loader.py` docstring documents scope and references cycle-005/cycle-017
- [ ] Roadmap test count updated to current baseline
- [ ] Ledger cycle-013 entry consistent with roadmap
- [ ] README lists actual context directory files

### Baseline

- [ ] Full test suite >= 741 tests passing
- [ ] No regressions in existing tests
