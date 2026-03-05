"""
Agents API Endpoints
====================

REST API for agent roster and details.

Endpoints:
- GET /api/v1/agents - List all agents
- GET /api/v1/agents/{id} - Get agent details
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..database.repositories.agent_repository import AgentRepository
from ..dependencies import get_db

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


class AgentResponse(BaseModel):
    """Agent response model — full roster fields."""
    id: str
    name: str
    archetype: str
    tier: int = 1
    level: int = 1

    # Status
    sanity: int = 100
    max_sanity: int = 100
    is_alive: bool = True
    death_cause: Optional[str] = None

    # Owner
    owner_id: str

    # Performance
    total_pnl_usd: float = 0.0
    win_rate: float = 0.0
    trades_count: int = 0

    # Genome
    genome: dict = {}
    parent_agent_ids: List[str] = []

    # Timestamps
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    """List of agents response."""
    agents: List[AgentResponse]
    total: int


def _agent_to_response(agent) -> AgentResponse:
    """Convert ORM Agent to response model."""
    return AgentResponse(
        id=agent.id,
        name=getattr(agent, 'name', agent.id),
        archetype=getattr(agent, 'archetype', 'DEGEN'),
        tier=getattr(agent, 'tier', 1),
        level=getattr(agent, 'level', 1),
        sanity=getattr(agent, 'sanity', 100),
        max_sanity=getattr(agent, 'max_sanity', 100),
        is_alive=getattr(agent, 'is_alive', True),
        death_cause=getattr(agent, 'death_cause', None),
        owner_id=getattr(agent, 'owner_id', ''),
        total_pnl_usd=getattr(agent, 'total_pnl_usd', 0.0),
        win_rate=getattr(agent, 'win_rate', 0.0),
        trades_count=getattr(agent, 'trades_count', 0),
        genome=getattr(agent, 'genome', {}),
        parent_agent_ids=getattr(agent, 'parent_agent_ids', []) or [],
        created_at=getattr(agent, 'created_at', datetime.utcnow()),
        updated_at=getattr(agent, 'updated_at', datetime.utcnow()),
    )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    archetype: Optional[str] = Query(None, description="Filter by archetype"),
    is_alive: Optional[bool] = Query(None, description="Filter by alive status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db_session: AsyncSession = Depends(get_db)
):
    """
    Get list of all agents (roster).

    Returns paginated list of agents with optional filtering.
    """
    repo = AgentRepository(db_session)

    # Get agents filtered by alive status
    if is_alive is None or is_alive:
        agents = await repo.get_all_alive()
    else:
        agents = await repo.get_all_dead()

    # Filter by archetype if provided
    if archetype:
        agents = [a for a in agents if hasattr(a, 'archetype') and a.archetype == archetype.upper()]

    # Paginate
    total = len(agents)
    agents = agents[offset:offset + limit]

    return AgentListResponse(
        agents=[_agent_to_response(a) for a in agents],
        total=total
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific agent.

    Includes agent stats, P&L, and current status.
    """
    repo = AgentRepository(db_session)
    agent = await repo.get(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return _agent_to_response(agent)
