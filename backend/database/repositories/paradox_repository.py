"""
Paradox Repository
==================

Repository pattern for Paradox data access.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paradox, ParadoxStatus


class ParadoxRepository:
    """Repository for Paradox operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, paradox_id: str) -> Optional[Paradox]:
        """Get paradox by ID."""
        result = await self.session.execute(
            select(Paradox).where(Paradox.id == paradox_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active(self) -> List[Paradox]:
        """Get all active paradoxes."""
        result = await self.session.execute(
            select(Paradox).where(Paradox.status == ParadoxStatus.ACTIVE)
        )
        return list(result.scalars().all())
    
    async def get_by_timeline(self, timeline_id: str) -> List[Paradox]:
        """Get paradoxes by timeline."""
        result = await self.session.execute(
            select(Paradox).where(Paradox.timeline_id == timeline_id)
        )
        return list(result.scalars().all())


