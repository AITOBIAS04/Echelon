# Bug Triage — bug-015-ch-wiring

**Title**: CH collector not executable from production request shape — 3 wiring gaps
**Priority**: P1
**Source**: Post-cycle-015 review
**Date**: 2026-03-04

## Observed Failures

### F1 — `_build_request()` drops per-source params (P1)

**File**: `backend/osint/engine/collection_runner.py:142`

`CollectionRunner._build_request()` builds a single generic request dict (theatre_id, evaluation_window, geo) and passes the same dict to ALL collectors. CompaniesHouseCollector hard-requires `company_number` in the request dict and returns `success=False` when it's missing.

**Evidence**: `test_e2e_corroboration.py:78` monkeypatches `_build_request()` to inject `company_number`, masking this gap in tests.

**Root Cause**: `CollectionPlan` has no field for per-source parameters. `_build_request()` has no mechanism to merge source-specific params from `oracle_config`.

**Fix**: Add `source_params: dict[str, dict] = field(default_factory=dict)` to `CollectionPlan`. Populate from `oracle_config["source_params"]` in `build_plan()`. Merge into request in `_collect_with_timeout()` before passing to collector.

### F2 — CH collector not in production bootstrap (P1)

**File**: `backend/osint/__init__.py`

`CompaniesHouseCollector` is only instantiated in test fixtures. The package `__all__` exports only `WorldMonitorCollector` and `WorldMonitorConfig`. No production DI/bootstrap path creates the CH collector or registers it with `CollectionRunner`.

**Note**: This is actually the same pattern as WM collectors — even WorldMonitor collectors are test-only in the `backend/` package. The real production orchestration lives in the WorldMonitor external service. However, CH is a direct-API collector that MUST be instantiated in the backend process. The missing piece is a collector factory that reads `sources.json` and builds the collectors dict.

**Fix**: Add `CompaniesHouseCollector` to `__init__.py` exports. Create a `build_collectors()` factory function in `collection_runner.py` (or a new `collector_factory.py`) that reads the source registry and instantiates registered collectors.

### F3 — Env var gating treats any non-empty string as enabled (P2)

**File**: `backend/osint/tests/conftest.py:35-38`

```python
skip_wm = not (config.getoption("--live-wm", default=False)
               or os.environ.get("ECHELON_LIVE_WM"))
skip_ch = not (config.getoption("--live-ch", default=False)
               or os.environ.get("ECHELON_LIVE_CH"))
```

`os.environ.get()` returns any non-empty string as truthy. Values like `"0"`, `"false"`, `"no"` would all enable live tests. The skip reason message says `ECHELON_LIVE_WM=1`, implying only `"1"` should work.

**Fix**: Check against explicit truthy values: `os.environ.get("ECHELON_LIVE_WM", "").lower() in ("1", "true", "yes")`.

## Suspected Files

| File | Change Type |
|------|-------------|
| `backend/osint/engine/collection_runner.py` | Modify — add `source_params` to `CollectionPlan`, wire in `_collect_with_timeout()` and `build_plan()` |
| `backend/osint/__init__.py` | Modify — export `CompaniesHouseCollector` |
| `backend/osint/tests/conftest.py` | Modify — fix env var truthiness check |
| `backend/osint/tests/test_e2e_corroboration.py` | Modify — remove monkeypatch workaround, use `source_params` |
| `backend/osint/tests/test_collection_runner.py` | Modify/Add — test `source_params` flow |

## Test Infrastructure

- **Runner**: pytest
- **Existing tests**: `backend/osint/tests/` (mock + live-gated)
- **Gate check**: `pytest backend/ -x --tb=short` — baseline: 942 passed, 15 skipped

## Eligibility

| Criterion | Score |
|-----------|-------|
| Observed failure in production code path | Yes — CH collector always fails in production |
| Reproducible | Yes — deterministic: `_build_request()` never includes `company_number` |
| Stack trace / code evidence | Yes — `collection_runner.py:142`, `companies_house.py:63` |
| **Total** | **3/3 — Eligible** |
