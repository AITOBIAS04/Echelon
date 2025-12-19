"""
Database Module
===============

Database configuration and connection management.
"""

from .config import DatabaseConfig, ENV_TEMPLATE
from .connection import (
    engine,
    async_session_maker,
    Base,
    get_session,
    get_db,
    init_db,
    close_db,
)
from .models import (
    User,
    Timeline,
    Agent,
    WingFlap,
    Paradox,
    UserPosition,
    WatchlistItem,
    PrivateFork,
    AgentArchetype,
    WingFlapType,
    ParadoxStatus,
    SeverityClass,
)

__all__ = [
    "DatabaseConfig",
    "ENV_TEMPLATE",
    "engine",
    "async_session_maker",
    "Base",
    "get_session",
    "get_db",
    "init_db",
    "close_db",
    # Models
    "User",
    "Timeline",
    "Agent",
    "WingFlap",
    "Paradox",
    "UserPosition",
    "WatchlistItem",
    "PrivateFork",
    # Enums
    "AgentArchetype",
    "WingFlapType",
    "ParadoxStatus",
    "SeverityClass",
]

