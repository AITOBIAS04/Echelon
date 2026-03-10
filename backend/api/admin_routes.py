"""
Admin/Demo endpoints for controlling the simulation.
God Mode: Trigger events on demand for demos and testing.
"""

import random
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.connection import get_db as get_async_session
from backend.database.models import (
    Timeline, Paradox, WingFlap, Agent, User, UserPosition,
    WingFlapType, FlapDirection,
)
from backend.worker.tasks.genesis import phoenix_protocol, SCENARIO_TEMPLATES
from backend.scripts.seed_database import (
    seed_users,
    seed_agents,
    seed_timelines,
    seed_paradoxes,
    seed_wing_flaps,
    seed_user_positions,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)

async def _get_any_agent_id(session: AsyncSession) -> Optional[str]:
    """Fetch any agent ID to satisfy FK constraints on wing flaps."""
    result = await session.execute(select(Agent.id).limit(1))
    return result.scalar_one_or_none()


@router.post("/inject-chaos")
async def inject_chaos(
    timeline_id: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    GOD MODE: Instantly spawn a Paradox in a timeline.
    If no timeline_id provided, targets the top timeline by gravity.
    """
    # Find target timeline
    if timeline_id:
        query = select(Timeline).where(Timeline.id == timeline_id)
    else:
        query = (
            select(Timeline)
            .where(
                Timeline.stability > 0,
                Timeline.has_active_paradox == False,
            )
            .order_by(Timeline.gravity_score.desc())
            .limit(1)
        )
    
    result = await session.execute(query)
    timeline = result.scalar_one_or_none()
    
    if not timeline:
        raise HTTPException(status_code=404, detail="No eligible timeline found")
    
    # Create the Paradox
    paradox = Paradox(
        timeline_id=timeline.id,
        severity_class="CLASS_2_SEVERE",
        logic_gap=0.55,
        status="ACTIVE",
        decay_multiplier=3.0,
        extraction_cost_usdc=500.0,
        extraction_cost_echelon=100.0,
        carrier_sanity_cost=15.0,
    )
    session.add(paradox)
    
    # Update timeline (0-1 scale)
    timeline.has_active_paradox = True
    timeline.stability = max(0.20, timeline.stability - 0.15)

    # Create wing flap
    agent_id = await _get_any_agent_id(session)
    if agent_id:
        flap_id = f"ADMIN_CHAOS_{timeline.id}_{uuid.uuid4().hex[:8]}"
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=timeline.id,
            agent_id=agent_id,
            flap_type=WingFlapType.PARADOX,
            action=f"GOD MODE: Paradox injected into {timeline.name}",
            stability_delta=-0.15,
            direction=FlapDirection.DESTABILISE.value,
            volume_usd=0.0,
            timeline_stability=timeline.stability,
            timeline_price=timeline.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
    
    await session.commit()
    
    return {
        "success": True,
        "message": f"Chaos injected into {timeline.id}",
        "timeline": timeline.name,
        "new_stability": timeline.stability,
        "paradox_severity": "CLASS_2_SEVERE",
    }


@router.post("/spawn-timeline")
async def spawn_timeline(
    scenario_id: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    GOD MODE: Manually spawn a new timeline.
    """
    result = await phoenix_protocol(session)
    return {
        "success": True,
        "spawned": result["spawned"],
        "timelines": result["spawned_timelines"],
    }


@router.post("/heal-timeline/{timeline_id}")
async def heal_timeline(
    timeline_id: str,
    stability_boost: float = 0.30,
    session: AsyncSession = Depends(get_async_session)
):
    """
    GOD MODE: Boost a timeline's stability.
    stability_boost is on 0-1 scale (default 0.30 = +30%).
    """
    query = select(Timeline).where(Timeline.id == timeline_id)
    result = await session.execute(query)
    timeline = result.scalar_one_or_none()

    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")

    old_stability = timeline.stability
    timeline.stability = min(1.0, timeline.stability + stability_boost)

    # Create wing flap
    agent_id = await _get_any_agent_id(session)
    if agent_id:
        flap_id = f"ADMIN_HEAL_{timeline.id}_{uuid.uuid4().hex[:8]}"
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=timeline.id,
            agent_id=agent_id,
            flap_type=WingFlapType.SHIELD,
            action=f"GOD MODE: Divine intervention (+{stability_boost:.0%} stability)",
            stability_delta=stability_boost,
            direction=FlapDirection.STABILISE.value,
            volume_usd=0.0,
            timeline_stability=timeline.stability,
            timeline_price=timeline.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
    
    await session.commit()
    
    return {
        "success": True,
        "timeline": timeline_id,
        "old_stability": old_stability,
        "new_stability": timeline.stability,
    }


@router.post("/reseed")
async def reseed_database(
    session: AsyncSession = Depends(get_async_session)
):
    """
    GOD MODE: Reseed the entire database.
    WARNING: This clears existing data!
    """
    # Clear existing data
    await session.execute(WingFlap.__table__.delete())
    await session.execute(Paradox.__table__.delete())
    await session.execute(UserPosition.__table__.delete())
    await session.execute(Agent.__table__.delete())
    await session.execute(Timeline.__table__.delete())
    await session.execute(User.__table__.delete())
    await session.commit()

    # Seed fresh data
    users = await seed_users(session)
    agents = await seed_agents(session, users)
    timelines = await seed_timelines(session, users)
    paradoxes = await seed_paradoxes(session, timelines)
    wing_flaps = await seed_wing_flaps(session, timelines, agents)
    positions = await seed_user_positions(session, users, timelines)

    await session.commit()

    # Also seed all template families (sync seeders — idempotent)
    scenario_count = 0
    investigation_count = 0
    theatre_tpl_count = 0
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as SyncSession
        from backend.database.config import DatabaseConfig
        sync_url = DatabaseConfig.SYNC_DATABASE_URL
        sync_engine = create_engine(sync_url)
        with SyncSession(sync_engine) as sync_session:
            from backend.services.scenario_template_seeder import seed_templates
            scenario_count = seed_templates(sync_session)
        with SyncSession(sync_engine) as sync_session:
            from backend.services.investigation_template_seeder import seed_investigation_templates
            investigation_count = seed_investigation_templates(sync_session)
        with SyncSession(sync_engine) as sync_session:
            from backend.services.theatre_template_seeder import seed_theatre_templates
            theatre_tpl_count = seed_theatre_templates(sync_session)
        sync_engine.dispose()
    except Exception as e:
        logger.warning("Could not seed templates during reseed: %s", e)

    return {
        "success": True,
        "message": "Database reseeded",
        "summary": {
            "users": len(users),
            "agents": len(agents),
            "timelines": len(timelines),
            "paradoxes": len(paradoxes),
            "wing_flaps": len(wing_flaps),
            "positions": len(positions),
            "scenario_templates": scenario_count,
            "investigation_templates": investigation_count,
            "theatre_templates": theatre_tpl_count,
        },
    }


@router.get("/status")
async def simulation_status(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get current simulation status for admin dashboard.
    """
    timeline_count = await session.scalar(
        select(func.count(Timeline.id)).where(Timeline.stability > 0)
    )
    paradox_count = await session.scalar(
        select(func.count(Paradox.id)).where(Paradox.status == "ACTIVE")
    )
    
    return {
        "active_timelines": timeline_count,
        "active_paradoxes": paradox_count,
        "min_timelines_threshold": 4,
        "phoenix_would_trigger": timeline_count < 4,
    }
