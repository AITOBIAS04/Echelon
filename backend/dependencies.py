"""
FastAPI dependency injection for shared services.
"""

import os
from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import async database connection
from backend.database.connection import get_db as get_db_session
from backend.database.repositories.timeline_repository import TimelineRepository
from backend.database.repositories.agent_repository import AgentRepository
from backend.database.repositories.paradox_repository import ParadoxRepository
from backend.database.repositories.user_repository import UserRepository

from backend.mechanics.butterfly_engine import ButterflyEngine
from backend.mechanics.paradox_engine import ParadoxEngine
from backend.core.osint_registry import get_osint_registry

# Check if we should use mocks
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"

# Global instances (singleton pattern)
_butterfly_engine: Optional[ButterflyEngine] = None
_paradox_engine: Optional[ParadoxEngine] = None
_user_service: Optional[Any] = None


# =============================================================================
# DATABASE SESSION
# =============================================================================

def get_db():
    """Database session dependency (async)."""
    return get_db_session()


# =============================================================================
# REPOSITORY DEPENDENCIES
# =============================================================================

if USE_MOCKS:
    # Use mock implementations
    from backend.mocks.mock_data import (
        MockTimelineRepository,
        MockAgentRepository,
        MockParadoxRepository,
        MockUserRepository
    )
    
    def get_timeline_repo():
        """Get timeline repository (mock)."""
        return MockTimelineRepository()
    
    def get_agent_repo():
        """Get agent repository (mock)."""
        return MockAgentRepository()
    
    def get_paradox_repo():
        """Get paradox repository (mock)."""
        return MockParadoxRepository()
    
    def get_user_repo():
        """Get user repository (mock)."""
        return MockUserRepository()

else:
    # Use real database repositories
    async def get_timeline_repo(db: AsyncSession = Depends(get_db_session)):
        """Get timeline repository (real database)."""
        return TimelineRepository(db)
    
    async def get_agent_repo(db: AsyncSession = Depends(get_db_session)):
        """Get agent repository (real database)."""
        return AgentRepository(db)
    
    async def get_paradox_repo(db: AsyncSession = Depends(get_db_session)):
        """Get paradox repository (real database)."""
        return ParadoxRepository(db)
    
    async def get_user_repo(db: AsyncSession = Depends(get_db_session)):
        """Get user repository (real database)."""
        return UserRepository(db)


# =============================================================================
# ENGINE DEPENDENCIES
# =============================================================================

def get_butterfly_engine() -> ButterflyEngine:
    """
    Get or create the Butterfly Engine singleton.
    
    Note: In production, this should be initialized with proper
    timeline_repo, agent_repo, and osint_service dependencies.
    """
    global _butterfly_engine
    if _butterfly_engine is None:
        # TODO: Initialize with actual repositories
        # For now, this will need to be set up in main.py
        raise HTTPException(
            status_code=503,
            detail="Butterfly Engine not initialized. Please configure repositories in main.py"
        )
    return _butterfly_engine


def get_paradox_engine() -> ParadoxEngine:
    """
    Get or create the Paradox Engine singleton.
    
    Note: In production, this should be initialized with proper
    timeline_repo, agent_repo, and butterfly_engine dependencies.
    """
    global _paradox_engine
    if _paradox_engine is None:
        # TODO: Initialize with actual repositories
        # For now, this will need to be set up in main.py
        raise HTTPException(
            status_code=503,
            detail="Paradox Engine not initialized. Please configure repositories in main.py"
        )
    return _paradox_engine


def init_butterfly_engine(engine: ButterflyEngine):
    """Initialize the global Butterfly Engine instance."""
    global _butterfly_engine
    _butterfly_engine = engine


def init_paradox_engine(engine: ParadoxEngine):
    """Initialize the global Paradox Engine instance."""
    global _paradox_engine
    _paradox_engine = engine


def get_user_service():
    """
    Get or create the User Service singleton.
    
    Note: In production, this should be initialized with proper
    repositories for positions, private forks, watchlist, etc.
    """
    global _user_service
    if _user_service is None:
        # TODO: Initialize with actual repositories
        # For now, this will need to be set up in main.py
        raise HTTPException(
            status_code=503,
            detail="User Service not initialized. Please configure repositories in main.py"
        )
    return _user_service


def init_user_service(service: Any):
    """Initialize the global User Service instance."""
    global _user_service
    _user_service = service


# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_current_user(db: AsyncSession = Depends(get_db_session)):
    """
    Get current authenticated user.
    
    This is a placeholder - in production, this should extract
    the user from JWT token or session.
    """
    # TODO: Implement proper authentication
    # For now, return a mock user or raise 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )
