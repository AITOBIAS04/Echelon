"""
Database Configuration
=====================

Database configuration using environment variables.
Supports both async (asyncpg) and sync (psycopg2) connections.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Database configuration from environment."""
    
    # PostgreSQL connection
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "echelon")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    
    # Connection URL
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Pool settings
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    # For sync operations (migrations, etc.)
    SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")


# Create .env file template
ENV_TEMPLATE = """
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=echelon
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Or use full URL
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
"""

