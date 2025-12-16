"""
Echelon Mission Factory
=======================

Auto-generates missions from OSINT signals using the Listener → Analyser → Publisher
architecture. Integrates with the Skills System for narrative generation.

Architecture:
    LISTENERS (poll every 5-15 min)
        │
        ▼
    ANALYSER (LLM generates narrative)
        │
        ▼
    PUBLISHER (deploys market, notifies agents)

Usage:
    from mission_factory import MissionFactory
    
    factory = MissionFactory()
    factory.register_listener(MarketListener())
    factory.register_listener(GeoListener())
    
    # Run the factory
    await factory.run()
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class SignalType(str, Enum):
    """Types of OSINT signals."""
    MARKET = "market"           # Price/volume anomalies
    NEWS = "news"               # Sentiment spikes
    GEO = "geo"                 # Geopolitical events
    CHAOS = "chaos"             # Dark fleet, VIP flights
    SOCIAL = "social"           # Social media trends
    ONCHAIN = "onchain"         # Whale movements


class MissionType(str, Enum):
    """Pre-defined mission templates."""
    GHOST_TANKER = "ghost_tanker"
    SILICON_ACQUISITION = "silicon_acquisition"
    CONTAGION_ZERO = "contagion_zero"
    DEEP_STATE_SHUFFLE = "deep_state_shuffle"
    SUMMIT_SNUB = "summit_snub"
    WHALE_ALERT = "whale_alert"
    FLASH_CRASH = "flash_crash"
    CUSTOM = "custom"


@dataclass
class RawSignal:
    """Raw signal from a listener."""
    signal_id: str
    signal_type: SignalType
    source: str                    # e.g., "spire_ais", "ravenpack", "polygon.io"
    data: dict                     # Raw JSON payload
    timestamp: datetime
    severity: float = 0.5          # 0-1: How significant
    
    @classmethod
    def create(cls, signal_type: SignalType, source: str, data: dict, severity: float = 0.5):
        return cls(
            signal_id=f"sig_{uuid4().hex[:12]}",
            signal_type=signal_type,
            source=source,
            data=data,
            timestamp=datetime.utcnow(),
            severity=severity,
        )


@dataclass
class MissionTemplate:
    """Template for mission generation."""
    mission_type: MissionType
    title_template: str
    description_template: str
    trigger_conditions: dict       # Conditions that activate this template
    market_question_template: str
    default_duration_hours: int
    reward_pool: float
    required_agents: list[str]     # e.g., ["shark", "spy"]


@dataclass
class GeneratedMission:
    """A fully generated mission ready for deployment."""
    mission_id: str
    mission_type: MissionType
    title: str
    description: str
    market_question: str
    trigger_signal: RawSignal
    narrative: str                 # LLM-generated story
    objectives: list[str]
    rewards: dict
    betting_options: list[dict]
    duration_hours: int
    time_pressure: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"        # pending, active, resolved


# =============================================================================
# Mission Templates
# =============================================================================

MISSION_TEMPLATES = {
    MissionType.GHOST_TANKER: MissionTemplate(
        mission_type=MissionType.GHOST_TANKER,
        title_template="Ghost Tanker: {vessel_count} vessels dark near {location}",
        description_template="Spire AIS data shows {vessel_count} oil tankers have gone dark near {location}. Sanctions evasion or routine maintenance?",
        trigger_conditions={
            "signal_type": SignalType.CHAOS,
            "source": "spire_ais",
            "min_vessels_dark": 3,
            "location_keywords": ["venezuela", "hormuz", "iran", "russia"],
        },
        market_question_template="Will Tanker {vessel_id} dock in {destination} within 48 hours?",
        default_duration_hours=48,
        reward_pool=5000,
        required_agents=["shark", "spy"],
    ),
    
    MissionType.SILICON_ACQUISITION: MissionTemplate(
        mission_type=MissionType.SILICON_ACQUISITION,
        title_template="Silicon Acquisition: {company} posts {job_count}+ AI roles",
        description_template="{company} has posted {job_count} AI-related job openings in {timeframe}. Major acquisition or internal project?",
        trigger_conditions={
            "signal_type": SignalType.NEWS,
            "source": "linkup_jobs",
            "min_ai_jobs": 50,
            "timeframe_days": 7,
        },
        market_question_template="Will {company} announce an AI acquisition within 30 days?",
        default_duration_hours=720,  # 30 days
        reward_pool=10000,
        required_agents=["spy", "diplomat"],
    ),
    
    MissionType.CONTAGION_ZERO: MissionTemplate(
        mission_type=MissionType.CONTAGION_ZERO,
        title_template="Contagion Zero: {percent_spike}% spike in '{keyword}' mentions in {location}",
        description_template="Social monitoring detected a {percent_spike}% increase in '{keyword}' mentions geo-clustered around {location}.",
        trigger_conditions={
            "signal_type": SignalType.SOCIAL,
            "source": "x_api",
            "min_spike_percent": 300,
            "keywords": ["flu", "outbreak", "sick", "hospital", "quarantine"],
        },
        market_question_template="Will WHO declare a public health emergency in {location} within 14 days?",
        default_duration_hours=336,  # 14 days
        reward_pool=15000,
        required_agents=["spy", "saboteur"],
    ),
    
    MissionType.DEEP_STATE_SHUFFLE: MissionTemplate(
        mission_type=MissionType.DEEP_STATE_SHUFFLE,
        title_template="Deep State Shuffle: Anomalies detected in {country}",
        description_template="NASA Black Marble shows {location} went dark at {time}. ADS-B tracking shows {flight_count} private jets departed for {destinations}.",
        trigger_conditions={
            "signal_type": SignalType.CHAOS,
            "sources": ["nasa_blackmarble", "adsb_exchange"],
            "night_lights_drop_percent": 50,
            "vip_flights_count": 3,
        },
        market_question_template="Will there be a leadership change in {country} within 7 days?",
        default_duration_hours=168,  # 7 days
        reward_pool=20000,
        required_agents=["shark", "spy", "diplomat", "saboteur"],
    ),
    
    MissionType.SUMMIT_SNUB: MissionTemplate(
        mission_type=MissionType.SUMMIT_SNUB,
        title_template="Summit Snub: {aircraft} diverts from {destination}",
        description_template="ADS-B tracking confirms {aircraft} has diverted from scheduled {event}. Deal collapsed or security threat?",
        trigger_conditions={
            "signal_type": SignalType.CHAOS,
            "source": "adsb_exchange",
            "aircraft_types": ["air_force_one", "government_vip"],
            "diversion_detected": True,
        },
        market_question_template="Will {event} proceed as scheduled?",
        default_duration_hours=24,
        reward_pool=8000,
        required_agents=["diplomat", "spy"],
    ),
    
    MissionType.WHALE_ALERT: MissionTemplate(
        mission_type=MissionType.WHALE_ALERT,
        title_template="Whale Alert: {amount} {token} moved to {destination}",
        description_template="On-chain monitoring detected {amount} {token} (~${usd_value}M) transferred to {destination}.",
        trigger_conditions={
            "signal_type": SignalType.ONCHAIN,
            "source": "whale_alert",
            "min_usd_value": 10_000_000,
        },
        market_question_template="Will {token} price move more than 5% in the next 24 hours?",
        default_duration_hours=24,
        reward_pool=5000,
        required_agents=["shark"],
    ),
    
    MissionType.FLASH_CRASH: MissionTemplate(
        mission_type=MissionType.FLASH_CRASH,
        title_template="Flash Crash: {asset} drops {percent}% in {minutes} minutes",
        description_template="Polygon.io detected {asset} dropped {percent}% in just {minutes} minutes. Fat finger or coordinated attack?",
        trigger_conditions={
            "signal_type": SignalType.MARKET,
            "source": "polygon.io",
            "min_drop_percent": 5,
            "max_timeframe_minutes": 5,
        },
        market_question_template="Will {asset} recover to pre-crash levels within 24 hours?",
        default_duration_hours=24,
        reward_pool=3000,
        required_agents=["shark", "saboteur"],
    ),
}


# =============================================================================
# Listeners (Data Ingestion)
# =============================================================================

class BaseListener(ABC):
    """Base class for OSINT listeners."""
    
    def __init__(self, poll_interval_seconds: int = 300):
        self.poll_interval = poll_interval_seconds
        self.last_poll: Optional[datetime] = None
        self.is_running = False
    
    @property
    @abstractmethod
    def signal_type(self) -> SignalType:
        """Return the type of signals this listener produces."""
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the data source name."""
        pass
    
    @abstractmethod
    async def poll(self) -> list[RawSignal]:
        """Poll the data source and return any signals."""
        pass
    
    async def run(self, callback: Callable[[RawSignal], None]):
        """Run the listener continuously."""
        self.is_running = True
        while self.is_running:
            try:
                signals = await self.poll()
                for signal in signals:
                    callback(signal)
                self.last_poll = datetime.utcnow()
            except Exception as e:
                logger.error(f"Listener {self.source_name} error: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the listener."""
        self.is_running = False


class MarketListener(BaseListener):
    """Monitors market data for anomalies (Polygon.io, platform APIs)."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(poll_interval_seconds=60)  # 1 minute
        self.api_key = api_key
        self.price_cache: dict[str, float] = {}
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.MARKET
    
    @property
    def source_name(self) -> str:
        return "polygon.io"
    
    async def poll(self) -> list[RawSignal]:
        """Check for price anomalies (>5% move in 5 minutes)."""
        signals = []
        
        # In production, this would call Polygon.io API
        # For now, return empty list (no anomalies)
        
        # Example anomaly detection logic:
        # for asset, current_price in await self._fetch_prices():
        #     cached_price = self.price_cache.get(asset, current_price)
        #     change_percent = abs(current_price - cached_price) / cached_price * 100
        #     
        #     if change_percent > 5:
        #         signals.append(RawSignal.create(
        #             signal_type=SignalType.MARKET,
        #             source=self.source_name,
        #             data={
        #                 "asset": asset,
        #                 "price": current_price,
        #                 "change_percent": change_percent,
        #                 "direction": "up" if current_price > cached_price else "down",
        #             },
        #             severity=min(change_percent / 10, 1.0),
        #         ))
        #     
        #     self.price_cache[asset] = current_price
        
        return signals


class NewsListener(BaseListener):
    """Monitors news sentiment (RavenPack, Dataminr)."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(poll_interval_seconds=300)  # 5 minutes
        self.api_key = api_key
        self.sentiment_baseline: dict[str, float] = {}
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.NEWS
    
    @property
    def source_name(self) -> str:
        return "ravenpack"
    
    async def poll(self) -> list[RawSignal]:
        """Check for sentiment spikes (>20 point drop)."""
        signals = []
        # Implementation would call RavenPack/Dataminr API
        return signals


class GeoListener(BaseListener):
    """Monitors geopolitical events (GDELT, ACLED)."""
    
    def __init__(self):
        super().__init__(poll_interval_seconds=900)  # 15 minutes
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.GEO
    
    @property
    def source_name(self) -> str:
        return "gdelt"
    
    async def poll(self) -> list[RawSignal]:
        """Check for conflict events, political changes."""
        signals = []
        # Implementation would call GDELT/ACLED APIs
        return signals


class ChaosListener(BaseListener):
    """Monitors chaos signals (Spire AIS, ADS-B, NASA Black Marble)."""
    
    def __init__(self, spire_key: Optional[str] = None):
        super().__init__(poll_interval_seconds=600)  # 10 minutes
        self.spire_key = spire_key
        self.tracked_vessels: set[str] = set()
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.CHAOS
    
    @property
    def source_name(self) -> str:
        return "spire_ais"
    
    async def poll(self) -> list[RawSignal]:
        """Check for dark fleet, VIP flights, night light changes."""
        signals = []
        # Implementation would call Spire/ADS-B/NASA APIs
        return signals


class OnChainListener(BaseListener):
    """Monitors on-chain activity (Whale Alert, Arkham, Nansen)."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(poll_interval_seconds=60)  # 1 minute
        self.api_key = api_key
        self.min_alert_usd = 10_000_000  # $10M minimum
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.ONCHAIN
    
    @property
    def source_name(self) -> str:
        return "whale_alert"
    
    async def poll(self) -> list[RawSignal]:
        """Check for large on-chain movements."""
        signals = []
        # Implementation would call Whale Alert/Arkham APIs
        return signals


# =============================================================================
# Analyser (LLM Narrative Generation)
# =============================================================================

class MissionAnalyser:
    """
    The 'Director' AI that generates mission narratives from raw signals.
    Uses Layer 2 of the Skills System for cost-effective generation.
    """
    
    def __init__(self, skill_router=None):
        self.skill_router = skill_router
        self.templates = MISSION_TEMPLATES
    
    def match_template(self, signal: RawSignal) -> Optional[MissionTemplate]:
        """Match a signal to the best mission template."""
        for mission_type, template in self.templates.items():
            conditions = template.trigger_conditions
            
            # Check signal type matches
            if conditions.get("signal_type") != signal.signal_type:
                continue
            
            # Check source matches
            source_match = (
                conditions.get("source") == signal.source or
                signal.source in conditions.get("sources", [])
            )
            if not source_match:
                continue
            
            # Template-specific condition checks
            if self._check_conditions(signal, conditions):
                return template
        
        return None
    
    def _check_conditions(self, signal: RawSignal, conditions: dict) -> bool:
        """Check template-specific conditions against signal data."""
        data = signal.data
        
        # Check minimum thresholds
        if "min_vessels_dark" in conditions:
            if data.get("vessels_dark", 0) < conditions["min_vessels_dark"]:
                return False
        
        if "min_ai_jobs" in conditions:
            if data.get("ai_jobs", 0) < conditions["min_ai_jobs"]:
                return False
        
        if "min_spike_percent" in conditions:
            if data.get("spike_percent", 0) < conditions["min_spike_percent"]:
                return False
        
        if "min_drop_percent" in conditions:
            if data.get("drop_percent", 0) < conditions["min_drop_percent"]:
                return False
        
        if "min_usd_value" in conditions:
            if data.get("usd_value", 0) < conditions["min_usd_value"]:
                return False
        
        # Check keyword matches
        if "location_keywords" in conditions:
            location = data.get("location", "").lower()
            if not any(kw in location for kw in conditions["location_keywords"]):
                return False
        
        if "keywords" in conditions:
            text = str(data).lower()
            if not any(kw in text for kw in conditions["keywords"]):
                return False
        
        return True
    
    async def generate_narrative(
        self, 
        signal: RawSignal, 
        template: MissionTemplate
    ) -> str:
        """Generate narrative using LLM (Layer 2)."""
        if self.skill_router:
            # Use Skills System for generation
            context = {
                "task": "generate_mission_narrative",
                "signal": signal.__dict__,
                "template": template.__dict__,
            }
            result = await self.skill_router.route(
                context=context,
                agent_type="director",
                decision_type="narrative_generation",
                min_layer=2,
            )
            return result.get("narrative", "")
        else:
            # Fallback: Simple template interpolation
            return template.description_template.format(**signal.data)
    
    async def analyse(self, signal: RawSignal) -> Optional[GeneratedMission]:
        """Analyse a signal and generate a mission if appropriate."""
        template = self.match_template(signal)
        if not template:
            logger.debug(f"No template matched for signal {signal.signal_id}")
            return None
        
        # Generate narrative
        narrative = await self.generate_narrative(signal, template)
        
        # Fill in template placeholders
        title = template.title_template.format(**signal.data)
        description = template.description_template.format(**signal.data)
        market_question = template.market_question_template.format(**signal.data)
        
        # Create mission
        mission = GeneratedMission(
            mission_id=f"mission_{uuid4().hex[:12]}",
            mission_type=template.mission_type,
            title=title,
            description=description,
            market_question=market_question,
            trigger_signal=signal,
            narrative=narrative,
            objectives=self._generate_objectives(template, signal),
            rewards={
                "completion": template.reward_pool * 0.5,
                "accuracy_bonus": template.reward_pool * 0.3,
                "speed_bonus": template.reward_pool * 0.2,
            },
            betting_options=self._generate_betting_options(template, signal),
            duration_hours=template.default_duration_hours,
            time_pressure=signal.severity,
        )
        
        logger.info(f"🎯 Generated mission: {mission.title}")
        return mission
    
    def _generate_objectives(
        self, 
        template: MissionTemplate, 
        signal: RawSignal
    ) -> list[str]:
        """Generate mission objectives based on template and signal."""
        objectives = [
            f"Monitor {signal.source} for updates",
            "Position before resolution deadline",
        ]
        
        if "shark" in template.required_agents:
            objectives.append("Identify and exploit liquidity gaps")
        if "spy" in template.required_agents:
            objectives.append("Gather additional intelligence")
        if "diplomat" in template.required_agents:
            objectives.append("Coordinate with allied agents")
        if "saboteur" in template.required_agents:
            objectives.append("Watch for disinformation campaigns")
        
        return objectives
    
    def _generate_betting_options(
        self, 
        template: MissionTemplate, 
        signal: RawSignal
    ) -> list[dict]:
        """Generate betting options for the mission market."""
        # Default binary market
        options = [
            {"option": "YES", "initial_price": 0.5},
            {"option": "NO", "initial_price": 0.5},
        ]
        
        # Some missions have multiple outcomes
        if template.mission_type == MissionType.GHOST_TANKER:
            options = [
                {"option": "China", "initial_price": 0.4},
                {"option": "Cuba", "initial_price": 0.2},
                {"option": "Intercepted", "initial_price": 0.2},
                {"option": "Other", "initial_price": 0.2},
            ]
        elif template.mission_type == MissionType.SILICON_ACQUISITION:
            options = [
                {"option": "OpenAI", "initial_price": 0.3},
                {"option": "Anthropic", "initial_price": 0.25},
                {"option": "In-house", "initial_price": 0.25},
                {"option": "No acquisition", "initial_price": 0.2},
            ]
        
        return options


# =============================================================================
# Publisher (Game State)
# =============================================================================

class MissionPublisher:
    """
    Publishes generated missions to the game state.
    Deploys markets, notifies agents, updates UI.
    """
    
    def __init__(
        self,
        market_deployer: Optional[Callable] = None,
        agent_notifier: Optional[Callable] = None,
        ui_updater: Optional[Callable] = None,
    ):
        self.market_deployer = market_deployer
        self.agent_notifier = agent_notifier
        self.ui_updater = ui_updater
        self.active_missions: dict[str, GeneratedMission] = {}
    
    async def publish(self, mission: GeneratedMission) -> dict:
        """Publish a mission to the game."""
        results = {
            "mission_id": mission.mission_id,
            "status": "published",
            "market_deployed": False,
            "agents_notified": False,
            "ui_updated": False,
        }
        
        # Deploy prediction market
        if self.market_deployer:
            try:
                market_result = await self.market_deployer(mission)
                results["market_deployed"] = True
                results["market_id"] = market_result.get("market_id")
            except Exception as e:
                logger.error(f"Failed to deploy market: {e}")
        
        # Notify agents
        if self.agent_notifier:
            try:
                await self.agent_notifier(mission)
                results["agents_notified"] = True
            except Exception as e:
                logger.error(f"Failed to notify agents: {e}")
        
        # Update UI
        if self.ui_updater:
            try:
                await self.ui_updater(mission)
                results["ui_updated"] = True
            except Exception as e:
                logger.error(f"Failed to update UI: {e}")
        
        # Track active mission
        mission.status = "active"
        self.active_missions[mission.mission_id] = mission
        
        logger.info(f"📢 Published mission: {mission.title}")
        return results
    
    def get_active_missions(self) -> list[GeneratedMission]:
        """Get all currently active missions."""
        return [m for m in self.active_missions.values() if m.status == "active"]
    
    def resolve_mission(self, mission_id: str, outcome: str) -> dict:
        """Resolve a mission with final outcome."""
        if mission_id in self.active_missions:
            mission = self.active_missions[mission_id]
            mission.status = "resolved"
            logger.info(f"✅ Resolved mission: {mission.title} -> {outcome}")
            return {"status": "resolved", "outcome": outcome}
        return {"status": "not_found"}


# =============================================================================
# Mission Factory (Orchestrator)
# =============================================================================

class MissionFactory:
    """
    Orchestrates the Listener → Analyser → Publisher pipeline.
    
    Usage:
        factory = MissionFactory()
        factory.register_listener(MarketListener())
        factory.register_listener(ChaosListener())
        await factory.run()
    """
    
    def __init__(self, skill_router=None):
        self.listeners: list[BaseListener] = []
        self.analyser = MissionAnalyser(skill_router)
        self.publisher = MissionPublisher()
        self.signal_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
    
    def register_listener(self, listener: BaseListener):
        """Register a new listener."""
        self.listeners.append(listener)
        logger.info(f"Registered listener: {listener.source_name}")
    
    def set_market_deployer(self, deployer: Callable):
        """Set the market deployment callback."""
        self.publisher.market_deployer = deployer
    
    def set_agent_notifier(self, notifier: Callable):
        """Set the agent notification callback."""
        self.publisher.agent_notifier = notifier
    
    def set_ui_updater(self, updater: Callable):
        """Set the UI update callback."""
        self.publisher.ui_updater = updater
    
    def _on_signal(self, signal: RawSignal):
        """Callback when a listener produces a signal."""
        self.signal_queue.put_nowait(signal)
        logger.debug(f"Signal queued: {signal.signal_id} from {signal.source}")
    
    async def _process_signals(self):
        """Process signals from the queue."""
        while self.is_running:
            try:
                signal = await asyncio.wait_for(
                    self.signal_queue.get(), 
                    timeout=1.0
                )
                
                # Analyse signal
                mission = await self.analyser.analyse(signal)
                
                if mission:
                    # Publish mission
                    await self.publisher.publish(mission)
                
                self.signal_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing signal: {e}")
    
    async def run(self):
        """Run the mission factory."""
        self.is_running = True
        logger.info("🚀 Mission Factory starting...")
        
        # Start all listeners
        listener_tasks = [
            asyncio.create_task(listener.run(self._on_signal))
            for listener in self.listeners
        ]
        
        # Start signal processor
        processor_task = asyncio.create_task(self._process_signals())
        
        # Wait for all tasks
        try:
            await asyncio.gather(*listener_tasks, processor_task)
        except asyncio.CancelledError:
            logger.info("Mission Factory shutting down...")
        finally:
            self.is_running = False
            for listener in self.listeners:
                listener.stop()
    
    def stop(self):
        """Stop the mission factory."""
        self.is_running = False
        for listener in self.listeners:
            listener.stop()
    
    def get_active_missions(self) -> list[GeneratedMission]:
        """Get all active missions."""
        return self.publisher.get_active_missions()
    
    async def inject_test_signal(self, signal: RawSignal):
        """Inject a test signal for development."""
        self._on_signal(signal)


# =============================================================================
# Example Usage
# =============================================================================

async def example_usage():
    """Demonstrate the Mission Factory."""
    
    # Create factory
    factory = MissionFactory()
    
    # Register listeners
    factory.register_listener(MarketListener())
    factory.register_listener(ChaosListener())
    factory.register_listener(OnChainListener())
    
    # Set up callbacks (in production, these would connect to real systems)
    async def deploy_market(mission):
        print(f"📊 Deploying market: {mission.market_question}")
        return {"market_id": f"market_{uuid4().hex[:8]}"}
    
    async def notify_agents(mission):
        print(f"🔔 Notifying agents about: {mission.title}")
    
    async def update_ui(mission):
        print(f"🖥️ Updating Situation Room: {mission.title}")
    
    factory.set_market_deployer(deploy_market)
    factory.set_agent_notifier(notify_agents)
    factory.set_ui_updater(update_ui)
    
    # Inject test signals
    print("\n" + "="*60)
    print("MISSION FACTORY TEST")
    print("="*60)
    
    # Test 1: Ghost Tanker signal
    tanker_signal = RawSignal.create(
        signal_type=SignalType.CHAOS,
        source="spire_ais",
        data={
            "vessels_dark": 4,
            "location": "Strait of Hormuz",
            "vessel_id": "VLCC-2847",
            "destination": "Unknown",
            "vessel_count": 4,
        },
        severity=0.8,
    )
    
    await factory.inject_test_signal(tanker_signal)
    await asyncio.sleep(0.5)  # Let it process
    
    # Test 2: Whale Alert signal
    whale_signal = RawSignal.create(
        signal_type=SignalType.ONCHAIN,
        source="whale_alert",
        data={
            "amount": 50000,
            "token": "BTC",
            "usd_value": 2_500_000_000,  # $2.5B
            "destination": "Unknown Wallet",
            "from": "Binance",
        },
        severity=0.9,
    )
    
    await factory.inject_test_signal(whale_signal)
    await asyncio.sleep(0.5)
    
    # Process signals
    await factory._process_signals.__wrapped__(factory)  # Run one iteration
    
    # Show active missions
    missions = factory.get_active_missions()
    print(f"\n📋 Active Missions: {len(missions)}")
    for m in missions:
        print(f"   - {m.title} (Time pressure: {m.time_pressure:.0%})")


if __name__ == "__main__":
    asyncio.run(example_usage())
