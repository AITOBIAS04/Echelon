import asyncio
from logging.config import fileConfig
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection

from alembic import context

# Import your models (but NOT DatabaseConfig yet - it may read env vars too early)
from database.connection import Base
from database import models  # This imports all models

# Alembic Config object
config = context.config

# CRITICAL: Read DATABASE_URL directly from environment FIRST
# Railway sets DATABASE_URL, so we MUST read it before importing DatabaseConfig
database_url = os.getenv("DATABASE_URL")

# Debug: Log what we found (but mask password)
if database_url:
    masked_url = database_url.split("@")[-1] if "@" in database_url else database_url
    print(f"🔍 [Alembic] Found DATABASE_URL: postgresql://***@{masked_url}", file=sys.stderr)
else:
    print("⚠️  [Alembic] DATABASE_URL not found in environment, using DatabaseConfig fallback", file=sys.stderr)
    # Only import DatabaseConfig if DATABASE_URL is not set
    from database.config import DatabaseConfig
    database_url = DatabaseConfig.SYNC_DATABASE_URL
    masked_url = database_url.split("@")[-1] if "@" in database_url else database_url
    print(f"🔍 [Alembic] Using DatabaseConfig: postgresql://***@{masked_url}", file=sys.stderr)

# Convert to sync URL format (psycopg2) for migrations
if database_url and database_url.startswith("postgresql://") and "+psycopg2" not in database_url and "+asyncpg" not in database_url:
    # Railway format: postgresql://... -> postgresql+psycopg2://...
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    print(f"✅ [Alembic] Converted to psycopg2 format", file=sys.stderr)
elif database_url and database_url.startswith("postgresql+asyncpg://"):
    # Already has asyncpg, convert to psycopg2 for sync migrations
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    print(f"✅ [Alembic] Converted asyncpg to psycopg2 format", file=sys.stderr)

# Set the URL for Alembic
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
    print(f"✅ [Alembic] Database URL configured for migrations", file=sys.stderr)
else:
    print("❌ [Alembic] ERROR: No database URL found!", file=sys.stderr)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using sync engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
