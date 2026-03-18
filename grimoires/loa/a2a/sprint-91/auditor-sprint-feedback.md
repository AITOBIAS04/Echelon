# Auditor Sprint Feedback — Sprint 91 (Cycle-026a Sprint-2)

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-17
**Sprint scope:** Standards Snapshot Registry (STANDARDS_CATALOG additions to r2_manifest_builder.py, build_standards_registry(), test_cycle026a_sprint2.py)

---

## Verdict: APPROVED

No CRITICAL, HIGH, or new MEDIUM findings. Sprint-2 extends the builder from sprint-1 to handle standards (WCAG, ARIA APG) using the exact same code paths. All sprint-1 findings (M-01, M-02) carry forward by inheritance — no new attack surface introduced.

---

## Security Checklist Results

### 1. Secrets
**PASS.** No credentials. Source URLs are public W3C standards pages. No authentication required for retrieval (not that this code retrieves anything — it only scans local directories).

### 2. Path Traversal
**PASS.** `build_standards_registry()` constructs paths via:
```python
asset_dir = staging_root / "standards" / asset_id / version / "raw"
```
Where `asset_id` and `version` come from the hardcoded `STANDARDS_CATALOG` tuple. No user input reaches the path construction. The downstream `build_manifest()` call inherits the same `relative_to()` containment from sprint-1.

### 3. Input Validation
**PASS.** The `staging_root` parameter defaults to `get_staging_root()` (validated in sprint-1 audit). The `registry_version` parameter is a string with no filesystem implications. All catalog metadata is hardcoded.

### 4. Data Integrity
**PASS.** Standards manifests use the identical `sha256_file()` and `sha256_json()` paths as benchmarks. The `asset_class="standard"` value flows through `DatasetRegistryEntry` which validates it via `Literal["benchmark", "standard"]`. Content hashing is deterministic and canonical.

### 5. Supply Chain
**PASS.** No new imports. `build_standards_registry()` uses only `Path` (stdlib) and internal module imports already audited in sprint-1.

### 6. Error Handling
**PASS.** `build_standards_registry()` raises `ValueError` when no standards directories are found, with a descriptive but non-sensitive error message. Individual `build_manifest()` failures for missing directories are silently skipped (the function checks `asset_dir.is_dir()` before calling the builder), which is correct behavior — partial builds are allowed.

### 7. Code Quality
**PASS.** The `build_standards_registry()` function is clean. It iterates the catalog, skips missing directories, builds manifests, and wraps the result. No dead code, no surprising control flow.

---

## Specific Observations

### Standards catalog is fully hardcoded
`STANDARDS_CATALOG` contains exactly 2 entries (`wcag`, `aria-apg`), both with public W3C URLs, fixed version strings, and `None` for license (appropriate — W3C standards don't have SPDX license identifiers). The catalog is immutable at runtime (it's a module-level list of tuples). Adding new standards requires a code change, which is the correct pattern for a curated evidence registry.

### R2 path convention extends cleanly
`r2_key_prefix("wcag", "2.2", asset_class="standard")` produces `"standards/wcag/2.2/"`. The `prefix_map` in `r2_key_prefix()` handles both `"benchmark"` and `"standard"` without needing modification. Good foresight in the sprint-1 design.

### Directory layout convention
Standards expect a specific layout: `standards/{asset_id}/{version}/raw/`. The `raw/` suffix is interesting — it separates raw downloads from potential processed artifacts. This is a good convention that prevents accidentally including build artifacts in snapshots.

---

## LOW Findings

### L-04: `build_standards_registry()` silently skips missing standards
If the staging directory exists but a specific standard's `raw/` directory is missing, the function silently skips it. This is correct behavior for partial builds, but there's no logging or warning. An operator might not realize a standard was skipped.

**Recommendation:** Consider logging a warning (not an error) when a cataloged standard's directory is missing. Not blocking.

---

## Test Coverage Assessment

**test_cycle026a_sprint2.py** provides thorough coverage:
- 14 test cases across 7 test classes.
- WCAG manifest: generation, stable hash.
- ARIA APG manifest: subdirectory traversal (patterns/ + practices/), stable hash.
- Catalog completeness: both entries present, metadata validated, specific values checked for each.
- R2 path convention: standards prefix, ARIA APG path, backward compatibility with benchmark default, unknown class rejection.
- Aggregate registry: full build (both standards), partial build (WCAG only), empty staging rejection.
- Provenance contract: standards use same schema as benchmarks, JSON round-trip for standards.

No gaps identified. The tests verify that standards share the same integrity guarantees (hash format, size tracking, sorted paths, JSON serialization) as benchmarks.

---

## Inherited Findings

The following findings from sprint-90 carry forward because `build_standards_registry()` uses the same `build_manifest()` and `r2_key_prefix()` functions:

- **M-01 (symlink following):** Applies to standard asset directories.
- **M-02 (R2 key prefix sanitization):** Mitigated here because all `r2_key_prefix()` calls for standards use hardcoded catalog values. No user-controlled input reaches the function for standards.

---

## Summary

Sprint-2 is a clean, minimal extension of the sprint-1 builder to support standards assets. No new attack surface. The same hashing, policy enforcement, and path containment mechanisms apply. The hardcoded catalog with public W3C URLs is appropriate for curated evidence anchoring. Approved.
