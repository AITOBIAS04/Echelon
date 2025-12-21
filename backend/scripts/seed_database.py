"""
Echelon Database Seeder
Run with: python -m backend.scripts.seed_database
Or with auto-reseed: python -m backend.scripts.seed_database --force
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
import uuid
import sys

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.connection import async_session_maker, init_db
from backend.database.models import (
    User, Agent, Timeline, WingFlap, Paradox, UserPosition,
    AgentArchetype, WingFlapType, ParadoxStatus, SeverityClass
)


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:8].upper()}"


async def seed_users(session) -> list:
    """Create test users."""
    users = [
        User(
            id="USR_001",
            username="DeepStateTrader",
            email="deep@echelon.io",
            password_hash="$2b$12$dummy_hash_for_testing",
            tier="pro",
            balance_usdc=15000.0,
            balance_echelon=5000
        ),
        User(
            id="USR_002",
            username="MacroMaven",
            email="macro@echelon.io",
            password_hash="$2b$12$dummy_hash_for_testing",
            tier="pro",
            balance_usdc=25000.0,
            balance_echelon=8000
        ),
        User(
            id="USR_003",
            username="BioHazardBets",
            email="bio@echelon.io",
            password_hash="$2b$12$dummy_hash_for_testing",
            tier="free",
            balance_usdc=5000.0,
            balance_echelon=1000
        ),
    ]
    
    for user in users:
        session.add(user)
    
    await session.flush()
    print(f"✅ Created {len(users)} users")
    return users


async def seed_agents(session, users: list) -> list:
    """Create test agents."""
    agents = [
        Agent(
            id="AGT_MEGALODON",
            name="MEGALODON",
            archetype=AgentArchetype.SHARK,
            tier=2,
            level=15,
            sanity=78,
            max_sanity=100,
            owner_id=users[0].id,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            total_pnl_usd=45230.50,
            win_rate=0.67,
            trades_count=234,
            genome={"aggression": 0.8, "patience": 0.3, "risk_tolerance": 0.7}
        ),
        Agent(
            id="AGT_CARDINAL",
            name="CARDINAL",
            archetype=AgentArchetype.SPY,
            tier=1,
            level=8,
            sanity=45,
            max_sanity=100,
            owner_id=users[1].id,
            wallet_address="0x2345678901abcdef2345678901abcdef23456789",
            total_pnl_usd=12450.00,
            win_rate=0.58,
            trades_count=89,
            genome={"stealth": 0.9, "intel_quality": 0.7, "network": 0.6}
        ),
        Agent(
            id="AGT_ENVOY",
            name="ENVOY",
            archetype=AgentArchetype.DIPLOMAT,
            tier=1,
            level=12,
            sanity=92,
            max_sanity=100,
            owner_id=users[0].id,
            wallet_address="0x3456789012abcdef3456789012abcdef34567890",
            total_pnl_usd=8900.25,
            win_rate=0.72,
            trades_count=56,
            genome={"charisma": 0.85, "negotiation": 0.9, "trust": 0.75}
        ),
        Agent(
            id="AGT_VIPER",
            name="VIPER",
            archetype=AgentArchetype.SABOTEUR,
            tier=1,
            level=6,
            sanity=23,
            max_sanity=100,
            owner_id=users[2].id,
            wallet_address="0x4567890123abcdef4567890123abcdef45678901",
            total_pnl_usd=-2340.00,
            win_rate=0.41,
            trades_count=67,
            genome={"deception": 0.95, "disruption": 0.8, "escape": 0.6}
        ),
        Agent(
            id="AGT_ORACLE",
            name="ORACLE",
            archetype=AgentArchetype.WHALE,
            tier=2,
            level=18,
            sanity=85,
            max_sanity=100,
            owner_id=users[1].id,
            wallet_address="0x5678901234abcdef5678901234abcdef56789012",
            total_pnl_usd=156000.00,
            win_rate=0.71,
            trades_count=412,
            genome={"capital": 0.95, "patience": 0.9, "market_impact": 0.85}
        ),
    ]
    
    for agent in agents:
        session.add(agent)
    
    await session.flush()
    print(f"✅ Created {len(agents)} agents")
    return agents


async def seed_timelines(session, users: list) -> list:
    """Create test timelines."""
    timelines = [
        Timeline(
            id="TL_GHOST_TANKER",
            name="Ghost Tanker - Venezuela Dark Fleet",
            narrative="Will the dark tanker dock in Shanghai within 48 hours?",
            keywords=["tanker", "venezuela", "oil", "sanctions", "shipping"],
            stability=67.5,
            surface_tension=72.0,
            price_yes=0.67,
            price_no=0.33,
            osint_alignment=45.0,
            logic_gap=0.22,
            gravity_score=78.5,
            total_volume_usd=125000.0,
            liquidity_depth_usd=45000.0,
            active_agent_count=12,
            decay_rate_per_hour=1.0,
            founder_id=users[0].id,
            founder_yield_rate=0.001,
            connected_timeline_ids=["TL_FED_RATE", "TL_OIL_CRISIS"],
            has_active_paradox=False
        ),
        Timeline(
            id="TL_FED_RATE",
            name="Fed Rate Decision - January 2026",
            narrative="Will the Fed cut rates by 25bps?",
            keywords=["fed", "rates", "fomc", "powell", "inflation"],
            stability=89.2,
            surface_tension=91.0,
            price_yes=0.72,
            price_no=0.28,
            osint_alignment=68.0,
            logic_gap=0.04,
            gravity_score=92.1,
            total_volume_usd=890000.0,
            liquidity_depth_usd=250000.0,
            active_agent_count=34,
            decay_rate_per_hour=1.0,
            founder_id=users[1].id,
            founder_yield_rate=0.0015,
            connected_timeline_ids=["TL_GHOST_TANKER", "TL_CONTAGION"],
            has_active_paradox=False
        ),
        Timeline(
            id="TL_CONTAGION",
            name="Contagion Zero - Mumbai Outbreak",
            narrative="Will WHO declare a health emergency within 7 days?",
            keywords=["outbreak", "pandemic", "who", "mumbai", "health"],
            stability=23.4,
            surface_tension=18.0,
            price_yes=0.82,
            price_no=0.18,
            osint_alignment=35.0,
            logic_gap=0.47,
            gravity_score=85.3,
            total_volume_usd=340000.0,
            liquidity_depth_usd=67000.0,
            active_agent_count=28,
            decay_rate_per_hour=5.0,  # Accelerated due to paradox
            founder_id=users[2].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_FED_RATE", "TL_OIL_CRISIS"],
            has_active_paradox=True
        ),
        Timeline(
            id="TL_OIL_CRISIS",
            name="Oil Crisis - Hormuz Strait",
            narrative="Will oil prices exceed $100/barrel this week?",
            keywords=["oil", "hormuz", "opec", "crude", "energy"],
            stability=54.7,
            surface_tension=58.0,
            price_yes=0.45,
            price_no=0.55,
            osint_alignment=52.0,
            logic_gap=0.07,
            gravity_score=71.2,
            total_volume_usd=567000.0,
            liquidity_depth_usd=189000.0,
            active_agent_count=19,
            decay_rate_per_hour=1.0,
            founder_id=users[0].id,
            founder_yield_rate=0.001,
            connected_timeline_ids=["TL_GHOST_TANKER", "TL_CONTAGION"],
            has_active_paradox=False
        ),
    ]
    
    for timeline in timelines:
        session.add(timeline)
    
    await session.flush()
    print(f"✅ Created {len(timelines)} timelines")
    return timelines


async def seed_paradoxes(session, timelines: list) -> list:
    """Create test paradoxes."""
    contagion = next(t for t in timelines if t.id == "TL_CONTAGION")
    
    paradoxes = [
        Paradox(
            id="PARADOX_CONTAGION_001",
            timeline_id=contagion.id,
            status=ParadoxStatus.ACTIVE,
            severity_class=SeverityClass.CLASS_2_SEVERE,
            logic_gap=0.47,
            spawned_at=(datetime.now(timezone.utc) - timedelta(hours=2)).replace(tzinfo=None),
            detonation_time=(datetime.now(timezone.utc) + timedelta(hours=4)).replace(tzinfo=None),
            decay_multiplier=5.0,
            extraction_cost_usdc=970.0,
            extraction_cost_echelon=288,
            carrier_sanity_cost=34
        ),
    ]
    
    for paradox in paradoxes:
        session.add(paradox)
    
    await session.flush()
    print(f"✅ Created {len(paradoxes)} paradoxes")
    return paradoxes


async def seed_wing_flaps(session, timelines: list, agents: list) -> list:
    """Create test wing flaps."""
    flaps = []
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    actions = [
        ("bought", "YES", WingFlapType.TRADE),
        ("sold", "YES", WingFlapType.TRADE),
        ("bought", "NO", WingFlapType.TRADE),
        ("deployed SHIELD on", "", WingFlapType.SHIELD),
        ("launched SABOTAGE on", "", WingFlapType.SABOTAGE),
    ]
    
    for i in range(50):
        timeline = random.choice(timelines)
        agent = random.choice(agents)
        action_template, side, flap_type = random.choice(actions)
        volume = random.uniform(500, 50000)
        stability_delta = random.uniform(-15, 15)
        
        if flap_type == WingFlapType.SHIELD:
            stability_delta = abs(stability_delta)
            action = f"{agent.name} deployed SHIELD on {timeline.name}"
        elif flap_type == WingFlapType.SABOTAGE:
            stability_delta = -abs(stability_delta)
            action = f"{agent.name} launched SABOTAGE on {timeline.name}"
        else:
            price = random.uniform(0.20, 0.80)
            action = f"{agent.name} {action_template} {int(volume/price)} {side} @ ${price:.2f}"
        
        flap = WingFlap(
            id=f"FLAP_{i:05d}",
            timestamp=base_time - timedelta(minutes=i*2),
            timeline_id=timeline.id,
            agent_id=agent.id,
            flap_type=flap_type,
            action=action,
            stability_delta=round(stability_delta, 2),
            direction="ANCHOR" if stability_delta > 0 else "DESTABILISE",
            volume_usd=round(volume, 2),
            timeline_stability=round(timeline.stability + stability_delta, 1),
            timeline_price=timeline.price_yes,
            spawned_ripple=abs(stability_delta) > 12,
            ripple_timeline_id=f"TL_FORK_{i}" if abs(stability_delta) > 12 else None,
            founder_yield_earned=round(abs(stability_delta) * 0.001 * volume, 2) if stability_delta > 0 else None
        )
        flaps.append(flap)
        session.add(flap)
    
    await session.flush()
    print(f"✅ Created {len(flaps)} wing flaps")
    return flaps


async def seed_user_positions(session, users: list, timelines: list) -> list:
    """Create test user positions."""
    positions = [
        UserPosition(
            id=generate_id("POS"),
            user_id=users[0].id,
            timeline_id="TL_GHOST_TANKER",
            side="YES",
            shards_held=450,
            average_entry_price=0.52,
            is_founder=True,
            founder_yield_earned_usd=125.40
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[0].id,
            timeline_id="TL_CONTAGION",
            side="NO",
            shards_held=200,
            average_entry_price=0.25,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[1].id,
            timeline_id="TL_FED_RATE",
            side="YES",
            shards_held=1200,
            average_entry_price=0.65,
            is_founder=True,
            founder_yield_earned_usd=450.00
        ),
    ]
    
    for pos in positions:
        session.add(pos)
    
    await session.flush()
    print(f"✅ Created {len(positions)} user positions")
    return positions


async def main():
    """Run the seeder."""
    print("=" * 60)
    print("ECHELON DATABASE SEEDER")
    print("=" * 60)
    print()
    
    # Initialize database
    print("🔌 Connecting to database...")
    await init_db()
    
    async with async_session_maker() as session:
        try:
            # Check if already seeded
            from sqlalchemy import select, func
            result = await session.execute(select(func.count()).select_from(User))
            user_count = result.scalar()
            
            if user_count > 0:
                print(f"⚠️  Database already has {user_count} users.")
                
                # Check for --force flag
                force_reseed = "--force" in sys.argv or "-f" in sys.argv
                
                if not force_reseed:
                    try:
                        response = input("Clear and reseed? (y/N): ")
                        if response.lower() != 'y':
                            print("Aborted.")
                            return
                    except EOFError:
                        # Non-interactive mode (e.g., piped input)
                        print("⚠️  Non-interactive mode detected. Use --force to auto-reseed.")
                        print("Aborted.")
                        return
                else:
                    print("🔄 Force reseed enabled, clearing existing data...")
                
                # Clear existing data
                print("🗑️  Clearing existing data...")
                await session.execute(WingFlap.__table__.delete())
                await session.execute(Paradox.__table__.delete())
                await session.execute(UserPosition.__table__.delete())
                await session.execute(Agent.__table__.delete())
                await session.execute(Timeline.__table__.delete())
                await session.execute(User.__table__.delete())
                await session.commit()
            
            # Seed data
            print()
            print("🌱 Seeding database...")
            print()
            
            users = await seed_users(session)
            agents = await seed_agents(session, users)
            timelines = await seed_timelines(session, users)
            paradoxes = await seed_paradoxes(session, timelines)
            wing_flaps = await seed_wing_flaps(session, timelines, agents)
            positions = await seed_user_positions(session, users, timelines)
            
            await session.commit()
            
            print()
            print("=" * 60)
            print("✅ DATABASE SEEDED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  • Users: {len(users)}")
            print(f"  • Agents: {len(agents)}")
            print(f"  • Timelines: {len(timelines)}")
            print(f"  • Paradoxes: {len(paradoxes)}")
            print(f"  • Wing Flaps: {len(wing_flaps)}")
            print(f"  • Positions: {len(positions)}")
            print()
            print("Next: Set USE_MOCKS=false in .env and restart server")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
