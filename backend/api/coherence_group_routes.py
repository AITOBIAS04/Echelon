"""
CoherenceGroup API Routes — theatre coherence group management.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CoherenceGroup, CoherenceGroupMember
from backend.schemas.coherence_group_schemas import (
    CreateCoherenceGroupRequest,
    AddMemberRequest,
    CoherenceGroupResponse,
    CoherenceGroupDetailResponse,
    CoherenceGroupMemberResponse,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData
from backend.services.coherence_group_service import CoherenceGroupService
from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/coherence-groups", tags=["coherence-groups"])


# ============================================
# POST / — Create group
# ============================================

@router.post("/", response_model=CoherenceGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_coherence_group(
    body: CreateCoherenceGroupRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new coherence group."""
    svc = CoherenceGroupService(db)
    group = await svc.create_group(
        name=body.name,
        group_type=body.group_type,
        policy_json=body.policy_json,
    )
    await db.commit()
    return CoherenceGroupResponse.model_validate(group)


# ============================================
# GET / — List groups
# ============================================

@router.get("/", response_model=list[CoherenceGroupResponse])
async def list_coherence_groups(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all coherence groups."""
    result = await db.execute(
        select(CoherenceGroup)
        .order_by(CoherenceGroup.created_at.desc())
        .limit(limit).offset(offset)
    )
    groups = list(result.scalars().all())
    return [CoherenceGroupResponse.model_validate(g) for g in groups]


# ============================================
# GET /{group_id} — Detail with members
# ============================================

@router.get("/{group_id}", response_model=CoherenceGroupDetailResponse)
async def get_coherence_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a coherence group with its members."""
    result = await db.execute(
        select(CoherenceGroup).where(CoherenceGroup.id == group_id)
    )
    group = result.scalars().first()
    if group is None:
        raise HTTPException(status_code=404, detail="CoherenceGroup not found")

    svc = CoherenceGroupService(db)
    members = await svc.get_group_members(group_id)

    return CoherenceGroupDetailResponse(
        id=group.id,
        name=group.name,
        group_type=group.group_type,
        policy_json=group.policy_json,
        created_at=group.created_at,
        members=[CoherenceGroupMemberResponse.model_validate(m) for m in members],
    )


# ============================================
# POST /{group_id}/members — Add member
# ============================================

@router.post("/{group_id}/members", response_model=CoherenceGroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: str,
    body: AddMemberRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a theatre to a coherence group."""
    result = await db.execute(
        select(CoherenceGroup).where(CoherenceGroup.id == group_id)
    )
    if result.scalars().first() is None:
        raise HTTPException(status_code=404, detail="CoherenceGroup not found")

    svc = CoherenceGroupService(db)
    member = await svc.add_member(
        group_id=group_id,
        theatre_id=body.theatre_id,
        role=body.role,
    )
    await db.commit()
    return CoherenceGroupMemberResponse.model_validate(member)


# ============================================
# POST /{group_id}/scan — Trigger scope overlap scan
# ============================================

@router.post("/{group_id}/scan")
async def scan_coherence_group(
    group_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger scope overlap scan for a coherence group."""
    result = await db.execute(
        select(CoherenceGroup).where(CoherenceGroup.id == group_id)
    )
    if result.scalars().first() is None:
        raise HTTPException(status_code=404, detail="CoherenceGroup not found")

    scanner = CrossTheatreParadoxScanner(db)
    paradoxes = await scanner.scan_coherence_group(group_id)
    await db.commit()

    return {
        "group_id": group_id,
        "paradoxes_detected": len(paradoxes),
        "paradox_ids": [p.id for p in paradoxes],
    }
