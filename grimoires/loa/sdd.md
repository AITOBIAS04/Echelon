# SDD — Cycle-039: External Theatre Operations

**Cycle:** cycle-039
**Date:** 19 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

Cycle 039 adds the operational shell around the already-working external theatre pipeline:

```
external theatre registry
    ↓
scheduled or triggered preparation + scan run
    ↓
038b orchestration
    ↓
038c classification
    ↓
persisted operational run record
    ↓
builder-facing status/report surface
```

This cycle is about persistence, repeatability, and visibility.

---

## 2. File-Level Design

### 2.1 External Theatre Registry Model

**Add: registry persistence model / table**

Suggested fields:

- `id`
- `slug`
- `version`
- `construct_class`
- `repo_path`
- `construct_json_path`
- `status`
- `is_active`
- `last_prepared_at`
- `last_scanned_at`
- `latest_summary_json`

The exact storage surface can be a new table or a stable existing JSON-backed operational model, but a dedicated table is preferred.

### 2.2 External Theatre Run Model

**Add: operational run persistence model / table**

Suggested fields:

- `id`
- `external_theatre_ids`
- `started_at`
- `completed_at`
- `status`
- `spec_hash`
- `contract_hash`
- `preparation_summary_json`
- `scan_summary_json`
- `result_counts_json`

This becomes the history of recurring operation.

### 2.3 Operations Service

**Add: `backend/services/external_theatre_operations_service.py`**

Responsibilities:

- register/unregister external theatres
- trigger a preparation + scan run
- persist run outcomes
- expose latest status/report views

This service should be a composition layer, not a reimplementation layer.

Explicit boundary:

- call the 038b orchestrator for preparation
- call the 038c scan adapter/runner for classification
- persist the resulting operational record

It should not duplicate orchestration logic, candidate generation, or scan logic locally.

### 2.4 Invocation Surface

**Add internal trigger surface only**

V1 should use a lightweight internal service method with a stable signature that a scheduler or operator job can call.

Do not add public or admin API routes in V1.

Idempotence contract:

- if an equivalent run is already `IN_PROGRESS`, the trigger path returns the active run record or a stable duplicate-run status
- inactive theatres cannot be triggered
- the operations service owns this guard before it calls 038b/038c

### 2.5 Reporting Surface

**Add reporting schema/service**

Responsibilities:

- latest status summary
- recent run history
- latest paradox/no-paradox outcomes
- builder feedback rollup

Builder feedback rollup means:

- persist the 038b required/optional/extraction feedback items
- aggregate them across recent runs
- surface latest status plus repeated fallback patterns
- do not invent a second independent feedback taxonomy

---

## 3. Risks and Mitigations

### 3.1 Too Much Platform Surface Too Early

If 039 tries to build a full marketplace/portal, it will sprawl.

Mitigation:

- focus on registry, runs, and reporting
- keep UI/API thin

### 3.2 Registry Without Good Run History

A registry alone is low value if there is no persisted operational evidence.

Mitigation:

- run records are first-class in V1

### 3.3 Confusing “No Paradox” With “No Data”

The operational layer must distinguish successful quiet scans from failed or absent runs.

Mitigation:

- explicit run status and result summaries
- explicit no-paradox outcome counts

---

## 4. Files Touched Summary

**New likely files**

- registry model / migration
- run model / migration
- `backend/services/external_theatre_operations_service.py`
- reporting schemas / services
- operational tests

**Existing likely integrated**

- `backend/services/external_theatre_orchestrator.py`
- `backend/services/external_theatre_scan_adapter.py`

**Cycle numbering note**

The pending cycle-numbering discrepancy between the OSINT pipeline and the Loa ledger must be explicitly resolved or deferred in the implementation metadata before this cycle is filed.

---

## 5. After This Cycle Ships

1. TREMOR and CORONA can be treated as ongoing managed external theatres
2. Echelon has persistent operational history for external theatre runs
3. builder feedback becomes a stable product surface instead of an ad hoc review step
