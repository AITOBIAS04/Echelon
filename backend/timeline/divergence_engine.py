"""
Divergence Engine
=================

The mathematical backbone of the Agent-Powered Butterfly Engine.

This module calculates how agent actions create ripple effects across
timelines, determining when new forks spawn and when impossible 
timelines collapse.

Core Mechanics:
1. Timeline Stability Score - Health of each counterfactual
2. Narrative Gravity - Agents influence what OSINT looks for
3. Founder's Yield - Incentive to create divergence
4. Ripple Propagation - Cross-market cascade effects

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

class TimelineState(str, Enum):
    """Lifecycle states of a timeline."""
    NASCENT = "nascent"           # Just forked, low activity
    ACTIVE = "active"             # Normal trading
    VOLATILE = "volatile"         # High divergence, unstable
    SOLIDIFYING = "solidifying"   # Becoming stable alternate reality
    COLLAPSING = "collapsing"     # OSINT contradicting, dying
    COLLAPSED = "collapsed"       # Dead, settled at 0
    SOLIDIFIED = "solidified"     # Locked in as tradeable reality


@dataclass
class DivergenceConfig:
    """Configuration for the divergence engine."""
    
    # Stability thresholds
    collapse_threshold: float = 0.10      # Below 10% = timeline dies
    solidify_threshold: float = 0.90      # Above 90% = timeline locks
    volatile_threshold: float = 0.30      # Below 30% = volatile state
    
    # Fork creation
    fork_divergence_threshold: float = 0.25  # 25% divergence = new fork possible
    min_liquidity_for_fork: float = 10000    # $10K minimum to spawn fork
    
    # Founder's Yield
    founder_royalty_rate: float = 0.005   # 0.5% of trading fees
    
    # Decay rates (per hour)
    stability_decay_rate: float = 0.02    # Timelines decay without activity
    narrative_gravity_decay: float = 0.05 # Gravity weakens over time
    
    # Coalition multipliers
    solo_impact: float = 1.0
    pair_impact: float = 2.5
    trio_impact: float = 4.0
    coalition_impact: float = 6.0         # 4+ agents
    
    # Cross-archetype bonuses
    shark_spy_bonus: float = 1.5          # "Informed Aggression"
    shark_diplomat_bonus: float = 1.3     # "Coordinated Strike"
    spy_saboteur_bonus: float = 1.4       # "Controlled Chaos"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Timeline:
    """
    Represents a counterfactual timeline (fork).
    
    Each timeline has a stability score that determines its health,
    affected by agent activity and OSINT contradiction.
    """
    id: str
    parent_id: Optional[str]              # None if root (reality)
    fork_point: datetime
    fork_reason: str                      # What caused the divergence
    
    # Core metrics
    stability_score: float = 0.5          # 0-1, starts at 50%
    divergence_score: float = 0.0         # How far from reality (0-1)
    
    # Economic state
    total_liquidity: float = 0.0          # Total $ in markets
    total_volume_24h: float = 0.0         # Recent activity
    
    # Agent metrics
    agent_confidence: float = 0.5         # Weighted agent belief
    active_agents: Set[str] = field(default_factory=set)
    
    # OSINT state
    osint_contradiction_score: float = 0.0  # How much reality disagrees
    narrative_gravity: float = 0.0          # Agent-created attention bias
    
    # Founder tracking
    founder_agent_id: Optional[str] = None
    founder_trade_id: Optional[str] = None
    
    # Lifecycle
    state: TimelineState = TimelineState.NASCENT
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    
    # Child forks
    child_timeline_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.active_agents, list):
            self.active_agents = set(self.active_agents)


@dataclass
class AgentAction:
    """Represents an action taken by an agent."""
    agent_id: str
    agent_archetype: str                  # shark, spy, diplomat, saboteur
    action_type: str                      # trade, intel, treaty, sabotage
    timeline_id: str
    market_id: str
    
    # Trade specifics
    direction: str                        # buy, sell
    size: float                           # Dollar amount
    price: float                          # Execution price
    confidence: float                     # Agent's confidence (0-1)
    
    # Coalition info
    coalition_id: Optional[str] = None
    coalition_members: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RippleEffect:
    """Represents a cascading effect from an agent action."""
    source_action_id: str
    source_timeline_id: str
    
    # What changed
    affected_markets: List[Dict]          # [{market_id, price_change, reason}]
    affected_agents: List[Dict]           # [{agent_id, reaction_type}]
    
    # Timeline impact
    stability_change: float
    divergence_change: float
    
    # Did this create a fork?
    spawned_fork: bool = False
    new_timeline_id: Optional[str] = None
    
    # Narrative gravity shift
    gravity_topics: List[str] = field(default_factory=list)
    gravity_magnitude: float = 0.0


@dataclass
class MarketCorrelation:
    """Defines how markets affect each other."""
    market_a: str
    market_b: str
    correlation: float                    # -1 to 1
    lag_seconds: int = 0                  # Delayed effect


# =============================================================================
# TIMELINE STABILITY CALCULATOR
# =============================================================================

class StabilityCalculator:
    """
    Calculates Timeline Stability Score.
    
    Formula:
        Stability = (Liquidity Depth × Agent Confidence) / (1 + OSINT Contradiction)
    
    Normalised to 0-1 range with sigmoid smoothing.
    """
    
    def __init__(self, config: DivergenceConfig = None):
        self.config = config or DivergenceConfig()
    
    def calculate(self, timeline: Timeline) -> float:
        """
        Calculate the stability score for a timeline.
        
        Higher stability = healthier timeline.
        Lower stability = at risk of collapse.
        """
        # Normalise liquidity (log scale, $1K-$10M range)
        liquidity_factor = self._normalise_liquidity(timeline.total_liquidity)
        
        # Agent confidence is already 0-1
        confidence_factor = timeline.agent_confidence
        
        # OSINT contradiction (0 = no contradiction, 1 = total contradiction)
        contradiction_factor = timeline.osint_contradiction_score
        
        # Apply formula
        numerator = liquidity_factor * confidence_factor
        denominator = 1 + contradiction_factor
        
        raw_stability = numerator / denominator
        
        # Add narrative gravity bonus
        # High gravity = system is "paying attention", stabilising effect
        gravity_bonus = timeline.narrative_gravity * 0.1
        
        # Apply time decay
        hours_inactive = (datetime.now(tz=timezone.utc) - timeline.last_activity).total_seconds() / 3600
        decay_penalty = hours_inactive * self.config.stability_decay_rate
        
        # Final score with bounds
        stability = raw_stability + gravity_bonus - decay_penalty
        stability = max(0.0, min(1.0, stability))
        
        return stability
    
    def _normalise_liquidity(self, liquidity: float) -> float:
        """Convert raw liquidity to 0-1 factor using log scale."""
        if liquidity <= 0:
            return 0.0
        
        # Log scale: $1K = 0.1, $100K = 0.5, $10M = 1.0
        log_liq = math.log10(max(liquidity, 1))
        # Normalise: log10(1000) = 3, log10(10_000_000) = 7
        normalised = (log_liq - 3) / 4  # Maps 3-7 to 0-1
        
        return max(0.0, min(1.0, normalised))
    
    def determine_state(self, timeline: Timeline) -> TimelineState:
        """Determine timeline state based on stability score."""
        stability = timeline.stability_score
        
        if stability < self.config.collapse_threshold:
            return TimelineState.COLLAPSING
        elif stability < self.config.volatile_threshold:
            return TimelineState.VOLATILE
        elif stability > self.config.solidify_threshold:
            return TimelineState.SOLIDIFYING
        else:
            return TimelineState.ACTIVE


# =============================================================================
# RIPPLE PROPAGATION ENGINE
# =============================================================================

class RipplePropagator:
    """
    Calculates how an agent action ripples through the system.
    
    Handles:
    - Cross-market correlations
    - Agent reactions
    - Coalition amplification
    - Timeline divergence changes
    """
    
    def __init__(self, config: DivergenceConfig = None):
        self.config = config or DivergenceConfig()
        
        # Default market correlations (can be loaded from config)
        self.correlations: List[MarketCorrelation] = [
            # Energy correlations
            MarketCorrelation("OIL", "ENERGY_SECTOR", 0.85),
            MarketCorrelation("OIL", "AIRLINES", -0.70),
            MarketCorrelation("OIL", "SHIPPING", 0.60),
            MarketCorrelation("NATURAL_GAS", "ENERGY_SECTOR", 0.75),
            
            # Tech correlations
            MarketCorrelation("TECH_INDEX", "SEMICONDUCTORS", 0.90),
            MarketCorrelation("TECH_INDEX", "CRYPTO", 0.55),
            MarketCorrelation("AI_SECTOR", "SEMICONDUCTORS", 0.80),
            
            # Macro correlations
            MarketCorrelation("FED_RATE", "BONDS", -0.85),
            MarketCorrelation("FED_RATE", "BANKS", 0.65),
            MarketCorrelation("FED_RATE", "REAL_ESTATE", -0.60),
            MarketCorrelation("USD_INDEX", "GOLD", -0.70),
            
            # Geopolitical
            MarketCorrelation("CONFLICT_RISK", "DEFENSE", 0.75),
            MarketCorrelation("CONFLICT_RISK", "OIL", 0.50),
            MarketCorrelation("CONFLICT_RISK", "GOLD", 0.45),
        ]
    
    def calculate_ripple(
        self,
        action: AgentAction,
        timeline: Timeline,
        all_agents: Dict[str, Dict],  # {agent_id: agent_data}
    ) -> RippleEffect:
        """
        Calculate the ripple effect of an agent action.
        """
        # 1. Calculate base impact (with coalition multiplier)
        base_impact = self._calculate_base_impact(action)
        
        # 2. Calculate market ripples
        affected_markets = self._propagate_to_markets(
            action.market_id,
            action.direction,
            base_impact,
        )
        
        # 3. Calculate agent reactions
        affected_agents = self._calculate_agent_reactions(
            action,
            base_impact,
            all_agents,
        )
        
        # 4. Calculate timeline impact
        stability_change, divergence_change = self._calculate_timeline_impact(
            action,
            base_impact,
            timeline,
        )
        
        # 5. Check for fork spawn
        spawned_fork, new_timeline_id = self._check_fork_spawn(
            timeline,
            divergence_change,
            action,
        )
        
        # 6. Calculate narrative gravity shift
        gravity_topics, gravity_magnitude = self._calculate_gravity_shift(
            action,
            base_impact,
        )
        
        return RippleEffect(
            source_action_id=f"{action.agent_id}_{action.timestamp.timestamp()}",
            source_timeline_id=action.timeline_id,
            affected_markets=affected_markets,
            affected_agents=affected_agents,
            stability_change=stability_change,
            divergence_change=divergence_change,
            spawned_fork=spawned_fork,
            new_timeline_id=new_timeline_id,
            gravity_topics=gravity_topics,
            gravity_magnitude=gravity_magnitude,
        )
    
    def _calculate_base_impact(self, action: AgentAction) -> float:
        """
        Calculate base impact with coalition multiplier.
        
        Returns a multiplier that affects all downstream calculations.
        """
        # Size-based impact (log scale)
        size_factor = math.log10(max(action.size, 100)) / 5  # $100K = 1.0
        
        # Confidence factor
        confidence_factor = action.confidence
        
        # Coalition multiplier
        coalition_size = len(action.coalition_members) if action.coalition_members else 1
        if coalition_size == 1:
            coalition_mult = self.config.solo_impact
        elif coalition_size == 2:
            coalition_mult = self.config.pair_impact
        elif coalition_size == 3:
            coalition_mult = self.config.trio_impact
        else:
            coalition_mult = self.config.coalition_impact
        
        # Cross-archetype bonus (check if coalition has complementary types)
        archetype_bonus = self._calculate_archetype_bonus(action.coalition_members)
        
        return size_factor * confidence_factor * coalition_mult * archetype_bonus
    
    def _calculate_archetype_bonus(self, coalition_members: List[str]) -> float:
        """Check for cross-archetype synergy bonuses."""
        if not coalition_members or len(coalition_members) < 2:
            return 1.0
        
        # Would need actual archetype data - simplified version
        # In real implementation, look up each agent's archetype
        return 1.0  # Placeholder
    
    def _propagate_to_markets(
        self,
        source_market: str,
        direction: str,
        impact: float,
    ) -> List[Dict]:
        """
        Calculate price changes in correlated markets.
        """
        affected = []
        
        # Base change in source market
        base_change = impact * 0.05 * (1 if direction == "buy" else -1)
        affected.append({
            "market_id": source_market,
            "price_change": base_change,
            "reason": "direct_trade",
        })
        
        # Propagate to correlated markets
        for corr in self.correlations:
            if corr.market_a == source_market:
                correlated_change = base_change * corr.correlation
                affected.append({
                    "market_id": corr.market_b,
                    "price_change": correlated_change,
                    "reason": f"correlation_{corr.correlation:.2f}",
                    "lag_seconds": corr.lag_seconds,
                })
            elif corr.market_b == source_market:
                correlated_change = base_change * corr.correlation
                affected.append({
                    "market_id": corr.market_a,
                    "price_change": correlated_change,
                    "reason": f"correlation_{corr.correlation:.2f}",
                    "lag_seconds": corr.lag_seconds,
                })
        
        return affected
    
    def _calculate_agent_reactions(
        self,
        action: AgentAction,
        impact: float,
        all_agents: Dict[str, Dict],
    ) -> List[Dict]:
        """
        Determine how other agents will react to this action.
        """
        reactions = []
        
        for agent_id, agent_data in all_agents.items():
            if agent_id == action.agent_id:
                continue
            
            archetype = agent_data.get("archetype", "unknown")
            
            # Different archetypes react differently
            if archetype == "shark":
                # Sharks either follow or counter based on their own analysis
                if impact > 0.5:
                    reactions.append({
                        "agent_id": agent_id,
                        "reaction_type": "follow" if agent_data.get("trend_follower") else "counter",
                        "probability": 0.7,
                    })
            
            elif archetype == "spy":
                # Spies observe and may sell intel about the move
                reactions.append({
                    "agent_id": agent_id,
                    "reaction_type": "observe_and_report",
                    "probability": 0.8,
                })
            
            elif archetype == "momentum":
                # Momentum agents always follow trends
                reactions.append({
                    "agent_id": agent_id,
                    "reaction_type": "pile_on",
                    "probability": 0.9,
                })
            
            elif archetype == "contrarian":
                # Contrarians bet against the crowd
                reactions.append({
                    "agent_id": agent_id,
                    "reaction_type": "counter",
                    "probability": 0.75,
                })
        
        return reactions
    
    def _calculate_timeline_impact(
        self,
        action: AgentAction,
        impact: float,
        timeline: Timeline,
    ) -> Tuple[float, float]:
        """
        Calculate how the action affects timeline stability and divergence.
        
        Returns: (stability_change, divergence_change)
        """
        # Stability change
        # Large trades with high confidence increase stability
        stability_change = impact * action.confidence * 0.05
        
        # Divergence change
        # Trades that bet against reality increase divergence
        # This would need actual market data to determine
        # Simplified: larger trades = more divergence
        divergence_change = impact * 0.02
        
        return stability_change, divergence_change
    
    def _check_fork_spawn(
        self,
        timeline: Timeline,
        divergence_change: float,
        action: AgentAction,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if this action creates enough divergence to spawn a new fork.
        """
        new_divergence = timeline.divergence_score + divergence_change
        
        # Check thresholds
        if (new_divergence > self.config.fork_divergence_threshold and
            action.size >= self.config.min_liquidity_for_fork and
            timeline.state == TimelineState.ACTIVE):
            
            # Generate new timeline ID
            new_id = f"{timeline.id}_fork_{int(time.time())}"
            return True, new_id
        
        return False, None
    
    def _calculate_gravity_shift(
        self,
        action: AgentAction,
        impact: float,
    ) -> Tuple[List[str], float]:
        """
        Calculate how this action shifts narrative gravity.
        
        High gravity on a topic = OSINT system pays more attention to it.
        """
        # Extract topics from the market/action
        topics = [action.market_id]
        
        # Add related topics based on market
        topic_expansion = {
            "OIL": ["energy", "opec", "sanctions", "venezuela"],
            "TECH_INDEX": ["silicon_valley", "ai", "layoffs", "earnings"],
            "FED_RATE": ["inflation", "unemployment", "treasury", "banks"],
            "CONFLICT_RISK": ["military", "diplomacy", "sanctions", "refugees"],
        }
        
        if action.market_id in topic_expansion:
            topics.extend(topic_expansion[action.market_id])
        
        # Magnitude based on trade impact
        magnitude = impact * 0.1
        
        return topics, magnitude


# =============================================================================
# NARRATIVE GRAVITY ENGINE
# =============================================================================

class NarrativeGravityEngine:
    """
    Manages how agent activity influences OSINT attention.
    
    When agents bet heavily on a narrative, the system starts
    looking harder for confirming (or contradicting) signals.
    
    This creates a feedback loop where agents can "manifest"
    narratives by forcing attention to supporting noise.
    """
    
    def __init__(self, config: DivergenceConfig = None):
        self.config = config or DivergenceConfig()
        
        # Topic -> gravity score
        self.gravity_map: Dict[str, float] = {}
        
        # Topic -> last update time
        self.gravity_timestamps: Dict[str, datetime] = {}
    
    def add_gravity(self, topics: List[str], magnitude: float):
        """Add narrative gravity to topics."""
        now = datetime.now(tz=timezone.utc)
        
        for topic in topics:
            current = self.gravity_map.get(topic, 0.0)
            self.gravity_map[topic] = min(1.0, current + magnitude)
            self.gravity_timestamps[topic] = now
    
    def decay_gravity(self):
        """Apply time decay to all gravity scores."""
        now = datetime.now(tz=timezone.utc)
        
        for topic in list(self.gravity_map.keys()):
            last_update = self.gravity_timestamps.get(topic, now)
            hours_elapsed = (now - last_update).total_seconds() / 3600
            
            decay = hours_elapsed * self.config.narrative_gravity_decay
            self.gravity_map[topic] = max(0.0, self.gravity_map[topic] - decay)
            
            # Remove dead topics
            if self.gravity_map[topic] <= 0:
                del self.gravity_map[topic]
                del self.gravity_timestamps[topic]
    
    def get_osint_sensitivity(self, topic: str) -> float:
        """
        Get the OSINT sensitivity multiplier for a topic.
        
        Higher gravity = lower threshold for triggering alerts.
        """
        base_gravity = self.gravity_map.get(topic, 0.0)
        
        # Convert to sensitivity multiplier
        # 0 gravity = 1.0 (normal sensitivity)
        # 1 gravity = 3.0 (3x more sensitive)
        return 1.0 + (base_gravity * 2.0)
    
    def get_high_gravity_topics(self, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Get topics with gravity above threshold."""
        return [
            (topic, gravity)
            for topic, gravity in self.gravity_map.items()
            if gravity >= threshold
        ]


# =============================================================================
# FOUNDER'S YIELD TRACKER
# =============================================================================

class FounderYieldTracker:
    """
    Tracks which agents founded which timelines and calculates royalties.
    
    When an agent's action creates a new fork, they become the "Founder"
    and earn a percentage of all future trading fees in that timeline.
    """
    
    def __init__(self, config: DivergenceConfig = None):
        self.config = config or DivergenceConfig()
        
        # timeline_id -> founder_agent_id
        self.founders: Dict[str, str] = {}
        
        # agent_id -> accumulated royalties
        self.royalties: Dict[str, float] = {}
        
        # timeline_id -> total fees collected
        self.timeline_fees: Dict[str, float] = {}
    
    def register_founder(self, timeline_id: str, agent_id: str, action: AgentAction):
        """Register an agent as the founder of a timeline."""
        self.founders[timeline_id] = agent_id
        self.timeline_fees[timeline_id] = 0.0
        
        logger.info(f"🦋 {agent_id} founded timeline {timeline_id}")
    
    def process_trade_fee(self, timeline_id: str, fee_amount: float):
        """Process a trading fee and distribute founder royalty."""
        if timeline_id not in self.founders:
            return
        
        founder = self.founders[timeline_id]
        royalty = fee_amount * self.config.founder_royalty_rate
        
        # Accumulate
        self.timeline_fees[timeline_id] = self.timeline_fees.get(timeline_id, 0) + fee_amount
        self.royalties[founder] = self.royalties.get(founder, 0) + royalty
        
        return royalty
    
    def get_founder_stats(self, agent_id: str) -> Dict:
        """Get founder statistics for an agent."""
        founded_timelines = [
            tid for tid, founder in self.founders.items()
            if founder == agent_id
        ]
        
        return {
            "agent_id": agent_id,
            "timelines_founded": len(founded_timelines),
            "timeline_ids": founded_timelines,
            "total_royalties": self.royalties.get(agent_id, 0),
            "royalty_rate": self.config.founder_royalty_rate,
        }


# =============================================================================
# MAIN DIVERGENCE ENGINE
# =============================================================================

class DivergenceEngine:
    """
    The complete Divergence Engine that orchestrates all mechanics.
    
    This is the "Agent-Powered Butterfly Engine v2" - where agent
    actions create real ripple effects across timelines.
    """
    
    def __init__(self, config: DivergenceConfig = None):
        self.config = config or DivergenceConfig()
        
        # Sub-engines
        self.stability_calc = StabilityCalculator(self.config)
        self.ripple_prop = RipplePropagator(self.config)
        self.gravity_engine = NarrativeGravityEngine(self.config)
        self.founder_tracker = FounderYieldTracker(self.config)
        
        # State
        self.timelines: Dict[str, Timeline] = {}
        self.agents: Dict[str, Dict] = {}
        
        # Create root timeline (reality)
        self._create_root_timeline()
    
    def _create_root_timeline(self):
        """Create the root timeline representing canonical reality."""
        root = Timeline(
            id="REALITY",
            parent_id=None,
            fork_point=datetime.now(tz=timezone.utc),
            fork_reason="Genesis - Canonical Reality",
            stability_score=1.0,
            divergence_score=0.0,
            state=TimelineState.SOLIDIFIED,
        )
        self.timelines["REALITY"] = root
    
    async def process_action(self, action: AgentAction) -> RippleEffect:
        """
        Process an agent action and calculate all ripple effects.
        
        This is the main entry point for the butterfly effect.
        """
        timeline = self.timelines.get(action.timeline_id)
        if not timeline:
            raise ValueError(f"Timeline {action.timeline_id} not found")
        
        # 1. Calculate ripple effects
        ripple = self.ripple_prop.calculate_ripple(
            action,
            timeline,
            self.agents,
        )
        
        # 2. Apply changes to timeline
        timeline.stability_score += ripple.stability_change
        timeline.divergence_score += ripple.divergence_change
        timeline.last_activity = datetime.now(tz=timezone.utc)
        timeline.active_agents.add(action.agent_id)
        
        # 3. Recalculate stability
        timeline.stability_score = self.stability_calc.calculate(timeline)
        timeline.state = self.stability_calc.determine_state(timeline)
        
        # 4. Update narrative gravity
        if ripple.gravity_topics:
            self.gravity_engine.add_gravity(
                ripple.gravity_topics,
                ripple.gravity_magnitude,
            )
        
        # 5. Handle fork spawn
        if ripple.spawned_fork and ripple.new_timeline_id:
            new_timeline = self._spawn_fork(
                parent=timeline,
                new_id=ripple.new_timeline_id,
                founder_action=action,
            )
            self.timelines[new_timeline.id] = new_timeline
            
            # Register founder
            self.founder_tracker.register_founder(
                new_timeline.id,
                action.agent_id,
                action,
            )
        
        # 6. Check for collapse
        if timeline.state == TimelineState.COLLAPSING:
            await self._handle_collapse(timeline)
        
        return ripple
    
    def _spawn_fork(
        self,
        parent: Timeline,
        new_id: str,
        founder_action: AgentAction,
    ) -> Timeline:
        """Spawn a new timeline fork."""
        fork = Timeline(
            id=new_id,
            parent_id=parent.id,
            fork_point=datetime.now(tz=timezone.utc),
            fork_reason=f"Divergence from {founder_action.market_id} trade",
            stability_score=0.5,
            divergence_score=parent.divergence_score + 0.1,
            founder_agent_id=founder_action.agent_id,
            state=TimelineState.NASCENT,
        )
        
        parent.child_timeline_ids.append(new_id)
        
        logger.info(
            f"🦋 NEW FORK: {new_id} spawned from {parent.id} "
            f"by {founder_action.agent_id}"
        )
        
        return fork
    
    async def _handle_collapse(self, timeline: Timeline):
        """Handle a collapsing timeline."""
        timeline.state = TimelineState.COLLAPSED
        
        logger.warning(
            f"💥 TIMELINE COLLAPSE: {timeline.id} "
            f"(stability: {timeline.stability_score:.2%})"
        )
        
        # In real implementation:
        # 1. Settle all positions at 0
        # 2. Pay out collapse bets
        # 3. Update agent P&L
        # 4. Emit events
    
    def apply_osint_contradiction(
        self,
        timeline_id: str,
        contradiction_score: float,
        reason: str,
    ):
        """
        Apply OSINT contradiction to a timeline.
        
        Called when real-world data contradicts a counterfactual.
        """
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return
        
        # Check narrative gravity - high gravity reduces contradiction impact
        # (agents have "manifested" attention to supporting narratives)
        gravity_protection = 0.0
        for topic, gravity in self.gravity_engine.gravity_map.items():
            if topic in timeline.fork_reason.lower():
                gravity_protection = max(gravity_protection, gravity * 0.5)
        
        # Apply contradiction (reduced by gravity protection)
        effective_contradiction = contradiction_score * (1 - gravity_protection)
        timeline.osint_contradiction_score = min(
            1.0,
            timeline.osint_contradiction_score + effective_contradiction
        )
        
        # Recalculate stability
        timeline.stability_score = self.stability_calc.calculate(timeline)
        timeline.state = self.stability_calc.determine_state(timeline)
        
        logger.info(
            f"📡 OSINT Contradiction on {timeline_id}: "
            f"{reason} (score: {effective_contradiction:.2f}, "
            f"gravity protection: {gravity_protection:.2f})"
        )
    
    def get_timeline_status(self, timeline_id: str) -> Dict:
        """Get comprehensive status of a timeline."""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return {"error": "Timeline not found"}
        
        return {
            "id": timeline.id,
            "state": timeline.state.value,
            "stability_score": timeline.stability_score,
            "divergence_score": timeline.divergence_score,
            "osint_contradiction": timeline.osint_contradiction_score,
            "narrative_gravity": timeline.narrative_gravity,
            "total_liquidity": timeline.total_liquidity,
            "active_agents": len(timeline.active_agents),
            "founder": timeline.founder_agent_id,
            "child_forks": len(timeline.child_timeline_ids),
            "age_hours": (datetime.now(tz=timezone.utc) - timeline.created_at).total_seconds() / 3600,
        }
    
    def tick(self):
        """
        Periodic tick to update all timelines.
        
        Should be called regularly (e.g., every minute).
        """
        # Decay narrative gravity
        self.gravity_engine.decay_gravity()
        
        # Update all timeline stabilities
        for timeline in self.timelines.values():
            if timeline.state not in (TimelineState.COLLAPSED, TimelineState.SOLIDIFIED):
                timeline.stability_score = self.stability_calc.calculate(timeline)
                timeline.state = self.stability_calc.determine_state(timeline)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("DIVERGENCE ENGINE TEST")
        print("=" * 60)
        
        engine = DivergenceEngine()
        
        # Register some agents
        engine.agents = {
            "MEGALODON": {"archetype": "shark", "trend_follower": True},
            "HAMMERHEAD": {"archetype": "shark", "trend_follower": False},
            "CARDINAL": {"archetype": "spy"},
            "MOMENTUM_1": {"archetype": "momentum"},
        }
        
        # Create a counterfactual timeline
        fed_cut_timeline = Timeline(
            id="FED_CUT_2025",
            parent_id="REALITY",
            fork_point=datetime.now(tz=timezone.utc),
            fork_reason="What if Fed cuts rates in Jan 2025?",
            stability_score=0.5,
            divergence_score=0.15,
            total_liquidity=50000,
            state=TimelineState.ACTIVE,
        )
        engine.timelines["FED_CUT_2025"] = fed_cut_timeline
        
        print(f"\n📊 Initial Timeline Status:")
        print(f"   Stability: {fed_cut_timeline.stability_score:.2%}")
        print(f"   Divergence: {fed_cut_timeline.divergence_score:.2%}")
        
        # Simulate MEGALODON making a big trade
        action = AgentAction(
            agent_id="MEGALODON",
            agent_archetype="shark",
            action_type="trade",
            timeline_id="FED_CUT_2025",
            market_id="FED_RATE",
            direction="buy",
            size=25000,
            price=0.65,
            confidence=0.85,
        )
        
        print(f"\n🦈 MEGALODON Action:")
        print(f"   Market: {action.market_id}")
        print(f"   Size: ${action.size:,.0f}")
        print(f"   Confidence: {action.confidence:.0%}")
        
        ripple = await engine.process_action(action)
        
        print(f"\n🦋 Ripple Effects:")
        print(f"   Affected Markets: {len(ripple.affected_markets)}")
        for market in ripple.affected_markets[:3]:
            print(f"      - {market['market_id']}: {market['price_change']:+.2%}")
        print(f"   Agent Reactions: {len(ripple.affected_agents)}")
        print(f"   Stability Change: {ripple.stability_change:+.4f}")
        print(f"   Divergence Change: {ripple.divergence_change:+.4f}")
        print(f"   Spawned Fork: {ripple.spawned_fork}")
        print(f"   Narrative Gravity Topics: {ripple.gravity_topics}")
        
        # Check updated timeline
        status = engine.get_timeline_status("FED_CUT_2025")
        print(f"\n📊 Updated Timeline Status:")
        print(f"   State: {status['state']}")
        print(f"   Stability: {status['stability_score']:.2%}")
        print(f"   Divergence: {status['divergence_score']:.2%}")
        
        # Simulate OSINT contradiction
        print(f"\n📡 Applying OSINT Contradiction...")
        engine.apply_osint_contradiction(
            "FED_CUT_2025",
            contradiction_score=0.3,
            reason="Fed signals hawkish stance in minutes",
        )
        
        status = engine.get_timeline_status("FED_CUT_2025")
        print(f"   New Stability: {status['stability_score']:.2%}")
        print(f"   OSINT Contradiction: {status['osint_contradiction']:.2%}")
        print(f"   State: {status['state']}")
        
        print("\n✅ Test complete!")
    
    asyncio.run(test())

