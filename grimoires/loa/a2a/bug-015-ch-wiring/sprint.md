# Micro-Sprint — bug-015-ch-wiring

**Title**: CH Collector Production Wiring Fix
**Priority**: P1
**Estimated Tasks**: 5

---

## Task 1: Add `source_params` to `CollectionPlan` and wire through pipeline

**File**: `backend/osint/engine/collection_runner.py`

1. Add `source_params: dict[str, dict] = field(default_factory=dict)` to `CollectionPlan`
2. In `build_plan()`: extract `oracle_config.get("source_params", {})` and pass to `CollectionPlan`
3. In `_collect_with_timeout()`: merge `plan.source_params.get(collector.source_id(), {})` into the request dict after `_build_request()`

**Acceptance Criteria**:
- `CollectionPlan` has `source_params` field (dict of source_id → params dict)
- `build_plan()` reads `source_params` from `oracle_config`
- `_collect_with_timeout()` merges source-specific params into request before calling `collector.fetch()`
- Generic request fields (theatre_id, evaluation_window, geo) are preserved
- Source-specific params override generic fields if collision (source wins)

## Task 2: Export `CompaniesHouseCollector` from package

**File**: `backend/osint/__init__.py`

Add `CompaniesHouseCollector` to imports and `__all__`.

**Acceptance Criteria**:
- `from backend.osint import CompaniesHouseCollector` works
- Existing imports unchanged

## Task 3: Fix env var truthiness in test gating

**File**: `backend/osint/tests/conftest.py`

Change raw `os.environ.get()` truthiness to explicit check:
```python
os.environ.get("ECHELON_LIVE_WM", "").lower() in ("1", "true", "yes")
```

**Acceptance Criteria**:
- `ECHELON_LIVE_WM=1` enables live WM tests
- `ECHELON_LIVE_WM=true` enables live WM tests
- `ECHELON_LIVE_WM=0` does NOT enable live WM tests
- `ECHELON_LIVE_WM=false` does NOT enable live WM tests
- Unset env var does NOT enable live tests
- Same behavior for `ECHELON_LIVE_CH`

## Task 4: Remove E2E test monkeypatch, use `source_params`

**File**: `backend/osint/tests/test_e2e_corroboration.py`

Replace the `_build_request` monkeypatch with proper `source_params` in `oracle_config`:
```python
oracle_config["source_params"] = {
    "companies_house_api": {"company_number": "00000006"}
}
```

Remove the `_patched_build` workaround entirely.

**Acceptance Criteria**:
- No monkeypatch of `_build_request` in test
- CH collector receives `company_number` via `source_params`
- Test still passes with same assertions

## Task 5: Tests for `source_params` flow

**File**: `backend/osint/tests/test_collection_runner.py` (new or extend)

1. `test_source_params_merged_into_request` — build plan with `source_params`, verify collector receives merged request
2. `test_source_params_empty_default` — plan without `source_params` still works (backward compat)
3. `test_source_params_no_override_generic` — verify source params merge (not replace) request
4. `test_env_var_gating_zero_is_false` — set `ECHELON_LIVE_WM=0`, verify live tests skipped
5. `test_env_var_gating_one_is_true` — set `ECHELON_LIVE_WM=1`, verify live tests enabled

**Acceptance Criteria**:
- All 5 tests pass
- Zero regressions in existing test suite

---

## Gate Rule

Baseline: >=942 passed, <=15 skipped. Zero new failures. All 5 new tests pass.
