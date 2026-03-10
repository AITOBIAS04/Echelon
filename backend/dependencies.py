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

# Global instances (singleton pattern)
_butterfly_engine: Optional[ButterflyEngine] = None
_paradox_engine: Optional[ParadoxEngine] = None
_user_service: Optional[Any] = None


# =============================================================================
# DATABASE SESSION
# =============================================================================

async def get_db():
    """Database session dependency (async)."""
    async for session in get_db_session():
        yield session


# =============================================================================
# REPOSITORY DEPENDENCIES
# =============================================================================

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

def get_butterfly_engine() -> Optional[ButterflyEngine]:
    """
    Get or create the Butterfly Engine singleton.

    Returns None — routes create their own engines with request-scoped sessions.
    """
    return None


def get_paradox_engine() -> Optional[ParadoxEngine]:
    """
    Get or create the Paradox Engine singleton.

    Returns None — routes create their own engines with request-scoped sessions.
    """
    return None


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

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.jwt import decode_token, TokenData

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token.

    Requires:
        Bearer token in Authorization header

    Returns:
        TokenData with user information

    Raises:
        HTTPException 401 if not authenticated or token invalid

    When TESTNET_AUTO_AUTH=true and no token is provided, returns a
    default seed user so every endpoint works without login.
    """
    if not credentials:
        # Testnet bypass: return default seed user when no token present
        if os.getenv("TESTNET_AUTO_AUTH", "false").lower() == "true":
            return TokenData(
                user_id="USR_001",
                username="DeepStateTrader",
                email="deep@echelon.io",
                tier="PRIME",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return token_data


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenData]:
    """
    Get current authenticated user from JWT token (optional).

    This version doesn't raise an error if no token is provided.
    Useful for endpoints that work with or without authentication.

    Returns:
        TokenData if authenticated, None otherwise
    """
    if not credentials:
        return None
    return decode_token(credentials.credentials)
