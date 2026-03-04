# SDD: MCP Auth & Transport Hardening + Baseline Drift Remediation

**Cycle**: 013-remediation (Gate C + Gate D)
**Version**: 1.0
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` v1.0

---

## 1. Executive Summary

Five surgical fixes: two MCP security/transport hardening items (Gate C) and three baseline drift cleanups (Gate D). No new features, no architectural changes to existing systems.

**Key architectural decisions**:
1. **Auth as middleware, not dispatch modification** -- `mcp/auth.py` exports functions that wrap handlers. The `dispatch()` function in `server.py` is not modified. HTTP transport calls auth before dispatch. Stdio transport bypasses auth (local trust).
2. **Plain JSON endpoints as separate routes, not JSON-RPC replacement** -- `POST /api/v1/tools/{tool_name}` routes are added alongside `POST /mcp`. JSON-RPC is preserved for backward compatibility and MCP protocol compliance.
3. **In-memory rate limiting** -- `collections.defaultdict` with timestamp deques. No external store. Sufficient for single-process HTTP server.
4. **Tool scopes declared in TOOLS registry** -- Each tool entry gains a `"scopes"` key. Centralised, auditable, no scattered config.
5. **Theatre run response enhancement, not flow change** -- `run_theatre` adds fields to the 202 response. `theatre_bridge.py` is not modified.

---

## 2. System Architecture

### 2.1 MCP Auth Layer

```
HTTP Request
    │
    ▼
┌─────────────────────┐
│  MCPHttpHandler     │
│                     │
│  do_POST()          │
│    │                │
│    ├── /api/v1/tools/{name}  ──► authenticate() ──► authorize(scopes) ──► rate_limit()
│    │                                                      │
│    │                                                      ▼
│    │                                              TOOLS[name]["handler"](body)
│    │                                                      │
│    │                                                      ▼
│    │                                              Plain JSON response
│    │
│    ├── /mcp  ──► (optional auth) ──► dispatch()  ──► JSON-RPC response
│    │
│    ├── /health  ──► no auth  ──► health response
│    │
│    └── /sse     ──► no auth  ──► stub response
│
└─────────────────────┘
```

### 2.2 Auth Module (`mcp/auth.py`)

```python
# Configuration (loaded from env)
MCP_AUTH_TOKENS = {
    "token-abc123": {
        "name": "consumer-1",
        "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status"],
    },
    "token-admin456": {
        "name": "admin",
        "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status", "calibrate"],
    },
}

# Functions
def load_auth_config() -> dict
    """Load token config from MCP_AUTH_TOKENS env var (JSON) or default."""

def authenticate(auth_header: str | None) -> tuple[bool, str | dict]
    """Validate bearer token. Returns (success, token_info_or_error)."""

def authorize(token_info: dict, required_scopes: list[str]) -> tuple[bool, str | None]
    """Check token scopes against required scopes."""

def check_rate_limit(token_name: str, max_rpm: int = 60) -> tuple[bool, dict | None]
    """Sliding window rate limit check. Returns (allowed, error_or_none)."""
```

### 2.3 Tool Scope Declarations

Each tool in `TOOLS` gains a `"scopes"` key:

| Tool | Required Scope |
|------|---------------|
| echelon_verify | `verify` |
| echelon_inspect | `inspect` |
| echelon_hash | `hash` |
| echelon_schema_check | `schema_check` |
| echelon_replay | `replay` |
| echelon_status | `status` |
| echelon_calibrate | `calibrate` |

### 2.4 Plain JSON Endpoint Contract

**Request:**
```
POST /api/v1/tools/echelon_status
Authorization: Bearer token-abc123
Content-Type: application/json

{
    "construct_id": "community_oracle_v1",
    "output_dir": "output"
}
```

**Response (200):**
```json
{
    "construct_id": "community_oracle_v1",
    "certificates_found": 1,
    "latest_certificate": { ... },
    "tier_summary": { ... },
    "_meta": { ... }
}
```

**Error (401):**
```json
{
    "error": "authentication_required",
    "message": "Missing or invalid Authorization header. Expected: Bearer <token>"
}
```

**Error (403):**
```json
{
    "error": "insufficient_scope",
    "message": "Token lacks required scope: calibrate",
    "required_scope": "calibrate"
}
```

**Error (429):**
```json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Max 60 requests/minute.",
    "retry_after_seconds": 42
}
```

### 2.5 Theatre Run Response Enhancement

**Current response:**
```json
{
    "theatre_id": "...",
    "status": "accepted",
    "message": "Theatre execution started"
}
```

**Enhanced response:**
```json
{
    "theatre_id": "...",
    "status": "accepted",
    "message": "Theatre execution started",
    "adapter_type": "mock",
    "local_mode": true,
    "local_mode_note": "Mock adapter in use. Certificates will not be signed."
}
```

When a real adapter is configured:
```json
{
    "theatre_id": "...",
    "status": "accepted",
    "message": "Theatre execution started",
    "adapter_type": "oracle",
    "local_mode": false
}
```

---

## 3. Data Models

### 3.1 Auth Config (Environment Variable)

```
MCP_AUTH_TOKENS='{"tokens": [{"token": "abc123", "name": "consumer-1", "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status"]}, {"token": "admin456", "name": "admin", "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status", "calibrate"]}], "rate_limit_rpm": 60}'
```

When `MCP_AUTH_TOKENS` is not set, auth is disabled (development mode). This allows the existing test suite to pass without configuration changes.

### 3.2 Rate Limit State (In-Memory)

```python
_rate_limit_windows: Dict[str, deque[float]] = defaultdict(deque)
# Key: token name
# Value: deque of Unix timestamps of recent requests
# Cleanup: timestamps older than 60s removed on each check
```

---

## 4. File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `mcp/auth.py` | **NEW** | Auth module: bearer validation, scope check, rate limit |
| `mcp/server.py` | MODIFY | Add `"scopes"` to each tool in `TOOLS` registry |
| `mcp/http.py` | MODIFY | Add `/api/v1/tools/{name}` routes, wire auth |
| `mcp/tests/test_auth.py` | **NEW** | Auth unit tests |
| `mcp/tests/test_http.py` | MODIFY | Add plain JSON endpoint tests |
| `backend/api/theatre_routes.py` | MODIFY | Add adapter info to run response |
| `backend/osint/sources.json` | MODIFY | Add scope documentation to description field |
| `backend/osint/tests/test_registry_loader.py` | MODIFY | Add scope documentation docstring |
| `grimoires/loa/context/echelon_platform_roadmap.md` | MODIFY | Update test count, verify cycle status |
| `grimoires/loa/ledger.json` | VERIFY | Confirm consistency (likely no change needed) |
| `grimoires/loa/context/README.md` | MODIFY | List actual context files |

---

## 5. Security Considerations

- Tokens stored in environment variable, not committed to repo
- Auth disabled when env var absent (dev mode) -- acceptable for v1, explicit opt-in for production
- Rate limiting is per-token, not per-IP -- tokens are the identity boundary
- Stdio transport (local Claude Code) bypasses auth entirely -- stdio implies local trust
- No timing-safe token comparison in v1 (acceptable for bearer tokens, not passwords)

---

## 6. Backward Compatibility

- `POST /mcp` JSON-RPC endpoint unchanged -- all existing MCP clients continue to work
- Stdio transport unchanged -- Claude Code integration unaffected
- All existing tests pass without modification
- Auth disabled by default (no env var) means zero breaking changes for existing users
- New `/api/v1/tools/{name}` endpoints are additive

---

## 7. Dependencies

No new external dependencies. All implementations use Python stdlib:
- `collections.defaultdict`, `collections.deque` for rate limiting
- `time.time()` for timestamps
- `json` for config parsing
- `os.environ` for config loading
- `re` for URL path matching
