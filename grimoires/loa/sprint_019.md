# Sprint Plan — Cycle-019: Agent Deployment + Investigation Persistence + Paradox Risk

**Cycle:** cycle-019
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd_019.md
**SDD:** grimoires/loa/sdd_019.md
**Sprints:** 6 (0–5)
**Total new tests:** 36
**Builder:** Loa (backend only)

---

## Sprint 0: Schema Foundation + Migration (4 tests)

### Task 0.1 — Agent Deployment Models

**Files:**
- `backend/database/models.py` (extend)

**Work:**
- Add `DeploymentStatus` enum (ACTIVE, PAUSED, WITHDRAWN)
- Add `StrategyProfile` enum (BALANCED, AGGRESSIVE, DEFENSIVE)
- Add `AgentDeployment` model (id, agent_id FK, theatre_id FK, status, strategy_profile, deployed_by, deployed_at, paused_at, withdrawn_at, routing_hint_snapshot, coherence_gate_status_snapshot, config_json, created_at, updated_at)
- Add `DeploymentAuditEvent` model (id, deployment_id FK, event_type, detail_json, created_at)
- Add composite index on (agent_id, theatre_id, status)

**Acceptance criteria:**
- [ ] `AgentDeployment` model importable and creates table in test DB
- [ ] `DeploymentAuditEvent` model with FK to agent_deployments
- [ ] Composite index `ix_agent_deployments_active` created

### Task 0.2 — Investigation Persistence Models

**Files:**
- `backend/database/models.py` (extend)

**Work:**
- Add `InvestigationStatus` enum (ACTIVE, COMPLETED)
- Add `Investigation` model (id, theatre_id, construct_id, inquiry_class, status, domain_filters_json, stop_condition, stop_config_json, created_by, created_at, updated_at, completed_at)
  - NOTE: construct_id follows run-scoped pattern for investigations linked to spawned theatres: `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}` (from Cycle 018 scenario pack provenance)
- Add `InvestigationEvidenceItem` model (id, investigation_id FK, content_hash, provenance_class, content_type, source_description, source_id, query_determinism, references_json, submitted_at)
- Add `InvestigationClaimNode` model (id, investigation_id FK, claim_text, claim_type, evidence_refs_json, counter_signals_json, status, confidence, independence_groups_json, created_at, updated_at)
- Add `InvestigationCounterSignal` model (id, investigation_id FK, signal_class, detected_at, evidence_ref, material, resolution_impact, detection_method)
- Add `InvestigationDriftEvent` model (id, investigation_id FK, drift_type, detected_at, original_value, new_value, evidence_ref, impact_assessment)
- Add `InvestigationCertificateRecord` model (id, investigation_id FK unique, certificate_hash, certificate_json, routing_decision, routing_reason, issued_at)

**Acceptance criteria:**
- [ ] All 7 investigation models importable and create tables in test DB
- [ ] FK relationships and back_populates correct
- [ ] `InvestigationCertificateRecord.investigation_id` has unique constraint

### Task 0.3 — Theatre Paradox Risk Extension

**Files:**
- `backend/database/models.py` (extend Theatre model)

**Work:**
- Add `paradox_risk_level` column (String(10), nullable)
- Add `paradox_risk_factors_json` column (JSON, nullable)
- Add `paradox_risk_updated_at` column (DateTime, nullable)

**Acceptance criteria:**
- [ ] Theatre model has 3 new nullable columns
- [ ] Existing theatre tests still pass

### Task 0.4 — Alembic Migration

**Files:**
- `backend/alembic/versions/c019_agent_deployment_investigation_persistence.py` (new)

**Work:**
- Dialect-safe migration creating 8 tables + 3 columns on theatres
- Inspector pattern for idempotent reruns

**Acceptance criteria:**
- [ ] Migration runs on SQLite
- [ ] Migration runs on PostgreSQL
- [ ] `alembic upgrade head` succeeds from clean state

### Task 0.5 — Pydantic Schemas

**Files:**
- `backend/schemas/agent_deployment_schemas.py` (new)
- `backend/schemas/investigation_schemas.py` (extend with ParadoxRiskResponse)

**Work:**
- `AgentDeploymentCreate`, `AgentDeploymentResponse`, `AgentDeploymentSummaryResponse`
- `DeploymentListResponse`, `StrategyUpdateRequest`
- `DeploymentAuditEventResponse`, `DeploymentDetailResponse`
- `ParadoxRiskResponse` (level, factors, explanation, updated_at)

**Acceptance criteria:**
- [ ] All schemas pass Pydantic v2 validation with sample data
- [ ] `ConfigDict(from_attributes=True)` on all response models

### Tests (4)

| # | Test | Type |
|---|------|------|
| 1 | All new models create tables without errors | Unit |
| 2 | Migration runs on SQLite + PostgreSQL | Integration |
| 3 | All Pydantic schemas validate with sample data | Unit |
| 4 | Regression: ≥1139 existing tests pass | Regression |

---

## Sprint 1: Agent Deployment Service + API (7 tests)

### Task 1.1 — AgentDeploymentService

**Files:**
- `backend/services/agent_deployment_service.py` (new)

**Work:**
- `create_deployment(session, agent_id, theatre_id, strategy_profile, deployed_by, config_json)` with guards (in order):
  - Agent exists and `is_alive=True`
  - Agent `sanity >= 15` (not in breakdown state)
  - Theatre exists
  - No active deployment of this agent to this theatre
  - Theatre deployability checks:
    * If theatre has latest certificate: reject if `routing_hint = BLOCKED`
    * If theatre has latest certificate: reject if `coherence_review_required = true` AND `coherence_gate_status != PASSED`
    * If theatre has no certificate: reject deployment (uncertified theatres are not deployable in Cycle 019)
  - Snapshots routing_hint and coherence_gate_status from theatre's latest certificate
- `withdraw_deployment(session, deployment_id, withdrawn_by)` — ACTIVE|PAUSED → WITHDRAWN
- `pause_deployment(session, deployment_id)` — ACTIVE → PAUSED
- `resume_deployment(session, deployment_id)` — PAUSED → ACTIVE
- `change_strategy(session, deployment_id, new_strategy)` — update strategy, audit event
- `list_deployments(session, agent_id, theatre_id, status, limit, offset)` — filtered list with count
- `get_active_count_for_agent(session, agent_id)` — count query
- All mutating methods create `DeploymentAuditEvent` records

**Acceptance criteria:**
- [ ] Create deployment succeeds with valid agent and theatre with healthy certificate
- [ ] Create deployment rejects dead agent (is_alive=False)
- [ ] Create deployment rejects agent with sanity < 15
- [ ] Create deployment rejects duplicate active deployment
- [ ] Create deployment rejects theatre with certificate routing_hint = BLOCKED
- [ ] Create deployment rejects theatre where coherence_review_required=true and coherence_gate_status != PASSED
- [ ] Create deployment handles missing certificate according to product policy
- [ ] Withdraw sets status=WITHDRAWN and withdrawn_at
- [ ] Strategy change creates STRATEGY_CHANGED audit event

### Task 1.2 — Deployment API Routes

**Files:**
- `backend/api/agent_deployment_routes.py` (new)
- `backend/main.py` (register router)

**Work:**
- `POST /api/v1/agent-deployments` — create deployment, auth via `Depends(get_current_user)`, `user.user_id` as deployed_by
- `GET /api/v1/agent-deployments` — list with filters (agent_id, theatre_id, status), pagination
- `GET /api/v1/agent-deployments/{deployment_id}` — detail with audit trail
- `POST /api/v1/agent-deployments/{deployment_id}/withdraw` — withdraw
- `POST /api/v1/agent-deployments/{deployment_id}/pause` — pause
- `POST /api/v1/agent-deployments/{deployment_id}/resume` — resume
- `POST /api/v1/agent-deployments/{deployment_id}/strategy` — change strategy
- Register `deployment_router` in FastAPI app

**Acceptance criteria:**
- [ ] POST create returns 201 with deployment record
- [ ] GET list returns filtered results with total count
- [ ] POST withdraw returns updated deployment with WITHDRAWN status
- [ ] All mutating endpoints require auth

### Task 1.3 — Agent Response Extension

**Files:**
- `backend/api/agents_routes.py` (modify)
- `backend/schemas/` (extend AgentResponse)

**Work:**
- Extend `AgentResponse` with `active_deployments_count: int` and `active_deployments: List[AgentDeploymentSummaryResponse]`
- In `get_agent` endpoint, join `agent_deployments` where status='ACTIVE'
- In `list_agents` endpoint, include count only (not full list) for performance

**Acceptance criteria:**
- [ ] GET /api/v1/agents/{id} returns active_deployments_count and active_deployments
- [ ] GET /api/v1/agents returns agents with active_deployments_count

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | Create deployment with valid agent + theatre | Integration |
| 2 | Create deployment rejects dead agent (guard) | Unit |
| 3 | Create deployment rejects duplicate active (guard) | Unit |
| 4 | Create deployment rejects theatre with BLOCKED routing_hint (guard) | Unit |
| 5 | Withdraw deployment sets WITHDRAWN + withdrawn_at | Integration |
| 6 | Change strategy creates audit event | Integration |
| 7 | Agent response includes active_deployments_count | Integration |

---

## Sprint 2: Investigation Persistence (8 tests)

### Task 2.1 — InvestigationRepository

**Files:**
- `backend/database/repositories/investigation_repository.py` (new)

**Work:**
- `create(config)` — create Investigation record + InvestigationToolset
- `get(investigation_id)` — eager load all sub-entities
- `list_all()` — list with summary counts
- `submit_evidence(investigation_id, evidence_data)` — persist InvestigationEvidenceItem + delegate to EvidenceEnvelope
- `register_claim(investigation_id, claim_data)` — persist InvestigationClaimNode + delegate to ClaimGraph
- `log_counter_signal(investigation_id, signal_data)` — persist InvestigationCounterSignal
- `log_drift(investigation_id, drift_data)` — persist InvestigationDriftEvent
- `build_certificate(investigation_id)` — rebuild toolset from DB, build certificate, persist InvestigationCertificateRecord
- `_rebuild_toolset(investigation)` — reconstruct InvestigationToolset from persisted records

**Acceptance criteria:**
- [ ] Create investigation persists to DB
- [ ] Evidence submission creates DB record with correct content_hash
- [ ] Claim registration creates DB record with correct fields
- [ ] Counter-signal log creates DB record
- [ ] Drift event log creates DB record
- [ ] Toolset rebuild from DB records produces identical certificate to in-memory path

### Task 2.2 — Route Migration

**Files:**
- `backend/api/investigation_routes.py` (modify)

**Work:**
- Remove `_investigations: dict[str, InvestigationToolset] = {}`
- Add `_get_repo` dependency returning `InvestigationRepository(session)`
- Replace all dict operations with repository calls
- Keep all request/response shapes identical
- Keep existing registry enforcement (receipt_body_required, legal_review)

**Acceptance criteria:**
- [ ] All existing investigation API tests pass unchanged
- [ ] POST /investigations/ persists to DB (verified by reading back)
- [ ] POST /investigations/{id}/evidence persists InvestigationEvidenceItem
- [ ] POST /investigations/{id}/claims persists InvestigationClaimNode
- [ ] POST /investigations/{id}/counter-signals persists InvestigationCounterSignal
- [ ] GET /investigations/{id}/certificate builds and persists certificate

### Task 2.3 — Restart Survival Test

**Work:**
- Test that creates investigation, submits evidence, registers claim, then simulates server restart (new DB session), and verifies all data is still accessible

**Acceptance criteria:**
- [ ] Investigation data survives simulated restart
- [ ] Certificate can be rebuilt from persisted data after restart

### Tests (8)

| # | Test | Type |
|---|------|------|
| 1 | Create investigation persists to DB | Integration |
| 2 | Submit evidence persists InvestigationEvidenceItem | Integration |
| 3 | Register claim persists InvestigationClaimNode | Integration |
| 4 | Log counter-signal persists InvestigationCounterSignal | Integration |
| 5 | Log drift event persists InvestigationDriftEvent | Integration |
| 6 | Build certificate persists InvestigationCertificateRecord | Integration |
| 7 | Investigation survives simulated restart | Integration |
| 8 | Existing investigation API contract unchanged (response shape check) | Regression |

---

## Sprint 3: Paradox Risk Service (6 tests)

### Task 3.1 — ParadoxRiskEvaluator

**Files:**
- `backend/services/paradox_risk_evaluator.py` (new)

**Work:**
- `evaluate(session, theatre)` → `ParadoxRiskAssessment(level, factors, explanation)`
- Inquiry-class-specific thresholds (5 classes × 3 weight categories)
- Factor computation:
  - `logic_gap`: from Timeline.logic_gap (0-1)
  - `stability`: from Timeline.stability (0-1, inverted — lower is worse)
  - `counter_signals_material`: count of material counter-signals from linked investigation
  - `evidence_freshness_hours`: hours since last evidence submission in linked investigation
  - `active_paradox`: boolean from Timeline.has_active_paradox
- Risk level determination:
  - HIGH: active paradox, or logic_gap > high threshold, or stability < high threshold
  - WATCH: logic_gap > watch threshold, or stability < watch threshold, or material counter-signals > 0
  - LOW: default
- Explanation generation using product vocabulary: "Evidence weak", "Counter-signals rising", "Logic gap widening", "Stale investigation", "Paradox active"
- **CRITICAL:** paradox_risk is a COMPUTED SURFACE with cached persistence, NOT operator-authored

**Acceptance criteria:**
- [ ] Returns LOW for healthy theatre (no paradox, low logic gap, high stability)
- [ ] Returns WATCH for theatre with moderate logic gap
- [ ] Returns HIGH for theatre with active paradox
- [ ] INVESTIGATIVE inquiry weighs evidence freshness more heavily than COUNTERFACTUAL
- [ ] SCRUTINY inquiry weighs counter-signals more heavily than other classes
- [ ] Explanation uses product vocabulary, not "fake market" language

### Task 3.2 — Theatre Response Extension

**Files:**
- `backend/api/theatre_routes.py` (modify)
- `backend/schemas/` (extend TheatreResponse)

**Work:**
- Add `paradox_risk: Optional[ParadoxRiskResponse]` to `TheatreResponse`
- Add `paradox_risk_level: Optional[str]` to `TheatreListItemResponse`
- In `get_theatre` endpoint, compute risk on request via `ParadoxRiskEvaluator`
- In `list_theatres` endpoint, return persisted `paradox_risk_level` from Theatre model

**Acceptance criteria:**
- [ ] GET /api/v1/theatres/{id} returns paradox_risk object with level, factors, explanation
- [ ] GET /api/v1/theatres returns paradox_risk_level per theatre

### Task 3.3 — Risk Computation Triggers

**Files:**
- `backend/worker/tasks/paradox.py` (extend)
- `backend/database/repositories/investigation_repository.py` (extend)

**Work:**
- **ParadoxTask tick trigger:** After paradox spawn/detonation tick updates Timeline stability or active_paradox state, recompute risk for affected theatres, persist updated risk level to Theatre record, broadcast PARADOX_RISK_CHANGED WS event if level changed
- **Counter-signal ingestion trigger:** In `InvestigationRepository.log_counter_signal`, if `signal.material=true`, trigger ParadoxRiskEvaluator for linked theatre
- **Evidence freshness trigger:** In `InvestigationRepository.submit_evidence`, compare evidence_freshness_hours to previous state; if crosses a configured threshold band, trigger ParadoxRiskEvaluator for linked theatre
- **Stale cache trigger:** On theatre detail/list read, check if cached `paradox_risk_level` is missing or exceeds staleness TTL; if so, trigger fresh evaluation

**Acceptance criteria:**
- [ ] ParadoxTask tick triggers and persists risk updates to Theatre.paradox_risk_level
- [ ] Material counter-signal ingestion triggers risk recalculation for linked theatre
- [ ] Evidence freshness threshold crossing triggers risk recalculation
- [ ] Stale cache detection on API read triggers fresh evaluation
- [ ] Level change from any trigger broadcasts PARADOX_RISK_CHANGED WS event

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | Evaluator returns LOW for healthy theatre | Unit |
| 2 | Evaluator returns WATCH for moderate logic gap | Unit |
| 3 | Evaluator returns HIGH for active paradox | Unit |
| 4 | INVESTIGATIVE inquiry weighs evidence freshness higher | Unit |
| 5 | SCRUTINY inquiry weighs counter-signals higher | Unit |
| 6 | Theatre response includes paradox_risk object | Integration |

---

## Sprint 4: Certificate Persistence + Deployment Lifecycle (5 tests)

### Task 4.1 — Certificate Persistence

**Files:**
- `backend/database/repositories/investigation_repository.py` (extend build_certificate)

**Work:**
- On `build_certificate`:
  1. Rebuild InvestigationToolset from DB records
  2. Delegate to CertificateBuilder.build()
  3. Persist `InvestigationCertificateRecord` with certificate_hash, certificate_json, routing_decision, routing_reason
  4. Set `Investigation.status = COMPLETED`, `Investigation.completed_at = now()`
  5. Broadcast `INVESTIGATION_STATUS_CHANGED` WS event

**Acceptance criteria:**
- [ ] Certificate record persisted with correct hash
- [ ] Investigation status set to COMPLETED
- [ ] Certificate FK links to investigation (unique constraint)

### Task 4.2 — Deployment State Machine

**Files:**
- `backend/services/agent_deployment_service.py` (extend)

**Work:**
- Validate transitions:
  - ACTIVE → PAUSED (via pause)
  - PAUSED → ACTIVE (via resume)
  - ACTIVE → WITHDRAWN (via withdraw)
  - PAUSED → WITHDRAWN (via withdraw)
  - Reject invalid transitions (WITHDRAWN → anything, ACTIVE → ACTIVE, etc.)
- All transitions create audit events

**Acceptance criteria:**
- [ ] ACTIVE → PAUSED succeeds
- [ ] PAUSED → ACTIVE succeeds
- [ ] WITHDRAWN → ACTIVE rejected (422)
- [ ] Each transition creates audit event

### Task 4.3 — Deployment Detail with Audit Trail

**Files:**
- `backend/api/agent_deployment_routes.py` (extend get_deployment)

**Work:**
- `GET /api/v1/agent-deployments/{id}` returns `DeploymentDetailResponse` including `audit_events` list
- Audit events ordered by created_at descending

**Acceptance criteria:**
- [ ] Deployment detail includes audit events
- [ ] Audit events show full lifecycle (DEPLOYED → STRATEGY_CHANGED → PAUSED → RESUMED → WITHDRAWN)

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Certificate persisted with correct hash | Integration |
| 2 | Investigation status set to COMPLETED on certificate build | Integration |
| 3 | Deployment ACTIVE → PAUSED → ACTIVE lifecycle | Integration |
| 4 | Deployment WITHDRAWN rejects further transitions | Unit |
| 5 | Deployment detail returns audit trail | Integration |

---

## Sprint 5: WebSocket Events + Integration + E2E (6 tests)

### Task 5.1 — WebSocket Event Broadcasts

**Files:**
- `backend/websockets/realtime_manager.py` (extend)

**Work:**
- `broadcast_agent_deployed(agent_id, theatre_id, strategy_profile, deployed_by)`
- `broadcast_agent_withdrawn(agent_id, theatre_id, withdrawn_by)`
- `broadcast_paradox_risk_changed(theatre_id, old_level, new_level, factors)`
- `broadcast_investigation_status_changed(investigation_id, old_status, new_status)`

**Acceptance criteria:**
- [ ] All 4 WS event types broadcast with correct payloads
- [ ] Events fire at correct lifecycle points

### Task 5.2 — Wire WS Events into Services

**Files:**
- `backend/services/agent_deployment_service.py` (extend)
- `backend/database/repositories/investigation_repository.py` (extend)
- `backend/worker/tasks/paradox.py` (extend)

**Work:**
- Deployment service: broadcast AGENT_DEPLOYED on create, AGENT_WITHDRAWN on withdraw
- Investigation repository: broadcast INVESTIGATION_STATUS_CHANGED on certificate build
- Paradox task: broadcast PARADOX_RISK_CHANGED when risk level changes

**Acceptance criteria:**
- [ ] Deploy agent → WS AGENT_DEPLOYED event
- [ ] Withdraw agent → WS AGENT_WITHDRAWN event
- [ ] Build certificate → WS INVESTIGATION_STATUS_CHANGED event
- [ ] Paradox tick → WS PARADOX_RISK_CHANGED event (when level changes)

### Task 5.3 — E2E Integration Test

**Work:**
- Full lifecycle test:
  1. Create agent deployment (agent → theatre)
  2. Create investigation for same theatre
  3. Submit evidence to investigation
  4. Register claim
  5. Log counter-signal (material)
  6. Verify paradox risk updated (WATCH or HIGH)
  7. Build certificate
  8. Verify investigation status COMPLETED
  9. Withdraw agent deployment
  10. Verify deployment status WITHDRAWN

**Acceptance criteria:**
- [ ] Full lifecycle completes without errors
- [ ] All DB records persisted correctly
- [ ] WS events would fire at correct points

### Task 5.4 — Regression Verification

**Work:**
- Run full test suite
- Verify all pre-019 tests pass

**Acceptance criteria:**
- [ ] ≥1139 existing tests pass (post-018 baseline)
- [ ] All 36 new 019 tests pass
- [ ] No regressions in investigation API contract

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | WS AGENT_DEPLOYED fires on deployment creation | Integration |
| 2 | WS AGENT_WITHDRAWN fires on withdrawal | Integration |
| 3 | WS PARADOX_RISK_CHANGED fires on level change | Integration |
| 4 | WS INVESTIGATION_STATUS_CHANGED fires on certificate build | Integration |
| 5 | E2E: deploy → investigate → risk → certificate → withdraw | E2E |
| 6 | Regression: ≥1139 existing tests pass | Regression |

---

## Risk Register

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Investigation toolset rebuild from DB may produce different hashes than in-memory path | Add hash comparison test in Sprint 2; canonical JSON serialization must be deterministic | Loa |
| Agent deployment guards depend on theatre certificate data (routing_hint, coherence_gate) that may be null | Treat null certificate data as "no blocker" — deployment guard only checks is_alive and no-duplicate | Loa |
| ParadoxRiskEvaluator thresholds are speculative | Thresholds are configurable constants; can be tuned after observation | Loa + Codex |
| Investigation persistence adds DB load to every evidence submission | Evidence is append-only with sequential IDs; DB writes are simple inserts, not updates | Loa |
| Paradox risk computation on every theatre detail request adds latency | Use persisted risk level for list endpoint; compute on-request only for detail | Loa |
