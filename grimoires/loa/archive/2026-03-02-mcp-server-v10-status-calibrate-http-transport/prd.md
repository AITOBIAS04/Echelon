# PRD: MCP Server v1.0 — Status Tool, Calibrate Tool, HTTP Transport

**Cycle**: 009
**Version**: 1.0
**Date**: 2026-03-02

---

## 1. Problem Statement

The Echelon Verifier MCP Server (v0.8.0, shipped Cycle-008) exposes five stateless verification tools over stdio. This is sufficient for local CLI use but insufficient for two scenarios:

1. **Programmatic status queries**: Downstream systems (e.g. Hounfour) need to query the current verification state of a construct — what certificates exist, what tier they hold, when they expire — without parsing file system output.

2. **Remote calibration triggering**: Construct operators need to trigger a full calibration run and receive a certificate over a protocol boundary, not by invoking a Python script directly.

3. **Network accessibility**: The stdio transport requires the MCP server to run as a subprocess of the client. HTTP transport enables the server to run as a persistent process accessible over the network.

> Sources: echelon_cycle_008_context.md (lines 304-313, deferred tools), echelon_platform_roadmap.md (lines 52-58, tier routing), Cycle-008 close-out recommendation (i).

---

## 2. Goals & Success Metrics

| Goal | Metric |
|------|--------|
| `echelon_status` returns construct verification state | Given a construct ID, returns current tier, certificate ID, composite score, expiry, and certificate count |
| `echelon_calibrate` runs full pipeline | Given a construct key, runs calibration end-to-end and returns the certificate dict |
| HTTP transport serves all 7 tools | `curl http://localhost:PORT/mcp` with JSON-RPC body receives valid response |
| SSE endpoint returns stub | `GET /sse` returns `{"status": "not_implemented", "available_from": "v1.3"}` |
| Existing stdio transport unchanged | All 17 existing MCP tests pass without modification |
| Server version bumped to 1.0.0 | `__version__` and serverInfo reflect v1.0.0 |

---

## 3. User & Stakeholder Context

**Primary**: Soju / Constructs Network — needs programmatic access to verification state for routing decisions.

**Secondary**: Construct operators — need to trigger calibration and retrieve certificates without running scripts manually.

**Constraint from user**: SSE is a stub only this cycle. The SSE endpoint returns a not-implemented response. Full SSE push subscriptions are deferred to v1.3.

---

## 4. Functional Requirements

### 4.1 `echelon_status` Tool

A stateless tool that reads the output directory to report construct verification state.

**Input**:
```json
{
  "construct_id": "community_oracle_v1",
  "output_dir": "output"
}
```

`output_dir` is optional (defaults to `"output"`).

**Output**:
```json
{
  "construct_id": "community_oracle_v1",
  "certificates_found": 1,
  "latest_certificate": {
    "certificate_id": "a64c7236-...",
    "template_id": "CONSTRUCT_CALIBRATION_V1",
    "composite_score": 0.6967,
    "verification_tier": "UNVERIFIED",
    "issued_at": "2026-03-01T00:00:00",
    "replay_count": 12
  },
  "tier_summary": {
    "current_tier": "UNVERIFIED",
    "backtested_threshold": 50,
    "current_replays": 12,
    "replays_needed": 38
  },
  "_meta": { ... }
}
```

If no certificates found, returns `certificates_found: 0` with `latest_certificate: null`.

**Implementation**: Scan `{output_dir}/construct_calibration/{construct_id}/certificates/` for JSON files, parse them, return the most recent by `issued_at`.

### 4.2 `echelon_calibrate` Tool

A stateful tool that runs the full construct calibration pipeline and returns the certificate.

**Input**:
```json
{
  "construct_id": "community_oracle_v1",
  "output_dir": "output"
}
```

`output_dir` is optional (defaults to `"output"`).

**Output**: The full certificate dict (same structure as `echelon_verify` input), plus `_meta` envelope and a `pipeline_summary` block:

```json
{
  "certificate": { ... },
  "pipeline_summary": {
    "construct_id": "community_oracle_v1",
    "template_id": "CONSTRUCT_CALIBRATION_V1",
    "composite_score": 0.6967,
    "scores": { "precision": 0.8000, "recall": 0.5417, "reply_accuracy": 0.8000 },
    "verification_tier": "UNVERIFIED",
    "evidence_bundle_hash": "cabd...",
    "mcp_verify_verdict": "PASS"
  },
  "_meta": { ... }
}
```

**Implementation**: Import and call `run_construct_calibration()` from `scripts/run_construct_calibration.py`. The existing runner already returns the certificate dict.

**Error handling**: If the construct key is unknown, return `error_code: INPUT_MALFORMED` with the list of known constructs. If the pipeline fails, return `error_code: INTERNAL_ERROR` with the exception message.

### 4.3 HTTP Transport

Add an HTTP server that accepts JSON-RPC 2.0 POST requests at `/mcp` and dispatches them through the same `dispatch()` function used by stdio.

**Endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/mcp` | JSON-RPC 2.0 dispatch (same as stdio) |
| GET | `/health` | Returns `{"status": "ok", "version": "1.0.0", "tools": 7}` |
| GET | `/sse` | Returns `{"status": "not_implemented", "available_from": "v1.3"}` |

**Server**: Use Python's built-in `http.server` module (no external dependencies). Single-threaded is acceptable for v1.0.

**CLI**:
```bash
python3 -m mcp.server                    # stdio (default, unchanged)
python3 -m mcp.server --http             # HTTP on port 3100
python3 -m mcp.server --http --port 8080 # HTTP on custom port
python3 -m mcp.server --list-tools       # unchanged
python3 -m mcp.server --call <tool> '{}'  # unchanged
```

**CORS**: Not required for v1.0 (server-to-server use case).

### 4.4 Version Bump

- `mcp/__init__.py`: `__version__ = "1.0.0"`
- `handle_initialize()`: `serverInfo.version = "1.0.0"`
- Tool count in `/health` response: `7`

---

## 5. Technical & Non-Functional Requirements

- **No new external dependencies**. HTTP server uses `http.server` from stdlib. `echelon_calibrate` imports the existing runner.
- **Python 3.9+ compatibility** maintained.
- **Existing tool handlers unchanged**. The 5 v0.8.0 tools must not be modified.
- **`_meta` envelope** on all new tool responses (consistent with existing tools).
- **Determinism**: `echelon_calibrate` produces deterministic output (inherits from the runner's fixed-epoch design).
- **Error codes**: Use existing standardised codes (`INPUT_MALFORMED`, `INTERNAL_ERROR`).

---

## 6. Scope & Prioritisation

### In scope

- `echelon_status` tool (file-based, stateless)
- `echelon_calibrate` tool (runs pipeline, stateful)
- HTTP transport at `/mcp` (POST, JSON-RPC 2.0)
- `/health` endpoint
- `/sse` stub endpoint
- Version bump to 1.0.0
- Tests for new tools and HTTP transport

### Out of scope

- Full SSE push subscriptions (v1.3)
- CORS headers
- Authentication or rate limiting
- Docker/serverless deployment configuration
- Frontend or dashboard
- New constructs or templates
- Registry expansion

---

## 7. Risks & Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| `echelon_calibrate` import path coupling | LOW | Runner already exports `run_construct_calibration()` as a callable function |
| HTTP server blocking during calibration | LOW | Single-threaded is acceptable for v1.0; calibration takes <1 second for 12 records |
| `http.server` not production-grade | LOW | Explicitly out of scope — this is a dev/integration server, not a production deployment |
| Construct registry currently hardcoded in runner | LOW | `echelon_calibrate` validates against the registry and returns available constructs on error |

---

## 8. Acceptance Criteria

1. `echelon_status` returns correct tier and certificate data for `community_oracle_v1`
2. `echelon_status` returns `certificates_found: 0` for an unknown construct
3. `echelon_calibrate` runs the full pipeline and returns a certificate that passes `echelon_verify`
4. `echelon_calibrate` returns `INPUT_MALFORMED` for unknown construct keys
5. HTTP server responds to `POST /mcp` with valid JSON-RPC responses
6. HTTP server responds to `GET /health` with status, version, and tool count
7. HTTP server responds to `GET /sse` with not-implemented stub
8. `tools/list` returns 7 tools (5 existing + 2 new)
9. All existing 17 MCP tests pass unchanged
10. All existing 23 theatre/integration tests pass unchanged
11. Server version is 1.0.0 in `__init__.py`, `handle_initialize()`, and `/health`
