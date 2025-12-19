"""
Timeline Repository
==================

Repository pattern for Timeline data access.
Provides clean interface for database operations.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Timeline, WingFlap


class TimelineRepository:
    """Repository for Timeline operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, timeline_id: str) -> Optional[Timeline]:
        """Get timeline by ID."""
        result = await self.session.execute(
            select(Timeline).where(Timeline.id == timeline_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> List[Timeline]:
        """Get all active timelines."""
        result = await self.session.execute(
            select(Timeline)
            .where(Timeline.is_active == True)
            .order_by(Timeline.gravity_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_gravity(
        self,
        min_gravity: float = 0,
        limit: int = 20
    ) -> List[Timeline]:
        """Get timelines sorted by gravity score."""
        result = await self.session.execute(
            select(Timeline)
            .where(Timeline.is_active == True)
            .where(Timeline.gravity_score >= min_gravity)
            .order_by(Timeline.gravity_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_with_paradox(self) -> List[Timeline]:
        """Get timelines with active paradoxes."""
        result = await self.session.execute(
            select(Timeline)
            .where(Timeline.has_active_paradox == True)
            .order_by(Timeline.stability.asc())
        )
        return list(result.scalars().all())
    
    async def create(self, timeline: Timeline) -> Timeline:
        """Create a new timeline."""
        self.session.add(timeline)
        await self.session.flush()
        return timeline
    
    async def update_stability(
        self,
        timeline_id: str,
        new_stability: float
    ):
        """Update timeline stability."""
        await self.session.execute(
            update(Timeline)
            .where(Timeline.id == timeline_id)
            .values(stability=new_stability, updated_at=datetime.utcnow())
        )
    
    async def set_decay_multiplier(
        self,
        timeline_id: str,
        multiplier: float
    ):
        """Set decay multiplier (for paradox)."""
        await self.session.execute(
            update(Timeline)
            .where(Timeline.id == timeline_id)
            .values(
                decay_multiplier=multiplier,
                decay_rate_per_hour=1.0 * multiplier
            )
        )
    
    async def set_paradox_status(
        self,
        timeline_id: str,
        has_paradox: bool
    ):
        """Set paradox status."""
        await self.session.execute(
            update(Timeline)
            .where(Timeline.id == timeline_id)
            .values(has_active_paradox=has_paradox)
        )
    
    async def count(self, min_gravity: float = 0) -> int:
        """Count active timelines."""
        result = await self.session.execute(
            select(func.count(Timeline.id))
            .where(Timeline.is_active == True)
            .where(Timeline.gravity_score >= min_gravity)
        )
        return result.scalar() or 0
    
    async def update_logic_gap(
        self,
        timeline_id: str,
        logic_gap: float
    ):
        """Update logic gap (for paradox detection)."""
        await self.session.execute(
            update(Timeline)
            .where(Timeline.id == timeline_id)
            .values(logic_gap=logic_gap)
        )
    
    async def get_flaps_since(
        self,
        timeline_id: str,
        since: datetime
    ) -> List[WingFlap]:
        """Get wing flaps since timestamp."""
        result = await self.session.execute(
            select(WingFlap)
            .where(WingFlap.timeline_id == timeline_id)
            .where(WingFlap.timestamp >= since)
            .order_by(WingFlap.timestamp.desc())
        )
        return list(result.scalars().all())
    
    async def create_fork(
        self,
        parent_id: str,
        narrative: str,
        initial_stability: float,
        founder_id: str
    ) -> Timeline:
        """Create a new fork timeline."""
        import uuid
        
        fork = Timeline(
            id=f"fork_{uuid.uuid4().hex[:12]}",
            name=f"Fork from {parent_id[:8]}",
            narrative=narrative,
            stability=initial_stability,
            price_yes=0.5,
            price_no=0.5,
            parent_timeline_id=parent_id,
            founder_id=founder_id,
            is_active=True,
        )
        
        self.session.add(fork)
        await self.session.flush()
        return fork

