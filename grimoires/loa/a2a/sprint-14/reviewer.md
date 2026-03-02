# Sprint 14 — Status + Calibrate Tools — Implementation Report

**Cycle**: 009
**Sprint**: 1 (global: 14)
**Date**: 2026-03-02

---

## Summary

Implemented two new MCP tools (`echelon_status`, `echelon_calibrate`) with full test coverage. Updated server registry to expose 7 tools. All 61 tests pass (14 new + 47 existing), zero regressions.

---

## Tasks Completed

### Task 1.1: `mcp/tools/status.py`

Created the `echelon_status` tool per SDD 3.1. Stateless file-system scanner that reads the certificate directory and reports construct verification state.

- `TOOL_DEFINITION` with `construct_id` (required) and `output_dir` (optional, default `"output"`)
- `handle()` scans `{output_dir}/construct_calibration/{construct_id}/certificates/*.json`
- Parses each JSON file, skips corrupt files with stderr warning
- Sorts by `issued_at`, selects latest certificate
- Computes `replays_needed` as `max(0, 50 - replay_count)`
- Returns `certificates_found: 0` with `None` fields when no certificates exist
- `_meta` envelope via `build_meta()`

**File**: `mcp/tools/status.py` (110 lines)

### Task 1.2: `mcp/tests/test_status.py`

8 tests covering all edge cases from SDD 4.1:

1. `test_status_existing_construct` — valid certificate, all fields correct
2. `test_status_no_certificates` — empty directory returns 0
3. `test_status_missing_output_dir` — non-existent path returns 0
4. `test_status_corrupt_json_skipped` — corrupt file skipped, valid file returned
5. `test_status_missing_construct_id` — returns INPUT_MALFORMED
6. `test_status_multiple_certificates_returns_latest` — two certs, latest by issued_at
7. `test_status_replays_needed_calculation` — 12 replays -> 38 needed; 60 -> 0 needed
8. `test_status_has_meta` — _meta envelope present with engine_version and timestamp

**File**: `mcp/tests/test_status.py` (170 lines)

### Task 1.3: `mcp/tools/calibrate.py`

Created the `echelon_calibrate` tool per SDD 3.2. Stateful tool that runs the full calibration pipeline via `asyncio.run()` bridge.

- `TOOL_DEFINITION` with `construct_id` (required) and `output_dir` (optional)
- Validates construct against `CONSTRUCTS` registry, returns available keys on error
- `asyncio.run()` bridge to call async `run_construct_calibration()`
- Runs `echelon_verify` against the produced certificate inline
- Returns `certificate` + `pipeline_summary` (with `mcp_verify_verdict`) + `_meta`
- `sys.path` setup matching the existing pattern in `verify.py`

**File**: `mcp/tools/calibrate.py` (96 lines)

### Task 1.4: `mcp/tests/test_calibrate.py`

6 tests per SDD 4.2:

1. `test_calibrate_known_construct` — runs pipeline, returns certificate + summary
2. `test_calibrate_unknown_construct` — INPUT_MALFORMED with Available list
3. `test_calibrate_certificate_passes_verify` — calibrate then verify integration
4. `test_calibrate_missing_construct_id` — returns INPUT_MALFORMED
5. `test_calibrate_deterministic` — two runs produce identical certificate_id and composite_score
6. `test_calibrate_has_meta` — _meta envelope present

**File**: `mcp/tests/test_calibrate.py` (91 lines)

### Task 1.5: `mcp/server.py` — Tool Registration

- Added `status, calibrate` to import line (line 23)
- Added `echelon_status` and `echelon_calibrate` to `TOOLS` dict

**File**: `mcp/server.py` (2 targeted edits)

### Task 1.6: `mcp/tests/test_server.py` — Tool Count

- Updated `test_tools_list`: expected count 5 -> 7
- Added `echelon_status` and `echelon_calibrate` to expected names set

**File**: `mcp/tests/test_server.py` (1 targeted edit)

### Task 1.7: Full Test Suite

```
61 passed in 0.12s
```

Breakdown:
- 8 new status tests — all pass
- 6 new calibrate tests — all pass
- 10 existing server tests — all pass (including updated tool count assertion)
- 17 existing tool tests — all pass unchanged
- 13 existing model tests — all pass unchanged
- 7 existing other tests — all pass unchanged

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `mcp/tools/status.py` | 110 | echelon_status tool |
| `mcp/tools/calibrate.py` | 96 | echelon_calibrate tool |
| `mcp/tests/test_status.py` | 170 | 8 status tests |
| `mcp/tests/test_calibrate.py` | 91 | 6 calibrate tests |

## Files Modified

| File | Change |
|------|--------|
| `mcp/server.py` | Import + register 2 new tools |
| `mcp/tests/test_server.py` | Tool count 5 -> 7, 2 new names in expected set |

## Files Unchanged

All 5 existing tool modules (`verify.py`, `inspect.py`, `hash.py`, `schema_check.py`, `replay.py`) and all model modules (`errors.py`, `meta.py`, `inputs.py`) are unchanged.

---

## Issues Encountered

None. Clean implementation — all patterns followed existing code conventions exactly.
