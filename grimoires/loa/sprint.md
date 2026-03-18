# Sprint Plan — Cycle-026a: Construct Evidence Anchoring + R2 Ingest Foundation

**Cycle:** cycle-026a
**Date:** 17 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Asset Policy + Registry Schema

**Goal:** define the classification and manifest model before any ingest work.

### Tasks

1. **Create registry schema models**
   - `DatasetRegistryEntry`
   - `DatasetRegistryDocument`
   - `RegistryFileEntry`
   - Write 3 tests: valid entry, missing files, invalid hash prefix

2. **Create construct anchor schema**
   - `AnchorClass`, `AnchorReference`, `EvaluationDimensionAnchor`
   - Write 2 tests: valid anchor mapping, weak anchor mapping

3. **Implement asset classification policy**
   - snapshot allowlist
   - live-only denylist
   - Write 3 tests: snapshot accepted, live accepted, mixed misuse rejected

**Exit:** 8 tests pass. Schema and policy surface are stable.

---

## Sprint 1 — Benchmark Ingest Registry

**Goal:** create manifest-ready benchmark entries for the initial construct verification pack.

### Tasks

1. **Add manifest builder service**
   - compute per-file hashes
   - compute top-level asset hash
   - emit `manifest.json`

2. **Register benchmark assets**
   - HumanEval
   - MBPP
   - HellaSwag
   - MMLU
   - MMLU-Pro
   - SWE-bench Verified metadata/splits

3. **Create aggregate dataset registry document**
   - `manifests/dataset_registry.json`

4. **Write tests**
   - 4 tests: manifest generation, stable hash, aggregate registry shape, path layout

**Exit:** benchmark registry pipeline works locally against populated folders.

---

## Sprint 2 — Standards Snapshot Registry

**Goal:** add standards snapshots as first-class anchor assets.

### Tasks

1. **Add standards entries**
   - WCAG 2.2
   - ARIA APG

2. **Create aggregate standards registry**
   - `manifests/standards_registry.json`

3. **Write tests**
   - 2 tests: WCAG manifest, ARIA manifest

**Exit:** standards have the same provenance contract as benchmarks.

---

## Sprint 3 — Construct Anchor Mapping

**Goal:** connect asset registries to construct verification semantics.

### Tasks

1. **Implement construct anchor mapper**
   - map dimensions to one or more anchor references
   - mark dimensions with no recognized anchor as `weakly_anchored`

2. **Add initial mapping rules**
   - deterministic code checks -> `deterministic_check`
   - benchmark prompt families -> `benchmark_dataset`
   - accessibility/UI compliance -> `public_standard`
   - real-world factual expertise -> `live_external_evidence`

3. **Optional utility script**
   - `build_eval_asset_manifest.py`

4. **Write tests**
   - 3 tests: fully anchored mapping, mixed mapping, weak-only mapping

5. **Final verification**
   - `npm run build`
   - full targeted test run

**Exit:** anchor mapping works and weakly anchored criteria are explicit.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Policy + schema | 8 |
| 1 | Benchmark manifest pipeline | 4 |
| 2 | Standards manifest pipeline | 2 |
| 3 | Construct anchor mapping | 3 |
| **Total** | | **~17** |

