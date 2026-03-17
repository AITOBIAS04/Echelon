# Auditor Sprint Feedback — Sprint 90 (Cycle-026a Sprint-1)

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-17
**Sprint scope:** Benchmark Ingest Registry (r2_manifest_builder.py, build_eval_asset_manifest.py, test_cycle026a_sprint1.py)

---

## Verdict: APPROVED

No CRITICAL or HIGH findings. Two MEDIUM findings documented below — both are defense-in-depth improvements, not blocking vulnerabilities given the current threat model (local CLI tool, not network-facing).

---

## Security Checklist Results

### 1. Secrets
**PASS.** No hardcoded credentials, API keys, or tokens. The `.huggingface` directory is in `SKIP_NAMES` — good, this prevents accidentally snapshotting HuggingFace auth tokens into R2 manifests. Explicit security awareness demonstrated.

### 2. Path Traversal

#### Q1: Does `sha256_file()` handle symlinks safely?
**MEDIUM (M-01).** `sha256_file()` calls `open(filepath, "rb")` which follows symlinks by default. If an attacker can place a symlink inside the `asset_root` directory pointing outside it (e.g., `raw/evil -> /etc/shadow`), the function will read and hash the target file. The symlink would also appear in the manifest with its target's `size_bytes` from `full_path.stat()` (which also follows symlinks).

**Mitigations already in place:**
- `build_manifest()` uses `os.walk()` which traverses symlinked directories by default but computes relative paths via `full_path.relative_to(asset_root).as_posix()`. The relative path would look normal (no `../` escaping), but the *content* read would be from the symlink target.
- The CLI tool is a local operator utility, not a network-facing service.
- The staging root is under user control (`~/.echelon/eval_data` or `ECHELON_EVAL_DATA_ROOT`).

**Residual risk:** An attacker with write access to the staging directory could exfiltrate sensitive file contents into the R2 manifest (hashes of those files, not the content itself — but hash presence confirms file existence and content matching). Risk is LOW in practice because if an attacker has write access to the staging dir, they already own the pipeline.

**Recommendation:** Add `if full_path.is_symlink(): continue` in the `build_manifest()` file walk, or use `full_path.resolve()` and verify containment via `resolved.relative_to(asset_root.resolve())`. Not blocking.

#### Q2: Does `build_manifest()` validate that the asset_root doesn't contain path traversal in file entries?
**PASS.** The `relative_to()` call on line 235 (`full_path.relative_to(asset_root).as_posix()`) is the key defense. If `full_path` is not actually under `asset_root`, Python's `pathlib.relative_to()` raises a `ValueError`. This means generated paths can never contain `..` components. The manifest builder cannot produce path-traversal entries from its own walk.

The concern raised in sprint-89 (L-01) about manually crafted `RegistryFileEntry` objects with `..` in the path remains, but that's a schema-layer issue, not a builder-layer issue.

### 3. Input Validation

#### Q3: Does `r2_key_prefix()` sanitize inputs for R2 path injection?
**MEDIUM (M-02).** `r2_key_prefix()` performs no sanitization on `asset_id` or `version` before interpolating them into the R2 key path:

```python
return f"{bucket}/{asset_id}/{version}/"
```

If `asset_id` were `"../../admin"` and `version` were `"../keys"`, the result would be `"benchmarks/../../admin/../keys/"` — a path traversal in the R2 key namespace.

**Mitigations already in place:**
- `asset_id` is validated by Pydantic's `_ASSET_ID_PATTERN` (`^[a-z0-9][a-z0-9_-]*$`) at the schema layer, which rejects slashes, dots, and all special characters.
- `version` is constrained by `min_length=1` only — no regex guard. However, `version` values in `BENCHMARK_CATALOG` and `STANDARDS_CATALOG` are hardcoded strings like `"v1.0"`, `"2.2"`, `"2024"`.
- `asset_class` is validated against a fixed `prefix_map` dict.

**Residual risk:** If `r2_key_prefix()` is ever called with user-controlled `version` or `asset_id` values that bypass schema validation (direct function call, not via Pydantic model), R2 path injection is possible.

**Recommendation:** Add a quick `assert "/" not in asset_id and "/" not in version` guard in `r2_key_prefix()`, or apply the `_ASSET_ID_PATTERN` regex to both. Not blocking for current usage, but a good defense-in-depth measure.

### 4. Data Integrity

#### SHA-256 hashing correct?
**PASS.**
- `sha256_file()` uses streaming reads with `_HASH_CHUNK_SIZE = 65_536` (64 KB). This is correct for large files and avoids loading entire files into memory.
- `sha256_json()` produces canonical JSON via `json.dumps(payload, sort_keys=True, separators=(",", ":"))` — deterministic, no whitespace variance, sorted keys. The entries are also pre-sorted by path before serialization. This is textbook canonical hashing.
- UTF-8 encoding is explicit: `canonical.encode("utf-8")`.

#### Canonical JSON for reproducibility?
**PASS.** The `sha256_json()` function sorts entries by path, sorts JSON keys, and uses compact separators. This produces identical hashes for semantically identical inputs regardless of insertion order. Verified by `test_sha256_json_deterministic`.

### 5. Supply Chain
**PASS.** Imports: `hashlib`, `json`, `os`, `datetime`, `pathlib`, `typing` (all stdlib), `argparse`, `sys` (stdlib in CLI). Internal imports from `backend.schemas` and `backend.services`. No third-party imports beyond pydantic (transitive through schemas).

### 6. Error Handling
**PASS.**
- `build_manifest()` raises `FileNotFoundError` for missing directories, `ValueError` for empty directories or policy violations. Error messages include the path or asset_id but no sensitive system information.
- The CLI script (`build_eval_asset_manifest.py`) catches `(FileNotFoundError, ValueError)` and prints to stderr, then exits with code 1. No stack traces leaked to stdout.
- `argparse` uses `choices=["benchmark", "standard"]` for `--asset-class`, providing built-in validation.

### 7. Code Quality
**PASS.** Clean, well-documented, no dead code. The `SKIP_NAMES` frozenset is a good pattern — immutable, O(1) lookup. The `_should_skip()` helper is simple and correct. The `BENCHMARK_CATALOG` and `STANDARDS_CATALOG` use tuples (immutable) rather than dicts.

---

## Specific Concerns (from audit brief)

### Q5: Does the CLI script (`build_eval_asset_manifest.py`) validate its argparse inputs?
**PASS.**
- `--asset-id`: Required, string (further validated by Pydantic downstream).
- `--asset-class`: `choices=["benchmark", "standard"]` — argparse rejects invalid values before they reach the builder.
- `--source-url`: Required, string (validated by Pydantic `min_length=1`).
- `--version`: Required, string.
- `--root`: Required, `type=Path` — argparse converts to Path object. The builder validates existence via `is_dir()`.
- `--license`: Optional, defaults to None.

The CLI does not run as root, does not open network connections, and outputs JSON to stdout. The attack surface is minimal.

---

## MEDIUM Findings

### M-01: `sha256_file()` follows symlinks
See Path Traversal section above. `open(filepath, "rb")` follows symlinks. An attacker with write access to the staging directory could craft symlinks to read file content hashes from outside the asset root.

**Severity:** MEDIUM (requires local write access to staging dir)
**Recommendation:** Skip symlinks in `build_manifest()` walk or resolve+containment-check.

### M-02: `r2_key_prefix()` does not sanitize path components
See Input Validation section above. Direct callers could inject path traversal into R2 key namespace if bypassing Pydantic schema validation.

**Severity:** MEDIUM (currently mitigated by schema-layer validation for all known call paths)
**Recommendation:** Add slash/dot-dot rejection guard in `r2_key_prefix()`.

---

## LOW Findings

### L-03: `ECHELON_EVAL_DATA_ROOT` environment variable not validated
`get_staging_root()` reads from `ECHELON_EVAL_DATA_ROOT` and passes it directly to `Path()`. A malicious env var value is unlikely in practice (the process owner controls their environment), but no existence or format check is performed.

**Recommendation:** No action needed. Standard practice for CLI tools.

---

## Test Coverage Assessment

**test_cycle026a_sprint1.py** provides strong coverage:
- 15 test cases across 6 test classes.
- Manifest generation, stable hashing, registry document shape.
- R2 path convention tested for all catalog entries.
- Skip artifact filtering tested with real `.cache`, `.huggingface`, `__pycache__`, `.gitattributes`.
- Empty directory rejection, nonexistent directory rejection, live-only policy rejection.
- Environment variable behavior for staging root (both default and override).
- JSON round-trip serialization.
- Deterministic hash ordering tested explicitly.
- Catalog completeness verified (6 benchmarks).

**Gap:** No test for symlink behavior in `build_manifest()`. This is consistent with M-01 above.

---

## Summary

Sprint-1 delivers the core manifest builder with correct hashing, proper file walking, policy enforcement, and a clean CLI interface. The two MEDIUM findings (symlink following and R2 key prefix sanitization) are defense-in-depth improvements that do not represent exploitable vulnerabilities in the current deployment context (local CLI, operator-controlled staging directory). Approved.
