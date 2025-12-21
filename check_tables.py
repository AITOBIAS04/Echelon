#!/usr/bin/env python3
"""Check what tables exist in the Railway database."""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import async_session_maker
from sqlalchemy import text

async def check_tables():
    """List all tables in the database."""
    async with async_session_maker() as session:
        result = await session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
        )
        tables = [row[0] for row in result]
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("❌ No tables found in database!")
        
        # Also check alembic_version
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one_or_none()
            if version:
                print(f"\n✅ Alembic version: {version}")
            else:
                print("\n⚠️  No Alembic version found (migrations may not have run)")
        except Exception as e:
            print(f"\n⚠️  Could not check Alembic version: {e}")

if __name__ == "__main__":
    # Use DATABASE_URL from environment or default
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL not set. Using public Railway URL...")
        os.environ["DATABASE_URL"] = "postgresql://postgres:<PASSWORD>@hopper.proxy.rlwy.net:15300/railway"
    
    asyncio.run(check_tables())

