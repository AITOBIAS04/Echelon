from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import os

from ..schemas.paradox_schemas import (
    Paradox, ParadoxListResponse,
    ExtractionRequest, ExtractionResult,
    AbandonmentRequest, AbandonmentResult
)
from ..mechanics.paradox_engine import ParadoxEngine
from ..dependencies import get_paradox_engine, get_current_user, get_db
from ..database.repositories.timeline_repository import TimelineRepository
from ..database.repositories.agent_repository import AgentRepository
from ..mechanics.butterfly_engine import ButterflyEngine
from ..core.osint_registry import get_osint_registry

router = APIRouter(prefix="/api/v1/paradox", tags=["Paradox System"])

# =========================================
# PARADOX QUERIES
# =========================================

@router.get("/active", response_model=ParadoxListResponse)
async def get_active_paradoxes(
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine)
):
    """
    Get all active Paradoxes (Containment Breaches).
    
    These should always be shown prominently in the UI.
    """
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # Use real database repositories with this request's session
        timeline_repo = TimelineRepository(db_session)
        agent_repo = AgentRepository(db_session)
        osint_service = get_osint_registry()
        
        # Create butterfly engine for paradox engine
        butterfly_engine = ButterflyEngine(timeline_repo, agent_repo, osint_service)
        
        # Create a temporary paradox engine instance for this request
        request_engine = ParadoxEngine(timeline_repo, agent_repo, butterfly_engine)
        
        paradoxes = await request_engine.get_active_paradoxes_async()
    else:
        # Use the singleton engine (mocks)
        paradoxes = engine.get_active_paradoxes()
    
    return ParadoxListResponse(
        paradoxes=paradoxes,
        total_active=len(paradoxes)
    )

@router.get("/{paradox_id}", response_model=Paradox)
async def get_paradox(
    paradox_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine)
):
    """Get details of a specific Paradox."""
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=404, detail="Paradox not found or already resolved")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    paradox = engine.get_paradox(paradox_id)
    if not paradox:
        raise HTTPException(status_code=404, detail="Paradox not found or already resolved")
    return paradox

@router.get("/timeline/{timeline_id}", response_model=Paradox)
async def get_paradox_for_timeline(
    timeline_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine)
):
    """Get Paradox affecting a specific timeline (if any)."""
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=404, detail="No active Paradox in this timeline")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    paradox = engine.get_paradox_for_timeline(timeline_id)
    if not paradox:
        raise HTTPException(status_code=404, detail="No active Paradox in this timeline")
    return paradox

# =========================================
# EXTRACTION
# =========================================

@router.post("/{paradox_id}/extract", response_model=ExtractionResult)
async def attempt_extraction(
    paradox_id: str,
    request: ExtractionRequest,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine),
    user = Depends(get_current_user)
):
    """
    Attempt to extract a Paradox using an agent.
    
    Requirements:
    - User must own the agent
    - Agent must have enough sanity
    - Destination must be a connected timeline
    - User must have funds for extraction cost
    
    Risks:
    - Agent may die during extraction
    - If agent dies, Paradox stays in place
    
    Costs:
    - USDC: Varies by severity
    - $ECHELON: Varies by severity
    - Agent Sanity: Varies by severity
    """
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=501, detail="Extraction not yet implemented for database mode")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    # Verify user owns the agent
    # (Implementation depends on your auth system)
    
    result = engine.attempt_extraction(
        paradox_id=paradox_id,
        agent_id=request.agent_id,
        destination_timeline_id=request.destination_timeline_id,
        user_id=user.id
    )
    
    return result

@router.get("/{paradox_id}/extraction-preview")
async def preview_extraction(
    paradox_id: str,
    agent_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine),
    user = Depends(get_current_user)
):
    """
    Preview extraction without executing.
    
    Shows costs and death risk for the selected agent.
    """
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=501, detail="Extraction preview not yet implemented for database mode")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    paradox = engine.get_paradox(paradox_id)
    if not paradox:
        raise HTTPException(status_code=404, detail="Paradox not found")
    
    agent = engine.agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    death_risk = engine._calculate_death_risk(agent, paradox)
    
    return {
        "paradox_id": paradox_id,
        "agent_id": agent_id,
        "agent_name": agent.name,
        "agent_sanity": agent.sanity,
        "costs": {
            "usdc": paradox.extraction_cost_usdc,
            "echelon": paradox.extraction_cost_echelon,
            "sanity": paradox.carrier_sanity_cost
        },
        "death_risk_percent": round(death_risk * 100, 1),
        "sanity_after": max(0, agent.sanity - paradox.carrier_sanity_cost),
        "can_extract": agent.sanity >= paradox.carrier_sanity_cost
    }

# =========================================
# ABANDONMENT
# =========================================

@router.post("/{paradox_id}/abandon", response_model=AbandonmentResult)
async def abandon_timeline(
    paradox_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine),
    user = Depends(get_current_user)
):
    """
    Abandon a timeline affected by a Paradox.
    
    This burns all your holdings in the timeline immediately.
    You get back a portion of the USDC based on current price.
    
    Use this to cut losses before detonation.
    """
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=501, detail="Abandon timeline not yet implemented for database mode")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    paradox = engine.get_paradox(paradox_id)
    if not paradox:
        raise HTTPException(status_code=404, detail="Paradox not found")
    
    # Get user's holdings in this timeline
    holdings = engine.timeline_repo.get_user_holdings(
        timeline_id=paradox.timeline_id,
        user_id=user.id
    )
    
    if not holdings or holdings.shards == 0:
        raise HTTPException(status_code=400, detail="No holdings to abandon")
    
    # Calculate return (current price * shards)
    timeline = engine.timeline_repo.get(paradox.timeline_id)
    price = timeline.price_yes if holdings.side == "YES" else timeline.price_no
    usdc_returned = holdings.shards * price
    
    # Execute abandonment
    engine.timeline_repo.burn_user_holdings(
        timeline_id=paradox.timeline_id,
        user_id=user.id
    )
    
    # Credit user
    engine.payment_service.credit(user.id, usdc_returned)
    
    return AbandonmentResult(
        shards_burned=holdings.shards,
        usdc_returned=usdc_returned,
        message=f"Abandoned {holdings.shards} shards. Returned ${usdc_returned:.2f} USDC."
    )

# =========================================
# ADMIN / DEBUG
# =========================================

@router.post("/debug/spawn", include_in_schema=False)
async def debug_spawn_paradox(
    timeline_id: str,
    logic_gap: float = 0.5,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine)
):
    """DEBUG: Manually spawn a paradox for testing."""
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if not USE_MOCKS:
        # TODO: Implement with database
        raise HTTPException(status_code=501, detail="Debug spawn not yet implemented for database mode")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not available")
    
    paradox = engine._spawn_paradox(timeline_id, logic_gap)
    return paradox

