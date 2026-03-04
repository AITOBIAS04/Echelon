APPROVED - LETS FUCKING GO

# Sprint 12 (Cycle-008, Sprint 1) -- Security Audit: Verifier MCP Server v1.0

**Auditor**: Paranoid Cypherpunk Security Auditor
**Date**: 2026-03-01
**Branch**: `feature/cycle-008-mcp-server`
**Decision**: APPROVED (with 2 LOW findings, 3 INFO observations)

---

## Audit Methodology

Full source review of all 9 MCP module files + 3 test files + 1 entry point. Static analysis for: hardcoded secrets, command injection, arbitrary file access, path traversal, unsafe deserialization, information disclosure, dead code, DoS vectors. Test suite executed: 47/47 PASS in 0.03s.

### Files Audited

| File | Lines | Status |
|------|-------|--------|
| `mcp/server.py` | 252 | CLEAN |
| `mcp/models/meta.py` | 33 | CLEAN |
| `mcp/models/errors.py` | 41 | CLEAN |
| `mcp/models/inputs.py` | 41 | CLEAN |
| `mcp/tools/verify.py` | 135 | CLEAN (1 LOW finding) |
| `mcp/tools/inspect.py` | 88 | CLEAN |
| `mcp/tools/hash.py` | 78 | CLEAN |
| `mcp/tools/schema_check.py` | 77 | CLEAN |
| `mcp/tools/replay.py` | 118 | CLEAN |
| `mcp/__init__.py` | 16 | CLEAN |
| `mcp/__main__.py` | 6 | CLEAN |
| `mcp/models/__init__.py` | 1 | CLEAN |
| `mcp/tools/__init__.py` | 1 | CLEAN |

---

## Security Checklist

### 1. Hardcoded Secrets / Credentials -- PASS

Zero matches for: `password`, `secret`, `token`, `api_key`, `private_key`, `AWS_`, `OPENAI_`, `ANTHROPIC_`. No credential material in any MCP source file. Version strings (`0.8.0`) are the only "magic" constants, appropriately declared in `mcp/models/meta.py`.

### 2. Command Injection -- PASS

Zero use of: `subprocess`, `os.system`, `os.popen`, `exec()`, `eval()`, `__import__()`, `compile()`. No `os`, `shutil`, `glob`, or `fnmatch` imports. The only system interaction is `sys.stdin`/`sys.stdout` for JSON-RPC stdio transport. No shell command construction anywhere.

### 3. Arbitrary File Read/Write -- PASS

**Read surface**: `evidence_bundle_path` in `verify.py` accepts an arbitrary path, which flows to `load_json()` in `tools/echelon_verify.py`. This is a read-only operation bounded by Python's `open()` + `json.load()`. The MCP server is a local stdio process (not network-exposed), so the caller already has full filesystem access. See SEC-S12-001 for a hardening note.

**Write surface**: Only `replay.py` creates temp files via `tempfile.NamedTemporaryFile(delete=False)`. Temp files are created in the OS temp directory (`/var/folders/.../T/`) with OS-generated random names. No user-controlled path components in the temp file creation. The `finally` block guarantees cleanup (lines 96-100), including when the `except` block returns early -- Python `finally` blocks execute after `return`.

### 4. Input Validation -- PASS

`parse_input()` in `mcp/models/inputs.py` enforces:
- Type check: input must be `dict` (line 22-26)
- Mode check: `mode` field required (line 29-30)
- Mode whitelist: only `"inline"` accepted; `"id"` rejected with clear message (lines 32-36)
- Value check: `value` field required (line 38-39)

Every tool handler validates presence of required parameters before calling `parse_input()`. Non-dict certificate values are rejected after parsing. The mode whitelist (`SUPPORTED_MODES = {"inline"}`) uses a set for O(1) lookup and prevents future mode additions without explicit code changes.

### 5. Temp File Cleanup -- PASS

`replay.py` lines 78-100: Both `template_path` and `fixtures_path` are initialized to `None` before the `try` block (lines 78-79). The `finally` block uses `if template_path:` guards with `unlink(missing_ok=True)`. This correctly handles:
- Normal execution: both cleaned up
- Exception on first temp file creation: `template_path` is `None`, no cleanup needed
- Exception on second temp file creation: `template_path` cleaned up, `fixtures_path` is `None`
- Exception from `check_deterministic_replay()`: both cleaned up

The reviewer's F-2 finding has been proactively addressed -- the code already implements the recommended pattern.

### 6. Information Disclosure in Error Messages -- PASS (with note)

Error messages expose:
- `str(e)` for `ValueError` from `parse_input()` -- safe, these are validation messages we control
- `str(e)` for generic `Exception` in `server.py:132` and `server.py:171` -- could leak internal state

For a local stdio MCP server, this is acceptable. The caller is a local MCP client (e.g., Claude Code) running as the same user. Internal error details are useful for debugging. No stack traces are exposed -- only `str(e)`. No `traceback`, `print_exc`, or `repr()` calls found.

### 7. Unsafe Deserialization -- PASS

Zero use of: `pickle`, `marshal`, `shelve`, `yaml.load()`, `yaml.unsafe_load()`. All deserialization is via `json.loads()` / `json.load()` which is safe against arbitrary code execution. JSON parsing occurs in:
- `server.py:186` -- stdin line parsing
- `server.py:211` -- CLI argument parsing
- `tools/echelon_verify.py:169` -- evidence bundle file loading

### 8. Path Traversal -- PASS (with LOW finding)

See SEC-S12-001 below. The `evidence_bundle_path` parameter accepts arbitrary filesystem paths. The downstream verifier functions (`check_dataset_hash`, `check_evidence_bundle_hash`, etc.) traverse into subdirectories (`inputs/`, `policy/`) relative to the provided path. Path.exists() follows symlinks. For a local stdio server, this is acceptable -- the MCP client already has full filesystem access and is expected to provide valid paths.

### 9. sys.path Manipulation -- PASS

Four files (`verify.py`, `hash.py`, `schema_check.py`, `replay.py`) append the repo root to `sys.path` to import from `tools/echelon_verify.py`:

```python
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```

This is safe because:
- `Path(__file__).resolve()` canonicalizes the path (resolves symlinks)
- `.parents[2]` is deterministic based on the file's physical location
- The guard `if str(_ROOT) not in sys.path` prevents duplicate entries
- Prepending (index 0) means the repo root takes priority, which is the intended behavior
- No user-controlled input flows into the path construction

---

## Findings

### SEC-S12-001: No Path Canonicalization on evidence_bundle_path (LOW)

**File**: `mcp/tools/verify.py:91`
**Type**: Path traversal (theoretical)
**Severity**: LOW

```python
evidence_dir = Path(ebp)
if not evidence_dir.exists():
    return error_response(...)
```

The `evidence_bundle_path` argument is used as-is without `resolve()` or symlink checking. A caller could supply a path containing `../` sequences or symlinks pointing to sensitive directories. The downstream verifier reads JSON files from `inputs/` and `policy/` subdirectories.

**Mitigating factors**:
- MCP server runs over stdio -- the caller is a local process with the same filesystem permissions
- All operations are read-only (JSON parsing only)
- The parameter is documented as "Absolute path to the evidence bundle directory"
- No sensitive data is returned beyond hash comparisons and structural checks
- The MCP client (Claude Code, etc.) already has full filesystem access

**Recommendation**: Add `evidence_dir = Path(ebp).resolve()` and optionally validate it falls within the project root. Low priority given the threat model.

### SEC-S12-002: No Input Size Limits (LOW)

**File**: `mcp/server.py:180-196`
**Type**: Denial of service (theoretical)
**Severity**: LOW

The stdio transport reads lines from stdin without size limits:

```python
for line in sys.stdin:
    line = line.strip()
    message = json.loads(line)
```

A malicious client could send an extremely large JSON-RPC message to consume memory. Similarly, inline certificate/template/fixture values have no size bounds.

**Mitigating factors**:
- The server is a local stdio process -- the caller is a trusted MCP client
- Python's `json.loads()` handles large inputs gracefully (bounded by available memory)
- The server is stateless -- memory is freed after each request
- No persistent state accumulation across requests

**Recommendation**: Not actionable for v1.0. If the server ever gains network transport (SSE/HTTP), add input size limits. For stdio transport, the OS pipe buffer and client behavior provide natural bounds.

### SEC-S12-003: Exception Detail Passthrough in Internal Errors (INFO)

**File**: `mcp/server.py:132`, `mcp/server.py:171`
**Type**: Information disclosure
**Severity**: INFO

```python
"error_message": str(e),    # line 132, tool call exception
f"Internal error: {e}"       # line 171, dispatch exception
```

Internal exceptions are passed through to the client as error messages. Could include file paths, internal state, or Python traceback fragments depending on the exception type.

**Acceptable for**: Local stdio server where caller is a trusted MCP client running as the same OS user.
**Not acceptable for**: Network-exposed server. If the transport changes, replace with generic error messages and log details server-side.

### SEC-S12-004: Tool Name Reflected in Error Response (INFO)

**File**: `mcp/server.py:108`
**Type**: Input reflection
**Severity**: INFO

```python
f"Unknown tool: {tool_name}. Available: {', '.join(TOOLS.keys())}"
```

User-supplied `tool_name` is reflected in the error response. For a JSON-RPC stdio server this is standard practice. No injection risk since the output is JSON-serialized.

### SEC-S12-005: replay.py Temp Files Use Predictable Suffix (INFO)

**File**: `mcp/tools/replay.py:82,88`
**Type**: Temp file predictability
**Severity**: INFO

Temp files use `suffix=".json"` but `tempfile.NamedTemporaryFile` generates cryptographically random filenames (via `os.urandom()`). The suffix is not a security concern. The `delete=False` + manual cleanup in `finally` pattern is the correct approach when the file path needs to be passed to another function.

---

## Code Quality Assessment

### Dead Code / Debug Statements -- CLEAN

- No `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, or `DEBUG` markers in any MCP source file
- `print()` calls exist only in `server.py`'s CLI interface (lines 206-242) -- appropriate for CLI usage, not in the stdio transport path
- No commented-out code blocks
- No unused imports

### Error Handling -- ROBUST

- Every tool handler has a guard for missing required parameters
- `parse_input()` raises `ValueError` with descriptive messages caught at the tool level
- `server.py` `dispatch()` has a top-level `try/except` for unexpected handler errors
- `replay.py` has proper `try/except/finally` for temp file lifecycle
- JSON parse errors in stdio transport are caught and returned as JSON-RPC parse errors (-32700)
- Unknown methods return standard JSON-RPC method-not-found (-32601)

### Side Effects -- MINIMAL

- `inspect`, `hash`, `schema_check` are pure functions (no side effects)
- `verify` performs read-only filesystem access (only when `evidence_bundle_path` provided)
- `replay` creates and cleans up temp files (guaranteed cleanup via `finally`)
- `server.py` writes only to stdout/stderr

---

## Test Suite Results

```
47 passed in 0.03s

test_models.py  -- 14 tests (meta, errors, inputs)
test_tools.py   -- 23 tests (verify: 6, inspect: 4, hash: 6, schema_check: 4, replay: 3)
test_server.py  -- 10 tests (JSON-RPC helpers, dispatch, tool registry)
```

All 47 tests pass. Test coverage spans:
- Happy paths for all 5 tools
- Missing/malformed input rejection for all tools
- Mode validation (inline accepted, id rejected)
- Error code fallback (unknown code -> INTERNAL_ERROR)
- JSON-RPC protocol compliance (initialize, tools/list, tools/call, notifications)
- Tool registry integrity (all tools have definition + callable handler)

Note: Replay tool has only 3 tests (error cases), no happy-path test for consistent template+fixtures. Flagged by code review (F-1). Not a security concern.

---

## Verdict

The MCP server implementation is clean, well-structured, and security-appropriate for its threat model (local stdio server for MCP clients). No CRITICAL or HIGH findings. Two LOW findings are theoretical and mitigated by the local-only transport model. Three INFO observations are documented for future reference if the transport model changes.

No secrets, no injection vectors, no unsafe deserialization, no arbitrary writes, no network calls, no debug leaks. The attack surface is minimal: stdin JSON parsing + optional read-only filesystem access for evidence bundles.

**Status: AUDIT_APPROVED**
