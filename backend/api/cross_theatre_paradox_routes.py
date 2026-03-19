"""
CrossTheatreParadox API Routes — network-level paradox management.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    CrossTheatreParadox,
    CrossTheatreParadoxStatus,
    CrossTheatreParadoxSeverity,
    CrossTheatreParadoxType,
)
from backend.schemas.cross_theatre_paradox_schemas import (
    CrossTheatreParadoxResponse,
    CrossTheatreParadoxListResponse,
    ResolveParadoxRequest,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cross-theatre-paradoxes", tags=["cross-theatre-paradoxes"])

# Valid status transitions
VALID_TRANSITIONS = {
    CrossTheatreParadoxStatus.OPEN: {
        CrossTheatreParadoxStatus.ACKNOWLEDGED,
        CrossTheatreParadoxStatus.RESOLVED,
        CrossTheatreParadoxStatus.DISMISSED,
    },
    CrossTheatreParadoxStatus.ACKNOWLEDGED: {
        CrossTheatreParadoxStatus.RESOLVED,
        CrossTheatreParadoxStatus.DISMISSED,
    },
}


# ============================================
# GET / — List paradoxes
# ============================================

@router.get("/", response_model=CrossTheatreParadoxListResponse)
async def list_paradoxes(
    severity: Optional[str] = Query(None),
    resolution_status: Optional[str] = Query(None),
    theatre_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List cross-theatre paradoxes with filters."""
    query = select(CrossTheatreParadox).order_by(CrossTheatreParadox.created_at.desc())

    if severity:
        query = query.where(CrossTheatreParadox.severity == severity)
    if resolution_status:
        query = query.where(CrossTheatreParadox.resolution_status == resolution_status)
    if theatre_id:
        query = query.where(
            or_(
                CrossTheatreParadox.theatre_a_id == theatre_id,
                CrossTheatreParadox.theatre_b_id == theatre_id,
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(query.limit(limit).offset(offset))
    paradoxes = list(result.scalars().all())

    return CrossTheatreParadoxListResponse(
        paradoxes=[CrossTheatreParadoxResponse.model_validate(p) for p in paradoxes],
        total=total,
    )


# ============================================
# GET /{paradox_id} — Detail
# ============================================

@router.get("/{paradox_id}", response_model=CrossTheatreParadoxResponse)
async def get_paradox(
    paradox_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a cross-theatre paradox by ID."""
    result = await db.execute(
        select(CrossTheatreParadox).where(CrossTheatreParadox.id == paradox_id)
    )
    paradox = result.scalars().first()
    if paradox is None:
        raise HTTPException(status_code=404, detail="CrossTheatreParadox not found")
    return CrossTheatreParadoxResponse.model_validate(paradox)


# ============================================
# POST /{paradox_id}/acknowledge — OPEN → ACKNOWLEDGED
# ============================================

@router.post("/{paradox_id}/acknowledge", response_model=CrossTheatreParadoxResponse)
async def acknowledge_paradox(
    paradox_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transition a paradox from OPEN to ACKNOWLEDGED."""
    paradox = await _get_and_validate_transition(
        db, paradox_id, CrossTheatreParadoxStatus.ACKNOWLEDGED,
    )
    paradox.resolution_status = CrossTheatreParadoxStatus.ACKNOWLEDGED
    await db.commit()

    logger.info("Paradox %s acknowledged", paradox_id)
    return CrossTheatreParadoxResponse.model_validate(paradox)


# ============================================
# POST /{paradox_id}/resolve — → RESOLVED
# ============================================

@router.post("/{paradox_id}/resolve", response_model=CrossTheatreParadoxResponse)
async def resolve_paradox(
    paradox_id: str,
    body: ResolveParadoxRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a paradox with a required note."""
    paradox = await _get_and_validate_transition(
        db, paradox_id, CrossTheatreParadoxStatus.RESOLVED,
    )
    paradox.resolution_status = CrossTheatreParadoxStatus.RESOLVED
    paradox.resolved_at = datetime.now(timezone.utc)
    paradox.evidence_json = {
        **paradox.evidence_json,
        "resolution_note": body.note,
    }
    await db.commit()

    logger.info("Paradox %s resolved: %s", paradox_id, body.note[:100])
    return CrossTheatreParadoxResponse.model_validate(paradox)


# ============================================
# POST /{paradox_id}/dismiss — → DISMISSED
# ============================================

@router.post("/{paradox_id}/dismiss", response_model=CrossTheatreParadoxResponse)
async def dismiss_paradox(
    paradox_id: str,
    body: ResolveParadoxRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a paradox with a required note."""
    paradox = await _get_and_validate_transition(
        db, paradox_id, CrossTheatreParadoxStatus.DISMISSED,
    )
    paradox.resolution_status = CrossTheatreParadoxStatus.DISMISSED
    paradox.resolved_at = datetime.now(timezone.utc)
    paradox.evidence_json = {
        **paradox.evidence_json,
        "dismissal_note": body.note,
    }
    await db.commit()

    logger.info("Paradox %s dismissed: %s", paradox_id, body.note[:100])
    return CrossTheatreParadoxResponse.model_validate(paradox)


# ============================================
# HELPERS
# ============================================

async def _get_and_validate_transition(
    db: AsyncSession,
    paradox_id: str,
    target_status: CrossTheatreParadoxStatus,
) -> CrossTheatreParadox:
    """Load paradox and validate state transition."""
    result = await db.execute(
        select(CrossTheatreParadox).where(CrossTheatreParadox.id == paradox_id)
    )
    paradox = result.scalars().first()
    if paradox is None:
        raise HTTPException(status_code=404, detail="CrossTheatreParadox not found")

    allowed = VALID_TRANSITIONS.get(paradox.resolution_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition from {paradox.resolution_status.value} to {target_status.value}",
        )

    return paradox
