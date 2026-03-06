# SDD — Cycle-017: Policy Surface

**Cycle:** cycle-017
**Date:** 6 March 2026
**PRD:** grimoires/loa/prd.md
**Design input:** `cycle017.ts` (type stubs), `featureFlags.ts`, `HANDOFF_MATRIX_ALEXANDER.md`

---

## 1. Architecture Overview

Cycle 017 adds a **policy layer** between raw results (certificates, scores, trades) and deployment decisions. The layer spans four new backend services, a schema migration, and frontend integration behind feature flags.

```
┌─────────────────────────────────────────────────────────┐
│                   POLICY SURFACE (017)                   │
│                                                          │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Routing        │  │ TAO Flow     │  │ Coherence    │ │
│  │ Evaluator      │  │ Aggregator   │  │ Gate         │ │
│  │                │  │              │  │ Evaluator    │ │
│  │ certificate →  │  │ wing_flaps → │  │ certificate →│ │
│  │ routing_hint   │  │ net_inflow   │  │ gate_status  │ │
│  └───────┬────────┘  └──────┬───────┘  └──────┬───────┘ │
│          │                   │                  │         │
│  ┌───────▼───────────────────▼──────────────────▼───────┐│
│  │              Registry Schema Expansion                ││
│  │  query_determinism, receipt_body_required,             ││
│  │  requires_legal_review                                ││
│  └───────┬───────────────────┬──────────────────┬───────┘│
│          │                   │                  │         │
└──────────┼───────────────────┼──────────────────┼────────┘
           │                   │                  │
    ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
    │ Certificate │    │  Timeline   │    │   Audit     │
    │   Model     │    │   Model     │    │   Events    │
    │ (extended)  │    │ (extended)  │    │ (gate log)  │
    └─────────────┘    └─────────────┘    └─────────────┘
```

### 1.1 Data Flow

**Routing evaluation** hooks into the existing certificate pipeline:

```
Theatre resolves
  → CertificatePipeline.issue()
    → RoutingEvaluator.evaluate(certificate) → routing_hint, review_reason_code
      → certificate.routing_hint = result
      → TheatreAuditEvent(ROUTING_DECISION)
        → WS broadcast: ROUTING_DECISION
```

**TAO flow aggregation** runs on the game loop:

```
Game loop tick (60s cadence)
  → TaoFlowAggregator.compute_all()
    → SELECT SUM(volume_usd) FROM wing_flaps WHERE type='TRADE' AND timestamp > now-24h
      → timeline.net_inflow_24h = result
      → timeline.net_inflow_7d = result_7d
        → WS broadcast: TAO_FLOW_ALERT (if threshold crossed)
```

**Coherence gates** fire after routing:

```
Certificate receives routing_hint
  → CoherenceGateEvaluator.evaluate(certificate)
    → if requires_coherence_review(routing_hint, inquiry_class):
        certificate.coherence_review_required = True
        certificate.coherence_gate_status = PENDING
        → TheatreAuditEvent(COHERENCE_GATE_OPENED)
          → WS broadcast: COHERENCE_GATE_TRANSITION
```

---

## 2. Sprint 0 — Schema Foundation + Migration

### 2.1 Model Extensions

**Modified:** `backend/database/models.py`

TheatreCertificate additions:

```python
# Deployability Routing (Sprint 1)
routing_hint: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True, index=True,
    comment="ALLOWED | REVIEW_REQUIRED | BLOCKED"
)
review_reason_code: Mapped[Optional[str]] = mapped_column(
    String(100), nullable=True,
    comment="Machine-readable reason for routing decision"
)

# Coherence Gates (Sprint 4)
coherence_review_required: Mapped[bool] = mapped_column(
    Boolean, default=False,
    comment="Whether certificate requires coherence review before deployment"
)
coherence_gate_status: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True,
    comment="PENDING | PASSED | FAILED"
)
coherence_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True,
    comment="When coherence review was completed"
)
coherence_reviewer_id: Mapped[Optional[str]] = mapped_column(
    String(50), nullable=True,
    comment="Who reviewed (user_id or SYSTEM)"
)
```

Timeline additions:

```python
# TAO Flow Metrics (Sprint 2)
net_inflow_24h: Mapped[float] = mapped_column(
    Float, default=0.0,
    comment="Net capital inflow over last 24 hours"
)
net_inflow_7d: Mapped[float] = mapped_column(
    Float, default=0.0,
    comment="Net capital inflow over last 7 days"
)
flow_updated_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True,
    comment="Last TAO flow aggregation timestamp"
)
```

### 2.2 Registry Schema Extension

Registry/source metadata fields. These extend the existing typed OSINT source registry at `backend/osint/models/registry.py`. May also be surfaced on `EvidenceItem` or a new `SourceRegistryEntry` DB table if persistence beyond the JSON-backed registry is needed:

```python
# Registry Schema (Sprint 3)
query_determinism: Mapped[Optional[str]] = mapped_column(
    String(30), nullable=True,
    comment="pure_id_lookup | search_endpoint | bulk_export"
)
receipt_body_required: Mapped[bool] = mapped_column(
    Boolean, default=False,
    comment="Whether evidence submission requires a receipt body"
)
requires_legal_review: Mapped[bool] = mapped_column(
    Boolean, default=False,
    comment="Whether evidence from this source requires legal review"
)
```

### 2.3 Migration

**New:** `backend/alembic/versions/c017_policy_surface.py`

Dialect-safe migration:

1. Add routing columns to `theatre_certificates` (nullable)
2. Add coherence columns to `theatre_certificates` (nullable, boolean defaults)
3. Add TAO flow columns to `timelines` (float defaults 0.0)
4. If DB persistence path: add `source_registry` table. Otherwise skip (fields live in existing OSINT registry).
5. Create index on `theatre_certificates.routing_hint`

### 2.4 Pydantic Schema Extensions

**Modified:** `backend/schemas/theatre.py`

```python
class TheatreCertificateResponse(BaseModel):
    # ... existing fields ...

    # Cycle 017: Deployability Routing
    routing_hint: Optional[str] = None  # ALLOWED | REVIEW_REQUIRED | BLOCKED
    review_reason_code: Optional[str] = None

    # Cycle 017: Coherence Gates
    coherence_review_required: bool = False
    coherence_gate_status: Optional[str] = None  # PENDING | PASSED | FAILED
    coherence_reviewed_at: Optional[datetime] = None
```

**Modified:** `backend/schemas/butterfly_schemas.py` (or timeline response schema)

```python
class TimelineResponse(BaseModel):
    # ... existing fields ...

    # Cycle 017: TAO Flow
    net_inflow_24h: float = 0.0
    net_inflow_7d: float = 0.0
    flow_updated_at: Optional[datetime] = None
```

---

## 3. Sprint 1 — Deployability Routing

### 3.1 RoutingEvaluator Service

**New:** `backend/services/routing_evaluator.py`

```python
from enum import Enum
from typing import Optional
from dataclasses import dataclass

class RoutingHint(str, Enum):
    ALLOWED = "ALLOWED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"

@dataclass
class RoutingDecision:
    hint: RoutingHint
    reason_code: Optional[str]
    rule_name: str  # which rule triggered

@dataclass
class RoutingPolicy:
    """Configurable policy rules for routing evaluation."""
    # Score thresholds
    block_below_score: float = 0.3
    review_below_score: float = 0.6

    # Inquiry class overrides
    always_review_inquiry_classes: list[str] = field(
        default_factory=lambda: ["INVESTIGATIVE", "SCRUTINY"]
    )

    # Verification tier rules
    block_tiers: list[str] = field(
        default_factory=lambda: ["REJECTED"]
    )
    review_tiers: list[str] = field(
        default_factory=lambda: ["DRAFT", "CONTESTED"]
    )

class RoutingEvaluator:
    """Evaluates deployability routing for theatre certificates."""

    def __init__(self, policy: Optional[RoutingPolicy] = None):
        self.policy = policy or RoutingPolicy()

    def evaluate(self, certificate) -> RoutingDecision:
        """
        Evaluate routing hint for a certificate.
        Rules are evaluated in priority order (first match wins):
        1. Blocked tiers → BLOCKED
        2. Score below block threshold → BLOCKED
        3. Review tiers → REVIEW_REQUIRED
        4. Score below review threshold → REVIEW_REQUIRED
        5. Always-review inquiry classes → REVIEW_REQUIRED
        6. Default → ALLOWED
        """
        ...
```

### 3.2 Certificate Pipeline Integration

**Modified:** `backend/services/certificate_pipeline.py`

After certificate scoring, before persistence:

```python
from backend.services.routing_evaluator import RoutingEvaluator

evaluator = RoutingEvaluator()
decision = evaluator.evaluate(certificate)
certificate.routing_hint = decision.hint.value
certificate.review_reason_code = decision.reason_code

# Audit
audit_event = TheatreAuditEvent(
    theatre_id=certificate.theatre_id,
    event_type="ROUTING_DECISION",
    detail_json={
        "routing_hint": decision.hint.value,
        "reason_code": decision.reason_code,
        "rule_name": decision.rule_name,
    }
)
```

### 3.3 API Extensions

**Modified:** `backend/api/theatre_routes.py`

- `GET /api/v1/certificates` — add `routing_hint` query parameter for filtering
- `GET /api/v1/theatres/{id}/certificate` — response already includes new fields via schema extension
- Responses include `routing_hint` and `review_reason_code` when present

### 3.4 Frontend Integration

Behind `CYCLE_017_DEPLOYABILITY_ROUTING` flag:

- `RoutingHintBadge` component (already exists from Cycle 016 investigation cert view)
- Certificate explorer card shows routing hint badge
- Certificate detail page shows review reason when REVIEW_REQUIRED

---

## 4. Sprint 2 — TAO Flow Metrics

### 4.1 TaoFlowAggregator Service

**New:** `backend/services/tao_flow_aggregator.py`

```python
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class TaoFlowAggregator:
    """Computes time-windowed net capital inflow for timelines."""

    async def compute_for_timeline(
        self,
        session: AsyncSession,
        timeline_id: str,
        now: Optional[datetime] = None,
    ) -> tuple[float, float]:
        """
        Returns (net_inflow_24h, net_inflow_7d).

        Net inflow = sum of trade amounts where:
        - Wing flaps of type TRADE or MIRROR_TRADE
        - Positive volume_usd = buy (inflow), negative = sell (outflow)
        - Windowed by timestamp
        """
        now = now or datetime.utcnow()

        # 24h window
        inflow_24h = await self._windowed_sum(
            session, timeline_id, now - timedelta(hours=24), now
        )

        # 7d window
        inflow_7d = await self._windowed_sum(
            session, timeline_id, now - timedelta(days=7), now
        )

        return (inflow_24h, inflow_7d)

    async def compute_all(self, session: AsyncSession) -> int:
        """
        Compute TAO flow for all active timelines.
        Called from game loop on 60s cadence.
        Returns count of timelines updated.
        """
        ...

    async def _windowed_sum(
        self,
        session: AsyncSession,
        timeline_id: str,
        start: datetime,
        end: datetime,
    ) -> float:
        """SUM(volume_usd) from trade-type wing flaps in time window."""
        stmt = (
            select(func.coalesce(func.sum(WingFlap.volume_usd), 0.0))
            .where(
                WingFlap.timeline_id == timeline_id,
                WingFlap.flap_type.in_(["TRADE", "MIRROR_TRADE"]),
                WingFlap.timestamp >= start,
                WingFlap.timestamp <= end,
            )
        )
        result = await session.execute(stmt)
        return float(result.scalar_one())
```

### 4.2 Game Loop Integration

**Modified:** `backend/worker/game_loop.py`

Add TAO flow aggregation at 60s cadence alongside existing evidence (120s) and divergence (60s) stubs:

```python
# TAO flow aggregation (60s cadence)
if tick_count % 12 == 0:  # every 60s at 5s tick rate
    aggregator = TaoFlowAggregator()
    updated_count = await aggregator.compute_all(session)
```

### 4.3 WingFlap Amount Field

**Confirmed:** The `WingFlap` model has a `volume_usd` field (not `amount`). This field captures the trade size for TRADE and MIRROR_TRADE flaps. No migration needed for this field — it already exists on the model.

### 4.4 Frontend Integration

Behind `CYCLE_017_TAO_FLOW` flag:

- TAO flow badge on theatre/timeline cards showing net_inflow_24h
- Colour coding: green (positive), red (negative), grey (zero)
- Tooltip with 7d figure
- Uses existing `TaoFlowFields` type from `cycle017.ts`

---

## 5. Sprint 3 — Registry Schema Expansion

### 5.1 Source Registry Model

An existing typed JSON-backed OSINT source registry lives at `backend/osint/models/registry.py`. This already structures source metadata with typed entries. Sprint 3 extends this registry with policy fields.

**Default path:** Extend the typed entries in `backend/osint/models/registry.py` with `query_determinism`, `receipt_body_required`, and `requires_legal_review` fields. This keeps source metadata co-located and avoids a new migration.

**Fallback (only if Sprint 3 needs DB persistence):**

```python
class SourceRegistryEntry(Base):
    __tablename__ = "source_registry"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50))

    # Cycle 017 fields
    query_determinism: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="pure_id_lookup | search_endpoint | bulk_export"
    )
    receipt_body_required: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    requires_legal_review: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
```

### 5.2 Evidence Submission Enforcement

**Modified:** `backend/investigation/evidence_envelope.py`

When `receipt_body_required=True` on the source:

```python
def submit_evidence(self, evidence_item, source_entry=None):
    if source_entry and source_entry.receipt_body_required:
        if not evidence_item.receipt_body:
            raise ValueError(
                f"Source '{source_entry.source_name}' requires receipt_body "
                f"on evidence submission"
            )
```

### 5.3 Legal Review Flag

When `requires_legal_review=True` on any evidence source within an investigation, the investigation detail API response includes a `has_legal_review_requirement: true` flag. The frontend surfaces this as a warning badge.

---

## 6. Sprint 4 — Coherence Gates

### 6.1 CoherenceGateEvaluator Service

**New:** `backend/services/coherence_gate_evaluator.py`

```python
class GateStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"

class CoherenceGateEvaluator:
    """
    Evaluates whether a certificate requires coherence review
    and manages the gate lifecycle.
    """

    def should_require_review(self, certificate) -> bool:
        """
        Determine if this certificate needs coherence review.
        Rules:
        - REVIEW_REQUIRED routing hint → always requires review
        - INVESTIGATIVE inquiry class with score < 0.8 → requires review
        - CONTESTED verification tier → requires review
        """
        ...

    def open_gate(self, certificate, session) -> None:
        """Set gate to PENDING, log audit event."""
        certificate.coherence_review_required = True
        certificate.coherence_gate_status = GateStatus.PENDING.value
        # Log TheatreAuditEvent(COHERENCE_GATE_OPENED)

    def resolve_gate(
        self, certificate, status: GateStatus,
        reviewer_id: str, session
    ) -> None:
        """
        Resolve gate to PASSED or FAILED.
        Logs audit event with reviewer context.
        """
        certificate.coherence_gate_status = status.value
        certificate.coherence_reviewed_at = datetime.utcnow()
        certificate.coherence_reviewer_id = reviewer_id
        # Log TheatreAuditEvent(COHERENCE_GATE_RESOLVED)
```

### 6.2 Gate Lifecycle

```
Certificate issued
  → RoutingEvaluator.evaluate() → routing_hint
  → CoherenceGateEvaluator.should_require_review()
    → if True:
        open_gate() → status = PENDING
        → WS: COHERENCE_GATE_TRANSITION(PENDING)
    → Manual review via API:
        resolve_gate(PASSED) or resolve_gate(FAILED)
        → WS: COHERENCE_GATE_TRANSITION(PASSED|FAILED)
```

### 6.3 Deployment Guard

Any system that reads certificates for deployment (e.g., external consumers) should check:

```python
def is_deployable(certificate) -> bool:
    if certificate.routing_hint == "BLOCKED":
        return False
    if certificate.coherence_review_required and \
       certificate.coherence_gate_status != "PASSED":
        return False
    return True
```

This is exposed as a computed field on the API response:

```python
class TheatreCertificateResponse(BaseModel):
    # ... existing + new fields ...
    is_deployable: bool  # computed from routing_hint + gate_status
```

### 6.4 API Endpoints

**New:** `POST /api/v1/certificates/{id}/gate/resolve`

Auth: `Depends(get_current_user)` — reviewer identity captured from `user.user_id` on the `TokenData` dependency.

```json
{
  "status": "PASSED",  // or "FAILED"
  "reviewer_notes": "Optional review notes"
}
```

**New:** `GET /api/v1/certificates/{id}/gate`

Returns gate status, audit trail, and deployment eligibility.

---

## 7. Sprint 5 — WebSocket Policy Events + Frontend Integration

### 7.1 New WebSocket Event Types

**Modified:** `backend/websockets/realtime_manager.py`

```python
async def broadcast_routing_decision(self, certificate_id: str, decision: dict):
    """Broadcast routing decision for a certificate."""
    await self.broadcast_global("ROUTING_DECISION", {
        "certificate_id": certificate_id,
        **decision
    })
    await self.broadcast_to_channel(
        f"theatre:{decision['theatre_id']}",
        "ROUTING_DECISION",
        decision
    )

async def broadcast_coherence_gate_transition(
    self, certificate_id: str, transition: dict
):
    """Broadcast coherence gate status change."""
    await self.broadcast_global("COHERENCE_GATE_TRANSITION", {
        "certificate_id": certificate_id,
        **transition
    })

async def broadcast_tao_flow_alert(
    self, timeline_id: str, alert: dict
):
    """Broadcast when TAO flow crosses a threshold."""
    await self.broadcast_to_channel(
        f"timeline:{timeline_id}",
        "TAO_FLOW_ALERT",
        alert
    )
```

### 7.2 Frontend Feature Flag Removal

Sprint 5 removes the three 017-scoped flags. Two flags with broader scope are retained:

| Flag | Action |
|------|--------|
| `CYCLE_017_DEPLOYABILITY_ROUTING` | **Remove** — render routing fields natively |
| `CYCLE_017_REGISTRY_SCHEMA` | **Remove** — render registry badges natively |
| `CYCLE_017_COHERENCE_GATES` | **Remove** — render gate status natively |
| `CYCLE_017_TAO_FLOW` | **Retain if still gating staged Alpamayo behaviour** beyond pure flow metrics; remove only if its sole remaining consumer is TAO flow badges |
| `WEBSOCKET_REALTIME` | **Retain** — generic realtime gate used by the shared channel hook (`useRealtimeChannel`), not a disposable 017-only shim |

### 7.3 Frontend Component Changes

**Certificate Explorer (`CertificatesPage.tsx`):**
- Add routing hint badge column
- Add coherence gate status column
- Add "deployable" indicator
- Filter by routing_hint

**Theatre/Timeline Cards (`MarketplacePage.tsx`, `WorldMonitorPage.tsx`):**
- Add TAO flow badge (net_inflow_24h)
- Colour: green/red/grey

**Investigation Detail (`InvestigationPage.tsx`):**
- Registry schema badges on evidence sources
- Legal review warning badge
- Receipt requirement indicator

**Certificate Detail (new component or extension):**
- Full routing decision display with reason code
- Gate status timeline (PENDING → PASSED/FAILED)
- Deployment eligibility summary

### 7.4 Type Migration

**Delete:** `frontend/src/types/cycle017.ts`

**Extend:**
- `frontend/src/types/theatre.ts` — add routing, coherence, flow fields to existing types
- `frontend/src/types/index.ts` — add RoutingHint, GateStatus type unions
- `frontend/src/types/investigation.ts` — add registry schema fields

### 7.5 WS Cache Invalidation Extensions

**Modified:** `frontend/src/hooks/useWebSocket.ts`

Add handlers for new event types:

```typescript
case 'ROUTING_DECISION':
  queryClient.invalidateQueries({ queryKey: ['certificates'] });
  queryClient.invalidateQueries({ queryKey: ['theatre', data.theatre_id] });
  break;

case 'COHERENCE_GATE_TRANSITION':
  queryClient.invalidateQueries({ queryKey: ['certificates', data.certificate_id] });
  queryClient.invalidateQueries({ queryKey: ['gate', data.certificate_id] });
  break;

case 'TAO_FLOW_ALERT':
  queryClient.invalidateQueries({ queryKey: ['timelines'] });
  queryClient.invalidateQueries({ queryKey: ['timeline', data.timeline_id] });
  break;
```

---

## 8. Testing Strategy

### Unit Tests (per service)

| Service | Tests | Focus |
|---------|-------|-------|
| RoutingEvaluator | 4 | Score thresholds, inquiry class rules, tier rules, default |
| TaoFlowAggregator | 3 | 24h window, 7d window, zero trades |
| CoherenceGateEvaluator | 3 | Gate open, resolve PASSED, resolve FAILED |
| Registry enforcement | 2 | Receipt required, legal review flag |

### Integration Tests

| Test | Focus |
|------|-------|
| Certificate issuance → routing hint | End-to-end pipeline |
| Game loop → flow aggregation | Async cadence |
| Gate lifecycle → audit trail | State machine |
| WS routing event → cache invalidation | Real-time |
| E2E: theatre → certificate → routing → gate → verify `is_deployable` | Full lifecycle |

### Regression

All existing 1060+ tests must pass before and after each sprint.
