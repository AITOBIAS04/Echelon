from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

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
    # Use real database repositories with this request's session
    timeline_repo = TimelineRepository(db_session)
    agent_repo = AgentRepository(db_session)
    osint_service = get_osint_registry()

    # Create butterfly engine for paradox engine
    butterfly_engine = ButterflyEngine(timeline_repo, agent_repo, osint_service)

    # Create a temporary paradox engine instance for this request
    request_engine = ParadoxEngine(timeline_repo, agent_repo, butterfly_engine)

    paradoxes = await request_engine.get_active_paradoxes_async()

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
    # TODO: Implement with database
    raise HTTPException(status_code=404, detail="Paradox not found or already resolved")

@router.get("/timeline/{timeline_id}", response_model=Paradox)
async def get_paradox_for_timeline(
    timeline_id: str,
    db_session: AsyncSession = Depends(get_db),
    engine: Optional[ParadoxEngine] = Depends(get_paradox_engine)
):
    """Get Paradox affecting a specific timeline (if any)."""
    # TODO: Implement with database
    raise HTTPException(status_code=404, detail="No active Paradox in this timeline")

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
    """
    # TODO: Implement with database
    raise HTTPException(status_code=501, detail="Extraction not yet implemented for database mode")

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
    # TODO: Implement with database
    raise HTTPException(status_code=501, detail="Extraction preview not yet implemented for database mode")

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
    # TODO: Implement with database
    raise HTTPException(status_code=501, detail="Abandon timeline not yet implemented for database mode")

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
    # TODO: Implement with database
    raise HTTPException(status_code=501, detail="Debug spawn not yet implemented for database mode")
