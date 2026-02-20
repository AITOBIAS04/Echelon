# Sprint 8 (sprint-12) — Code Review Feedback

**Reviewer**: Senior Technical Lead
**Date**: 2026-02-19
**Decision**: APPROVED (with minor notes)

---

## Summary

Sprint 8 delivers a solid cross-repository invariant infrastructure. The schema, declarations, verification script, and BATS tests are all well-structured and pass verification. Tasks 8.5/8.6 (eval regression) are appropriately deferred — the analysis script exists but requires upstream eval infrastructure.

**All good.** Proceed to `/audit-sprint sprint-8`.

---

## Detailed Review

### Task 8.1: invariants.schema.json — PASS

- JSON Schema draft 2020-12 compliant
- `additionalProperties: false` at all levels prevents schema drift
- `id` pattern `^INV-[0-9]{3}$` enforces consistent naming
- `minLength: 10` on description prevents stub entries
- `minItems: 1` on `verified_in` ensures every invariant is grounded

No issues.

### Task 8.2: invariants.yaml — PASS

- 5 invariants covering the critical economic properties (conservation, non-negative spend, deduplication, monotonicity, trust boundary)
- 17 `verified_in` references, all verified by `verify-invariants.sh` (17/17 PASS)
- `protocol: loa-hounfour@7.0.0` traceability annotation present
- Property expressions are clear and mathematically precise

No issues.

### Task 8.3: verify-invariants.sh — PASS (minor note)

- Robust symbol detection: Python (def/class), YAML (top-level key), Shell (function), generic fallback
- JSON output mode works correctly (`--json` implies `--quiet`)
- Exit codes 0/1/2 properly differentiated
- Cross-repo references correctly SKIPped

**Minor note**: AC item "Integrates with `quality-gates.bats` as an optional check" is unchecked. Not blocking — quality-gates.bats doesn't exist in this repo. Can be wired when moved upstream.

**Minor note**: YAML key detection (`^${REF_SYMBOL}:`) is anchored to line start — only matches top-level keys. All current invariants.yaml refs target top-level keys (e.g., `model_permissions`), so this is correct now. If nested key verification is needed later, the pattern would need enhancement.

### Task 8.4: invariant-verification.bats — PASS (minor note)

- 14 test cases covering all 6 acceptance criteria
- Good test isolation: each test creates its own invariants YAML in `$TEST_DIR`
- Covers text mode, JSON mode, exit codes, mixed results, cross-repo skip
- The `exit code 2 for unsupported schema version` test catches the edge case of schema evolution

**Minor note**: `setup()` creates `$TEST_DIR/src/example.py` and `$TEST_DIR/src/config.yaml` which are not used by any test. These are dead fixtures that should be removed in a future cleanup pass.

**Note**: reviewer.md claims "19/19 tests" but the current file has 14 tests. The reviewer.md reflects a prior implementation version. Not a blocking discrepancy — the current 14 tests cover all ACs.

### Tasks 8.5/8.6: Eval Regression — APPROPRIATELY DEFERRED

The analysis script is structurally sound. The deferral is correct — `evals/` directory with harness and regression tasks exists upstream only. Well-documented in NOTES.md.

---

## Acceptance Criteria Checklist

| AC | Status |
|----|--------|
| Schema defines invariants array with id, description, properties, verified_in | PASS |
| Schema validates severity and category enums | PASS |
| JSON Schema draft 2020-12 compatible | PASS |
| 5 invariants declared with correct severity/category | PASS |
| Cross-repo references annotated with protocol version | PASS |
| verify-invariants.sh reads YAML and verifies refs | PASS |
| Cross-repo refs SKIPped | PASS |
| Exit codes 0/1/2 correct | PASS |
| BATS tests cover all 6 criteria | PASS |
| Eval analysis script structurally complete | PASS |

---

## Status: REVIEW_APPROVED
