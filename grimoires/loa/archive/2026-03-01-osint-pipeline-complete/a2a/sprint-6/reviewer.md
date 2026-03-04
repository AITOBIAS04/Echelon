# Sprint 6 (Cycle-002 Sprint 3) — Implementation Report

**Sprint:** CLI, Config & End-to-End Integration
**Global ID:** sprint-6
**Date:** 2026-03-01
**Tests:** 228 passed (OSINT), 35 passed (theatre regression)

---

## Files Created (10)

| File | Lines | Purpose |
|------|-------|---------|
| `osint_pipeline/config.py` | 93 | PipelineConfig dataclass — env var loading, no framework deps |
| `osint_pipeline/cli.py` | 270 | CLI with run/inspect/validate/collect commands (argparse) |
| `osint_pipeline/collectors/fred.py` | 131 | FRED API collector (US, api_key auth, economic indicators) |
| `osint_pipeline/collectors/boe.py` | 119 | BoE Statistics collector (GB, no auth, interest rates) |
| `osint_pipeline/collectors/gazette.py` | 147 | London Gazette collector (GB, no auth, counter-signal source) |
| `tests/osint_pipeline/test_config.py` | 97 | 13 tests: defaults, env loading, collector configs, frozen |
| `tests/osint_pipeline/test_new_collectors.py` | 280 | 28 tests: FRED/BoE/Gazette init, build, extract, collect |
| `tests/osint_pipeline/test_cli.py` | 107 | 11 tests: help, inspect, validate, collect, run args |
| `tests/osint_pipeline/test_e2e_pipeline.py` | 306 | 8 tests: full pipeline, hash determinism, serialisation |
| `tests/osint_pipeline/test_fixtures_regression.py` | 114 | 15 tests: registry loads, known sources, alignment |

## Files Modified (3)

| File | Change |
|------|--------|
| `osint_pipeline/__main__.py` | Delegates to `cli.main()` (was stub) |
| `osint_pipeline/collectors/__init__.py` | Added BoECollector, FREDCollector, GazetteCollector re-exports |
| `pyproject.toml` | Added [project] metadata, pydantic/httpx deps, dev deps |

---

## Task Completion

### T3.1: `config.py` — Configuration Module
- [x] Loads `OSINT_REGISTRY_PATH` with default path
- [x] Loads `COMPANIES_HOUSE_API_KEY`, `SEC_EDGAR_USER_AGENT`, `FRED_API_KEY` from env
- [x] Loads `OSINT_MAX_WORKERS` (default 5), `OSINT_TIMEOUT_BUDGET` (default 60.0), `OSINT_COLLECTOR_TIMEOUT` (default 30.0)
- [x] No secrets in code or committed files
- [x] No framework dependency (stdlib `os` + `dataclasses` only)
- [x] Frozen dataclass (immutable)
- [x] `collector_configs()` returns per-collector config dicts

### T3.2: `cli.py` — Command-Line Interface
- [x] `run` command: full 3-stage pipeline with `--theatre`, `--query`, `--output`, `--registry`
- [x] `inspect` command: pretty-prints JSON file
- [x] `validate` command: loads registry, reports version, source count, free sources
- [x] `collect` command: runs single collector with `--source`, `--query`
- [x] Uses `argparse` (stdlib)
- [x] Exit codes: 0 success, 1 error
- [x] Meaningful error messages for missing API keys and unknown sources

### T3.3: Should-Have Collectors (FRED, BoE, Gazette)
- [x] `FREDCollector`: `fred_api`, US, API key auth, economic indicators
- [x] `BoECollector`: `boe_rates` (registry value), GB, no auth, interest rates
- [x] `GazetteCollector`: `uk_gazette` (registry value), GB, no auth, insolvency notices
- [x] All inherit from `BaseCollector` correctly
- [x] All `independence_upstream_id` values match registry
- [x] `extract()` returns sensible structured extracts
- [x] Gazette includes counter-signal detection (insolvency notice detection)

### T3.4: `__main__.py` Module Entry Point
- [x] `python -m osint_pipeline --help` shows usage
- [x] Delegates to `cli.main()`

### T3.5: End-to-End Integration Tests
- [x] `test_fixtures_regression.py`: registry loads, known sources present, alignment verified
- [x] End-to-end: 3 stub collectors -> CollectionRunner -> CorroborationEngine -> CounterSignalChecker -> Scorer -> OracleOutput
- [x] `OracleOutput.bundle_hash` is deterministic (same collection -> same hash)
- [x] `OracleOutput.composite_score` in [0.0, 1.0]
- [x] `OracleOutput.coverage_percentage` computed correctly
- [x] Existing 35 tests in `tests/theatre/test_canonical_json.py` still pass
- [x] All 228 new `tests/osint_pipeline/` tests pass
- [x] OracleOutput serialises to JSON without error

### T3.6: Package Metadata and `pyproject.toml` Updates
- [x] `pyproject.toml` has `pythonpath = ["."]` for `import osint_pipeline`
- [x] `pydantic` and `httpx` in dependencies
- [x] `pytest` in dev dependencies
- [x] No circular imports between `osint_pipeline` and `theatre`

---

## Registry Alignment

Sprint plan estimated source_ids differ from actual registry:
- BoE: `boe_rates` (registry) vs `boe_statistics` (sprint plan estimate)
- Gazette: `uk_gazette` (registry) vs `london_gazette` (sprint plan estimate)
- FRED: `fred_api` matches in both

Implementation uses registry values as source of truth (same pattern as Sprint 2).

## CLI Validation

```
$ python -m osint_pipeline validate --registry .../echelon_osint_source_registry_v0_4_0.json
Registry: echelon_osint_source_registry_v0_4_0.json
Version:  0.4.0
Sources:  57
Free:     7
Eligible: 13
Upstreams:56
```
