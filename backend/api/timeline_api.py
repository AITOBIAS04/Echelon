"""
Timeline API Endpoints
======================

REST API for the Divergence Engine and Timeline Fork Management.

Endpoints:
- GET /timelines - List all timelines with health metrics
- GET /timelines/{fork_id} - Get specific timeline details
- GET /timelines/{fork_id}/health - Get timeline health/stability
- POST /timelines/{fork_id}/osint-contradiction - Apply OSINT contradiction
- GET /timelines/{fork_id}/ripples - Get recent ripple effects
- POST /timelines - Create a new fork
- GET /agents/{agent_id}/founder-stats - Get agent's founder statistics

Author: Echelon Protocol
Version: 1.0.0
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/timelines",
    tags=["timelines", "divergence"],
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class TimelineHealthResponse(BaseModel):
    """Timeline health metrics."""
    
    id: str
    state: str
    stability_score: float = Field(..., ge=0, le=1)
    divergence_score: float = Field(..., ge=0, le=1)
    osint_contradiction: float = Field(..., ge=0, le=1)
    narrative_gravity: float = Field(..., ge=0, le=1)
    total_liquidity: float
    active_agents: int
    founder: Optional[str] = None
    child_forks: int
    age_hours: float


class TimelineSummary(BaseModel):
    """Summary of a timeline for list views."""
    
    fork_id: str
    premise: str
    status: str
    stability_score: float
    divergence_score: float
    active_agents: int
    total_volume: float
    created_at: datetime
    expires_at: Optional[datetime] = None


class TimelineDetailResponse(BaseModel):
    """Full timeline details."""
    
    fork_id: str
    fork_type: str
    status: str
    
    # Fork point info
    premise: str
    source_market_id: str
    source_platform: str
    fork_timestamp: datetime
    
    # Divergence metrics
    stability_score: float
    divergence_score: float
    osint_contradiction_score: float
    narrative_gravity: float
    agent_confidence: float
    
    # Activity
    active_agent_ids: List[str]
    total_volume: float
    unique_traders: int
    
    # Relationships
    parent_fork_id: Optional[str] = None
    child_fork_ids: List[str] = []
    founder_agent_id: Optional[str] = None
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None


class CreateForkRequest(BaseModel):
    """Request to create a new timeline fork."""
    
    source_market_id: str = Field(..., description="Market ID to fork from")
    source_platform: str = Field(..., description="polymarket, kalshi, or echelon_internal")
    premise: str = Field(..., description="What-if scenario description")
    duration_hours: int = Field(48, ge=1, le=168, description="Fork duration (1-168 hours)")
    outcomes: Optional[List[str]] = Field(None, description="Market outcomes (default: Yes/No)")


class CreateForkResponse(BaseModel):
    """Response after creating a fork."""
    
    fork_id: str
    status: str
    premise: str
    stability_score: float
    expires_at: datetime
    message: str


class OSINTContradictionRequest(BaseModel):
    """Request to apply OSINT contradiction to a timeline."""
    
    contradiction_score: float = Field(..., ge=0, le=1, description="Strength of contradiction (0-1)")
    reason: str = Field(..., description="Why this contradicts the timeline")
    source: Optional[str] = Field(None, description="OSINT source that detected contradiction")


class OSINTContradictionResponse(BaseModel):
    """Response after applying OSINT contradiction."""
    
    fork_id: str
    previous_stability: float
    new_stability: float
    previous_state: str
    new_state: str
    osint_contradiction_score: float
    message: str


class RippleEffectSummary(BaseModel):
    """Summary of a ripple effect from an agent action."""
    
    timestamp: datetime
    agent_id: str
    action_type: str
    market_id: str
    size: float
    
    stability_change: float
    divergence_change: float
    affected_markets: List[Dict[str, Any]]
    spawned_fork: bool
    new_fork_id: Optional[str] = None


class AgentFounderStats(BaseModel):
    """Founder statistics for an agent."""
    
    agent_id: str
    timelines_founded: int
    timeline_ids: List[str]
    total_royalties: float
    royalty_rate: float


class NarrativeGravityResponse(BaseModel):
    """Current narrative gravity state."""
    
    high_gravity_topics: List[Dict[str, float]]
    total_topics_tracked: int


# =============================================================================
# DEPENDENCY: Get divergence integration
# =============================================================================

# Global instance (will be set by main.py on startup)
_divergence_integration = None
_fork_manager = None
_divergence_engine = None


def get_divergence_integration():
    """Get the divergence integration instance."""
    if _divergence_integration is None:
        raise HTTPException(
            status_code=503,
            detail="Divergence engine not initialised. Server starting up."
        )
    return _divergence_integration


def get_fork_manager():
    """Get the fork manager instance."""
    if _fork_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Fork manager not initialised. Server starting up."
        )
    return _fork_manager


def get_divergence_engine():
    """Get the divergence engine instance."""
    if _divergence_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Divergence engine not initialised. Server starting up."
        )
    return _divergence_engine


def init_timeline_api(fork_manager, divergence_engine, divergence_integration):
    """
    Initialise the timeline API with required dependencies.
    
    Call this from main.py after creating the managers.
    """
    global _fork_manager, _divergence_engine, _divergence_integration
    _fork_manager = fork_manager
    _divergence_engine = divergence_engine
    _divergence_integration = divergence_integration
    logger.info("✅ Timeline API initialised with divergence engine")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[TimelineSummary])
async def list_timelines(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    min_stability: Optional[float] = Query(None, ge=0, le=1, description="Minimum stability"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all timeline forks with summary metrics.
    
    Use for dashboard displays and timeline selection.
    """
    fork_manager = get_fork_manager()
    
    forks = list(fork_manager._forks.values())
    
    # Apply filters
    if status_filter:
        forks = [f for f in forks if f.status.value == status_filter]
    
    if min_stability is not None:
        forks = [f for f in forks if f.stability_score >= min_stability]
    
    # Sort by created_at descending (newest first)
    forks.sort(key=lambda f: f.created_at, reverse=True)
    
    # Paginate
    forks = forks[offset:offset + limit]
    
    return [
        TimelineSummary(
            fork_id=f.fork_id,
            premise=f.fork_point.premise,
            status=f.status.value,
            stability_score=f.stability_score,
            divergence_score=f.divergence_score,
            active_agents=len(f.active_agent_ids),
            total_volume=float(f.total_volume),
            created_at=f.created_at,
            expires_at=f.expires_at,
        )
        for f in forks
    ]


@router.get("/{fork_id}", response_model=TimelineDetailResponse)
async def get_timeline(fork_id: str):
    """
    Get detailed information about a specific timeline.
    """
    fork_manager = get_fork_manager()
    
    fork = fork_manager._forks.get(fork_id)
    if not fork:
        raise HTTPException(status_code=404, detail=f"Timeline {fork_id} not found")
    
    return TimelineDetailResponse(
        fork_id=fork.fork_id,
        fork_type=fork.fork_type.value,
        status=fork.status.value,
        premise=fork.fork_point.premise,
        source_market_id=fork.fork_point.source_market_id,
        source_platform=fork.fork_point.source_platform,
        fork_timestamp=fork.fork_point.timestamp,
        stability_score=fork.stability_score,
        divergence_score=fork.divergence_score,
        osint_contradiction_score=fork.osint_contradiction_score,
        narrative_gravity=fork.narrative_gravity,
        agent_confidence=fork.agent_confidence,
        active_agent_ids=fork.active_agent_ids,
        total_volume=float(fork.total_volume),
        unique_traders=fork.unique_traders,
        parent_fork_id=fork.parent_fork_id,
        child_fork_ids=fork.child_fork_ids,
        founder_agent_id=fork.founder_agent_id,
        created_at=fork.created_at,
        expires_at=fork.expires_at,
        last_activity_at=fork.last_activity_at,
    )


@router.get("/{fork_id}/health", response_model=TimelineHealthResponse)
async def get_timeline_health(fork_id: str):
    """
    Get real-time health metrics for a timeline.
    
    Use for monitoring timeline stability and risk of collapse.
    """
    integration = get_divergence_integration()
    
    try:
        health = integration.get_timeline_health(fork_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Timeline {fork_id} not found: {e}")
    
    if "error" in health:
        raise HTTPException(status_code=404, detail=health["error"])
    
    return TimelineHealthResponse(**health)


@router.post("/", response_model=CreateForkResponse)
async def create_fork(request: CreateForkRequest):
    """
    Create a new timeline fork.
    
    This creates a counterfactual "what-if" scenario from a real market.
    """
    fork_manager = get_fork_manager()
    integration = get_divergence_integration()
    
    try:
        fork = await fork_manager.create_global_fork(
            source_market_id=request.source_market_id,
            source_platform=request.source_platform,
            premise=request.premise,
            duration_hours=request.duration_hours,
            outcomes=request.outcomes,
        )
        
        # Sync to divergence engine
        integration.sync_fork_to_divergence(fork)
        
        logger.info(f"🔀 Created fork {fork.fork_id}: {request.premise}")
        
        return CreateForkResponse(
            fork_id=fork.fork_id,
            status=fork.status.value,
            premise=fork.fork_point.premise,
            stability_score=fork.stability_score,
            expires_at=fork.expires_at,
            message=f"Timeline fork created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create fork: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create fork: {e}")


@router.post("/{fork_id}/osint-contradiction", response_model=OSINTContradictionResponse)
async def apply_osint_contradiction(fork_id: str, request: OSINTContradictionRequest):
    """
    Apply an OSINT contradiction to a timeline.
    
    This simulates real-world data contradicting the counterfactual premise,
    which destabilises the timeline.
    """
    fork_manager = get_fork_manager()
    integration = get_divergence_integration()
    
    fork = fork_manager._forks.get(fork_id)
    if not fork:
        raise HTTPException(status_code=404, detail=f"Timeline {fork_id} not found")
    
    previous_stability = fork.stability_score
    previous_state = fork.status.value
    
    try:
        integration.apply_osint_contradiction(
            fork_id=fork_id,
            contradiction_score=request.contradiction_score,
            reason=request.reason,
        )
        
        # Refresh fork data
        fork = fork_manager._forks.get(fork_id)
        
        logger.info(
            f"📡 OSINT contradiction on {fork_id}: {request.reason} "
            f"(score: {request.contradiction_score:.2f}, "
            f"stability: {previous_stability:.2%} → {fork.stability_score:.2%})"
        )
        
        return OSINTContradictionResponse(
            fork_id=fork_id,
            previous_stability=previous_stability,
            new_stability=fork.stability_score,
            previous_state=previous_state,
            new_state=fork.status.value,
            osint_contradiction_score=fork.osint_contradiction_score,
            message=f"OSINT contradiction applied: {request.reason}",
        )
        
    except Exception as e:
        logger.error(f"Failed to apply OSINT contradiction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply contradiction: {e}")


@router.get("/gravity/topics", response_model=NarrativeGravityResponse)
async def get_narrative_gravity():
    """
    Get current narrative gravity state.
    
    Shows which topics agents are betting heavily on,
    affecting OSINT sensitivity.
    """
    engine = get_divergence_engine()
    
    high_gravity = engine.gravity_engine.get_high_gravity_topics(threshold=0.1)
    
    return NarrativeGravityResponse(
        high_gravity_topics=[
            {"topic": topic, "gravity": gravity}
            for topic, gravity in high_gravity
        ],
        total_topics_tracked=len(engine.gravity_engine.gravity_map),
    )


@router.post("/{fork_id}/tick")
async def trigger_tick(fork_id: str):
    """
    Manually trigger a tick for a specific timeline.
    
    Useful for testing. In production, ticks are automatic.
    """
    integration = get_divergence_integration()
    fork_manager = get_fork_manager()
    
    fork = fork_manager._forks.get(fork_id)
    if not fork:
        raise HTTPException(status_code=404, detail=f"Timeline {fork_id} not found")
    
    previous_stability = fork.stability_score
    
    integration.tick()
    
    fork = fork_manager._forks.get(fork_id)
    
    return {
        "fork_id": fork_id,
        "previous_stability": previous_stability,
        "new_stability": fork.stability_score,
        "status": fork.status.value,
        "message": "Tick processed",
    }


@router.get("/stats/summary")
async def get_timeline_stats():
    """
    Get aggregate statistics across all timelines.
    """
    fork_manager = get_fork_manager()
    engine = get_divergence_engine()
    
    forks = list(fork_manager._forks.values())
    
    if not forks:
        return {
            "total_timelines": 0,
            "by_status": {},
            "average_stability": 0,
            "total_volume": 0,
            "total_active_agents": 0,
            "high_gravity_topics": [],
        }
    
    # Count by status
    status_counts = {}
    for fork in forks:
        status = fork.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate averages
    avg_stability = sum(f.stability_score for f in forks) / len(forks)
    total_volume = sum(float(f.total_volume) for f in forks)
    
    # Unique active agents across all timelines
    all_agents = set()
    for fork in forks:
        all_agents.update(fork.active_agent_ids)
    
    # High gravity topics
    high_gravity = engine.gravity_engine.get_high_gravity_topics(threshold=0.2)
    
    return {
        "total_timelines": len(forks),
        "by_status": status_counts,
        "average_stability": avg_stability,
        "total_volume": total_volume,
        "total_active_agents": len(all_agents),
        "high_gravity_topics": [
            {"topic": t, "gravity": g} for t, g in high_gravity
        ],
    }


# =============================================================================
# AGENT FOUNDER ENDPOINTS
# =============================================================================

@router.get("/agents/{agent_id}/founder-stats", response_model=AgentFounderStats)
async def get_agent_founder_stats(agent_id: str):
    """
    Get founder statistics for an agent.
    
    Shows how many timelines they've created via divergence
    and their accumulated royalties.
    """
    engine = get_divergence_engine()
    
    stats = engine.founder_tracker.get_founder_stats(agent_id)
    
    return AgentFounderStats(**stats)


# =============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES (Future)
# =============================================================================

# @router.websocket("/ws/{fork_id}")
# async def timeline_websocket(websocket: WebSocket, fork_id: str):
#     """
#     WebSocket for real-time timeline updates.
#     
#     Streams:
#     - Stability changes
#     - Agent actions and ripples
#     - OSINT contradictions
#     - Fork spawns
#     """
#     await websocket.accept()
#     # Implementation pending



