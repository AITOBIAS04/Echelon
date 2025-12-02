"""
Situation Room API Routes
=========================

FastAPI routes for the Situation Room frontend.
These endpoints power the React UI.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import engine and generators
try:
    from backend.core.situation_room_engine import SituationRoomEngine
    from backend.core.autouploader import SituationRoomAutoUploader, AutoUploadConfig, MODERATE_CONFIG
    from backend.core.synthetic_osint import SyntheticOSINTGenerator, SyntheticOSINTFeed
    from backend.core.narrative_war import NarrativeWarEngine
    from backend.core.models import AgentRole, Faction, MissionType, SpecialAbility
except ImportError:
    from core.situation_room_engine import SituationRoomEngine
    from core.autouploader import SituationRoomAutoUploader, AutoUploadConfig, MODERATE_CONFIG
    from core.synthetic_osint import SyntheticOSINTGenerator, SyntheticOSINTFeed
    from core.narrative_war import NarrativeWarEngine
    from core.models import AgentRole, Faction, MissionType, SpecialAbility

# =============================================================================
# INITIALIZE ENGINES (Singleton pattern)
# =============================================================================

# Global instances - in production, use dependency injection
_engine: Optional[SituationRoomEngine] = None
_uploader: Optional[SituationRoomAutoUploader] = None
_narrative_war: Optional[NarrativeWarEngine] = None
_synthetic_feed: Optional[SyntheticOSINTFeed] = None


def get_engine() -> SituationRoomEngine:
    global _engine
    if _engine is None:
        _engine = SituationRoomEngine()
    return _engine


def get_uploader() -> SituationRoomAutoUploader:
    global _uploader, _engine
    if _uploader is None:
        _uploader = SituationRoomAutoUploader(get_engine(), MODERATE_CONFIG)
    return _uploader


def get_narrative_war() -> NarrativeWarEngine:
    global _narrative_war
    if _narrative_war is None:
        _narrative_war = NarrativeWarEngine()
    return _narrative_war


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(prefix="/api/situation-room", tags=["Situation Room"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class MissionAcceptRequest(BaseModel):
    agent_id: str
    agent_role: str = "spy"


class AbilityUseRequest(BaseModel):
    agent_id: str
    ability: str
    target: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class IntelPurchaseRequest(BaseModel):
    buyer_id: str
    payment_usdc: float


class TreatyProposeRequest(BaseModel):
    proposer_agent_id: str
    proposer_faction: str
    target_faction: str
    terms: str
    escrow_amount: float = 100.0


class TreatyAcceptRequest(BaseModel):
    accepter_agent_id: str
    escrow_amount: float


class BetRequest(BaseModel):
    bettor_id: str
    amount: float
    bet_truth: bool


class ReportPublishRequest(BaseModel):
    agent_id: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    stance: str = "truth"


# =============================================================================
# GAME STATE ENDPOINTS
# =============================================================================

@router.get("/state")
async def get_game_state():
    """Get current Situation Room state"""
    engine = get_engine()
    narrative = get_narrative_war()
    
    state = engine.get_state_snapshot()
    state["narrative_war"] = narrative.get_narrative_state()
    
    return state


@router.get("/status")
async def get_status():
    """Get system status"""
    engine = get_engine()
    uploader = get_uploader()
    
    return {
        "status": "online",
        "tick_count": engine.tick_count,
        "uploader_stats": uploader.get_stats(),
        "missions_active": len([m for m in engine.missions.values() if m.status.value in ["pending", "active"]]),
        "last_tick": engine.last_tick.isoformat() if engine.last_tick else None,
    }


@router.post("/tick")
async def force_tick():
    """Force a game tick (for testing)"""
    engine = get_engine()
    await engine.tick()
    return {"message": "Tick executed", "tick_count": engine.tick_count}


# =============================================================================
# MISSION ENDPOINTS
# =============================================================================

@router.get("/missions")
async def get_missions(
    status: Optional[str] = None,
    mission_type: Optional[str] = None,
):
    """Get mission board"""
    engine = get_engine()
    missions = list(engine.missions.values())
    
    if status:
        missions = [m for m in missions if m.status.value == status]
    
    if mission_type:
        missions = [m for m in missions if m.mission_type.value == mission_type]
    
    return [m.to_dict() for m in missions]


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    """Get specific mission details"""
    engine = get_engine()
    mission = engine.missions.get(mission_id)
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return mission.to_dict()


@router.post("/missions/{mission_id}/accept")
async def accept_mission(mission_id: str, request: MissionAcceptRequest):
    """Accept a mission"""
    engine = get_engine()
    
    try:
        role = AgentRole(request.agent_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.agent_role}")
    
    success, message = await engine.assign_agent_to_mission(
        mission_id,
        request.agent_id,
        role
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.post("/missions/{mission_id}/complete/{objective_id}")
async def complete_objective(mission_id: str, objective_id: str, agent_id: str):
    """Complete a mission objective"""
    engine = get_engine()
    
    success, message = await engine.complete_mission_objective(
        mission_id,
        objective_id,
        agent_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


# =============================================================================
# INTEL MARKET ENDPOINTS
# =============================================================================

@router.get("/intel")
async def get_intel_packets():
    """Get available intel packets"""
    engine = get_engine()
    
    packets = [
        {
            "id": p.id,
            "encrypted_preview": p.encrypted_preview,
            "price_usdc": p.price_usdc,
            "creator_agent_id": p.creator_agent_id,
            "time_advantage_seconds": p.time_advantage_seconds,
            "times_purchased": p.times_purchased,
            "is_active": p.is_active,
        }
        for p in engine.intel_market.packets.values()
        if p.is_active
    ]
    
    return packets


@router.post("/intel/{packet_id}/purchase")
async def purchase_intel(packet_id: str, request: IntelPurchaseRequest):
    """Purchase an intel packet"""
    engine = get_engine()
    
    success, result = engine.intel_market.purchase_intel(
        packet_id,
        request.buyer_id,
        request.payment_usdc
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=result)
    
    return {"success": True, "content": result}


@router.get("/intel/leaderboard")
async def get_spy_leaderboard():
    """Get top spy agents by intel quality"""
    engine = get_engine()
    return engine.intel_market.get_spy_leaderboard()


# =============================================================================
# TREATY ENDPOINTS
# =============================================================================

@router.get("/treaties")
async def get_treaties(active_only: bool = True):
    """Get treaties"""
    engine = get_engine()
    
    if active_only:
        treaties = engine.treaty_system.get_active_treaties()
    else:
        treaties = list(engine.treaty_system.treaties.values())
    
    return [
        {
            "id": t.id,
            "treaty_name": t.treaty_name,
            "party_a_faction": t.party_a_faction.value,
            "party_b_faction": t.party_b_faction.value,
            "total_escrow": t.total_escrow,
            "tension_threshold": t.tension_threshold,
            "is_active": t.is_active,
            "is_violated": t.is_violated,
            "terms": t.terms,
        }
        for t in (treaties if isinstance(treaties[0] if treaties else None, dict) is False else 
                 [engine.treaty_system.treaties[t["id"]] for t in treaties])
    ] if treaties else []


@router.post("/treaties/propose")
async def propose_treaty(request: TreatyProposeRequest):
    """Propose a new treaty"""
    engine = get_engine()
    
    try:
        proposer_faction = Faction(request.proposer_faction)
        target_faction = Faction(request.target_faction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    treaty = engine.treaty_system.propose_treaty(
        request.proposer_agent_id,
        proposer_faction,
        target_faction,
        request.terms,
        request.escrow_amount
    )
    
    return {"success": True, "treaty_id": treaty.id}


@router.post("/treaties/{treaty_id}/accept")
async def accept_treaty(treaty_id: str, request: TreatyAcceptRequest):
    """Accept a proposed treaty"""
    engine = get_engine()
    
    success, message = engine.treaty_system.accept_treaty(
        treaty_id,
        request.accepter_agent_id,
        request.escrow_amount
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


# =============================================================================
# NARRATIVE ARC ENDPOINTS
# =============================================================================

@router.get("/narratives")
async def get_narratives():
    """Get active narrative arcs"""
    engine = get_engine()
    
    return [
        {
            "id": arc.id,
            "title": arc.title,
            "synopsis": arc.synopsis,
            "theme": arc.theme,
            "current_chapter": arc.current_chapter,
            "total_chapters": arc.total_chapters,
            "possible_endings": arc.possible_endings,
            "current_ending_trajectory": arc.current_ending_trajectory,
        }
        for arc in engine.narrative_arcs.values()
    ]


# =============================================================================
# SLEEPER CELL ENDPOINTS
# =============================================================================

@router.get("/mole/mystery")
async def get_mole_mystery():
    """Get current 'Who is the Mole?' market"""
    engine = get_engine()
    
    # Get active sleeper assignments (without revealing who it is!)
    active_assignments = [
        a for a in engine.sleeper_system.assignments.values()
        if not a.is_revealed
    ]
    
    return {
        "active": len(active_assignments) > 0,
        "season": engine.sleeper_system.current_season,
        "mole_revealed": engine.sleeper_system.mole_revealed,
        "hint": "One agent is not who they appear to be..." if active_assignments else None,
    }


@router.get("/mole/suspects")
async def get_mole_suspects():
    """Get list of potential mole suspects"""
    engine = get_engine()
    
    # Return all agent IDs that could be the mole (not the actual mole)
    # In production, this would be based on active agents
    suspects = list(engine.agent_stats.keys())[:10]
    
    return {
        "suspects": suspects,
        "market_open": not engine.sleeper_system.mole_revealed,
    }


# =============================================================================
# ABILITY ENDPOINTS
# =============================================================================

@router.post("/ability/use")
async def use_ability(request: AbilityUseRequest):
    """Use an agent ability"""
    engine = get_engine()
    
    try:
        ability = SpecialAbility(request.ability)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid ability: {request.ability}")
    
    success, result = await engine.use_ability(
        request.agent_id,
        ability,
        request.target,
        request.context or {}
    )
    
    return {"success": success, "result": result}


# =============================================================================
# NARRATIVE WAR ENDPOINTS
# =============================================================================

@router.get("/narrative-war/state")
async def get_narrative_war_state():
    """Get Narrative War state"""
    narrative = get_narrative_war()
    return narrative.get_narrative_state()


@router.get("/narrative-war/leaderboard")
async def get_narrative_leaderboard(role: Optional[str] = None):
    """Get Narrative War reputation leaderboard"""
    narrative = get_narrative_war()
    
    if role:
        try:
            role_enum = AgentRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        return narrative.get_leaderboard(role_enum)
    
    return narrative.get_leaderboard()


@router.get("/narrative-war/truth-markets")
async def get_truth_markets(resolved: bool = False):
    """Get Truth vs Hype betting markets"""
    narrative = get_narrative_war()
    
    markets = [
        {
            "id": m.id,
            "headline": m.headline,
            "truth_pool": m.truth_pool,
            "hype_pool": m.hype_pool,
            "truth_probability": m.truth_probability,
            "is_resolved": m.is_resolved,
            "outcome": m.actual_outcome,
        }
        for m in narrative.truth_markets.values()
        if m.is_resolved == resolved or not resolved
    ]
    
    return markets


@router.post("/narrative-war/truth-markets/{market_id}/bet")
async def bet_on_truth_market(market_id: str, request: BetRequest):
    """Place a bet on a Truth vs Hype market"""
    narrative = get_narrative_war()
    
    success, message = narrative.bet_on_truth(
        market_id,
        request.bettor_id,
        request.amount,
        request.bet_truth
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


# =============================================================================
# SYNTHETIC OSINT ENDPOINTS (For Testing)
# =============================================================================

@router.post("/test/inject-signal")
async def inject_test_signal(
    category: str = "geopolitical",
    high_urgency: bool = False
):
    """Inject a synthetic test signal"""
    try:
        from backend.core.mission_generator import SignalCategory
    except ImportError:
        from core.mission_generator import SignalCategory
    
    engine = get_engine()
    uploader = get_uploader()
    generator = SyntheticOSINTGenerator()
    
    try:
        cat = SignalCategory(category)
    except ValueError:
        cat = SignalCategory.GEOPOLITICAL
    
    signal = generator.generate_signal(category=cat, force_high_urgency=high_urgency)
    await uploader.process_signal(signal)
    
    return {
        "success": True,
        "signal_id": signal.id,
        "headline": signal.headline,
        "urgency": signal.urgency,
        "virality": signal.virality_score,
    }


@router.post("/test/inject-crisis")
async def inject_crisis(scenario: str = "taiwan"):
    """Inject a crisis scenario (multiple related signals)"""
    engine = get_engine()
    uploader = get_uploader()
    generator = SyntheticOSINTGenerator()
    
    signals = generator.generate_crisis_scenario(scenario)
    
    for signal in signals:
        await uploader.process_signal(signal)
    
    return {
        "success": True,
        "scenario": scenario,
        "signals_injected": len(signals),
    }


@router.post("/test/inject-mystery")
async def inject_mystery():
    """Inject a 'Who Killed X?' mystery event"""
    engine = get_engine()
    uploader = get_uploader()
    generator = SyntheticOSINTGenerator()
    
    signal = generator.generate_mystery_event()
    await uploader.process_signal(signal)
    
    return {
        "success": True,
        "signal_id": signal.id,
        "headline": signal.headline,
    }


# =============================================================================
# BACKGROUND TASK: AUTO-UPLOADER
# =============================================================================

async def start_synthetic_feed(background_tasks: BackgroundTasks):
    """Start the synthetic OSINT feed in background"""
    global _synthetic_feed
    
    _synthetic_feed = SyntheticOSINTFeed(
        signals_per_minute=1.0,
        chaos_level=0.5,
        include_crises=True,
        crisis_probability=0.05,
    )
    
    uploader = get_uploader()
    
    async def feed_loop():
        async for signal in _synthetic_feed.stream():
            await uploader.process_signal(signal)
    
    background_tasks.add_task(feed_loop)


@router.post("/test/start-feed")
async def start_feed(background_tasks: BackgroundTasks):
    """Start synthetic OSINT feed (for demo mode)"""
    await start_synthetic_feed(background_tasks)
    return {"message": "Synthetic feed started"}


@router.post("/test/stop-feed")
async def stop_feed():
    """Stop synthetic OSINT feed"""
    global _synthetic_feed
    if _synthetic_feed:
        _synthetic_feed.stop()
    return {"message": "Synthetic feed stopped"}


# =============================================================================
# EXPORT ROUTER
# =============================================================================

def include_router(app):
    """Include this router in a FastAPI app"""
    app.include_router(router)


# For direct testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Situation Room API")
    app.include_router(router)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

