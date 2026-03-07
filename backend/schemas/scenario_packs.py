"""
Pydantic schemas for Scenario Packs Engine (Cycle-018).
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


# ── Nested components ──

class ObjectiveVectorComponent(BaseModel):
    component: str
    weight: float
    description: str


class ForkPointSchema(BaseModel):
    trigger: str
    market_question: str = Field(alias="marketQuestion", default="")
    options: List[str] = []
    decision_window_sec: int = Field(alias="decisionWindowSec", default=30)

    model_config = ConfigDict(populate_by_name=True)


class SaboteurCard(BaseModel):
    card: str
    price: float
    bounded_effect: float = Field(alias="boundedEffect", default=0.0)
    notes: str = ""

    model_config = ConfigDict(populate_by_name=True)


class CheckpointResponse(BaseModel):
    id: str
    sequence_num: int
    trigger: str
    market_question: str
    decision_window_sec: int
    can_spawn_theatre: bool
    evaluator_type: str
    branch_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class BranchResponse(BaseModel):
    id: str
    label: str
    outcome_type: str
    next_checkpoint_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Template schemas ──

class ScenarioPackTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    family: str
    fantasy: Optional[str] = None
    training_primitives: Optional[str] = None
    template_status: str
    objective_vector: List[ObjectiveVectorComponent] = []
    fork_points: List[ForkPointSchema] = []
    saboteur_deck: List[SaboteurCard] = []
    episode_length_sec: Optional[int] = None
    fork_points_min: int = 1
    fork_points_max: int = 10
    is_seeded: bool = False
    checkpoint_count: int = 0
    checkpoints: List[CheckpointResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioPackTemplateSummaryResponse(BaseModel):
    id: str
    name: str
    family: str
    description: Optional[str] = None
    template_status: str
    checkpoint_count: int = 0
    fork_points_min: int = 1
    fork_points_max: int = 10
    is_seeded: bool = False

    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    templates: List[ScenarioPackTemplateSummaryResponse]
    total: int
    limit: int
    offset: int


# ── Pack schemas ──

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


# ── Run schemas ──

class ScenarioRunResponse(BaseModel):
    id: str
    pack_id: str
    agent_id: Optional[str] = None
    status: str
    environment_seed: Optional[int] = None
    run_mode: str
    current_checkpoint_seq: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    episode_duration_sec: Optional[float] = None
    total_reward: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Checkpoint result schemas ──

class CheckpointResultResponse(BaseModel):
    id: str
    checkpoint_id: str
    selected_branch_id: str
    reward: float
    spawned_theatre_id: Optional[str] = None
    resolved_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Episode tree response ──

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
