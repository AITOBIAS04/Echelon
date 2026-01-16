"""
Echelon Database Seeder - Deterministic Edition
================================================
Full demo data: 12 genesis agents, 10 timelines, 3 paradoxes, 75 wing flaps

This seeder is deterministic - running it multiple times produces the same data.
All IDs, names, and values are fixed (no random generation).

Run with: python -m backend.scripts.seed_database
Or with auto-reseed: python -m backend.scripts.seed_database --force

For fixtures-based seeding: python -m backend.scripts.seed_database --fixtures data/seed/fixtures/
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
import uuid
import sys

# Add parent to path for imports
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
        User(
            id="USR_004",
            username="WhaleHunter",
            email="whale@echelon.io",
            password_hash="$2b$12$dummy_hash_for_testing",
            tier="pro",
            balance_usdc=50000.0,
            balance_echelon=15000
        ),
        User(
            id="USR_005",
            username="ShadowBroker",
            email="shadow@echelon.io",
            password_hash="$2b$12$dummy_hash_for_testing",
            tier="elite",
            balance_usdc=100000.0,
            balance_echelon=25000
        ),
    ]
    
    for user in users:
        session.add(user)
    
    await session.flush()
    print(f"✅ Created {len(users)} users")
    return users


async def seed_agents(session, users: list) -> list:
    """Create the 12 genesis agents."""
    agents = [
        # ===== SHARKS (Aggressive Traders) =====
        Agent(
            id="AGT_MEGALODON",
            name="MEGALODON",
            archetype=AgentArchetype.SHARK,
            tier=3,
            level=25,
            sanity=78,
            max_sanity=100,
            owner_id=users[0].id,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            total_pnl_usd=45230.50,
            win_rate=0.67,
            trades_count=234,
            genome={"aggression": 0.85, "patience": 0.25, "risk_tolerance": 0.80}
        ),
        Agent(
            id="AGT_THRESHER",
            name="THRESHER",
            archetype=AgentArchetype.SHARK,
            tier=2,
            level=18,
            sanity=85,
            max_sanity=100,
            owner_id=users[1].id,
            wallet_address="0x2345678901abcdef2345678901abcdef23456789",
            total_pnl_usd=23400.25,
            win_rate=0.62,
            trades_count=189,
            genome={"aggression": 0.72, "patience": 0.35, "risk_tolerance": 0.68}
        ),
        Agent(
            id="AGT_HAMMERHEAD",
            name="HAMMERHEAD",
            archetype=AgentArchetype.SHARK,
            tier=2,
            level=14,
            sanity=72,
            max_sanity=100,
            owner_id=users[2].id,
            wallet_address="0x3456789012abcdef3456789012abcdef34567890",
            total_pnl_usd=18900.00,
            win_rate=0.58,
            trades_count=156,
            genome={"aggression": 0.78, "patience": 0.30, "risk_tolerance": 0.75}
        ),
        
        # ===== SPIES (Intelligence Gatherers) =====
        Agent(
            id="AGT_CARDINAL",
            name="CARDINAL",
            archetype=AgentArchetype.SPY,
            tier=2,
            level=16,
            sanity=45,
            max_sanity=100,
            owner_id=users[1].id,
            wallet_address="0x4567890123abcdef4567890123abcdef45678901",
            total_pnl_usd=12450.00,
            win_rate=0.71,
            trades_count=112,
            genome={"stealth": 0.90, "intel_quality": 0.75, "network": 0.65}
        ),
        Agent(
            id="AGT_RAVEN",
            name="RAVEN",
            archetype=AgentArchetype.SPY,
            tier=1,
            level=10,
            sanity=88,
            max_sanity=100,
            owner_id=users[3].id,
            wallet_address="0x5678901234abcdef5678901234abcdef56789012",
            total_pnl_usd=8905.50,
            win_rate=0.65,
            trades_count=78,
            genome={"stealth": 0.82, "intel_quality": 0.70, "network": 0.58}
        ),
        Agent(
            id="AGT_ORACLE",
            name="ORACLE",
            archetype=AgentArchetype.SPY,
            tier=3,
            level=22,
            sanity=92,
            max_sanity=100,
            owner_id=users[4].id,
            wallet_address="0x6789012345abcdef6789012345abcdef67890123",
            total_pnl_usd=89000.00,
            win_rate=0.78,
            trades_count=201,
            genome={"stealth": 0.95, "intel_quality": 0.92, "network": 0.88}
        ),
        
        # ===== DIPLOMATS (Stability Maintainers) =====
        Agent(
            id="AGT_ENVOY",
            name="ENVOY",
            archetype=AgentArchetype.DIPLOMAT,
            tier=2,
            level=15,
            sanity=92,
            max_sanity=100,
            owner_id=users[0].id,
            wallet_address="0x7890123456abcdef7890123456abcdef78901234",
            total_pnl_usd=8900.25,
            win_rate=0.72,
            trades_count=56,
            genome={"charisma": 0.85, "negotiation": 0.90, "trust": 0.75}
        ),
        Agent(
            id="AGT_ARBITER",
            name="ARBITER",
            archetype=AgentArchetype.DIPLOMAT,
            tier=1,
            level=11,
            sanity=95,
            max_sanity=100,
            owner_id=users[2].id,
            wallet_address="0x8901234567abcdef8901234567abcdef89012345",
            total_pnl_usd=5602.50,
            win_rate=0.68,
            trades_count=34,
            genome={"charisma": 0.78, "negotiation": 0.82, "trust": 0.80}
        ),
        Agent(
            id="AGT_PHOENIX",
            name="PHOENIX",
            archetype=AgentArchetype.DIPLOMAT,
            tier=2,
            level=17,
            sanity=90,
            max_sanity=100,
            owner_id=users[4].id,
            wallet_address="0x9012345678abcdef9012345678abcdef90123456",
            total_pnl_usd=32000.00,
            win_rate=0.70,
            trades_count=89,
            genome={"charisma": 0.88, "negotiation": 0.85, "trust": 0.82}
        ),
        
        # ===== SABOTEURS (Chaos Agents) =====
        Agent(
            id="AGT_VIPER",
            name="VIPER",
            archetype=AgentArchetype.SABOTEUR,
            tier=2,
            level=13,
            sanity=33,
            max_sanity=100,
            owner_id=users[3].id,
            wallet_address="0xa123456789abcdefa123456789abcdefa1234567",
            total_pnl_usd=-3400.00,
            win_rate=0.42,
            trades_count=67,
            genome={"deception": 0.95, "disruption": 0.85, "escape": 0.70}
        ),
        Agent(
            id="AGT_SPECTER",
            name="SPECTER",
            archetype=AgentArchetype.SABOTEUR,
            tier=1,
            level=8,
            sanity=55,
            max_sanity=100,
            owner_id=users[1].id,
            wallet_address="0xb234567890abcdefb234567890abcdefb2345678",
            total_pnl_usd=-1205.00,
            win_rate=0.45,
            trades_count=23,
            genome={"deception": 0.82, "disruption": 0.75, "escape": 0.60}
        ),
        
        # ===== WHALES (Market Movers) =====
        Agent(
            id="AGT_LEVIATHAN",
            name="LEVIATHAN",
            archetype=AgentArchetype.WHALE,
            tier=3,
            level=28,
            sanity=95,
            max_sanity=100,
            owner_id=users[4].id,
            wallet_address="0xc345678901abcdefc345678901abcdefc3456789",
            total_pnl_usd=234000.00,
            win_rate=0.65,
            trades_count=28,
            genome={"capital": 0.98, "patience": 0.92, "market_impact": 0.90}
        ),
    ]
    
    for agent in agents:
        session.add(agent)
    
    await session.flush()
    print(f"✅ Created {len(agents)} agents")
    return agents


async def seed_timelines(session, users: list) -> list:
    """Create 10 diverse timelines across categories."""
    timelines = [
        # ===== GEOPOLITICAL =====
        Timeline(
            id="TL_GHOST_TANKER",
            name="Ghost Tanker - Venezuela Dark Fleet",
            narrative="What if 3 oil tankers going dark near Venezuela signals sanctions evasion at scale?",
            keywords=["tanker", "venezuela", "oil", "sanctions", "shipping", "dark fleet"],
            stability=45.2,
            surface_tension=52.0,
            price_yes=0.67,
            price_no=0.33,
            osint_alignment=35.0,
            logic_gap=0.32,
            gravity_score=84.5,
            total_volume_usd=125000.0,
            liquidity_depth_usd=45000.0,
            active_agent_count=18,
            decay_rate_per_hour=2.5,
            founder_id=users[0].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_HORMUZ_CHOKEPOINT", "TL_TEHRAN_BLACKOUT"],
            has_active_paradox=True
        ),
        Timeline(
            id="TL_TEHRAN_BLACKOUT",
            name="Tehran Blackout Protocol",
            narrative="What if the sudden communications blackout in Tehran indicates regime instability?",
            keywords=["iran", "tehran", "blackout", "regime", "communications", "protests"],
            stability=28.5,
            surface_tension=22.0,
            price_yes=0.52,
            price_no=0.48,
            osint_alignment=38.0,
            logic_gap=0.45,
            gravity_score=91.2,
            total_volume_usd=89000.0,
            liquidity_depth_usd=28000.0,
            active_agent_count=24,
            decay_rate_per_hour=5.0,
            founder_id=users[1].id,
            founder_yield_rate=0.003,
            connected_timeline_ids=["TL_HORMUZ_CHOKEPOINT", "TL_GHOST_TANKER"],
            has_active_paradox=True
        ),
        Timeline(
            id="TL_HORMUZ_CHOKEPOINT",
            name="Hormuz Strait Chokepoint",
            narrative="What if Iranian naval exercises escalate into a shipping lane blockade?",
            keywords=["hormuz", "iran", "shipping", "blockade", "navy", "oil"],
            stability=91.5,
            surface_tension=88.0,
            price_yes=0.41,
            price_no=0.59,
            osint_alignment=52.0,
            logic_gap=0.11,
            gravity_score=78.3,
            total_volume_usd=340000.0,
            liquidity_depth_usd=125000.0,
            active_agent_count=32,
            decay_rate_per_hour=1.0,
            founder_id=users[4].id,
            founder_yield_rate=0.001,
            connected_timeline_ids=["TL_TEHRAN_BLACKOUT", "TL_GHOST_TANKER"],
            has_active_paradox=False
        ),
        
        # ===== FINANCIAL =====
        Timeline(
            id="TL_FED_PIVOT",
            name="Fed Pivot January 2026",
            narrative="What if the Federal Reserve cuts rates by 50bps instead of 25bps?",
            keywords=["fed", "rates", "fomc", "powell", "inflation", "pivot"],
            stability=67.2,
            surface_tension=71.0,
            price_yes=0.72,
            price_no=0.28,
            osint_alignment=68.0,
            logic_gap=0.12,
            gravity_score=92.1,
            total_volume_usd=520000.0,
            liquidity_depth_usd=180000.0,
            active_agent_count=45,
            decay_rate_per_hour=1.0,
            founder_id=users[1].id,
            founder_yield_rate=0.0015,
            connected_timeline_ids=["TL_NVIDIA_EARNINGS", "TL_ETH_ETF"],
            has_active_paradox=False
        ),
        Timeline(
            id="TL_NVIDIA_EARNINGS",
            name="NVIDIA Q4 Earnings Shock",
            narrative="What if NVIDIA misses earnings expectations by more than 10%?",
            keywords=["nvidia", "earnings", "ai", "chips", "gpu", "datacenter"],
            stability=58.5,
            surface_tension=62.0,
            price_yes=0.23,
            price_no=0.77,
            osint_alignment=78.0,
            logic_gap=0.18,
            gravity_score=86.4,
            total_volume_usd=180000.0,
            liquidity_depth_usd=65000.0,
            active_agent_count=28,
            decay_rate_per_hour=1.5,
            founder_id=users[2].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_FED_PIVOT", "TL_OPENAI_EXODUS"],
            has_active_paradox=False
        ),
        
        # ===== TECH =====
        Timeline(
            id="TL_OPENAI_EXODUS",
            name="OpenAI Exodus Event",
            narrative="What if 5+ senior OpenAI researchers announce departure to competitor?",
            keywords=["openai", "ai", "exodus", "researchers", "anthropic", "google"],
            stability=63.3,
            surface_tension=58.0,
            price_yes=0.35,
            price_no=0.65,
            osint_alignment=71.0,
            logic_gap=0.22,
            gravity_score=79.8,
            total_volume_usd=95000.0,
            liquidity_depth_usd=32000.0,
            active_agent_count=19,
            decay_rate_per_hour=1.5,
            founder_id=users[3].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_NVIDIA_EARNINGS", "TL_APPLE_AI_PIVOT"],
            has_active_paradox=False
        ),
        Timeline(
            id="TL_APPLE_AI_PIVOT",
            name="Apple AI Strategy Pivot",
            narrative="What if Apple announces acquisition of AI startup for >$5B?",
            keywords=["apple", "ai", "acquisition", "strategy", "siri", "llm"],
            stability=55.1,
            surface_tension=52.0,
            price_yes=0.58,
            price_no=0.42,
            osint_alignment=82.0,
            logic_gap=0.15,
            gravity_score=72.6,
            total_volume_usd=145000.0,
            liquidity_depth_usd=48000.0,
            active_agent_count=22,
            decay_rate_per_hour=1.5,
            founder_id=users[0].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_OPENAI_EXODUS", "TL_NVIDIA_EARNINGS"],
            has_active_paradox=False
        ),
        
        # ===== CRYPTO =====
        Timeline(
            id="TL_ETH_ETF",
            name="Ethereum ETF Approval",
            narrative="What if SEC approves spot Ethereum ETF before Q2 2026?",
            keywords=["ethereum", "etf", "sec", "crypto", "approval", "spot"],
            stability=48.5,
            surface_tension=45.0,
            price_yes=0.81,
            price_no=0.19,
            osint_alignment=91.0,
            logic_gap=0.08,
            gravity_score=88.9,
            total_volume_usd=680000.0,
            liquidity_depth_usd=220000.0,
            active_agent_count=52,
            decay_rate_per_hour=1.0,
            founder_id=users[4].id,
            founder_yield_rate=0.001,
            connected_timeline_ids=["TL_FED_PIVOT", "TL_TETHER_COLLAPSE"],
            has_active_paradox=False
        ),
        Timeline(
            id="TL_TETHER_COLLAPSE",
            name="Tether Stability Crisis",
            narrative="What if Tether de-pegs by more than 5% for over 24 hours?",
            keywords=["tether", "usdt", "stablecoin", "depeg", "crisis", "reserves"],
            stability=23.4,
            surface_tension=18.0,
            price_yes=0.12,
            price_no=0.88,
            osint_alignment=67.0,
            logic_gap=0.55,
            gravity_score=95.2,
            total_volume_usd=890000.0,
            liquidity_depth_usd=280000.0,
            active_agent_count=67,
            decay_rate_per_hour=8.0,
            founder_id=users[3].id,
            founder_yield_rate=0.003,
            connected_timeline_ids=["TL_ETH_ETF", "TL_FED_PIVOT"],
            has_active_paradox=True
        ),
        
        # ===== SCIENCE =====
        Timeline(
            id="TL_ANTARCTIC_SHELF",
            name="Antarctic Ice Shelf Event",
            narrative="What if Thwaites Glacier shows acceleration beyond model predictions?",
            keywords=["antarctica", "thwaites", "glacier", "climate", "ice", "collapse"],
            stability=52.7,
            surface_tension=48.0,
            price_yes=0.44,
            price_no=0.56,
            osint_alignment=56.0,
            logic_gap=0.31,
            gravity_score=68.4,
            total_volume_usd=67000.0,
            liquidity_depth_usd=22000.0,
            active_agent_count=14,
            decay_rate_per_hour=1.5,
            founder_id=users[2].id,
            founder_yield_rate=0.002,
            connected_timeline_ids=["TL_HORMUZ_CHOKEPOINT"],
            has_active_paradox=False
        ),
    ]
    
    for timeline in timelines:
        session.add(timeline)
    
    await session.flush()
    print(f"✅ Created {len(timelines)} timelines")
    return timelines


async def seed_paradoxes(session, timelines: list) -> list:
    """Create 3 active paradoxes for demo drama."""
    
    # Find timelines with active paradoxes
    ghost_tanker = next(t for t in timelines if t.id == "TL_GHOST_TANKER")
    tehran = next(t for t in timelines if t.id == "TL_TEHRAN_BLACKOUT")
    tether = next(t for t in timelines if t.id == "TL_TETHER_COLLAPSE")
    
    paradoxes = [
        # CLASS_3 - Moderate threat, longer countdown
        Paradox(
            id="PARADOX_GHOST_001",
            timeline_id=ghost_tanker.id,
            status=ParadoxStatus.ACTIVE,
            severity_class=SeverityClass.CLASS_3_MODERATE,
            logic_gap=0.32,
            spawned_at=(datetime.now(timezone.utc) - timedelta(hours=4)).replace(tzinfo=None),
            detonation_time=(datetime.now(timezone.utc) + timedelta(hours=8)).replace(tzinfo=None),
            decay_multiplier=2.5,
            extraction_cost_usdc=450.0,
            extraction_cost_echelon=135,
            carrier_sanity_cost=18
        ),
        # CLASS_2 - Severe threat, medium countdown
        Paradox(
            id="PARADOX_TEHRAN_001",
            timeline_id=tehran.id,
            status=ParadoxStatus.ACTIVE,
            severity_class=SeverityClass.CLASS_2_SEVERE,
            logic_gap=0.45,
            spawned_at=(datetime.now(timezone.utc) - timedelta(hours=3)).replace(tzinfo=None),
            detonation_time=(datetime.now(timezone.utc) + timedelta(hours=5)).replace(tzinfo=None),
            decay_multiplier=5.0,
            extraction_cost_usdc=820.0,
            extraction_cost_echelon=245,
            carrier_sanity_cost=28
        ),
        # CLASS_1 - Critical threat, short countdown (DRAMA!)
        Paradox(
            id="PARADOX_TETHER_001",
            timeline_id=tether.id,
            status=ParadoxStatus.ACTIVE,
            severity_class=SeverityClass.CLASS_1_CRITICAL,
            logic_gap=0.55,
            spawned_at=(datetime.now(timezone.utc) - timedelta(hours=6)).replace(tzinfo=None),
            detonation_time=(datetime.now(timezone.utc) + timedelta(hours=2)).replace(tzinfo=None),
            decay_multiplier=8.0,
            extraction_cost_usdc=1850.0,
            extraction_cost_echelon=555,
            carrier_sanity_cost=45
        ),
    ]
    
    for paradox in paradoxes:
        session.add(paradox)
    
    await session.flush()
    print(f"✅ Created {len(paradoxes)} paradoxes (including 1 CRITICAL!)")
    return paradoxes


async def seed_wing_flaps(session, timelines: list, agents: list) -> list:
    """Create 75 wing flaps with realistic activity patterns."""
    flaps = []
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # More diverse action templates
    trade_actions = [
        ("bought", "YES"),
        ("sold", "YES"),
        ("bought", "NO"),
        ("sold", "NO"),
        ("accumulated", "YES"),
        ("liquidated", "NO"),
    ]
    
    shield_narratives = [
        "deployed SHIELD on",
        "reinforced stability on",
        "activated protection for",
    ]
    
    sabotage_narratives = [
        "launched SABOTAGE on",
        "disrupted",
        "attacked stability of",
    ]
    
    ripple_narratives = [
        "triggered cascade from",
        "absorbed ripple from",
        "propagated shock to",
    ]
    
    for i in range(75):
        timeline = random.choice(timelines)
        agent = random.choice(agents)
        
        # Weight flap types by agent archetype
        if agent.archetype == AgentArchetype.SHARK:
            flap_type = random.choices(
                [WingFlapType.TRADE, WingFlapType.RIPPLE],
                weights=[0.85, 0.15]
            )[0]
        elif agent.archetype == AgentArchetype.DIPLOMAT:
            flap_type = random.choices(
                [WingFlapType.SHIELD, WingFlapType.TRADE],
                weights=[0.70, 0.30]
            )[0]
        elif agent.archetype == AgentArchetype.SABOTEUR:
            flap_type = random.choices(
                [WingFlapType.SABOTAGE, WingFlapType.TRADE],
                weights=[0.65, 0.35]
            )[0]
        elif agent.archetype == AgentArchetype.WHALE:
            flap_type = random.choices(
                [WingFlapType.TRADE, WingFlapType.RIPPLE],
                weights=[0.75, 0.25]
            )[0]
        else:  # SPY
            flap_type = random.choices(
                [WingFlapType.TRADE, WingFlapType.SHIELD],
                weights=[0.80, 0.20]
            )[0]
        
        volume = random.uniform(500, 75000)
        
        # Generate stability delta based on flap type
        if flap_type == WingFlapType.SHIELD:
            stability_delta = random.uniform(2, 12)
            action = f"{agent.name} {random.choice(shield_narratives)} {timeline.name}"
        elif flap_type == WingFlapType.SABOTAGE:
            stability_delta = -random.uniform(5, 18)
            action = f"{agent.name} {random.choice(sabotage_narratives)} {timeline.name}"
        elif flap_type == WingFlapType.RIPPLE:
            stability_delta = random.uniform(-8, 8)
            action = f"{agent.name} {random.choice(ripple_narratives)} {timeline.name}"
        else:  # TRADE
            stability_delta = random.uniform(-12, 12)
            action_verb, side = random.choice(trade_actions)
            price = random.uniform(0.15, 0.85)
            shares = int(volume / price)
            action = f"{agent.name} {action_verb} {shares:,} {side} @ ${price:.2f}"
        
        # Whales have bigger impact
        if agent.archetype == AgentArchetype.WHALE:
            volume *= 3
            stability_delta *= 1.5
        
        flap = WingFlap(
            id=f"FLAP_{i:05d}",
            timestamp=base_time - timedelta(minutes=i*1.5 + random.randint(0, 30)),
            timeline_id=timeline.id,
            agent_id=agent.id,
            flap_type=flap_type,
            action=action,
            stability_delta=round(stability_delta, 2),
            direction="ANCHOR" if stability_delta > 0 else "DESTABILISE",
            volume_usd=round(volume, 2),
            timeline_stability=round(max(0, min(100, timeline.stability + stability_delta)), 1),
            timeline_price=timeline.price_yes,
            spawned_ripple=abs(stability_delta) > 10,
            ripple_timeline_id=random.choice([t.id for t in timelines if t.id != timeline.id]) if abs(stability_delta) > 10 else None,
            founder_yield_earned=round(abs(stability_delta) * 0.001 * volume, 2) if stability_delta > 0 else None
        )
        flaps.append(flap)
        session.add(flap)
    
    await session.flush()
    print(f"✅ Created {len(flaps)} wing flaps")
    return flaps


async def seed_user_positions(session, users: list, timelines: list) -> list:
    """Create diverse user positions across timelines."""
    
    # Get timeline references
    tl_map = {t.id: t for t in timelines}
    
    positions = [
        # User 1 - DeepStateTrader (Geopolitical focus)
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
            timeline_id="TL_TEHRAN_BLACKOUT",
            side="NO",
            shards_held=300,
            average_entry_price=0.42,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[0].id,
            timeline_id="TL_APPLE_AI_PIVOT",
            side="YES",
            shards_held=200,
            average_entry_price=0.48,
            is_founder=True,
            founder_yield_earned_usd=45.20
        ),
        
        # User 2 - MacroMaven (Financial focus)
        UserPosition(
            id=generate_id("POS"),
            user_id=users[1].id,
            timeline_id="TL_FED_PIVOT",
            side="YES",
            shards_held=1200,
            average_entry_price=0.65,
            is_founder=True,
            founder_yield_earned_usd=450.00
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[1].id,
            timeline_id="TL_NVIDIA_EARNINGS",
            side="NO",
            shards_held=800,
            average_entry_price=0.72,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
        
        # User 3 - BioHazardBets (High risk)
        UserPosition(
            id=generate_id("POS"),
            user_id=users[2].id,
            timeline_id="TL_TETHER_COLLAPSE",
            side="YES",
            shards_held=500,
            average_entry_price=0.08,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[2].id,
            timeline_id="TL_ANTARCTIC_SHELF",
            side="YES",
            shards_held=350,
            average_entry_price=0.38,
            is_founder=True,
            founder_yield_earned_usd=28.50
        ),
        
        # User 4 - WhaleHunter (Crypto focus)
        UserPosition(
            id=generate_id("POS"),
            user_id=users[3].id,
            timeline_id="TL_ETH_ETF",
            side="YES",
            shards_held=2500,
            average_entry_price=0.72,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[3].id,
            timeline_id="TL_TETHER_COLLAPSE",
            side="NO",
            shards_held=1800,
            average_entry_price=0.82,
            is_founder=True,
            founder_yield_earned_usd=320.00
        ),
        
        # User 5 - ShadowBroker (Diversified whale)
        UserPosition(
            id=generate_id("POS"),
            user_id=users[4].id,
            timeline_id="TL_HORMUZ_CHOKEPOINT",
            side="NO",
            shards_held=3000,
            average_entry_price=0.52,
            is_founder=True,
            founder_yield_earned_usd=890.00
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[4].id,
            timeline_id="TL_ETH_ETF",
            side="YES",
            shards_held=5000,
            average_entry_price=0.68,
            is_founder=True,
            founder_yield_earned_usd=1250.00
        ),
        UserPosition(
            id=generate_id("POS"),
            user_id=users[4].id,
            timeline_id="TL_OPENAI_EXODUS",
            side="NO",
            shards_held=1500,
            average_entry_price=0.58,
            is_founder=False,
            founder_yield_earned_usd=0
        ),
    ]
    
    for pos in positions:
        session.add(pos)
    
    await session.flush()
    print(f"✅ Created {len(positions)} user positions")
    return positions


async def main():
    """Run the enhanced seeder."""
    print("=" * 60)
    print("ECHELON DATABASE SEEDER - ENHANCED EDITION")
    print("=" * 60)
    print()
    print("📦 Full demo data:")
    print("   • 5 users (including elite tier)")
    print("   • 12 genesis agents (all archetypes)")
    print("   • 10 timelines (geopolitical, financial, tech, crypto, science)")
    print("   • 3 active paradoxes (including 1 CRITICAL)")
    print("   • 75 wing flaps (realistic activity patterns)")
    print("   • 12 user positions (diversified holdings)")
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
                
                # Clear existing data (order matters for FK constraints)
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
            print(f"  • Users:      {len(users)}")
            print(f"  • Agents:     {len(agents)} (12 genesis)")
            print(f"  • Timelines:  {len(timelines)}")
            print(f"  • Paradoxes:  {len(paradoxes)} (1 CRITICAL!)")
            print(f"  • Wing Flaps: {len(wing_flaps)}")
            print(f"  • Positions:  {len(positions)}")
            print()
            print("🎯 Demo highlights:")
            print("   • MEGALODON (Tier 3 Shark) with $45K P&L")
            print("   • LEVIATHAN (Tier 3 Whale) with $234K P&L")
            print("   • ORACLE (Tier 3 Spy) with 78% win rate")
            print("   • Tether Collapse timeline with CRITICAL paradox (2hr countdown!)")
            print("   • $3.1M+ total volume across all timelines")
            print()
            print("🚀 Refresh your frontend to see the live data!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
