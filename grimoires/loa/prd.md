# PRD — Cycle-039: External Theatre Operations

**Cycle:** cycle-039
**Date:** 19 March 2026
**Depends on:** Cycle-038b, Cycle-038c
**Sprints:** 5 (0–4)
**Builder:** Loa (backend only)
**Planning source:** TREMOR and CORONA now compile, execute, compare, and classify; the next step is to make external theatres ongoing network participants rather than one-off fixtures

---

## 1. Problem Statement

### 1.1 The External Theatre Stack Now Works End To End

By the end of Cycle 038c, Echelon can:

- ingest external theatre metadata
- extract deterministic fixtures
- execute theatre checks
- build comparison bundles
- generate cross-theatre candidates
- classify those candidates through the scanner path

That is a major milestone.

### 1.2 The Remaining Gap Is Operational Reality

Today this still behaves like a project workflow:

- choose repos
- run orchestration
- inspect results

What is still missing is the layer that makes external theatres part of the living network:

- persistent registration
- recurring scan schedules
- stored run history
- builder-visible status and reports

### 1.3 The Goal Of 039

Turn external theatre verification from a manually-invoked flow into an operational system.

Cycle 039 should make external theatres like TREMOR and CORONA feel like first-class network participants with:

- a registry entry
- an operational status
- recurring preparation + scan runs
- persisted results
- builder-facing feedback surfaces

---

## 2. Product Contracts

### 2.1 External Theatre Registry

Cycle 039 must add a persistent registry for external theatres.

Minimum fields:

- slug
- version
- repo path or artifact path
- construct class
- active status
- last prepared at
- last scanned at
- last result summary

This is the system of record for ongoing operation.

### 2.2 Operational Run Records

Each orchestration + scan cycle should persist an operational run record.

Minimum contents:

- theatre set involved
- execution timestamp
- `spec_hash`
- `contract_hash`
- preparation success/failure counts
- candidate count
- scan outcomes summary
- top-level paradox/no-paradox result counts

### 2.3 Scheduling Surface

Cycle 039 must provide a first-class way to run external theatre scans repeatedly.

V1 should be:

- an internal service method with a stable signature
- callable from a cron job, scheduler, or manual operator trigger

It should not add public/admin API surface in V1.

The key requirement is that external theatres can be scanned repeatedly without manual test-style wiring.

Idempotence contract:

- if a run is already `IN_PROGRESS` for the same theatre set, a second trigger should not create a duplicate live run
- repeated triggers may either return the active run or reject with a stable operational status
- active/inactive theatre status must be enforced before orchestration begins

### 2.4 Builder-Facing Reporting

Cycle 039 should expose a structured reporting surface for builders like El Captain.

Minimum V1 report contents:

- latest readiness state
- latest preparation result
- latest scan summary
- enrichment recommendations
- recent paradox findings or explicit no-paradox result

The builder feedback rollup is not a new feedback model. It is the persisted and aggregated form of the 038b feedback surface across operational runs, so builders can see:

- latest required/optional metadata status
- repeated extraction fallbacks
- whether feedback is improving or stable across runs

### 2.5 No-Paradox Is A Positive Operational State

The operational layer must make “no paradox found” visible as a legitimate successful result, not just the absence of issues.

---

## 3. What This Cycle Does NOT Do

- **Does NOT redesign the paradox scanner.**
- **Does NOT require live oracle polling for V1 scheduling.**
- **Does NOT move builder feedback into the external repos themselves.**
- **Does NOT replace existing construct/certificate flows.**

---

## 4. Acceptance Criteria

1. External theatres can be registered persistently for operations
2. An operational run record exists for orchestration + scan cycles
3. TREMOR and CORONA can be scheduled or invoked through a first-class operations surface
4. Latest run status and findings can be retrieved without rerunning the whole pipeline manually
5. Builder-facing report summaries exist for external theatres
6. No-paradox and paradox outcomes are both represented clearly in the operational record
7. Regression confirms existing 037-family contract/execution paths still work cleanly alongside operations
8. Cycle numbering discrepancy is explicitly resolved or deferred in the cycle metadata before implementation starts
9. ≥34 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| External theatre registry | 8 | create, update, list, active/inactive |
| Operational run records | 8 | persist prep + scan summaries, error handling |
| Scheduling/invocation surface | 8 | manual trigger, scheduler-facing service signature, idempotence, active-state rules |
| Builder reporting | 8 | latest status, findings, persisted 038b feedback rollup |
| TREMOR + CORONA operations | 8 | real fixture participants in stored runs |
| Regression | 4 | no breakage to 038b/038c behavior |
| **Total** | **~40** | |

---

## 6. Why This Matters

Cycle 039 is where the external theatre network starts to feel real as infrastructure rather than as a successful demo chain.

It gives Echelon:

- a registry
- an operations layer
- persisted history
- builder-visible trust surfaces

That is the step from “we can verify external theatres” to “we operate an external theatre network.”
