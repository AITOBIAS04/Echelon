"""
FactAnchor API Routes — real-world event registry with theatre linking.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    FactAnchor,
    FactAnchorLink,
    CrossTheatreParadox,
)
from backend.schemas.fact_anchor_schemas import (
    CreateFactAnchorRequest,
    LinkTheatreRequest,
    FactAnchorResponse,
    FactAnchorDetailResponse,
    FactAnchorLinkResponse,
)
from backend.schemas.cross_theatre_paradox_schemas import (
    CrossTheatreParadoxResponse,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData
from backend.services.fact_anchor_service import FactAnchorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fact-anchors", tags=["fact-anchors"])


def _anchor_to_response(anchor: FactAnchor, link_count: int = 0) -> FactAnchorResponse:
    return FactAnchorResponse(
        id=anchor.id,
        anchor_type=anchor.anchor_type,
        external_id=anchor.external_id,
        external_source=anchor.external_source,
        occurred_at=anchor.occurred_at,
        location_json=anchor.location_json,
        metadata_json=anchor.metadata_json,
        link_count=link_count,
        created_at=anchor.created_at,
    )


# ============================================
# POST / — Create or get FactAnchor (idempotent)
# ============================================

@router.post("/", response_model=FactAnchorResponse, status_code=status.HTTP_201_CREATED)
async def create_fact_anchor(
    body: CreateFactAnchorRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or retrieve a FactAnchor by (external_source, external_id)."""
    svc = FactAnchorService(db)
    anchor = await svc.get_or_create(
        anchor_type=body.anchor_type,
        external_id=body.external_id,
        external_source=body.external_source,
        occurred_at=body.occurred_at,
        location_json=body.location_json,
        metadata_json=body.metadata_json,
    )
    await db.commit()

    count_result = await db.execute(
        select(func.count(FactAnchorLink.id)).where(
            FactAnchorLink.fact_anchor_id == anchor.id
        )
    )
    link_count = count_result.scalar_one()

    return _anchor_to_response(anchor, link_count)


# ============================================
# GET / — List anchors
# ============================================

@router.get("/", response_model=list[FactAnchorResponse])
async def list_fact_anchors(
    anchor_type: Optional[str] = Query(None),
    external_source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List FactAnchors with optional filters."""
    query = select(FactAnchor).order_by(FactAnchor.created_at.desc())
    if anchor_type:
        query = query.where(FactAnchor.anchor_type == anchor_type)
    if external_source:
        query = query.where(FactAnchor.external_source == external_source)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    anchors = list(result.scalars().all())

    responses = []
    for a in anchors:
        count_result = await db.execute(
            select(func.count(FactAnchorLink.id)).where(
                FactAnchorLink.fact_anchor_id == a.id
            )
        )
        responses.append(_anchor_to_response(a, count_result.scalar_one()))

    return responses


# ============================================
# GET /{anchor_id} — Detail with links
# ============================================

@router.get("/{anchor_id}", response_model=FactAnchorDetailResponse)
async def get_fact_anchor(
    anchor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a FactAnchor with its theatre links."""
    result = await db.execute(
        select(FactAnchor).where(FactAnchor.id == anchor_id)
    )
    anchor = result.scalars().first()
    if anchor is None:
        raise HTTPException(status_code=404, detail="FactAnchor not found")

    link_result = await db.execute(
        select(FactAnchorLink).where(FactAnchorLink.fact_anchor_id == anchor_id)
    )
    links = list(link_result.scalars().all())

    return FactAnchorDetailResponse(
        id=anchor.id,
        anchor_type=anchor.anchor_type,
        external_id=anchor.external_id,
        external_source=anchor.external_source,
        occurred_at=anchor.occurred_at,
        location_json=anchor.location_json,
        metadata_json=anchor.metadata_json,
        link_count=len(links),
        created_at=anchor.created_at,
        links=[FactAnchorLinkResponse.model_validate(link) for link in links],
    )


# ============================================
# POST /{anchor_id}/link — Link theatre
# ============================================

@router.post("/{anchor_id}/link", status_code=status.HTTP_201_CREATED)
async def link_theatre_to_anchor(
    anchor_id: str,
    body: LinkTheatreRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a theatre to a FactAnchor. Triggers scanner if >= 2 theatres."""
    # Verify anchor exists
    result = await db.execute(
        select(FactAnchor).where(FactAnchor.id == anchor_id)
    )
    if result.scalars().first() is None:
        raise HTTPException(status_code=404, detail="FactAnchor not found")

    svc = FactAnchorService(db)
    link, should_scan = await svc.link_theatre(
        anchor_id=anchor_id,
        theatre_id=body.theatre_id,
        link_type=body.link_type,
        linked_entity_id=body.linked_entity_id,
        linked_entity_type=body.linked_entity_type,
        link_confidence=body.link_confidence,
    )
    await db.commit()

    return {
        "link_id": link.id,
        "should_scan": should_scan,
        "theatre_id": body.theatre_id,
        "anchor_id": anchor_id,
    }


# ============================================
# GET /{anchor_id}/paradoxes — Paradoxes for anchor
# ============================================

@router.get("/{anchor_id}/paradoxes", response_model=list[CrossTheatreParadoxResponse])
async def get_anchor_paradoxes(
    anchor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all cross-theatre paradoxes for a FactAnchor."""
    result = await db.execute(
        select(CrossTheatreParadox).where(
            CrossTheatreParadox.fact_anchor_id == anchor_id
        ).order_by(CrossTheatreParadox.created_at.desc())
    )
    paradoxes = list(result.scalars().all())
    return [CrossTheatreParadoxResponse.model_validate(p) for p in paradoxes]
