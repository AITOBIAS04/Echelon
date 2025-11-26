"""
Three-Tier Scheduler for Project Seed
======================================
The "Living Engine" orchestrator that runs the simulation.

Architecture:
- MICRO TICK (10s): Price updates, yield distribution
- NARRATIVE TICK (60s): News checks, agent reactions, virality detection
- MACRO TICK (300s): Season end, evolution, batch jobs

Features:
- Automatic virality detection and fork triggering
- Multi-domain simulation coordination
- Graceful shutdown handling
- State persistence
"""

import asyncio
import json
import os
import signal
import time
from datetime import datetime
from typing import Optional, Dict, Any

# --- IMPORTS ---
# Use try/except for flexible import paths
try:
    from backend.simulation.world_state import WorldState
    from backend.agents.autonomous_agent import GeopoliticalAgent
    from backend.simulation.yield_manager import YieldManager
    from backend.simulation.genome import AgentGenome
    from backend.simulation.timeline_manager import TimelineManager
    from backend.core.event_orchestrator import EventOrchestrator, ViralityConfig
except ImportError:
    from simulation.world_state import WorldState
    from agents.autonomous_agent import GeopoliticalAgent
    from simulation.yield_manager import YieldManager
    from simulation.genome import AgentGenome
    from simulation.timeline_manager import TimelineManager
    try:
        from core.event_orchestrator import EventOrchestrator, ViralityConfig
    except ImportError:
        EventOrchestrator = None
        ViralityConfig = None

# Fixed file path using relative location
STATE_FILE = os.path.join(os.path.dirname(__file__), "world_state.json")




# =============================================================================
# CONFIGURATION
# =============================================================================

class SchedulerConfig:
    """Scheduler timing configuration."""
    
    # Tick rates in seconds
    MICRO_TICK_RATE = 10      # Fast: prices, yields
    NARRATIVE_TICK_RATE = 60  # Medium: news, reactions (1 min for dev, 6hr for prod)
    MACRO_TICK_RATE = 300     # Slow: seasons, evolution (5 min for dev, 24hr for prod)
    
    # Virality threshold for auto-forking
    VIRALITY_FORK_THRESHOLD = 75
    
    # Max concurrent forks
    MAX_ACTIVE_FORKS = 5




# =============================================================================
# STATE MANAGEMENT
# =============================================================================

async def load_state() -> WorldState:
    """Loads state from JSON or creates default."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        
        # Handle migration from old format to new format
        if "global_tension" not in data:
            data["global_tension"] = data.get("global_tension_score", 0.5)
            data["recent_reasoning"] = "Migrated from old world state format."
            data["event_log"] = []
        
        # Handle legacy string dates if they exist
        if isinstance(data.get("last_updated"), str):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        elif "last_updated" not in data:
            data["last_updated"] = datetime.now()
        
        # Ensure required fields exist
        if "recent_reasoning" not in data:
            data["recent_reasoning"] = "System initialized."
        if "event_log" not in data:
            data["event_log"] = []
        
        return WorldState(**data)
    return WorldState(global_tension=0.0)




async def save_state(state: WorldState):
    """Dumps Pydantic model to JSON."""
    with open(STATE_FILE, "w") as f:
        f.write(state.model_dump_json(indent=2))




# =============================================================================
# VIRALITY CALCULATION
# =============================================================================

def calculate_virality(headlines: list, sentiment_score: float) -> float:
    """
    Calculate how 'Viral' or 'Market Moving' the current news cycle is.
    
    Formula: (Volume * 0.4) + (Sentiment_Magnitude * 0.6)
    
    Returns: 0-100 score
    """
    # Volume: How many unique, relevant headlines? (Cap at 20)
    volume_score = min(len(headlines), 20) / 20 * 100
    
    # Magnitude: How extreme is the sentiment? (0.0 neutral -> 0, 1.0 extreme -> 100)
    sentiment_magnitude = abs(sentiment_score) * 100
    
    # Weighted Score
    virality = (volume_score * 0.4) + (sentiment_magnitude * 0.6)
    
    return round(virality, 1)




async def fetch_news_sentiment() -> tuple:
    """
    Fetch news and calculate sentiment + virality.
    
    Returns: (sentiment: float, virality: float)
    """
    # TODO: Integrate with actual news_scraper when available
    # from core.news_scraper import fetch_news_sentiment as real_fetch
    # return await real_fetch()
    
    # Mock implementation for testing
    import random
    
    # Simulate headlines
    num_headlines = random.randint(3, 15)
    headlines = [f"Headline {i}" for i in range(num_headlines)]
    
    # Simulate sentiment (-1 to +1)
    sentiment = random.uniform(-0.5, 0.5)
    
    # Calculate virality
    virality = calculate_virality(headlines, sentiment)
    
    # Occasionally spike for testing
    if random.random() < 0.05:
        virality = random.uniform(75, 95)
        sentiment = random.choice([-0.8, 0.8])
    
    return sentiment, virality




# =============================================================================
# THREE-TIER GAME LOOP
# =============================================================================

async def game_loop():
    """
    The Living Engine - Three-Tier Architecture
    
    TIER 1 (MICRO): Every 10s - Yield, quick updates
    TIER 2 (NARRATIVE): Every 60s - News, agent decisions, virality
    TIER 3 (MACRO): Every 300s - Season end, evolution, cleanup
    """
    config = SchedulerConfig()
    
    print("=" * 50)
    print("🌍 THE LIVING ENGINE: THREE-TIER ORCHESTRATOR")
    print("=" * 50)
    print(f"   ⚡ Micro tick:     {config.MICRO_TICK_RATE}s")
    print(f"   📖 Narrative tick: {config.NARRATIVE_TICK_RATE}s")
    print(f"   🏛️ Macro tick:     {config.MACRO_TICK_RATE}s")
    print("=" * 50)
    
    # 1. Initialize Components
    default_genome = AgentGenome(
        aggression=0.5,
        deception=0.5,
        risk_tolerance=0.5,
        archetype="Director",
        speech_style="Formal",
        secret_objective="SURVIVE"
    )
    agent = GeopoliticalAgent(agent_id="Director_AI", genome=default_genome)
    yield_manager = YieldManager()
    
    # Initialize Timeline Manager for Snapshot & Fork
    try:
        timeline_manager = TimelineManager()
        has_timeline_manager = True
    except Exception as e:
        print(f"⚠️ Timeline Manager not available: {e}")
        has_timeline_manager = False
    
    # Initialize Event Orchestrator for market creation
    try:
        if EventOrchestrator:
            event_orchestrator = EventOrchestrator()
            has_orchestrator = True
            print("   ✅ Event Orchestrator initialized")
        else:
            has_orchestrator = False
    except Exception as e:
        print(f"⚠️ Event Orchestrator not available: {e}")
        has_orchestrator = False
    
    # Timers
    last_micro = 0
    last_narrative = 0
    last_macro = 0
    
    # Stats
    stats = {
        "micro_ticks": 0,
        "narrative_ticks": 0,
        "macro_ticks": 0,
        "forks_created": 0,
        "markets_created": 0,
        "agents_dispatched": 0,
    }
    
    while True:
        now = time.time()
        
        # =====================================================================
        # TIER 1: MICRO TICK (Fast - Yields, Prices)
        # =====================================================================
        if now - last_micro >= config.MICRO_TICK_RATE:
            stats["micro_ticks"] += 1
            
            # Distribute yield (pay agents)
            yield_manager.distribute_yield()
            
            # TODO: Add market price updates here when integrated
            # market_engine.run_tick()
            
            last_micro = now
        
        # =====================================================================
        # TIER 2: NARRATIVE TICK (Medium - News, Decisions, Virality)
        # =====================================================================
        if now - last_narrative >= config.NARRATIVE_TICK_RATE:
            stats["narrative_ticks"] += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{timestamp}] 📖 NARRATIVE TICK")
            
            # 1. Load current state
            current_state = await load_state()
            print(f"   Current Tension: {current_state.global_tension:.2f}")
            
            # 2. Fetch news and calculate virality
            sentiment, virality = await fetch_news_sentiment()
            print(f"   📰 Sentiment: {sentiment:+.2f}, Virality: {virality:.0f}/100")
            
            # 3. Check for high virality -> Auto-fork
            if virality > config.VIRALITY_FORK_THRESHOLD and has_timeline_manager:
                if len(timeline_manager.active_forks) < config.MAX_ACTIVE_FORKS:
                    print(f"   🚨 HIGH VIRALITY! Creating fork...")
                    
                    # Snapshot current reality
                    snap_id = timeline_manager.create_snapshot(
                        f"VIRALITY_{int(virality)}"
                    )
                    
                    # Fork: "What if this escalates?"
                    fork_id = timeline_manager.fork_timeline(
                        snap_id,
                        "ESCALATION",
                        f"Virality {virality:.0f} exceeded threshold"
                    )
                    
                    stats["forks_created"] += 1
                    print(f"   🔀 Fork created: {fork_id}")
            
            # 3b. Event Orchestrator - Process events and create markets
            if has_orchestrator and virality > 50:
                try:
                    # In production, this would fetch real news
                    # For now, we check if any events warrant market creation
                    print(f"   📊 Checking for market opportunities...")
                    
                    # Get active markets count
                    active_markets = len(event_orchestrator.get_active_markets())
                    print(f"   📈 Active markets: {active_markets}")
                    
                    # If virality is very high, trigger event processing
                    if virality > ViralityConfig.AUTO_MARKET_THRESHOLD if ViralityConfig else 80:
                        print(f"   🔥 High virality detected! Processing events...")
                        summary = event_orchestrator.process_events()
                        stats["markets_created"] += summary.get("markets_created", 0)
                        stats["agents_dispatched"] += sum(
                            len(event_orchestrator.dispatcher.active_agents.get(m.id, []))
                            for m in event_orchestrator.get_active_markets()
                        )
                        print(f"   ✅ Created {summary.get('markets_created', 0)} new markets")
                    
                except Exception as e:
                    print(f"   ⚠️ Orchestrator error: {e}")
            
            # 4. Agent decision (The Brain)
            brain_mode = "routine"
            if current_state.global_tension > 0.7 or current_state.global_tension < 0.1:
                brain_mode = "critical"
            
            print(f"   🧠 Agent thinking (Mode: {brain_mode})...")
            decision = await agent.think(current_state, mode=brain_mode)
            
            # 5. Update state
            new_tension = decision.get("new_tension", current_state.global_tension)
            
            # Apply sentiment influence
            new_tension = max(0.0, min(1.0, new_tension + sentiment * 0.1))
            
            reasoning = decision.get("reasoning", "No reason given.")
            
            current_state.global_tension = new_tension
            current_state.recent_reasoning = reasoning
            current_state.last_updated = datetime.now()
            
            # 6. Persist
            await save_state(current_state)
            
            print(f"   ⚡ Tension: {new_tension:.2f}")
            print(f"   📝 Reasoning: {reasoning[:60]}...")
            
            last_narrative = now
        
        # =====================================================================
        # TIER 3: MACRO TICK (Slow - Seasons, Evolution, Cleanup)
        # =====================================================================
        if now - last_macro >= config.MACRO_TICK_RATE:
            stats["macro_ticks"] += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{timestamp}] 🏛️ MACRO TICK")
            
            # 1. Cleanup old forks
            if has_timeline_manager:
                cleaned = timeline_manager.cleanup_old_forks(max_age_days=7)
                if cleaned > 0:
                    print(f"   🗑️ Cleaned {cleaned} old timelines")
            
            # 2. TODO: Evolution/Breeding
            # evolution_engine.run_generation()
            
            # 3. TODO: Season end logic
            # season_manager.check_season_end()
            
            # 4. Print stats
            print(f"   📊 Stats: {stats}")
            
            last_macro = now
        
        # Heartbeat
        await asyncio.sleep(1)




# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    # Handle shutdown gracefully
    def handle_shutdown(signum, frame):
        print("\n\n🛑 Shutting down...")
        raise SystemExit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run the engine
    asyncio.run(game_loop())
