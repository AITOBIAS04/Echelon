"""
FastAPI dependency injection for shared services.
"""

from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal, User as DBUser
from backend.mechanics.butterfly_engine import ButterflyEngine
from backend.mechanics.paradox_engine import ParadoxEngine
from backend.core.osint_registry import get_osint_registry

# Global instances (singleton pattern)
_butterfly_engine: Optional[ButterflyEngine] = None
_paradox_engine: Optional[ParadoxEngine] = None
_user_service: Optional[Any] = None


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def get_current_user(db: Session = Depends(get_db)):
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

