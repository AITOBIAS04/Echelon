# SDD — Cycle-037e: Theatre Check Execution

**Cycle:** cycle-037e
**Date:** 19 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

Cycle 037e adds the deterministic execution layer that sits between theatre contract planning and certificate issuance:

```
theatre construct repo
    ↓
037 / 037d contract compilation
    ↓
planned theatre checks
    ↓
theatre execution runner
    ↓
executed theatre check results
    ↓
certificate builder / issuance path
```

This is not a replacement for the 037 substrate. It is the runtime that makes the theatre-specific check families real.

---

## 2. File-Level Design

### 2.1 Theatre Runner Models

**Add: `backend/schemas/theatre_execution.py`**

Responsibilities:

- request/response models for theatre check execution
- per-check execution result shape
- oracle/evidence provenance fields
- explicit status model for `SUPPORTED`, `EXECUTED`, `PASSED`, `FAILED`, `SKIPPED`

Suggested core types:

- `TheatreExecutionRequest`
- `TheatreExecutionResult`
- `TheatreCheckExecutionResult`

### 2.2 Theatre Check Runner

**Add: `backend/services/theatre_check_runner.py`**

Responsibilities:

- dispatch by `check_type`
- execute deterministic theatre checks
- return structured execution results with provenance
- never infer execution from existing scores

Dispatch families:

- `SETTLEMENT_ACCURACY`
- `ORACLE_CONSISTENCY`
- `CALIBRATION_VALIDITY`
- `FUNCTIONAL_CORRECTNESS`

### 2.3 Oracle / Fixture Adapters

**Add: `backend/services/theatre_fixture_loader.py`**

Responsibilities:

- load TREMOR / CORONA fixture inputs from repo-local metadata or test assets
- provide normalized replay inputs to the runner
- isolate repo-specific fixture shape from the generic runner

V1 should prefer repo fixtures and deterministic replay over live network calls.

### 2.4 Deterministic Execution Methods

**Update or add helper surfaces under `backend/services/`**

Execution methods:

- `execute_settlement_accuracy()`
  - replay known event/theatre outcome against expected oracle result
- `execute_oracle_consistency()`
  - compare primary and cross-validation source records
- `execute_calibration_validity()`
  - recompute Brier/calibration outputs from stored predictions and outcomes
- `execute_functional_correctness()`
  - validate template-level deterministic transformations or state-machine outputs

These may live inside `theatre_check_runner.py` or split into narrowly-scoped helpers if that reads better.

### 2.5 Certificate Integration

**Update: existing certificate builder / construct issuance path**

Responsibilities:

- call the theatre runner when theatre-specific planned checks are present
- merge execution results into check-plan reporting
- preserve 037 issuance semantics
- ensure stored certificate artifacts reflect final executed state

Required behavior:

- executed theatre checks must not remain `NOT_EXECUTED`
- unsupported or missing-fixture paths must become `SKIPPED` with explicit reasons
- critical skipped theatre checks must influence readiness truthfully

### 2.6 Fixture Coverage

**Add tests / fixture inputs for both external theatre repos**

Required fixture coverage:

- TREMOR settlement replay
- TREMOR oracle consistency replay
- CORONA settlement replay
- CORONA calibration replay
- at least one failing or skipped case per family

---

## 3. Risks and Mitigations

### 3.1 Accidental Live-Network Dependence

If theatre execution depends on live oracle feeds for tests, the cycle becomes flaky.

Mitigation:

- V1 uses deterministic replay fixtures first
- live-oracle execution may exist behind a separate adapter later

### 3.2 Conflating Runner Output With Scorer Output

Theatre execution is deterministic and should not be modeled as soft rubric scoring.

Mitigation:

- keep runner and scorer language separate
- use deterministic status/result models

### 3.3 Repo-Specific Overfitting

TREMOR and CORONA have different metadata layouts and domain semantics.

Mitigation:

- normalize through 037d compile output
- keep repo-specific parsing in the fixture loader, not in the generic runner

### 3.4 Incorrect Issuance Promotion

Executed theatre checks must not be allowed to silently degrade into ready certificates when critical checks are skipped.

Mitigation:

- reuse 037 readiness semantics
- ensure execution gaps are represented as real skipped coverage

---

## 4. Files Touched Summary

**New likely files**

- `backend/schemas/theatre_execution.py`
- `backend/services/theatre_check_runner.py`
- `backend/services/theatre_fixture_loader.py`
- theatre execution test modules

**Existing likely updated**

- contract/certificate integration surface
- construct issuance route
- certificate builder or execution integration service

---

## 5. After This Cycle Ships

1. theatre checks move from planned to executable
2. TREMOR and CORONA become real end-to-end verification fixtures
3. Cycle 038 can build on executed theatre evidence rather than planned-only metadata
