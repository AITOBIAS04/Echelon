"""Pydantic schemas for OracleConsistency API.

Cycle 038: Cross-Theatre Paradox Detection.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecordOracleResponseRequest(BaseModel):
    theatre_id: str
    source: str = Field(..., description="Oracle source (e.g., usgs_neic)")
    event_id: str = Field(..., description="Source-specific event ID")
    value_json: dict = Field(..., description="Full oracle response data")
    queried_at: datetime
    is_provisional: bool = Field(False, description="True for automatic/preliminary responses")


class OracleResponseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    theatre_id: str
    source: str
    event_id: str
    value_json: dict
    queried_at: datetime
    is_provisional: bool
    created_at: datetime


class ConsistencyCheckResponse(BaseModel):
    is_consistent: bool
    source: str
    event_id: str
    responses: list[dict]
    max_delta: Optional[float] = None
    explanation: str


class DivergenceRecordResponse(BaseModel):
    source: str
    event_id: str
    theatre_ids: list[str]
    delta: float
    detected_at: datetime
