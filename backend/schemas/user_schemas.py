from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class WatchlistItemType(str, Enum):
    AGENT = "AGENT"
    TIMELINE = "TIMELINE"

# ============================================
# USER POSITION
# ============================================

class UserPosition(BaseModel):
    """A user's position in a timeline."""
    timeline_id: str
    timeline_name: str
    
    # Position
    side: str  # "YES" or "NO"
    shards_held: int
    average_entry_price: float
    current_price: float
    
    # P&L
    unrealised_pnl_usd: float
    unrealised_pnl_percent: float
    
    # Risk
    timeline_stability: float
    has_active_paradox: bool
    hours_until_reaper: Optional[float] = None
    
    # Founder status
    is_founder: bool = False
    founder_yield_earned_usd: float = 0

class UserPositionsResponse(BaseModel):
    """All user positions."""
    positions: List[UserPosition]
    total_value_usd: float
    total_unrealised_pnl_usd: float
    total_founder_yield_usd: float

# ============================================
# PRIVATE FORK (User Simulation)
# ============================================

class PrivateFork(BaseModel):
    """A user's private simulation (not public)."""
    id: str
    name: str
    narrative: str  # "What if Tesla acquires Rivian?"
    created_at: datetime
    
    # State
    status: str  # "DRAFT", "RUNNING", "COMPLETE"
    stability: float
    
    # Results (if complete)
    simulation_result: Optional[str] = None
    
    # Publish option
    can_publish: bool = True
    publish_cost_echelon: float = 100

class PrivateForkCreateRequest(BaseModel):
    """Create a new private simulation."""
    name: str
    narrative: str
    base_timeline_id: str  # Fork from this

class PrivateForksResponse(BaseModel):
    """User's private forks."""
    forks: List[PrivateFork]
    total_count: int
    max_allowed: int = 5  # Free tier limit

# ============================================
# WATCHLIST
# ============================================

class WatchlistItem(BaseModel):
    """An item on user's watchlist."""
    id: str
    item_type: WatchlistItemType
    item_id: str  # Agent ID or Timeline ID
    item_name: str
    added_at: datetime
    
    # Current state (populated at query time)
    current_stability: Optional[float] = None  # For timelines
    current_sanity: Optional[int] = None       # For agents
    recent_activity: Optional[str] = None      # Last action

class WatchlistAddRequest(BaseModel):
    """Add item to watchlist."""
    item_type: WatchlistItemType
    item_id: str

class WatchlistResponse(BaseModel):
    """User's watchlist."""
    items: List[WatchlistItem]
    total_count: int
    max_allowed: int = 20  # Free tier limit

# ============================================
# PORTFOLIO SUMMARY
# ============================================

class PortfolioSummary(BaseModel):
    """Overview of user's entire portfolio."""
    # Value
    total_value_usd: float
    total_unrealised_pnl_usd: float
    total_unrealised_pnl_percent: float
    
    # Positions
    active_position_count: int
    timelines_at_risk: int  # Positions with stability < 30%
    
    # Founder earnings
    total_founder_yield_earned_usd: float
    active_founder_positions: int
    
    # Risk exposure
    highest_risk_timeline_id: Optional[str] = None
    highest_risk_timeline_name: Optional[str] = None
    highest_risk_stability: Optional[float] = None



