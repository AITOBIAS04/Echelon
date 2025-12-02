"""
Situation Room - Auto Mission Uploader
=======================================

This module handles automatic mission generation and upload to the Situation Room.
It connects OSINT sources to the mission generator with configurable parameters.

Parameters you can set:
- Mission generation thresholds
- Auto-upload frequency
- Mission types to generate
- Narrative arc triggers
- Faction-specific missions

This runs as a background service that continuously:
1. Monitors OSINT feeds
2. Analyzes signals for mission potential
3. Auto-generates missions above threshold
4. Uploads to Situation Room mission board
5. Creates associated betting markets
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    from backend.core.models import (
        AgentRole, MissionType, Difficulty, Faction,
        Mission, NarrativeArc, TheaterState
    )
    from backend.core.mission_generator import (
        OSINTSignal, SignalCategory, SignalSource,
        SignalAnalyzer, MissionGenerator, NarrativeArcGenerator
    )
    from backend.core.situation_room_engine import SituationRoomEngine
except ImportError:
    from core.models import (
        AgentRole, MissionType, Difficulty, Faction,
        Mission, NarrativeArc, TheaterState
    )
    from core.mission_generator import (
        OSINTSignal, SignalCategory, SignalSource,
        SignalAnalyzer, MissionGenerator, NarrativeArcGenerator
    )
    from core.situation_room_engine import SituationRoomEngine


# =============================================================================
# AUTO-UPLOAD CONFIGURATION
# =============================================================================

@dataclass
class AutoUploadConfig:
    """
    Configuration for automatic mission generation and upload.
    Set these parameters to control what gets uploaded to the Situation Room.
    """
    
    # =========================================================================
    # MISSION GENERATION THRESHOLDS
    # =========================================================================
    
    # Minimum mission potential score to auto-generate (0.0 - 1.0)
    # Higher = fewer, more significant missions
    min_mission_potential: float = 0.5
    
    # Minimum signal virality to consider (0.0 - 1.0)
    min_virality: float = 0.3
    
    # Minimum urgency to auto-generate (0.0 - 1.0)
    min_urgency: float = 0.4
    
    # =========================================================================
    # UPLOAD FREQUENCY
    # =========================================================================
    
    # How often to check for new signals (seconds)
    check_interval_seconds: int = 60
    
    # Maximum missions to generate per check cycle
    max_missions_per_cycle: int = 3
    
    # Maximum active missions at any time (0 = unlimited)
    max_active_missions: int = 20
    
    # Cooldown between similar mission types (minutes)
    mission_type_cooldown_minutes: int = 30
    
    # =========================================================================
    # MISSION TYPE FILTERS
    # =========================================================================
    
    # Which mission types to auto-generate (empty = all types)
    allowed_mission_types: List[MissionType] = field(default_factory=list)
    
    # Mission types to never auto-generate
    blocked_mission_types: List[MissionType] = field(default_factory=list)
    
    # Probability weights for mission types (optional)
    mission_type_weights: Dict[str, float] = field(default_factory=dict)
    
    # =========================================================================
    # DIFFICULTY SETTINGS
    # =========================================================================
    
    # Minimum difficulty to auto-generate
    min_difficulty: Difficulty = Difficulty.ROUTINE
    
    # Maximum difficulty to auto-generate
    max_difficulty: Difficulty = Difficulty.CRITICAL
    
    # =========================================================================
    # NARRATIVE ARC SETTINGS
    # =========================================================================
    
    # Auto-generate narrative arcs?
    enable_narrative_arcs: bool = True
    
    # Minimum signals needed to start a narrative arc
    min_signals_for_arc: int = 2
    
    # Maximum active narrative arcs
    max_active_arcs: int = 3
    
    # Arc types to auto-generate
    allowed_arc_types: List[str] = field(default_factory=lambda: [
        "crisis_escalation",
        "assassination_mystery",
        "market_manipulation",
    ])
    
    # =========================================================================
    # FACTION SETTINGS
    # =========================================================================
    
    # Generate faction-specific missions?
    enable_faction_missions: bool = True
    
    # Faction balance targets (try to keep missions distributed)
    target_faction_balance: bool = True
    
    # =========================================================================
    # SPECIAL EVENTS
    # =========================================================================
    
    # Auto-generate "Who Killed X?" mysteries
    enable_assassination_mysteries: bool = True
    mystery_generation_probability: float = 0.1  # 10% chance per cycle
    
    # Auto-trigger sleeper cells based on tension
    enable_sleeper_auto_trigger: bool = True
    sleeper_trigger_tension: float = 0.9
    
    # =========================================================================
    # BETTING MARKET INTEGRATION
    # =========================================================================
    
    # Auto-create betting markets for missions?
    auto_create_betting_markets: bool = True
    
    # Minimum reward to create betting market
    min_reward_for_betting_market: float = 10.0


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

# Conservative: Few missions, high quality
CONSERVATIVE_CONFIG = AutoUploadConfig(
    min_mission_potential=0.7,
    min_virality=0.5,
    min_urgency=0.6,
    check_interval_seconds=300,  # 5 minutes
    max_missions_per_cycle=1,
    max_active_missions=10,
    min_difficulty=Difficulty.STANDARD,
)

# Moderate: Balanced approach
MODERATE_CONFIG = AutoUploadConfig(
    min_mission_potential=0.5,
    min_virality=0.3,
    min_urgency=0.4,
    check_interval_seconds=120,  # 2 minutes
    max_missions_per_cycle=3,
    max_active_missions=20,
)

# Aggressive: Many missions, fast-paced
AGGRESSIVE_CONFIG = AutoUploadConfig(
    min_mission_potential=0.3,
    min_virality=0.2,
    min_urgency=0.2,
    check_interval_seconds=30,
    max_missions_per_cycle=5,
    max_active_missions=50,
    max_difficulty=Difficulty.IMPOSSIBLE,
)

# Chaos Mode: Everything goes
CHAOS_CONFIG = AutoUploadConfig(
    min_mission_potential=0.1,
    min_virality=0.1,
    min_urgency=0.1,
    check_interval_seconds=10,
    max_missions_per_cycle=10,
    max_active_missions=100,
    mystery_generation_probability=0.3,
    sleeper_trigger_tension=0.7,
)


# =============================================================================
# AUTO-UPLOADER SERVICE
# =============================================================================

class SituationRoomAutoUploader:
    """
    Background service that automatically generates and uploads missions
    to the Situation Room based on incoming OSINT signals.
    
    Usage:
        engine = SituationRoomEngine()
        config = AutoUploadConfig(min_mission_potential=0.6)
        uploader = SituationRoomAutoUploader(engine, config)
        
        # Start the auto-upload service
        await uploader.start()
        
        # Feed signals (from your OSINT sources)
        await uploader.process_signal(signal)
    """
    
    def __init__(
        self,
        engine: SituationRoomEngine,
        config: Optional[AutoUploadConfig] = None
    ):
        self.engine = engine
        self.config = config or AutoUploadConfig()
        
        # State tracking
        self.is_running = False
        self.last_check = datetime.now(timezone.utc)
        self.missions_generated_this_cycle = 0
        self.mission_type_last_generated: Dict[MissionType, datetime] = {}
        
        # Signal buffer
        self.pending_signals: List[OSINTSignal] = []
        self.processed_signal_ids: set = set()
        
        # Stats
        self.stats = {
            "signals_processed": 0,
            "missions_generated": 0,
            "missions_rejected": 0,
            "arcs_generated": 0,
            "cycles_completed": 0,
        }
        
        # Callbacks
        self.on_mission_uploaded: Optional[Callable] = None
        self.on_arc_created: Optional[Callable] = None
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def start(self):
        """Start the auto-upload background service"""
        self.is_running = True
        print(f"🚀 Situation Room Auto-Uploader started")
        print(f"   Config: potential>{self.config.min_mission_potential}, "
              f"interval={self.config.check_interval_seconds}s")
        
        while self.is_running:
            try:
                await self._run_cycle()
                await asyncio.sleep(self.config.check_interval_seconds)
            except Exception as e:
                print(f"❌ Auto-uploader error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    def stop(self):
        """Stop the auto-upload service"""
        self.is_running = False
        print("🛑 Situation Room Auto-Uploader stopped")
    
    async def _run_cycle(self):
        """Run one cycle of the auto-upload process"""
        self.missions_generated_this_cycle = 0
        self.stats["cycles_completed"] += 1
        
        # 1. Process pending signals
        await self._process_pending_signals()
        
        # 2. Check for narrative arc opportunities
        if self.config.enable_narrative_arcs:
            await self._check_narrative_opportunities()
        
        # 3. Random special events
        await self._check_special_events()
        
        # 4. Update engine state
        await self.engine.tick()
        
        self.last_check = datetime.now(timezone.utc)
    
    # =========================================================================
    # SIGNAL PROCESSING
    # =========================================================================
    
    async def process_signal(self, signal: OSINTSignal) -> bool:
        """
        Process an incoming OSINT signal.
        Returns True if signal was accepted for processing.
        
        Call this from your OSINT sources to feed signals into the system.
        """
        # Skip duplicates
        if signal.id in self.processed_signal_ids:
            return False
        
        # Analyze signal
        if not signal.processed:
            analyzer = SignalAnalyzer()
            signal = analyzer.analyze(signal)
        
        # Check if meets thresholds
        if not self._meets_thresholds(signal):
            self.stats["missions_rejected"] += 1
            return False
        
        # Add to pending queue
        self.pending_signals.append(signal)
        self.processed_signal_ids.add(signal.id)
        self.stats["signals_processed"] += 1
        
        # Also add to engine
        await self.engine.ingest_signal(signal)
        
        return True
    
    def _meets_thresholds(self, signal: OSINTSignal) -> bool:
        """Check if signal meets auto-upload thresholds"""
        if signal.mission_potential < self.config.min_mission_potential:
            return False
        if signal.virality_score < self.config.min_virality:
            return False
        if signal.urgency < self.config.min_urgency:
            return False
        return True
    
    async def _process_pending_signals(self):
        """Process all pending signals and generate missions"""
        
        # Check active mission count
        active_count = len([
            m for m in self.engine.missions.values()
            if m.status.value in ["pending", "active"]
        ])
        
        if self.config.max_active_missions > 0 and active_count >= self.config.max_active_missions:
            return  # Too many active missions
        
        # Sort by potential (highest first)
        self.pending_signals.sort(key=lambda s: s.mission_potential, reverse=True)
        
        # Process top signals
        for signal in self.pending_signals[:self.config.max_missions_per_cycle]:
            if self.missions_generated_this_cycle >= self.config.max_missions_per_cycle:
                break
            
            mission = await self._generate_and_upload_mission(signal)
            if mission:
                self.missions_generated_this_cycle += 1
        
        # Clear processed signals
        processed_ids = {s.id for s in self.pending_signals[:self.config.max_missions_per_cycle]}
        self.pending_signals = [s for s in self.pending_signals if s.id not in processed_ids]
    
    async def _generate_and_upload_mission(
        self, 
        signal: OSINTSignal
    ) -> Optional[Mission]:
        """Generate a mission from signal and upload to Situation Room"""
        
        # Determine mission type
        mission_type = self._select_mission_type(signal)
        if not mission_type:
            return None
        
        # Check cooldown
        if not self._check_type_cooldown(mission_type):
            return None
        
        # Generate mission
        mission = await self.engine.generate_mission_from_signal(
            signal.id,
            force_type=mission_type
        )
        
        if not mission:
            return None
        
        # Check difficulty bounds
        if mission.difficulty.value < self.config.min_difficulty.value:
            return None
        if mission.difficulty.value > self.config.max_difficulty.value:
            return None
        
        # Update tracking
        self.mission_type_last_generated[mission_type] = datetime.now(timezone.utc)
        self.stats["missions_generated"] += 1
        
        # Create betting market if enabled
        if self.config.auto_create_betting_markets:
            if mission.base_reward_usdc >= self.config.min_reward_for_betting_market:
                mission.betting_market_id = f"market-{mission.id[:8]}"
        
        # Callback
        if self.on_mission_uploaded:
            await self._safe_callback(self.on_mission_uploaded, mission)
        
        print(f"✅ Auto-uploaded: {mission.codename} ({mission.mission_type.value})")
        
        return mission
    
    def _select_mission_type(self, signal: OSINTSignal) -> Optional[MissionType]:
        """Select appropriate mission type for signal"""
        
        # Use signal's suggested types
        suggested = signal.suggested_mission_types
        if not suggested:
            suggested = [MissionType.INTELLIGENCE]
        
        for mt in suggested:
            # Check blocked list
            if mt in self.config.blocked_mission_types:
                continue
            
            # Check allowed list (if specified)
            if self.config.allowed_mission_types and mt not in self.config.allowed_mission_types:
                continue
            
            return mt
        
        return None
    
    def _check_type_cooldown(self, mission_type: MissionType) -> bool:
        """Check if mission type is off cooldown"""
        last_generated = self.mission_type_last_generated.get(mission_type)
        if not last_generated:
            return True
        
        cooldown = timedelta(minutes=self.config.mission_type_cooldown_minutes)
        return datetime.now(timezone.utc) >= last_generated + cooldown
    
    # =========================================================================
    # NARRATIVE ARCS
    # =========================================================================
    
    async def _check_narrative_opportunities(self):
        """Check if we should start a new narrative arc"""
        
        # Count active arcs
        active_arcs = len([
            a for a in self.engine.narrative_arcs.values()
            if a.current_chapter <= a.total_chapters
        ])
        
        if active_arcs >= self.config.max_active_arcs:
            return
        
        # Look for related signals to seed an arc
        recent_signals = list(self.engine.processed_signals.values())[-20:]
        
        # Group by category
        category_signals: Dict[SignalCategory, List[OSINTSignal]] = {}
        for signal in recent_signals:
            if signal.category not in category_signals:
                category_signals[signal.category] = []
            category_signals[signal.category].append(signal)
        
        # Check if any category has enough signals for an arc
        for category, signals in category_signals.items():
            if len(signals) >= self.config.min_signals_for_arc:
                arc_type = self._category_to_arc_type(category)
                if arc_type and arc_type in self.config.allowed_arc_types:
                    await self._create_narrative_arc(signals[:3], arc_type)
                    break
    
    def _category_to_arc_type(self, category: SignalCategory) -> Optional[str]:
        """Map signal category to narrative arc type"""
        mapping = {
            SignalCategory.GEOPOLITICAL: "crisis_escalation",
            SignalCategory.CORPORATE: "corporate_espionage",
            SignalCategory.ECONOMIC: "market_manipulation",
            SignalCategory.MILITARY: "crisis_escalation",
        }
        return mapping.get(category)
    
    async def _create_narrative_arc(
        self, 
        seed_signals: List[OSINTSignal],
        arc_type: str
    ):
        """Create a narrative arc from seed signals"""
        arc_generator = NarrativeArcGenerator(self.engine.mission_generator)
        
        arc = await arc_generator.generate_arc(
            seed_signals=seed_signals,
            arc_type=arc_type,
            theater_state=self.engine.theater_state
        )
        
        self.engine.narrative_arcs[arc.id] = arc
        self.stats["arcs_generated"] += 1
        
        if self.on_arc_created:
            await self._safe_callback(self.on_arc_created, arc)
        
        print(f"📖 Auto-created narrative arc: {arc.title}")
    
    # =========================================================================
    # SPECIAL EVENTS
    # =========================================================================
    
    async def _check_special_events(self):
        """Check for special event triggers"""
        import random
        
        # Random assassination mystery
        if self.config.enable_assassination_mysteries:
            if random.random() < self.config.mystery_generation_probability:
                await self._generate_assassination_mystery()
        
        # Sleeper activation
        if self.config.enable_sleeper_auto_trigger:
            if self.engine.theater_state.global_tension >= self.config.sleeper_trigger_tension:
                self.engine.sleeper_system.check_triggers()
    
    async def _generate_assassination_mystery(self):
        """Generate a 'Who Killed X?' mystery"""
        arc_generator = NarrativeArcGenerator(self.engine.mission_generator)
        arc = await arc_generator.generate_assassination_mystery()
        
        self.engine.narrative_arcs[arc.id] = arc
        self.stats["arcs_generated"] += 1
        
        print(f"🔍 Auto-created mystery: {arc.title}")
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    async def _safe_callback(self, callback: Callable, *args):
        """Safely execute a callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            print(f"Callback error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get auto-uploader statistics"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "pending_signals": len(self.pending_signals),
            "last_check": self.last_check.isoformat(),
            "config": {
                "min_potential": self.config.min_mission_potential,
                "interval": self.config.check_interval_seconds,
                "max_per_cycle": self.config.max_missions_per_cycle,
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def setup_auto_uploader(
    engine: SituationRoomEngine,
    mode: str = "moderate"
) -> SituationRoomAutoUploader:
    """
    Set up auto-uploader with a preset configuration.
    
    Modes:
    - "conservative": Few missions, high quality
    - "moderate": Balanced (default)
    - "aggressive": Many missions, fast-paced
    - "chaos": Everything goes
    
    Example:
        engine = SituationRoomEngine()
        uploader = await setup_auto_uploader(engine, mode="moderate")
        asyncio.create_task(uploader.start())
    """
    configs = {
        "conservative": CONSERVATIVE_CONFIG,
        "moderate": MODERATE_CONFIG,
        "aggressive": AGGRESSIVE_CONFIG,
        "chaos": CHAOS_CONFIG,
    }
    
    config = configs.get(mode, MODERATE_CONFIG)
    return SituationRoomAutoUploader(engine, config)


# =============================================================================
# EXAMPLE INTEGRATION
# =============================================================================

async def example_auto_upload():
    """Example of setting up auto-upload with OSINT feed"""
    
    # 1. Create engine
    engine = SituationRoomEngine()
    
    # 2. Configure auto-uploader
    config = AutoUploadConfig(
        # Mission thresholds
        min_mission_potential=0.5,
        min_virality=0.3,
        
        # Frequency
        check_interval_seconds=60,
        max_missions_per_cycle=3,
        max_active_missions=20,
        
        # Types
        allowed_mission_types=[
            MissionType.INTELLIGENCE,
            MissionType.INVESTIGATION,
            MissionType.DIPLOMACY,
            MissionType.SABOTAGE,
        ],
        
        # Narratives
        enable_narrative_arcs=True,
        enable_assassination_mysteries=True,
        mystery_generation_probability=0.05,  # 5% chance per cycle
        
        # Betting
        auto_create_betting_markets=True,
    )
    
    uploader = SituationRoomAutoUploader(engine, config)
    
    # 3. Set up callbacks (optional)
    def on_mission(mission):
        print(f"📋 New mission available: {mission.codename}")
        # Here you would: update UI, create betting market, notify agents
    
    def on_arc(arc):
        print(f"📖 New storyline: {arc.title}")
        # Here you would: update narrative timeline, create arc betting market
    
    uploader.on_mission_uploaded = on_mission
    uploader.on_arc_created = on_arc
    
    # 4. Start the uploader (runs in background)
    upload_task = asyncio.create_task(uploader.start())
    
    # 5. Simulate OSINT feed
    test_signals = [
        OSINTSignal(
            headline="China announces new Taiwan military exercises",
            summary="PLA deploys additional forces to Fujian province...",
            category=SignalCategory.GEOPOLITICAL,
            source=SignalSource.NEWS_API,
            urgency=0.8,
            virality_score=0.7,
        ),
        OSINTSignal(
            headline="Major tech CEO unexpectedly resigns",
            summary="Industry shocked by sudden departure...",
            category=SignalCategory.CORPORATE,
            source=SignalSource.NEWS_API,
            urgency=0.6,
            virality_score=0.8,
        ),
        OSINTSignal(
            headline="Oil prices surge on supply concerns",
            summary="Brent crude jumps 5% on Middle East tensions...",
            category=SignalCategory.ECONOMIC,
            source=SignalSource.MARKET_DATA,
            urgency=0.7,
            virality_score=0.6,
        ),
    ]
    
    # Feed signals to uploader
    for signal in test_signals:
        await uploader.process_signal(signal)
        await asyncio.sleep(1)
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Check stats
    print("\n📊 Auto-Uploader Stats:")
    print(uploader.get_stats())
    
    # Stop
    uploader.stop()
    upload_task.cancel()


if __name__ == "__main__":
    asyncio.run(example_auto_upload())
