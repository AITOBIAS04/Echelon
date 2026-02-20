# Project Notes

## Learnings

- **Invariant verification is local-only**: The `verify-invariants.sh` script validates `verified_in` references against the local codebase only. Cross-repo references (hounfour, arrakis) are SKIPped with a note — they're verified in their respective CIs.
- **Mounted Loa context**: `.claude/` directory is mounted from upstream Loa framework via `mount-loa.sh`. The `evals/` directory and eval harness infrastructure exist in the upstream repo, not this prediction market monorepo.

## Blockers

- **Tasks 8.5/8.6 (Eval Regression Analysis)**: The eval harness (`evals/harness/run-eval.sh`) and regression task definitions (`evals/tasks/regression/*.yaml`) exist in the upstream Loa repo (0xHoneyJar/loa), not in this mounted context. The analysis script (`.claude/scripts/tests/eval-regression-analysis.sh`) is structurally complete but requires upstream eval infrastructure to execute. **Action**: Run eval-regression-analysis.sh in the upstream Loa repo when eval infrastructure is available.

## Observations

- **Sprint 8 progress (2026-02-19)**: Tasks 8.1-8.3 fully implemented and verified (17/17 invariant checks pass). Task 8.4 (BATS tests) implemented. Tasks 8.5-8.6 deferred to upstream.
- **Invariant health**: All 5 cross-repository invariants (INV-001 through INV-005) pass verification against the local codebase. Conservation, non-negative spend, deduplication, budget monotonicity, and trust boundary invariants all have valid source references.
