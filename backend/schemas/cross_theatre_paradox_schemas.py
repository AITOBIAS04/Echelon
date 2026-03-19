"""Pydantic schemas for CrossTheatreParadox API.

Cycle 038: Cross-Theatre Paradox Detection.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ParadoxTypeEnum(str, Enum):
    SETTLEMENT_DIVERGENCE = "SETTLEMENT_DIVERGENCE"
    ORACLE_INCONSISTENCY = "ORACLE_INCONSISTENCY"
    SCOPE_OVERLAP_GAP = "SCOPE_OVERLAP_GAP"
    TEMPORAL_DRIFT = "TEMPORAL_DRIFT"


class ParadoxSeverityEnum(str, Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    MATERIAL = "MATERIAL"
    CRITICAL = "CRITICAL"


class ParadoxStatusEnum(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class CrossTheatreParadoxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fact_anchor_id: str
    coherence_group_id: Optional[str] = None
    paradox_type: ParadoxTypeEnum
    severity: ParadoxSeverityEnum
    theatre_a_id: str
    theatre_b_id: str
    description: str
    evidence_json: dict
    resolution_status: ParadoxStatusEnum
    resolved_at: Optional[datetime] = None
    created_at: datetime


class CrossTheatreParadoxListResponse(BaseModel):
    paradoxes: list[CrossTheatreParadoxResponse]
    total: int


class ResolveParadoxRequest(BaseModel):
    note: str = Field(..., min_length=1, description="Resolution note explaining the action")
