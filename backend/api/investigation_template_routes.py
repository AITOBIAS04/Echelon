"""Investigation Template API Routes — Read-only endpoints for investigation templates.

Cycle-022 Sprint 1: Template catalog (list + detail).
Templates are seeded, not user-created — no CRUD endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import InvestigationTemplate
from backend.dependencies import get_db
from backend.schemas.investigation_template_schemas import (
    InvestigationTemplateDetail,
    InvestigationTemplateListItem,
    InvestigationTemplateListResponse,
)

logger = logging.getLogger(__name__)

templates_router = APIRouter(
    prefix="/api/v1/investigation-templates",
    tags=["investigation-templates"],
)


@templates_router.get("/", response_model=InvestigationTemplateListResponse)
async def list_investigation_templates(
    inquiry_class: Optional[str] = Query(None, description="Filter by inquiry class (exact match)"),
    status: Optional[str] = Query(None, description="Filter by template_status (ACTIVE or DRAFT)"),
    session: AsyncSession = Depends(get_db),
):
    """List investigation templates with optional inquiry_class and status filters.

    Defaults to ACTIVE templates only if no status filter is provided.
    """
    query = select(InvestigationTemplate)
    count_query = select(func.count()).select_from(InvestigationTemplate)

    # Default to ACTIVE only
    effective_status = status.upper() if status else "ACTIVE"
    query = query.where(InvestigationTemplate.template_status == effective_status)
    count_query = count_query.where(InvestigationTemplate.template_status == effective_status)

    if inquiry_class:
        inquiry_upper = inquiry_class.upper()
        query = query.where(InvestigationTemplate.inquiry_class == inquiry_upper)
        count_query = count_query.where(InvestigationTemplate.inquiry_class == inquiry_upper)

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get results ordered by name
    query = query.order_by(InvestigationTemplate.name)
    result = await session.execute(query)
    templates = result.scalars().all()

    items = [
        InvestigationTemplateListItem(
            template_id=t.id,
            name=t.name,
            description=t.description,
            inquiry_class=t.inquiry_class,
            template_status=t.template_status,
            domain_filter_count=len(t.domain_filters_json) if t.domain_filters_json else 0,
            requires_legal_review=t.requires_legal_review,
        )
        for t in templates
    ]

    return InvestigationTemplateListResponse(templates=items, total=total)


@templates_router.get("/{template_id}", response_model=InvestigationTemplateDetail)
async def get_investigation_template(
    template_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get full investigation template detail by ID."""
    result = await session.execute(
        select(InvestigationTemplate).where(InvestigationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail=f"Investigation template '{template_id}' not found")

    return InvestigationTemplateDetail(
        template_id=template.id,
        name=template.name,
        description=template.description,
        inquiry_class=template.inquiry_class,
        domain_filters=template.domain_filters_json or [],
        default_sources=template.default_sources_json or [],
        default_stop_condition=template.default_stop_condition,
        default_time_window_days=template.default_time_window_days,
        requires_legal_review=template.requires_legal_review,
        min_corroboration_groups=template.min_corroboration_groups,
        template_status=template.template_status,
        is_seeded=template.is_seeded,
        created_at=template.created_at,
    )
