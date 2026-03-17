All good

## Sprint 91 (Cycle-026a Sprint 2) — Standards Snapshot Registry

### Tasks Verified

1. **Standards entries** — `STANDARDS_CATALOG` in `r2_manifest_builder.py` (lines 89-102):
   - WCAG 2.2: source_url matches PRD (`https://www.w3.org/TR/WCAG22/`), version `"2.2"`, license `None`.
   - ARIA APG: source_url matches PRD (`https://www.w3.org/WAI/ARIA/apg/`), version `"2024"`, license `None`.

2. **Aggregate standards registry** — `build_standards_registry` function:
   - Iterates `STANDARDS_CATALOG`, builds manifests for each standard whose local directory exists.
   - Expects layout `standards/{asset_id}/{version}/raw/` under the staging root.
   - Gracefully skips missing directories (partial builds supported).
   - Raises `ValueError` if no standards directories exist at all.

3. **R2 path convention for standards** — `r2_key_prefix("wcag", "2.2", asset_class="standard")` produces `"standards/wcag/2.2/"` as required by the SDD layout contract.

### Tests: 17 (exceeds sprint plan target of 2)

Sprint plan called for 2 tests (WCAG manifest, ARIA manifest); implementation delivers 17. Additional coverage includes:
- Stable hash for both WCAG and ARIA APG
- `STANDARDS_CATALOG` completeness and value assertions
- R2 key prefix for standards vs benchmarks, including unknown class rejection
- Aggregate standards registry with full staging, partial staging, and empty staging
- Provenance contract parity: standard entries use the exact same `DatasetRegistryEntry` schema as benchmarks
- JSON round-trip for standard entries

All 17 pass on Python 3.9.6.

### Observations

- The test `test_standard_same_schema_as_benchmark` (line 301-335 of test file) asserts structural equivalence between benchmark and standard entries. This directly verifies PRD acceptance criterion: "standards have the same provenance contract as benchmarks."
- Test helpers (`_populate_wcag_dir`, `_populate_aria_apg_dir`) create realistic directory structures that mirror the expected R2 layout (patterns/practices subdirs for ARIA APG).
- Good that `build_standards_registry` supports partial builds -- this means the operator can incrementally populate their staging root.
