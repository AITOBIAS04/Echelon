# PRD — Cycle-017: Policy Surface

**Cycle:** cycle-017
**Date:** 6 March 2026
**Predecessor:** cycle-016 (Results Surface), cycle-014c (Investigation Toolset), cycle-015 (Live Collectors), cycle-013 (Agent Runtime), cycle-012 (Sponsored Theatres), cycle-010a (LMSR)
**Sprints:** 6 total (0–5)
**Design input:** `HANDOFF_MATRIX_ALEXANDER.md`, `cycle017.ts` (frontend type stubs), `featureFlags.ts`
**Baseline:** ≥1060 passed (post-016 target), 8 pre-existing async heartbeat failures

---

## 1. Problem Statement

Cycle 016 delivered the Results Surface — the core frontend views now render from real backend data, investigations are end-to-end, and the bulk of the mock presentation layer is retired. Several surfaces remain honestly staged: Create Theatre's blank path and Alpamayo shell are deferred, Scenario Packs is an empty-state shell with no backend, and agent deployment is a staged modal backed by mock theatres with a disabled deploy button (see handoff matrix §3). But the platform's **policy layer** doesn't exist yet:

- **Certificates have no routing intelligence.** A certificate says "this theatre scored 0.73" but nothing about whether that result is deployable, review-required, or blocked. The `routing_hint` field exists as a frontend type stub but has no backend computation.
- **No flow metrics.** Theatre and timeline cards show static state but not capital flow — net inflow over 24h/7d (`TAO Flow`) is stubbed in `cycle017.ts` but has no backend aggregation.
- **Registry metadata is incomplete.** Source queries used by investigations lack determinism classification, receipt body requirements, and legal review flags — all critical for audit trails.
- **No coherence gates.** Post-routing policy evaluation (did this certificate pass coherence review before deployment?) is entirely absent. The `CoherenceGateFields` stub exists but nothing computes or persists gate status.
- **WebSocket is fire-and-forget.** The real-time infrastructure from Cycle 016 broadcasts events but doesn't broadcast policy state changes — routing decisions, gate transitions, flow threshold alerts.

This cycle adds the **policy surface**: the intelligence that sits between raw results (certificates, scores, trades) and deployment decisions (can this be used? should it be reviewed? is it blocked?).

> Sources: cycle017.ts type stubs, featureFlags.ts flag definitions, HANDOFF_MATRIX_ALEXANDER.md §3–§4

## 2. Objective

### Sprint 0: Schema Foundation + Migration

Extend backend models with all Cycle 017 fields. Create the database migration. No runtime logic yet — just the schema layer so that all subsequent sprints can write to real columns.

### Sprint 1: Deployability Routing

Build the routing evaluation engine. When a theatre certificate is issued, compute a `routing_hint` (ALLOWED / REVIEW_REQUIRED / BLOCKED) based on configurable policy rules. Persist the hint on the certificate. Expose via API.

### Sprint 2: TAO Flow Metrics

Build time-windowed capital flow aggregation. Compute `net_inflow_24h` and `net_inflow_7d` for timelines from wing flap trade data. Expose on timeline and theatre responses. Surface in the frontend on theatre/timeline cards.

### Sprint 3: Registry Schema Expansion

Extend the existing OSINT source registry (`backend/osint/models/registry.py`) with `query_determinism`, `receipt_body_required`, and `requires_legal_review`. Update the investigation toolset to enforce receipt requirements and flag legal review needs. Surface in investigation detail views. Only introduce a new DB table if persistence beyond the current JSON-backed registry is needed.

### Sprint 4: Coherence Gates

Build the post-routing coherence gate system. After a certificate receives a routing hint, it may require a coherence review before deployment. Track gate status (PENDING → PASSED / FAILED). Integrate with the certificate pipeline and expose via API + WS.

### Sprint 5: WebSocket Policy Events + Frontend Integration + Polish

Extend the WebSocket event system with policy-layer events. Wire all Cycle 017 fields into the frontend behind feature flags. Remove the three 017-scoped flags (`DEPLOYABILITY_ROUTING`, `REGISTRY_SCHEMA`, `COHERENCE_GATES`); retain `CYCLE_017_TAO_FLOW` if it still gates staged Alpamayo behaviour and `WEBSOCKET_REALTIME` as a generic realtime gate. Polish and test.

## 3. Success Criteria

### SC-0: Schema Foundation

1. All Cycle 017 fields present as columns in the database
2. Migration is dialect-safe (PostgreSQL + SQLite)
3. All existing tests still pass (zero regressions)
4. Pydantic response schemas extended with new fields (optional, nullable)

### SC-1: Deployability Routing

1. `RoutingEvaluator` service computes routing_hint for any `TheatreCertificate`
2. Routing hint persisted on certificate at issuance time
3. `TheatreCertificateResponse` includes `routing_hint` and `review_reason_code`
4. `GET /api/v1/theatres/{id}/certificate` returns routing fields
5. `GET /api/v1/certificates?routing_hint=REVIEW_REQUIRED` — filter by routing status
6. Policy rules are configurable (score thresholds, inquiry class rules, tier rules)
7. 8+ tests covering routing evaluation logic

### SC-2: TAO Flow Metrics

1. `TaoFlowAggregator` service computes 24h/7d net inflow from wing flap trade data
2. Aggregation runs on game loop cadence (configurable, default 60s)
3. `net_inflow_24h` and `net_inflow_7d` persisted on Timeline
4. Timeline and Theatre API responses include flow fields
5. Frontend theatre/timeline cards show flow badges when flag enabled
6. 6+ tests covering flow computation edge cases

### SC-3: Registry Schema Expansion

1. Source metadata model extended with `query_determinism`, `receipt_body_required`, `requires_legal_review`
2. Investigation evidence submission enforces `receipt_body_required` when set
3. Legal review flag surfaced in investigation detail views
4. 4+ tests covering registry schema enforcement

### SC-4: Coherence Gates

1. `CoherenceGateEvaluator` service evaluates gate conditions
2. Gate status (PENDING / PASSED / FAILED) persisted on certificate
3. Gate transitions are auditable (TheatreAuditEvent)
4. Certificates with `coherence_review_required=true` cannot be deployed until gate PASSED
5. `GET /api/v1/certificates/{id}/gate` — gate status endpoint
6. 6+ tests covering gate lifecycle

### SC-5: WebSocket + Frontend + Polish

1. New WS event types: ROUTING_DECISION, COHERENCE_GATE_TRANSITION, TAO_FLOW_ALERT
2. Three 017-scoped feature flags removed (`DEPLOYABILITY_ROUTING`, `REGISTRY_SCHEMA`, `COHERENCE_GATES`); `CYCLE_017_TAO_FLOW` and `WEBSOCKET_REALTIME` retained if still gating non-017 surfaces
3. Certificate explorer shows routing hint badge + coherence gate status
4. Timeline/theatre cards show TAO flow metrics
5. Investigation detail shows registry schema fields
6. Responsive, loading, empty, and error states for all new UI
7. 4+ frontend tests

### SC-6: Test Gate

1. ≥1060 passed (post-016 baseline maintained)
2. Zero new test failures
3. 40+ new tests across backend and frontend
4. Post-017 expected: ≥1100 passed

## 4. Codebase Grounding

### Existing Infrastructure (017 Dependencies)

| Component | Location | Relevance |
|-----------|----------|-----------|
| TheatreCertificate model | `backend/database/models.py` | Extend with routing_hint, coherence fields |
| Timeline model | `backend/database/models.py` | Extend with TAO flow fields |
| Certificate pipeline | `backend/services/certificate_pipeline.py` | Hook routing evaluation into issuance |
| Theatre routes | `backend/api/theatre_routes.py` | Extend responses with 017 fields |
| Investigation toolset | `backend/investigation/` | Enforce registry schema on evidence |
| WebSocket manager | `backend/websockets/realtime_manager.py` | Add policy event broadcasts |
| Feature flags | `frontend/src/lib/featureFlags.ts` | Gate 017 UI until backend ships |
| Type stubs | `frontend/src/types/cycle017.ts` | Migrate to real types |
| Handoff matrix | `output/HANDOFF_MATRIX_ALEXANDER.md` | Route + empty state contracts |
| Game loop | `backend/worker/game_loop.py` | Add TAO flow aggregation cadence |
| Audit events | `backend/database/models.py` (TheatreAuditEvent) | Track gate transitions |
| Investigation routes | `backend/api/investigation_routes.py` | Extend with registry enforcement |

### Frontend Type Stubs → Real Types

| Stub Interface | Flag | Target Sprint |
|---------------|------|---------------|
| `DeployabilityRoutingFields` | `CYCLE_017_DEPLOYABILITY_ROUTING` | Sprint 1 |
| `TaoFlowFields` | `CYCLE_017_TAO_FLOW` | Sprint 2 |
| `RegistrySchemaFields` | `CYCLE_017_REGISTRY_SCHEMA` | Sprint 3 |
| `CoherenceGateFields` | `CYCLE_017_COHERENCE_GATES` | Sprint 4 |
| — | `WEBSOCKET_REALTIME` | Sprint 5 |

## 5. Sprint Breakdown

### Sprint 0: Schema Foundation + Migration (4 tasks)

Extend all models, create migration, extend Pydantic schemas. No runtime logic.

| Task | Description | Tests |
|------|-------------|-------|
| 0.1 | Model layer: add all 017 columns to TheatreCertificate, Timeline, source metadata | — |
| 0.2 | Alembic migration (dialect-safe) | 2 |
| 0.3 | Pydantic schema extensions (optional fields on existing responses) | 2 |
| 0.4 | Regression test: verify all existing tests pass with new nullable columns | — |

**Sprint 0 total:** 4 tests

### Sprint 1: Deployability Routing (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 1.1 | `RoutingEvaluator` service with configurable policy rules | 4 |
| 1.2 | Hook into certificate pipeline — compute routing_hint at issuance | 2 |
| 1.3 | Extend theatre routes — filter certificates by routing_hint | 1 |
| 1.4 | Frontend: routing hint badge on certificate explorer (behind flag) | 1 |
| 1.5 | Sprint 1 integration test | — |

**Sprint 1 total:** 8 tests

### Sprint 2: TAO Flow Metrics (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 2.1 | `TaoFlowAggregator` service — windowed net inflow computation | 3 |
| 2.2 | Game loop integration — run aggregation on cadence | 1 |
| 2.3 | Extend Timeline + Theatre responses with flow fields | 1 |
| 2.4 | Frontend: flow badges on theatre/timeline cards (behind flag) | 1 |
| 2.5 | Sprint 2 edge case tests (zero trades, negative flow, boundary windows) | — |

**Sprint 2 total:** 6 tests

### Sprint 3: Registry Schema Expansion (4 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 3.1 | Extend source metadata model with registry fields | 1 |
| 3.2 | Enforce `receipt_body_required` on evidence submission | 2 |
| 3.3 | Surface legal review flag in investigation detail API | 1 |
| 3.4 | Frontend: registry badges in investigation detail view (behind flag) | — |

**Sprint 3 total:** 4 tests

### Sprint 4: Coherence Gates (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 4.1 | `CoherenceGateEvaluator` service — gate lifecycle | 3 |
| 4.2 | Audit event logging for gate transitions | 1 |
| 4.3 | Certificate deployment guard (block deploy if gate PENDING/FAILED) | 1 |
| 4.4 | Gate status API endpoint | 1 |
| 4.5 | Frontend: gate status badge on certificate explorer (behind flag) | — |

**Sprint 4 total:** 6 tests

### Sprint 5: WebSocket Policy Events + Frontend Integration + Polish (6 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 5.1 | WS event types: ROUTING_DECISION, COHERENCE_GATE_TRANSITION, TAO_FLOW_ALERT | 2 |
| 5.2 | Frontend: remove feature flags, wire all 017 fields natively | — |
| 5.3 | Frontend: delete `cycle017.ts` stubs, extend real type files | — |
| 5.4 | Frontend: responsive layout, loading, empty, error states for new UI | 2 |
| 5.5 | E2E test: theatre → certificate → routing → gate → verify `is_deployable` | 1 |
| 5.6 | Final audit: zero feature-flagged code in production paths | — |

**Sprint 5 total:** 5 tests

**Grand total:** 4 + 8 + 6 + 4 + 6 + 5 = 33 new tests. Post-017 expected: ≥1100 passed.

## 6. Non-Functional Requirements

### NFR-1: Policy Auditability

All policy decisions (routing hints, gate transitions) are logged as `TheatreAuditEvent` records with full context. No silent state changes.

### NFR-2: Backwards Compatibility

All new fields are optional/nullable in API responses. Existing clients that don't read 017 fields continue to work unchanged. Feature flags gate the frontend until backend is stable.

### NFR-3: Configurable Policy

Routing rules and coherence gate conditions are configurable — not hardcoded. Policy parameters live in a config structure, not scattered across service code.

### NFR-4: Performance

TAO flow aggregation must not block the game loop. Windowed queries use indexed timestamp columns. Aggregation runs async on its own cadence.

### NFR-5: Design Language

All new UI follows the existing kree8.studio terminal aesthetic. Routing hint badges use existing `--routing-allowed` / `--routing-review` tokens from Cycle 016. Gate status badges extend the same colour vocabulary.

## 7. Out of Scope

- Multi-user policy approval workflows (e.g., 2-of-3 reviewers approve a gate)
- Historical TAO flow charting (aggregation is point-in-time, not time-series)
- Policy rule versioning or A/B testing
- External policy engine integration (OPA, Cedar, etc.)
- Automated gate resolution (gates are manually resolved in this cycle)
- Chain anchoring for policy decisions
- OKLCH colour migration (remains P3, not a blocker)
- Investigation persistence to database (remains in-memory; separate cycle)

## 8. Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Cycle-016 (Results Surface) | ✓ Complete | All frontend views wired to real APIs |
| Certificate Pipeline | ✓ Exists | Hook point for routing evaluation |
| WebSocket Manager | ✓ Exists | Extension point for policy events |
| Game Loop | ✓ Exists | Extension point for flow aggregation |
| TheatreAuditEvent model | ✓ Exists | Audit trail for gate transitions |
| Feature Flag System | ✓ Exists | Gates for frontend integration |
| Empty State System | ✓ Exists | All pages have appropriate empty states |

## 9. What This Unlocks

- **Deployment intelligence** — certificates carry routing decisions, not just scores
- **Capital flow visibility** — theatre cards show whether money is flowing in or out
- **Audit-ready investigations** — registry metadata supports receipt and legal review requirements
- **Gated deployment** — coherence gates prevent premature deployment of unchecked results
- **Real-time policy awareness** — WS events notify the UI of routing decisions and gate transitions as they happen
- **Feature flag cleanup** — the 5 Cycle 017 flags are removed, simplifying the codebase
