"""
Situation Room Scheduler
========================

The heartbeat of the Geopolitical RPG.

Integrates:
- Synthetic OSINT (for budget testing)
- Auto Mission Uploader
- Narrative War system
- Agent brains
- Real OSINT sources (when available)

Based on Gemini's scheduler structure.
"""

import asyncio
import os
import sys
import signal
import time
from datetime import datetime
from typing import Optional

# Add project root to Python path (always, not just when __main__)
# File is at: backend/simulation/situation-room/scheduler.py
# Need to go up 4 levels to get to project root
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try production imports first, fall back to local
try:
    from backend.core.situation_room_engine import SituationRoomEngine
    from backend.core.mission_generator import OSINTSignal, SignalCategory, SignalSource
    from backend.core.osint_registry import get_osint_registry
    from backend.agents.multi_brain import get_brain
    from backend.core.autouploader import (
        SituationRoomAutoUploader, 
        AutoUploadConfig,
        MODERATE_CONFIG,
        AGGRESSIVE_CONFIG,
    )
    from backend.core.synthetic_osint import SyntheticOSINTGenerator, SyntheticOSINTFeed
    from backend.core.narrative_war import NarrativeWarEngine
except ImportError:
    # Fallback for local runs
    try:
        from backend.core.situation_room_engine import SituationRoomEngine
        from backend.core.mission_generator import OSINTSignal, SignalCategory, SignalSource
        from backend.core.osint_registry import get_osint_registry
        from backend.agents.multi_brain import get_brain
        from backend.core.autouploader import (
            SituationRoomAutoUploader,
            AutoUploadConfig,
            MODERATE_CONFIG,
            AGGRESSIVE_CONFIG,
        )
        from backend.core.synthetic_osint import SyntheticOSINTGenerator, SyntheticOSINTFeed
        from backend.core.narrative_war import NarrativeWarEngine
    except ImportError:
        # If all imports fail, we can't run - raise error with helpful message
        raise ImportError(
            "Failed to import Situation Room modules. "
            "Make sure you're running from the project root and all dependencies are installed. "
            "Try: pip install -r requirements.txt"
        )


# =============================================================================
# CONFIGURATION
# =============================================================================

class SchedulerConfig:
    """Configuration for the Situation Room scheduler"""
    
    # Mode: "synthetic" for testing, "production" for real OSINT
    MODE = os.getenv("SITUATION_ROOM_MODE", "synthetic")
    
    # Tick interval (seconds)
    NARRATIVE_TICK_INTERVAL = int(os.getenv("NARRATIVE_TICK_INTERVAL", "60"))
    
    # Synthetic OSINT settings
    SYNTHETIC_SIGNALS_PER_MINUTE = float(os.getenv("SYNTHETIC_SIGNALS_PER_MINUTE", "1.0"))
    SYNTHETIC_CHAOS_LEVEL = float(os.getenv("SYNTHETIC_CHAOS_LEVEL", "0.5"))
    SYNTHETIC_CRISIS_PROBABILITY = float(os.getenv("SYNTHETIC_CRISIS_PROBABILITY", "0.05"))
    
    # Auto-uploader preset: "conservative", "moderate", "aggressive", "chaos"
    AUTO_UPLOAD_PRESET = os.getenv("AUTO_UPLOAD_PRESET", "moderate")
    
    # Enable features
    ENABLE_NARRATIVE_WAR = os.getenv("ENABLE_NARRATIVE_WAR", "true").lower() == "true"
    ENABLE_SLEEPER_CELLS = os.getenv("ENABLE_SLEEPER_CELLS", "true").lower() == "true"
    ENABLE_TREATIES = os.getenv("ENABLE_TREATIES", "true").lower() == "true"


# =============================================================================
# SIGNAL CONVERTER
# =============================================================================

def convert_osint_signal(raw_signal):
    # Type: Optional[OSINTSignal]
    """
    Convert a signal from the OSINT registry to RPG OSINTSignal.
    Handles different source formats.
    """
    if raw_signal is None:
        return None
    
    # If already an OSINTSignal, return as-is
    if isinstance(raw_signal, OSINTSignal):
        return raw_signal
    
    # Convert from backend.core Signal format
    try:
        # Map source to SignalSource
        source_mapping = {
            "news": SignalSource.NEWS_API,
            "twitter": SignalSource.TWITTER,
            "reddit": SignalSource.REDDIT,
            "market": SignalSource.MARKET_DATA,
            "government": SignalSource.GOVERNMENT,
            "crypto": SignalSource.CRYPTO_CHAIN,
        }
        
        source_value = getattr(raw_signal, 'source', None)
        if hasattr(source_value, 'value'):
            source_str = source_value.value.lower()
        else:
            source_str = str(source_value).lower()
        
        source = source_mapping.get(source_str, SignalSource.NEWS_API)
        
        # Map category
        category_mapping = {
            "geopolitical": SignalCategory.GEOPOLITICAL,
            "economic": SignalCategory.ECONOMIC,
            "corporate": SignalCategory.CORPORATE,
            "technology": SignalCategory.TECHNOLOGY,
            "military": SignalCategory.MILITARY,
            "social": SignalCategory.SOCIAL,
        }
        
        category_str = getattr(raw_signal, 'category', 'geopolitical')
        if hasattr(category_str, 'value'):
            category_str = category_str.value
        category = category_mapping.get(str(category_str).lower(), SignalCategory.GEOPOLITICAL)
        
        # Extract data
        raw_data = getattr(raw_signal, 'raw_data', {}) or {}
        
        return OSINTSignal(
            source=source,
            headline=getattr(raw_signal, 'description', '') or raw_data.get('headline', 'Unknown'),
            summary=raw_data.get('summary', getattr(raw_signal, 'description', '')),
            category=category,
            urgency=getattr(raw_signal, 'level', 0.5),
            virality_score=getattr(raw_signal, 'confidence', 0.5),
            sentiment=raw_data.get('sentiment', -0.3),
            entities=raw_data.get('entities', []),
            source_credibility=getattr(raw_signal, 'confidence', 0.7),
        )
    except Exception as e:
        print(f"⚠️ Failed to convert signal: {e}")
        return None


# =============================================================================
# MAIN GAME LOOP
# =============================================================================

async def game_loop():
    """
    Main game loop for the Situation Room.
    
    This is the heartbeat that:
    1. Ingests OSINT signals (synthetic or real)
    2. Generates missions automatically
    3. Updates global state
    4. Manages narrative arcs
    5. Runs agent AI
    """
    print("=" * 60)
    print("🎭 SITUATION ROOM: INITIALIZING")
    print("=" * 60)
    print(f"   Mode: {SchedulerConfig.MODE}")
    print(f"   Tick Interval: {SchedulerConfig.NARRATIVE_TICK_INTERVAL}s")
    print(f"   Auto-Upload Preset: {SchedulerConfig.AUTO_UPLOAD_PRESET}")
    print("=" * 60)
    
    # 1. Initialize the RPG Engine
    llm_client = get_brain()  # Your Hybrid Brain for narratives (can be None)
    engine = SituationRoomEngine(llm_client=llm_client)
    
    # 2. Initialize Auto-Uploader with config
    preset_configs = {
        "conservative": AutoUploadConfig(
            min_mission_potential=0.7,
            check_interval_seconds=300,
            max_missions_per_cycle=1,
        ),
        "moderate": MODERATE_CONFIG,
        "aggressive": AGGRESSIVE_CONFIG,
        "chaos": AutoUploadConfig(
            min_mission_potential=0.2,
            check_interval_seconds=30,
            max_missions_per_cycle=10,
        ),
    }
    
    upload_config = preset_configs.get(
        SchedulerConfig.AUTO_UPLOAD_PRESET, 
        MODERATE_CONFIG
    )
    uploader = SituationRoomAutoUploader(engine, upload_config)
    
    # 3. Initialize Narrative War (if enabled)
    narrative_war = None
    if SchedulerConfig.ENABLE_NARRATIVE_WAR:
        narrative_war = NarrativeWarEngine()
        print("   ✅ Narrative War enabled")
    
    # 4. Connect OSINT sources based on mode
    osint_registry = None
    synthetic_generator = None
    
    if SchedulerConfig.MODE == "production":
        osint_registry = get_osint_registry()
        if osint_registry:
            print("   ✅ Real OSINT sensors connected")
        else:
            print("   ⚠️ OSINT registry not available, falling back to synthetic")
            SchedulerConfig.MODE = "synthetic"
    
    if SchedulerConfig.MODE == "synthetic":
        synthetic_generator = SyntheticOSINTGenerator(
            chaos_level=SchedulerConfig.SYNTHETIC_CHAOS_LEVEL
        )
        print("   ✅ Synthetic OSINT generator active")
        print(f"      Chaos Level: {SchedulerConfig.SYNTHETIC_CHAOS_LEVEL}")
        print(f"      Signals/min: {SchedulerConfig.SYNTHETIC_SIGNALS_PER_MINUTE}")
    
    print("\n" + "=" * 60)
    print("🎭 SITUATION ROOM: ONLINE")
    print("=" * 60 + "\n")
    
    # Timing
    last_narrative_tick = 0
    last_synthetic_signal = 0
    synthetic_interval = 60.0 / SchedulerConfig.SYNTHETIC_SIGNALS_PER_MINUTE
    
    # Stats
    signals_processed = 0
    missions_generated = 0
    
    while True:
        now = time.time()
        
        try:
            # =================================================================
            # SYNTHETIC SIGNAL INJECTION (Budget Mode)
            # =================================================================
            if SchedulerConfig.MODE == "synthetic" and synthetic_generator:
                if now - last_synthetic_signal >= synthetic_interval:
                    # Maybe inject a crisis
                    if SchedulerConfig.SYNTHETIC_CRISIS_PROBABILITY > 0:
                        import random
                        if random.random() < SchedulerConfig.SYNTHETIC_CRISIS_PROBABILITY:
                            crisis_type = random.choice(["taiwan", "economic_collapse", "assassination"])
                            crisis_signals = synthetic_generator.generate_crisis_scenario(crisis_type)
                            print(f"\n🚨 CRISIS TRIGGERED: {crisis_type.upper()}")
                            for signal in crisis_signals:
                                await uploader.process_signal(signal)
                                signals_processed += 1
                        else:
                            # Normal signal
                            signal = synthetic_generator.generate_signal()
                            await uploader.process_signal(signal)
                            signals_processed += 1
                    else:
                        signal = synthetic_generator.generate_signal()
                        await uploader.process_signal(signal)
                        signals_processed += 1
                    
                    last_synthetic_signal = now
            
            # =================================================================
            # NARRATIVE TICK (Main Game Update)
            # =================================================================
            if now - last_narrative_tick >= SchedulerConfig.NARRATIVE_TICK_INTERVAL:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{timestamp}] 📡 NARRATIVE TICK")
                
                # A. Scan Real World Signals (if in production mode)
                if SchedulerConfig.MODE == "production" and osint_registry:
                    try:
                        raw_signals = await osint_registry.scan_all()
                        for raw_signal in raw_signals:
                            rpg_signal = convert_osint_signal(raw_signal)
                            if rpg_signal:
                                await uploader.process_signal(rpg_signal)
                                signals_processed += 1
                    except Exception as e:
                        print(f"   ⚠️ OSINT scan error: {e}")
                
                # B. Run Game Logic (Engine Tick)
                await engine.tick()
                
                # C. Update Narrative War influence on tension
                if narrative_war:
                    tension_influence = narrative_war.get_tension_influence()
                    engine.theater_state.global_tension = max(0, min(1,
                        engine.theater_state.global_tension + tension_influence * 0.01
                    ))
                
                # D. Print Status Dashboard
                state = engine.get_state_snapshot()
                uploader_stats = uploader.get_stats()
                
                print(f"   ┌─────────────────────────────────────┐")
                print(f"   │ 🌍 Global Tension: {state['global_tension']:.1%}              │")
                print(f"   │ 🎭 Chaos Index:    {state['chaos_index']:.1%}              │")
                print(f"   │ 📋 Active Missions: {state['active_missions']:>2}               │")
                print(f"   │ 📊 Signals Today:   {signals_processed:>3}              │")
                print(f"   │ ✅ Missions Gen'd:  {uploader_stats['missions_generated']:>3}              │")
                print(f"   └─────────────────────────────────────┘")
                
                # E. Log recent events
                recent_events = state.get('recent_events', [])[-3:]
                if recent_events:
                    print(f"   Recent Events:")
                    for event in recent_events:
                        event_type = event.get('type', 'unknown')
                        print(f"      → {event_type}")
                
                last_narrative_tick = now
            
            # Sleep briefly to avoid busy loop
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"\n❌ Game loop error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)  # Brief pause on error


# =============================================================================
# GRACEFUL SHUTDOWN
# =============================================================================

shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    print("\n\n🛑 Shutdown signal received...")
    shutdown_event.set()


async def main():
    """Main entry point with graceful shutdown"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run game loop
    game_task = asyncio.create_task(game_loop())
    shutdown_task = asyncio.create_task(shutdown_event.wait())
    
    # Wait for either game loop to finish or shutdown signal
    done, pending = await asyncio.wait(
        [game_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # Cancel pending tasks
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    print("\n🎭 SITUATION ROOM: OFFLINE")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Situation Room Offline")
