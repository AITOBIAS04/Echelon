"""Investigation Template API schemas — Pydantic models for template REST endpoints (Cycle-022)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================
# RESPONSE SCHEMAS
# ============================================


class InvestigationTemplateListItem(BaseModel):
    """Summary item for template list responses."""

    template_id: str
    name: str
    description: Optional[str] = None
    inquiry_class: str = "INVESTIGATIVE"
    template_status: str = "ACTIVE"
    domain_filter_count: int = 0
    requires_legal_review: bool = False


class InvestigationTemplateListResponse(BaseModel):
    """Paginated list of investigation templates."""

    templates: list[InvestigationTemplateListItem] = Field(default_factory=list)
    total: int = 0


class InvestigationTemplateDetail(BaseModel):
    """Full investigation template detail."""

    template_id: str
    name: str
    description: Optional[str] = None
    inquiry_class: str = "INVESTIGATIVE"
    domain_filters: list[str] = Field(default_factory=list)
    default_sources: list[str] = Field(default_factory=list)
    default_stop_condition: str = "OUTCOME_RESOLUTION"
    default_time_window_days: Optional[int] = None
    requires_legal_review: bool = False
    min_corroboration_groups: int = 2
    template_status: str = "ACTIVE"
    is_seeded: bool = False
    created_at: datetime
