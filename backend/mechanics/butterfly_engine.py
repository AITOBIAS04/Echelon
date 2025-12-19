from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import random
import math
from ..schemas.butterfly_schemas import (
    WingFlap, WingFlapType, StabilityDirection, AgentArchetype,
    TimelineHealth, GravityBreakdown, Ripple
)

class ButterflyEngine:
    """
    The Butterfly Engine calculates causality effects.
    
    Core principle: Every agent action creates a "Wing Flap" that affects
    timeline stability. Large flaps may spawn "Ripples" (forks).
    """
    
    # Thresholds
    RIPPLE_THRESHOLD = 15.0  # |Stability Δ| > 15% spawns a fork
    LOGIC_GAP_PARADOX_THRESHOLD = 0.3  # Gap > 30% may spawn paradox
    
    # Decay rates
    BASE_DECAY_PER_HOUR = 1.0  # 1% per hour
    PARADOX_DECAY_MULTIPLIER = 5.0  # 5x during paradox
    
    def __init__(self, timeline_repo, agent_repo, osint_service):
        self.timeline_repo = timeline_repo
        self.agent_repo = agent_repo
        self.osint_service = osint_service
    
    # =========================================
    # WING FLAP CREATION
    # =========================================
    
    def create_wing_flap(
        self,
        timeline_id: str,
        agent_id: str,
        action_type: WingFlapType,
        volume_usd: float,
        raw_action: str  # "bought 500 YES @ $0.67"
    ) -> WingFlap:
        """
        Create a Wing Flap from an agent action.
        
        Returns the flap with calculated stability delta.
        """
        timeline = self.timeline_repo.get(timeline_id)
        agent = self.agent_repo.get(agent_id)
        
        # Calculate stability delta based on action
        stability_delta = self._calculate_stability_delta(
            timeline=timeline,
            agent=agent,
            action_type=action_type,
            volume_usd=volume_usd
        )
        
        # Determine direction
        direction = (
            StabilityDirection.ANCHOR if stability_delta > 0 
            else StabilityDirection.DESTABILISE
        )
        
        # Apply delta to timeline
        new_stability = max(0, min(100, timeline.stability + stability_delta))
        self.timeline_repo.update_stability(timeline_id, new_stability)
        
        # Check for ripple (fork)
        spawned_ripple = False
        ripple_timeline_id = None
        if abs(stability_delta) > self.RIPPLE_THRESHOLD:
            ripple = self._spawn_ripple(timeline, agent, stability_delta)
            spawned_ripple = True
            ripple_timeline_id = ripple.child_timeline_id
        
        # Calculate founder yield (if applicable)
        founder_yield = self._calculate_founder_yield(timeline, stability_delta)
        
        # Create the flap
        flap = WingFlap(
            id=f"FLAP_{timeline_id}_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            timeline_id=timeline_id,
            timeline_name=timeline.name,
            agent_id=agent_id,
            agent_name=agent.name,
            agent_archetype=agent.archetype,
            flap_type=action_type,
            action=f"{agent.name} {raw_action}",
            stability_delta=stability_delta,
            direction=direction,
            volume_usd=volume_usd,
            timeline_stability=new_stability,
            timeline_price=timeline.price_yes,
            spawned_ripple=spawned_ripple,
            ripple_timeline_id=ripple_timeline_id,
            founder_id=timeline.founder_id,
            founder_yield_earned=founder_yield
        )
        
        # Persist and broadcast
        self._persist_flap(flap)
        self._broadcast_flap(flap)
        
        return flap
    
    def _calculate_stability_delta(
        self,
        timeline,
        agent,
        action_type: WingFlapType,
        volume_usd: float
    ) -> float:
        """
        Calculate how much an action affects stability.
        
        Formula incorporates:
        - Volume (larger trades = larger impact)
        - Agent archetype (Sharks destabilise, Diplomats stabilise)
        - Action type (Shields stabilise, Sabotage destabilises)
        - Liquidity (thin markets are more volatile)
        """
        # Base impact from volume (logarithmic)
        base_impact = math.log10(max(100, volume_usd)) * 2  # $1000 = 6, $10000 = 8
        
        # Archetype modifier
        archetype_modifiers = {
            AgentArchetype.SHARK: -1.2,      # Destabilising
            AgentArchetype.SPY: -0.5,        # Slightly destabilising
            AgentArchetype.DIPLOMAT: 1.5,    # Stabilising
            AgentArchetype.SABOTEUR: -2.0,   # Very destabilising
            AgentArchetype.WHALE: -0.8,      # Destabilising (moves markets)
            AgentArchetype.DEGEN: -0.3,      # Slightly destabilising (noise)
        }
        archetype_mod = archetype_modifiers.get(agent.archetype, 0)
        
        # Action type modifier
        action_modifiers = {
            WingFlapType.TRADE: 1.0,
            WingFlapType.SHIELD: 2.0,       # Shields are stabilising
            WingFlapType.SABOTAGE: -2.5,    # Sabotage is destabilising
            WingFlapType.RIPPLE: 0,         # Ripples don't affect parent
            WingFlapType.PARADOX: -5.0,     # Paradoxes are very destabilising
            WingFlapType.FOUNDER_YIELD: 0,  # Yields don't affect stability
        }
        action_mod = action_modifiers.get(action_type, 1.0)
        
        # Liquidity modifier (thin markets are more volatile)
        liquidity_depth = timeline.liquidity_depth_usd or 10000
        liquidity_mod = 10000 / max(1000, liquidity_depth)  # 1.0 at $10k, 10.0 at $1k
        
        # Final calculation
        delta = base_impact * archetype_mod * action_mod * liquidity_mod
        
        # Clamp to reasonable range
        return max(-50, min(50, delta))
    
    # =========================================
    # RIPPLE (FORK) SPAWNING
    # =========================================
    
    def _spawn_ripple(self, timeline, agent, stability_delta: float) -> Ripple:
        """
        Spawn a new timeline fork when stability delta exceeds threshold.
        """
        # Generate fork narrative
        narrative = self._generate_fork_narrative(timeline, stability_delta)
        
        # Create child timeline
        child_timeline = self.timeline_repo.create_fork(
            parent_id=timeline.id,
            narrative=narrative,
            initial_stability=50.0,  # Forks start at 50%
            founder_id=agent.owner_id  # Agent's owner becomes founder
        )
        
        ripple = Ripple(
            id=f"RIPPLE_{child_timeline.id}",
            parent_timeline_id=timeline.id,
            child_timeline_id=child_timeline.id,
            spawned_at=datetime.now(),
            trigger_flap_id="",  # Will be set by caller
            trigger_agent_id=agent.id,
            trigger_stability_delta=stability_delta,
            fork_narrative=narrative,
            initial_stability=50.0,
            founder_id=agent.owner_id,
            founder_stake_usd=0  # Will be set when founder stakes
        )
        
        return ripple
    
    def _generate_fork_narrative(self, timeline, stability_delta: float) -> str:
        """Generate a narrative for the new fork."""
        # In production, this would use LLM
        # For now, simple template
        if stability_delta > 0:
            return f"What if {timeline.name} stabilises further?"
        else:
            return f"What if {timeline.name} collapses?"
    
    # =========================================
    # FOUNDER YIELD
    # =========================================
    
    def _calculate_founder_yield(self, timeline, stability_delta: float) -> Optional[float]:
        """
        Calculate yield for the timeline founder.
        
        Founders earn yield when stability INCREASES (their timeline is healthy).
        """
        if not timeline.founder_id:
            return None
        
        if stability_delta <= 0:
            return None  # No yield for destabilisation
        
        # Yield rate: 0.1% of delta as USDC
        yield_rate = 0.001
        yield_amount = abs(stability_delta) * yield_rate * timeline.total_volume_usd
        
        # Pay the founder
        self._pay_founder_yield(timeline.founder_id, yield_amount)
        
        return yield_amount
    
    def _pay_founder_yield(self, founder_id: str, amount: float):
        """Credit yield to founder's account."""
        # Implementation depends on your payment system
        pass
    
    # =========================================
    # GRAVITY CALCULATION
    # =========================================
    
    def calculate_gravity(self, timeline_id: str) -> GravityBreakdown:
        """
        Calculate the "Gravity" score for a timeline.
        
        Gravity determines importance/visibility in the UI.
        High gravity = shown prominently in SIGINT.
        """
        timeline = self.timeline_repo.get(timeline_id)
        
        # Component 1: Volume (0-25)
        volume_score = min(25, (timeline.total_volume_usd / 100000) * 25)
        
        # Component 2: Agent Activity (0-25)
        agent_count = timeline.active_agent_count
        agent_score = min(25, (agent_count / 20) * 25)
        
        # Component 3: Volatility (0-25)
        # Recent stability changes indicate action
        recent_delta = self._get_recent_stability_delta(timeline_id, hours=1)
        volatility_score = min(25, abs(recent_delta) * 2.5)
        
        # Component 4: Narrative Relevance (0-25)
        # How much OSINT mentions this topic
        osint_hits = self.osint_service.count_mentions(timeline.keywords, hours=24)
        narrative_score = min(25, (osint_hits / 100) * 25)
        
        total_gravity = volume_score + agent_score + volatility_score + narrative_score
        
        return GravityBreakdown(
            timeline_id=timeline_id,
            total_gravity=total_gravity,
            volume_score=volume_score,
            agent_activity_score=agent_score,
            volatility_score=volatility_score,
            narrative_relevance_score=narrative_score,
            related_keywords=timeline.keywords,
            osint_sources=self.osint_service.get_sources(timeline.keywords),
            trending_rank=None  # Calculated separately
        )
    
    def _get_recent_stability_delta(self, timeline_id: str, hours: int) -> float:
        """Get sum of stability changes in recent hours."""
        # Query recent flaps
        cutoff = datetime.now() - timedelta(hours=hours)
        flaps = self.timeline_repo.get_flaps_since(timeline_id, cutoff)
        return sum(f.stability_delta for f in flaps)
    
    # =========================================
    # LOGIC GAP (Paradox Detection)
    # =========================================
    
    def calculate_logic_gap(self, timeline_id: str) -> float:
        """
        Calculate the gap between market price and OSINT reality.
        
        High gap = market is mispriced = paradox risk.
        """
        timeline = self.timeline_repo.get(timeline_id)
        
        # Market says this price
        market_confidence = timeline.price_yes  # 0.0 - 1.0
        
        # OSINT says this probability
        osint_probability = self.osint_service.get_reality_score(
            timeline.keywords,
            timeline.narrative
        ) / 100  # Convert to 0.0 - 1.0
        
        # The gap
        logic_gap = abs(market_confidence - osint_probability)
        
        # Update timeline
        self.timeline_repo.update_logic_gap(timeline_id, logic_gap)
        
        return logic_gap
    
    # =========================================
    # PERSISTENCE & BROADCAST
    # =========================================
    
    def _persist_flap(self, flap: WingFlap):
        """Save flap to database."""
        # Implementation depends on your database
        pass
    
    def _broadcast_flap(self, flap: WingFlap):
        """Broadcast flap via WebSocket to connected clients."""
        # Implementation in websockets/realtime_manager.py
        pass

