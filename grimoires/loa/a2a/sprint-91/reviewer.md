# Implementation Report — Sprint 91 (Cycle-026a Sprint 2)

**Sprint:** 2 (global ID 91)
**Cycle:** 026a — Construct Evidence Anchoring + R2 Ingest Foundation
**Goal:** Standards Snapshot Registry
**Date:** 2026-03-17

---

## Files Modified

| File | Change |
|------|--------|
| `backend/services/r2_manifest_builder.py` | Added `STANDARDS_CATALOG`, updated `r2_key_prefix()` to handle `asset_class`, added `build_standards_registry()` |

## Files Created

| File | Purpose |
|------|---------|
| `backend/tests/test_cycle026a_sprint2.py` | 17 tests across 6 test classes covering all sprint-2 surfaces |

## Implementation Details

### 1. Standards Catalog (`STANDARDS_CATALOG`)

2 initial standards entries as `list[tuple[str, str, str, Optional[str]]]`:

| Asset ID | Source URL | Version | License |
|----------|-----------|---------|---------|
| wcag | https://www.w3.org/TR/WCAG22/ | 2.2 | None |
| aria-apg | https://www.w3.org/WAI/ARIA/apg/ | 2024 | None |

Same tuple schema as `BENCHMARK_CATALOG` — (asset_id, source_url, version, license).

### 2. Updated `r2_key_prefix()`

Added `asset_class` keyword argument (default `"benchmark"` for backward compatibility):
- `asset_class="benchmark"` → `benchmarks/{asset_id}/{version}/`
- `asset_class="standard"` → `standards/{asset_id}/{version}/`
- Unknown `asset_class` raises `ValueError`

Sprint-1 tests pass without modification because the default is `"benchmark"`.

### 3. `build_standards_registry()`

Aggregate builder that:
- Iterates over `STANDARDS_CATALOG`
- Looks for each standard at `staging_root/standards/{asset_id}/{version}/raw/`
- Skips standards whose directory does not exist (partial builds supported)
- Calls `build_manifest()` with `asset_class="standard"` for each present directory
- Wraps results in a `DatasetRegistryDocument` via `build_registry_document()`
- Raises `ValueError` if no standards directories are found

## Test Results

```
47 passed in 0.17s
```

| Test Class | Tests | Status |
|------------|-------|--------|
| TestWcagManifest | 2 (temp dir manifest, stable hash) | All PASSED |
| TestAriaApgManifest | 2 (temp dir with subdirs, stable hash) | All PASSED |
| TestStandardsCatalog | 4 (entries completeness, metadata, WCAG values, ARIA APG values) | All PASSED |
| TestR2PathConventionStandards | 4 (standard prefix, aria-apg prefix, benchmark default, unknown rejected) | All PASSED |
| TestStandardsRegistry | 3 (full registry, partial registry, empty staging rejected) | All PASSED |
| TestProvenanceContract | 2 (same schema as benchmark, JSON round-trip) | All PASSED |

Sprint-0 regression: 14 passed. Sprint-1 regression: 16 passed. No regressions.

## Exit Criteria

- [x] 2+ tests pass for standards (17 pass)
- [x] Standards have same provenance contract as benchmarks (verified by TestProvenanceContract)
- [x] WCAG test creates temp dir with wcag22.html, verifies asset_class="standard"
- [x] ARIA APG test creates temp dir with patterns/ and practices/ subdirs
- [x] R2 path convention: standards use `standards/` prefix, benchmarks still use `benchmarks/`
- [x] Tests use only temp dirs (no developer-specific paths)
- [x] No DB migrations, no API routes
- [x] Sprint-0 and sprint-1 tests pass (zero regressions)

## Design Decisions

1. **Backward-compatible `r2_key_prefix()`:** Added `asset_class` as a keyword-only argument with default `"benchmark"` — all sprint-1 callers continue working without changes
2. **Prefix map over if/elif:** `r2_key_prefix()` uses a dict lookup with explicit `ValueError` for unknown classes, making it easy to add future asset classes
3. **Partial build support:** `build_standards_registry()` gracefully skips missing standard directories, allowing incremental ingestion
4. **License=None for standards:** W3C standards are not distributed under SPDX software licenses — `None` is the honest representation
5. **Same provenance contract enforced by test:** `TestProvenanceContract` verifies that standards and benchmarks share identical schema fields, hash format, and serialization behavior
