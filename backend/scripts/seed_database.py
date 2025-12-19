"""
Database Seeding Script
=======================

Seeds the database with initial data for development and testing.
Run with: python -m backend.scripts.seed_database
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.database.connection import get_session, init_db
from backend.database.models import (
    User, Timeline, Agent, WingFlap, Paradox, 
    UserPosition, WatchlistItem, PrivateFork, AgentArchetype
)
from backend.auth.password import hash_password


async def seed_users():
    """Seed initial users."""
    async with get_session() as session:
        # Check if users already exist
        from sqlalchemy import select
        result = await session.execute(select(User).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Users already exist, skipping user seed")
            return
        
        # Create test users
        users = [
            User(
                id="USR_0001",
                username="testuser",
                email="test@test.com",
                password_hash=hash_password("password123"),
                tier="free",
                balance_usdc=1000.0,
                balance_echelon=100,
                wallet_address=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            User(
                id="USR_0002",
                username="premium_user",
                email="premium@test.com",
                password_hash=hash_password("password123"),
                tier="premium",
                balance_usdc=5000.0,
                balance_echelon=500,
                wallet_address=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        for user in users:
            session.add(user)
        
        await session.commit()
        print(f"✅ Seeded {len(users)} users")


async def seed_timelines():
    """Seed initial timelines."""
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Timeline).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Timelines already exist, skipping timeline seed")
            return
        
        timelines = [
            Timeline(
                id="TL_0001",
                name="Bitcoin Price Prediction",
                narrative="Will Bitcoin reach $100k by end of year?",
                keywords=["bitcoin", "crypto", "price"],
                stability=75.0,
                surface_tension=50.0,
                price_yes=0.65,
                price_no=0.35,
                osint_alignment=70.0,
                logic_gap=0.1,
                gravity_score=60.0,
                gravity_factors={},
                total_volume_usd=100000.0,
                liquidity_depth_usd=50000.0,
                active_agent_count=10,
                decay_rate_per_hour=1.0,
                decay_multiplier=1.0,
                founder_id=None,
                founder_yield_rate=0.001,
                parent_timeline_id=None,
                connected_timeline_ids=[],
                has_active_paradox=False,
                is_active=True,
                created_at=datetime.utcnow(),
                resolved_at=None
            ),
            Timeline(
                id="TL_0002",
                name="Election Outcome",
                narrative="2028 Presidential Election: Newsom vs DeSantis",
                keywords=["election", "politics", "president"],
                stability=80.0,
                surface_tension=60.0,
                price_yes=0.55,
                price_no=0.45,
                osint_alignment=75.0,
                logic_gap=0.05,
                gravity_score=70.0,
                gravity_factors={},
                total_volume_usd=200000.0,
                liquidity_depth_usd=100000.0,
                active_agent_count=15,
                decay_rate_per_hour=1.0,
                decay_multiplier=1.0,
                founder_id=None,
                founder_yield_rate=0.001,
                parent_timeline_id=None,
                connected_timeline_ids=[],
                has_active_paradox=False,
                is_active=True,
                created_at=datetime.utcnow(),
                resolved_at=None
            ),
        ]
        
        for timeline in timelines:
            session.add(timeline)
        
        await session.commit()
        print(f"✅ Seeded {len(timelines)} timelines")


async def seed_agents():
    """Seed initial agents."""
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Agent).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Agents already exist, skipping agent seed")
            return
        
        agents = [
            Agent(
                id="AGENT_0001",
                name="MEGALODON",
                archetype=AgentArchetype.SHARK,
                owner_id="USR_0001",
                is_alive=True,
                sanity=100,
                wallet_address="0x0000000000000000000000000000000000000001",  # Placeholder wallet
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Agent(
                id="AGENT_0002",
                name="CARDINAL",
                archetype=AgentArchetype.SPY,
                owner_id="USR_0002",
                is_alive=True,
                sanity=100,
                wallet_address="0x0000000000000000000000000000000000000002",  # Placeholder wallet
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        for agent in agents:
            session.add(agent)
        
        await session.commit()
        print(f"✅ Seeded {len(agents)} agents")


async def main():
    """Main seeding function."""
    print("🌱 Starting database seed...")
    print("=" * 60)
    
    try:
        # Initialize database (create tables if needed)
        await init_db()
        print("✅ Database initialized")
        
        # Seed data
        await seed_users()
        await seed_timelines()
        await seed_agents()
        
        print("=" * 60)
        print("✅ Database seeding complete!")
        print("\nSeeded data:")
        print("  - 2 users (testuser, premium_user)")
        print("  - 2 timelines (Bitcoin, Election)")
        print("  - 2 agents (MEGALODON, CARDINAL)")
        print("\nDefault credentials:")
        print("  Email: test@test.com")
        print("  Password: password123")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

