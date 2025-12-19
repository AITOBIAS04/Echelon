"""
User Repository
===============

Repository pattern for User data access.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, UserPosition, WatchlistItem, PrivateFork


class UserRepository:
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_positions(self, user_id: str) -> List[UserPosition]:
        """Get user positions."""
        result = await self.session.execute(
            select(UserPosition).where(UserPosition.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def get_watchlist(self, user_id: str) -> List[WatchlistItem]:
        """Get user watchlist."""
        result = await self.session.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def get_private_forks(self, user_id: str) -> List[PrivateFork]:
        """Get user private forks."""
        result = await self.session.execute(
            select(PrivateFork).where(PrivateFork.user_id == user_id)
        )
        return list(result.scalars().all())

