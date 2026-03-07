"""
Pydantic schemas for Agent Deployment API (Cycle 019).
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class AgentDeploymentCreate(BaseModel):
    agent_id: str
    theatre_id: str
    strategy_profile: str = "BALANCED"
    config_json: Optional[dict] = None


class StrategyUpdateRequest(BaseModel):
    strategy_profile: str


class AgentDeploymentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    theatre_id: str
    status: str
    strategy_profile: str
    deployed_at: datetime
    created_at: datetime


class AgentDeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    config_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class DeploymentAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    deployment_id: str
    event_type: str
    detail_json: Optional[dict] = None
    created_at: datetime


class DeploymentDetailResponse(AgentDeploymentResponse):
    audit_events: List[DeploymentAuditEventResponse] = []


class DeploymentListResponse(BaseModel):
    deployments: List[AgentDeploymentSummaryResponse]
    total: int
    limit: int
    offset: int


class ParadoxRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: Optional[str] = None
    factors: Optional[dict] = None
    explanation: Optional[str] = None
    updated_at: Optional[datetime] = None
