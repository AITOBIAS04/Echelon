"""
Async Database Connection
=========================

Async database connection using SQLAlchemy 2.0 with asyncpg.
Provides session management, FastAPI dependencies, and lifecycle hooks.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import DatabaseConfig

# Create async engine
engine = create_async_engine(
    DatabaseConfig.DATABASE_URL,
    pool_size=DatabaseConfig.POOL_SIZE,
    max_overflow=DatabaseConfig.MAX_OVERFLOW,
    echo=False,  # Set True for SQL logging
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# =========================================
# SESSION MANAGEMENT
# =========================================

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with automatic cleanup."""
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_session() as session:
        yield session


# =========================================
# LIFECYCLE
# =========================================

async def init_db():
    """Verify database connectivity on startup.

    Table creation is handled exclusively by Alembic migrations.
    This only validates the connection pool is reachable.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db():
    """Close database connections."""
    await engine.dispose()



