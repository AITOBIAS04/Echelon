"""Test database connection and repositories."""
import sys
import os
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database.connection import engine, get_db
from backend.database.repositories import TimelineRepository
from backend.database.config import DatabaseConfig

async def test_connection():
    """Test async database connection."""
    print("🔌 Testing database connection...")
    print(f"   URL: {DatabaseConfig.DATABASE_URL[:60]}...")
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_repository():
    """Test repository access."""
    print("\n📦 Testing repository...")
    
    try:
        async for db in get_db():
            repo = TimelineRepository(db)
            timelines = await repo.get_all_active()
            print(f"✅ Repository test successful!")
            print(f"   Found {len(timelines)} active timelines")
            return True
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    print()
    
    conn_ok = await test_connection()
    repo_ok = await test_repository()
    
    print()
    print("=" * 60)
    if conn_ok and repo_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

