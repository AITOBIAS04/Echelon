# Cycle-017: Policy Surface

**Date:** 6 March 2026
**Depends on:** Cycle-016 (Results Surface), Cycle-014c (Investigation Toolset), Cycle-012 (Sponsored Theatres), Cycle-013 (Agent Runtime)
**Sprints:** 6 (0–5)
**Scope:** Add a policy layer between raw results (certificates, scores, trades) and deployment decisions. Five capability areas: deployability routing, TAO flow metrics, registry schema expansion, coherence gates, and WebSocket policy events. Backend services, schema migration, API extensions, and frontend integration behind feature flags.

---

## Why This Cycle Exists

Cycle 016 delivered the Results Surface — the core frontend views now render from real backend data, investigations are end-to-end, and the bulk of the mock presentation layer is retired. Several surfaces remain honestly staged: Create Theatre's blank path and Alpamayo shell are deferred, Scenario Packs is an empty-state shell with no backend, and agent deployment is a staged modal backed by mock theatres with a disabled deploy button (see handoff matrix §3 "Current Truth in Code"). But the platform has **no policy intelligence**:

- **Certificates carry scores but no routing decisions.** A certificate says "composite score 0.73" but nothing about whether that result is deployable, review-required, or blocked.
- **No capital flow visibility.** Theatre and timeline cards show static state but not how money is moving — net inflow over 24h/7d is invisible.
- **Registry metadata is incomplete.** Source queries lack determinism classification, receipt body requirements, and legal review flags — all critical for audit trails.
- **No post-routing gates.** After a certificate gets a routing hint, there's no coherence review checkpoint before deployment.
- **WebSocket doesn't broadcast policy events.** The real-time infrastructure from Cycle 016 broadcasts trades and paradoxes but not routing decisions or gate transitions.

---

## What Already Exists (Cycle 017 Scaffolding)

### Frontend Type Stubs (`frontend/src/types/cycle017.ts`)

Five mixin interfaces stubbed for fields that don't exist in API responses yet:

| Interface | Fields | Target |
|-----------|--------|--------|
| `DeployabilityRoutingFields` | `routing_hint` (ALLOWED/REVIEW_REQUIRED/BLOCKED), `review_reason_code` | TheatreCertificate |
| `TaoFlowFields` | `net_inflow_24h`, `net_inflow_7d` | Timeline |
| `RegistrySchemaFields` | `query_determinism`, `receipt_body_required`, `requires_legal_review` | Source metadata |
| `CoherenceGateFields` | `coherence_review_required`, `coherence_gate_status` (PENDING/PASSED/FAILED) | TheatreCertificate |
| Composites | `Cycle017CertificateExtensions`, `Cycle017TimelineExtensions`, `Cycle017RegistryExtensions` | — |

### Feature Flags (`frontend/src/lib/featureFlags.ts`)

Resolution: localStorage override → env var (`VITE_FF_*`) → default `false`.

| Flag | Intent | Sprint 5 Disposition |
|------|--------|---------------------|
| `CYCLE_017_DEPLOYABILITY_ROUTING` | Gate routing hint UI | **Remove** — sole consumer is 017 routing badges |
| `CYCLE_017_TAO_FLOW` | Gate flow metric UI + staged Alpamayo behaviour in Create Theatre | **Retain if still gating Alpamayo** — also used in CreateTheatrePage staged shell; remove only when all consumers are native |
| `CYCLE_017_REGISTRY_SCHEMA` | Gate registry metadata UI | **Remove** — sole consumer is 017 registry badges |
| `CYCLE_017_COHERENCE_GATES` | Gate coherence gate UI | **Remove** — sole consumer is 017 gate status |
| `WEBSOCKET_REALTIME` | Gate live update surfaces via shared `useRealtimeChannel` hook | **Retain** — generic realtime gate, not a disposable 017-only shim |

### Backend Infrastructure Ready to Extend

| Component | Location | Extension Point |
|-----------|----------|-----------------|
| TheatreCertificate model | `backend/database/models.py` | Add routing_hint, coherence columns |
| Timeline model | `backend/database/models.py` | Add TAO flow columns |
| Certificate pipeline | `backend/services/certificate_pipeline.py` | Hook routing evaluation into issuance |
| WebSocket manager | `backend/websockets/realtime_manager.py` | Add policy event broadcasts |
| Game loop | `backend/worker/game_loop.py` | Add TAO flow aggregation cadence |
| TheatreAuditEvent | `backend/database/models.py` | Track gate transitions |
| Investigation routes | `backend/api/investigation_routes.py` | Enforce registry schema |

---

## Sprint Plan

### Sprint 0: Schema Foundation + Migration

Extend all models with 017 columns. Create Alembic migration (dialect-safe). Extend Pydantic schemas with optional/nullable new fields. No runtime logic.

**Key changes:**
- TheatreCertificate: +6 columns (routing_hint, review_reason_code, coherence_review_required, coherence_gate_status, coherence_reviewed_at, coherence_reviewer_id)
- Timeline: +3 columns (net_inflow_24h, net_inflow_7d, flow_updated_at)
- Source registry: +3 fields (query_determinism, receipt_body_required, requires_legal_review)
- New migration: `c017_policy_surface.py`
- Response schemas extended with new optional fields + computed `is_deployable`

**Decision point:** Source metadata model — extend existing typed OSINT registry at `backend/osint/models/registry.py` (preferred) vs new `SourceRegistryEntry` DB table (only if DB persistence needed beyond JSON-backed approach).

### Sprint 1: Deployability Routing

New `RoutingEvaluator` service with configurable policy rules:

| Priority | Rule | Result |
|----------|------|--------|
| 1 | verification_tier in BLOCKED_TIERS (REJECTED) | BLOCKED |
| 2 | composite_score < 0.3 | BLOCKED |
| 3 | verification_tier in REVIEW_TIERS (DRAFT, CONTESTED) | REVIEW_REQUIRED |
| 4 | composite_score < 0.6 | REVIEW_REQUIRED |
| 5 | inquiry_class in ALWAYS_REVIEW (INVESTIGATIVE, SCRUTINY) | REVIEW_REQUIRED |
| 6 | Default | ALLOWED |

Hooks into certificate pipeline at issuance. Persists routing_hint on certificate. Creates TheatreAuditEvent. API filter: `GET /api/v1/certificates?routing_hint=REVIEW_REQUIRED`. Frontend: routing hint badge on certificate explorer (behind flag).

### Sprint 2: TAO Flow Metrics

New `TaoFlowAggregator` service. Computes time-windowed net capital inflow from TRADE + MIRROR_TRADE wing flap amounts. Runs on game loop at 60s cadence.

- `net_inflow_24h` = SUM(volume_usd) from trade flaps in last 24h
- `net_inflow_7d` = SUM(volume_usd) from trade flaps in last 7d
- Persisted on Timeline, exposed in API responses
- Frontend: flow badges on theatre/timeline cards (green/red/grey, behind flag)

**Confirmed:** WingFlap model has `volume_usd` field (not `amount`). No migration needed for this field.

### Sprint 3: Registry Schema Expansion

Formalise source metadata with `query_determinism` (pure_id_lookup / search_endpoint / bulk_export), `receipt_body_required`, `requires_legal_review`.

- Evidence submission enforces receipt requirement (422 when missing)
- Investigation detail API includes `has_legal_review_requirement` when any source needs legal review
- Frontend: registry badges + legal review warning (behind flag)

### Sprint 4: Coherence Gates

New `CoherenceGateEvaluator` service. Gate lifecycle: certificate → routing hint → gate evaluation → PENDING → manual review → PASSED/FAILED.

Rules for requiring review:
- routing_hint == REVIEW_REQUIRED → always
- INVESTIGATIVE inquiry + score < 0.8 → yes
- CONTESTED verification tier → yes

Deployment guard: `is_deployable = routing_hint != BLOCKED AND (not coherence_required OR gate == PASSED)`

New endpoints:
- `GET /api/v1/certificates/{id}/gate` — status + audit trail
- `POST /api/v1/certificates/{id}/gate/resolve` — resolve to PASSED/FAILED

All transitions logged as TheatreAuditEvent.

### Sprint 5: WebSocket Policy Events + Frontend Integration + Polish

Three new WS event types: ROUTING_DECISION, COHERENCE_GATE_TRANSITION, TAO_FLOW_ALERT.

Remove the three 017-scoped feature flags (`CYCLE_017_DEPLOYABILITY_ROUTING`, `CYCLE_017_REGISTRY_SCHEMA`, `CYCLE_017_COHERENCE_GATES`). `CYCLE_017_TAO_FLOW` is retained if it still gates staged Alpamayo behaviour beyond pure flow metrics. `WEBSOCKET_REALTIME` is a generic realtime gate used by the shared channel hook — it stays until all dependent surfaces (not just 017) are confirmed native. Delete `cycle017.ts` stubs, migrate types to canonical files. Wire all 017 fields into frontend natively. Polish responsive/loading/empty/error states. E2E test: theatre → certificate → routing → gate → verify `is_deployable` computed field (not the agent deployment flow, which is out of scope for this cycle).

---

## New Backend Services

| Service | File | Purpose |
|---------|------|---------|
| RoutingEvaluator | `backend/services/routing_evaluator.py` | Compute routing_hint from configurable policy rules |
| TaoFlowAggregator | `backend/services/tao_flow_aggregator.py` | Windowed capital flow aggregation |
| CoherenceGateEvaluator | `backend/services/coherence_gate_evaluator.py` | Gate lifecycle management |

---

## API Changes

### Extended Responses

- `TheatreCertificateResponse`: +routing_hint, +review_reason_code, +coherence_review_required, +coherence_gate_status, +coherence_reviewed_at, +is_deployable (computed)
- `TheatreCertificateSummaryResponse`: +routing_hint, +coherence_gate_status, +is_deployable
- Timeline response: +net_inflow_24h, +net_inflow_7d

### New Endpoints

- `GET /api/v1/certificates?routing_hint=X` — filter by routing status
- `GET /api/v1/certificates/{id}/gate` — gate status + audit trail
- `POST /api/v1/certificates/{id}/gate/resolve` — resolve gate

### Extended Endpoints

- `GET /api/v1/investigations/{id}` — includes `has_legal_review_requirement`
- `POST /api/v1/investigations/{id}/evidence` — enforces receipt_body_required

---

## WebSocket Event Additions

| Event Type | Trigger | Payload |
|------------|---------|---------|
| ROUTING_DECISION | Certificate issued | certificate_id, theatre_id, routing_hint, reason_code |
| COHERENCE_GATE_TRANSITION | Gate status change | certificate_id, from_status, to_status, reviewer_id |
| TAO_FLOW_ALERT | Flow threshold crossed | timeline_id, net_inflow_24h, threshold |

---

## Test Targets

33 new tests across 6 sprints. Post-017 expected: ≥1100 passed.

| Sprint | Tests | Focus |
|--------|-------|-------|
| 0 | 4 | Migration, schema extensions |
| 1 | 8 | Routing evaluation, pipeline integration, API filter |
| 2 | 6 | Flow aggregation, game loop, API response |
| 3 | 4 | Registry model, receipt enforcement, legal review flag |
| 4 | 6 | Gate lifecycle, audit events, deployment guard, API |
| 5 | 5 | WS events, frontend integration, E2E |

---

## Out of Scope

- Multi-user policy approval workflows
- Historical TAO flow charting (point-in-time aggregation only)
- Policy rule versioning or A/B testing
- External policy engine integration (OPA, Cedar, etc.)
- Automated gate resolution (manual review only)
- Chain anchoring for policy decisions
- OKLCH colour migration (remains P3)
- Investigation persistence to database (remains in-memory)
- Agent deployment flow (separate future cycle)

---

## Relationship to Handoff Matrix

The handoff matrix (`output/HANDOFF_MATRIX_ALEXANDER.md`) remains the frozen contract for empty states, routes, and vocabulary. Cycle 017 does not modify the handoff matrix — it extends the surfaces defined there with policy fields. The 017-scoped feature flags gate new UI until Sprint 5 removes them; `CYCLE_017_TAO_FLOW` and `WEBSOCKET_REALTIME` may persist if they still gate surfaces beyond this cycle's scope.

Open decisions from the handoff matrix that remain relevant:
1. Alpamayo path → keep staged shell (unchanged by 017)
2. Scenario Packs → leave deferred (unchanged by 017)
3. Agent deployment → keep staged modal (separate cycle)
4. Certificates → enhanced by 017 (routing + gate badges)
5. Route normalization → keep current (unchanged by 017)
6. Create Theatre editorial → keep staged (unchanged by 017)
