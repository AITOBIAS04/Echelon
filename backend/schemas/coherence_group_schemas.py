"""Pydantic schemas for CoherenceGroup API.

Cycle 038: Cross-Theatre Paradox Detection.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateCoherenceGroupRequest(BaseModel):
    name: str = Field(..., description="Unique group name")
    group_type: str = Field(..., description="Group type (e.g., domain_overlap)")
    policy_json: dict = Field(
        default_factory=dict,
        description="Policy thresholds (settlement_divergence_threshold, oracle_tolerance, etc.)",
    )


class AddMemberRequest(BaseModel):
    theatre_id: str
    role: str = Field("primary", description="Member role (primary | observer)")


class CoherenceGroupMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    coherence_group_id: str
    theatre_id: str
    role: str
    joined_at: datetime


class CoherenceGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    group_type: str
    policy_json: dict
    created_at: datetime


class CoherenceGroupDetailResponse(CoherenceGroupResponse):
    members: list[CoherenceGroupMemberResponse] = []
