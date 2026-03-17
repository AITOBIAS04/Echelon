"""
OSINT Signals API Endpoints — Cycle 025
=========================================

REST API for OSINT (Open Source Intelligence) signals feed.

Endpoints:
- GET /api/v1/osint/signals - Paginated signals query
- GET /api/v1/osint/health - Feed health status
- GET /api/v1/osint/signals/summary - Signal aggregates
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..database.models import OsintSignal, Investigation
from ..schemas.osint_schemas import (
    PaginatedSignalsResponse,
    OsintHealthResponse,
    SignalSummaryResponse,
)
from ..osint.models.registry import RegistryLoader

router = APIRouter(prefix="/api/v1/osint", tags=["OSINT"])

REGISTRY_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "osint", "sources.json"
)


@router.get("/signals", response_model=PaginatedSignalsResponse)
async def get_signals(
    source_group: Optional[str] = Query(None, description="Filter by source group"),
    investigation_id: Optional[str] = Query(None, description="Filter by investigation"),
    since: Optional[datetime] = Query(None, description="Only signals after this timestamp"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Paginated OSINT signals from the osint_signals table."""
    query = select(OsintSignal).order_by(OsintSignal.collected_at.desc())
    if source_group:
        query = query.where(OsintSignal.source_group == source_group)
    if investigation_id:
        query = query.where(OsintSignal.investigation_id == investigation_id)
    if since:
        query = query.where(OsintSignal.collected_at >= since)
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return PaginatedSignalsResponse(
        signals=result.scalars().all(),
        limit=limit,
        offset=offset,
    )


@router.get("/health", response_model=OsintHealthResponse)
async def get_osint_health(session: AsyncSession = Depends(get_db)):
    """Feed health: online/total feeds, signal latency, escalation queue."""
    # Count total registered sources
    feeds_total = 0
    if os.path.exists(REGISTRY_JSON_PATH):
        loader = RegistryLoader(registry_path=REGISTRY_JSON_PATH)
        feeds_total = len(loader.sources)

    # Feeds online: distinct source_ids with a signal in last hour
    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent_sources = await session.execute(
        select(func.count(func.distinct(OsintSignal.source_id)))
        .where(OsintSignal.collected_at >= cutoff)
    )
    feeds_online = recent_sources.scalar() or 0

    # Signal latency from most recent signal
    latest = await session.execute(
        select(OsintSignal.collected_at)
        .order_by(OsintSignal.collected_at.desc())
        .limit(1)
    )
    row = latest.scalar_one_or_none()
    latency_sec = round((datetime.utcnow() - row).total_seconds()) if row else None

    # Escalation queue: ACTIVE investigations as proxy
    escalation_count = await session.execute(
        select(func.count()).select_from(Investigation)
        .where(Investigation.status == "ACTIVE")
    )

    return OsintHealthResponse(
        feeds_online=feeds_online,
        feeds_total=feeds_total,
        signal_latency_sec=latency_sec,
        escalation_queue_depth=escalation_count.scalar() or 0,
        replay_workers_active=0,
    )


@router.get("/signals/summary", response_model=SignalSummaryResponse)
async def get_signals_summary(session: AsyncSession = Depends(get_db)):
    """Signal aggregates for the canvas toolbar."""
    # Total signals
    total = await session.execute(
        select(func.count()).select_from(OsintSignal)
    )

    # Group by source_group
    by_group = await session.execute(
        select(OsintSignal.source_group, func.count())
        .group_by(OsintSignal.source_group)
    )

    # Counter-signals from counter_signal resolution_role sources
    counter_count_val = 0
    if os.path.exists(REGISTRY_JSON_PATH):
        loader = RegistryLoader(registry_path=REGISTRY_JSON_PATH)
        counter_sources = {
            sid for sid, s in loader.sources.items()
            if s.resolution_role == "counter_signal"
        }
        if counter_sources:
            counter_result = await session.execute(
                select(func.count()).select_from(OsintSignal)
                .where(OsintSignal.source_id.in_(counter_sources))
            )
            counter_count_val = counter_result.scalar() or 0

    # Certificate candidates: investigations in CERTIFICATE_READY
    cert_candidates = await session.execute(
        select(func.count()).select_from(Investigation)
        .where(Investigation.status == "CERTIFICATE_READY")
    )

    return SignalSummaryResponse(
        total_signals=total.scalar() or 0,
        by_source_group=dict(by_group.all()),
        counter_signals=counter_count_val,
        certificate_candidates=cert_candidates.scalar() or 0,
        convergence_cells=0,  # Populated once convergence scorer runs
    )
