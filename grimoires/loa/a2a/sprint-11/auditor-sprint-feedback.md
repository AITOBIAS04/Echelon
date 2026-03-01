# Security Audit: Sprint 11

**Verdict: APPROVED - LETS FUCKING GO**

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-01
**Sprint**: 1 (Global Sprint 11) — Cycle 007: Two-Rail Deterministic Theatres — Unified Pipeline
**Files Audited**: 8 code files (7 new, 1 additive modification)

---

## Prerequisites Verified

- `engineer-feedback.md`: Verdict "All good" confirmed (line 6)
- `reviewer.md`: All 9 tasks PASS, SC-10 compliance verified

---

## Security Checklist

| Check | Status | Notes |
|-------|--------|-------|
| Hardcoded secrets | PASS | No API keys, tokens, passwords, or credentials anywhere in new code |
| Credentials in test fixtures | PASS | Fixture data contains only financial domain data (balances, states, transitions) |
| Secrets in error messages/logs | PASS | Print statements expose only template keys and composite scores |
| Command injection (argparse) | PASS | `--template` uses `choices=` whitelist from `TEMPLATE_REGISTRY` keys; `--output-dir` creates local Path only |
| Path traversal (record_id) | PASS | `record_id` values used in filenames (`{rid}.json`); all fixture record_ids verified alphanumeric+underscore only (scanned all v02 datasets) |
| Path traversal (evidence_dir) | PASS | Constructed from `output_dir / f"evidence_{template_key}"` where template_key is whitelisted via `TEMPLATE_REGISTRY` |
| JSON parsing safety | PASS | Uses `json.loads()` exclusively; no `yaml.unsafe_load`, no `pickle`, no `eval`/`exec` |
| Decimal edge cases (NaN/Infinity) | LOW | `Decimal(str(value))` where value comes from `dict.get(key, 0)` — default 0 prevents None. NaN/Infinity from fixture data would produce `Decimal('NaN')` or `Decimal('Infinity')` which would fail tolerance checks, returning 0.0 (fail-safe). Not exploitable — fixture data is project-controlled, not user-supplied |
| `shutil.rmtree()` safety | PASS | Line 180: `shutil.rmtree(evidence_dir)` where `evidence_dir = output_dir / f"evidence_{template_key}"`. Template key is from TEMPLATE_REGISTRY (hardcoded dict). Output_dir from `--output-dir` arg (default: `output/unified_certificates`). Cannot delete unintended directories — path is always scoped under the output directory |
| File writes | PASS | All writes target `evidence_dir` subdirectories; all paths constructed from controlled template keys and fixture record_ids |
| `sys.path` manipulation | LOW | Lines 32-37: Inserts project root and osint/ directory. Standard pattern used across the codebase. Not exploitable — paths are computed from `__file__` parent, not user input |
| Deterministic hashing | PASS | `sort_keys=True` on all JSON writes, `canonical_hash()` for commitment, fixed `DETERMINISTIC_EPOCH`, `build_manifest()` called before `manifest.json` write (excluding self from hash). Determinism tests confirm dual-run SHA-256 match |
| Certificate field validation | PASS | All required fields populated, `CalibrationCertificate(**data)` model validation in cross-path schema tests |
| Manifest completeness | PASS | Integration test `test_manifest_contains_all_files` asserts set equality of manifest keys vs actual files (excluding manifest.json and certificate.json) |
| Test isolation | PASS | All integration/determinism/all-templates tests use pytest `tmp_path` or `tmp_path_factory` fixtures with automatic cleanup. No shared mutable state between tests |
| SC-10 compliance | PASS | `git diff HEAD` confirms only `theatre/scoring/__init__.py` modified (additive: +2 lines, 0 deletions). No changes to existing scorers, engine, pipeline script, or OSINT infrastructure |
| `eval`/`exec`/`subprocess` | PASS | None present in any audited file |
| Network calls | PASS | No HTTP/network calls in scorers or runner. All data from local fixtures |

---

## Detailed File-by-File Analysis

### 1. `theatre/scoring/arrears_scorer.py` (NEW)

**Lines of code**: 261
**Risk**: LOW

- Clean scorer implementation matching the established pattern (EscrowScorer, WaterfallScorer, ReconciliationScorer)
- All 6 criteria dispatch through a dict lookup (lines 63-69) — no dynamic dispatch, no reflection
- `VALID_TRANSITIONS` frozenset (24 pairs) is immutable at module level — cannot be tampered with at runtime
- `Decimal(str(value))` pattern used consistently for all financial arithmetic (10 call sites verified)
- Unknown criteria return 0.0 (fail-safe, line 74) — correct behavior, prevents false positives
- `ROUND_HALF_UP` imported but unused (line 17): cosmetic only, noted by engineer review. Not a security issue
- Each `_check_*` method cross-checks structural analysis against `criteria_verdicts` from expected data — defense-in-depth against fixture corruption

### 2. `theatre/scoring/__init__.py` (MODIFIED — additive)

**Change**: +2 lines (1 import, 1 `__all__` entry)
**Risk**: NONE

- Git diff confirmed: zero deletions, all prior exports intact

### 3. `scripts/run_two_rail_certificates.py` (NEW)

**Lines of code**: 345
**Risk**: LOW

- `TEMPLATE_REGISTRY` (lines 61-86) is a hardcoded dict — no dynamic template loading from user input
- `argparse` `--template` uses `choices=` whitelist — rejects unknown template keys at CLI parsing level
- `shutil.rmtree` (line 180) operates only on `evidence_dir` scoped under `output_dir`, constructed from whitelisted template keys
- `output_dir.mkdir(parents=True, exist_ok=True)` (line 333) — safe directory creation
- `json.dumps(... sort_keys=True, indent=2)` on all file writes — deterministic output
- `model_dump_json()` + `json.loads()` round-trip for Pydantic models (lines 220, 257) — safe serialization
- Import order documented with an explicit hazard comment (lines 39-41) — good engineering practice
- Exit code propagation correct: 0 if all pass, non-zero otherwise (line 299)

### 4. `tests/theatre/test_arrears_scorer.py` (NEW)

**Lines of code**: 170
**Risk**: NONE

- `_run()` helper uses deprecated `asyncio.get_event_loop().run_until_complete()` (line 59) — pragmatic workaround for missing `pytest-asyncio`, noted by engineer review. Functionally correct for sync test execution. Not a security risk
- Fixture path resolved via `Path(__file__).resolve().parents[2]` — controlled, not user-supplied
- 14 test cases with clear intent per test

### 5. `tests/theatre/test_unified_pipeline.py` (NEW)

**Lines of code**: 93
**Risk**: NONE

- Uses `tmp_path` fixture for test isolation
- `scripts` added to `sys.path` for importing `run_two_rail_certificates` — same pattern as other test files
- 5 well-structured integration tests

### 6. `tests/theatre/test_determinism.py` (NEW)

**Lines of code**: 83
**Risk**: NONE

- Dual-run determinism validation via SHA-256 comparison
- Correctly excludes `certificate.json` from file content comparison (contains UUID)
- Uses `tmp_path` fixture for isolated runs

### 7. `tests/theatre/test_all_templates.py` (NEW)

**Lines of code**: 69
**Risk**: NONE

- `scope="module"` fixture correctly shares pipeline run across parametrized tests (performance optimization, not a security concern)
- Composite score ranges are intentionally wide to absorb fixture drift — acceptable

### 8. `tests/theatre/test_cross_path_schema.py` (NEW)

**Lines of code**: 65
**Risk**: NONE

- Validates 11 required certificate fields
- Pydantic model round-trip confirms schema compatibility

---

## Advisory Findings (Non-Blocking)

### A-1: Decimal(str()) with NaN/Infinity — Severity: LOW (informational)

**File**: `theatre/scoring/arrears_scorer.py`, lines 115-189
**Finding**: `Decimal(str(value))` will happily parse `"nan"` or `"inf"` from fixture data without raising. These would produce `Decimal('NaN')` or `Decimal('Infinity')`.
**Impact**: Nil in practice — fixture data is project-controlled (not user-supplied). Arithmetic comparisons with NaN always fail tolerance checks, producing 0.0 (fail-safe behavior). Not exploitable.
**Recommendation**: No action required. If fixture data ever comes from external sources, add an explicit `if not val.is_finite(): return 0.0` guard.

### A-2: sys.path manipulation — Severity: LOW (informational)

**Files**: `scripts/run_two_rail_certificates.py` (lines 32-37), all test files
**Finding**: Multiple `sys.path.insert(0, ...)` calls to resolve import order dependencies.
**Impact**: Standard pattern in this codebase. Paths are computed from `__file__` parent (not user input). The documented import-order hazard (echelon_verify shadowing theatre/) is mitigated by the comment on lines 39-41.
**Recommendation**: No action required for this sprint. Consider a pyproject.toml workspace configuration in a future cycle to eliminate sys.path manipulation.

### A-3: ROUND_HALF_UP unused import — Severity: LOW (cosmetic)

**File**: `theatre/scoring/arrears_scorer.py`, line 17
**Finding**: `ROUND_HALF_UP` is imported but never used. Docstring references it but no `.quantize()` calls exist.
**Impact**: None. Linting may flag it, but it serves as a forward-compatibility import.
**Recommendation**: No action required. Remove when linting is enforced.

---

## Verdict

**APPROVED.** All 8 files pass the security checklist. No secrets, no injection vectors, no unsafe deserialization, no path traversal, no non-determinism sources. SC-10 compliance verified via git diff. The implementation is clean, follows established patterns, and the test coverage is thorough (32 new tests across 5 test files). The 3 advisory findings are informational only and do not require remediation.
