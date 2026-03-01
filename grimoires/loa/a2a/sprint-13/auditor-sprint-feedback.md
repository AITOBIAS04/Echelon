# Sprint 2 (Global Sprint-13) — Security Audit

**Auditor**: Paranoid Cypherpunk Security Auditor
**Date**: 2026-03-01
**Verdict**: APPROVED

---

## Scope

8 files audited across the Loa Construct Calibration Pilot sprint:

| # | File | Verdict |
|---|------|---------|
| 1 | `theatre/scoring/construct_calibration_scorer.py` | CLEAN |
| 2 | `scripts/run_construct_calibration.py` | CLEAN |
| 3 | `theatre/fixtures/construct_calibration/templates/CONSTRUCT_CALIBRATION_V1.template.json` | CLEAN |
| 4 | `theatre/fixtures/construct_calibration/datasets/community_oracle_v1_fixtures.json` | CLEAN |
| 5 | `tests/theatre/test_construct_calibration.py` | CLEAN |
| 6 | `tests/test_mcp_integration.py` | CLEAN |
| 7 | `reports/construct_calibration_pilot.md` | CLEAN |
| 8 | `theatre/scoring/__init__.py` | CLEAN |

---

## Security Checklist Results

### Secrets
No hardcoded credentials, API keys, tokens, or passwords found in any file. All hash values present (evidence bundle hash, commitment hash, dataset hash) are content integrity hashes, not secrets.

### Input Validation
- Scorer: Unknown `criteria_id` returns 0.0. Empty annotations return 0.0. Missing `expected_output` returns 0.0. No division-by-zero possible (empty list guards precede all division).
- Runner CLI: `--construct` validated against `CONSTRUCTS` registry via argparse `choices`. `--output-dir` used as a `Path()` for file output only, not interpolated into shell commands.

### Path Traversal
- Template and dataset paths are hardcoded relative to `FIXTURE_BASE` (a constant derived from `__file__`).
- Output paths are constructed from the user-specified `--output-dir` plus internal constants. No user input is interpolated into file paths beyond the output directory root.
- All components of `shutil.rmtree()` target are programmatically constructed from constants.

### Data Privacy
- Fixture dataset contains only synthetic PR diffs with no real PII.
- No real usernames, email addresses, API keys, repository URLs, or internal paths exposed.
- Single public CVE reference (CVE-2023-32681) is publicly known information.

### Error Handling
- ImportError for MCP tools caught gracefully with "SKIPPED" message.
- Missing evidence bundle files produce logger warning (no stack trace exposure).
- No information disclosure in error paths.

### Dependencies
- No `eval`, `exec`, `subprocess`, `pickle`, or `os.system` in any sprint file.
- All imports are from standard library or project's own modules.
- No third-party library additions.

### File Operations
- `shutil.rmtree()` targets only the evidence bundle subdirectory (deterministic cleanup).
- All file writes use `Path.write_text()` with `json.dumps()` (safe serialization).
- `mkdir(parents=True, exist_ok=True)` for directory creation (safe).
- No race conditions (single-threaded pipeline).

### Cryptographic
- SHA-256 used for content integrity hashing (appropriate).
- `uuid.uuid5()` uses SHA-1 per UUID spec for deterministic ID generation (acceptable -- not a cryptographic security context).
- No weak algorithms. No custom crypto.

---

## Cross-Cutting Findings

### Positive Security Properties
1. **Fully deterministic pipeline**: Fixed epoch, deterministic UUIDs, cleanup-before-write. Eliminates timing leakage and ensures reproducibility.
2. **No network calls in scoring path**: Scorer and fixtures are fully offline. MCP verify is local-only and import-guarded.
3. **No shell command construction**: No subprocess/os.system/shell string interpolation.
4. **No deserialization of untrusted data**: All JSON from own fixtures or pipeline outputs.
5. **Tamper detection tested**: Integration test verifies that mutated certificates are caught by the verifier.

### Advisory Notes (Non-Blocking)
1. **`asyncio.get_event_loop()` deprecation**: Both test files use the deprecated pattern. No security impact. Future cleanup recommended (matches reviewer note #2).
2. **`import shutil` inside function body**: Minor style inconsistency. No security impact.
3. **`--construct-source` CLI arg accepted but unused**: Documented as "not used in fixture mode". No security impact since it's never processed.

---

## Decision

**APPROVED**. No security issues found. The sprint code is clean, defensive, and well-structured. The deterministic design is a security positive. All 8 files pass the full security checklist.
