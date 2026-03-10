# SDD — Cycle-019: Agent Deployment + Investigation Persistence + Paradox Risk

**Cycle:** cycle-019
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd_019.md
**Design input:** Alexander Brief (7 March 2026), Echelon_Investigation_Toolset_Design_Note_v1 (v1.3.0), Codex product decisions

---

## 1. Architecture Overview

Cycle 019 adds three backend capabilities: agent-to-theatre deployment with persisted strategy profiles, database persistence for the investigation toolset, and inquiry-class-aware paradox risk computation on theatres.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CYCLE 019 ADDITIONS                            │
│                                                                     │
│  ┌────────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Agent Deployment    │  │ Investigation    │  │ Paradox Risk   │  │
│  │ Service             │  │ Repository       │  │ Evaluator      │  │
│  │                     │  │                  │  │                │  │
│  │ roster → theatre    │  │ in-memory → DB   │  │ inquiry-class  │  │
│  │ strategy profiles   │  │ all 8 tools      │  │ aware scoring  │  │
│  │ deployment guards   │  │ persisted        │  │ risk factors   │  │
│  └─────────┬───────────┘  └────────┬─────────┘  └───────┬────────┘  │
│            │                       │                     │           │
│  ┌─────────▼───────────────────────▼─────────────────────▼────────┐  │
│  │                    WebSocket Extensions                          │  │
│  │  AGENT_DEPLOYED | AGENT_WITHDRAWN | PARADOX_RISK_CHANGED        │  │
│  │  INVESTIGATION_STATUS_CHANGED                                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                       │                     │
  ┌──────▼──────┐     ┌─────────▼──────┐    ┌────────▼────────────┐
  │ agent_      │     │ investigations │    │ Theatre model       │
  │ deployments │     │ + 4 sub-tables │    │ + paradox_risk_*    │
  └─────────────┘     └────────────────┘    └─────────────────────┘
```

---

## 2. Sprint 0 — Schema Foundation + Migration

### 2.1 Agent Deployment Model

**New in:** `backend/database/models.py`

```python
class DeploymentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    WITHDRAWN = "WITHDRAWN"

class StrategyProfile(str, enum.Enum):
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"
    DEFENSIVE = "DEFENSIVE"

class AgentDeployment(Base):
    __tablename__ = "agent_deployments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    agent_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("agents.id"), index=True
    )
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", index=True,
        comment="ACTIVE | PAUSED | WITHDRAWN"
    )
    strategy_profile: Mapped[str] = mapped_column(
        String(20), default="BALANCED",
        comment="BALANCED | AGGRESSIVE | DEFENSIVE"
    )
    deployed_by: Mapped[str] = mapped_column(String(50), index=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Snapshot of theatre state at deployment time
    routing_hint_snapshot: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="ALLOWED | REVIEW_REQUIRED | BLOCKED at deploy time"
    )
    coherence_gate_status_snapshot: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="PENDING | PASSED | FAILED at deploy time"
    )

    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent: Mapped["Agent"] = relationship()
    theatre: Mapped["Theatre"] = relationship()
    audit_events: Mapped[List["DeploymentAuditEvent"]] = relationship(
        back_populates="deployment"
    )

    __table_args__ = (
        Index("ix_agent_deployments_active", "agent_id", "theatre_id", "status"),
    )
```

**DeploymentAuditEvent** — mirrors TheatreAuditEvent pattern:

```python
class DeploymentAuditEvent(Base):
    __tablename__ = "deployment_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    deployment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("agent_deployments.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), index=True,
        comment="DEPLOYED | STRATEGY_CHANGED | PAUSED | RESUMED | WITHDRAWN"
    )
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    deployment: Mapped["AgentDeployment"] = relationship(back_populates="audit_events")
```

### 2.2 Investigation Persistence Models

**New in:** `backend/database/models.py`

Convert the in-memory investigation toolset entities to persisted DB models. The existing in-memory classes (`EvidenceItem`, `ClaimNode`, etc.) remain as domain objects; the DB models mirror their fields.

```python
class InvestigationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(String(50), default="", index=True)
    construct_id: Mapped[str] = mapped_column(String(100), default="")
    # For investigations linked to spawned theatres (Cycle 018 scenario packs):
    # Use run-scoped pattern: scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}
    inquiry_class: Mapped[str] = mapped_column(
        String(30), default="INVESTIGATIVE",
        comment="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", index=True,
        comment="ACTIVE | COMPLETED"
    )
    domain_filters_json: Mapped[list] = mapped_column(JSON, default=list)
    stop_condition: Mapped[str] = mapped_column(
        String(30), default="OUTCOME_RESOLUTION",
        comment="OUTCOME_RESOLUTION | EVIDENCE_THRESHOLD | SPONSOR_DEFINED"
    )
    stop_config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    evidence_items: Mapped[List["InvestigationEvidenceItem"]] = relationship(
        back_populates="investigation", order_by="InvestigationEvidenceItem.submitted_at"
    )
    claim_nodes: Mapped[List["InvestigationClaimNode"]] = relationship(
        back_populates="investigation"
    )
    counter_signals: Mapped[List["InvestigationCounterSignal"]] = relationship(
        back_populates="investigation", order_by="InvestigationCounterSignal.detected_at"
    )
    drift_events: Mapped[List["InvestigationDriftEvent"]] = relationship(
        back_populates="investigation", order_by="InvestigationDriftEvent.detected_at"
    )
    certificate: Mapped[Optional["InvestigationCertificateRecord"]] = relationship(
        back_populates="investigation", uselist=False
    )
```

```python
class InvestigationEvidenceItem(Base):
    __tablename__ = "investigation_evidence_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_class: Mapped[str] = mapped_column(
        String(30),
        comment="public_primary | public_secondary | private_leak | analyst_derived | third_party_tool_output"
    )
    content_type: Mapped[str] = mapped_column(String(50), default="text/plain")
    source_description: Mapped[str] = mapped_column(Text, default="")
    source_id: Mapped[str] = mapped_column(String(100), default="")
    query_determinism: Mapped[str] = mapped_column(String(30), default="")
    references_json: Mapped[list] = mapped_column(JSON, default=list)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="evidence_items")
```

```python
class InvestigationClaimNode(Base):
    __tablename__ = "investigation_claim_nodes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(
        String(20), comment="fact | causal | attribution"
    )
    evidence_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    counter_signals_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(30), default="UNCONFIRMED",
        comment="SUPPORTED | PARTIALLY_SUPPORTED | UNCONFIRMED | CONTRADICTED"
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    independence_groups_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="claim_nodes")
```

```python
class InvestigationCounterSignal(Base):
    __tablename__ = "investigation_counter_signals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    signal_class: Mapped[str] = mapped_column(
        String(50),
        comment="11 classes: OFFICIAL_DENIAL through WITNESS_SOURCE_RECANTATION"
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_impact: Mapped[str] = mapped_column(Text, default="")
    detection_method: Mapped[str] = mapped_column(
        String(30), default="human_submitted",
        comment="automated_osint | paradox_engine | human_submitted"
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="counter_signals")
```

```python
class InvestigationDriftEvent(Base):
    __tablename__ = "investigation_drift_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    drift_type: Mapped[str] = mapped_column(
        String(30),
        comment="ENTITY_RESTRUCTURE | CONTRACT_AMENDMENT | MARKET_RULE_CHANGE | REGULATORY_STATUS_CHANGE | JURISDICTION_CHANGE"
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    original_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impact_assessment: Mapped[str] = mapped_column(
        String(20), default="non_material",
        comment="material | non_material"
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="drift_events")
```

```python
class InvestigationCertificateRecord(Base):
    __tablename__ = "investigation_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), unique=True, index=True
    )
    certificate_hash: Mapped[str] = mapped_column(String(64))
    certificate_json: Mapped[dict] = mapped_column(JSON)
    routing_decision: Mapped[str] = mapped_column(
        String(20), comment="ALLOWED | REVIEW_REQUIRED"
    )
    routing_reason: Mapped[str] = mapped_column(String(50), default="")
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="certificate")
```

### 2.3 Theatre Model Extension

**Modified:** `backend/database/models.py` — Theatre model

```python
# On Theatre model
paradox_risk_level: Mapped[Optional[str]] = mapped_column(
    String(10), nullable=True,
    comment="LOW | WATCH | HIGH"
)
paradox_risk_factors_json: Mapped[Optional[dict]] = mapped_column(
    JSON, nullable=True,
    comment="logic_gap, stability, counter_signals_material, evidence_freshness_hours, active_paradox"
)
paradox_risk_updated_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True
)
```

### 2.4 Migration

**New:** `backend/alembic/versions/c019_agent_deployment_investigation_persistence.py`

Dialect-safe migration:

1. Create `agent_deployments` table
2. Create `deployment_audit_events` table (FK → agent_deployments)
3. Create `investigations` table
4. Create `investigation_evidence_items` table (FK → investigations)
5. Create `investigation_claim_nodes` table (FK → investigations)
6. Create `investigation_counter_signals` table (FK → investigations)
7. Create `investigation_drift_events` table (FK → investigations)
8. Create `investigation_certificates` table (FK → investigations, unique constraint)
9. Add `paradox_risk_level`, `paradox_risk_factors_json`, `paradox_risk_updated_at` columns to `theatres` table
10. Create indexes on status, agent_id, theatre_id, investigation_id

Total: 8 new tables + 3 columns on theatres.

### 2.5 Pydantic Schema Extensions

**New file:** `backend/schemas/agent_deployment_schemas.py`

```python
class AgentDeploymentCreate(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=50)
    theatre_id: str = Field(..., min_length=1, max_length=50)
    strategy_profile: str = Field("BALANCED")
    config_json: Optional[dict] = None

class AgentDeploymentResponse(BaseModel):
    id: str
    agent_id: str
    theatre_id: str
    status: str
    strategy_profile: str
    deployed_by: str
    deployed_at: datetime
    paused_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    routing_hint_snapshot: Optional[str] = None
    coherence_gate_status_snapshot: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentDeploymentSummaryResponse(BaseModel):
    id: str
    theatre_id: str
    status: str
    strategy_profile: str
    deployed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeploymentListResponse(BaseModel):
    deployments: List[AgentDeploymentResponse]
    total: int

class StrategyUpdateRequest(BaseModel):
    strategy_profile: str = Field(..., pattern="^(BALANCED|AGGRESSIVE|DEFENSIVE)$")

class DeploymentAuditEventResponse(BaseModel):
    id: str
    event_type: str
    detail_json: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeploymentDetailResponse(AgentDeploymentResponse):
    audit_events: List[DeploymentAuditEventResponse] = []

class ParadoxRiskResponse(BaseModel):
    level: Optional[str] = None  # LOW | WATCH | HIGH
    factors: Optional[dict] = None
    explanation: Optional[str] = None
    updated_at: Optional[datetime] = None
```

---

## 3. Sprint 1 — Agent Deployment Service + API

### 3.1 AgentDeploymentService

**New:** `backend/services/agent_deployment_service.py`

```python
class AgentDeploymentService:
    """
    Manages agent-to-theatre assignments.

    Product contract: Deploy Agent = assign existing roster agent to theatre.
    Not "mint a new organism."
    """

    async def create_deployment(
        self,
        session: AsyncSession,
        agent_id: str,
        theatre_id: str,
        strategy_profile: str,
        deployed_by: str,
        config_json: Optional[dict] = None,
    ) -> AgentDeployment:
        """
        Create a new deployment.

        Guards (checked in order):
        1. Agent must exist and be alive (is_alive=True)
        2. Agent sanity must be >= 15 (not in breakdown)
        3. Theatre must exist
        4. No active deployment of this agent to this theatre
        5. Theatre deployability checks:
           - If theatre has latest certificate:
             * Reject if certificate routing_hint = BLOCKED
             * Reject if coherence_review_required = true AND coherence_gate_status != PASSED
           - If theatre has no certificate:
             * Reject deployment (uncertified theatres are not deployable in Cycle 019)

        Snapshots theatre routing_hint and coherence_gate_status at deploy time.
        Creates DEPLOYED audit event.
        Broadcasts AGENT_DEPLOYED WS event.
        """
        ...

    async def withdraw_deployment(
        self, session: AsyncSession, deployment_id: str, withdrawn_by: str
    ) -> AgentDeployment:
        """Withdraw an active deployment. Sets status=WITHDRAWN, withdrawn_at=now."""
        ...

    async def pause_deployment(
        self, session: AsyncSession, deployment_id: str
    ) -> AgentDeployment:
        """Pause an active deployment. Sets status=PAUSED, paused_at=now."""
        ...

    async def resume_deployment(
        self, session: AsyncSession, deployment_id: str
    ) -> AgentDeployment:
        """Resume a paused deployment. Sets status=ACTIVE, clears paused_at."""
        ...

    async def change_strategy(
        self, session: AsyncSession, deployment_id: str, new_strategy: str
    ) -> AgentDeployment:
        """Change strategy profile. Creates STRATEGY_CHANGED audit event."""
        ...

    async def list_deployments(
        self,
        session: AsyncSession,
        agent_id: Optional[str] = None,
        theatre_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[AgentDeployment], int]:
        """List deployments with optional filters."""
        ...

    async def get_active_count_for_agent(
        self, session: AsyncSession, agent_id: str
    ) -> int:
        """Count active deployments for an agent."""
        ...
```

### 3.2 Deployment API

**New file:** `backend/api/agent_deployment_routes.py`

```python
deployment_router = APIRouter(
    prefix="/api/v1/agent-deployments",
    tags=["agent-deployments"]
)

@deployment_router.post("/", response_model=AgentDeploymentResponse, status_code=201)
async def create_deployment(
    body: AgentDeploymentCreate,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Deploy an existing agent to a theatre with a strategy profile."""
    ...

@deployment_router.get("/", response_model=DeploymentListResponse)
async def list_deployments(
    agent_id: Optional[str] = Query(None),
    theatre_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List deployments filtered by agent, theatre, or status."""
    ...

@deployment_router.get("/{deployment_id}", response_model=DeploymentDetailResponse)
async def get_deployment(
    deployment_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get deployment detail with audit trail."""
    ...

@deployment_router.post("/{deployment_id}/withdraw", response_model=AgentDeploymentResponse)
async def withdraw_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Withdraw an active or paused deployment."""
    ...

@deployment_router.post("/{deployment_id}/pause", response_model=AgentDeploymentResponse)
async def pause_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Pause an active deployment."""
    ...

@deployment_router.post("/{deployment_id}/resume", response_model=AgentDeploymentResponse)
async def resume_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Resume a paused deployment."""
    ...

@deployment_router.post("/{deployment_id}/strategy", response_model=AgentDeploymentResponse)
async def change_strategy(
    deployment_id: str,
    body: StrategyUpdateRequest,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change strategy profile for an active deployment."""
    ...
```

### 3.3 Agent Response Extension

**Modified:** `backend/api/agents_routes.py`

Extend `AgentResponse` with:

```python
active_deployments_count: int = 0
active_deployments: List[AgentDeploymentSummaryResponse] = []
```

**Detail endpoint** (`GET /api/v1/agents/{id}`): Computed by joining `agent_deployments` where `status = 'ACTIVE'`. Returns both count and full deployment summaries.

**List endpoint** (`GET /api/v1/agents`): Returns `active_deployments_count` only (not full list) for performance. Fleet roster needs this count to display "deployed theatres" column without N+1 detail fetches.

---

## 4. Sprint 2 — Investigation Persistence

### 4.1 InvestigationRepository

**New:** `backend/database/repositories/investigation_repository.py`

```python
class InvestigationRepository:
    """
    Replaces the process-local dict in investigation_routes.py.
    Wraps the in-memory toolset classes with DB persistence.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, config: InvestigationCreateRequest) -> Investigation:
        """Create investigation DB record + instantiate InvestigationToolset."""
        ...

    async def get(self, investigation_id: str) -> Optional[Investigation]:
        """Get investigation with all sub-entities eagerly loaded."""
        ...

    async def list_all(self) -> List[Investigation]:
        """List all investigations with summary counts."""
        ...

    async def submit_evidence(
        self, investigation_id: str, evidence_data: dict
    ) -> InvestigationEvidenceItem:
        """
        Submit evidence: persist to DB AND delegate to EvidenceEnvelope.
        The in-memory envelope is rebuilt from DB records on access.
        """
        ...

    async def register_claim(
        self, investigation_id: str, claim_data: dict
    ) -> InvestigationClaimNode:
        """Persist claim and update ClaimGraph."""
        ...

    async def log_counter_signal(
        self, investigation_id: str, signal_data: dict
    ) -> InvestigationCounterSignal:
        """Persist counter-signal."""
        ...

    async def log_drift(
        self, investigation_id: str, drift_data: dict
    ) -> InvestigationDriftEvent:
        """Persist drift event."""
        ...

    async def build_certificate(
        self, investigation_id: str
    ) -> InvestigationCertificateRecord:
        """
        Rebuild InvestigationToolset from DB records,
        delegate to CertificateBuilder, persist result.
        """
        ...

    def _rebuild_toolset(self, investigation: Investigation) -> InvestigationToolset:
        """
        Reconstruct the in-memory InvestigationToolset from persisted DB records.
        This preserves the existing toolset logic while adding persistence.
        """
        ...
```

### 4.2 Route Modification

**Modified:** `backend/api/investigation_routes.py`

Replace all `_investigations` dict access with `InvestigationRepository(session)` calls. The API contract (request/response shapes) remains identical.

Before:
```python
_investigations: dict[str, InvestigationToolset] = {}
```

After:
```python
# No module-level state. All state flows through repository + DB session.
async def _get_repo(session: AsyncSession = Depends(get_session)):
    return InvestigationRepository(session)
```

Every endpoint signature gains `repo: InvestigationRepository = Depends(_get_repo)` and delegates to the repository instead of the dict.

---

## 5. Sprint 3 — Paradox Risk Service

### 5.1 ParadoxRiskEvaluator

**New:** `backend/services/paradox_risk_evaluator.py`

```python
class ParadoxRiskLevel(str, enum.Enum):
    LOW = "LOW"
    WATCH = "WATCH"
    HIGH = "HIGH"

@dataclass(frozen=True)
class ParadoxRiskAssessment:
    level: ParadoxRiskLevel
    factors: dict  # logic_gap, stability, counter_signals_material, evidence_freshness_hours, active_paradox
    explanation: str  # Human-readable, product vocabulary

class ParadoxRiskEvaluator:
    """
    Computes inquiry-class-aware paradox risk for theatres.

    CRITICAL: paradox_risk is a COMPUTED SURFACE with cached persistence, NOT operator-authored.

    Risk levels:
    - LOW: no active concerns
    - WATCH: early warning signals
    - HIGH: active paradox or severe divergence

    Inquiry-class weighting (from product spec):
    - COUNTERFACTUAL: market-vs-signal divergence, stability
    - INVESTIGATIVE: evidence weakness, corroboration gaps, freshness
    - INSPECTION: unmet criteria, criteria contradiction
    - SURVEY: thin participation, sampling distortion
    - SCRUTINY: adversarial contradiction, counter-signals

    Recalculation MUST be triggered explicitly:
    1. After paradox task updates timeline stability / active paradox state
    2. After material counter-signal ingestion (in investigation)
    3. After investigation evidence freshness crosses threshold bands
    4. On theatre detail/list read if cached risk is missing or stale (staleness TBD by Codex)
    """

    # Thresholds per inquiry class
    THRESHOLDS = {
        "COUNTERFACTUAL": {
            "watch_logic_gap": 0.25,
            "high_logic_gap": 0.40,
            "watch_stability": 0.45,
            "high_stability": 0.30,
            "evidence_weight": 0.3,
            "counter_signal_weight": 0.3,
            "stability_weight": 0.4,
        },
        "INVESTIGATIVE": {
            "watch_logic_gap": 0.20,
            "high_logic_gap": 0.35,
            "watch_stability": 0.50,
            "high_stability": 0.35,
            "evidence_weight": 0.5,
            "counter_signal_weight": 0.3,
            "stability_weight": 0.2,
        },
        "INSPECTION": {
            "watch_logic_gap": 0.30,
            "high_logic_gap": 0.45,
            "watch_stability": 0.40,
            "high_stability": 0.25,
            "evidence_weight": 0.4,
            "counter_signal_weight": 0.2,
            "stability_weight": 0.4,
        },
        "SURVEY": {
            "watch_logic_gap": 0.30,
            "high_logic_gap": 0.50,
            "watch_stability": 0.35,
            "high_stability": 0.20,
            "evidence_weight": 0.2,
            "counter_signal_weight": 0.2,
            "stability_weight": 0.6,
        },
        "SCRUTINY": {
            "watch_logic_gap": 0.15,
            "high_logic_gap": 0.30,
            "watch_stability": 0.50,
            "high_stability": 0.35,
            "evidence_weight": 0.3,
            "counter_signal_weight": 0.5,
            "stability_weight": 0.2,
        },
    }

    async def evaluate(
        self,
        session: AsyncSession,
        theatre: Theatre,
    ) -> ParadoxRiskAssessment:
        """
        Compute paradox risk for a theatre.

        Inputs:
        - Theatre's inquiry_class
        - Active timeline's logic_gap and stability
        - Active paradox existence
        - Investigation evidence freshness (if linked)
        - Counter-signal material count (if investigation linked)
        """
        ...

    def _compute_explanation(
        self, level: ParadoxRiskLevel, factors: dict, inquiry_class: str
    ) -> str:
        """
        Generate human-readable explanation using product vocabulary.

        Examples:
        - "Evidence weak — corroboration gaps detected in investigative inquiry"
        - "Counter-signals rising — 3 material contradictions in scrutiny inquiry"
        - "Logic gap widening — market diverging from OSINT signals"
        - "Paradox active — Class 2 severity, 3h to detonation window"
        """
        ...
```

### 5.2 Theatre Response Extension

**Modified:** Theatre response schemas

```python
class TheatreResponse(BaseModel):
    # ... existing fields ...
    paradox_risk: Optional[ParadoxRiskResponse] = None

class TheatreListItemResponse(BaseModel):
    # ... existing fields ...
    paradox_risk_level: Optional[str] = None
```

### 5.3 Risk Computation Integration

The `ParadoxRiskEvaluator` computes risk on-demand. Recalculation is triggered explicitly at these points:

1. **On theatre detail API call** (`GET /api/v1/theatres/{id}`): compute fresh risk level on each request
2. **On theatre list API call** (`GET /api/v1/theatres`): return cached risk_level from Theatre record; if missing or stale, trigger background recalculation
3. **After paradox task tick** (`backend/worker/tasks/paradox.py`): when timeline stability or active_paradox state changes, recompute risk and persist to Theatre record; broadcast WS event if level changed
4. **After material counter-signal ingestion** (in `InvestigationRepository.log_counter_signal`): if signal.material=true, trigger recalculation for linked theatre
5. **After evidence freshness crosses threshold band** (in `InvestigationRepository.submit_evidence`): compare new evidence_freshness_hours to previous; if crosses a configured threshold band, trigger recalculation for linked theatre

---

## 6. Sprint 4 — Certificate Persistence + Deployment Lifecycle

### 6.1 Certificate Persistence

When `build_certificate` is called on an investigation, the `InvestigationRepository`:

1. Rebuilds the `InvestigationToolset` from DB records
2. Calls `CertificateBuilder.build()` to produce the frozen certificate
3. Persists the certificate as `InvestigationCertificateRecord`:
   - `certificate_hash`: SHA-256 of canonical JSON
   - `certificate_json`: full certificate fields
   - `routing_decision`: from certificate routing cascade
   - `routing_reason`: from routing reason code
4. Sets `Investigation.status = COMPLETED`, `Investigation.completed_at = now()`
5. Broadcasts `INVESTIGATION_STATUS_CHANGED` WS event

### 6.2 Deployment Lifecycle

Full state machine for deployments:

```
ACTIVE ←→ PAUSED
  ↓
WITHDRAWN (terminal)
```

Valid transitions:
- ACTIVE → PAUSED: via `POST /{id}/pause`
- PAUSED → ACTIVE: via `POST /{id}/resume`
- ACTIVE → WITHDRAWN: via `POST /{id}/withdraw`
- PAUSED → WITHDRAWN: via `POST /{id}/withdraw`

Each transition creates a `DeploymentAuditEvent`.

---

## 7. Sprint 5 — WebSocket Events + Integration

### 7.1 New WebSocket Events

**Modified:** `backend/websockets/realtime_manager.py`

```python
async def broadcast_agent_deployed(
    self, agent_id: str, theatre_id: str, strategy_profile: str, deployed_by: str
):
    """Broadcast when an agent is deployed to a theatre."""
    await self.broadcast_global("AGENT_DEPLOYED", {
        "agent_id": agent_id,
        "theatre_id": theatre_id,
        "strategy_profile": strategy_profile,
        "deployed_by": deployed_by,
    })

async def broadcast_agent_withdrawn(
    self, agent_id: str, theatre_id: str, withdrawn_by: str
):
    """Broadcast when an agent is withdrawn from a theatre."""
    await self.broadcast_global("AGENT_WITHDRAWN", {
        "agent_id": agent_id,
        "theatre_id": theatre_id,
        "withdrawn_by": withdrawn_by,
    })

async def broadcast_paradox_risk_changed(
    self, theatre_id: str, old_level: str, new_level: str, factors: dict
):
    """Broadcast when a theatre's paradox risk level changes."""
    await self.broadcast_global("PARADOX_RISK_CHANGED", {
        "theatre_id": theatre_id,
        "old_level": old_level,
        "new_level": new_level,
        "factors": factors,
    })

async def broadcast_investigation_status_changed(
    self, investigation_id: str, old_status: str, new_status: str
):
    """Broadcast when an investigation's status changes."""
    await self.broadcast_global("INVESTIGATION_STATUS_CHANGED", {
        "investigation_id": investigation_id,
        "old_status": old_status,
        "new_status": new_status,
    })
```

---

## 8. Testing Strategy

### Unit Tests (per service)

| Service | Tests | Focus |
|---------|-------|-------|
| AgentDeploymentService | 4 | Create, guards (dead agent, duplicate), withdraw, strategy change |
| InvestigationRepository | 4 | Create, evidence persist, claim persist, restart survival |
| ParadoxRiskEvaluator | 3 | LOW/WATCH/HIGH thresholds, inquiry-class weighting, explanation generation |

### Integration Tests

| Test | Focus |
|------|-------|
| Deploy agent → list by theatre → withdraw | Deployment lifecycle |
| Create investigation → submit evidence → build certificate → verify persisted | Investigation persistence |
| Theatre with high logic gap → paradox risk HIGH | Risk computation |
| Deploy agent → paradox fires → risk changes → WS event | Cross-system integration |
| E2E: deploy → investigate → risk updates → withdraw | Full lifecycle |

### Regression

All existing post-018 tests (≥1139) must pass before and after each sprint.
