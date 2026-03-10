# Sprint Plan — Cycle-021: Live Investigation Intelligence + Deployment Operations

**Cycle:** cycle-021
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd_021.md
**SDD:** grimoires/loa/sdd_021.md
**Sprints:** 6 (0–5)
**Total new tests:** 37
**Builder:** Loa (backend/runtime only)

---

## Sprint 0: Operational Contract Tightening (5 tests)

Freeze the operational contracts and verify dependency health before extending live deployment/investigation behavior.

### Task 0.1 — Dependency Health Check

**Files:**
- `grimoires/loa/context/echelon_cycle_021.md` (reference)
- `grimoires/loa/prd_021.md` (reference)
- `grimoires/loa/sdd_021.md` (reference)
- live 014c/015/017/019/020 implementation surfaces

**Work:**
- Verify live dependency surfaces needed by 021 are present and green:
  - investigation toolset contract from 014c
  - collector surfaces from 015 used by Signal Scanner
  - registry/policy constraints from 017
  - deployment/persistence foundations from 019
  - paradox orchestration behavior from 020
- Record any blocking code/doc drift
- Freeze the post-020 regression baseline before implementation starts

**Acceptance criteria:**
- [ ] No unresolved blocking drift remains on active dependency surfaces
- [ ] Post-020 baseline recorded
- [ ] Dependency-health note captured in cycle docs or implementation notes

### Task 0.2 — Deployment Summary Contract

**Files:**
- `backend/api/agents_routes.py`
- `backend/api/agent_deployment_routes.py`

**Work:**
- Freeze the deployment summary shape for Fleet and Agent Detail
- Define required operational fields:
  - deployment_id
  - theatre_id
  - theatre label
  - strategy profile
  - status
  - deployed_at
  - last activity summary
  - intervention state

**Acceptance criteria:**
- [ ] Summary contract is explicit and testable
- [ ] Fleet and detail needs are covered without N+1-only design

### Task 0.3 — Investigation Readiness / WS Contract

**Files:**
- `backend/api/investigation_routes.py`
- `backend/websockets/realtime_manager.py`

**Work:**
- Freeze:
  - readiness response shape
  - `READY` / `ANCHORED` / `ISSUED` semantics
  - deployment/investigation websocket payload contracts

**Acceptance criteria:**
- [ ] Readiness semantics are explicit
- [ ] WS event payloads are frozen before implementation

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Dependency-health verification for active 014c/015/017/019/020 surfaces | Regression |
| 2 | Deployment summary schema validates | Unit |
| 3 | Readiness response schema validates | Unit |
| 4 | WS payload contracts validate | Unit |
| 5 | Domain-filter commitment contract is represented in test fixtures | Unit |

---

## Sprint 1: Deployment Summaries + Intervention API (7 tests)

Turn deployments into operational objects for Fleet and Agent Detail.

### Task 1.1 — DeploymentTelemetryService

**Files:**
- `backend/services/deployment_telemetry_service.py` (new)
- `backend/api/agents_routes.py`
- `backend/api/agent_deployment_routes.py`

**Work:**
- Build reusable deployment summaries with latest activity/intervention state
- Extend list/detail endpoints to return operational summaries
- Avoid duplicate summary assembly across routes

**Acceptance criteria:**
- [ ] Deployment list/detail include operational summary fields
- [ ] Agent list/detail include consistent deployment summaries/counts

### Task 1.2 — DeploymentInterventionService

**Files:**
- `backend/services/deployment_intervention_service.py` (new)
- `backend/api/agent_deployment_routes.py`

**Work:**
- Wrap pause/resume/withdraw/strategy adjustment operations
- Require actor identity and reason where appropriate
- Persist structured audit events

**Acceptance criteria:**
- [ ] Pause/resume/withdraw/strategy actions use intervention service
- [ ] Audit events record actor and reason

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | Agent list returns operational deployment summary/count fields | Integration |
| 2 | Agent detail returns richer deployment summaries | Integration |
| 3 | Pause requires reason and records audit event | Integration |
| 4 | Resume records actor identity | Integration |
| 5 | Strategy change records old/new strategy + reason | Integration |
| 6 | Withdraw updates operational summary correctly | Integration |
| 7 | Summary builder avoids inconsistent route payloads | Unit |

---

## Sprint 2: Live Signal Scanner Intake (7 tests)

Wire investigations to live collector-backed signal intake under committed scope.

### Task 2.1 — InvestigationSignalIngestor

**Files:**
- `backend/services/investigation_signal_ingestor.py` (new)
- `backend/api/investigation_routes.py`
- `backend/investigation/signal_scanner.py`

**Work:**
- Connect Signal Scanner to currently supported collector surfaces only
- Persist scanner outputs as investigation-linked signal records
- Distinguish machine-discovered, human-submitted, and material counter-signal paths

**Acceptance criteria:**
- [ ] Scanner can ingest from supported collectors
- [ ] Ingested signals persist with provenance/receipt context

### Task 2.2 — Domain Filter Enforcement

**Files:**
- `backend/services/investigation_signal_ingestor.py`
- `backend/database/repositories/investigation_repository.py` (if additive persistence metadata needed)

**Work:**
- Enforce committed domain filters at ingestion time
- Reject or explicitly flag out-of-scope signals
- Preserve monitored domain set in commitment/certificate path

**Acceptance criteria:**
- [ ] Out-of-scope signals are not silently ingested
- [ ] Committed domain scope remains legible in persisted investigation state

### Task 2.3 — Registry Policy Enforcement

**Files:**
- `backend/services/investigation_signal_ingestor.py`
- registry/policy surfaces already in repo

**Work:**
- Respect:
  - `query_determinism`
  - `receipt_body_required`
  - `requires_legal_review`
- Mark or reject inadmissible signal paths accordingly

**Acceptance criteria:**
- [ ] Registry policy constraints are enforced on scanner ingestion
- [ ] Legal review requirement is surfaced when applicable

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | Supported collector signal ingests successfully | Integration |
| 2 | Out-of-domain signal is rejected | Integration |
| 3 | Out-of-domain signal can be explicitly flagged if configured | Integration |
| 4 | Receipt-body-required source without receipt body is not admitted cleanly | Integration |
| 5 | Legal-review-required source surfaces legal review flag | Integration |
| 6 | Scanner persists provenance/receipt metadata | Integration |
| 7 | Monitored domain set remains part of commitment/certificate path | Unit |

---

## Sprint 3: Entity Resolver + Evidence Enrichment (6 tests)

Make evidence and claims materially more useful at runtime without breaking stable APIs.

### Task 3.1 — InvestigationEntityEnricher

**Files:**
- `backend/services/investigation_entity_enricher.py` (new)
- `backend/investigation/entity_resolver.py`
- `backend/api/investigation_routes.py`

**Work:**
- Resolve entity context for evidence and claims
- Persist/cache bounded resolved profiles
- Link evidence items to resolved entities where appropriate

**Acceptance criteria:**
- [ ] Evidence items can reference resolved entity context
- [ ] Enrichment cache/persistence is bounded and deterministic enough for release use

### Task 3.2 — Additive Response Exposure

**Files:**
- `backend/schemas/investigation_schemas.py`
- `backend/api/investigation_routes.py`

**Work:**
- Add enrichment context additively where safe
- Prefer optional fields or additive endpoints over breaking schema changes

**Acceptance criteria:**
- [ ] Existing investigation consumers are not broken
- [ ] Enriched context is useful and not overexposed

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | Entity enricher resolves and caches profile | Integration |
| 2 | Evidence item links to resolved entity | Integration |
| 3 | Repeated enrichment hits cache/bounded persistence path | Integration |
| 4 | Enrichment respects determinism/legal-review constraints | Unit |
| 5 | Investigation response exposes additive enrichment fields | Integration |
| 6 | Existing investigation response consumers remain compatible | Regression |

---

## Sprint 4: Stop Condition Orchestration + Certificate Readiness (6 tests)

Turn investigations into live bounded inquiries with readiness and issuance semantics.

### Task 4.1 — StopConditionOrchestrator

**Files:**
- `backend/services/stop_condition_orchestrator.py` (new)
- `backend/api/investigation_routes.py`
- `backend/investigation/stop_conditions.py`

**Work:**
- Evaluate stop conditions after material mutations:
  - evidence submission
  - claim status change
  - material counter-signal ingestion
  - drift event
- Persist stop-condition status and reasons

**Acceptance criteria:**
- [ ] Stop conditions evaluate automatically from material mutation paths
- [ ] Readiness reasons are persisted/exposed

### Task 4.2 — InvestigationReadinessService

**Files:**
- `backend/services/investigation_readiness_service.py` (new)
- `backend/api/investigation_routes.py`

**Work:**
- Maintain lifecycle:
  - `NOT_READY`
  - `READY`
  - `ANCHORED`
  - `ISSUED`
- Respect daily batch anchor at `00:00 UTC`
- Keep `issued_at` gated behind anchor confirmation

**Acceptance criteria:**
- [ ] READY is distinct from ISSUED
- [ ] Anchor timing controls issuance
- [ ] Material drift can push readiness back or force `REVIEW_REQUIRED`

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | Evidence mutation triggers stop-condition evaluation | Integration |
| 2 | Counter-signal mutation triggers stop-condition evaluation | Integration |
| 3 | Drift event can force REVIEW_REQUIRED routing impact | Integration |
| 4 | Investigation transitions to READY when criteria met | Integration |
| 5 | Daily batch anchor gates ISSUED and issued_at | Integration |
| 6 | READY can revert if later drift/counter-signal invalidates readiness | Integration |

---

## Sprint 5: WebSocket Events + Integration + E2E (6 tests)

Expose deployments and investigations as live release-grade backend surfaces.

### Task 5.1 — Deployment Events

**Files:**
- `backend/websockets/realtime_manager.py`
- deployment service/routes

**Work:**
- Emit:
  - `DEPLOYMENT_STATUS_CHANGED`
  - `DEPLOYMENT_INTERVENTION_REQUIRED`

**Acceptance criteria:**
- [ ] Deployment lifecycle events emit correct payloads
- [ ] Intervention-required state is distinct from ordinary status change

### Task 5.2 — Investigation Events

**Files:**
- `backend/websockets/realtime_manager.py`
- investigation orchestration/readiness services

**Work:**
- Emit:
  - `INVESTIGATION_SIGNAL_INGESTED`
  - `INVESTIGATION_STOP_CONDITION_MET`
  - `INVESTIGATION_CERTIFICATE_READY`

**Acceptance criteria:**
- [ ] Investigation event payloads reflect real operational transitions
- [ ] No duplicate/noise emission on non-material state changes

### Task 5.3 — Integration / E2E

**Work:**
- Full operational path:
  - deploy agent
  - ingest signal under committed domain filter
  - enrich entity context
  - mutate investigation state
  - stop condition met
  - readiness recorded
  - anchor/issuance progression
  - deployment events remain coherent

**Acceptance criteria:**
- [ ] Operational deployment flow passes end to end
- [ ] Operational investigation flow passes end to end
- [ ] Regression suite remains green

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | DEPLOYMENT_STATUS_CHANGED payload is correct | Integration |
| 2 | DEPLOYMENT_INTERVENTION_REQUIRED emits on blocked/degraded state | Integration |
| 3 | INVESTIGATION_SIGNAL_INGESTED emits on successful scanner intake | Integration |
| 4 | INVESTIGATION_STOP_CONDITION_MET emits on material readiness transition | Integration |
| 5 | INVESTIGATION_CERTIFICATE_READY emits for READY/ANCHORED/ISSUED progression | Integration |
| 6 | End-to-end deployment + investigation operational flow passes | E2E |

---

## Cycle 021 Summary Target

- **37 tests**
- **6 new operational services**
- Deployment upgraded from persisted record to operational backend surface
- Investigation upgraded from durable record to live bounded inquiry workspace backend
- Domain filters, drift, and batch anchoring respected as first-class constraints
- Regression suite green against the post-020 baseline
