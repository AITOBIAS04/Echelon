"""
Phoenix Protocol - Genesis Task
Ensures the simulation never dies by maintaining minimum timeline count.
"From the ashes of collapsed timelines, new realities emerge."
"""

import random
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Timeline, Agent, WingFlap
from backend.database.connection import get_async_session

logger = logging.getLogger(__name__)

# Narrative Deck - Templates for spawning new timelines
SCENARIO_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "TL_GHOST_TANKER",
        "name": "Ghost Tanker - Venezuela Dark Fleet",
        "narrative": "What if 3 oil tankers went dark near Venezuelan waters?",
        "keywords": ["oil", "tanker", "venezuela", "sanctions", "shipping"],
        "base_stability": 72.0,
        "price_yes": 0.45,
    },
    {
        "id": "TL_FED_RATE",
        "name": "Fed Rate Decision - Emergency Cut",
        "narrative": "What if the Fed announced an emergency 50bp rate cut?",
        "keywords": ["fed", "rates", "economy", "markets", "powell"],
        "base_stability": 78.0,
        "price_yes": 0.62,
    },
    {
        "id": "TL_CONTAGION",
        "name": "Contagion Zero - Unknown Pathogen",
        "narrative": "What if WHO detected an unknown respiratory illness cluster?",
        "keywords": ["health", "outbreak", "WHO", "pandemic", "virus"],
        "base_stability": 65.0,
        "price_yes": 0.38,
    },
    {
        "id": "TL_OIL_CRISIS",
        "name": "Oil Crisis - Hormuz Strait",
        "narrative": "What if Iran closed the Strait of Hormuz?",
        "keywords": ["oil", "iran", "hormuz", "energy", "geopolitics"],
        "base_stability": 58.0,
        "price_yes": 0.55,
    },
    {
        "id": "TL_SILICON_ACQ",
        "name": "Silicon Acquisition - Tech Giant Move",
        "narrative": "What if Apple announced a major AI company acquisition?",
        "keywords": ["apple", "acquisition", "AI", "tech", "stocks"],
        "base_stability": 82.0,
        "price_yes": 0.72,
    },
    {
        "id": "TL_CRYPTO_CRASH",
        "name": "Crypto Cascade - Exchange Failure",
        "narrative": "What if a top-5 exchange halted withdrawals?",
        "keywords": ["crypto", "exchange", "bitcoin", "withdrawal", "panic"],
        "base_stability": 45.0,
        "price_yes": 0.28,
    },
    {
        "id": "TL_REGIME_CHANGE",
        "name": "Regime Change - Palace Lights Dark",
        "narrative": "What if satellite imagery showed unusual activity at a major capital?",
        "keywords": ["coup", "government", "military", "palace", "intelligence"],
        "base_stability": 52.0,
        "price_yes": 0.35,
    },
    {
        "id": "TL_CLIMATE_EVENT",
        "name": "Climate Shock - Category 6",
        "narrative": "What if a hurricane exceeded all existing categories?",
        "keywords": ["hurricane", "climate", "disaster", "evacuation", "FEMA"],
        "base_stability": 68.0,
        "price_yes": 0.42,
    },
]

# Minimum timelines to maintain
MIN_ACTIVE_TIMELINES = 4
MAX_SPAWN_PER_CYCLE = 2


async def phoenix_protocol(session: AsyncSession) -> Dict[str, Any]:
    """
    The Phoenix Protocol - Ensures simulation never dies.
    
    Checks active timeline count and spawns new ones if below threshold.
    Returns stats about what was done.
    """
    result = {
        "checked": True,
        "active_count": 0,
        "spawned": 0,
        "spawned_timelines": [],
    }
    
    try:
        # 1. Count active timelines (stability > 0)
        count_query = select(func.count(Timeline.id)).where(
            Timeline.stability > 0,
            Timeline.status == "ACTIVE"
        )
        active_count = await session.scalar(count_query) or 0
        result["active_count"] = active_count
        
        # 2. Check if we're below minimum
        if active_count >= MIN_ACTIVE_TIMELINES:
            logger.debug(f"Phoenix: {active_count} active timelines. All stable.")
            return result
        
        # 3. Calculate deficit
        deficit = MIN_ACTIVE_TIMELINES - active_count
        spawn_count = min(deficit, MAX_SPAWN_PER_CYCLE)
        
        logger.warning(f"🔥 PHOENIX PROTOCOL ACTIVATED: Only {active_count} timelines active. Spawning {spawn_count}...")
        
        # 4. Get existing timeline IDs to avoid duplicates
        existing_query = select(Timeline.id)
        existing_result = await session.execute(existing_query)
        existing_ids = {row[0] for row in existing_result.fetchall()}
        
        # 5. Find available scenarios (not already active)
        available_scenarios = [
            s for s in SCENARIO_TEMPLATES 
            if s["id"] not in existing_ids
        ]
        
        # If all scenarios exist, create variants
        if not available_scenarios:
            available_scenarios = SCENARIO_TEMPLATES.copy()
        
        random.shuffle(available_scenarios)
        
        # 6. Spawn new timelines
        for i in range(spawn_count):
            if i >= len(available_scenarios):
                break
                
            scenario = available_scenarios[i]
            timeline_id = scenario["id"]
            
            # Add suffix if timeline ID already exists
            if timeline_id in existing_ids:
                suffix = datetime.now(timezone.utc).strftime("%H%M")
                timeline_id = f"{scenario['id']}_{suffix}"
            
            # Add randomness to stability (±10%)
            stability_variance = random.uniform(-10, 10)
            stability = max(20, min(95, scenario["base_stability"] + stability_variance))
            
            # Create the timeline
            new_timeline = Timeline(
                id=timeline_id,
                name=scenario["name"],
                narrative=scenario["narrative"],
                keywords=scenario["keywords"],
                stability=stability,
                surface_tension=random.uniform(40, 70),
                price_yes=scenario["price_yes"],
                price_no=1.0 - scenario["price_yes"],
                total_volume_usd=random.uniform(10000, 50000),
                liquidity_depth_usd=random.uniform(5000, 25000),
                osint_alignment=scenario["price_yes"] * 100,
                logic_gap=random.uniform(0.05, 0.25),
                gravity_score=random.uniform(50, 80),
                active_agent_count=random.randint(5, 20),
                decay_rate_per_hour=1.0,
                has_active_paradox=False,
                status="ACTIVE",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(new_timeline)
            result["spawned_timelines"].append(timeline_id)
            
            # Create a GENESIS wing flap
            genesis_flap = WingFlap(
                timeline_id=timeline_id,
                flap_type="GENESIS",
                agent_id=None,
                action=f"Phoenix Protocol: {scenario['name']} emerged from the void",
                stability_delta=stability,
                direction="ANCHOR",
                volume_usd=0,
                timeline_stability=stability,
                timeline_price=scenario["price_yes"],
                spawned_ripple=False,
                created_at=datetime.now(timezone.utc),
            )
            session.add(genesis_flap)
            
            logger.info(f"  🌅 Spawned: {timeline_id} (stability: {stability:.1f}%)")
        
        await session.commit()
        result["spawned"] = len(result["spawned_timelines"])
        
        logger.info(f"🔥 Phoenix complete: Spawned {result['spawned']} new timelines")
        
    except Exception as e:
        logger.error(f"Phoenix Protocol error: {e}")
        await session.rollback()
        raise
    
    return result


async def run_genesis_task():
    """Entry point for the game loop to call."""
    async for session in get_async_session():
        return await phoenix_protocol(session)

