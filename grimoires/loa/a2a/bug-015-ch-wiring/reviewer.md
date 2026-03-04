# Implementation Report — bug-015-ch-wiring

**Title**: CH Collector Production Wiring Fix
**Date**: 2026-03-04
**Status**: IMPLEMENTED

## Summary

Fixed 3 wiring gaps preventing CompaniesHouseCollector from executing in production: added per-source parameter support to `CollectionRunner`, exported CH collector from package, and fixed env var truthiness in test gating.

## Task 1: Add `source_params` to `CollectionPlan` and wire through pipeline

**File**: `backend/osint/engine/collection_runner.py`

- Added `source_params: dict[str, dict] = field(default_factory=dict)` to `CollectionPlan` dataclass
- `build_plan()` now reads `oracle_config.get("source_params", {})` and passes to `CollectionPlan`
- `_collect_with_timeout()` merges `plan.source_params.get(collector.source_id(), {})` into request dict before calling `collector.fetch()`
- Source-specific params merge (not replace) the generic request — source keys override on collision
- Zero impact on existing callers: `source_params` defaults to empty dict

## Task 2: Export `CompaniesHouseCollector` from package

**File**: `backend/osint/__init__.py`

- Added `from backend.osint.collectors.companies_house import CompaniesHouseCollector`
- Added `"CompaniesHouseCollector"` to `__all__`
- `from backend.osint import CompaniesHouseCollector` now works

## Task 3: Fix env var truthiness in test gating

**File**: `backend/osint/tests/conftest.py`

Changed:
```python
os.environ.get("ECHELON_LIVE_WM")  # any non-empty string was truthy
```
To:
```python
os.environ.get("ECHELON_LIVE_WM", "").lower() in ("1", "true", "yes")
```

Same fix applied for `ECHELON_LIVE_CH`.

## Task 4: Remove E2E test monkeypatch, use `source_params`

**File**: `backend/osint/tests/test_e2e_corroboration.py`

- Added `"source_params": {"companies_house_api": {"company_number": "00000006"}}` to `oracle_config`
- Removed the `_patched_build` / `patch.object(runner, "_build_request", ...)` workaround
- Removed unused `json` import
- Test passes cleanly — CH collector receives `company_number` through the proper `source_params` path

## Task 5: Tests for `source_params` flow and env var gating

**File**: `backend/osint/tests/test_collection_runner.py` — 5 new tests:
- `test_build_plan_source_params` — verifies `source_params` extracted from `oracle_config`
- `test_build_plan_source_params_default_empty` — verifies empty default
- `test_source_params_merged_into_request` — verifies collector receives merged request
- `test_source_params_empty_backward_compat` — verifies plan without `source_params` works
- `test_source_params_only_applied_to_matching_collector` — verifies no cross-leak

**File**: `backend/osint/tests/test_env_gating.py` — 9 new tests:
- Truthy values: `"1"`, `"true"`, `"TRUE"`, `"yes"` → enabled
- Falsy values: `"0"`, `"false"`, `"no"`, `""`, unset → not enabled

## Test Results

```
803 passed, 11 skipped (9 pre-existing collection errors excluded)
22 new/modified tests pass (14 new + 8 existing in test_collection_runner.py)
Zero regressions
```

## Files Modified

| File | Change |
|------|--------|
| `backend/osint/engine/collection_runner.py` | Added `source_params` to `CollectionPlan`, `build_plan()`, `_collect_with_timeout()` |
| `backend/osint/__init__.py` | Added `CompaniesHouseCollector` import and `__all__` entry |
| `backend/osint/tests/conftest.py` | Fixed env var truthiness to explicit `("1", "true", "yes")` check |
| `backend/osint/tests/test_e2e_corroboration.py` | Replaced monkeypatch with `source_params`, removed unused `json` import |
| `backend/osint/tests/test_collection_runner.py` | Added 5 tests for `source_params` flow |
| `backend/osint/tests/test_env_gating.py` | NEW — 9 tests for env var gating |
