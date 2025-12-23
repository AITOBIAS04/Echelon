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

from ..database.repositories.agent_repository import AgentRepository
from ..dependencies import get_db

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


class Agent(BaseModel):
    """Agent response model."""
    id: str
    name: Optional[str] = None
    archetype: Optional[str] = None
    is_alive: bool = True
    owner_id: Optional[str] = None


class AgentListResponse(BaseModel):
    """List of agents response."""
    agents: List[Agent]
    total: int


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
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if USE_MOCKS:
        # Return mock data structure
        return AgentListResponse(
            agents=[],
            total=0
        )
    
    repo = AgentRepository(db_session)
    
    # Get all alive agents (or all if is_alive is None)
    if is_alive is None or is_alive:
        agents = await repo.get_all_alive()
    else:
        # For dead agents, we'd need a different method
        agents = []
    
    # Filter by archetype if provided
    if archetype:
        agents = [a for a in agents if hasattr(a, 'archetype') and a.archetype == archetype.upper()]
    
    # Paginate
    total = len(agents)
    agents = agents[offset:offset + limit]
    
    # Convert to response model
    agent_list = [
        Agent(
            id=a.id,
            name=getattr(a, 'name', None),
            archetype=getattr(a, 'archetype', None),
            is_alive=getattr(a, 'is_alive', True),
            owner_id=getattr(a, 'owner_id', None)
        )
        for a in agents
    ]
    
    return AgentListResponse(
        agents=agent_list,
        total=total
    )


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific agent.
    
    Includes agent stats, P&L, and current status.
    """
    import os
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if USE_MOCKS:
        raise HTTPException(status_code=404, detail="Agent not found (mock mode)")
    
    repo = AgentRepository(db_session)
    agent = await repo.get(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return Agent(
        id=agent.id,
        name=getattr(agent, 'name', None),
        archetype=getattr(agent, 'archetype', None),
        is_alive=getattr(agent, 'is_alive', True),
        owner_id=getattr(agent, 'owner_id', None)
    )

