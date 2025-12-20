from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class AgentArchetype(str, Enum):
    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"
    WHALE = "WHALE"
    DEGEN = "DEGEN"

class WingFlapType(str, Enum):
    TRADE = "TRADE"              # Agent executed trade
    SHIELD = "SHIELD"           # User deployed shield
    SABOTAGE = "SABOTAGE"       # Saboteur attack
    RIPPLE = "RIPPLE"           # Fork spawned
    PARADOX = "PARADOX"         # Containment breach
    FOUNDER_YIELD = "FOUNDER_YIELD"  # Yield payout

class StabilityDirection(str, Enum):
    ANCHOR = "ANCHOR"           # Stabilising (positive delta)
    DESTABILISE = "DESTABILISE" # Destabilising (negative delta)

# ============================================
# WING FLAP (Causality Event)
# ============================================

class WingFlap(BaseModel):
    """A single causality event in the Butterfly Engine."""
    id: str
    timestamp: datetime
    timeline_id: str
    timeline_name: str
    
    # Who caused it
    agent_id: str
    agent_name: str
    agent_archetype: AgentArchetype
    
    # What happened
    flap_type: WingFlapType
    action: str  # Human-readable: "MEGALODON bought 500 YES @ $0.67"
    
    # Impact
    stability_delta: float = Field(..., description="Change in stability (-100 to +100)")
    direction: StabilityDirection
    volume_usd: float
    
    # Current state after this flap
    timeline_stability: float = Field(..., ge=0, le=100)
    timeline_price: float = Field(..., ge=0, le=1)
    
    # Ripple info (if this flap spawned a fork)
    spawned_ripple: bool = False
    ripple_timeline_id: Optional[str] = None
    
    # Founder info
    founder_id: Optional[str] = None
    founder_yield_earned: Optional[float] = None

class WingFlapFeedRequest(BaseModel):
    """Request parameters for wing flap feed."""
    timeline_id: Optional[str] = None  # Filter to specific timeline
    agent_id: Optional[str] = None     # Filter to specific agent
    min_stability_delta: float = 0     # Only show events with |delta| > this
    min_volume_usd: float = 0          # Only show events with volume > this
    flap_types: Optional[List[WingFlapType]] = None  # Filter by type
    limit: int = Field(default=50, le=200)
    offset: int = 0

class WingFlapFeedResponse(BaseModel):
    """Response containing wing flaps."""
    flaps: List[WingFlap]
    total_count: int
    has_more: bool

# ============================================
# TIMELINE HEALTH
# ============================================

class TimelineHealth(BaseModel):
    """Health status of a single timeline."""
    id: str
    name: str
    
    # Core metrics
    stability: float = Field(..., ge=0, le=100)
    surface_tension: float = Field(..., ge=0, le=100, description="Decay threshold")
    price_yes: float = Field(..., ge=0, le=1)
    price_no: float = Field(..., ge=0, le=1)
    
    # OSINT alignment
    osint_alignment: float = Field(..., ge=0, le=100, description="How much price matches reality")
    logic_gap: float = Field(..., ge=0, le=1, description="Price vs Reality divergence")
    
    # Gravity (importance score)
    gravity_score: float = Field(..., ge=0, le=100)
    gravity_factors: dict  # { "volume": 30, "agent_count": 20, "volatility": 25, ... }
    
    # Liquidity
    total_volume_usd: float
    liquidity_depth_usd: float
    
    # Agents
    active_agent_count: int
    dominant_agent_id: Optional[str] = None
    dominant_agent_name: Optional[str] = None
    
    # Founder
    founder_id: Optional[str] = None
    founder_name: Optional[str] = None
    founder_yield_rate: float = 0  # % yield per stability point
    
    # Decay
    decay_rate_per_hour: float = 1.0  # Base 1%, increased during paradox
    hours_until_reaper: Optional[float] = None  # None if stable
    
    # Paradox
    has_active_paradox: bool = False
    paradox_id: Optional[str] = None
    paradox_detonation_time: Optional[datetime] = None
    
    # Connections
    connected_timeline_ids: List[str] = []  # For paradox extraction
    parent_timeline_id: Optional[str] = None  # If this is a fork

class TimelineHealthRequest(BaseModel):
    """Request for timeline health data."""
    sort_by: str = "gravity_score"  # gravity_score, stability, volume, decay
    sort_order: str = "desc"
    min_gravity: float = 0
    include_paradox_only: bool = False
    limit: int = Field(default=20, le=100)

class TimelineHealthResponse(BaseModel):
    """Response with timeline health data."""
    timelines: List[TimelineHealth]
    total_count: int

# ============================================
# GRAVITY CALCULATION
# ============================================

class GravityBreakdown(BaseModel):
    """Detailed gravity calculation for a timeline."""
    timeline_id: str
    total_gravity: float
    
    # Component scores (each 0-25, total = 100 max)
    volume_score: float
    agent_activity_score: float
    volatility_score: float
    narrative_relevance_score: float
    
    # Narrative targeting
    related_keywords: List[str]
    osint_sources: List[str]  # Which OSINT feeds mention this
    trending_rank: Optional[int] = None  # Position in trending list

# ============================================
# RIPPLE (Fork Event)
# ============================================

class Ripple(BaseModel):
    """A fork spawned from a Wing Flap."""
    id: str
    parent_timeline_id: str
    child_timeline_id: str
    spawned_at: datetime
    
    # What caused the fork
    trigger_flap_id: str
    trigger_agent_id: str
    trigger_stability_delta: float
    
    # Fork details
    fork_narrative: str  # "What if the Fed cut rates?"
    initial_stability: float
    
    # Founder attribution
    founder_id: str
    founder_stake_usd: float

class RippleListResponse(BaseModel):
    """List of recent ripples (forks)."""
    ripples: List[Ripple]
    total_today: int
    total_all_time: int


