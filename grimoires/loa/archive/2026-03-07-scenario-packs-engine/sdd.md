# SDD — Cycle-018: Scenario Packs Engine

**Cycle:** cycle-018
**Date:** 6 March 2026
**PRD:** grimoires/loa/prd_018.md
**Design input:** `Echelon_Scenario_Packs_Library_v1.md`, `echelon_scenario_packs_v1.html`, theatre template JSON fixtures, `fork_manager.py`

---

## 1. Architecture Overview

Cycle 018 adds the **Scenario Packs Engine**: a parallel product track to theatres, handling episodic RL environments with branching checkpoints, derived theatre spawning, and RLMF telemetry output.

```
┌──────────────────────────────────────────────────────────────────┐
│                   SCENARIO PACKS ENGINE (018)                     │
│                                                                   │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Template       │  │ Pack Lifecycle    │  │ Checkpoint       │  │
│  │ Catalog        │  │ Manager          │  │ Evaluator        │  │
│  │                │  │                  │  │                  │  │
│  │ 18 seeded +    │  │ DRAFT→COMMITTED  │  │ sequential eval  │  │
│  │ user-created   │  │ →ACTIVE→SETTLING │  │ branch selection │  │
│  │                │  │ →RESOLVED        │  │ result recording │  │
│  └───────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│          │                    │                      │            │
│  ┌───────▼────────────────────▼──────────────────────▼─────────┐  │
│  │                  Theatre Spawner                              │  │
│  │  checkpoint.can_spawn_theatre → Theatre(provenance link)     │  │
│  └───────┬──────────────────────────────────────────────────────┘  │
│          │                                                        │
│  ┌───────▼──────────────────────────────────────────────────────┐  │
│  │              RLMF Telemetry Pipeline                          │  │
│  │  run decisions, state vectors, rewards → export-ready         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │                    │                      │
  ┌──────▼──────┐    ┌──────▼──────┐    ┌───────────▼───────────┐
  │ Scenario    │    │ Run/Result  │    │ Spawned Theatres      │
  │ Pack Tables │    │ Tables      │    │ (existing pipeline)   │
  └─────────────┘    └─────────────┘    └───────────────────────┘
```

### 1.1 Data Flow

**Template → Pack → Run → Checkpoints → Results:**

```
User selects ScenarioPackTemplate from catalog
  → POST /api/v1/scenario-packs (creates ScenarioPack in DRAFT)
    → POST /api/v1/scenario-packs/{id}/commit (DRAFT → COMMITTED)
      → POST /api/v1/scenario-packs/{id}/run (COMMITTED → ACTIVE, creates ScenarioRun)
        → CheckpointEvaluator processes checkpoints in sequence_num order:
          → Checkpoint 1: evaluate agent decision → select branch → RunCheckpointResult
            → if can_spawn_theatre: TheatreSpawner.spawn() → Theatre record
          → Checkpoint 2: ...
          → Checkpoint N: ...
        → All checkpoints resolved → ScenarioPack: ACTIVE → SETTLING → RESOLVED
          → Telemetry aggregated → available to RLMF export pipeline
```

**Derived theatre spawning:**

```
Checkpoint resolves with can_spawn_theatre=True
  → TheatreSpawner.spawn(checkpoint, branch_result)
    → Creates Theatre(spawned_from_checkpoint_id=checkpoint.id)
    → Theatre follows normal lifecycle: DRAFT → COMMITTED → ACTIVE → RESOLVED
    → ScenarioPackAuditEvent(THEATRE_SPAWNED)
      → WS broadcast: THEATRE_SPAWNED
```

---

## 2. Sprint 0 — Schema Foundation + Migration

### 2.1 Model Definitions

**New file concepts in:** `backend/database/models.py`

**ScenarioPackTemplate** — immutable definition of a scenario pack:

```python
class ScenarioPackTemplate(Base):
    __tablename__ = "scenario_pack_templates"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    family: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="NAV_UNC | SOC_NAV | MAN_FORCE | MARL_C3 | 3D_INERT | LONG_HZN | PUZ_LOGIC | ADV_AIR | PREC_MAN"
    )
    fantasy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    training_primitives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON blobs matching existing fixture shape
    objective_vector_json: Mapped[dict] = mapped_column(JSON, default=list)
    fork_point_schema_json: Mapped[dict] = mapped_column(JSON, default=list)
    saboteur_deck_json: Mapped[dict] = mapped_column(JSON, default=list)
    telemetry_spec_json: Mapped[dict] = mapped_column(JSON, default=dict)
    settlement_rules_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Meta
    episode_length_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fork_points_min: Mapped[int] = mapped_column(Integer, default=1)
    fork_points_max: Mapped[int] = mapped_column(Integer, default=10)
    settlement_latency_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    template_status: Mapped[str] = mapped_column(String(20), default="CATALOG_ONLY", comment="RUNNABLE | CATALOG_ONLY")
    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    packs: Mapped[List["ScenarioPack"]] = relationship(back_populates="template")
    checkpoints: Mapped[List["ScenarioCheckpoint"]] = relationship(
        back_populates="template", order_by="ScenarioCheckpoint.sequence_num"
    )
```

**ScenarioCheckpoint** — a decision point within a template:

```python
class ScenarioCheckpoint(Base):
    __tablename__ = "scenario_checkpoints"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("scenario_pack_templates.id"), index=True
    )
    sequence_num: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String(255))
    trigger_condition_json: Mapped[dict] = mapped_column(JSON, default=dict)
    market_question: Mapped[str] = mapped_column(Text)
    decision_window_sec: Mapped[int] = mapped_column(Integer, default=30)
    can_spawn_theatre: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluator_type: Mapped[str] = mapped_column(String(30), default="binary_risk_gate", comment="binary_risk_gate | resource_depletion | detection_event | timing_breach | mission_completion")
    theatre_spawn_rule_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    template: Mapped["ScenarioPackTemplate"] = relationship(back_populates="checkpoints")
    branches: Mapped[List["CheckpointBranch"]] = relationship(back_populates="checkpoint")
```

**CheckpointBranch** — an outcome path from a checkpoint:

```python
class CheckpointBranch(Base):
    __tablename__ = "checkpoint_branches"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    checkpoint_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    branch_rule_json: Mapped[dict] = mapped_column(JSON, default=dict)
    outcome_type: Mapped[str] = mapped_column(
        String(20), comment="success | failure | partial | continue"
    )
    reward_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict)
    next_checkpoint_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id"), nullable=True
    )

    # Relationships
    checkpoint: Mapped["ScenarioCheckpoint"] = relationship(
        back_populates="branches", foreign_keys=[checkpoint_id]
    )
```

**ScenarioPack** — an instance of a pack created by a user:

```python
class ScenarioPack(Base):
    __tablename__ = "scenario_packs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("scenario_pack_templates.id"), index=True
    )
    state: Mapped[str] = mapped_column(
        String(20), default="DRAFT", index=True,
        comment="DRAFT | COMMITTED | ACTIVE | SETTLING | RESOLVED"
    )
    commitment_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Run configuration
    run_mode: Mapped[str] = mapped_column(String(30), default="TRAINING", comment="TRAINING | EVALUATION | CALIBRATION | REPLAY")
    agent_assignment: Mapped[str] = mapped_column(String(50), default="auto_assign")
    simulation_scale: Mapped[str] = mapped_column(String(20), default="single_1x")
    objective_profile: Mapped[str] = mapped_column(String(50), default="pack_default")

    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    template: Mapped["ScenarioPackTemplate"] = relationship(back_populates="packs")
    runs: Mapped[List["ScenarioRun"]] = relationship(back_populates="pack")
    audit_events: Mapped[List["ScenarioPackAuditEvent"]] = relationship(back_populates="pack")
```

**ScenarioRun** — a single execution of a pack through checkpoints:

```python
class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    pack_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_packs.id"), index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING",
        comment="PENDING | RUNNING | COMPLETED | FAILED"
    )
    environment_seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    run_mode: Mapped[str] = mapped_column(String(20), default="TRAINING", comment="TRAINING | EVALUATION | CALIBRATION | REPLAY")
    current_checkpoint_seq: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    telemetry_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    episode_duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_reward: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    pack: Mapped["ScenarioPack"] = relationship(back_populates="runs")
    checkpoint_results: Mapped[List["RunCheckpointResult"]] = relationship(
        back_populates="run", order_by="RunCheckpointResult.resolved_at"
    )
```

**RunCheckpointResult** — the outcome at a specific checkpoint during a run:

```python
class RunCheckpointResult(Base):
    __tablename__ = "run_checkpoint_results"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    run_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_runs.id"), index=True
    )
    checkpoint_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id")
    )
    selected_branch_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("checkpoint_branches.id")
    )
    agent_decision_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    state_vector_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    spawned_theatre_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=True
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["ScenarioRun"] = relationship(back_populates="checkpoint_results")
```

**ScenarioPackAuditEvent** — mirrors TheatreAuditEvent pattern:

```python
class ScenarioPackAuditEvent(Base):
    __tablename__ = "scenario_pack_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    pack_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_packs.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), index=True,
        comment="PACK_CREATED | PACK_COMMITTED | RUN_STARTED | CHECKPOINT_RESOLVED | THEATRE_SPAWNED | PACK_RESOLVED"
    )
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    pack: Mapped["ScenarioPack"] = relationship(back_populates="audit_events")
```

### 2.2 Theatre Model Extension

**Modified:** `backend/database/models.py` — Theatre model

Add provenance link for derived theatres:

```python
# On Theatre model
spawned_from_checkpoint_id: Mapped[Optional[str]] = mapped_column(
    String(50), ForeignKey("scenario_checkpoints.id"), nullable=True,
    comment="Provenance: which scenario checkpoint spawned this theatre"
)
```

### 2.3 Migration

**New:** `backend/alembic/versions/c018_scenario_packs.py`

Dialect-safe migration:

1. Create `scenario_pack_templates` table
2. Create `scenario_checkpoints` table (FK → templates)
3. Create `checkpoint_branches` table (FK → checkpoints)
4. Create `scenario_packs` table (FK → templates)
5. Create `scenario_runs` table (FK → packs)
6. Create `run_checkpoint_results` table (FK → runs, checkpoints, branches, theatres)
7. Create `scenario_pack_audit_events` table (FK → packs)
8. Add `spawned_from_checkpoint_id` column to `theatres` table
9. Create indexes on state, family, template_id, pack_id, checkpoint_id

### 2.4 Pydantic Schema Extensions

**New file:** `backend/schemas/scenario_packs.py`

```python
# Template schemas
class ObjectiveVectorComponent(BaseModel):
    component: str
    weight: float
    description: str

class ForkPointSchema(BaseModel):
    trigger: str
    market_question: str = Field(alias="marketQuestion")
    options: List[str]
    decision_window_sec: int = Field(alias="decisionWindowSec")

class SaboteurCard(BaseModel):
    card: str
    price: float
    bounded_effect: float = Field(alias="boundedEffect")
    notes: str

class ScenarioPackTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    family: str
    fantasy: Optional[str] = None
    training_primitives: Optional[str] = None
    template_status: str  # RUNNABLE | CATALOG_ONLY
    objective_vector: List[ObjectiveVectorComponent]
    fork_points: List[ForkPointSchema]
    saboteur_deck: List[SaboteurCard]
    episode_length_sec: Optional[int] = None
    fork_points_min: int
    fork_points_max: int
    is_seeded: bool
    checkpoint_count: int  # computed
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ScenarioPackTemplateSummaryResponse(BaseModel):
    id: str
    name: str
    family: str
    description: Optional[str] = None
    template_status: str  # RUNNABLE | CATALOG_ONLY
    checkpoint_count: int
    fork_points_min: int
    fork_points_max: int
    is_seeded: bool
    model_config = ConfigDict(from_attributes=True)

class TemplateListResponse(BaseModel):
    templates: List[ScenarioPackTemplateSummaryResponse]
    total: int
    limit: int
    offset: int

# Pack schemas
class ScenarioPackCreate(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=100)
    run_mode: str = Field("TRAINING")
    agent_assignment: str = Field("auto_assign")
    simulation_scale: str = Field("single_1x")
    objective_profile: str = Field("pack_default")
    config_json: Optional[dict] = None

class ScenarioPackResponse(BaseModel):
    id: str
    user_id: str
    template_id: str
    state: str
    run_mode: str
    agent_assignment: str
    simulation_scale: str
    objective_profile: str
    commitment_hash: Optional[str] = None
    committed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Run schemas
class ScenarioRunResponse(BaseModel):
    id: str
    pack_id: str
    agent_id: Optional[str] = None
    status: str
    current_checkpoint_seq: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    episode_duration_sec: Optional[float] = None
    total_reward: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Checkpoint result schemas
class CheckpointResultResponse(BaseModel):
    id: str
    checkpoint_id: str
    selected_branch_id: str
    reward: float
    spawned_theatre_id: Optional[str] = None
    resolved_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Episode tree response
class EpisodeTreeNode(BaseModel):
    checkpoint_id: str
    sequence_num: int
    trigger: str
    market_question: str
    selected_branch: Optional[str] = None
    outcome_type: Optional[str] = None
    reward: Optional[float] = None
    spawned_theatre_id: Optional[str] = None
    children: List["EpisodeTreeNode"] = []

class EpisodeTreeResponse(BaseModel):
    run_id: str
    pack_id: str
    template_name: str
    status: str
    nodes: List[EpisodeTreeNode]
    total_reward: float
    episode_duration_sec: Optional[float] = None
```

---

## 3. Sprint 1 — Template Catalog + Seeding

### 3.1 Template Seeder

**New:** `backend/services/scenario_template_seeder.py`

Converts the 18 library entries into `ScenarioPackTemplate` + `ScenarioCheckpoint` + `CheckpointBranch` records. Also ingests the 4 existing JSON fixtures for templates that overlap (Neon Courier, Disaster Response, Orbital Salvage, Blacksite Heist).

```python
TEMPLATE_FAMILIES = {
    "NAV_UNC": ["neon_courier", "midnight_exchange", "runway_intercept", "last_mile_hospital"],
    "SOC_NAV": ["velvet_rope"],
    "MAN_FORCE": ["skybridge_assembly", "high_rise_steel"],
    "MARL_C3": ["disaster_response", "cooling_plant", "reactor_protocol", "heist_echelon", "blacksite_heist"],
    "3D_INERT": ["orbital_salvage", "orbital_docking"],
    "LONG_HZN": ["icebreaker_convoy"],
    "PUZ_LOGIC": ["escape_room"],
    "ADV_AIR": ["dogfight_echelon"],
    "PREC_MAN": ["cleanroom_microsurgery"],
}

async def seed_templates(session: AsyncSession) -> int:
    """Seed all 18 templates. Idempotent — skips existing."""
    ...
```

For templates with existing JSON fixtures, the seeder reads `forkPointSchema` entries and creates `ScenarioCheckpoint` + `CheckpointBranch` records from them.

For templates without fixtures (library-only), the seeder creates checkpoints from the `Fork points` description and branches from the listed options.

### 3.2 Template API

**New file:** `backend/api/scenario_pack_routes.py`

```python
templates_router = APIRouter(
    prefix="/api/v1/scenario-pack-templates",
    tags=["scenario-pack-templates"]
)

@templates_router.get("/", response_model=TemplateListResponse)
async def list_templates(
    family: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List scenario pack templates, optionally filtered by family."""
    ...

@templates_router.get("/{template_id}", response_model=ScenarioPackTemplateResponse)
async def get_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a single template with checkpoints, objective vector, and saboteur deck."""
    ...
```

### 3.3 Frontend Integration

Replace the empty ScenarioPacksPage catalog with real API calls to `/api/v1/scenario-pack-templates`. Render template cards with family badge, checkpoint count, and fork range.

---

## 4. Sprint 2 — Pack Lifecycle

### 4.1 Pack State Machine

Mirrors Theatre lifecycle:

```
DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED
         (hash)      (run)    (auto)     (auto)
```

Valid transitions:
- DRAFT → COMMITTED: generates commitment_hash
- COMMITTED → ACTIVE: on run launch
- ACTIVE → SETTLING: when all checkpoints resolved
- SETTLING → RESOLVED: when telemetry aggregated

### 4.2 Pack CRUD API

```python
packs_router = APIRouter(
    prefix="/api/v1/scenario-packs",
    tags=["scenario-packs"]
)

@packs_router.post("/", response_model=ScenarioPackResponse, status_code=201)
async def create_pack(
    body: ScenarioPackCreate,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new scenario pack from a template."""
    ...

@packs_router.post("/{pack_id}/commit", response_model=ScenarioPackResponse)
async def commit_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Commit the pack (DRAFT → COMMITTED). Generates commitment hash."""
    ...

@packs_router.post("/{pack_id}/run", status_code=202)
async def run_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Launch an async run (COMMITTED → ACTIVE). Returns run_id."""
    ...

@packs_router.get("/{pack_id}", response_model=ScenarioPackResponse)
async def get_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get pack details. Auth: owner only."""
    ...
```

---

## 5. Sprint 3 — Checkpoint Resolution + Branching

### 5.0 ScenarioSeedManager Service

**New:** `backend/services/scenario_seed_manager.py`

```python
class ScenarioSeedManager:
    """
    Allocates environment seeds for scenario runs based on run_mode policy.

    Run mode semantics:
    - TRAINING: stochastic, varying seeds (random per run)
    - EVALUATION: controlled stochasticity from a fixed seed set
    - CALIBRATION: canonical seed set for cross-run comparability
    - REPLAY: exact recorded path, no fresh randomness (uses stored seed)
    """

    def allocate_seed(self, run_mode: str, run_index: int = 0, replay_seed: Optional[int] = None) -> int:
        """Return environment seed for a new run."""
        ...

    CALIBRATION_SEEDS = [42, 137, 256, 512, 1024]  # canonical seed set
```

### 5.1 CheckpointEvaluator Service

**New:** `backend/services/checkpoint_evaluator.py`

```python
class CheckpointEvaluator:
    """
    Schema-driven checkpoint automation engine.

    Processes checkpoints in sequence using declarative checkpoint schemas.
    Each checkpoint declares: trigger_condition, decision_window, evaluator_type,
    branch_rules, reward_mapping, optional theatre_spawn_rule.

    Built-in evaluator primitives (v1):
    - BINARY_RISK_GATE: binary pass/fail based on risk threshold
    - RESOURCE_DEPLETION: resource level vs threshold comparison
    - DETECTION_EVENT: detection probability vs stealth score
    - TIMING_BREACH: time elapsed vs window constraint
    - MISSION_COMPLETION: objective completion percentage

    Branch selection is deterministic given (agent action, checkpoint state,
    environment seed, evaluator config). Environment seed allocated by
    ScenarioSeedManager based on run_mode policy.

    At each checkpoint:
    1. Evaluate trigger_condition_json against current run state
    2. Execute evaluator_type primitive with checkpoint config
    3. Select branch via branch_rule_json, deterministically using environment seed
    4. Compute reward from reward_mapping_json + objective vector weights
    5. Record RunCheckpointResult
    6. If theatre_spawn_rule_json present + can_spawn_theatre, trigger TheatreSpawner
    7. Advance to next checkpoint (via branch.next_checkpoint_id)
    """

    async def evaluate_next(
        self, session: AsyncSession, run: ScenarioRun, seed: Optional[int] = None
    ) -> RunCheckpointResult:
        """Evaluate the next checkpoint in sequence with optional seed parameter."""
        ...

    async def evaluate_all(
        self, session: AsyncSession, run: ScenarioRun, seed: Optional[int] = None
    ) -> List[RunCheckpointResult]:
        """Process all remaining checkpoints for a run with seed parameter."""
        ...

    def _select_branch(
        self, checkpoint: ScenarioCheckpoint, decision: dict, seed: Optional[int] = None
    ) -> CheckpointBranch:
        """Determine which branch the agent's decision leads to, deterministically using seed."""
        ...

    def _compute_reward(
        self, checkpoint: ScenarioCheckpoint, branch: CheckpointBranch,
        objective_vector: List[dict]
    ) -> float:
        """Compute reward at this checkpoint based on objective vector weights."""
        ...
```

### 5.2 Episode Tree Reconstruction

```python
@packs_router.get(
    "/{pack_id}/runs/{run_id}/tree",
    response_model=EpisodeTreeResponse
)
async def get_episode_tree(
    pack_id: str, run_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Reconstruct the full episode tree from checkpoint results.
    Returns a tree structure showing which branches were taken,
    rewards at each node, and any spawned theatres.
    """
    ...
```

### 5.3 Branch Probability Tracking

Across multiple runs of the same template, track how often each branch is selected:

```python
@templates_router.get(
    "/{template_id}/branch-probabilities",
    response_model=dict
)
async def get_branch_probabilities(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Returns {checkpoint_id: {branch_id: probability}} computed from
    all completed runs of this template.
    """
    ...
```

---

## 6. Sprint 4 — Derived Theatre Spawning

### 6.1 TheatreSpawner Service

**New:** `backend/services/theatre_spawner.py`

```python
class TheatreSpawner:
    """
    Spawns real Theatre records from scenario checkpoints.

    Principle: scenario packs can spawn theatres;
    theatres do not contain scenario packs.
    """

    async def spawn(
        self,
        session: AsyncSession,
        checkpoint: ScenarioCheckpoint,
        branch_result: RunCheckpointResult,
        pack: ScenarioPack,
        run: ScenarioRun,
    ) -> Theatre:
        """
        Create a Theatre from a checkpoint's market question.

        The spawned theatre:
        - Uses the checkpoint's market_question as the inquiry
        - Gets spawned_from_checkpoint_id for provenance
        - Includes run_id for per-run uniqueness in construct_id
        - Follows normal theatre lifecycle
        - Can issue certificates via existing pipeline
        """
        theatre = Theatre(
            user_id=pack.user_id,
            template_id=self._derive_template_id(checkpoint),
            construct_id=f"scenario_{pack.id}_run_{run.id}_cp_{checkpoint.id}",
            spawned_from_checkpoint_id=checkpoint.id,
            state="DRAFT",
            # ... other fields from checkpoint context
        )
        session.add(theatre)

        # Audit event
        audit = ScenarioPackAuditEvent(
            pack_id=pack.id,
            event_type="THEATRE_SPAWNED",
            detail_json={
                "theatre_id": theatre.id,
                "checkpoint_id": checkpoint.id,
                "branch_id": branch_result.selected_branch_id,
                "market_question": checkpoint.market_question,
            }
        )
        session.add(audit)

        return theatre
```

### 6.2 Derived Theatre API

```python
@packs_router.get(
    "/{pack_id}/derived-theatres",
    response_model=List[TheatreResponse]
)
async def list_derived_theatres(
    pack_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List all theatres spawned from this pack's checkpoints."""
    ...
```

---

## 7. Sprint 5 — RLMF Telemetry + Frontend Integration

### 7.1 RLMF Telemetry Integration

Scenario run telemetry feeds into the existing RLMF export infrastructure:

```python
class ScenarioTelemetryExporter:
    """
    Converts ScenarioRun + RunCheckpointResults into RLMF-compatible
    export records matching the existing ExportFilter/ExportScope shape.
    """

    async def export_run(self, run: ScenarioRun) -> dict:
        """
        Returns RLMF training record:
        {
            "episode_id": run.id,
            "scenario_pack_id": run.pack_id,
            "template_id": run.pack.template_id,
            "agent_id": run.agent_id,
            "actions": [...],  # checkpoint decisions
            "rewards": [...],  # per-checkpoint rewards
            "state_features": {...},  # aggregated state vectors
            "fork_count": len(run.checkpoint_results),
            "episode_duration_sec": run.episode_duration_sec,
            "branch_path": [...],  # ordered branch selections
            "spawned_theatre_ids": [...],
        }
        """
        ...
```

### 7.2 New WebSocket Event Types

**Modified:** `backend/websockets/realtime_manager.py`

```python
async def broadcast_scenario_run_status(self, pack_id: str, run_id: str, status: str):
    """Broadcast run status change (PENDING → RUNNING → COMPLETED)."""
    await self.broadcast_global("SCENARIO_RUN_STATUS", {
        "pack_id": pack_id,
        "run_id": run_id,
        "status": status,
    })

async def broadcast_checkpoint_resolved(self, pack_id: str, result: dict):
    """Broadcast when a checkpoint is resolved during a run."""
    await self.broadcast_to_channel(
        f"scenario:{pack_id}",
        "CHECKPOINT_RESOLVED",
        result,
    )

async def broadcast_theatre_spawned(self, pack_id: str, theatre_id: str, checkpoint_id: str):
    """Broadcast when a derived theatre is spawned."""
    await self.broadcast_global("THEATRE_SPAWNED", {
        "pack_id": pack_id,
        "theatre_id": theatre_id,
        "checkpoint_id": checkpoint_id,
    })
```

### 7.3 Frontend Components

**ScenarioPacksPage** — wire to `/api/v1/scenario-pack-templates` for catalog, `/api/v1/scenario-packs` for user packs.

**Branch Map Visualization** — render from episode tree API (`/runs/{id}/tree`). Colour vocabulary from design reference:
- Start node: purple
- Checkpoint node: orange
- Success terminal: green
- Failure terminal: red
- Partial terminal: dark orange
- Main path edges: purple
- Success branch edges: green
- Failure branch edges: red

**Launch Configuration Panel** — submits to `POST /api/v1/scenario-packs` with run_mode, agent_assignment, simulation_scale, objective_profile.

**Run Status** — subscribe to `SCENARIO_RUN_STATUS` and `CHECKPOINT_RESOLVED` WS events for live updates.

---

## 8. Testing Strategy

### Unit Tests (per service)

| Service | Tests | Focus |
|---------|-------|-------|
| Template seeder | 2 | Seed all 18, idempotent re-seed |
| CheckpointEvaluator | 4 | Sequential eval, branch selection, reward computation, spawn trigger |
| TheatreSpawner | 3 | Spawn creation, provenance link, audit event |
| ScenarioTelemetryExporter | 1 | RLMF record shape |

### Integration Tests

| Test | Focus |
|------|-------|
| Template catalog listing + family filter | API |
| Pack create → commit → run lifecycle | State machine |
| Checkpoint resolution → branch probabilities | Episode logic |
| Checkpoint → derived theatre spawn | Cross-entity |
| E2E: pack → run → checkpoints → theatre spawn → RLMF | Full lifecycle |

### Regression

All existing post-017 tests (≥1100) must pass before and after each sprint.
