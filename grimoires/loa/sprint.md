# Sprint Plan — Cycle-039: External Theatre Operations

**Cycle:** cycle-039
**Date:** 19 March 2026
**Builder:** Loa
**Sprints:** 5 (0–4)

---

## Sprint 0 — Registry Models + Schemas

**Goal:** Define persistent external theatre registry and run-record shapes.

### Tasks

1. Add registry persistence model
2. Add run-record persistence model
3. Add schemas and migrations
4. Write model/schema tests

**Exit:** ~8 tests pass.

---

## Sprint 1 — Operations Service

**Goal:** Build the service that registers theatres and persists orchestration/scan runs.

### Tasks

1. Add operations service as a composition layer over 038b + 038c
2. Register/unregister external theatres
3. Persist run records including `spec_hash` / `contract_hash`
4. Write service tests

**Exit:** ~8 tests pass.

---

## Sprint 2 — Trigger / Scheduling Surface

**Goal:** Make external theatre runs invokable through a first-class surface.

### Tasks

1. Add internal trigger method with stable scheduler-facing signature
2. Add manual trigger path through the same service boundary
3. Enforce idempotence / active-state rules
4. Write invocation tests

**Exit:** ~8 tests pass.

---

## Sprint 3 — Reporting Surface

**Goal:** Expose latest status, run history, and builder-facing summaries.

### Tasks

1. Add latest-status reporting
2. Add recent-run summaries
3. Add persisted 038b feedback rollups
4. Write reporting tests

**Exit:** ~8 tests pass.

---

## Sprint 4 — TREMOR + CORONA Operational Regression

**Goal:** Prove the operations layer works for the first external theatre pair.

### Tasks

1. Register TREMOR and CORONA
2. Run persisted orchestration + scan cycles
3. Verify stored no-paradox/paradox summaries
4. Run regression tests

**Exit:** ~8 tests pass.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Registry models + schemas | 8 |
| 1 | Operations service | 8 |
| 2 | Trigger / scheduling surface | 8 |
| 3 | Reporting surface | 8 |
| 4 | TREMOR + CORONA operational regression | 8 |
| **Total** | | **~40** |
