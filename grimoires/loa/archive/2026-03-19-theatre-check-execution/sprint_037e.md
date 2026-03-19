# Sprint Plan — Cycle-037e: Theatre Check Execution

**Cycle:** cycle-037e
**Date:** 19 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Execution Models + Fixture Loader

**Goal:** Define deterministic execution result shapes and fixture ingestion before runner logic starts.

### Tasks

1. Add theatre execution schemas
2. Add repo fixture loader for TREMOR and CORONA
3. Add fixture parsing tests

**Exit:** ~10 tests pass.

---

## Sprint 1 — Core Theatre Runner

**Goal:** Execute the four theatre-specific check families deterministically.

### Tasks

1. Add settlement accuracy execution
2. Add oracle consistency execution
3. Add calibration validity recomputation
4. Add functional correctness execution
5. Write runner tests across pass/fail/skip cases

**Exit:** ~14 tests pass.

---

## Sprint 2 — Certificate Integration

**Goal:** Thread executed theatre results into the existing construct run / certificate path.

### Tasks

1. Call theatre runner from the contract/certificate flow
2. Project executed results into stored certificate artifacts
3. Preserve readiness semantics for skipped critical coverage
4. Write integration tests

**Exit:** ~10 tests pass.

---

## Sprint 3 — TREMOR + CORONA Fixtures + Regression

**Goal:** Prove the execution layer works against real external theatre constructs.

### Tasks

1. Run end-to-end fixture execution for TREMOR
2. Run end-to-end fixture execution for CORONA
3. Add one failing/partial-coverage fixture per repo
4. Run regression against non-theatre construct paths

**Exit:** ~10 tests pass.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Execution models + fixture loader | 10 |
| 1 | Core theatre runner | 14 |
| 2 | Certificate integration | 10 |
| 3 | TREMOR + CORONA fixtures + regression | 10 |
| **Total** | | **~44** |
