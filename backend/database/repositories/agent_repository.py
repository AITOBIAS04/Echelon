"""
Agent Repository
================

Repository pattern for Agent data access.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Agent


class AgentRepository:
    """Repository for Agent operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_alive(self) -> List[Agent]:
        """Get all alive agents."""
        result = await self.session.execute(
            select(Agent).where(Agent.is_alive == True)
        )
        return list(result.scalars().all())
    
    async def get_by_owner(self, owner_id: str) -> List[Agent]:
        """Get agents by owner."""
        result = await self.session.execute(
            select(Agent).where(Agent.owner_id == owner_id)
        )
        return list(result.scalars().all())


