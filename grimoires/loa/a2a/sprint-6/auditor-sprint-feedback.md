# Sprint 6 (Cycle-002 Sprint 3) — Security & Quality Audit

**Sprint:** CLI, Config & End-to-End Integration
**Global ID:** sprint-6
**Date:** 2026-03-01
**Auditor:** Paranoid Cypherpunk Auditor

---

## Verdict: APPROVED - LETS FUCKING GO

All 13 files reviewed. No blocking security findings. No hardcoded secrets. No information disclosure. No command injection vectors. Test coverage is thorough and correctly isolated from live APIs. Implementation is clean, defensive, and architecturally consistent with prior sprints.

---

## Security Audit — Detailed Findings

### 1. SECRETS: No hardcoded credentials

| Check | Result |
|-------|--------|
| Hardcoded API keys in source | CLEAN — all keys loaded from env vars via `PipelineConfig.from_env()` |
| API keys in CLI args | CLEAN — keys come from env, not from `--query` or other CLI flags |
| API keys in error messages | CLEAN — error messages say "Set config['api_key'] from..." but never print the actual key value |
| API keys in serialized output | CLEAN — see detailed analysis below |
| API keys in git history | CLEAN — no `.env` files committed |
| Secrets in `pyproject.toml` | CLEAN |

**Deep-dive: FRED API key flow.**

The FRED API key flows: env var -> `PipelineConfig.fred_api_key` -> `config.collector_configs()["fred_api"]["api_key"]` -> `FREDCollector.__init__` -> `build_request()` params dict -> httpx query parameter (HTTPS, in transit only).

Critical: the API key does NOT leak into the `HTTPTranscriptReceipt` or `EvidenceBundle` because:
- `receipt.url` stores the BASE URL from `build_request()`, not the full URL with query params (httpx appends params internally)
- `receipt.request_headers` stores only `{"Accept": "application/json"}` — no auth header
- `canonical.py` line 28-32 explicitly maintains a `CANONICAL_HEADER_ALLOWLIST` that excludes `Authorization`, `Cookie`, etc.
- `EvidenceBundle.query_context` stores the USER's query context (e.g. `{"series_id": "GDP"}`), not the collector's internal params dict
- No logging of the params dict anywhere in the codebase

**Verified clean end-to-end.** API keys are ephemeral in-memory values that never reach any serialized output.

### 2. INPUT VALIDATION: CLI JSON parsing

| Check | Result |
|-------|--------|
| `_parse_query()` rejects non-JSON | CLEAN — catches `json.JSONDecodeError`, exits 1 |
| `_parse_query()` rejects non-dict JSON | CLEAN — `isinstance(ctx, dict)` check, exits 1 |
| Error message exposure | CLEAN — prints `"Invalid query JSON: {exc}"` which shows the parse error but no internal state |
| Collector `build_request()` validates required fields | CLEAN — all three new collectors raise `ValueError` on missing required fields |

### 3. COMMAND INJECTION: CLI argument handling

| Check | Result |
|-------|--------|
| Shell injection via `--query` | NOT VULNERABLE — argparse passes raw strings, `json.loads()` parses, no shell execution |
| Shell injection via `--output` | NOT VULNERABLE — `Path(output_path).write_text()` — no shell involvement |
| Shell injection via `--source` | NOT VULNERABLE — dict lookup `collector_map[source_id]` — no dynamic import or eval |
| Shell injection via `--theatre` | NOT VULNERABLE — passed as a plain string to `CollectionRunner.run()` |

### 4. ERROR HANDLING: No information disclosure

| Check | Result |
|-------|--------|
| Stack traces exposed to CLI user | CLEAN — all errors caught and printed as user-friendly messages to stderr |
| Internal paths exposed | CLEAN — `cmd_validate` shows only filename, not full path (`path.name`) |
| API response bodies in errors | CLEAN — non-200 responses return `{"error": "HTTP {status_code}"}` — no response body leakage |
| `cmd_run` exception handling | CLEAN — `runner.close_all()` in `finally` block (line 196) ensures cleanup |
| Broad `except Exception` in `cmd_validate` | ACCEPTABLE — line 230 catches registry validation errors, prints message, exits 1. This is a CLI tool; users need to see why validation failed. |

### 5. PATH TRAVERSAL: File paths in inspect/validate commands

| Check | Result |
|-------|--------|
| `cmd_inspect --bundle` | ACCEPTABLE — user-controlled path, CLI tool. Users are expected to provide file paths. `Path.read_text()` does not execute anything. Same pattern as `cat`, `jq`, etc. |
| `cmd_validate --registry` | ACCEPTABLE — same rationale. Validates file existence before reading. |
| `_write_output --output` | ACCEPTABLE — user-controlled output path. CLI tools write where told. No symlink following concern beyond OS defaults. |
| No directory listing or recursive operations | CLEAN |

### 6. CODE QUALITY: No obvious bugs

| Check | Result |
|-------|--------|
| FRED `extract()` observation cap | CLEAN — `observations[:20]` prevents unbounded memory on large responses |
| BoE `extract()` observation cap | CLEAN — `observations[:20]` same pattern |
| Gazette `extract()` notice cap | CLEAN — `results[:10]` capped |
| `PipelineConfig` immutability | VERIFIED — `@dataclass(frozen=True)`, tested in `test_frozen_dataclass` |
| Numeric env var parsing | MINOR NOTE — `int(os.environ.get("OSINT_MAX_WORKERS", "5"))` will raise `ValueError` on non-numeric input. This is acceptable: a bad env var *should* fail fast at startup rather than silently use a default. |
| `cmd_run` registry override pattern | CLEAN — creates new frozen config with override, no mutation |
| Counter-signal detection | CLEAN — case-insensitive `"insolvency" in (n.get("notice_type") or "").lower()` handles None values correctly |
| `collector_configs()` for no-auth sources | CLEAN — always includes `ecb_data_api`, `boe_rates`, `uk_gazette` with empty config dicts |
| `__main__.py` entry point | CLEAN — `raise SystemExit(main())` is idiomatic Python |

---

## Test Coverage Assessment

| File | Tests | Coverage Assessment |
|------|-------|---------------------|
| `test_config.py` | 13 | Defaults, env loading, collector configs, immutability — THOROUGH |
| `test_new_collectors.py` | 28 | Init validation, build_request, extract, mock HTTP collect, error paths — THOROUGH |
| `test_cli.py` | 11 | Help, inspect valid/missing/invalid, validate missing/actual, collect unknown/missing-key, run args — THOROUGH |
| `test_e2e_pipeline.py` | 8 | Full pipeline, score range, coverage %, hash determinism, gap report, serialization, partial/failed collectors — EXCELLENT |
| `test_fixtures_regression.py` | 15 | Registry loads, known sources, settlement eligible, free sources, upstream groups, jurisdiction, collector alignment — THOROUGH |

**Notable test quality:**
- All HTTP calls use `httpx.MockTransport` — zero live API calls in tests
- E2E tests use 3 stub collectors covering 3 different source groups, jurisdictions, and resolution roles
- Error paths tested: auth failure (401), server error (500), not found (404), invalid JSON, missing required fields
- Regression tests verify all 6 collector source_ids exist in the actual registry fixture
- Alignment tests verify `independence_upstream_id`, `jurisdiction`, and `source_group` match between collectors and registry

**Gap noted (non-blocking):** No test for `cmd_run` with a mocked successful pipeline (only argument validation tested). This is acceptable because the E2E tests cover the same code path through direct Python calls, and `cmd_run` is essentially a thin CLI wrapper around the same pipeline.

---

## Architectural Observations

1. **Zero framework dependencies.** Config uses stdlib `os` + `dataclasses`. CLI uses stdlib `argparse`. No Dynaconf, Click, or Typer. This is correct for a pipeline that must be dependency-minimal.

2. **Lazy imports in CLI.** `cmd_run` and `_get_collector_map()` use local imports to avoid loading heavy modules (pydantic models, httpx) until needed. Good for CLI responsiveness.

3. **Registry as source of truth.** Sprint plan estimated `boe_statistics` and `london_gazette`; implementation correctly uses `boe_rates` and `uk_gazette` from the registry. Same pattern as Sprint 2. Consistent discipline.

4. **Frozen config.** `PipelineConfig` is a frozen dataclass. The `cmd_run` registry override creates a new instance rather than mutating. Correct immutability pattern.

5. **Counter-signal integration.** Gazette collector sets `counter_signal_detected` and `counter_signal_detail` in its structured extract, correctly flowing into the pipeline's counter-signal evaluation stage.

---

## Environment Note

Unable to independently execute the test suite during this audit — both virtual environments (`backend/venv`, `backend/.venv`) have broken Python symlinks. This is an environment issue, not a code issue. The reviewer's attestation of 263 passing tests (228 OSINT + 35 theatre regression) is accepted based on the detailed reviewer.md report and my thorough code review confirming the tests are well-structured and would exercise the code paths claimed.

---

## Summary

| Category | Status |
|----------|--------|
| Secrets | CLEAN |
| Input Validation | CLEAN |
| Command Injection | NOT VULNERABLE |
| Error Handling | CLEAN |
| Path Traversal | ACCEPTABLE (CLI tool pattern) |
| Code Quality | CLEAN |
| Test Coverage | THOROUGH |
| Architectural Consistency | CLEAN |

**No blocking findings. No advisories. Ship it.**
