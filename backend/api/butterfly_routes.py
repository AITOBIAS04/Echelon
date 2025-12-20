from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.butterfly_schemas import (
    WingFlap, WingFlapFeedRequest, WingFlapFeedResponse,
    TimelineHealth, TimelineHealthRequest, TimelineHealthResponse,
    GravityBreakdown, Ripple, RippleListResponse
)
from ..mechanics.butterfly_engine import ButterflyEngine
from ..dependencies import get_butterfly_engine, get_current_user, get_db
from ..database.repositories.timeline_repository import TimelineRepository
from ..database.repositories.agent_repository import AgentRepository
from ..core.osint_registry import get_osint_registry

router = APIRouter(prefix="/api/v1/butterfly", tags=["Butterfly Engine"])

# =========================================
# WING FLAPS (Causality Feed)
# =========================================

@router.get("/wing-flaps", response_model=WingFlapFeedResponse)
async def get_wing_flaps(
    timeline_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    min_stability_delta: float = Query(default=0, ge=0),
    min_volume_usd: float = Query(default=0, ge=0),
    flap_types: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get the Wing Flap feed (causality events).
    
    Filters:
    - timeline_id: Only flaps for this timeline
    - agent_id: Only flaps by this agent
    - min_stability_delta: Only flaps with |delta| >= this value
    - min_volume_usd: Only flaps with volume >= this value
    - flap_types: Only these types (TRADE, SHIELD, SABOTAGE, etc.)
    """
    # Create repositories with the request's database session
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # Use real database repositories with this request's session
        # Note: db_session is already an AsyncSession from the dependency
        timeline_repo = TimelineRepository(db_session)
        agent_repo = AgentRepository(db_session)
        osint_service = get_osint_registry()
        
        # Create a temporary engine instance for this request
        request_engine = ButterflyEngine(timeline_repo, agent_repo, osint_service)
        
        flaps = await request_engine.get_flaps_async(
            timeline_id=timeline_id,
            agent_id=agent_id,
            min_delta=min_stability_delta,
            min_volume=min_volume_usd,
            flap_types=flap_types,
            limit=limit,
            offset=offset
        )
        
        # Use async count if available, otherwise use sync
        if hasattr(request_engine, 'count_flaps_async'):
            total = await request_engine.count_flaps_async(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types
            )
        else:
            total = request_engine.count_flaps(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types
            )
    else:
        # Use the singleton engine (mocks)
        if hasattr(engine, 'get_flaps_async'):
            flaps = await engine.get_flaps_async(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types,
                limit=limit,
                offset=offset
            )
        else:
            flaps = engine.get_flaps(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types,
                limit=limit,
                offset=offset
            )
        
        if hasattr(engine, 'count_flaps_async'):
            total = await engine.count_flaps_async(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types
            )
        else:
            total = engine.count_flaps(
                timeline_id=timeline_id,
                agent_id=agent_id,
                min_delta=min_stability_delta,
                min_volume=min_volume_usd,
                flap_types=flap_types
            )
    
    return WingFlapFeedResponse(
        flaps=flaps,
        total_count=total,
        has_more=(offset + len(flaps)) < total
    )

@router.get("/wing-flaps/recent", response_model=List[WingFlap])
async def get_recent_flaps(
    hours: int = Query(default=1, le=24),
    limit: int = Query(default=20, le=100),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get the most recent high-impact wing flaps.
    
    Sorted by |stability_delta| descending.
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        return []
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    since = datetime.now() - timedelta(hours=hours)
    return engine.get_recent_high_impact_flaps(since=since, limit=limit)

# =========================================
# TIMELINE HEALTH
# =========================================

@router.get("/timelines/health", response_model=TimelineHealthResponse)
async def get_timeline_health(
    sort_by: str = Query(default="gravity_score", regex="^(gravity_score|stability|volume|decay)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    min_gravity: float = Query(default=0, ge=0),
    include_paradox_only: bool = Query(default=False),
    limit: int = Query(default=20, le=100),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get health status of timelines.
    
    Default: Top 20 by Gravity score (most important).
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # Use real database repositories with this request's session
        timeline_repo = TimelineRepository(db_session)
        agent_repo = AgentRepository(db_session)
        osint_service = get_osint_registry()
        
        # Create a temporary engine instance for this request
        request_engine = ButterflyEngine(timeline_repo, agent_repo, osint_service)
        
        timelines = await request_engine.get_timeline_health_async(
            sort_by=sort_by,
            sort_order=sort_order,
            min_gravity=min_gravity,
            paradox_only=include_paradox_only,
            limit=limit
        )
        
        total = await request_engine.count_timelines_async(
            min_gravity=min_gravity,
            paradox_only=include_paradox_only
        )
    else:
        # Use the singleton engine (mocks)
        timelines = engine.get_timeline_health(
            sort_by=sort_by,
            sort_order=sort_order,
            min_gravity=min_gravity,
            paradox_only=include_paradox_only,
            limit=limit
        )
        
        total = engine.count_timelines(min_gravity=min_gravity, paradox_only=include_paradox_only)
    
    return TimelineHealthResponse(
        timelines=timelines,
        total_count=total
    )

@router.get("/timelines/{timeline_id}/health", response_model=TimelineHealth)
async def get_single_timeline_health(
    timeline_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """Get detailed health for a single timeline."""
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    health = engine.get_timeline_health_by_id(timeline_id)
    if not health:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return health

# =========================================
# GRAVITY
# =========================================

@router.get("/timelines/{timeline_id}/gravity", response_model=GravityBreakdown)
async def get_gravity_breakdown(
    timeline_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get detailed Gravity calculation for a timeline.
    
    Shows how each factor contributes to the total score.
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    breakdown = engine.calculate_gravity(timeline_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return breakdown

@router.get("/gravity/trending", response_model=List[GravityBreakdown])
async def get_trending_timelines(
    limit: int = Query(default=10, le=50),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get timelines with highest gravity (trending).
    
    These are the most important timelines to show in SIGINT.
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        return []
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    return engine.get_trending_timelines(limit=limit)

# =========================================
# RIPPLES (Forks)
# =========================================

@router.get("/ripples", response_model=RippleListResponse)
async def get_ripples(
    parent_timeline_id: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=20, le=100),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get recent Ripples (forks spawned from Wing Flaps).
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        return RippleListResponse(ripples=[], total_today=0, total_all_time=0)
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    since = datetime.now() - timedelta(hours=hours)
    ripples = engine.get_ripples(
        parent_id=parent_timeline_id,
        since=since,
        limit=limit
    )
    
    return RippleListResponse(
        ripples=ripples,
        total_today=engine.count_ripples_since(datetime.now().replace(hour=0, minute=0)),
        total_all_time=engine.count_all_ripples()
    )

@router.get("/ripples/{timeline_id}/tree")
async def get_fork_tree(
    timeline_id: str,
    depth: int = Query(default=3, le=10),
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ButterflyEngine] = Depends(get_butterfly_engine)
):
    """
    Get the fork tree for a timeline.
    
    Shows parent, siblings, and children up to specified depth.
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        return {}
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    return engine.get_fork_tree(timeline_id, depth=depth)

