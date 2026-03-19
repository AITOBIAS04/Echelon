"""
OracleConsistency API Routes — oracle response tracking and consistency checks.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.oracle_consistency_schemas import (
    RecordOracleResponseRequest,
    OracleResponseResponse,
    ConsistencyCheckResponse,
    DivergenceRecordResponse,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData
from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oracle-consistency", tags=["oracle-consistency"])


# ============================================
# POST /responses — Record oracle response
# ============================================

@router.post("/responses", response_model=OracleResponseResponse, status_code=status.HTTP_201_CREATED)
async def record_oracle_response(
    body: RecordOracleResponseRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an oracle response from a theatre. Idempotent on (theatre, source, event)."""
    monitor = OracleConsistencyMonitor(db)
    response = await monitor.record_response(
        theatre_id=body.theatre_id,
        source=body.source,
        event_id=body.event_id,
        value_json=body.value_json,
        queried_at=body.queried_at,
        is_provisional=body.is_provisional,
    )
    await db.commit()
    return OracleResponseResponse.model_validate(response)


# ============================================
# GET /check/{source}/{event_id} — Check consistency
# ============================================

@router.get("/check/{source}/{event_id}", response_model=ConsistencyCheckResponse)
async def check_consistency(
    source: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check oracle consistency for a specific event across all theatres."""
    monitor = OracleConsistencyMonitor(db)
    result = await monitor.check_consistency(source=source, event_id=event_id)

    return ConsistencyCheckResponse(
        is_consistent=result.is_consistent,
        source=result.source,
        event_id=result.event_id,
        responses=result.responses,
        max_delta=result.max_delta,
        explanation=result.explanation,
    )


# ============================================
# GET /divergences/{source} — Divergence history
# ============================================

@router.get("/divergences/{source}", response_model=list[DivergenceRecordResponse])
async def get_divergence_history(
    source: str,
    window_hours: int = Query(168, ge=1, le=8760, description="Lookback window in hours"),
    db: AsyncSession = Depends(get_db),
):
    """Get recent oracle divergence events for a source."""
    monitor = OracleConsistencyMonitor(db)
    divergences = await monitor.get_divergence_history(
        source=source,
        window_hours=window_hours,
    )

    return [
        DivergenceRecordResponse(
            source=d.source,
            event_id=d.event_id,
            theatre_ids=d.theatre_ids,
            delta=d.delta,
            detected_at=d.detected_at,
        )
        for d in divergences
    ]
