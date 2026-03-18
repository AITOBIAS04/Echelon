# Implementation Report — Sprint 90 (Cycle-026a Sprint 1)

**Sprint:** 1 (global ID 90)
**Cycle:** 026a — Construct Evidence Anchoring + R2 Ingest Foundation
**Goal:** Benchmark Ingest Registry
**Date:** 2026-03-17

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/services/r2_manifest_builder.py` | Manifest builder service: `build_manifest()`, `build_registry_document()`, SHA-256 helpers, benchmark catalog, R2 path conventions |
| `backend/tests/test_cycle026a_sprint1.py` | 16 tests across 6 test classes covering all sprint surfaces |

## Implementation Details

### 1. Manifest Builder Service (`r2_manifest_builder.py`)

**Core function: `build_manifest()`**
- Accepts `asset_root: Path` plus keyword args for asset metadata
- Policy gate: calls `reject_live_as_immutable()` before any I/O
- Walks directory recursively via `os.walk()`, pruning `SKIP_NAMES` directories in-place
- Computes per-file SHA-256 via `sha256_file()` (64 KB streaming chunks)
- Computes top-level aggregate hash via `sha256_json()` (canonical JSON of sorted file list)
- Returns a fully validated `DatasetRegistryEntry`
- Raises `FileNotFoundError` for missing directories, `ValueError` for empty/live assets

**Helpers:**
- `sha256_file(filepath)` — streams file in 64 KB chunks, returns `sha256:<hex>`
- `sha256_json(file_entries)` — sorts entries by path, hashes canonical JSON, returns `sha256:<hex>`
- `get_staging_root()` — reads `ECHELON_EVAL_DATA_ROOT` env var, falls back to `~/.echelon/eval_data`
- `r2_key_prefix(asset_id, version)` — returns `benchmarks/{asset_id}/{version}/`
- `_should_skip(name)` — checks against `SKIP_NAMES` frozenset

**Skip artifacts:** `.cache`, `.gitattributes`, `.huggingface`, `__pycache__`

### 2. Benchmark Catalog (`BENCHMARK_CATALOG`)

6 initial benchmark entries as `list[tuple[str, str, str, Optional[str]]]`:

| Asset ID | Source | Version | License |
|----------|--------|---------|---------|
| humaneval | github.com/openai/human-eval | v1.0 | MIT |
| mbpp | github.com/google-research/.../mbpp | v1.0 | Apache-2.0 |
| hellaswag | github.com/rowanz/hellaswag | v1.0 | MIT |
| mmlu | github.com/hendrycks/test | v1.0 | MIT |
| mmlu-pro | huggingface.co/datasets/TIGER-Lab/MMLU-Pro | v1.0 | MIT |
| swe-bench-verified | github.com/princeton-nlp/SWE-bench | v1.0 | MIT |

### 3. Registry Document Builder (`build_registry_document()`)

- Wraps a list of `DatasetRegistryEntry` into a `DatasetRegistryDocument`
- Sets `generated_at` to current UTC time
- Configurable `registry_version` (default "1.0")

## Test Results

```
16 passed in 0.28s
```

| Test Class | Tests | Status |
|------------|-------|--------|
| TestManifestGeneration | 2 (temp dir manifest, files sorted by path) | All PASSED |
| TestStableHash | 3 (same input same hash, different content different hash, sha256_json deterministic) | All PASSED |
| TestRegistryDocument | 3 (aggregate shape, JSON round-trip, benchmark catalog completeness) | All PASSED |
| TestR2PathConvention | 2 (prefix format, various assets) | All PASSED |
| TestSkipArtifacts | 1 (cache artifacts skipped) | All PASSED |
| TestEdgeCases | 5 (empty dir rejected, nonexistent dir rejected, live asset rejected, staging root default, staging root from env) | All PASSED |

Sprint-0 regression: 14 passed (no regressions).

## Exit Criteria

- [x] 4+ tests pass (16 pass)
- [x] Manifest builder produces valid `DatasetRegistryEntry` objects
- [x] Stable hashing (deterministic across runs and input order)
- [x] R2 path convention enforced
- [x] Transport/cache artifacts skipped
- [x] Policy gate rejects live-only assets
- [x] stdlib + pydantic only (hashlib, pathlib, json, os, datetime)
- [x] Tests use only temp dirs (no developer-specific paths)
- [x] No DB migrations, no API routes

## Design Decisions

1. **Policy gate first:** `build_manifest()` calls `reject_live_as_immutable()` before any filesystem I/O, failing fast for policy violations
2. **In-place directory pruning:** `dirnames[:] = [d for d in dirnames if not _should_skip(d)]` prevents `os.walk` from descending into skipped directories, avoiding unnecessary I/O
3. **Canonical JSON for top-level hash:** `sha256_json()` sorts entries by path and uses `sort_keys=True, separators=(",", ":")` to produce a deterministic representation regardless of input order
4. **BENCHMARK_CATALOG as list of tuples:** lightweight data structure that avoids creating Pydantic objects for static catalog data — these are metadata templates, not manifests
5. **16 tests (4x the minimum):** extra coverage for edge cases (empty dirs, nonexistent paths, env var handling, order independence, regression against sprint-0)
