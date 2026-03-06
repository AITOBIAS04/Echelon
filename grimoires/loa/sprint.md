# Sprint Plan — Cycle-017: Policy Surface

**Cycle:** cycle-017
**Date:** 6 March 2026
**PRD:** grimoires/loa/prd_017.md
**SDD:** grimoires/loa/sdd_017.md
**Sprints:** 6 (0–5)
**Baseline:** ≥1060 passed (post-016), 8 pre-existing async heartbeat failures

---

## Sprint 0: Schema Foundation + Migration

Extend all backend models with Cycle 017 columns. Create the Alembic migration. Extend Pydantic schemas. No runtime logic — just the data layer.

### Task 0.1: Model Layer — Add All 017 Columns

**Files modified:**
- `backend/database/models.py` — TheatreCertificate (routing + coherence), Timeline (TAO flow)

**TheatreCertificate additions:**

```python
routing_hint: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True, index=True)
review_reason_code: Mapped[Optional[str]] = mapped_column(
    String(100), nullable=True)
coherence_review_required: Mapped[bool] = mapped_column(
    Boolean, default=False)
coherence_gate_status: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True)
coherence_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True)
coherence_reviewer_id: Mapped[Optional[str]] = mapped_column(
    String(50), nullable=True)
```

**Timeline additions:**

```python
net_inflow_24h: Mapped[float] = mapped_column(Float, default=0.0)
net_inflow_7d: Mapped[float] = mapped_column(Float, default=0.0)
flow_updated_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True)
```

**Acceptance Criteria:**
- [ ] TheatreCertificate has 6 new columns (routing_hint, review_reason_code, coherence_review_required, coherence_gate_status, coherence_reviewed_at, coherence_reviewer_id)
- [ ] Timeline has 3 new columns (net_inflow_24h, net_inflow_7d, flow_updated_at)
- [ ] All new columns are nullable or have safe defaults
- [ ] Existing model tests pass unchanged

### Task 0.2: Source Registry Model

**Context:** An existing typed JSON-backed OSINT source registry lives at `backend/osint/models/registry.py`. Prefer extending the existing registry with policy fields. Only create a new `SourceRegistryEntry` DB table if Sprint 3 explicitly needs DB persistence beyond the JSON-backed approach.

**Files:**
- `backend/osint/models/registry.py` — extend existing typed entries with policy fields
- Verify `backend/investigation/evidence_envelope.py` source handling

**Default path — extend existing OSINT registry:**

Add `query_determinism`, `receipt_body_required`, and `requires_legal_review` fields to the existing typed source entries in `backend/osint/models/registry.py`. This keeps source metadata co-located and avoids a new DB table.

**Fallback (only if DB persistence needed):**

```python
class SourceRegistryEntry(Base):
    __tablename__ = "source_registry"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50))
    query_determinism: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True)
    receipt_body_required: Mapped[bool] = mapped_column(
        Boolean, default=False)
    requires_legal_review: Mapped[bool] = mapped_column(
        Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
```

**Acceptance Criteria:**
- [ ] Registry fields exist on source entries (either in-registry or DB-backed)
- [ ] query_determinism accepts: pure_id_lookup, search_endpoint, bulk_export
- [ ] receipt_body_required defaults to False
- [ ] requires_legal_review defaults to False

### Task 0.3: Alembic Migration

**New file:** `backend/alembic/versions/c017_policy_surface.py`

Dialect-safe migration:

1. Add 6 columns to `theatre_certificates`
2. Add 3 columns to `timelines`
3. If DB persistence path chosen: create `source_registry` table. Otherwise skip (fields live in existing OSINT registry).
4. Create index on `theatre_certificates.routing_hint`

**Acceptance Criteria:**
- [ ] Migration runs clean on PostgreSQL
- [ ] Migration runs clean on SQLite (dialect-safe)
- [ ] Downgrade removes all new columns/table
- [ ] 2 tests: upgrade/downgrade round-trip, verify column existence

### Task 0.4: Pydantic Schema Extensions

**Files modified:**
- `backend/schemas/theatre.py` — extend TheatreCertificateResponse, TheatreCertificateSummaryResponse
- `backend/schemas/butterfly_schemas.py` — extend timeline response (if applicable)

**TheatreCertificateResponse additions:**

```python
routing_hint: Optional[str] = None
review_reason_code: Optional[str] = None
coherence_review_required: bool = False
coherence_gate_status: Optional[str] = None
coherence_reviewed_at: Optional[datetime] = None
is_deployable: bool = True  # computed
```

**TheatreCertificateSummaryResponse additions:**

```python
routing_hint: Optional[str] = None
coherence_gate_status: Optional[str] = None
is_deployable: bool = True  # computed
```

**Timeline response additions:**

```python
net_inflow_24h: float = 0.0
net_inflow_7d: float = 0.0
```

**Acceptance Criteria:**
- [ ] All new fields are optional or have safe defaults
- [ ] Existing API consumers see no breaking changes
- [ ] `is_deployable` is computed from routing_hint + coherence_gate_status
- [ ] 2 tests: serialise certificate with/without 017 fields, verify defaults

### Sprint 0 Summary Target

- **4 tests**
- **3–5 files modified/created**
- **Zero regressions** on existing 1060+ tests
- All 017 columns exist and are queryable

---

## Sprint 1: Deployability Routing

Build the routing evaluation engine. Compute routing hints at certificate issuance. Expose via API.

### Task 1.1: RoutingEvaluator Service

**New file:** `backend/services/routing_evaluator.py`

Configurable policy with priority-ordered rules:

| Priority | Rule | Result |
|----------|------|--------|
| 1 | verification_tier in BLOCKED_TIERS (REJECTED) | BLOCKED |
| 2 | composite_score < block_threshold (0.3) | BLOCKED |
| 3 | verification_tier in REVIEW_TIERS (DRAFT, CONTESTED) | REVIEW_REQUIRED |
| 4 | composite_score < review_threshold (0.6) | REVIEW_REQUIRED |
| 5 | inquiry_class in ALWAYS_REVIEW (INVESTIGATIVE, SCRUTINY) | REVIEW_REQUIRED |
| 6 | Default | ALLOWED |

Each rule produces a `RoutingDecision(hint, reason_code, rule_name)`.

4 tests:
1. Score below block threshold → BLOCKED + reason code
2. INVESTIGATIVE inquiry class + good score → REVIEW_REQUIRED
3. REJECTED tier → BLOCKED regardless of score
4. Good score + COUNTERFACTUAL → ALLOWED

**Acceptance Criteria:**
- [x] RoutingEvaluator with RoutingPolicy dataclass
- [x] evaluate() returns RoutingDecision
- [x] First matching rule wins (priority order)
- [x] All 4 tests pass

### Task 1.2: Certificate Pipeline Integration

**Files modified:**
- `backend/services/certificate_pipeline.py` — hook routing evaluation after scoring

After certificate scores are computed, before persistence:

```python
evaluator = RoutingEvaluator()
decision = evaluator.evaluate(certificate)
certificate.routing_hint = decision.hint.value
certificate.review_reason_code = decision.reason_code
```

Also create a `TheatreAuditEvent` with `event_type="ROUTING_DECISION"`.

2 tests:
1. Certificate issuance produces routing_hint
2. Audit event logged with correct detail_json

**Acceptance Criteria:**
- [x] Every new certificate gets a routing_hint
- [x] routing_hint persisted to DB
- [x] Audit event with ROUTING_DECISION type created
- [x] Both tests pass

### Task 1.3: API Filter — Certificates by Routing Hint

**Files modified:**
- `backend/api/theatre_routes.py` — extend `GET /api/v1/certificates` with `routing_hint` query param

```python
@router.get("/api/v1/certificates")
async def list_certificates(
    routing_hint: Optional[str] = Query(None),
    ...
):
    query = select(TheatreCertificate)
    if routing_hint:
        query = query.where(
            TheatreCertificate.routing_hint == routing_hint.upper()
        )
    ...
```

1 test:
1. Filter returns only certificates matching routing_hint

**Acceptance Criteria:**
- [x] `GET /api/v1/certificates?routing_hint=REVIEW_REQUIRED` works
- [x] Invalid routing_hint values return empty list (not error)
- [x] Test passes

### Task 1.4: Frontend — Routing Hint Badge (Behind Flag)

**Files modified:**
- `frontend/src/pages/CertificatesPage.tsx` — conditional routing badge
- `frontend/src/hooks/useCertificateGallery.ts` — parse new response fields

Behind `isEnabled('CYCLE_017_DEPLOYABILITY_ROUTING')`:
- Show `RoutingHintBadge` on certificate cards (reuse from investigation cert view)
- ALLOWED = green, REVIEW_REQUIRED = amber, BLOCKED = red

1 test:
1. Badge renders correct colour for each routing_hint value

**Acceptance Criteria:**
- [x] Badge only appears when flag enabled
- [x] Correct colours for all 3 routing_hint values
- [x] Test passes

### Sprint 1 Summary Target

- **8 tests**
- **3 new files, 3 modified**
- RoutingEvaluator computes hints; pipeline persists them; API exposes and filters; frontend renders (flagged)

---

## Sprint 2: TAO Flow Metrics

Build windowed capital flow aggregation. Surface on timeline/theatre responses.

### Task 2.1: TaoFlowAggregator Service

**New file:** `backend/services/tao_flow_aggregator.py`

Core method: windowed SUM of trade-type wing flap `volume_usd` values.

```python
async def compute_for_timeline(session, timeline_id, now=None):
    """Returns (net_inflow_24h, net_inflow_7d)."""
```

`compute_all()` iterates active timelines and updates their flow fields.

3 tests:
1. 24h window with mixed buy/sell → correct net
2. 7d window computation
3. Zero trades → 0.0 for both windows

**Acceptance Criteria:**
- [x] Correctly sums TRADE + MIRROR_TRADE flap `volume_usd` values
- [x] Uses indexed timestamp column for windowed queries
- [x] Returns (0.0, 0.0) when no trades exist
- [x] All 3 tests pass

### Task 2.2: Game Loop Integration

**Files modified:**
- `backend/worker/game_loop.py` — add TAO flow aggregation at 60s cadence

```python
if tick_count % 12 == 0:  # 60s at 5s tick
    aggregator = TaoFlowAggregator()
    await aggregator.compute_all(session)
```

1 test:
1. Game loop calls compute_all on correct cadence

**Acceptance Criteria:**
- [x] TAO flow runs every 60s (not every tick)
- [x] Does not block game loop (async)
- [x] Test passes

### Task 2.3: API Response Extensions

**Files modified:**
- `backend/schemas/butterfly_schemas.py` (or wherever timeline responses live)
- `backend/api/theatre_routes.py` — theatre detail includes flow from associated timeline

Response fields added in Sprint 0 schema work; this task verifies they serialize correctly.

1 test:
1. Timeline API response includes net_inflow_24h and net_inflow_7d

**Acceptance Criteria:**
- [x] Both flow fields present in API response
- [x] Default 0.0 when no aggregation has run
- [x] Test passes

### Task 2.4: Frontend — Flow Badges (Behind Flag)

**Files modified:**
- `frontend/src/pages/MarketplacePage.tsx` — flow badge on theatre cards
- `frontend/src/pages/WorldMonitorPage.tsx` — flow badge on timeline cards

Behind `isEnabled('CYCLE_017_TAO_FLOW')`:
- Badge shows net_inflow_24h
- Green (positive), red (negative), grey (zero)
- Tooltip: "24h: +$1,234 / 7d: -$567"

1 test:
1. Badge renders correct colour and value

**Acceptance Criteria:**
- [x] Badge only appears when flag enabled
- [x] Correct colour for positive/negative/zero
- [x] Test passes

### Sprint 2 Summary Target

- **6 tests**
- **1 new file, 3 modified**
- TAO flow aggregation runs on game loop; updates timeline fields; API exposes; frontend renders (flagged)

---

## Sprint 3: Registry Schema Expansion

Extend source metadata with query determinism, receipt requirements, and legal review flags.

### Task 3.1: Source Registry Model + Seed Data

**Files modified:**
- `backend/osint/models/registry.py` — extend existing typed entries with policy fields
- If DB path: `backend/database/models.py` + migration from Sprint 0

Seed known sources with appropriate registry fields:
- Polymarket → `pure_id_lookup`, no receipt, no legal review
- Companies House → `search_endpoint`, receipt required, no legal review
- Private leak sources → `bulk_export`, receipt required, legal review required

1 test:
1. Source registry entries correctly store and return policy fields

**Acceptance Criteria:**
- [x] Policy fields accessible on source entries (in-registry or DB-backed)
- [x] Seed data applied for known sources
- [x] Test passes

### Task 3.2: Evidence Submission — Receipt Enforcement

**Files modified:**
- `backend/investigation/evidence_envelope.py` — check receipt_body_required
- `backend/api/investigation_routes.py` — validate on evidence POST

When source has `receipt_body_required=True`:
- Evidence submission without `receipt_body` returns 422
- Evidence submission with `receipt_body` proceeds normally

2 tests:
1. Submit evidence without receipt when required → 422
2. Submit evidence with receipt when required → 200

**Acceptance Criteria:**
- [x] 422 with clear error message when receipt missing
- [x] Normal flow when receipt present
- [x] Non-required sources unaffected
- [x] Both tests pass

### Task 3.3: Legal Review Flag — Investigation Detail API

**Files modified:**
- `backend/api/investigation_routes.py` — extend detail response
- `backend/schemas/investigation_schemas.py` — add `has_legal_review_requirement`

When any evidence source in an investigation has `requires_legal_review=True`, the investigation detail response includes `has_legal_review_requirement: true`.

1 test:
1. Investigation with legal-review source returns flag=true

**Acceptance Criteria:**
- [x] Flag computed from source registry entries
- [x] Default false when no legal review sources
- [x] Test passes

### Task 3.4: Frontend — Registry Badges (Behind Flag)

**Files modified:**
- `frontend/src/pages/InvestigationPage.tsx` — legal review warning badge
- `frontend/src/components/investigation/EvidenceItemCard.tsx` — source type badge

Behind `isEnabled('CYCLE_017_REGISTRY_SCHEMA')`:
- Evidence items show query determinism badge
- Legal review warning at investigation header when `has_legal_review_requirement`

No tests (visual integration, verified manually).

**Acceptance Criteria:**
- [x] Badges only appear when flag enabled
- [x] Legal review warning is prominent but not blocking

### Sprint 3 Summary Target

- **4 tests**
- **2 files modified, 0–1 new**
- Registry fields enforced on evidence submission; legal review flagged; frontend renders (flagged)

---

## Sprint 4: Coherence Gates

Build the post-routing coherence gate system. Gate lifecycle: PENDING → PASSED / FAILED.

### Task 4.1: CoherenceGateEvaluator Service

**New file:** `backend/services/coherence_gate_evaluator.py`

Rules for requiring coherence review:
- `routing_hint == REVIEW_REQUIRED` → always
- `inquiry_class == INVESTIGATIVE` and `composite_score < 0.8` → yes
- `verification_tier == CONTESTED` → yes
- Otherwise → no

Methods: `should_require_review()`, `open_gate()`, `resolve_gate()`

3 tests:
1. REVIEW_REQUIRED routing → gate opens (PENDING)
2. resolve_gate(PASSED) → status + timestamp + reviewer
3. resolve_gate(FAILED) → status + timestamp + reviewer

**Acceptance Criteria:**
- [x] should_require_review correctly evaluates conditions
- [x] open_gate sets coherence_review_required=True, gate_status=PENDING
- [x] resolve_gate sets status, timestamp, reviewer_id
- [x] All 3 tests pass

### Task 4.2: Audit Event Logging

**Files modified:**
- `backend/services/coherence_gate_evaluator.py` — create TheatreAuditEvent on transitions

Audit events:
- `COHERENCE_GATE_OPENED` — when gate goes to PENDING
- `COHERENCE_GATE_RESOLVED` — when gate goes to PASSED/FAILED

detail_json includes: certificate_id, from_status, to_status, reviewer_id (if resolve)

1 test:
1. Gate open + resolve creates 2 audit events with correct types

**Acceptance Criteria:**
- [x] Both event types logged
- [x] detail_json contains all context
- [x] Test passes

### Task 4.3: Deployment Guard

**Files modified:**
- `backend/schemas/theatre.py` — `is_deployable` computed field

```python
@model_validator(mode="after")
def compute_is_deployable(self) -> "TheatreCertificateResponse":
    if self.routing_hint == "BLOCKED":
        self.is_deployable = False
    elif self.coherence_review_required and self.coherence_gate_status != "PASSED":
        self.is_deployable = False
    else:
        self.is_deployable = True
    return self
```

1 test:
1. BLOCKED → not deployable, PENDING gate → not deployable, PASSED gate → deployable

**Acceptance Criteria:**
- [x] is_deployable correctly reflects routing + gate status
- [x] Test passes

### Task 4.4: Gate Status API Endpoint

**Files modified:**
- `backend/api/theatre_routes.py` — add gate endpoints

```
GET  /api/v1/certificates/{id}/gate         — gate status + audit trail
POST /api/v1/certificates/{id}/gate/resolve  — resolve gate (PASSED/FAILED)
```

Auth: resolve endpoint uses `Depends(get_current_user)` from `backend/dependencies.py`. Reviewer identity is `user.user_id` from the `TokenData` model (not `user.sub`).

1 test:
1. POST resolve → GET shows updated status + audit trail

**Acceptance Criteria:**
- [x] GET returns gate status, reviewer, timestamp, audit events
- [x] POST validates status is PASSED or FAILED
- [x] Only resolves gates in PENDING state
- [x] Test passes

### Task 4.5: Frontend — Gate Status Badge (Behind Flag)

**Files modified:**
- `frontend/src/pages/CertificatesPage.tsx` — gate status column
- New or extended certificate detail component

Behind `isEnabled('CYCLE_017_COHERENCE_GATES')`:
- PENDING = amber pulse, PASSED = green, FAILED = red
- `is_deployable` indicator on certificate card

No tests (visual integration).

**Acceptance Criteria:**
- [x] Badge only appears when flag enabled
- [x] Correct colours for all 3 gate states
- [x] is_deployable indicator clear

### Sprint 4 Summary Target

- **6 tests**
- **1 new file, 2 modified**
- Gate lifecycle works; deployment guard enforced; API endpoint exposes; frontend renders (flagged)

---

## Sprint 5: WebSocket Policy Events + Frontend Integration + Polish

Extend WS with policy events. Remove 017-scoped feature flags (retain `CYCLE_017_TAO_FLOW` and `WEBSOCKET_REALTIME` if still gating non-017 surfaces). Final integration and polish.

### Task 5.1: WebSocket Policy Event Types

**Files modified:**
- `backend/websockets/realtime_manager.py` — 3 new broadcast methods

```python
broadcast_routing_decision(certificate_id, decision)
broadcast_coherence_gate_transition(certificate_id, transition)
broadcast_tao_flow_alert(timeline_id, alert)
```

Hook broadcasts into:
- `certificate_pipeline.py` → ROUTING_DECISION
- `coherence_gate_evaluator.py` → COHERENCE_GATE_TRANSITION
- `tao_flow_aggregator.py` → TAO_FLOW_ALERT (when threshold crossed)

2 tests:
1. Certificate issuance triggers ROUTING_DECISION WS event
2. Gate resolution triggers COHERENCE_GATE_TRANSITION WS event

**Acceptance Criteria:**
- [x] All 3 event types broadcast correctly
- [x] Events include correct payloads
- [x] Both tests pass

### Task 5.2: Frontend — Remove 017-Scoped Feature Flags

**Files modified:**
- All pages/components that check `isEnabled('CYCLE_017_*')` — remove checks
- `frontend/src/lib/featureFlags.ts` — remove 017-scoped flag definitions

Remove the three flags whose sole purpose is gating 017 UI:
- `CYCLE_017_DEPLOYABILITY_ROUTING` — remove
- `CYCLE_017_REGISTRY_SCHEMA` — remove
- `CYCLE_017_COHERENCE_GATES` — remove

Retain flags with broader scope:
- `CYCLE_017_TAO_FLOW` — retain if it still gates staged Alpamayo behaviour beyond pure flow metrics
- `WEBSOCKET_REALTIME` — retain; this is a generic realtime gate used by the shared channel hook, not a disposable 017-only shim

Replace all patterns like:

```typescript
{isEnabled('CYCLE_017_DEPLOYABILITY_ROUTING') && <RoutingHintBadge />}
```

With:

```typescript
<RoutingHintBadge />
```

**Acceptance Criteria:**
- [x] Zero `isEnabled('CYCLE_017_DEPLOYABILITY_ROUTING')`, `CYCLE_017_REGISTRY_SCHEMA`, or `CYCLE_017_COHERENCE_GATES` references in codebase
- [x] All 017 routing/registry/coherence UI renders unconditionally
- [x] `CYCLE_017_TAO_FLOW` and `WEBSOCKET_REALTIME` retained with clear comments on remaining dependencies

### Task 5.3: Frontend — Delete Stubs, Extend Real Types

**Files modified/deleted:**
- **Delete:** `frontend/src/types/cycle017.ts`
- **Extend:** `frontend/src/types/theatre.ts` — add routing_hint, coherence fields, is_deployable, TAO flow
- **Extend:** `frontend/src/types/index.ts` — add RoutingHint, GateStatus union types
- **Extend:** `frontend/src/types/investigation.ts` — add registry schema fields (if applicable)

**Acceptance Criteria:**
- [x] `cycle017.ts` deleted
- [x] All 017 types live on their canonical type files
- [x] Zero imports from `cycle017.ts` in codebase

### Task 5.4: Frontend — Polish + States

**Files modified:**
- All pages with 017 additions — verify loading, empty, error states
- Responsive layout for new badges/columns

2 tests:
1. Certificate explorer renders all 017 fields correctly
2. Timeline card renders TAO flow badge correctly

**Acceptance Criteria:**
- [x] Loading skeletons for new data
- [x] Empty states when fields are null
- [x] Responsive on narrow viewports
- [x] Both tests pass

### Task 5.5: E2E Test — Full Policy Lifecycle

1 test:
1. Create theatre → run → settle → certificate issued → routing hint = REVIEW_REQUIRED → coherence gate PENDING → resolve gate PASSED → verify `is_deployable = true` (computed field, not the agent deployment flow which is out of scope)

**Acceptance Criteria:**
- [x] Full lifecycle works end-to-end
- [x] All intermediate states correct
- [x] Test passes

### Task 5.6: Final Audit

Grep-based audit:
- Zero `CYCLE_017_DEPLOYABILITY_ROUTING`, `CYCLE_017_REGISTRY_SCHEMA`, or `CYCLE_017_COHERENCE_GATES` references
- Zero imports from `cycle017.ts`
- Zero `isEnabled` calls for the three removed flags
- `CYCLE_017_TAO_FLOW` and `WEBSOCKET_REALTIME` retained only if still gating non-017 surfaces
- All new fields present in API responses

**Acceptance Criteria:**
- [x] Clean audit
- [x] Build passes
- [x] All tests pass

### Sprint 5 Summary Target

- **5 tests**
- **Multiple files modified, 1 deleted**
- WS policy events live; feature flags removed; types migrated; all UI native; E2E verified

---

## Test Summary

| Sprint | New Tests | Cumulative |
|--------|-----------|------------|
| 0 | 4 | 4 |
| 1 | 8 | 12 |
| 2 | 6 | 18 |
| 3 | 4 | 22 |
| 4 | 6 | 28 |
| 5 | 5 | 33 |

**Post-017 expected:** ≥1100 passed (1060 baseline + ~33 new + overlap/consolidation margin).

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| WingFlap field name | **Resolved:** field is `volume_usd`, not `amount`. No migration needed. |
| Source metadata model approach | Existing typed OSINT registry at `backend/osint/models/registry.py` — extend first, new DB table only if persistence needed |
| Investigation persistence is in-memory | Registry fields work in-memory too; DB persistence is a separate cycle |
| TAO flow queries may be slow at scale | Index on (timeline_id, flap_type, timestamp); async aggregation |
| Gate resolution has no multi-user workflow | Out of scope; single-reviewer model in this cycle |
