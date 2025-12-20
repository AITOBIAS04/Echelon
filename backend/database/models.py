"""
SQLAlchemy Models for Echelon
==============================

All database models for the Echelon prediction market platform.
Uses SQLAlchemy 2.0 async-compatible syntax.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
import enum

from .connection import Base

# ============================================
# ENUMS
# ============================================

class AgentArchetype(str, enum.Enum):
    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"
    WHALE = "WHALE"
    DEGEN = "DEGEN"

class WingFlapType(str, enum.Enum):
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"
    PARADOX = "PARADOX"
    FOUNDER_YIELD = "FOUNDER_YIELD"
    ENTROPY = "ENTROPY"  # System-generated stability decay

class ParadoxStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXTRACTING = "EXTRACTING"
    DETONATED = "DETONATED"
    RESOLVED = "RESOLVED"

class SeverityClass(str, enum.Enum):
    CLASS_1_CRITICAL = "CLASS_1_CRITICAL"
    CLASS_2_SEVERE = "CLASS_2_SEVERE"
    CLASS_3_MODERATE = "CLASS_3_MODERATE"
    CLASS_4_MINOR = "CLASS_4_MINOR"

# ============================================
# USER
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(20), default="free")
    balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    balance_echelon: Mapped[int] = mapped_column(Integer, default=0)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents: Mapped[List["Agent"]] = relationship(back_populates="owner")
    positions: Mapped[List["UserPosition"]] = relationship(back_populates="user")
    watchlist_items: Mapped[List["WatchlistItem"]] = relationship(back_populates="user")
    private_forks: Mapped[List["PrivateFork"]] = relationship(back_populates="user")

# ============================================
# TIMELINE
# ============================================

class Timeline(Base):
    __tablename__ = "timelines"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    narrative: Mapped[str] = mapped_column(Text)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Core metrics
    stability: Mapped[float] = mapped_column(Float, default=50.0)
    surface_tension: Mapped[float] = mapped_column(Float, default=50.0)
    price_yes: Mapped[float] = mapped_column(Float, default=0.5)
    price_no: Mapped[float] = mapped_column(Float, default=0.5)
    
    # OSINT alignment
    osint_alignment: Mapped[float] = mapped_column(Float, default=50.0)
    logic_gap: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Gravity
    gravity_score: Mapped[float] = mapped_column(Float, default=0.0)
    gravity_factors: Mapped[dict] = mapped_column(JSON, default={})
    
    # Liquidity
    total_volume_usd: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity_depth_usd: Mapped[float] = mapped_column(Float, default=0.0)
    active_agent_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Decay
    decay_rate_per_hour: Mapped[float] = mapped_column(Float, default=1.0)
    decay_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Founder
    founder_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("users.id"), nullable=True)
    founder_yield_rate: Mapped[float] = mapped_column(Float, default=0.001)
    
    # Relationships
    parent_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("timelines.id"), nullable=True)
    connected_timeline_ids: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Status
    has_active_paradox: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    wing_flaps: Mapped[List["WingFlap"]] = relationship(back_populates="timeline")
    paradoxes: Mapped[List["Paradox"]] = relationship(back_populates="timeline")
    
    # Indexes
    __table_args__ = (
        Index("ix_timelines_gravity", "gravity_score"),
        Index("ix_timelines_stability", "stability"),
        Index("ix_timelines_active", "is_active"),
    )

# ============================================
# AGENT
# ============================================

class Agent(Base):
    __tablename__ = "agents"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    archetype: Mapped[AgentArchetype] = mapped_column(SQLEnum(AgentArchetype))
    tier: Mapped[int] = mapped_column(Integer, default=1)
    level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    sanity: Mapped[int] = mapped_column(Integer, default=100)
    max_sanity: Mapped[int] = mapped_column(Integer, default=100)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    death_cause: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Owner
    owner_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="agents")
    
    # Wallet
    wallet_address: Mapped[str] = mapped_column(String(100))
    
    # Performance
    total_pnl_usd: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    trades_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Genome (for breeding/evolution)
    genome: Mapped[dict] = mapped_column(JSON, default={})
    
    # Lineage
    parent_agent_ids: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wing_flaps: Mapped[List["WingFlap"]] = relationship(back_populates="agent")
    
    # Indexes
    __table_args__ = (
        Index("ix_agents_owner", "owner_id"),
        Index("ix_agents_archetype", "archetype"),
        Index("ix_agents_alive", "is_alive"),
    )

# ============================================
# WING FLAP (Causality Event)
# ============================================

# Helper function for WingFlap default timestamp (must be defined outside class)
def _wingflap_default_timestamp() -> datetime:
    """Return a naive UTC datetime for database compatibility."""
    return datetime.utcnow().replace(tzinfo=None)

class WingFlap(Base):
    __tablename__ = "wing_flaps"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    # Default timestamp (naive datetime for TIMESTAMP WITHOUT TIME ZONE)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_wingflap_default_timestamp, index=True)
    
    # Timeline
    timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"), index=True)
    timeline: Mapped["Timeline"] = relationship(back_populates="wing_flaps")
    
    # Agent
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), index=True)
    agent: Mapped["Agent"] = relationship(back_populates="wing_flaps")
    
    # Event details
    flap_type: Mapped[WingFlapType] = mapped_column(SQLEnum(WingFlapType))
    action: Mapped[str] = mapped_column(Text)
    
    # Impact
    stability_delta: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(20))  # ANCHOR or DESTABILISE
    volume_usd: Mapped[float] = mapped_column(Float)
    
    # State after flap
    timeline_stability: Mapped[float] = mapped_column(Float)
    timeline_price: Mapped[float] = mapped_column(Float)
    
    # Ripple
    spawned_ripple: Mapped[bool] = mapped_column(Boolean, default=False)
    ripple_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Founder yield
    founder_yield_earned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_wing_flaps_timeline_time", "timeline_id", "timestamp"),
        Index("ix_wing_flaps_agent_time", "agent_id", "timestamp"),
        Index("ix_wing_flaps_type", "flap_type"),
    )

# ============================================
# PARADOX (Containment Breach)
# ============================================

class Paradox(Base):
    __tablename__ = "paradoxes"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Timeline
    timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"), index=True)
    timeline: Mapped["Timeline"] = relationship(back_populates="paradoxes")
    
    # Status
    status: Mapped[ParadoxStatus] = mapped_column(SQLEnum(ParadoxStatus), default=ParadoxStatus.ACTIVE)
    severity_class: Mapped[SeverityClass] = mapped_column(SQLEnum(SeverityClass))
    logic_gap: Mapped[float] = mapped_column(Float)
    
    # Timing
    spawned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detonation_time: Mapped[datetime] = mapped_column(DateTime)
    
    # Decay
    decay_multiplier: Mapped[float] = mapped_column(Float, default=5.0)
    
    # Costs
    extraction_cost_usdc: Mapped[float] = mapped_column(Float)
    extraction_cost_echelon: Mapped[int] = mapped_column(Integer)
    carrier_sanity_cost: Mapped[int] = mapped_column(Integer)
    
    # Carrier
    carrier_agent_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("agents.id"), nullable=True)
    
    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_paradoxes_status", "status"),
        Index("ix_paradoxes_timeline", "timeline_id"),
    )

# ============================================
# USER POSITION
# ============================================

class UserPosition(Base):
    __tablename__ = "user_positions"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # User
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="positions")
    
    # Timeline
    timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"), index=True)
    
    # Position
    side: Mapped[str] = mapped_column(String(10))  # YES or NO
    shards_held: Mapped[int] = mapped_column(Integer, default=0)
    average_entry_price: Mapped[float] = mapped_column(Float)
    
    # Founder status
    is_founder: Mapped[bool] = mapped_column(Boolean, default=False)
    founder_yield_earned_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        Index("ix_user_positions_user_timeline", "user_id", "timeline_id", unique=True),
    )

# ============================================
# WATCHLIST
# ============================================

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # User
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="watchlist_items")
    
    # Item
    item_type: Mapped[str] = mapped_column(String(20))  # AGENT or TIMELINE
    item_id: Mapped[str] = mapped_column(String(50))
    
    # Timestamps
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        Index("ix_watchlist_user_item", "user_id", "item_type", "item_id", unique=True),
    )

# ============================================
# PRIVATE FORK
# ============================================

class PrivateFork(Base):
    __tablename__ = "private_forks"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # User
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="private_forks")
    
    # Fork details
    name: Mapped[str] = mapped_column(String(255))
    narrative: Mapped[str] = mapped_column(Text)
    base_timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"))
    
    # State
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    stability: Mapped[float] = mapped_column(Float, default=50.0)
    simulation_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Publishing
    can_publish: Mapped[bool] = mapped_column(Boolean, default=True)
    published_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

