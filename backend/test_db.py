"""
Database Connection Test
=======================

Test script to verify database connection and table creation.
"""
import sys
import os
import asyncio

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database.connection import engine, init_db

async def test():
    """Test database connection and initialization."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    print()
    
    print("🔌 Testing database connection...")
    try:
        # Test connection
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
        
        print()
        print("📦 Initializing database tables...")
        await init_db()
        print("✅ Database tables created/verified!")
        
        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Database error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()
        print("\n🔌 Connection closed")

if __name__ == "__main__":
    asyncio.run(test())

