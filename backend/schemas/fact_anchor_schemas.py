"""Pydantic schemas for FactAnchor API.

Cycle 038: Cross-Theatre Paradox Detection.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateFactAnchorRequest(BaseModel):
    anchor_type: str = Field(..., description="Domain type (e.g., seismic_event)")
    external_id: str = Field(..., description="Source-specific event ID (e.g., us6000test)")
    external_source: str = Field(..., description="Data source (e.g., usgs_neic)")
    occurred_at: datetime = Field(..., description="When the real-world event occurred")
    location_json: Optional[dict] = Field(None, description="Location data (lat/lon/depth)")
    metadata_json: Optional[dict] = Field(None, description="Source-specific metadata")


class LinkTheatreRequest(BaseModel):
    theatre_id: str
    link_type: str = Field(..., description="settlement | evidence | oracle_query")
    linked_entity_id: str = Field(..., description="ID of the linked entity in the theatre")
    linked_entity_type: str = Field(..., description="Type of linked entity (e.g., theatre_outcome)")
    link_confidence: float = Field(1.0, ge=0.0, le=1.0)


class FactAnchorLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    theatre_id: str
    link_type: str
    link_confidence: float
    linked_entity_id: str
    linked_entity_type: str
    created_at: datetime


class FactAnchorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    anchor_type: str
    external_id: str
    external_source: str
    occurred_at: datetime
    location_json: Optional[dict] = None
    metadata_json: Optional[dict] = None
    link_count: int = 0
    created_at: datetime


class FactAnchorDetailResponse(FactAnchorResponse):
    links: list[FactAnchorLinkResponse] = []
