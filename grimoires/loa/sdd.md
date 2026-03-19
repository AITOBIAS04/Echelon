# SDD — Cycle-038: Cross-Theatre Paradox Detection

**Cycle:** cycle-038
**Date:** 19 March 2026
**Depends on:** Cycle-037d (theatre construct verification), Cycle-020 (ParadoxRiskOrchestrator), Cycle-010b (Paradox Engine)
**PRD:** `grimoires/loa/prd.md`
**Builder:** Loa (backend only)

---

## 1. Executive Summary

Cycle 038 extends the Paradox Engine from theatre-local logic gap scanning to network-level coherence detection. It introduces FactAnchors (real-world event linking), CoherenceGroups (theatre grouping), and CrossTheatreParadox records (network-level divergence). A new CrossTheatreParadoxScanner detects four paradox patterns: settlement divergence, oracle inconsistency, scope overlap gaps, and temporal drift. An OracleConsistencyMonitor tracks oracle responses across theatres. Integration with existing infrastructure is additive: ParadoxRiskOrchestrator gains a `cross_theatre_exposure` factor, WingFlap gains a new type, and WebSocket emission is material-delta gated.

**New tables:** 6 (fact_anchors, fact_anchor_links, coherence_groups, coherence_group_members, cross_theatre_paradoxes, oracle_responses)
**New services:** 4
**Modified services:** 2 (ParadoxRiskOrchestrator, ConnectionManager)
**New API routes:** ~10
**Migration:** c038_cross_theatre_paradox

---

## 2. System Architecture

### 2.1 Component Diagram

```
                    ┌─────────────────────────┐
                    │    Theatre Routes API    │
                    │ /api/v1/theatres/        │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  Existing Theatre Stack  │
                    │  (unchanged)             │
                    └──────────┬──────────────┘
                               │ settlement events
                    ┌──────────▼──────────────┐
                    │   FactAnchorService      │──→ fact_anchors
                    │   (link events to world) │──→ fact_anchor_links
                    └──────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
   ┌──────────▼─────┐  ┌──────▼───────┐  ┌─────▼──────────────┐
   │ OracleConsist-  │  │ Coherence    │  │ CrossTheatre       │
   │ encyMonitor     │  │ GroupService │  │ ParadoxScanner     │
   │ (track oracles) │  │ (manage      │  │ (detect patterns)  │
   └──────────┬──────┘  │  groups)     │  └──────┬─────────────┘
              │         └──────────────┘         │
              │                                  │
              └──────────────┬───────────────────┘
                             │ cross_theatre_exposure
                  ┌──────────▼──────────────┐
                  │ ParadoxRiskOrchestrator  │
                  │ (per-theatre risk +      │
                  │  network exposure)       │
                  └──────────┬──────────────┘
                             │ material delta
                  ┌──────────▼──────────────┐
                  │   WebSocket Manager     │
                  │   CROSS_THEATRE_PARADOX_ │
                  │   DETECTED event        │
                  └─────────────────────────┘
```

### 2.2 Data Flow

1. Theatre settles an outcome → caller creates/links a FactAnchor via FactAnchorService
2. FactAnchorService detects multiple theatre links on same anchor → triggers CrossTheatreParadoxScanner
3. Scanner evaluates 4 detection patterns → creates CrossTheatreParadox records
4. Scanner feeds `cross_theatre_exposure` count into ParadoxRiskOrchestrator for affected theatres
5. Orchestrator recomputes per-theatre risk with new factor → emits WebSocket if material

---

## 3. Data Architecture

### 3.1 New Models

All models in `backend/database/models.py`. Migration: `c038_cross_theatre_paradox`.

#### FactAnchor

```python
class FactAnchor(Base):
    __tablename__ = "fact_anchors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    anchor_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_source: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    location_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    links: Mapped[list["FactAnchorLink"]] = relationship(back_populates="fact_anchor")

    # Indexes
    __table_args__ = (
        Index("ix_fact_anchors_external", "external_source", "external_id", unique=True),
        Index("ix_fact_anchors_type_time", "anchor_type", "occurred_at"),
    )
```

**Design decisions:**
- `(external_source, external_id)` is unique — same USGS event cannot be duplicated
- `anchor_type` indexed for domain-scoped queries (e.g., all seismic events)
- `location_json` is domain-specific (lat/lon/depth for seismic, HPC region for solar)
- `metadata_json` stores source-specific values (magnitude, flare class, Kp index)

#### FactAnchorLink

```python
class FactAnchorLink(Base):
    __tablename__ = "fact_anchor_links"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    fact_anchor_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("fact_anchors.id"), nullable=False, index=True
    )
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=False, index=True
    )
    link_type: Mapped[str] = mapped_column(String(30), nullable=False)
    link_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    linked_entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    linked_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    fact_anchor: Mapped["FactAnchor"] = relationship(back_populates="links")

    # Indexes
    __table_args__ = (
        Index("ix_fact_anchor_links_anchor_theatre", "fact_anchor_id", "theatre_id"),
    )
```

**Design decisions:**
- `link_type` is one of: `settlement`, `evidence`, `oracle_query`
- `link_confidence` enables soft matching (0.8 for USGS automatic → reviewed reconciliation)
- Polymorphic reference via `linked_entity_id` + `linked_entity_type` avoids per-entity FK proliferation
- Composite index on `(fact_anchor_id, theatre_id)` for cross-theatre lookups

#### CoherenceGroup

```python
class CoherenceGroup(Base):
    __tablename__ = "coherence_groups"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    group_type: Mapped[str] = mapped_column(String(30), nullable=False)
    policy_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    members: Mapped[list["CoherenceGroupMember"]] = relationship(back_populates="group")
```

**`policy_json` schema:**
```json
{
    "settlement_divergence_threshold": 0.0,
    "oracle_tolerance": 0.1,
    "temporal_drift_hours": 24,
    "scope_overlap_domains": ["seismic_event", "volcanic_activity"]
}
```

#### CoherenceGroupMember

```python
class CoherenceGroupMember(Base):
    __tablename__ = "coherence_group_members"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    coherence_group_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("coherence_groups.id"), nullable=False
    )
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="primary")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    group: Mapped["CoherenceGroup"] = relationship(back_populates="members")

    __table_args__ = (
        Index("ix_coherence_members_group", "coherence_group_id"),
        Index("ix_coherence_members_theatre", "theatre_id"),
    )
```

#### CrossTheatreParadox

```python
class CrossTheatreParadoxStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class CrossTheatreParadoxType(str, enum.Enum):
    SETTLEMENT_DIVERGENCE = "SETTLEMENT_DIVERGENCE"
    ORACLE_INCONSISTENCY = "ORACLE_INCONSISTENCY"
    SCOPE_OVERLAP_GAP = "SCOPE_OVERLAP_GAP"
    TEMPORAL_DRIFT = "TEMPORAL_DRIFT"

class CrossTheatreParadoxSeverity(str, enum.Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    MATERIAL = "MATERIAL"
    CRITICAL = "CRITICAL"

class CrossTheatreParadox(Base):
    __tablename__ = "cross_theatre_paradoxes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    fact_anchor_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("fact_anchors.id"), nullable=False, index=True
    )
    coherence_group_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("coherence_groups.id"), nullable=True
    )
    paradox_type: Mapped[CrossTheatreParadoxType] = mapped_column(
        SQLEnum(CrossTheatreParadoxType), nullable=False
    )
    severity: Mapped[CrossTheatreParadoxSeverity] = mapped_column(
        SQLEnum(CrossTheatreParadoxSeverity), nullable=False
    )
    theatre_a_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=False
    )
    theatre_b_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    resolution_status: Mapped[CrossTheatreParadoxStatus] = mapped_column(
        SQLEnum(CrossTheatreParadoxStatus), default=CrossTheatreParadoxStatus.OPEN
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_cross_paradox_anchor", "fact_anchor_id"),
        Index("ix_cross_paradox_theatres", "theatre_a_id", "theatre_b_id"),
        Index("ix_cross_paradox_status", "resolution_status"),
        Index("ix_cross_paradox_severity", "severity"),
    )
```

**`evidence_json` schema:**
```json
{
    "theatre_a_value": "M6.2",
    "theatre_b_value": "M5.8",
    "theatre_a_source": "usgs_neic",
    "theatre_b_source": "emsc",
    "delta": 0.4,
    "threshold": 0.1,
    "oracle_query_time_a": "2026-03-19T10:00:00Z",
    "oracle_query_time_b": "2026-03-19T10:05:00Z"
}
```

#### OracleResponse

```python
class OracleResponse(Base):
    __tablename__ = "oracle_responses"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    queried_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_oracle_responses_source_event", "source", "event_id"),
        Index("ix_oracle_responses_theatre", "theatre_id"),
    )
```

**Design decisions:**
- `is_provisional` flags USGS automatic (pre-reviewed) responses, enabling the context_038 rule: provisional → reviewed revision is INFO, not MATERIAL
- `value_json` stores the full oracle response for provenance
- Composite index on `(source, event_id)` for cross-theatre consistency queries

### 3.2 Model Modifications

#### WingFlapType Enum Extension

Add to existing enum in `backend/database/models.py`:

```python
class WingFlapType(str, enum.Enum):
    # ... existing 17 types unchanged ...
    CROSS_THEATRE_PARADOX = "CROSS_THEATRE_PARADOX"  # NEW
```

The Alembic migration adds the value to the PostgreSQL enum type via `ALTER TYPE wingflaptype ADD VALUE 'CROSS_THEATRE_PARADOX'`.

### 3.3 Alembic Migration

**File:** `backend/alembic/versions/c038_cross_theatre_paradox.py`
**Down revision:** `c037_evaluation_contracts`

Creates:
1. `fact_anchors` table with unique constraint on `(external_source, external_id)`
2. `fact_anchor_links` table with FK to fact_anchors and theatres
3. `coherence_groups` table with unique constraint on `name`
4. `coherence_group_members` table with FK to coherence_groups and theatres
5. `cross_theatre_paradoxes` table with FK to fact_anchors, coherence_groups, theatres
6. `oracle_responses` table with FK to theatres
7. ALTER TYPE `wingflaptype` ADD VALUE `CROSS_THEATRE_PARADOX`

---

## 4. Component Design

### 4.1 FactAnchorService

**File:** `backend/services/fact_anchor_service.py`

```python
class FactAnchorService:
    """CRUD and linking for FactAnchors — real-world event registry."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_or_create(
        self,
        anchor_type: str,
        external_id: str,
        external_source: str,
        occurred_at: datetime,
        location_json: Optional[dict] = None,
        metadata_json: Optional[dict] = None,
    ) -> FactAnchor:
        """Upsert a FactAnchor by (external_source, external_id).

        Idempotent: returns existing anchor if already registered.
        """

    async def link_theatre(
        self,
        anchor_id: str,
        theatre_id: str,
        link_type: str,
        linked_entity_id: str,
        linked_entity_type: str,
        link_confidence: float = 1.0,
    ) -> FactAnchorLink:
        """Link a theatre's settlement/evidence to a FactAnchor.

        After linking, checks if multiple theatres now share this anchor
        and triggers cross-theatre scanning if threshold reached (>= 2 theatres).
        """

    async def get_theatres_for_anchor(
        self, anchor_id: str,
    ) -> list[FactAnchorLink]:
        """Get all theatre links for a FactAnchor."""

    async def get_anchors_for_theatre(
        self, theatre_id: str,
        anchor_type: Optional[str] = None,
    ) -> list[FactAnchorLink]:
        """Get all FactAnchors linked to a theatre."""
```

**Key behavior:**
- `get_or_create` is idempotent on `(external_source, external_id)` — concurrent theatre settlements for the same USGS event converge to one anchor
- `link_theatre` triggers cross-theatre scanning when a second theatre links to the same anchor
- The trigger is synchronous within the transaction — paradox detection is atomic with the linking operation

### 4.2 CoherenceGroupService

**File:** `backend/services/coherence_group_service.py`

```python
class CoherenceGroupService:
    """Management of CoherenceGroups and membership."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_group(
        self, name: str, group_type: str, policy_json: dict,
    ) -> CoherenceGroup:
        """Create a coherence group with policy thresholds."""

    async def add_member(
        self, group_id: str, theatre_id: str, role: str = "primary",
    ) -> CoherenceGroupMember:
        """Add a theatre to a coherence group."""

    async def get_groups_for_theatre(
        self, theatre_id: str,
    ) -> list[CoherenceGroup]:
        """Get all coherence groups containing a theatre."""

    async def get_group_members(
        self, group_id: str,
    ) -> list[CoherenceGroupMember]:
        """Get all members of a coherence group."""
```

### 4.3 CrossTheatreParadoxScanner

**File:** `backend/services/cross_theatre_paradox_scanner.py`

```python
class CrossTheatreParadoxScanner:
    """Detects coherence failures across theatres sharing FactAnchors.

    Four detection patterns:
    1. Settlement divergence — opposite outcomes for same event
    2. Oracle inconsistency — same source, different values
    3. Scope overlap gap — expected correlated event absent
    4. Temporal drift — settlement timing exceeds window
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def scan_fact_anchor(
        self, anchor_id: str,
    ) -> list[CrossTheatreParadox]:
        """Scan a FactAnchor for cross-theatre paradoxes.

        Triggered when a new theatre link is added to an existing anchor.
        Evaluates all pairwise comparisons between linked theatres.
        Returns new paradox records (already persisted).
        """

    async def scan_coherence_group(
        self, group_id: str,
    ) -> list[CrossTheatreParadox]:
        """Scan a CoherenceGroup for scope overlap gaps.

        Evaluates whether group members have corresponding anchors
        for events that the group policy expects to be correlated.
        """

    async def evaluate_settlement_divergence(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Compare two theatres' settlements for the same anchor.

        Severity logic:
        - Both theatres ACTIVE/SETTLED with opposite outcomes → MATERIAL
        - One theatre superseded/resolved → WATCH
        - Same outcome → None (no paradox)
        """

    async def evaluate_oracle_inconsistency(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Compare oracle responses for same event across theatres.

        Uses OracleResponse records. Severity logic:
        - Same source, delta > threshold → MATERIAL
        - Same source, within tolerance → None
        - Different sources, delta > threshold → WATCH
        - Provisional → reviewed revision → INFO (context_038 rule)
        """

    async def evaluate_temporal_drift(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Check if settlement timing diverges significantly.

        Uses the coherence group's temporal_drift_hours threshold.
        Severity: INFO if delta > window, WATCH if delta > 2x window.
        """

    async def evaluate_scope_overlap(
        self,
        group: CoherenceGroup,
        anchor: FactAnchor,
    ) -> Optional[CrossTheatreParadox]:
        """Check if coherence group members all have links for an anchor.

        Expected: if group policy includes anchor_type in
        scope_overlap_domains, all primary members should have a link.
        Missing link → WATCH (absence is suspicious, not contradictory).
        """

    def _classify_provisional_revision(
        self,
        response_a: OracleResponse,
        response_b: OracleResponse,
    ) -> CrossTheatreParadoxSeverity:
        """Context_038 rule: provisional oracle revision is INFO, not MATERIAL.

        If one response is_provisional and the other is not, and both
        reference the same (source, event_id), this is a normal oracle
        lifecycle event, not a material paradox.
        """
```

**Deduplication:** Before persisting, check for existing OPEN record with same `(fact_anchor_id, theatre_a_id, theatre_b_id, paradox_type)`. If found, update severity if changed, otherwise skip.

**Ordering convention:** `theatre_a_id < theatre_b_id` (lexicographic) to prevent (A,B) and (B,A) duplicates.

### 4.4 OracleConsistencyMonitor

**File:** `backend/services/oracle_consistency_monitor.py`

```python
@dataclass(frozen=True)
class ConsistencyResult:
    is_consistent: bool
    source: str
    event_id: str
    responses: list[dict]  # [{theatre_id, value, queried_at, is_provisional}]
    max_delta: Optional[float]
    explanation: str

@dataclass(frozen=True)
class DivergenceRecord:
    source: str
    event_id: str
    theatre_ids: list[str]
    delta: float
    detected_at: datetime


class OracleConsistencyMonitor:
    """Tracks oracle responses across theatres for consistency.

    Records are created when theatres report oracle query results
    (typically at settlement time). Does not poll oracles directly.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def record_response(
        self,
        theatre_id: str,
        source: str,
        event_id: str,
        value_json: dict,
        queried_at: datetime,
        is_provisional: bool = False,
    ) -> OracleResponse:
        """Record an oracle response. Idempotent on (theatre_id, source, event_id)."""

    async def check_consistency(
        self, source: str, event_id: str,
    ) -> ConsistencyResult:
        """Check if all theatres that queried (source, event_id) agree."""

    async def get_divergence_history(
        self, source: str, window_hours: int = 168,
    ) -> list[DivergenceRecord]:
        """Get recent divergence events for a source (default: 7 days)."""
```

### 4.5 ParadoxRiskOrchestrator Extension

**File:** `backend/services/paradox_risk_orchestrator.py` (MODIFIED)

Add `cross_theatre_exposure` as a new optional parameter to `trigger_recompute`:

```python
async def trigger_recompute(
    db,
    theatre_id: str,
    trigger_reason: str,
    *,
    # ... existing parameters unchanged ...
    cross_theatre_exposure: Optional[int] = None,  # NEW
    emit_ws: bool = False,
) -> Optional[ParadoxRiskAssessment]:
```

**Factor computation:** When `cross_theatre_exposure` is not provided, query CrossTheatreParadox for OPEN records where `(theatre_a_id == theatre_id OR theatre_b_id == theatre_id) AND severity IN ('MATERIAL', 'CRITICAL')`.

**Risk level floor:**
- `cross_theatre_exposure >= 1` → minimum level WATCH
- `cross_theatre_exposure >= 3` → minimum level HIGH
- Applied after existing per-theatre assessment

**Factors dict extension:**
```python
factors = {
    # ... existing 5 factors unchanged ...
    "cross_theatre_exposure": int,  # NEW
}
```

**Materiality:** `cross_theatre_exposure` change triggers material delta.

### 4.6 WebSocket Extension

**File:** `backend/websockets/realtime_manager.py` (MODIFIED)

```python
async def broadcast_cross_theatre_paradox(
    self,
    paradox_id: str,
    paradox_type: str,
    severity: str,
    theatre_a_id: str,
    theatre_b_id: str,
    fact_anchor_id: str,
    description: str,
) -> None:
    """Broadcast CROSS_THEATRE_PARADOX_DETECTED to both theatre channels."""
    data = {
        "paradox_id": paradox_id,
        "paradox_type": paradox_type,
        "severity": severity,
        "theatre_a_id": theatre_a_id,
        "theatre_b_id": theatre_b_id,
        "fact_anchor_id": fact_anchor_id,
        "description": description,
    }
    await self.broadcast_to_channel(
        f"theatre:{theatre_a_id}", "CROSS_THEATRE_PARADOX_DETECTED", data
    )
    await self.broadcast_to_channel(
        f"theatre:{theatre_b_id}", "CROSS_THEATRE_PARADOX_DETECTED", data
    )
```

**Emission gating:** Only for severity MATERIAL or CRITICAL.

### 4.7 WingFlap Integration

When CrossTheatreParadox is created with severity MATERIAL or CRITICAL, create a WingFlap for each affected theatre:

```python
async def _record_wingflap(
    db: AsyncSession,
    theatre_id: str,
    paradox: CrossTheatreParadox,
) -> None:
    flap = WingFlap(
        id=str(uuid4()),
        timeline_id=theatre_id,  # WingFlap timeline_id = theatre scope
        agent_id="system",
        flap_type=WingFlapType.CROSS_THEATRE_PARADOX,
        action=f"Cross-theatre {paradox.paradox_type.value}: {paradox.description[:200]}",
        stability_delta=-0.15,
        direction="DESTABILISE",
        volume_usd=0.0,
        timeline_stability=0.0,
        timeline_price=0.0,
    )
    db.add(flap)
```

---

## 5. API Design

### 5.1 FactAnchor Routes

**File:** `backend/api/fact_anchor_routes.py`
**Router:** `APIRouter(prefix="/api/v1/fact-anchors", tags=["fact-anchors"])`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/` | Required | Create or get FactAnchor (idempotent) |
| `GET` | `/` | Public | List anchors (filter by type, source, time range) |
| `GET` | `/{anchor_id}` | Public | Get anchor detail with links |
| `POST` | `/{anchor_id}/link` | Required | Link a theatre to an anchor |
| `GET` | `/{anchor_id}/paradoxes` | Public | Get cross-theatre paradoxes for anchor |

**Schemas** in `backend/schemas/fact_anchor_schemas.py`:

```python
class CreateFactAnchorRequest(BaseModel):
    anchor_type: str
    external_id: str
    external_source: str
    occurred_at: datetime
    location_json: Optional[dict] = None
    metadata_json: Optional[dict] = None

class LinkTheatreRequest(BaseModel):
    theatre_id: str
    link_type: str  # "settlement" | "evidence" | "oracle_query"
    linked_entity_id: str
    linked_entity_type: str
    link_confidence: float = 1.0

class FactAnchorResponse(BaseModel):
    id: str
    anchor_type: str
    external_id: str
    external_source: str
    occurred_at: datetime
    location_json: Optional[dict]
    metadata_json: Optional[dict]
    link_count: int
    created_at: datetime

class FactAnchorDetailResponse(FactAnchorResponse):
    links: list[FactAnchorLinkResponse]

class FactAnchorLinkResponse(BaseModel):
    id: str
    theatre_id: str
    link_type: str
    link_confidence: float
    linked_entity_id: str
    linked_entity_type: str
    created_at: datetime
```

### 5.2 CoherenceGroup Routes

**File:** `backend/api/coherence_group_routes.py`
**Router:** `APIRouter(prefix="/api/v1/coherence-groups", tags=["coherence-groups"])`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/` | Required | Create coherence group |
| `GET` | `/` | Public | List groups |
| `GET` | `/{group_id}` | Public | Get group with members |
| `POST` | `/{group_id}/members` | Required | Add theatre to group |
| `POST` | `/{group_id}/scan` | Required | Trigger scope overlap scan |

### 5.3 CrossTheatreParadox Routes

**File:** `backend/api/cross_theatre_paradox_routes.py`
**Router:** `APIRouter(prefix="/api/v1/cross-theatre-paradoxes", tags=["cross-theatre-paradoxes"])`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | Public | List paradoxes (filter by severity, status, theatre) |
| `GET` | `/{paradox_id}` | Public | Get paradox detail |
| `POST` | `/{paradox_id}/acknowledge` | Required | OPEN → ACKNOWLEDGED |
| `POST` | `/{paradox_id}/resolve` | Required | → RESOLVED (requires note) |
| `POST` | `/{paradox_id}/dismiss` | Required | → DISMISSED (requires note) |

### 5.4 OracleConsistency Routes

**File:** `backend/api/oracle_consistency_routes.py`
**Router:** `APIRouter(prefix="/api/v1/oracle-consistency", tags=["oracle-consistency"])`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/responses` | Required | Record oracle response from theatre |
| `GET` | `/check/{source}/{event_id}` | Public | Check consistency for event |
| `GET` | `/divergences/{source}` | Public | Get divergence history |

---

## 6. Integration Points

### 6.1 Trigger Flow

Primary trigger is `FactAnchorService.link_theatre()`:

```
Theatre settles → POST /api/v1/fact-anchors/{id}/link
  → FactAnchorService.link_theatre()
    → Count theatre links for this anchor
    → If >= 2 theatres linked:
      → CrossTheatreParadoxScanner.scan_fact_anchor(anchor_id)
        → For each pair: evaluate_settlement_divergence()
        → For each pair: evaluate_oracle_inconsistency()
        → For each pair: evaluate_temporal_drift()
        → For each new MATERIAL+ paradox:
          → _record_wingflap() for both theatres
          → ws_manager.broadcast_cross_theatre_paradox()
          → trigger_recompute() for both theatres
```

### 6.2 Scope Overlap Trigger

Separate path — triggered explicitly:

```
POST /api/v1/coherence-groups/{id}/scan
  → CrossTheatreParadoxScanner.scan_coherence_group(group_id)
    → For each anchor_type in policy.scope_overlap_domains:
      → Get anchors linked by any group member
      → For each anchor missing a link from a primary member:
        → evaluate_scope_overlap()
```

### 6.3 Router Registration

Add to app factory alongside existing routers:

```python
from backend.api.fact_anchor_routes import router as fact_anchor_router
from backend.api.coherence_group_routes import router as coherence_group_router
from backend.api.cross_theatre_paradox_routes import router as cross_paradox_router
from backend.api.oracle_consistency_routes import router as oracle_consistency_router
```

---

## 7. Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pairwise comparison O(n^2) per anchor | Slow for many-theatre anchors | 2-5 theatres per anchor in practice. No premature optimization. |
| WingFlap `timeline_id` naming | Conceptual confusion | Code comment documenting timeline_id = theatre scope |
| Enum migration for WingFlapType | PostgreSQL DDL | Standard `ALTER TYPE ADD VALUE` in Alembic |
| Concurrent anchor upsert race | Duplicate FactAnchor | Unique constraint + ON CONFLICT DO NOTHING |
| Paradox deduplication | Duplicates from repeated scans | Dedup key with theatre_a < theatre_b ordering |

---

## 8. Sprint Mapping

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| Sprint 0 | Schema + Migration | 6 new tables, 3 new enums, WingFlapType extension, Alembic migration c038, model tests |
| Sprint 1 | Core Services | FactAnchorService (get_or_create, link_theatre, queries), CoherenceGroupService (CRUD, membership), OracleConsistencyMonitor (record, check, history) |
| Sprint 2 | Scanner + Integration | CrossTheatreParadoxScanner (4 detection patterns, dedup, provisional rule), ParadoxRiskOrchestrator cross_theatre_exposure, WingFlap CROSS_THEATRE_PARADOX, WebSocket broadcast |
| Sprint 3 | API Routes + TREMOR Fixture + Regression | 4 route files (~15 endpoints), TREMOR end-to-end fixture, full regression suite, router registration |

---

## 9. What This Cycle Does NOT Design

- **No real-time oracle polling** — oracles observed passively via settlement reports
- **No settlement cascade** — paradox does not auto-invalidate certificates
- **No automated resolution** — detection and recording only; resolution is manual
- **No frontend surfaces** — API-only; visualization is future
- **No changes to per-theatre Paradox Engine** — `backend/engines/paradox.py` untouched
