"""
Timeline Fork Manager
=====================

Manages timeline forks with support for both:
1. Global Forks - Shared counterfactual timelines (current implementation)
2. User Forks - Personal "what if" scenarios for individual users

User-specific forks allow:
- Personal counterfactual exploration without affecting global markets
- Practice/simulation mode before committing real capital
- Custom scenario creation for educational purposes
- Private agent training environments

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class ForkType(str, Enum):
    """Type of timeline fork."""
    GLOBAL = "global"           # Shared by all users, real capital
    USER_PRIVATE = "private"    # Single user, simulated capital
    USER_PUBLIC = "public"      # Created by user, others can join
    AGENT_SANDBOX = "sandbox"   # Agent training environment


class ForkStatus(str, Enum):
    """Status of a fork."""
    PENDING = "pending"         # Awaiting VRF seed
    ACTIVE = "active"           # Open for trading
    PAUSED = "paused"           # Temporarily halted
    RESOLVED = "resolved"       # Outcome determined
    REAPED = "reaped"           # Killed by Reality Reaper
    EXPIRED = "expired"         # Time limit reached


class ForkVisibility(str, Enum):
    """Visibility settings for user forks."""
    PRIVATE = "private"         # Only creator can see/trade
    FRIENDS = "friends"         # Creator + approved users
    PUBLIC = "public"           # Anyone can view, trade requires invite
    OPEN = "open"               # Anyone can view and trade


# =============================================================================
# DATA MODELS
# =============================================================================

class ForkPoint(BaseModel):
    """Represents the point where a timeline diverges from reality."""
    
    timestamp: datetime = Field(..., description="When the fork occurred")
    
    # Source market state
    source_market_id: str = Field(..., description="Polymarket/Kalshi market ID")
    source_platform: str = Field(..., description="polymarket or kalshi")
    source_price: Decimal = Field(..., description="Price at fork point")
    source_volume: Decimal = Field(Decimal("0"), description="Volume at fork")
    
    # State hash for verification
    state_hash: str = Field(..., description="Hash of market state at fork")
    
    # The counterfactual premise
    premise: str = Field(..., description="What if scenario description")
    
    # VRF data
    vrf_seed: Optional[str] = Field(None, description="Chainlink VRF seed")
    vrf_request_id: Optional[str] = Field(None, description="VRF request ID")


class UserForkConfig(BaseModel):
    """Configuration for user-specific forks."""
    
    # Ownership
    creator_address: str = Field(..., description="Creator wallet address")
    creator_user_id: Optional[str] = Field(None, description="Platform user ID")
    
    # Visibility and access
    visibility: ForkVisibility = Field(ForkVisibility.PRIVATE)
    allowed_users: list[str] = Field(default_factory=list)
    
    # Capital settings
    simulated_capital: Decimal = Field(Decimal("10000"), description="Starting capital")
    use_real_capital: bool = Field(False, description="Use real USDC")
    
    # Limits
    max_position_size: Decimal = Field(Decimal("1000"))
    max_leverage: Decimal = Field(Decimal("1"))
    
    # Duration
    auto_expire_hours: int = Field(168, description="Auto-expire after N hours (default 7 days)")
    
    # Agent settings
    allow_agents: bool = Field(True, description="Allow AI agents in this fork")
    agent_ids: list[str] = Field(default_factory=list, description="Specific agents to include")


class TimelineFork(BaseModel):
    """Represents a forked timeline (global or user-specific)."""
    
    fork_id: str = Field(..., description="Unique fork identifier")
    
    # Fork type and status
    fork_type: ForkType = Field(ForkType.GLOBAL)
    status: ForkStatus = Field(ForkStatus.PENDING)
    
    # Fork point
    fork_point: ForkPoint = Field(...)
    
    # Parent reference (for nested forks)
    parent_fork_id: Optional[str] = Field(None, description="Parent fork if nested")
    
    # User-specific config (None for global forks)
    user_config: Optional[UserForkConfig] = Field(None)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None)
    resolved_at: Optional[datetime] = Field(None)
    
    # Markets within this fork
    market_ids: list[str] = Field(default_factory=list)
    
    # Metrics
    total_volume: Decimal = Field(Decimal("0"))
    unique_traders: int = Field(0)
    
    # Resolution
    resolution_outcome: Optional[str] = Field(None)
    resolution_source: Optional[str] = Field(None)


class UserForkPosition(BaseModel):
    """User's position in a specific fork."""
    
    user_address: str
    fork_id: str
    
    # Capital tracking
    initial_capital: Decimal = Field(Decimal("0"))
    current_capital: Decimal = Field(Decimal("0"))
    
    # Positions
    positions: dict[str, Decimal] = Field(default_factory=dict)  # market_id -> size
    
    # P&L
    realized_pnl: Decimal = Field(Decimal("0"))
    unrealized_pnl: Decimal = Field(Decimal("0"))
    
    # Activity
    trade_count: int = Field(0)
    last_trade_at: Optional[datetime] = Field(None)


class ForkLeaderboard(BaseModel):
    """Leaderboard for a fork."""
    
    fork_id: str
    
    entries: list["LeaderboardEntry"] = Field(default_factory=list)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""
    
    rank: int
    user_address: str
    
    pnl: Decimal = Field(Decimal("0"))
    pnl_percentage: Decimal = Field(Decimal("0"))
    
    trade_count: int = Field(0)
    win_rate: Decimal = Field(Decimal("0"))


# =============================================================================
# FORK MANAGER
# =============================================================================

class TimelineForkManager:
    """
    Manages timeline forks for the Echelon protocol.
    
    Supports:
    - Global forks: Shared counterfactual markets with real capital
    - User forks: Personal "what if" scenarios
    - Agent sandboxes: Training environments for AI agents
    """
    
    def __init__(
        self,
        vrf_consumer: Optional[Any] = None,
        timeline_shard_contract: Optional[Any] = None,
        storage_backend: Optional[Any] = None
    ):
        self.vrf_consumer = vrf_consumer
        self.timeline_shard = timeline_shard_contract
        self.storage = storage_backend
        
        # In-memory storage (replace with DB in production)
        self._forks: dict[str, TimelineFork] = {}
        self._user_positions: dict[str, dict[str, UserForkPosition]] = {}  # user -> fork_id -> position
        self._fork_markets: dict[str, list[dict]] = {}  # fork_id -> markets
    
    # =========================================================================
    # FORK CREATION
    # =========================================================================
    
    async def create_global_fork(
        self,
        source_market_id: str,
        source_platform: str,
        premise: str,
        duration_hours: int = 48,
        outcomes: list[str] = None
    ) -> TimelineFork:
        """
        Create a global fork from a real market.
        
        This creates a shared counterfactual timeline that all users can trade.
        """
        if outcomes is None:
            outcomes = ["Yes", "No"]
        
        # Generate fork ID
        fork_id = self._generate_fork_id("global", source_market_id, premise)
        
        # Get current market state
        market_state = await self._fetch_market_state(source_market_id, source_platform)
        
        # Create fork point
        fork_point = ForkPoint(
            timestamp=datetime.utcnow(),
            source_market_id=source_market_id,
            source_platform=source_platform,
            source_price=market_state.get("price", Decimal("0.5")),
            source_volume=market_state.get("volume", Decimal("0")),
            state_hash=self._hash_state(market_state),
            premise=premise
        )
        
        # Request VRF seed
        if self.vrf_consumer:
            vrf_request = await self.vrf_consumer.request_timeline_fork(fork_id)
            fork_point.vrf_request_id = vrf_request
        
        # Create fork
        fork = TimelineFork(
            fork_id=fork_id,
            fork_type=ForkType.GLOBAL,
            status=ForkStatus.PENDING if self.vrf_consumer else ForkStatus.ACTIVE,
            fork_point=fork_point,
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
        )
        
        self._forks[fork_id] = fork
        
        # Create markets within fork
        await self._create_fork_markets(fork_id, premise, outcomes)
        
        return fork
    
    async def create_user_fork(
        self,
        user_address: str,
        source_market_id: str,
        source_platform: str,
        premise: str,
        config: Optional[UserForkConfig] = None
    ) -> TimelineFork:
        """
        Create a user-specific fork for personal exploration.
        
        User forks:
        - Use simulated capital by default
        - Are private to the creator
        - Can be shared with friends
        - Auto-expire after configured duration
        """
        if config is None:
            config = UserForkConfig(
                creator_address=user_address,
                visibility=ForkVisibility.PRIVATE,
                simulated_capital=Decimal("10000"),
                use_real_capital=False
            )
        else:
            config.creator_address = user_address
        
        # Generate fork ID
        fork_id = self._generate_fork_id("user", source_market_id, premise, user_address)
        
        # Get current market state
        market_state = await self._fetch_market_state(source_market_id, source_platform)
        
        # Create fork point
        fork_point = ForkPoint(
            timestamp=datetime.utcnow(),
            source_market_id=source_market_id,
            source_platform=source_platform,
            source_price=market_state.get("price", Decimal("0.5")),
            source_volume=market_state.get("volume", Decimal("0")),
            state_hash=self._hash_state(market_state),
            premise=premise
        )
        
        # User forks use deterministic "VRF" based on user + timestamp
        fork_point.vrf_seed = self._generate_user_seed(user_address, fork_id)
        
        # Create fork
        fork = TimelineFork(
            fork_id=fork_id,
            fork_type=ForkType.USER_PRIVATE,
            status=ForkStatus.ACTIVE,
            fork_point=fork_point,
            user_config=config,
            expires_at=datetime.utcnow() + timedelta(hours=config.auto_expire_hours)
        )
        
        self._forks[fork_id] = fork
        
        # Initialize user position
        await self._initialize_user_position(user_address, fork_id, config.simulated_capital)
        
        # Create markets within fork
        await self._create_fork_markets(fork_id, premise, ["Yes", "No"])
        
        return fork
    
    async def create_agent_sandbox(
        self,
        agent_ids: list[str],
        source_market_id: str,
        source_platform: str,
        premise: str,
        training_config: Optional[dict] = None
    ) -> TimelineFork:
        """
        Create a sandbox environment for agent training.
        
        Sandboxes:
        - Are isolated from real markets
        - Can be reset and replayed
        - Track detailed agent metrics
        - Support accelerated time for faster training
        """
        config = UserForkConfig(
            creator_address="system",
            visibility=ForkVisibility.PRIVATE,
            simulated_capital=Decimal("100000"),
            use_real_capital=False,
            allow_agents=True,
            agent_ids=agent_ids,
            auto_expire_hours=24 * 30  # 30 days for training
        )
        
        fork_id = self._generate_fork_id("sandbox", source_market_id, premise)
        
        market_state = await self._fetch_market_state(source_market_id, source_platform)
        
        fork_point = ForkPoint(
            timestamp=datetime.utcnow(),
            source_market_id=source_market_id,
            source_platform=source_platform,
            source_price=market_state.get("price", Decimal("0.5")),
            source_volume=market_state.get("volume", Decimal("0")),
            state_hash=self._hash_state(market_state),
            premise=premise,
            vrf_seed=self._generate_user_seed("sandbox", fork_id)
        )
        
        fork = TimelineFork(
            fork_id=fork_id,
            fork_type=ForkType.AGENT_SANDBOX,
            status=ForkStatus.ACTIVE,
            fork_point=fork_point,
            user_config=config,
            expires_at=datetime.utcnow() + timedelta(hours=config.auto_expire_hours)
        )
        
        self._forks[fork_id] = fork
        
        # Initialize agent positions
        for agent_id in agent_ids:
            await self._initialize_user_position(agent_id, fork_id, config.simulated_capital)
        
        await self._create_fork_markets(fork_id, premise, ["Yes", "No"])
        
        return fork
    
    # =========================================================================
    # FORK OPERATIONS
    # =========================================================================
    
    async def get_fork(self, fork_id: str) -> Optional[TimelineFork]:
        """Get a fork by ID."""
        return self._forks.get(fork_id)
    
    async def get_user_forks(
        self,
        user_address: str,
        include_expired: bool = False
    ) -> list[TimelineFork]:
        """Get all forks created by or accessible to a user."""
        user_forks = []
        
        for fork in self._forks.values():
            # Check if user created it
            if fork.user_config and fork.user_config.creator_address == user_address:
                if include_expired or fork.status == ForkStatus.ACTIVE:
                    user_forks.append(fork)
                continue
            
            # Check if user has access
            if fork.user_config:
                if fork.user_config.visibility == ForkVisibility.OPEN:
                    user_forks.append(fork)
                elif fork.user_config.visibility == ForkVisibility.PUBLIC:
                    user_forks.append(fork)
                elif user_address in fork.user_config.allowed_users:
                    user_forks.append(fork)
            
            # Global forks are always accessible
            if fork.fork_type == ForkType.GLOBAL:
                if include_expired or fork.status == ForkStatus.ACTIVE:
                    user_forks.append(fork)
        
        return user_forks
    
    async def get_global_forks(
        self,
        status: Optional[ForkStatus] = None,
        limit: int = 50
    ) -> list[TimelineFork]:
        """Get global forks."""
        forks = [
            f for f in self._forks.values()
            if f.fork_type == ForkType.GLOBAL
            and (status is None or f.status == status)
        ]
        
        # Sort by volume/activity
        forks.sort(key=lambda f: f.total_volume, reverse=True)
        
        return forks[:limit]
    
    async def can_user_access_fork(
        self,
        user_address: str,
        fork_id: str
    ) -> bool:
        """Check if user can access a fork."""
        fork = self._forks.get(fork_id)
        if not fork:
            return False
        
        # Global forks are always accessible
        if fork.fork_type == ForkType.GLOBAL:
            return True
        
        # Check user config
        if fork.user_config:
            if fork.user_config.creator_address == user_address:
                return True
            if fork.user_config.visibility == ForkVisibility.OPEN:
                return True
            if fork.user_config.visibility == ForkVisibility.PUBLIC:
                return True  # Can view, may need invite to trade
            if user_address in fork.user_config.allowed_users:
                return True
        
        return False
    
    async def can_user_trade_fork(
        self,
        user_address: str,
        fork_id: str
    ) -> bool:
        """Check if user can trade in a fork."""
        fork = self._forks.get(fork_id)
        if not fork:
            return False
        
        if fork.status != ForkStatus.ACTIVE:
            return False
        
        # Global forks - anyone can trade
        if fork.fork_type == ForkType.GLOBAL:
            return True
        
        # User forks - check permissions
        if fork.user_config:
            if fork.user_config.creator_address == user_address:
                return True
            if fork.user_config.visibility == ForkVisibility.OPEN:
                return True
            if user_address in fork.user_config.allowed_users:
                return True
        
        return False
    
    # =========================================================================
    # USER POSITION MANAGEMENT
    # =========================================================================
    
    async def get_user_position(
        self,
        user_address: str,
        fork_id: str
    ) -> Optional[UserForkPosition]:
        """Get user's position in a fork."""
        user_positions = self._user_positions.get(user_address, {})
        return user_positions.get(fork_id)
    
    async def _initialize_user_position(
        self,
        user_address: str,
        fork_id: str,
        initial_capital: Decimal
    ) -> UserForkPosition:
        """Initialize a user's position in a fork."""
        position = UserForkPosition(
            user_address=user_address,
            fork_id=fork_id,
            initial_capital=initial_capital,
            current_capital=initial_capital
        )
        
        if user_address not in self._user_positions:
            self._user_positions[user_address] = {}
        
        self._user_positions[user_address][fork_id] = position
        
        return position
    
    async def update_user_position(
        self,
        user_address: str,
        fork_id: str,
        market_id: str,
        size_delta: Decimal,
        cost: Decimal
    ) -> UserForkPosition:
        """Update user position after a trade."""
        position = await self.get_user_position(user_address, fork_id)
        
        if not position:
            # Auto-initialize for global forks
            fork = self._forks.get(fork_id)
            if fork and fork.fork_type == ForkType.GLOBAL:
                position = await self._initialize_user_position(
                    user_address, fork_id, Decimal("0")
                )
            else:
                raise ValueError("User not initialized in this fork")
        
        # Update position
        current_size = position.positions.get(market_id, Decimal("0"))
        position.positions[market_id] = current_size + size_delta
        
        # Update capital
        position.current_capital -= cost
        position.trade_count += 1
        position.last_trade_at = datetime.utcnow()
        
        return position
    
    async def get_fork_leaderboard(self, fork_id: str) -> ForkLeaderboard:
        """Get leaderboard for a fork."""
        fork = self._forks.get(fork_id)
        if not fork:
            raise ValueError("Fork not found")
        
        entries = []
        
        # Collect all positions in this fork
        for user_address, forks in self._user_positions.items():
            if fork_id in forks:
                position = forks[fork_id]
                
                pnl = position.current_capital - position.initial_capital + position.realized_pnl
                pnl_pct = (pnl / position.initial_capital * 100) if position.initial_capital > 0 else Decimal("0")
                
                entries.append(LeaderboardEntry(
                    rank=0,  # Set below
                    user_address=user_address,
                    pnl=pnl,
                    pnl_percentage=pnl_pct,
                    trade_count=position.trade_count
                ))
        
        # Sort and rank
        entries.sort(key=lambda e: e.pnl, reverse=True)
        for i, entry in enumerate(entries):
            entry.rank = i + 1
        
        return ForkLeaderboard(fork_id=fork_id, entries=entries)
    
    # =========================================================================
    # FORK LIFECYCLE
    # =========================================================================
    
    async def activate_fork(self, fork_id: str, vrf_seed: str) -> TimelineFork:
        """Activate a pending fork with VRF seed."""
        fork = self._forks.get(fork_id)
        if not fork:
            raise ValueError("Fork not found")
        
        if fork.status != ForkStatus.PENDING:
            raise ValueError("Fork is not pending")
        
        fork.fork_point.vrf_seed = vrf_seed
        fork.status = ForkStatus.ACTIVE
        
        return fork
    
    async def resolve_fork(
        self,
        fork_id: str,
        outcome: str,
        source: str = "osint"
    ) -> TimelineFork:
        """Resolve a fork with outcome."""
        fork = self._forks.get(fork_id)
        if not fork:
            raise ValueError("Fork not found")
        
        fork.status = ForkStatus.RESOLVED
        fork.resolved_at = datetime.utcnow()
        fork.resolution_outcome = outcome
        fork.resolution_source = source
        
        return fork
    
    async def reap_fork(self, fork_id: str, reason: str) -> TimelineFork:
        """Kill a fork via Reality Reaper."""
        fork = self._forks.get(fork_id)
        if not fork:
            raise ValueError("Fork not found")
        
        fork.status = ForkStatus.REAPED
        fork.resolved_at = datetime.utcnow()
        fork.resolution_source = f"reaped: {reason}"
        
        return fork
    
    async def expire_old_forks(self) -> int:
        """Expire forks past their expiry time."""
        expired_count = 0
        now = datetime.utcnow()
        
        for fork in self._forks.values():
            if fork.status == ForkStatus.ACTIVE and fork.expires_at:
                if now > fork.expires_at:
                    fork.status = ForkStatus.EXPIRED
                    expired_count += 1
        
        return expired_count
    
    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================
    
    def _generate_fork_id(
        self,
        prefix: str,
        market_id: str,
        premise: str,
        user: str = ""
    ) -> str:
        """Generate unique fork ID."""
        data = f"{prefix}:{market_id}:{premise}:{user}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _hash_state(self, state: dict) -> str:
        """Hash market state for verification."""
        return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()
    
    def _generate_user_seed(self, user: str, fork_id: str) -> str:
        """Generate deterministic seed for user forks."""
        data = f"{user}:{fork_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _fetch_market_state(self, market_id: str, platform: str) -> dict:
        """Fetch current market state from platform."""
        # In production, this would call Polymarket/Kalshi API
        return {
            "market_id": market_id,
            "platform": platform,
            "price": Decimal("0.5"),
            "volume": Decimal("10000"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _create_fork_markets(
        self,
        fork_id: str,
        premise: str,
        outcomes: list[str]
    ) -> list[dict]:
        """Create markets within a fork."""
        markets = []
        
        # Create main counterfactual market
        market = {
            "market_id": f"{fork_id}_main",
            "fork_id": fork_id,
            "question": premise,
            "outcomes": outcomes,
            "created_at": datetime.utcnow().isoformat()
        }
        markets.append(market)
        
        # Could create related markets here
        
        self._fork_markets[fork_id] = markets
        
        fork = self._forks.get(fork_id)
        if fork:
            fork.market_ids = [m["market_id"] for m in markets]
        
        return markets


# =============================================================================
# ANALYSIS: CURRENT VS ENHANCED ARCHITECTURE
# =============================================================================

"""
CURRENT IMPLEMENTATION (TimelineShard.sol):
==========================================

Timeline Struct:
- id, forkPointTimestamp, forkPointStateHash
- parentTimelineId, description, expiryTimestamp
- status, vrfSeed

Issues for User-Specific Forks:
1. No creator/owner field - can't track who created fork
2. No visibility settings - all forks are global
3. No capital segregation - all users share same pool
4. No access control per-fork - anyone can trade
5. Gas costs for many user forks would be prohibitive

ENHANCED ARCHITECTURE (This Module):
===================================

Hybrid Approach:
1. Global Forks → On-chain (TimelineShard.sol)
   - Real capital, shared liquidity
   - VRF-secured, fully verifiable
   - Higher stakes, more expensive

2. User Forks → Off-chain (TimelineForkManager)
   - Simulated capital
   - Personal exploration
   - Cheap to create/discard
   - Can "graduate" to global if popular

3. Agent Sandboxes → Off-chain
   - Training environments
   - Accelerated time
   - Reset capability

Benefits:
- Cost-effective user exploration
- Maintains on-chain integrity for real trading
- Scalable to millions of user forks
- Clear upgrade path from practice to real

RECOMMENDATION:
==============

Keep on-chain for:
- Global forks with real capital
- Final resolution and settlement
- Audit trail and verification

Use off-chain for:
- User-specific exploration
- Practice/simulation
- Agent training
- High-frequency updates

Bridge:
- Popular user forks can be "promoted" to global
- User positions can migrate to on-chain when ready
- Leaderboards can influence global fork creation
"""


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of fork manager."""
    
    manager = TimelineForkManager()
    
    # Create a global fork (would be on-chain in production)
    global_fork = await manager.create_global_fork(
        source_market_id="0x123abc",
        source_platform="polymarket",
        premise="What if the Fed had cut rates in December 2024?",
        duration_hours=48
    )
    print(f"Global fork: {global_fork.fork_id}")
    
    # Create a user-specific fork
    user_fork = await manager.create_user_fork(
        user_address="0xUser123",
        source_market_id="0x456def",
        source_platform="kalshi",
        premise="What if Bitcoin hit $200k by end of 2024?",
        config=UserForkConfig(
            creator_address="0xUser123",
            visibility=ForkVisibility.PRIVATE,
            simulated_capital=Decimal("50000")
        )
    )
    print(f"User fork: {user_fork.fork_id}")
    
    # Get user's forks
    user_forks = await manager.get_user_forks("0xUser123")
    print(f"User has {len(user_forks)} forks")
    
    # Update position
    await manager.update_user_position(
        user_address="0xUser123",
        fork_id=user_fork.fork_id,
        market_id=f"{user_fork.fork_id}_main",
        size_delta=Decimal("100"),
        cost=Decimal("65")
    )
    
    # Get leaderboard
    leaderboard = await manager.get_fork_leaderboard(user_fork.fork_id)
    print(f"Leaderboard entries: {len(leaderboard.entries)}")


if __name__ == "__main__":
    asyncio.run(example_usage())
