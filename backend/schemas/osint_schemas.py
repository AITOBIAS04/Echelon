"""
OSINT Schemas — Cycle 025
=========================

Response schemas for OSINT signals, health, and summary endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OsintSignalResponse(BaseModel):
    """Individual OSINT signal from the persisted signals table."""
    id: str
    source_id: str
    source_group: str
    signal_type: str
    geo_region: Optional[str] = None
    entity_ref: Optional[str] = None
    content_hash: str
    normalised_data: dict
    investigation_id: Optional[str] = None
    collected_at: datetime

    class Config:
        from_attributes = True


class PaginatedSignalsResponse(BaseModel):
    """Paginated response for GET /osint/signals."""
    signals: list[OsintSignalResponse]
    limit: int
    offset: int


class OsintHealthResponse(BaseModel):
    """OSINT feed health for the Operations panel."""
    feeds_online: int
    feeds_total: int
    signal_latency_sec: Optional[int] = None
    escalation_queue_depth: int
    replay_workers_active: int


class SignalSummaryResponse(BaseModel):
    """Signal aggregates for the canvas toolbar."""
    total_signals: int
    by_source_group: dict[str, int]
    counter_signals: int
    certificate_candidates: int
    convergence_cells: int
