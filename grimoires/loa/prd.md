# PRD — Cycle-038a: Theatre Execution Fixtures For Cross-Theatre Paradox

**Cycle:** cycle-038a
**Date:** 19 March 2026
**Depends on:** Cycle-037d, Cycle-037e, Cycle-038
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Planning source:** TREMOR and CORONA now compile as external theatre constructs; 037e executes local deterministic checks; 038 needs executed fixture data rather than planned-only metadata

---

## 1. Problem Statement

### 1.1 Planned Theatres Are Not Enough For Strong Cross-Theatre Review

Cycle 038 defines the cross-theatre paradox model:

- linker
- contradiction classes
- paradox records
- resolution policy

That is the right network layer.

But cross-theatre comparison is materially stronger when it operates on **executed local theatre evidence** rather than only planned contract metadata.

### 1.2 The Missing Bridge Is Executed Cross-Theatre Fixture Material

After 037e, Echelon will have:

- executed `SETTLEMENT_ACCURACY`
- executed `ORACLE_CONSISTENCY`
- executed `CALIBRATION_VALIDITY`
- executed `FUNCTIONAL_CORRECTNESS`

for individual theatre constructs such as TREMOR and CORONA.

What still needs to exist is a clean bridge from those executed results into cross-theatre comparison inputs:

- normalized comparison bundles
- shared fixture records
- same-event and overlap-scope candidate sets
- provenance snapshots suitable for paradox classification

### 1.3 The Goal Of 038a

Build the executed-fixture bridge that lets Cycle 038 compare theatre constructs using real local execution results.

This cycle should make TREMOR and CORONA the first canonical comparison fixtures for the cross-theatre layer, even if the initial contradiction set is intentionally small.

---

## 2. Product Contracts

### 2.1 Executed Theatre Comparison Bundle

Cycle 038a must define a normalized bundle that represents a theatre’s executed local verification state for comparison purposes.

Minimum contents:

- construct slug / version / certificate ref
- template id / theatre id
- executed theatre check results
- oracle source ids and roles
- event or scope keys
- settlement timing / maturity state
- confidence / discounting signals when available

### 2.2 TREMOR And CORONA As Canonical Comparison Fixtures

Cycle 038a must materialize reusable comparison fixtures from:

- `TREMOR`
- `CORONA`

These fixtures should be stable, deterministic, and suitable for both local regression and later paradox-layer testing.

### 2.3 Same-Event And Overlap-Scope Candidate Sets

This cycle does not need to re-implement the full linker from 038, but it should produce comparison-ready candidate inputs:

- same-event candidate bundles
- overlap-scope candidate bundles

This is the substrate the paradox engine can consume cleanly.

### 2.4 Provenance Snapshot For Comparison

The comparison bundle must snapshot the local execution provenance needed for later paradox interpretation:

- executed vs skipped critical checks
- local settlement result
- local oracle consistency summary
- local calibration summary
- linkable event/scope metadata

### 2.5 Deterministic Fixture-First Design

Cycle 038a should remain fixture-first:

- deterministic replay inputs
- repo-backed or synthesized fixture outputs
- no live network dependency

---

## 3. What This Cycle Does NOT Do

- **Does NOT replace Cycle 038 paradox detection.**
- **Does NOT redesign the event/entity linker.**
- **Does NOT require full contradiction classification across every theatre pair.**
- **Does NOT add new theatre check families.**

---

## 4. Acceptance Criteria

1. A normalized executed-theatre comparison bundle exists
2. TREMOR executed outputs can be materialized into comparison fixtures
3. CORONA executed outputs can be materialized into comparison fixtures
4. Same-event and overlap-scope candidate fixture sets can be produced deterministically
5. Comparison bundles preserve local execution provenance needed by Cycle 038
6. At least one TREMOR↔CORONA comparison fixture path exists for regression, even if it does not yield a material paradox yet
7. ≥28 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Comparison bundle schemas | 4 | shape, provenance, event/scope keys |
| Fixture materialization | 6 | TREMOR and CORONA executed outputs to bundles |
| Candidate-set generation | 6 | same-event, overlap-scope, no-match |
| Provenance projection | 4 | local execution summaries preserved |
| Regression into 038 surfaces | 6 | paradox engine can consume bundle shape without special-casing |
| End-to-end fixtures | 4 | TREMOR↔CORONA executed comparison path |
| **Total** | **~30** | |

---

## 6. Why This Matters

Cycle 038 makes the Paradox Engine a network integrity layer.

Cycle 038a makes that network layer operate on stronger local truth:

- not just planned contract requirements
- not just raw repo metadata
- but executed local deterministic verification results

That is the cleaner foundation for cross-theatre coherence.
