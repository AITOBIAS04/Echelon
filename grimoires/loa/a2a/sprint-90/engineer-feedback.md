All good

## Sprint 90 (Cycle-026a Sprint 1) — Benchmark Ingest Registry

### Tasks Verified

1. **Manifest builder service** — `backend/services/r2_manifest_builder.py`
   - `sha256_file` streams in 64 KB chunks (good for large files).
   - `sha256_json` sorts entries by path before hashing canonical JSON, ensuring deterministic output regardless of input order.
   - `build_manifest` walks `asset_root` with `os.walk`, prunes `SKIP_NAMES` in-place (`.cache`, `.gitattributes`, `.huggingface`, `__pycache__`), and sorts file entries by path.
   - Policy gate: `reject_live_as_immutable` is called before any I/O, preventing wasted work.
   - Uses `datetime.now(timezone.utc)` (not deprecated `datetime.utcnow()`).

2. **Benchmark asset registration** — `BENCHMARK_CATALOG` contains all 6 required entries:
   - humaneval, mbpp, hellaswag, mmlu, mmlu-pro, swe-bench-verified
   - Each has source_url, version, and license.

3. **Aggregate registry document** — `build_registry_document` wraps entries in a `DatasetRegistryDocument`.

4. **R2 path conventions** — `r2_key_prefix` produces `benchmarks/{asset}/{version}/` or `standards/{asset}/{version}/` with unknown class rejection.

5. **Configurable staging root** — `get_staging_root` reads `ECHELON_EVAL_DATA_ROOT` env var, falls back to `~/.echelon/eval_data`. No hardcoded developer paths.

### Tests: 16 (exceeds sprint plan target of 4)

Sprint plan called for 4 tests; implementation delivers 16. Additional coverage includes:
- File sort order verification
- Different-content-different-hash (negative hash stability)
- `sha256_json` deterministic ordering test
- JSON round-trip for registry document
- `BENCHMARK_CATALOG` completeness assertion
- Per-benchmark R2 key prefix validation
- Skip artifact exclusion (`.cache`, `.gitattributes`, `.huggingface`, `__pycache__`)
- Empty directory rejection
- Non-existent directory rejection
- Live-only asset policy gate integration
- Staging root default and env-var override

All 16 pass on Python 3.9.6.

### Observations

- Minor source URL discrepancies with PRD section 6 (informational, not blocking):
  - `mmlu-pro`: PRD recommends `https://github.com/TIGER-AI-Lab/MMLU-Pro`, code uses `https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro`. The HuggingFace URL is the canonical data source, arguably more correct.
  - `swe-bench-verified`: PRD recommends `https://github.com/SWE-bench/SWE-bench`, code uses `https://github.com/princeton-nlp/SWE-bench`. The Princeton NLP repo is the original; the SWE-bench org repo is a fork/mirror. Either is defensible.
- `build_standards_registry` helper is also defined in this file (used in sprint 2). Good that it lives with the other builder functions rather than in a separate module.
- The `SKIP_NAMES` set covers the main transport/cache artifacts. If new ones emerge, they can be added to the frozenset.
