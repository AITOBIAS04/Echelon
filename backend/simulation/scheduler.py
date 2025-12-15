"""
Three-Tier Scheduler for Project Seed (PolyGlobe Edition)
=========================================================
Now integrated with OSINT Registry for automated mission generation.
"""

import logging

# Suppress noisy HTTP logs so we can see our own "Orchestra" logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

import asyncio
import json
import os
import signal
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# --- IMPORTS ---
from backend.simulation.world_state import WorldState
from backend.agents.autonomous_agent import GeopoliticalAgent
from backend.simulation.yield_manager import YieldManager
from backend.simulation.genome import AgentGenome
from backend.simulation.timeline_manager import TimelineManager
from backend.core.event_orchestrator import EventOrchestrator, RawEvent, EventDomain
from backend.core.osint_registry import get_osint_registry

# Fixed file path
STATE_FILE = os.path.join(os.path.dirname(__file__), "world_state.json")

# --- CONFIGURATION ---
class SchedulerConfig:
    MICRO_TICK_RATE = 10      # 10s: Yields
    NARRATIVE_TICK_RATE = 60  # 60s: News & OSINT Scans
    MACRO_TICK_RATE = 300     # 5m: Evolution

async def load_state() -> WorldState:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            
            # SAFETY CLAMP: Fix invalid values before Pydantic validation
            if "global_tension" in data:
                val = float(data["global_tension"])
                data["global_tension"] = min(1.0, max(0.0, val))
                
            # Handle legacy migration
            if "global_tension" not in data:
                data["global_tension"] = data.get("global_tension_score", 0.5)
            if "recent_reasoning" not in data:
                data["recent_reasoning"] = "System initialized."
            if "event_log" not in data:
                data["event_log"] = []
            
            return WorldState(**data)
        except Exception as e:
            print(f"⚠️ State load error: {e}. Resetting to default.")
            return WorldState(global_tension=0.0)
            
    return WorldState(global_tension=0.0)

async def save_state(state: WorldState):
    with open(STATE_FILE, "w") as f:
        f.write(state.model_dump_json(indent=2))

async def game_loop():
    print("=" * 60)
    print("🌍 POLYGLOBE ENGINE: ONLINE")
    print("=" * 60)
    
    # Initialize Systems
    agent = GeopoliticalAgent(agent_id="Director_AI", genome=AgentGenome(
        aggression=0.5, deception=0.5, risk_tolerance=0.5, 
        archetype="Director", speech_style="Formal", secret_objective="SURVIVE"
    ))
    yield_manager = YieldManager()
    timeline_manager = TimelineManager()
    event_orchestrator = EventOrchestrator()
    osint_registry = get_osint_registry() # <--- NEW: The Spy Network
    
    last_micro = 0
    last_narrative = 0
    last_macro = 0
    
    while True:
        now = time.time()
        
        # --- TIER 1: MICRO TICK ---
        if now - last_micro >= SchedulerConfig.MICRO_TICK_RATE:
            yield_manager.distribute_yield()
            last_micro = now
        
        # --- TIER 2: NARRATIVE TICK (The War Room) ---
        if now - last_narrative >= SchedulerConfig.NARRATIVE_TICK_RATE:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{timestamp}] 📡 SCANNING FREQUENCIES...")
            
            # 1. Run OSINT Scan (The "Pizzint" Check)
            signals = await osint_registry.scan_all()
            if signals:
                print(f"   🚨 {len(signals)} Signals Detected across {len(osint_registry.active_signals)} active tracks")
            
            # 2. Generate Missions (Markets) from Signals
            # We check all domains for critical alerts
            for domain in ["geopolitics", "financial", "sports"]:
                missions = osint_registry.generate_domain_missions(domain)
                
                for mission in missions:
                    print(f"   🎯 MISSION GENERATED: {mission.title}")
                    
                    # Convert Mission to Event for Market Creation
                    domain_enum = {
                        "geopolitics": EventDomain.GEOPOLITICS,
                        "financial": EventDomain.FINANCE,
                        "sports": EventDomain.SPORTS
                    }.get(domain, EventDomain.UNKNOWN)
                    
                    mission_event = RawEvent(
                        id=mission.id,
                        title=f"⚠️ {mission.title}", # Add alert icon
                        description=mission.description,
                        source="OSINT_NETWORK",
                        url="internal://classified",
                        published_at=datetime.now(timezone.utc),
                        domain=domain_enum,
                        virality_score=mission.virality_score,
                        sentiment=-0.8 # Missions usually imply tension
                    )
                    
                    # Auto-create market for this mission
                    market = event_orchestrator.create_market(mission_event)
                    event_orchestrator.dispatch_agents(market)
            
            # 3. Agent Decision (Director AI)
            current_state = await load_state()
            
            # Feed OSINT status into the Agent's context
            osint_status = osint_registry.get_full_status()
            defcon = osint_status['defcon_name']
            
            # Update state with threat level
            if defcon == "DEFCON_1" or defcon == "DEFCON_2":
                # STRICT CLAMP: Never exceed 1.0
                current_state.global_tension = min(1.0, current_state.global_tension + 0.1)
            
            print(f"   🧠 Director analyzing intel (Threat Level: {defcon})...")
            decision = await agent.think(current_state, mode="routine")
            
            # Update & Save
            new_tension = decision.get("new_tension", current_state.global_tension)
            # Ensure we strictly clamp to [0.0, 1.0]
            current_state.global_tension = min(1.0, max(0.0, float(new_tension)))
            current_state.recent_reasoning = decision.get("reasoning", "Analyzing signals.")
            current_state.last_updated = datetime.now()
            await save_state(current_state)
            
            last_narrative = now
        
        # --- TIER 3: MACRO TICK ---
        if now - last_macro >= SchedulerConfig.MACRO_TICK_RATE:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🏛️ MACRO SYNCHRONIZATION")
            timeline_manager.cleanup_old_forks()
            last_macro = now
            
        await asyncio.sleep(1)

if __name__ == "__main__":
    def handle_shutdown(signum, frame):
        print("\n🛑 Shutting down...")
        raise SystemExit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    asyncio.run(game_loop())
