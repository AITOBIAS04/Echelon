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
import uuid

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
    # --- Original 010b types ---
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"
    PARADOX = "PARADOX"
    FOUNDER_YIELD = "FOUNDER_YIELD"
    ENTROPY = "ENTROPY"  # System-generated stability decay
    # --- 016 Coherence Lock additions ---
    MIRROR_SYNC = "MIRROR_SYNC"        # Polymarket price sync (no trade)
    MIRROR_TRADE = "MIRROR_TRADE"      # Polymarket trade mirrored into anchor
    EVIDENCE = "EVIDENCE"              # OSINT evidence ingestion
    CLAIM = "CLAIM"                    # Claim submitted to timeline
    COUNTER_SIGNAL = "COUNTER_SIGNAL"  # Counter-evidence against claim
    CORROBORATION = "CORROBORATION"    # Evidence corroborating existing claim
    DETONATION = "DETONATION"          # Paradox detonation (timeline collapse)
    FORK_SPAWN = "FORK_SPAWN"          # Fork created from anchor
    STOP_CONDITION = "STOP_CONDITION"  # Investigation stop condition met
    CERTIFICATE = "CERTIFICATE"        # Verification certificate issued


class FlapDirection(str, enum.Enum):
    """Direction of a Wing Flap's stability impact."""
    STABILISE = "STABILISE"      # Positive stability impact
    DESTABILISE = "DESTABILISE"  # Negative stability impact
    NEUTRAL = "NEUTRAL"          # Sync / lifecycle — no stability change

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
    
    # Core metrics (0.0–1.0 scale; migration normalises legacy 0–100 values)
    stability: Mapped[float] = mapped_column(Float, default=0.5)
    surface_tension: Mapped[float] = mapped_column(Float, default=0.5)
    price_yes: Mapped[float] = mapped_column(Float, default=0.5)
    price_no: Mapped[float] = mapped_column(Float, default=0.5)
    
    # OSINT alignment (0.0–1.0 scale)
    osint_alignment: Mapped[float] = mapped_column(Float, default=0.5)
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

    # Anchor / fork model (016 Coherence Lock)
    is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)
    anchor_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("timelines.id"), nullable=True)
    fork_divergence: Mapped[float] = mapped_column(Float, default=0.0)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ── Cycle-017: TAO Flow ──
    net_inflow_24h: Mapped[float] = mapped_column(Float, default=0.0)
    net_inflow_7d: Mapped[float] = mapped_column(Float, default=0.0)
    flow_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    has_active_paradox: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    wing_flaps: Mapped[List["WingFlap"]] = relationship(back_populates="timeline")
    paradoxes: Mapped[List["Paradox"]] = relationship(back_populates="timeline")

    # Indexes
    __table_args__ = (
        Index("ix_timelines_gravity", "gravity_score"),
        Index("ix_timelines_stability", "stability"),
        Index("ix_timelines_active", "is_active"),
        Index("ix_timelines_anchor", "is_anchor"),
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
    direction: Mapped[str] = mapped_column(String(20))  # STABILISE, DESTABILISE, or NEUTRAL
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

# ============================================
# VERIFICATION (echelon-verify integration)
# ============================================

class VerificationRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    INGESTING = "INGESTING"
    INVOKING = "INVOKING"
    SCORING = "SCORING"
    CERTIFYING = "CERTIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class VerificationCertificate(Base):
    __tablename__ = "verification_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str] = mapped_column(String(50), default="community_oracle")
    replay_count: Mapped[int] = mapped_column(Integer)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    reply_accuracy: Mapped[float] = mapped_column(Float)
    composite_score: Mapped[float] = mapped_column(Float)
    brier: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    ground_truth_source: Mapped[str] = mapped_column(String(500))
    commit_range: Mapped[str] = mapped_column(String(255))
    methodology_version: Mapped[str] = mapped_column(String(20))
    scoring_model: Mapped[str] = mapped_column(String(100))
    raw_scores_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped[Optional["VerificationRun"]] = relationship(back_populates="certificate")
    replay_scores: Mapped[List["VerificationReplayScore"]] = relationship(
        back_populates="certificate"
    )

    __table_args__ = (
        Index("ix_verification_certs_construct_created", "construct_id", "created_at"),
        Index("ix_verification_certs_brier", "brier"),
    )


class VerificationReplayScore(Base):
    __tablename__ = "verification_replay_scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    certificate_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("verification_certificates.id"), index=True
    )
    ground_truth_id: Mapped[str] = mapped_column(String(255))
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    reply_accuracy: Mapped[float] = mapped_column(Float)
    claims_total: Mapped[int] = mapped_column(Integer)
    claims_supported: Mapped[int] = mapped_column(Integer)
    changes_total: Mapped[int] = mapped_column(Integer)
    changes_surfaced: Mapped[int] = mapped_column(Integer)
    scoring_model: Mapped[str] = mapped_column(String(100))
    scoring_latency_ms: Mapped[int] = mapped_column(Integer)
    scored_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    certificate: Mapped["VerificationCertificate"] = relationship(
        back_populates="replay_scores"
    )


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[VerificationRunStatus] = mapped_column(
        SQLEnum(VerificationRunStatus), default=VerificationRunStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("verification_certificates.id"), nullable=True
    )
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    certificate: Mapped[Optional["VerificationCertificate"]] = relationship(
        back_populates="run"
    )

    __table_args__ = (
        Index("ix_verification_runs_status", "status"),
        Index("ix_verification_runs_user_created", "user_id", "created_at"),
        Index("ix_verification_runs_construct", "construct_id"),
    )


# ============================================
# THEATRE (Theatre Template Engine — Cycle-031)
# ============================================

class TheatreTemplate(Base):
    __tablename__ = "theatre_templates"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    template_family: Mapped[str] = mapped_column(String(50))
    execution_path: Mapped[str] = mapped_column(String(10))
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20))
    inquiry_class: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, server_default="COUNTERFACTUAL"
    )
    template_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    theatres: Mapped[List["Theatre"]] = relationship(back_populates="template")

    __table_args__ = (
        Index("ix_theatre_templates_family", "template_family"),
        Index("ix_theatre_templates_execution_path", "execution_path"),
        Index("ix_theatre_templates_inquiry_class", "inquiry_class"),
    )


class Theatre(Base):
    __tablename__ = "theatres"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("theatre_templates.id"), index=True
    )
    state: Mapped[str] = mapped_column(String(20), default="DRAFT")
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    inquiry_class: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, server_default="COUNTERFACTUAL"
    )

    # Commitment fields (populated on COMMITTED transition)
    commitment_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version_pins: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    dataset_hashes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Investigation stop condition (set on creation, included in commitment hash)
    stop_condition: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    stop_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Scenario pack provenance (cycle-018)
    spawned_from_checkpoint_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id"), nullable=True
    )

    # Paradox risk surface (cycle-019)
    paradox_risk_level: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="LOW | WATCH | HIGH"
    )
    paradox_risk_factors_json: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="logic_gap, stability, counter_signals_material, evidence_freshness_hours, active_paradox"
    )
    paradox_risk_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Execution tracking
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total_episodes: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatre_certificates.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    template: Mapped["TheatreTemplate"] = relationship(back_populates="theatres")
    certificate: Mapped[Optional["TheatreCertificate"]] = relationship(
        back_populates="theatre"
    )
    episode_scores: Mapped[List["TheatreEpisodeScore"]] = relationship(
        back_populates="theatre"
    )
    audit_events: Mapped[List["TheatreAuditEvent"]] = relationship(
        back_populates="theatre"
    )

    __table_args__ = (
        Index("ix_theatres_state", "state"),
        Index("ix_theatres_construct", "construct_id"),
        Index("ix_theatres_user_created", "user_id", "created_at"),
        Index("ix_theatres_inquiry_class", "inquiry_class"),
    )


class TheatreCertificate(Base):
    __tablename__ = "theatre_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(String(50), index=True)
    template_id: Mapped[str] = mapped_column(String(100), index=True)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)
    inquiry_class: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, server_default="COUNTERFACTUAL"
    )

    # Criteria & scores
    criteria_json: Mapped[dict] = mapped_column(JSON)
    scores_json: Mapped[dict] = mapped_column(JSON)
    composite_score: Mapped[float] = mapped_column(Float)

    # Calibration (optional)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reply_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ece: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Evidence
    replay_count: Mapped[int] = mapped_column(Integer)
    evidence_bundle_hash: Mapped[str] = mapped_column(String(64))
    ground_truth_hash: Mapped[str] = mapped_column(String(64))

    # Reproducibility
    construct_version: Mapped[str] = mapped_column(String(64))
    construct_chain_versions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scorer_version: Mapped[str] = mapped_column(String(100))
    methodology_version: Mapped[str] = mapped_column(String(20))
    dataset_hash: Mapped[str] = mapped_column(String(64))

    # Trust
    verification_tier: Mapped[str] = mapped_column(String(20))
    commitment_hash: Mapped[str] = mapped_column(String(64))

    # Timestamps
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    theatre_committed_at: Mapped[datetime] = mapped_column(DateTime)
    theatre_resolved_at: Mapped[datetime] = mapped_column(DateTime)

    # Integration
    ground_truth_source: Mapped[str] = mapped_column(String(100))
    execution_path: Mapped[str] = mapped_column(String(10))

    # ── Cycle-017: Policy Surface ──
    routing_hint: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True)
    review_reason_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True)
    coherence_review_required: Mapped[bool] = mapped_column(
        Boolean, default=False)
    coherence_gate_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True)
    coherence_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)
    coherence_reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True)

    # Relationships
    theatre: Mapped[Optional["Theatre"]] = relationship(back_populates="certificate")
    episode_scores: Mapped[List["TheatreEpisodeScore"]] = relationship(
        back_populates="certificate"
    )

    __table_args__ = (
        Index("ix_theatre_certs_construct_created", "construct_id", "issued_at"),
        Index("ix_theatre_certs_tier", "verification_tier"),
        Index("ix_theatre_certs_template", "template_id"),
        Index("ix_theatre_certs_routing_hint", "routing_hint"),
    )


class TheatreEpisodeScore(Base):
    __tablename__ = "theatre_episode_scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatre_certificates.id"), nullable=True, index=True
    )
    episode_id: Mapped[str] = mapped_column(String(255))
    invocation_status: Mapped[str] = mapped_column(String(20))
    latency_ms: Mapped[int] = mapped_column(Integer)
    scores_json: Mapped[dict] = mapped_column(JSON)
    composite_score: Mapped[float] = mapped_column(Float)
    scored_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    theatre: Mapped["Theatre"] = relationship(back_populates="episode_scores")
    certificate: Mapped[Optional["TheatreCertificate"]] = relationship(
        back_populates="episode_scores"
    )


class TheatreAuditEvent(Base):
    __tablename__ = "theatre_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    from_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    theatre: Mapped["Theatre"] = relationship(back_populates="audit_events")

    __table_args__ = (
        Index("ix_theatre_audit_theatre_created", "theatre_id", "created_at"),
    )


# ============================================
# SCENARIO PACK MODELS (Cycle-018)
# ============================================

class ScenarioPackTemplate(Base):
    """Immutable template definition for a scenario pack."""
    __tablename__ = "scenario_pack_templates"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    family: Mapped[str] = mapped_column(String(20))
    fantasy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    training_primitives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON blobs matching existing theatre fixture shape
    objective_vector_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fork_point_schema_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    saboteur_deck_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    telemetry_spec_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    settlement_rules_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Meta
    episode_length_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fork_points_min: Mapped[int] = mapped_column(Integer, default=1)
    fork_points_max: Mapped[int] = mapped_column(Integer, default=10)
    settlement_latency_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    template_status: Mapped[str] = mapped_column(
        String(20), default="CATALOG_ONLY",
    )
    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    packs: Mapped[List["ScenarioPack"]] = relationship(back_populates="template")
    checkpoints: Mapped[List["ScenarioCheckpoint"]] = relationship(
        back_populates="template", order_by="ScenarioCheckpoint.sequence_num"
    )

    __table_args__ = (
        Index("ix_scenario_pack_templates_family", "family"),
        Index("ix_scenario_pack_templates_status", "template_status"),
    )


class ScenarioCheckpoint(Base):
    """A decision point within a scenario pack template."""
    __tablename__ = "scenario_checkpoints"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("scenario_pack_templates.id"), index=True
    )
    sequence_num: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String(255))
    trigger_condition_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    market_question: Mapped[str] = mapped_column(Text)
    decision_window_sec: Mapped[int] = mapped_column(Integer, default=30)
    can_spawn_theatre: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluator_type: Mapped[str] = mapped_column(String(30), default="BINARY_RISK_GATE")
    theatre_spawn_rule_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reward_mapping_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    template: Mapped["ScenarioPackTemplate"] = relationship(back_populates="checkpoints")
    branches: Mapped[List["CheckpointBranch"]] = relationship(
        back_populates="checkpoint",
        foreign_keys="CheckpointBranch.checkpoint_id"
    )

    __table_args__ = (
        Index("ix_scenario_checkpoints_template_seq", "template_id", "sequence_num"),
    )


class CheckpointBranch(Base):
    """An outcome path from a checkpoint."""
    __tablename__ = "checkpoint_branches"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    checkpoint_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    branch_rule_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outcome_type: Mapped[str] = mapped_column(String(20))
    reward_mapping_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    next_checkpoint_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id"), nullable=True
    )

    # Relationships
    checkpoint: Mapped["ScenarioCheckpoint"] = relationship(
        back_populates="branches", foreign_keys=[checkpoint_id]
    )


class ScenarioPack(Base):
    """A user-created instance of a scenario pack from a template."""
    __tablename__ = "scenario_packs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("scenario_pack_templates.id"), index=True
    )
    state: Mapped[str] = mapped_column(String(20), default="DRAFT", index=True)
    commitment_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Run configuration
    run_mode: Mapped[str] = mapped_column(String(30), default="TRAINING")
    agent_assignment: Mapped[str] = mapped_column(String(50), default="auto_assign")
    simulation_scale: Mapped[str] = mapped_column(String(20), default="single_1x")
    objective_profile: Mapped[str] = mapped_column(String(50), default="pack_default")
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    template: Mapped["ScenarioPackTemplate"] = relationship(back_populates="packs")
    runs: Mapped[List["ScenarioRun"]] = relationship(back_populates="pack")
    audit_events: Mapped[List["ScenarioPackAuditEvent"]] = relationship(back_populates="pack")

    __table_args__ = (
        Index("ix_scenario_packs_user", "user_id"),
        Index("ix_scenario_packs_template", "template_id"),
    )


class ScenarioRun(Base):
    """A single execution of a scenario pack through checkpoints."""
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    pack_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_packs.id"), index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    environment_seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    run_mode: Mapped[str] = mapped_column(String(20), default="TRAINING")
    current_checkpoint_seq: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    telemetry_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    episode_duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_reward: Mapped[float] = mapped_column(Float, default=0.0)
    source_run_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("scenario_runs.id"), nullable=True,
        comment="For REPLAY mode: the source run whose recorded path is replayed"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    pack: Mapped["ScenarioPack"] = relationship(back_populates="runs")
    checkpoint_results: Mapped[List["RunCheckpointResult"]] = relationship(
        back_populates="run", order_by="RunCheckpointResult.resolved_at"
    )

    __table_args__ = (
        Index("ix_scenario_runs_pack", "pack_id"),
        Index("ix_scenario_runs_status", "status"),
    )


class RunCheckpointResult(Base):
    """The outcome at a specific checkpoint during a run."""
    __tablename__ = "run_checkpoint_results"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    run_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_runs.id"), index=True
    )
    checkpoint_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_checkpoints.id")
    )
    selected_branch_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("checkpoint_branches.id")
    )
    agent_decision_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    state_vector_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    spawned_theatre_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatres.id"), nullable=True
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["ScenarioRun"] = relationship(back_populates="checkpoint_results")

    __table_args__ = (
        Index("ix_run_checkpoint_results_run", "run_id"),
    )


class ScenarioPackAuditEvent(Base):
    """Audit trail for scenario pack lifecycle events."""
    __tablename__ = "scenario_pack_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    pack_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scenario_packs.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    pack: Mapped["ScenarioPack"] = relationship(back_populates="audit_events")

    __table_args__ = (
        Index("ix_scenario_pack_audit_pack_created", "pack_id", "created_at"),
    )


# ============================================
# AGENT DEPLOYMENT (Cycle 019)
# ============================================

class AgentDeployment(Base):
    """Agent-to-theatre deployment with strategy profile."""
    __tablename__ = "agent_deployments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    agent_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("agents.id"), index=True
    )
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", index=True,
        comment="ACTIVE | PAUSED | WITHDRAWN"
    )
    strategy_profile: Mapped[str] = mapped_column(
        String(20), default="BALANCED",
        comment="BALANCED | AGGRESSIVE | DEFENSIVE"
    )
    deployed_by: Mapped[str] = mapped_column(String(50), index=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Snapshot of theatre state at deployment time
    routing_hint_snapshot: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="ALLOWED | REVIEW_REQUIRED | BLOCKED at deploy time"
    )
    coherence_gate_status_snapshot: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="PENDING | PASSED | FAILED at deploy time"
    )

    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent: Mapped["Agent"] = relationship()
    theatre: Mapped["Theatre"] = relationship()
    audit_events: Mapped[List["DeploymentAuditEvent"]] = relationship(
        back_populates="deployment"
    )

    __table_args__ = (
        Index("ix_agent_deployments_active", "agent_id", "theatre_id", "status"),
    )


class DeploymentAuditEvent(Base):
    """Audit trail for agent deployment lifecycle events."""
    __tablename__ = "deployment_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    deployment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("agent_deployments.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), index=True,
        comment="DEPLOYED | STRATEGY_CHANGED | PAUSED | RESUMED | WITHDRAWN"
    )
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    deployment: Mapped["AgentDeployment"] = relationship(back_populates="audit_events")


# ============================================
# INVESTIGATION PERSISTENCE (Cycle 019)
# ============================================

class Investigation(Base):
    """Persisted investigation record — replaces in-memory dict."""
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(String(50), default="", index=True)
    construct_id: Mapped[str] = mapped_column(String(100), default="")
    inquiry_class: Mapped[str] = mapped_column(
        String(30), default="INVESTIGATIVE",
        comment="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", index=True,
        comment="ACTIVE | CERTIFICATE_READY | COMPLETED"
    )
    domain_filters_json: Mapped[list] = mapped_column(JSON, default=list)
    stop_condition: Mapped[str] = mapped_column(
        String(30), default="OUTCOME_RESOLUTION",
        comment="OUTCOME_RESOLUTION | EVIDENCE_THRESHOLD | SPONSOR_DEFINED"
    )
    stop_config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Stop condition evaluation (cycle-021)
    stop_condition_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="NOT_READY | READY"
    )
    stop_condition_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stop_condition_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    evidence_items: Mapped[List["InvestigationEvidenceItem"]] = relationship(
        back_populates="investigation", order_by="InvestigationEvidenceItem.submitted_at"
    )
    claim_nodes: Mapped[List["InvestigationClaimNode"]] = relationship(
        back_populates="investigation"
    )
    counter_signals: Mapped[List["InvestigationCounterSignal"]] = relationship(
        back_populates="investigation", order_by="InvestigationCounterSignal.detected_at"
    )
    drift_events: Mapped[List["InvestigationDriftEvent"]] = relationship(
        back_populates="investigation", order_by="InvestigationDriftEvent.detected_at"
    )
    certificate: Mapped[Optional["InvestigationCertificateRecord"]] = relationship(
        back_populates="investigation", uselist=False
    )



class InvestigationEvidenceItem(Base):
    """Persisted evidence item for an investigation."""
    __tablename__ = "investigation_evidence_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_class: Mapped[str] = mapped_column(
        String(30),
        comment="public_primary | public_secondary | private_leak | analyst_derived | third_party_tool_output"
    )
    content_type: Mapped[str] = mapped_column(String(50), default="text/plain")
    source_description: Mapped[str] = mapped_column(Text, default="")
    source_id: Mapped[str] = mapped_column(String(100), default="")
    query_determinism: Mapped[str] = mapped_column(String(30), default="")
    references_json: Mapped[list] = mapped_column(JSON, default=list)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="evidence_items")


class InvestigationClaimNode(Base):
    """Persisted claim node for an investigation."""
    __tablename__ = "investigation_claim_nodes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(
        String(20), comment="fact | causal | attribution"
    )
    evidence_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    counter_signals_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(30), default="UNCONFIRMED",
        comment="SUPPORTED | PARTIALLY_SUPPORTED | UNCONFIRMED | CONTRADICTED"
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    independence_groups_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="claim_nodes")


class InvestigationCounterSignal(Base):
    """Persisted counter-signal for an investigation."""
    __tablename__ = "investigation_counter_signals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    signal_class: Mapped[str] = mapped_column(
        String(50),
        comment="11 classes: OFFICIAL_DENIAL through WITNESS_SOURCE_RECANTATION"
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_impact: Mapped[str] = mapped_column(Text, default="")
    detection_method: Mapped[str] = mapped_column(
        String(30), default="human_submitted",
        comment="automated_osint | paradox_engine | human_submitted"
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="counter_signals")


class InvestigationDriftEvent(Base):
    """Persisted drift event for an investigation."""
    __tablename__ = "investigation_drift_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), index=True
    )
    drift_type: Mapped[str] = mapped_column(
        String(30),
        comment="ENTITY_RESTRUCTURE | CONTRACT_AMENDMENT | MARKET_RULE_CHANGE | REGULATORY_STATUS_CHANGE | JURISDICTION_CHANGE"
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    original_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impact_assessment: Mapped[str] = mapped_column(
        String(20), default="non_material",
        comment="material | non_material"
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="drift_events")


class InvestigationCertificateRecord(Base):
    """Persisted certificate record for an investigation (1:1)."""
    __tablename__ = "investigation_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("investigations.id"), unique=True, index=True
    )
    certificate_hash: Mapped[str] = mapped_column(String(64))
    certificate_json: Mapped[dict] = mapped_column(JSON)
    routing_decision: Mapped[str] = mapped_column(
        String(20), comment="ALLOWED | REVIEW_REQUIRED"
    )
    routing_reason: Mapped[str] = mapped_column(String(50), default="")
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Certificate lifecycle (cycle-021)
    certificate_status: Mapped[str] = mapped_column(
        String(20), default="READY", comment="READY | ANCHORED | ISSUED"
    )
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    anchored_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    batch_anchor_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(back_populates="certificate")

