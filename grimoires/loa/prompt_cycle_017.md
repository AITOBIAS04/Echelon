# Cycle-017: Policy Surface — Implementation Prompt

**Date:** 6 March 2026
**Branch:** `feature/cycle-017-policy-surface` (create from `main`)
**Predecessor commit:** `16757a23` on `feature/cycle-016-results-surface` (merged)

---

## Mission

Implement Cycle 017 "Policy Surface" — the intelligence layer between raw results (certificates, scores, trades) and deployment decisions. Six sprints (0–5), five capability areas, 33 new tests, zero regressions against the existing ≥1060 baseline.

Execute sprint-by-sprint. After each sprint, run the full test suite and confirm zero regressions before proceeding.

---

## Planning Documents

All planning docs live in `grimoires/loa/`. Read each before starting:

| Document | Path | Purpose |
|----------|------|---------|
| **PRD** | `grimoires/loa/prd.md` | Requirements, success criteria, sprint breakdown, NFRs, out of scope |
| **SDD** | `grimoires/loa/sdd.md` | Architecture, data flow, service designs, code examples, testing strategy |
| **Sprint Plan** | `grimoires/loa/sprint.md` | Task-level breakdown with files, acceptance criteria, test counts |
| **Context** | `grimoires/loa/context/echelon_cycle_017.md` | Why this cycle exists, scaffolding inventory, decision points |
| **Handoff Matrix** | `output/HANDOFF_MATRIX_ALEXANDER.md` | Frozen contract for empty states, routes, vocabulary — do not modify |

---

## Pre-Answered Discovery Questions

These were researched and verified against the codebase. Do not re-investigate — use these answers directly.

### Q1: Source Registry Model — new table or extend existing?

An existing typed JSON-backed OSINT source registry lives at `backend/osint/models/registry.py`. **Extend the existing registry first** — add `query_determinism`, `receipt_body_required`, and `requires_legal_review` fields to the existing typed source entries. This keeps source metadata co-located and avoids a new DB table/migration. Only introduce a new `SourceRegistryEntry` DB table if Sprint 3 explicitly needs DB persistence beyond the JSON-backed approach.

### Q2: WingFlap field for TAO flow aggregation

The `WingFlap` model has a `volume_usd` field. There is **no `amount` field**. TAO flow aggregation must use `WingFlap.volume_usd`. No migration needed for this field — it already exists on the model.

Relevant fields on `WingFlap`: `volume_usd`, `stability_delta`, `flap_type`, `direction`, `timeline_stability`, `timeline_price`, `spawned_ripple`.

### Q3: Routing rules — hardcoded enum vs env-driven thresholds?

Use **env-driven thresholds** (Option B). The `RoutingPolicy` dataclass holds `block_below_score`, `review_below_score`, `always_review_inquiry_classes`, `block_tiers`, `review_tiers` — all configurable. Default values are provided (0.3, 0.6, etc.) but can be overridden. See SDD §3.1 for the full `RoutingPolicy` spec.

### Q4: Coherence gate resolve endpoint — auth pattern

Use `Depends(get_current_user)` from `backend/dependencies.py`. This returns a `TokenData` model with fields: `user_id`, `username`, `email`, `tier`. The reviewer identity is **`user.user_id`** (not `user.sub` — `TokenData` does not expose `sub`).

### Q5: E2E test scope — what does "deploy" mean?

The E2E test verifies the **`is_deployable` computed field** on the certificate response. It does NOT test the agent deployment flow (which is a staged modal with mock data — entirely out of scope for this cycle). The test creates a theatre → runs → settles → certificate issued → routing hint = REVIEW_REQUIRED → coherence gate PENDING → resolve gate PASSED → assert `is_deployable = true`.

---

## Sprint Execution Order

### Sprint 0: Schema Foundation + Migration
- Extend TheatreCertificate (6 new columns), Timeline (3 new columns)
- Extend source registry (prefer existing `backend/osint/models/registry.py`)
- Create Alembic migration `c017_policy_surface.py` (dialect-safe)
- Extend Pydantic schemas with optional/nullable fields + computed `is_deployable`
- **4 tests**, zero runtime logic

### Sprint 1: Deployability Routing
- New `RoutingEvaluator` service with `RoutingPolicy` dataclass
- Hook into certificate pipeline at issuance
- API filter: `GET /api/v1/certificates?routing_hint=REVIEW_REQUIRED`
- Frontend: routing hint badge behind `CYCLE_017_DEPLOYABILITY_ROUTING`
- **8 tests**

### Sprint 2: TAO Flow Metrics
- New `TaoFlowAggregator` — windowed SUM of `volume_usd` (not `amount`)
- Game loop integration at 60s cadence
- Timeline/theatre API responses include flow fields
- Frontend: flow badges behind `CYCLE_017_TAO_FLOW`
- **6 tests**

### Sprint 3: Registry Schema Expansion
- Extend existing OSINT registry with policy fields
- Evidence submission enforces `receipt_body_required` (422 when missing)
- Investigation detail includes `has_legal_review_requirement`
- Frontend: registry badges behind `CYCLE_017_REGISTRY_SCHEMA`
- **4 tests**

### Sprint 4: Coherence Gates
- New `CoherenceGateEvaluator` — gate lifecycle PENDING → PASSED/FAILED
- Audit event logging for all transitions
- Deployment guard: `is_deployable` computed field
- Gate API: GET status, POST resolve (auth via `Depends(get_current_user)`, identity is `user.user_id`)
- Frontend: gate status badge behind `CYCLE_017_COHERENCE_GATES`
- **6 tests**

### Sprint 5: WebSocket + Frontend + Polish
- 3 new WS events: ROUTING_DECISION, COHERENCE_GATE_TRANSITION, TAO_FLOW_ALERT
- Remove 3 flags: `CYCLE_017_DEPLOYABILITY_ROUTING`, `CYCLE_017_REGISTRY_SCHEMA`, `CYCLE_017_COHERENCE_GATES`
- Retain 2 flags: `CYCLE_017_TAO_FLOW` (if still gating Alpamayo), `WEBSOCKET_REALTIME` (generic gate)
- Delete `cycle017.ts` stubs, migrate types to canonical files
- Polish responsive/loading/empty/error states
- E2E test: full policy lifecycle → verify `is_deployable`
- Final audit: grep for stale flag references
- **5 tests**

---

## Critical Constraints

1. **Do not modify the handoff matrix.** It is a frozen contract.
2. **Do not implement agent deployment.** The `DeployAgentModal` is a staged mock — separate future cycle.
3. **Feature flags gate frontend only.** Backend services ship unconditionally; flags only wrap UI rendering.
4. **All new DB columns are nullable or have safe defaults.** Zero breaking changes to existing API consumers.
5. **Existing ≥1060 tests must pass after every sprint.** 8 pre-existing async heartbeat failures are known and tolerated.
6. **TAO flow uses `volume_usd`, not `amount`.** The `amount` field does not exist on `WingFlap`.
7. **Auth uses `user.user_id`, not `user.sub`.** `TokenData` from `get_current_user` exposes `user_id`.
8. **Source registry: extend existing first.** `backend/osint/models/registry.py` has a typed JSON-backed registry. New DB table only if explicitly needed.

---

## Out of Scope

- Multi-user policy approval workflows
- Historical TAO flow charting (point-in-time only)
- Policy rule versioning or A/B testing
- External policy engine (OPA, Cedar)
- Automated gate resolution (manual only)
- Chain anchoring for policy decisions
- OKLCH colour migration
- Investigation persistence to database
- Agent deployment flow
