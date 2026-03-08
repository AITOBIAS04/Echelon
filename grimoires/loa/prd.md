# PRD — Cycle-021: Investigation Certificate Lifecycle + Domain Filter Enforcement

**Cycle:** cycle-021
**Date:** 7 March 2026
**Depends on:** Cycle-020 (Scenario Pack Evaluator v2 + Paradox Risk Orchestration), Cycle-019 (Investigation Persistence + Paradox Risk), Cycle-014c (Investigation Toolset)
**Builder:** Loa (backend/runtime only — Alexander consumes APIs)
**Scope:** 4 items, narrowly focused on the investigation certificate pipeline

> Sources: echelon_cycle_021.md:61,122-123,178-181,212-214,219-222,288-290; codebase exploration of investigation/, api/investigation_routes.py, database/models.py

---

## 1. Problem Statement

Investigations can be created, evidence submitted, claims registered, and certificates built. But the certificate pipeline has 4 production gaps:

1. **Domain filters are stored but not enforced.** Evidence submitted to an investigation is accepted regardless of whether the source domain matches the committed domain filters. The commitment surface is incomplete — a committed investigation can silently ingest out-of-scope evidence.

2. **Drift is a routing signal but not a stop condition input.** Material drift forces REVIEW_REQUIRED at certificate build time, but it doesn't trigger automated stop condition evaluation. Drift can occur at any time, but the system only notices it when someone manually requests a certificate.

3. **Certificate lifecycle has no intermediate states.** Calling `GET /certificate` immediately builds, persists, and completes the investigation in one step. There is no readiness check, no separation between "ready to issue" and "issued", and no operator confirmation gate.

4. **No batch anchor.** Certificate issuance is instantaneous. The product requires that `issued_at` only be set during the daily batch anchor window at 00:00 UTC. Readiness may precede issuance by hours.

## 2. Goals & Success Metrics

| Goal | Metric |
|------|--------|
| Domain filter enforcement | Evidence/signal submission to a committed investigation rejects or explicitly flags items from sources outside the committed domain scope. Zero silent ingestion of out-of-scope items. |
| Drift-triggered stop evaluation | Material drift events from `CommitmentMonitor` trigger automated stop condition evaluation. If drift causes a stop condition change, the investigation's stop status updates without manual intervention. |
| Three-state certificate lifecycle | Certificate records transition through READY → ANCHORED → ISSUED with persisted timestamps and reasons at each stage. No state can be skipped. |
| Daily batch anchor | `issued_at` is only set during the 00:00 UTC batch window. Certificates that become READY at 14:00 UTC are not ISSUED until 00:00 UTC. The batch job is idempotent. |

**Success bar:** All 4 items must be verifiable with tests. No staged behavior — each item either works in production or the docs say it doesn't.

## 3. Users & Stakeholders

| Persona | Interaction |
|---------|-------------|
| Investigation operator | Submits evidence, registers claims, monitors stop conditions. Expects domain filter violations to be caught, not silently accepted. |
| Certificate consumer | Receives issued certificates. Expects READY/ANCHORED/ISSUED to mean what they say. |
| Automated pipeline | Evaluates stop conditions after mutations. Runs daily batch anchor. |
| Alexander (frontend) | Consumes certificate readiness state and lifecycle transitions via API + WebSocket. |

## 4. Functional Requirements

### FR-1: Domain Filter Enforcement at Ingestion

**What exists:** `Investigation.domain_filters_json` stores committed domain filters. `SignalScanner` uses them for OSINT scans. Evidence submission endpoint does not check them.

**What must change:**

- When evidence is submitted to a committed investigation (via `POST /{id}/evidence`), validate that the evidence source is within the committed domain filters
- "Committed" means the investigation has `domain_filters_json` set and non-empty
- If domain filters are empty or the investigation has no commitment surface, evidence passes through (backward compatible)
- If evidence source falls outside committed domain filters: reject with 422 and clear error message
- Domain filter validation must also apply to signal ingestion paths (counter-signals, scanner output)
- The validation function must be reusable — not duplicated across endpoints

**Acceptance criteria:**
- Evidence from in-scope domain: accepted
- Evidence from out-of-scope domain: rejected with 422
- Evidence to investigation with empty domain filters: accepted (no enforcement)
- Signal from out-of-scope domain: rejected with 422
- Domain filter set is part of commitment hash (already true — verify)

### FR-2: Drift as First-Class Stop Condition Input

**What exists:** `CommitmentMonitor.has_material_drift()` returns True when any drift event has MATERIAL impact. Certificate builder checks this for REVIEW_REQUIRED routing. `InvestigationStopConditionEvaluator` exists but is never called automatically.

**What must change:**

- After a drift event is logged (via `POST /{id}/drift` or internal drift detection), automatically evaluate stop conditions
- Material drift is an additional stop condition input: if material drift is present, the stop condition evaluation must include it as a factor
- Stop condition evaluation result must be persisted on the investigation record
- If stop condition evaluation determines the investigation is ready for resolution, transition the investigation to a "ready for certificate" state
- Stop condition evaluation must also run after: evidence submission, claim status change, counter-signal ingestion (all material mutation paths)
- Readiness reasoning must record whether drift, evidence, or outcome state triggered readiness

**Acceptance criteria:**
- Material drift event triggers stop condition evaluation
- Stop condition evaluation result is persisted (ready/not-ready + reason)
- Readiness reasoning includes drift state when drift is material
- Evidence submission triggers stop condition evaluation
- Counter-signal ingestion triggers stop condition evaluation
- Non-material drift does not force readiness

### FR-3: Certificate Lifecycle READY → ANCHORED → ISSUED

**What exists:** `InvestigationCertificateRecord` has `anchoring_status` ("pending"/"anchored"). Certificate is built and investigation is COMPLETED in a single endpoint call.

**What must change:**

- Add `certificate_status` field to `InvestigationCertificateRecord` with three states:
  - `READY` — stop conditions satisfied, certificate hash computed, awaiting batch anchor
  - `ANCHORED` — certificate included in daily batch, anchor hash confirmed
  - `ISSUED` — `issued_at` set, certificate is final and immutable
- `READY` transition: happens when stop conditions are satisfied AND certificate is built
  - Sets `ready_at` timestamp
  - Does NOT set `issued_at`
  - Investigation status becomes `CERTIFICATE_READY` (not `COMPLETED`)
- `ANCHORED` transition: happens during the daily batch anchor job
  - Sets `anchored_at` timestamp
  - Sets batch_anchor_hash for v1 local anchor
- `ISSUED` transition: happens after anchoring confirms
  - Sets `issued_at` timestamp
  - Investigation status becomes `COMPLETED`
- Existing certificate endpoint must be refactored: `GET /{id}/certificate` returns current state; `POST /{id}/certificate/build` triggers the READY transition
- No state can be skipped: READY → ANCHORED → ISSUED is the only valid path

**Acceptance criteria:**
- Certificate can be in READY state without being ISSUED
- READY certificates have `ready_at` but no `issued_at`
- ANCHORED certificates have `anchored_at` and anchor hash
- ISSUED certificates have `issued_at`
- Investigation is COMPLETED only after ISSUED
- Attempting to skip states raises ValueError

### FR-4: Daily Batch Anchor at 00:00 UTC

**What exists:** Nothing. Certificates are issued immediately.

**What must change:**

- Implement a batch anchor service that processes all READY certificates
- The batch runs at 00:00 UTC (or is triggered manually for v1)
- Batch job:
  1. Query all certificates with `certificate_status = 'READY'`
  2. Compute batch anchor hash (SHA-256 of sorted certificate hashes)
  3. Transition each certificate to ANCHORED with the batch anchor hash
  4. Transition each certificate to ISSUED with `issued_at` = batch run timestamp
  5. Mark investigations as COMPLETED
- The batch job must be idempotent: running it twice in the same window produces the same result
- For v1, the batch anchor is a local hash anchor (not blockchain). The `anchoring_tx_hash` field stores the batch anchor hash.
- Emit `INVESTIGATION_CERTIFICATE_ISSUED` WebSocket event for each issued certificate

**Acceptance criteria:**
- READY certificates are not ISSUED until batch runs
- Batch computes anchor hash from all READY certificate hashes
- Batch transitions READY → ANCHORED → ISSUED atomically
- Batch is idempotent (second run is a no-op)
- `issued_at` is within the batch window, not certificate build time
- WebSocket event emitted per issued certificate

## 5. Technical & Non-Functional Requirements

### Database Changes

- Add `certificate_status` column to `investigation_certificate_records` (String, default 'READY')
- Add `ready_at` column (DateTime, nullable)
- Add `anchored_at` column (DateTime, nullable)
- Add `batch_anchor_hash` column (String, nullable)
- Add `stop_condition_status` column to `investigations` (String, nullable) — persists evaluation result
- Add `stop_condition_reason` column to `investigations` (String, nullable)
- Add `stop_condition_evaluated_at` column to `investigations` (DateTime, nullable)
- Alembic migration required

### New Services

| Service | File | Purpose |
|---------|------|---------|
| DomainFilterValidator | `backend/services/domain_filter_validator.py` | Reusable domain filter enforcement for evidence/signal ingestion |
| StopConditionOrchestrator | `backend/services/stop_condition_orchestrator.py` | Automatic stop condition evaluation after material mutations |
| CertificateLifecycleService | `backend/services/certificate_lifecycle_service.py` | READY/ANCHORED/ISSUED state machine + batch anchor |

### API Changes

| Endpoint | Change |
|----------|--------|
| `POST /{id}/evidence` | Add domain filter validation before acceptance |
| `POST /{id}/counter-signals` | Add domain filter validation |
| `POST /{id}/drift` | Trigger stop condition evaluation after persistence |
| `GET /{id}/certificate` | Return current certificate state (READY/ANCHORED/ISSUED) without building |
| `POST /{id}/certificate/build` | Build certificate and transition to READY (replaces current GET behavior) |
| `POST /certificates/anchor-batch` | Trigger daily batch anchor (admin/cron) |
| `GET /{id}/readiness` | Return stop condition evaluation status |

### WebSocket Events

| Event | Trigger |
|-------|---------|
| `INVESTIGATION_STOP_CONDITION_MET` | Stop condition evaluator determines readiness |
| `INVESTIGATION_CERTIFICATE_READY` | Certificate transitions to READY |
| `INVESTIGATION_CERTIFICATE_ISSUED` | Certificate transitions to ISSUED via batch |

## 6. Scope & Prioritization

### In Scope (4 items only)

1. Domain filter enforcement at evidence/signal ingestion
2. Drift as automated stop condition input
3. Certificate lifecycle READY → ANCHORED → ISSUED
4. Daily batch anchor at 00:00 UTC

### Explicitly Out of Scope

- Deployment operations (Fleet summaries, interventions, telemetry)
- Live Signal Scanner collector integrations
- Entity Resolver enrichment
- New investigation endpoints beyond what's needed for the 4 items
- Frontend implementation (Alexander-owned)
- Blockchain anchoring (v1 uses local hash anchor)
- New OSINT collector integrations
- Agent deployment lifecycle changes

## 7. Risks & Dependencies

| Risk | Impact | Mitigation |
|------|--------|------------|
| Domain filter enforcement breaks existing evidence submission workflows | Medium | Empty domain filters = no enforcement (backward compatible) |
| Certificate lifecycle refactor breaks existing certificate consumers | Medium | Existing `GET /certificate` continues to work, returns current state |
| Batch anchor timing sensitivity | Low | Batch is idempotent; manual trigger available for v1 |
| Stop condition evaluation performance on every mutation | Low | Evaluation is lightweight (pure function on in-memory state) |

## 8. Dependencies on Prior Cycles

| Dependency | Cycle | Status |
|------------|-------|--------|
| Investigation persistence | 019 | Shipped |
| Certificate builder + routing | 014c | Shipped |
| Stop condition evaluator | 014c | Shipped |
| Domain filter enum + scanner | 014c | Shipped |
| Commitment monitor + drift events | 014c | Shipped |
| Paradox risk orchestration (for recompute on cert) | 020 | Shipped |
