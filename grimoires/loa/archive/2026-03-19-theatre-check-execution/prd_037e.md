# PRD — Cycle-037e: Theatre Check Execution

**Cycle:** cycle-037e
**Date:** 19 March 2026
**Depends on:** Cycle-037, Cycle-037b, Cycle-037d
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Planning source:** TREMOR and CORONA validated as external theatre constructs that compile cleanly but do not yet execute planned theatre checks

---

## 1. Problem Statement

### 1.1 Theatre Contracts Now Compile, But They Do Not Execute

Cycle 037d proved that theatre constructs can compile into valid `EvaluationContract` artifacts with theatre-specific planned checks:

- `SETTLEMENT_ACCURACY`
- `ORACLE_CONSISTENCY`
- `CALIBRATION_VALIDITY`
- `FUNCTIONAL_CORRECTNESS`

That is necessary, but not sufficient.

Today those checks are planned and then remain `NOT_EXECUTED` in the certificate path because no theatre-aware execution layer exists.

### 1.2 The Missing Layer Is Deterministic Execution

For theatre constructs, the strongest part of the model is that execution can be deterministic:

- replay settlement against public oracle data
- recompute Brier / calibration math
- compare cross-validation oracle records
- run pure-function validation against declared template logic

The missing system is not another scorer in the generic sense. It is a deterministic theatre check runner.

### 1.3 The Goal Of 037e

Make planned theatre checks executable and project real execution results into certificate provenance.

Cycle 037e should make TREMOR and CORONA the first real end-to-end theatre verification fixtures:

- register construct
- compile contract
- execute theatre checks
- persist results
- issue a deterministic-first certificate with theatre checks marked `EXECUTED`

---

## 2. Product Contracts

### 2.1 Executable Theatre Check Families

Cycle 037e must execute the four theatre-specific families introduced in 037d:

- `SETTLEMENT_ACCURACY`
- `ORACLE_CONSISTENCY`
- `CALIBRATION_VALIDITY`
- `FUNCTIONAL_CORRECTNESS`

### 2.2 Deterministic Status Model

Each theatre check must project one explicit execution state:

- `PLANNED`
- `SUPPORTED`
- `EXECUTED`
- `PASSED`
- `FAILED`
- `SKIPPED`

V1 may continue to store these through the existing check-plan / certificate surfaces, but the semantics must reflect real execution rather than inferred execution.

### 2.3 TREMOR And CORONA As Canonical Fixtures

Cycle 037e must execute theatre checks against both external fixtures:

- `TREMOR`
- `CORONA`

This is important because the parser already proved it can normalize two different metadata layouts. The execution layer should prove it can operate across both without special-casing.

### 2.4 Deterministic-First Issuance

Theatre execution should preserve the Cycle 037 distinction between readiness and judgement:

- missing execution coverage blocks issuance or keeps checks `SKIPPED`
- executed deterministic failures surface as real failures
- no LLM rubric path should be required for theatre-specific deterministic claims

### 2.5 Certificate Projection

Theatre execution results must appear in certificate output and provenance with enough detail to audit:

- which theatre templates were executed
- which oracle sources were queried or replayed
- what evidence window was used
- what arithmetic/calibration result was recomputed
- pass/fail/skip status per theatre check

---

## 3. What This Cycle Does NOT Do

- **Does NOT add cross-theatre paradox detection.** That remains Cycle 038.
- **Does NOT redesign contract compilation.** 037d already proved the compile path.
- **Does NOT require rubric scoring for theatre claims.** This remains deterministic-first.
- **Does NOT depend on security/domain pack logic.**

---

## 4. Acceptance Criteria

1. Theatre-specific planned checks can be executed through a deterministic runtime path
2. `SETTLEMENT_ACCURACY`, `ORACLE_CONSISTENCY`, `CALIBRATION_VALIDITY`, and `FUNCTIONAL_CORRECTNESS` each have at least one real execution path
3. TREMOR executes theatre checks end-to-end and persists results into certificate provenance
4. CORONA executes theatre checks end-to-end and persists results into certificate provenance
5. Certificates distinguish planned vs executed vs skipped theatre checks truthfully
6. Readiness / issuance semantics remain coherent when execution coverage is incomplete
7. ≥32 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Theatre runner schemas | 5 | request/result models, deterministic status projection |
| Settlement accuracy execution | 8 | pass, fail, skipped, window/oracle variants |
| Oracle consistency execution | 6 | cross-validation convergence, divergence, missing source |
| Calibration validity execution | 5 | binary and multi-class Brier recomputation |
| Functional correctness execution | 5 | template-level deterministic function checks |
| Certificate integration | 5 | executed results projected into stored certificate artifacts |
| TREMOR + CORONA fixtures | 6 | end-to-end execution across both repos |
| Regression | 4 | no breakage to non-theatre construct paths |
| **Total** | **~44** | |

---

## 6. Why This Matters

Cycle 037d proved that theatre constructs fit the contract model.

Cycle 037e is the step that makes those contracts operational.

Once it ships, Echelon no longer merely says “these theatre checks should run.” It can say “they ran, here is the evidence, and here is the deterministic certificate output.”
