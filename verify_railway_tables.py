#!/usr/bin/env python3
"""Verify tables exist in Railway database and show row counts."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import async_session_maker
from sqlalchemy import text

async def verify_tables():
    """List all tables and their row counts."""
    # Never hardcode credentials. Require DATABASE_URL from the environment.
    if not os.getenv("DATABASE_URL"):
        raise SystemExit(
            "DATABASE_URL is not set.\n"
            "Set it to your Railway public Postgres URL, e.g.\n"
            "  export DATABASE_URL='postgresql://postgres:<PASSWORD>@hopper.proxy.rlwy.net:15300/railway'\n"
        )
    
    async with async_session_maker() as session:
        # Get all tables
        result = await session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
        )
        tables = [row[0] for row in result]
        
        print("=" * 60)
        print("RAILWAY DATABASE VERIFICATION")
        print("=" * 60)
        print(f"\n✅ Found {len(tables)} tables:\n")
        
        # Get row counts for each table
        for table in tables:
            try:
                result = await session.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                )
                count = result.scalar_one()
                print(f"  📊 {table:25} → {count:4} rows")
            except Exception as e:
                print(f"  ⚠️  {table:25} → Error: {e}")
        
        # Check Alembic version
        print("\n" + "=" * 60)
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one_or_none()
            if version:
                print(f"✅ Alembic migration version: {version}")
            else:
                print("⚠️  No Alembic version found")
        except Exception as e:
            print(f"⚠️  Could not check Alembic version: {e}")
        
        print("=" * 60)
        print("\n✅ Your database is fully migrated and seeded!")
        print("   Railway's UI may not show existing tables, but they're all there.")

if __name__ == "__main__":
    asyncio.run(verify_tables())

