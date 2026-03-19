# Sprint Plan — Cycle-037b: Multi-Evaluator Orchestration + Residual Scoring

**Cycle:** cycle-037b
**Date:** 18 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Schemas + Residual Filtering

**Goal:** Define orchestration schemas and ensure deterministic-covered dimensions are excluded from scorer execution.

### Tasks

1. Add orchestration schemas
2. Add residual dimension filter
3. Write tests for deterministic-vs-rubric separation

**Exit:** ~8 tests pass.

---

## Sprint 1 — Evaluator Adapter + Orchestrator

**Goal:** Execute 3 scorers over the residual dimension set.

### Tasks

1. Add scorer adapter interface
2. Add evaluator orchestrator
3. Write tests for 3-scorer invocation and output normalization

**Exit:** ~7 tests pass.

---

## Sprint 2 — Convergence Policy + Persistence

**Goal:** Compute convergence outcomes and persist the judging trace.

### Tasks

1. Add convergence policy
2. Persist per-evaluator and summary data
3. Write tests for 3/3, 2/3, divergent, and skipped cases

**Exit:** ~7 tests pass.

---

## Sprint 3 — Route / Certificate Integration + Regression

**Goal:** Wire orchestration into issuance and keep Cycle 037 semantics intact.

### Tasks

1. Integrate with construct issuance path
2. Preserve `DEFERRED` for missing coverage only
3. Add regression tests for old construct path behavior

**Exit:** ~6 tests pass.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Schemas + residual filtering | 8 |
| 1 | Adapter + orchestrator | 7 |
| 2 | Convergence + persistence | 7 |
| 3 | Route integration + regression | 6 |
| **Total** | | **~28** |
