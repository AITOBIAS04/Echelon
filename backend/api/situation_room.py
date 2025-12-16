"""
Echelon Situation Room API
==========================

FastAPI router providing all endpoints needed by the Situation Room frontend.

Endpoints:
- /api/situation-room/state - Global state (tension, factions, etc.)
- /api/situation-room/missions - Active missions
- /api/situation-room/intel - Intel market items
- /api/situation-room/treaties - Active treaties
- /api/situation-room/narratives - Storylines
- /api/situation-room/tension - Global tension index
- /api/situation-room/live-feed - Real-time event feed

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/situation-room", tags=["Situation Room"])


# =============================================================================
# MODELS
# =============================================================================

class TensionLevel(str, Enum):
    PEACE = "peace"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
    WAR = "war"


class Faction(BaseModel):
    id: str
    name: str
    power: float = Field(ge=0, le=100)
    color: str
    description: Optional[str] = None


class GlobalState(BaseModel):
    tension_index: float = Field(ge=0, le=100)
    tension_level: TensionLevel
    peace_percentage: float
    chaos_index: float
    factions: list[Faction]
    active_missions: int
    active_agents: int
    last_updated: datetime


class Mission(BaseModel):
    id: str
    title: str
    description: str
    category: str  # "ghost_tanker", "silicon_acquisition", etc.
    status: str  # "active", "completed", "failed"
    tension_impact: float
    reward_pool: float
    time_remaining: Optional[int] = None  # seconds
    participants: int
    created_at: datetime
    
    # Frontend-compatible fields (computed or aliased)
    mission_type: Optional[str] = None  # Maps from category
    base_reward_usdc: Optional[float] = None  # Maps from reward_pool
    codename: Optional[str] = None
    difficulty: Optional[int] = None
    expires_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    assigned_agents: Optional[list[str]] = []
    max_agents: Optional[int] = None
    required_roles: Optional[list[str]] = []
    
    class Config:
        # Allow fields to be computed from other fields
        allow_population_by_field_name = True


class IntelItem(BaseModel):
    id: str
    title: str
    content: str
    source_agent: str
    source_type: str  # "spy", "osint", "intercept"
    accuracy: float = Field(ge=0, le=1)
    price: float
    expires_at: Optional[datetime] = None
    purchased_by: list[str] = []


class Treaty(BaseModel):
    id: str
    name: str
    parties: list[str]  # Agent names or faction IDs
    status: str  # "active", "broken", "pending"
    terms: str
    stability: float = Field(ge=0, le=100)
    escrow_amount: float = Field(default=0.0, description="USDC held in escrow for this treaty")
    created_at: datetime
    expires_at: Optional[datetime] = None


class Narrative(BaseModel):
    id: str
    title: str
    description: str
    chapter: int
    status: str  # "ongoing", "concluded"
    related_missions: list[str]
    tension_arc: list[float]


class LiveEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    title: str
    description: str
    icon: str
    severity: str  # "low", "medium", "high", "critical"
    market_impact: Optional[str] = None


# =============================================================================
# IN-MEMORY STATE (Replace with database in production)
# =============================================================================

class SituationRoomState:
    """Manages the live state of the Situation Room."""
    
    def __init__(self):
        self.tension_index = 35.0
        self.chaos_index = 15.0
        self.last_updated = datetime.utcnow()
        
        self.factions = [
            Faction(id="eastern", name="Eastern Bloc", power=28, color="#ef4444"),
            Faction(id="western", name="Western Alliance", power=25, color="#3b82f6"),
            Faction(id="corporate", name="Corporate", power=22, color="#f59e0b"),
            Faction(id="underground", name="Underground", power=15, color="#8b5cf6"),
            Faction(id="non_aligned", name="Non-Aligned", power=10, color="#6b7280"),
        ]
        
        self.missions: list[Mission] = []
        self.intel_items: list[IntelItem] = []
        self.treaties: list[Treaty] = []
        self.narratives: list[Narrative] = []
        self.live_events: list[LiveEvent] = []
        
        # Initialize with some data
        self._seed_initial_data()
    
    def _seed_initial_data(self):
        """Seed initial missions, intel, etc."""
        now = datetime.utcnow()
        
        # Seed missions
        self.missions = [
            Mission(
                id="mission_001",
                title="Ghost Tanker",
                description="Oil tanker went dark near Strait of Hormuz. Sanctions evasion suspected.",
                category="maritime",
                status="active",
                tension_impact=12.5,
                reward_pool=5000,
                time_remaining=3600,
                participants=23,
                created_at=now - timedelta(hours=2),
                mission_type="intelligence",
                base_reward_usdc=5000.0,
                codename="GHOST_TANKER",
                difficulty=3,
                expires_at=now + timedelta(hours=1),
                duration_minutes=60,
                assigned_agents=[],
                max_agents=5,
                required_roles=["spy", "analyst"]
            ),
            Mission(
                id="mission_002", 
                title="Silicon Acquisition",
                description="Apple posted 50+ AI roles in 48 hours. Major acquisition incoming?",
                category="corporate",
                status="active",
                tension_impact=5.0,
                reward_pool=2500,
                time_remaining=7200,
                participants=45,
                created_at=now - timedelta(hours=1),
                mission_type="intelligence",
                base_reward_usdc=2500.0,
                codename="SILICON_ACQ",
                difficulty=2,
                expires_at=now + timedelta(hours=2),
                duration_minutes=120,
                assigned_agents=[],
                max_agents=3,
                required_roles=["spy"]
            ),
            Mission(
                id="mission_003",
                title="Summit Snub",
                description="Air Force One diverted from scheduled G7 summit. Security threat or deal collapse?",
                category="geopolitical",
                status="active",
                tension_impact=18.0,
                reward_pool=10000,
                time_remaining=1800,
                participants=67,
                created_at=now - timedelta(minutes=30),
                mission_type="assassination",
                base_reward_usdc=10000.0,
                codename="SUMMIT_SNUB",
                difficulty=4,
                expires_at=now + timedelta(minutes=30),
                duration_minutes=30,
                assigned_agents=[],
                max_agents=8,
                required_roles=["spy", "saboteur", "diplomat"]
            ),
        ]
        
        # Seed intel
        self.intel_items = [
            IntelItem(
                id="intel_001",
                title="Tanker Destination Confirmed",
                content="AIS data shows vessel heading to Shanghai, ETA 72 hours.",
                source_agent="SPY_CARDINAL",
                source_type="spy",
                accuracy=0.87,
                price=50,
                expires_at=now + timedelta(hours=6)
            ),
            IntelItem(
                id="intel_002",
                title="Apple Acquisition Target",
                content="Sources indicate Anthropic is the primary target. Board meeting scheduled.",
                source_agent="SPY_ZERO",
                source_type="intercept",
                accuracy=0.72,
                price=150,
                expires_at=now + timedelta(hours=12)
            ),
            IntelItem(
                id="intel_003",
                title="Summit Security Intel",
                content="False alarm. Drone incursion near venue triggered evacuation protocol.",
                source_agent="DIPLOMAT_ENVOY",
                source_type="osint",
                accuracy=0.95,
                price=25,
                expires_at=now + timedelta(hours=2)
            ),
        ]
        
        # Seed treaties with agent names
        self.treaties = [
            Treaty(
                id="treaty_001",
                name="Pacific Trade Accord",
                parties=["CARDINAL", "HAMMERHEAD"],
                status="active",
                terms="Mutual market access, no tariffs on tech exports",
                stability=78,
                escrow_amount=50000.0,
                created_at=now - timedelta(days=30),
                expires_at=now + timedelta(days=60)
            ),
            Treaty(
                id="treaty_002",
                name="Non-Aggression Pact",
                parties=["SHADOW", "PHANTOM"],
                status="active",
                terms="No hostile market operations for 90 days",
                stability=45,
                escrow_amount=25000.0,
                created_at=now - timedelta(days=15),
                expires_at=now + timedelta(days=75)
            ),
            Treaty(
                id="treaty_003",
                name="Intelligence Sharing Agreement",
                parties=["CARDINAL", "SHADOW", "ZERO"],
                status="active",
                terms="Shared OSINT data, coordinated market analysis",
                stability=65,
                escrow_amount=75000.0,
                created_at=now - timedelta(days=7),
                expires_at=now + timedelta(days=30)
            ),
            Treaty(
                id="treaty_004",
                name="Resource Extraction Rights",
                parties=["HAMMERHEAD", "PHANTOM"],
                status="pending",
                terms="Joint mining operations in disputed territories",
                stability=35,
                escrow_amount=100000.0,
                created_at=now - timedelta(days=2),
                expires_at=now + timedelta(days=90)
            ),
            Treaty(
                id="treaty_005",
                name="Mutual Defense Protocol",
                parties=["CARDINAL", "SHADOW"],
                status="broken",
                terms="Defensive alliance against external threats",
                stability=15,
                escrow_amount=0.0,  # Escrow released after violation
                created_at=now - timedelta(days=45),
                expires_at=now - timedelta(days=10)  # Expired
            ),
        ]
        
        # Seed narratives
        self.narratives = [
            Narrative(
                id="narrative_001",
                title="The Tanker War",
                description="A shadow war fought through sanctions evasion and dark fleet operations.",
                chapter=3,
                status="ongoing",
                related_missions=["mission_001"],
                tension_arc=[25, 32, 38, 35]
            ),
            Narrative(
                id="narrative_002",
                title="Silicon Cold War",
                description="Tech giants manoeuvre for AI supremacy through acquisitions and talent wars.",
                chapter=1,
                status="ongoing",
                related_missions=["mission_002"],
                tension_arc=[10, 15, 18]
            ),
        ]
    
    def get_tension_level(self) -> TensionLevel:
        """Convert tension index to level."""
        if self.tension_index < 20:
            return TensionLevel.PEACE
        elif self.tension_index < 40:
            return TensionLevel.ELEVATED
        elif self.tension_index < 60:
            return TensionLevel.HIGH
        elif self.tension_index < 80:
            return TensionLevel.CRITICAL
        else:
            return TensionLevel.WAR
    
    def update_tension(self, delta: float):
        """Update tension index."""
        self.tension_index = max(0, min(100, self.tension_index + delta))
        self.last_updated = datetime.utcnow()
    
    def add_live_event(self, event: LiveEvent):
        """Add event to live feed."""
        self.live_events.insert(0, event)
        # Keep only last 50 events
        self.live_events = self.live_events[:50]


# Global state instance
state = SituationRoomState()

# Ensure state is initialized (in case module is reloaded)
if not state.missions:
    state._seed_initial_data()


# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def tension_ticker():
    """Background task that updates tension and chaos based on OSINT signals and market volatility."""
    # Track previous signal count for decay detection
    previous_signal_count = 0
    previous_signal_ids = set()
    
    while True:
        try:
            from backend.core.osint_registry import get_osint_registry
            osint_registry = get_osint_registry()
            
            # ACTUALLY POLL FOR NEW SIGNALS (every 30 seconds)
            print(f"🔍 [TENSION] Polling for new OSINT signals...")
            new_signals = await osint_registry.scan_all()
            print(f"📡 [TENSION] Found {len(new_signals)} signals from scan")
            
            # Get current active signals
            current_signal_ids = {s.id for s in osint_registry.active_signals}
            new_signal_count = len(current_signal_ids - previous_signal_ids)
            signal_count = len(osint_registry.active_signals)
            
            current_tension = state.tension_index
            
            # Calculate signal-based tension impact from actual signals
            signal_impact = 0.0
            if signal_count > 0:
                # Get priority signals (sorted by severity/confidence)
                priority_signals = osint_registry.get_priority_signals(limit=20)
                total_signal_impact = 0.0
                
                for signal in priority_signals:
                    # Signal impact based on severity level and confidence
                    # Severity: 1=low, 2=medium, 3=high, 4=critical
                    severity = getattr(signal, 'severity', 1)
                    if isinstance(severity, str):
                        # Convert string severity to number
                        severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                        severity = severity_map.get(severity.lower(), 1)
                    
                    confidence = getattr(signal, 'confidence', 0.5)
                    if confidence > 1.0:
                        confidence = confidence / 100.0  # Normalize if percentage
                    
                    # Impact: severity * confidence, capped at 5% per signal
                    signal_strength = severity * confidence
                    impact = min(5.0, signal_strength * 1.25)  # Cap at 5% per signal
                    total_signal_impact += impact
                    print(f"  📊 Signal {signal.id}: severity={severity}, confidence={confidence:.2f}, impact={impact:.2f}%")
                
                # Cap total signal impact at 30%
                signal_impact = min(30.0, total_signal_impact)
                print(f"📈 [TENSION] Total signal impact: {signal_impact:.2f}%")
            
            # Calculate mission impact
            active_mission_count = len([m for m in state.missions if m.status in ["active", "in_progress"]])
            mission_impact = min(10.0, active_mission_count * 1.5)  # Max 10% from missions
            
            # Calculate target tension from signals and missions
            base_tension_from_signals = 35.0 + signal_impact + mission_impact
            
            # Apply decay or increase based on new signals
            if new_signal_count == 0 and signal_count <= previous_signal_count:
                # Decay: decrease by 0.5% per tick towards baseline of 35%
                if current_tension > 35.0:
                    new_tension = max(35.0, current_tension - 0.5)
                    print(f"📉 [TENSION] Decay: {current_tension:.1f}% → {new_tension:.1f}%")
                else:
                    new_tension = 35.0
            else:
                # New signals detected - use damping formula for smooth changes
                target_tension = base_tension_from_signals
                new_tension = (current_tension * 0.85) + (target_tension * 0.15)  # Faster response
                print(f"📈 [TENSION] Increase: {current_tension:.1f}% → {new_tension:.1f}% (target: {target_tension:.1f}%)")
            
            # Clamp to valid range
            state.tension_index = max(0.0, min(100.0, new_tension))
            
            # Calculate chaos index based on:
            # 1. Market volatility (price swings)
            # 2. Signal activity
            # 3. Treaty breaks
            # 4. Mission failures
            
            chaos_components = []
            
            # 1. Market volatility
            try:
                # Import EventOrchestrator directly to avoid circular imports
                from backend.core.event_orchestrator import EventOrchestrator
                orchestrator = EventOrchestrator()
                
                market_volatility = 0.0
                
                if orchestrator and hasattr(orchestrator, 'markets') and orchestrator.markets:
                    # Calculate average price volatility across markets
                    volatility_sum = 0.0
                    market_count = 0
                    
                    for market_id, market in orchestrator.markets.items():
                        if hasattr(market, 'outcome_odds') and market.outcome_odds:
                            # Calculate volatility as spread between YES and NO odds
                            yes_odds = market.outcome_odds.get('YES', 0.5)
                            no_odds = market.outcome_odds.get('NO', 0.5)
                            spread = abs(yes_odds - no_odds)
                            # Low spread = high volatility (uncertainty)
                            volatility = (1.0 - spread) * 100  # Convert to 0-100 scale
                            volatility_sum += volatility
                            market_count += 1
                    
                    if market_count > 0:
                        market_volatility = volatility_sum / market_count
                        chaos_components.append(("market_volatility", market_volatility))
                        print(f"📊 [CHAOS] Market volatility: {market_volatility:.1f}%")
            except Exception as e:
                print(f"⚠️ [CHAOS] Failed to calculate market volatility: {e}")
            
            # 2. Signal activity (new signals increase chaos)
            signal_chaos = min(50.0, signal_count * 3.0 + new_signal_count * 10.0)
            chaos_components.append(("signal_activity", signal_chaos))
            
            # 3. Treaty breaks
            broken_treaties = len([t for t in state.treaties if t.status == "broken"])
            treaty_chaos = broken_treaties * 15.0
            chaos_components.append(("treaty_breaks", treaty_chaos))
            
            # 4. Mission failures (expired or failed missions)
            failed_missions = len([m for m in state.missions if m.status in ["expired", "failed"]])
            mission_chaos = failed_missions * 5.0
            chaos_components.append(("mission_failures", mission_chaos))
            
            # Combine chaos components (weighted average)
            total_chaos = sum(comp[1] for comp in chaos_components) / max(1, len(chaos_components))
            state.chaos_index = min(100.0, total_chaos)
            
            print(f"🌪️ [CHAOS] Updated: {state.chaos_index:.1f}% (components: {chaos_components})")
            
            # Track signal count for next iteration
            previous_signal_count = signal_count
            previous_signal_ids = current_signal_ids
            
        except Exception as e:
            import traceback
            print(f"❌ [TENSION] Error in tension_ticker: {e}")
            print(traceback.format_exc())
            # Fallback: gentle decay if OSINT fails
            current_tension = state.tension_index
            if current_tension > 35.0:
                state.tension_index = max(35.0, current_tension - 0.5)
            else:
                state.tension_index = 35.0
            state.chaos_index = max(0.0, state.chaos_index - 1.0)  # Decay chaos too
        
        # Wait 30 seconds before next poll
        await asyncio.sleep(30)
        
        # Occasionally generate events
        if random.random() < 0.3:
            event_templates = [
                ("📈", "MARKET_SPIKE", "Volatility Alert", "Unusual price movement detected in {market}"),
                ("🚢", "DARK_FLEET", "Vessel Alert", "AIS signal lost for tanker near {location}"),
                ("✈️", "VIP_MOVEMENT", "Flight Tracked", "Private jet departed {location} heading {direction}"),
                ("🐋", "WHALE_ALERT", "Large Transfer", "{amount} USDC moved to {exchange}"),
                ("📰", "NEWS_BREAK", "Breaking News", "Reports emerging of {event}"),
                ("🔄", "SENTIMENT_SHIFT", "Sentiment Change", "Social media sentiment shifted {direction} on {topic}"),
            ]
            
            template = random.choice(event_templates)
            
            # Fill in placeholders
            markets = ["BTC-USD", "ETH-USD", "Oil Futures", "Gold", "S&P 500"]
            locations = ["Strait of Hormuz", "South China Sea", "Geneva", "Davos", "Singapore"]
            directions = ["north", "south", "bearish", "bullish"]
            events = ["diplomatic tensions", "trade deal progress", "military exercises", "central bank meeting"]
            topics = ["Fed policy", "China relations", "crypto regulation", "oil prices"]
            
            description = template[3].format(
                market=random.choice(markets),
                location=random.choice(locations),
                direction=random.choice(directions),
                amount=f"${random.randint(1, 50)}M",
                exchange=random.choice(["Binance", "Coinbase", "Unknown Wallet"]),
                event=random.choice(events),
                topic=random.choice(topics)
            )
            
            event = LiveEvent(
                id=f"event_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
                event_type=template[1],
                title=template[2],
                description=description,
                icon=template[0],
                severity=random.choice(["low", "medium", "high"])
            )
            
            state.add_live_event(event)
        
        await asyncio.sleep(5)  # Update every 5 seconds


# Start background task when module loads
_ticker_task = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.on_event("startup")
async def startup():
    """Start background tasks on router startup."""
    global _ticker_task
    
    # Reset tension to baseline if it's stuck at 100%
    if state.tension_index >= 100.0:
        print("⚠️  Tension was at 100%, resetting to baseline 35%")
        state.tension_index = 35.0
    
    if _ticker_task is None:
        _ticker_task = asyncio.create_task(tension_ticker())
        print("✅ Situation Room background tasks started")


@router.get("/state", response_model=GlobalState)
async def get_state():
    """Get the current global state of the Situation Room."""
    # Get OSINT signals for the frontend
    recent_signals = []
    try:
        from backend.core.osint_registry import get_osint_registry
        osint_registry = get_osint_registry()
        # Get top 20 most recent/important signals
        top_signals = sorted(
            osint_registry.active_signals,
            key=lambda s: (s.level * s.confidence, s.timestamp),
            reverse=True
        )[:20]
        recent_signals = [s.to_dict() for s in top_signals]
    except Exception as e:
        print(f"⚠️ Error fetching OSINT signals: {e}")
    
    # Create response with signals included
    response = GlobalState(
        tension_index=state.tension_index,
        tension_level=state.get_tension_level(),
        peace_percentage=100 - state.tension_index,
        chaos_index=state.chaos_index,
        factions=state.factions,
        active_missions=len([m for m in state.missions if m.status == "active"]),
        active_agents=88,  # From your screenshot
        last_updated=state.last_updated
    )
    
    # Add signals as a dict field (not in the model, but we'll return it)
    response_dict = response.dict()
    response_dict["recent_signals"] = recent_signals
    return response_dict


@router.get("/tension")
async def get_tension():
    """Get the current global tension index."""
    return {
        "tension_index": state.tension_index,
        "tension_level": state.get_tension_level().value,
        "peace_percentage": 100 - state.tension_index,
        "chaos_index": state.chaos_index,
        "trend": "rising" if random.random() > 0.5 else "falling",
        "last_updated": state.last_updated.isoformat()
    }


@router.get("/missions", response_model=list[Mission])
async def get_missions(status: Optional[str] = None):
    """Get all missions, optionally filtered by status."""
    missions = state.missions
    if status:
        missions = [m for m in missions if m.status == status]
    
    # Ensure all missions have frontend-required fields
    category_to_type = {
        "maritime": "intelligence",
        "corporate": "intelligence",
        "geopolitical": "assassination",
        "intelligence": "intelligence",
        "assassination": "assassination",
        "sabotage": "sabotage",
    }
    
    enriched_missions = []
    for m in missions:
        # Create a dict from the mission
        mission_dict = m.dict() if hasattr(m, 'dict') else m
        
        # Fill in missing fields
        if not mission_dict.get("mission_type"):
            mission_dict["mission_type"] = category_to_type.get(mission_dict.get("category", ""), "intelligence")
        if not mission_dict.get("base_reward_usdc"):
            mission_dict["base_reward_usdc"] = mission_dict.get("reward_pool", 0.0)
        if not mission_dict.get("codename"):
            mission_dict["codename"] = mission_dict.get("id", "").upper().replace("MISSION_", "")
        if not mission_dict.get("difficulty"):
            # Derive difficulty from tension_impact
            impact = mission_dict.get("tension_impact", 0)
            mission_dict["difficulty"] = min(5, max(1, int(impact / 5)))
        if not mission_dict.get("expires_at") and mission_dict.get("time_remaining"):
            # Calculate expires_at from time_remaining
            expires_dt = datetime.utcnow() + timedelta(seconds=mission_dict["time_remaining"])
            mission_dict["expires_at"] = expires_dt
        if not mission_dict.get("duration_minutes") and mission_dict.get("time_remaining"):
            mission_dict["duration_minutes"] = mission_dict["time_remaining"] // 60
        if not mission_dict.get("assigned_agents"):
            mission_dict["assigned_agents"] = []
        if not mission_dict.get("max_agents"):
            mission_dict["max_agents"] = mission_dict.get("participants", 0) + 2
        if not mission_dict.get("required_roles"):
            # Default required roles based on category
            category = mission_dict.get("category", "")
            if category == "geopolitical":
                mission_dict["required_roles"] = ["spy", "saboteur"]
            elif category == "corporate":
                mission_dict["required_roles"] = ["spy"]
            else:
                mission_dict["required_roles"] = ["spy", "analyst"]
        
        enriched_missions.append(Mission(**mission_dict))
    
    return enriched_missions


@router.post("/missions/{mission_id}/accept")
async def accept_mission(mission_id: str, wallet_address: Optional[str] = None):
    """Accept a mission and assign it to the user."""
    print(f"🔍 [ACCEPT] Accepting mission {mission_id} for wallet: {wallet_address}")
    
    # Find the mission
    for mission in state.missions:
        if mission.id == mission_id:
            # Check if mission is still active
            if mission.status != "active":
                print(f"❌ [ACCEPT] Mission {mission_id} is not active (status: {mission.status})")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Mission {mission_id} is not active (status: {mission.status})"
                )
            
            # Check if mission has expired
            if mission.expires_at and mission.expires_at < datetime.utcnow():
                mission.status = "expired"
                print(f"❌ [ACCEPT] Mission {mission_id} has expired")
                raise HTTPException(
                    status_code=400,
                    detail=f"Mission {mission_id} has expired"
                )
            
            # Check if max agents reached
            if mission.max_agents and len(mission.assigned_agents) >= mission.max_agents:
                print(f"❌ [ACCEPT] Mission {mission_id} is full (max agents: {mission.max_agents})")
                raise HTTPException(
                    status_code=400,
                    detail=f"Mission {mission_id} is full (max agents: {mission.max_agents})"
                )
            
            # Add wallet address to assigned agents if provided
            if wallet_address:
                wallet_lower = wallet_address.lower()
                if not mission.assigned_agents:
                    mission.assigned_agents = []
                # Check if already assigned (case-insensitive)
                if wallet_lower not in [addr.lower() for addr in mission.assigned_agents]:
                    mission.assigned_agents.append(wallet_address)
                    print(f"✅ [ACCEPT] Added wallet {wallet_address} to mission {mission_id}")
                else:
                    print(f"⚠️ [ACCEPT] Wallet {wallet_address} already assigned to mission {mission_id}")
            else:
                print(f"⚠️ [ACCEPT] No wallet address provided for mission {mission_id}")
            
            # Update mission status and participants
            mission.participants = len(mission.assigned_agents) if mission.assigned_agents else mission.participants + 1
            if mission.status == "active" and len(mission.assigned_agents) > 0:
                mission.status = "in_progress"
                print(f"✅ [ACCEPT] Mission {mission_id} status changed to in_progress")
            
            print(f"✅ [ACCEPT] Mission {mission_id} accepted. Assigned agents: {mission.assigned_agents}")
            return {
                "status": "accepted",
                "mission_id": mission_id,
                "title": mission.title,
                "message": f"Mission '{mission.title}' accepted",
                "participants": mission.participants,
                "assigned_agents": mission.assigned_agents
            }
    
    print(f"❌ [ACCEPT] Mission {mission_id} not found")
    raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")


@router.post("/missions/{mission_id}/complete")
async def complete_mission(mission_id: str, wallet_address: str = None):
    """Mark a mission as completed."""
    # Find the mission
    for mission in state.missions:
        if mission.id == mission_id:
            # Check if mission can be completed
            if mission.status not in ["active", "in_progress"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Mission {mission_id} cannot be completed (status: {mission.status})"
                )
            
            # Verify wallet is assigned (if wallet_address provided)
            if wallet_address and mission.assigned_agents:
                if wallet_address not in mission.assigned_agents:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Wallet {wallet_address} is not assigned to this mission"
                    )
            
            # Update mission status
            mission.status = "completed"
            
            # Calculate reward (could be distributed to assigned agents)
            reward_per_agent = mission.reward_pool / max(1, len(mission.assigned_agents)) if mission.assigned_agents else mission.reward_pool
            
            return {
                "status": "completed",
                "mission_id": mission_id,
                "title": mission.title,
                "message": f"Mission '{mission.title}' completed successfully",
                "reward_pool": mission.reward_pool,
                "reward_per_agent": reward_per_agent,
                "assigned_agents": mission.assigned_agents
            }
    
    raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")


@router.post("/missions/{mission_id}/abandon")
async def abandon_mission(mission_id: str, wallet_address: str = None):
    """Abandon a mission (remove assignment)."""
    # Find the mission
    for mission in state.missions:
        if mission.id == mission_id:
            # Check if mission is active or in progress
            if mission.status not in ["active", "in_progress"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Mission {mission_id} cannot be abandoned (status: {mission.status})"
                )
            
            # Remove wallet from assigned agents if provided
            if wallet_address and wallet_address in mission.assigned_agents:
                mission.assigned_agents.remove(wallet_address)
                mission.participants = max(0, mission.participants - 1)
                
                # If no agents assigned, revert to active
                if len(mission.assigned_agents) == 0:
                    mission.status = "active"
            elif wallet_address:
                raise HTTPException(
                    status_code=400,
                    detail=f"Wallet {wallet_address} is not assigned to this mission"
                )
            
            return {
                "status": "abandoned",
                "mission_id": mission_id,
                "title": mission.title,
                "message": f"Mission '{mission.title}' abandoned",
                "participants": mission.participants,
                "assigned_agents": mission.assigned_agents
            }
    
    raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")


@router.get("/my-missions", response_model=list[Mission])
async def get_my_missions(wallet_address: Optional[str] = None):
    """Get missions assigned to a specific wallet address."""
    if not wallet_address:
        return []
    
    # Normalize wallet address (lowercase)
    wallet_lower = wallet_address.lower()
    
    # Filter missions where wallet is in assigned_agents
    my_missions = []
    for mission in state.missions:
        if mission.assigned_agents and wallet_lower in [addr.lower() for addr in mission.assigned_agents]:
            my_missions.append(mission)
    
    # Ensure all missions have frontend-required fields (same as get_missions)
    category_to_type = {
        "maritime": "intelligence",
        "corporate": "intelligence",
        "geopolitical": "assassination",
        "intelligence": "intelligence",
        "assassination": "assassination",
        "sabotage": "sabotage",
    }
    
    enriched_missions = []
    for m in my_missions:
        mission_dict = {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "status": m.status,
            "tension_impact": m.tension_impact,
            "reward_pool": m.reward_pool,
            "time_remaining": m.time_remaining,
            "participants": m.participants,
            "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
            "mission_type": getattr(m, 'mission_type', category_to_type.get(m.category, "intelligence")),
            "base_reward_usdc": getattr(m, 'base_reward_usdc', m.reward_pool),
            "codename": getattr(m, 'codename', m.id.upper()),
            "difficulty": getattr(m, 'difficulty', 1),
            "expires_at": m.expires_at.isoformat() if m.expires_at and hasattr(m.expires_at, 'isoformat') else None,
            "duration_minutes": getattr(m, 'duration_minutes', 60),
            "assigned_agents": m.assigned_agents or [],
            "max_agents": getattr(m, 'max_agents', None),
            "required_roles": getattr(m, 'required_roles', []),
        }
        enriched_missions.append(mission_dict)
    
    return enriched_missions


@router.get("/intel", response_model=list[IntelItem])
async def get_intel():
    """Get available intel items."""
    # Filter out expired intel
    now = datetime.utcnow()
    return [i for i in state.intel_items if not i.expires_at or i.expires_at > now]


@router.post("/intel/{intel_id}/purchase")
async def purchase_intel(intel_id: str, buyer_id: str = "user"):
    """Purchase an intel item."""
    for intel in state.intel_items:
        if intel.id == intel_id:
            if buyer_id not in intel.purchased_by:
                intel.purchased_by.append(buyer_id)
            return {"status": "purchased", "intel": intel}
    return {"status": "not_found"}


@router.get("/treaties", response_model=list[Treaty])
async def get_treaties():
    """Get all treaties."""
    # Ensure datetime fields are properly serialized
    treaties_data = []
    for treaty in state.treaties:
        treaty_dict = {
            "id": treaty.id,
            "name": treaty.name,
            "parties": treaty.parties,
            "status": treaty.status,
            "terms": treaty.terms,
            "stability": treaty.stability,
            "escrow_amount": getattr(treaty, 'escrow_amount', 0.0),
            "created_at": treaty.created_at.isoformat() if hasattr(treaty.created_at, 'isoformat') else str(treaty.created_at),
            "expires_at": treaty.expires_at.isoformat() if treaty.expires_at and hasattr(treaty.expires_at, 'isoformat') else (str(treaty.expires_at) if treaty.expires_at else None),
        }
        treaties_data.append(treaty_dict)
    return treaties_data


@router.get("/narratives", response_model=list[Narrative])
async def get_narratives():
    """Get all storylines/narratives."""
    return state.narratives


@router.get("/live-feed", response_model=list[LiveEvent])
async def get_live_feed(limit: int = 20):
    """Get recent live events."""
    return state.live_events[:limit]


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    
    try:
        while True:
            # Send current state every 2 seconds
            await websocket.send_json({
                "type": "state_update",
                "tension_index": state.tension_index,
                "tension_level": state.get_tension_level().value,
                "active_missions": len([m for m in state.missions if m.status == "active"]),
                "latest_event": state.live_events[0].dict() if state.live_events else None,
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


# =============================================================================
# SIMULATION INTEGRATION
# =============================================================================

@router.post("/simulation/start")
async def start_simulation():
    """Start a new simulation."""
    # This would integrate with your run_simulation.py
    return {
        "status": "started",
        "simulation_id": f"sim_{datetime.utcnow().timestamp()}",
        "message": "Simulation started. Events will appear in live feed."
    }


@router.post("/simulation/inject-event")
async def inject_event(
    event_type: str,
    title: str,
    description: str,
    severity: str = "medium"
):
    """Manually inject an event (for testing)."""
    event = LiveEvent(
        id=f"event_{datetime.utcnow().timestamp()}",
        timestamp=datetime.utcnow(),
        event_type=event_type,
        title=title,
        description=description,
        icon="📡",
        severity=severity
    )
    state.add_live_event(event)
    
    # Update tension based on severity
    tension_delta = {"low": 1, "medium": 3, "high": 5, "critical": 10}.get(severity, 2)
    state.update_tension(tension_delta)
    
    return {"status": "injected", "event": event}



