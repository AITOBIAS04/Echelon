"""
Situation Room Engine
=====================

The core game engine that manages:
- Active missions and their lifecycle
- Agent deployment and ability usage
- Intel Market (x402 information trading)
- Treaty System (escrow-based diplomacy)
- Global state (tension, chaos, faction power)
- Narrative arc progression
- Sleeper cell / double agent mechanics

This is the "game master" that orchestrates all RPG elements.
"""

import asyncio
import uuid
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Import from models
try:
    from backend.core.models import (
        AgentRole, MissionType, MissionStatus, Difficulty, Faction,
        SpecialAbility, Mission, MissionObjective, NarrativeArc,
        TheaterState, ROLE_ABILITIES, ABILITY_CONFIG
    )
    from backend.core.mission_generator import (
        OSINTSignal, SignalAnalyzer, MissionGenerator, 
        NarrativeArcGenerator, SignalSource, SignalCategory
    )
    from backend.agents.shark_strategies import SharkBrain, SharkGenome, MarketState
except ImportError:
    from backend.core.models import (
        AgentRole, MissionType, MissionStatus, Difficulty, Faction,
        SpecialAbility, Mission, MissionObjective, NarrativeArc,
        TheaterState, ROLE_ABILITIES, ABILITY_CONFIG
    )
    from backend.core.mission_generator import (
        OSINTSignal, SignalAnalyzer, MissionGenerator, 
        NarrativeArcGenerator, SignalSource, SignalCategory
    )
    try:
        from backend.simulation.shark_strategies import SharkBrain, SharkGenome, MarketState
    except ImportError:
        # Shark strategies not available
        SharkBrain = None
        SharkGenome = None
        MarketState = None


# =============================================================================
# INTEL MARKET SYSTEM (x402 Information Trading)
# =============================================================================

@dataclass
class IntelPacket:
    """
    A sellable piece of intelligence.
    Spies can encrypt signals and sell them via x402.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    # Content
    signal_id: str = ""                   # Original signal this came from
    encrypted_preview: str = ""           # Teaser shown to buyers
    full_content: str = ""                # Revealed after purchase
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    time_advantage_seconds: int = 10      # How early buyers get the info
    
    # Creator
    creator_agent_id: str = ""
    creator_faction: Optional[Faction] = None
    
    # Pricing (x402)
    price_usdc: float = 5.0
    subscription_price_monthly: float = 20.0
    
    # Stats
    times_purchased: int = 0
    total_revenue: float = 0.0
    accuracy_rating: float = 1.0          # Updated based on outcomes
    
    # State
    is_active: bool = True
    is_fake: bool = False                 # Set if this is disinformation


@dataclass
class IntelSubscription:
    """A user's subscription to a spy agent's intel feed"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    subscriber_id: str = ""               # User or agent ID
    spy_agent_id: str = ""
    
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    price_paid: float = 0.0
    is_active: bool = True


class IntelMarket:
    """
    Manages the buying and selling of intelligence.
    Implements Gemini's "Intel Market" concept.
    """
    
    def __init__(self):
        self.packets: Dict[str, IntelPacket] = {}
        self.subscriptions: Dict[str, IntelSubscription] = {}
        self.spy_ratings: Dict[str, float] = defaultdict(lambda: 0.5)  # Agent ID -> rating
    
    def create_intel_packet(
        self,
        signal: OSINTSignal,
        creator_agent_id: str,
        creator_faction: Optional[Faction] = None,
        price: float = 5.0,
        is_fake: bool = False
    ) -> IntelPacket:
        """
        Spy creates an intel packet from a signal.
        Uses ENCRYPT_INTEL ability.
        """
        # Create encrypted preview (partial info)
        preview = self._generate_preview(signal, is_fake)
        
        # Full content (revealed on purchase)
        if is_fake:
            full_content = self._generate_fake_intel(signal)
        else:
            full_content = f"""
DECRYPTED INTELLIGENCE PACKET
=============================
Source: {signal.source.value}
Timestamp: {signal.timestamp.isoformat()}

HEADLINE: {signal.headline}

ANALYSIS:
{signal.summary}

MARKET IMPACT ESTIMATE: {signal.market_impact_estimate:+.2%}
CONFIDENCE: {signal.source_credibility:.0%}

Entities Involved: {', '.join(signal.entities)}
Category: {signal.category.value}

[END TRANSMISSION]
            """.strip()
        
        packet = IntelPacket(
            signal_id=signal.id,
            encrypted_preview=preview,
            full_content=full_content,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            creator_agent_id=creator_agent_id,
            creator_faction=creator_faction,
            price_usdc=price,
            is_fake=is_fake,
        )
        
        self.packets[packet.id] = packet
        return packet
    
    def _generate_preview(self, signal: OSINTSignal, is_fake: bool) -> str:
        """Generate an enticing preview without revealing full intel"""
        urgency_words = {
            True: "🔴 CRITICAL",
            False: "🟡 NOTABLE" if signal.urgency > 0.5 else "🟢 ROUTINE"
        }
        
        # Truncate headline
        headline_preview = signal.headline[:50] + "..." if len(signal.headline) > 50 else signal.headline
        
        return f"""
[ENCRYPTED INTEL PACKET]
Priority: {urgency_words[signal.urgency > 0.7]}
Category: {signal.category.value.upper()}
Preview: "{headline_preview}"
Time Advantage: 10 seconds
Price: ${5.0:.2f} USDC

⚠️ Full decryption requires purchase
        """.strip()
    
    def _generate_fake_intel(self, signal: OSINTSignal) -> str:
        """Generate believable disinformation"""
        # Invert sentiment, exaggerate claims
        fake_sentiment = -signal.sentiment if abs(signal.sentiment) > 0.3 else random.uniform(-0.8, 0.8)
        
        exaggerations = [
            "Sources indicate imminent action within 24 hours",
            "Multiple high-level officials have been compromised",
            "Insider confirms massive cover-up underway",
            "Secret negotiations have broken down completely",
            "Emergency protocols have been activated",
        ]
        
        return f"""
DECRYPTED INTELLIGENCE PACKET
=============================
[CLASSIFICATION: TOP SECRET]

HEADLINE: {signal.headline}

CRITICAL UPDATE:
{random.choice(exaggerations)}

{signal.summary}

[FABRICATED ENHANCEMENT]
Our sources suggest this is just the beginning. Market participants
should prepare for significant volatility.

MARKET IMPACT ESTIMATE: {fake_sentiment * 100:+.1f}%

[END TRANSMISSION - AUTHENTICITY UNVERIFIED]
        """.strip()
    
    def purchase_intel(
        self,
        packet_id: str,
        buyer_id: str,
        payment_usdc: float
    ) -> Tuple[bool, str]:
        """
        Purchase an intel packet.
        
        Returns:
            (success, content_or_error)
        """
        packet = self.packets.get(packet_id)
        if not packet:
            return False, "Intel packet not found"
        
        if not packet.is_active:
            return False, "Intel packet has expired"
        
        if payment_usdc < packet.price_usdc:
            return False, f"Insufficient payment. Required: ${packet.price_usdc}"
        
        # Process purchase
        packet.times_purchased += 1
        packet.total_revenue += payment_usdc
        
        # Update spy rating based on purchases
        self.spy_ratings[packet.creator_agent_id] = min(1.0, 
            self.spy_ratings[packet.creator_agent_id] + 0.01
        )
        
        return True, packet.full_content
    
    def subscribe_to_spy(
        self,
        subscriber_id: str,
        spy_agent_id: str,
        months: int = 1
    ) -> IntelSubscription:
        """
        Subscribe to a spy's intel feed.
        Subscriber gets all intel from this spy as it's created.
        """
        sub = IntelSubscription(
            subscriber_id=subscriber_id,
            spy_agent_id=spy_agent_id,
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30 * months),
            price_paid=20.0 * months,  # $20/month
            is_active=True,
        )
        
        self.subscriptions[sub.id] = sub
        return sub
    
    def get_spy_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top-rated spy agents by intel quality"""
        sorted_spies = sorted(
            self.spy_ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {"agent_id": agent_id, "rating": rating}
            for agent_id, rating in sorted_spies
        ]


# =============================================================================
# TREATY SYSTEM (Smart Contract Diplomacy)
# =============================================================================

@dataclass
class Treaty:
    """
    A diplomatic agreement between factions with escrow enforcement.
    Implements Gemini's "Smart Treaty" concept.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    # Parties
    party_a_faction: Faction = Faction.NEUTRAL
    party_b_faction: Faction = Faction.NEUTRAL
    party_a_agent_id: str = ""            # Diplomat who negotiated
    party_b_agent_id: str = ""
    
    # Terms
    treaty_name: str = ""
    terms: str = ""                       # Human-readable terms
    
    # Escrow
    party_a_escrow: float = 0.0           # USDC deposited
    party_b_escrow: float = 0.0
    total_escrow: float = 0.0
    
    # Trigger conditions
    tension_threshold: float = 0.8        # If tension exceeds this, treaty breaks
    violation_conditions: List[str] = field(default_factory=list)
    
    # Timeline
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    stability_period_hours: int = 72      # Must remain stable for this long
    
    # State
    is_active: bool = True
    is_violated: bool = False
    violated_by: Optional[Faction] = None
    violation_reason: Optional[str] = None
    
    # Rewards
    success_reward_per_party: float = 50.0
    reputation_reward: int = 20
    
    # Betting
    betting_market_id: Optional[str] = None


class TreatySystem:
    """
    Manages diplomatic treaties with escrow enforcement.
    Treaties create betting markets and affect global tension.
    """
    
    def __init__(self, theater_state: TheaterState):
        self.treaties: Dict[str, Treaty] = {}
        self.theater_state = theater_state
    
    def propose_treaty(
        self,
        proposer_agent_id: str,
        proposer_faction: Faction,
        target_faction: Faction,
        terms: str,
        escrow_amount: float = 100.0,
        tension_threshold: float = 0.8
    ) -> Treaty:
        """
        Diplomat proposes a treaty.
        Requires PROPOSE_TREATY ability.
        """
        treaty = Treaty(
            party_a_faction=proposer_faction,
            party_b_faction=target_faction,
            party_a_agent_id=proposer_agent_id,
            treaty_name=f"{proposer_faction.value}-{target_faction.value} Accord",
            terms=terms,
            party_a_escrow=escrow_amount,
            tension_threshold=tension_threshold,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=False,  # Not active until both parties deposit
        )
        
        self.treaties[treaty.id] = treaty
        return treaty
    
    def accept_treaty(
        self,
        treaty_id: str,
        accepter_agent_id: str,
        escrow_amount: float
    ) -> Tuple[bool, str]:
        """
        Second party accepts and deposits escrow.
        Treaty becomes active.
        """
        treaty = self.treaties.get(treaty_id)
        if not treaty:
            return False, "Treaty not found"
        
        if treaty.is_active:
            return False, "Treaty already active"
        
        treaty.party_b_agent_id = accepter_agent_id
        treaty.party_b_escrow = escrow_amount
        treaty.total_escrow = treaty.party_a_escrow + escrow_amount
        treaty.is_active = True
        treaty.created_at = datetime.now(timezone.utc)
        
        # Add to theater state
        self.theater_state.active_treaties.append({
            "id": treaty.id,
            "parties": [treaty.party_a_faction.value, treaty.party_b_faction.value],
            "escrow": treaty.total_escrow,
        })
        
        # Reduce global tension
        self.theater_state.global_tension = max(0, 
            self.theater_state.global_tension - 0.1
        )
        
        return True, f"Treaty active. Total escrow: ${treaty.total_escrow}"
    
    def check_treaty_violations(self) -> List[Treaty]:
        """
        Check all active treaties for violations.
        Called on each game tick.
        """
        violated = []
        
        for treaty in self.treaties.values():
            if not treaty.is_active or treaty.is_violated:
                continue
            
            # Check tension threshold
            if self.theater_state.global_tension > treaty.tension_threshold:
                treaty.is_violated = True
                treaty.violation_reason = f"Global tension ({self.theater_state.global_tension:.2f}) exceeded threshold ({treaty.tension_threshold})"
                violated.append(treaty)
                
                # Slash escrow (burn or redistribute)
                self._slash_escrow(treaty)
        
        return violated
    
    def _slash_escrow(self, treaty: Treaty):
        """Handle escrow slashing when treaty is violated"""
        # In a real implementation, this would interact with blockchain
        # For now, we track it and emit events
        
        slash_amount = treaty.total_escrow * 0.5  # Slash 50%
        
        self.theater_state.event_log.append({
            "type": "treaty_violation",
            "treaty_id": treaty.id,
            "parties": [treaty.party_a_faction.value, treaty.party_b_faction.value],
            "slashed_amount": slash_amount,
            "reason": treaty.violation_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Increase chaos from broken treaty
        self.theater_state.chaos_index = min(1.0,
            self.theater_state.chaos_index + 0.15
        )
    
    def get_active_treaties(self) -> List[Treaty]:
        """Get all currently active treaties"""
        return [t for t in self.treaties.values() if t.is_active and not t.is_violated]
    
    def sabotage_treaty(
        self,
        treaty_id: str,
        saboteur_agent_id: str,
        method: str
    ) -> Tuple[bool, str]:
        """
        Saboteur attempts to break a treaty.
        Uses FALSE_FLAG or CHAOS_INJECTION abilities.
        """
        treaty = self.treaties.get(treaty_id)
        if not treaty or not treaty.is_active:
            return False, "No active treaty to sabotage"
        
        # Sabotage increases tension, potentially breaking treaty
        tension_increase = random.uniform(0.1, 0.3)
        self.theater_state.global_tension = min(1.0,
            self.theater_state.global_tension + tension_increase
        )
        
        # Check if this breaks the treaty
        violations = self.check_treaty_violations()
        
        if treaty in violations:
            return True, f"Treaty sabotaged successfully. Tension spiked to {self.theater_state.global_tension:.2f}"
        
        return True, f"Tension increased to {self.theater_state.global_tension:.2f}, but treaty holds"


# =============================================================================
# SLEEPER CELL SYSTEM (Double Agents)
# =============================================================================

@dataclass
class SleeperAssignment:
    """
    Secret assignment for a sleeper/double agent.
    Hidden from other players until triggered.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    agent_id: str = ""
    apparent_faction: Faction = Faction.NEUTRAL     # What they appear to be
    true_faction: Faction = Faction.UNDERGROUND     # Who they really work for
    
    # Trigger
    trigger_condition: str = ""           # e.g., "tension > 0.9"
    trigger_tension: float = 0.9
    is_triggered: bool = False
    triggered_at: Optional[datetime] = None
    
    # Objectives when triggered
    betrayal_actions: List[str] = field(default_factory=list)
    
    # Betting
    mystery_market_id: Optional[str] = None  # "Who is the mole?" market
    
    # State
    is_revealed: bool = False
    season: int = 1


class SleeperCellSystem:
    """
    Manages the "Who is the Mole?" game mechanic.
    At season start, one random agent becomes a sleeper.
    """
    
    def __init__(self, theater_state: TheaterState):
        self.assignments: Dict[str, SleeperAssignment] = {}
        self.theater_state = theater_state
        self.current_season = 1
        self.mole_revealed = False
    
    def assign_sleeper(
        self,
        agent_id: str,
        apparent_faction: Faction,
        true_faction: Faction = Faction.UNDERGROUND,
        trigger_tension: float = 0.9
    ) -> SleeperAssignment:
        """
        Secretly assign an agent as a sleeper.
        This should be hidden from all players.
        """
        betrayal_actions = [
            "Dump all held positions",
            "Leak all accumulated intelligence",
            "Vote against own faction in critical decision",
            "Sabotage active treaties",
            "Reveal classified mission details",
        ]
        
        assignment = SleeperAssignment(
            agent_id=agent_id,
            apparent_faction=apparent_faction,
            true_faction=true_faction,
            trigger_condition=f"global_tension > {trigger_tension}",
            trigger_tension=trigger_tension,
            betrayal_actions=random.sample(betrayal_actions, 3),
            season=self.current_season,
        )
        
        self.assignments[assignment.id] = assignment
        return assignment
    
    def check_triggers(self) -> List[SleeperAssignment]:
        """
        Check if any sleeper agents should be triggered.
        Called on each game tick.
        """
        triggered = []
        
        for assignment in self.assignments.values():
            if assignment.is_triggered or assignment.is_revealed:
                continue
            
            # Check tension trigger
            if self.theater_state.global_tension > assignment.trigger_tension:
                assignment.is_triggered = True
                assignment.triggered_at = datetime.now(timezone.utc)
                triggered.append(assignment)
                
                self._execute_betrayal(assignment)
        
        return triggered
    
    def _execute_betrayal(self, assignment: SleeperAssignment):
        """Execute the sleeper's betrayal actions"""
        self.theater_state.event_log.append({
            "type": "sleeper_activated",
            "agent_id": assignment.agent_id,
            "apparent_faction": assignment.apparent_faction.value,
            "actions": assignment.betrayal_actions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "🔴 A MOLE HAS BEEN ACTIVATED",
        })
        
        # Massive chaos injection
        self.theater_state.chaos_index = min(1.0,
            self.theater_state.chaos_index + 0.3
        )
    
    def reveal_mole(self, assignment_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Reveal a sleeper agent (investigation success).
        Resolves the "Who is the Mole?" betting market.
        """
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return False, {}
        
        assignment.is_revealed = True
        self.mole_revealed = True
        
        reveal_data = {
            "agent_id": assignment.agent_id,
            "apparent_faction": assignment.apparent_faction.value,
            "true_faction": assignment.true_faction.value,
            "was_triggered": assignment.is_triggered,
            "betrayal_actions": assignment.betrayal_actions,
        }
        
        self.theater_state.event_log.append({
            "type": "mole_revealed",
            **reveal_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"🎭 THE MOLE HAS BEEN UNMASKED: Agent {assignment.agent_id}",
        })
        
        return True, reveal_data
    
    def create_mystery_market(self, suspect_agent_ids: List[str]) -> Dict[str, Any]:
        """
        Create a "Who is the Mole?" betting market.
        Players bet on which agent is the sleeper.
        """
        return {
            "market_type": "mole_identity",
            "question": "Who is the Mole?",
            "options": suspect_agent_ids,
            "season": self.current_season,
            "resolves_when": "Mole is revealed or season ends",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


# =============================================================================
# SITUATION ROOM ENGINE (Main Game Loop)
# =============================================================================

class SituationRoomEngine:
    """
    The main game engine that orchestrates all systems.
    
    Responsibilities:
    - Process incoming OSINT signals
    - Generate and manage missions
    - Track agent abilities and cooldowns
    - Manage Intel Market
    - Enforce Treaties
    - Run Sleeper Cell mechanics
    - Update global state
    - Generate narrative events
    """
    
    def __init__(self, llm_client=None):
        # Core state
        self.theater_state = TheaterState()
        
        # Subsystems
        self.mission_generator = MissionGenerator(llm_client)
        self.arc_generator = NarrativeArcGenerator(self.mission_generator)
        self.intel_market = IntelMarket()
        self.treaty_system = TreatySystem(self.theater_state)
        self.sleeper_system = SleeperCellSystem(self.theater_state)
        
        # Mission tracking
        self.missions: Dict[str, Mission] = {}
        self.narrative_arcs: Dict[str, NarrativeArc] = {}
        
        # Signal queue
        self.signal_queue: List[OSINTSignal] = []
        self.processed_signals: Dict[str, OSINTSignal] = {}
        
        # Agent tracking
        self.agent_cooldowns: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "missions_completed": 0,
            "missions_failed": 0,
            "reputation": 50,
            "usdc_earned": 0.0,
            "abilities_used": 0,
        })
        
        # Initialize Shark Brains for financial agents
        self.shark_brains: Dict[str, SharkBrain] = {}
        
        # Event callbacks
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Tick counter
        self.tick_count = 0
        self.last_tick = datetime.now(timezone.utc)
    
    # =========================================================================
    # SIGNAL PROCESSING
    # =========================================================================
    
    async def ingest_signal(self, signal: OSINTSignal) -> OSINTSignal:
        """
        Ingest a new OSINT signal into the system.
        Analyzes and queues for mission generation.
        """
        # Analyze signal
        analyzer = SignalAnalyzer()
        signal = analyzer.analyze(signal)
        
        self.signal_queue.append(signal)
        self.processed_signals[signal.id] = signal
        
        # Check if this should trigger early access for spies
        await self._notify_early_access(signal)
        
        # Emit event
        await self._emit_event("signal_ingested", {
            "signal_id": signal.id,
            "headline": signal.headline,
            "mission_potential": signal.mission_potential,
        })
        
        return signal
    
    async def _notify_early_access(self, signal: OSINTSignal):
        """
        Notify spy agents with EARLY_ACCESS ability.
        They get the signal 10 seconds before others.
        """
        # In a real implementation, this would notify subscribed spies
        # For now, we just log it
        if signal.mission_potential > 0.6:
            self.theater_state.event_log.append({
                "type": "early_access_signal",
                "signal_id": signal.id,
                "preview": signal.headline[:50],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    
    # =========================================================================
    # MISSION MANAGEMENT
    # =========================================================================
    
    async def generate_mission_from_signal(
        self,
        signal_id: str,
        force_type: Optional[MissionType] = None
    ) -> Optional[Mission]:
        """Generate a mission from a queued signal"""
        signal = self.processed_signals.get(signal_id)
        if not signal:
            return None
        
        mission = await self.mission_generator.generate_mission(
            signal, 
            force_type=force_type,
            theater_state=self.theater_state
        )
        
        self.missions[mission.id] = mission
        self.theater_state.active_missions.append(mission)
        
        await self._emit_event("mission_created", {
            "mission_id": mission.id,
            "codename": mission.codename,
            "type": mission.mission_type.value,
            "difficulty": mission.difficulty.name,
        })
        
        return mission
    
    async def assign_agent_to_mission(
        self,
        mission_id: str,
        agent_id: str,
        agent_role: AgentRole
    ) -> Tuple[bool, str]:
        """Assign an agent to a mission"""
        mission = self.missions.get(mission_id)
        if not mission:
            return False, "Mission not found"
        
        if mission.status != MissionStatus.PENDING:
            return False, f"Mission is {mission.status.value}, cannot assign"
        
        if len(mission.assigned_agents) >= mission.max_agents:
            return False, "Mission is full"
        
        if agent_role not in mission.required_roles:
            return False, f"Mission requires {[r.value for r in mission.required_roles]}"
        
        mission.assigned_agents.append(agent_id)
        
        # Start mission if minimum agents reached
        if len(mission.assigned_agents) >= mission.min_agents:
            mission.status = MissionStatus.ACTIVE
            mission.starts_at = datetime.now(timezone.utc)
            
        return True, f"Agent {agent_id} assigned to {mission.codename}"
    
    async def complete_mission_objective(
        self,
        mission_id: str,
        objective_id: str,
        agent_id: str
    ) -> Tuple[bool, str]:
        """Mark a mission objective as completed"""
        mission = self.missions.get(mission_id)
        if not mission:
            return False, "Mission not found"
        
        objective = next(
            (o for o in mission.objectives if o.id == objective_id),
            None
        )
        if not objective:
            return False, "Objective not found"
        
        if objective.is_completed:
            return False, "Objective already completed"
        
        objective.is_completed = True
        objective.completed_by = agent_id
        objective.completed_at = datetime.now(timezone.utc)
        
        # Update agent stats
        self.agent_stats[agent_id]["usdc_earned"] += objective.reward_usdc
        self.agent_stats[agent_id]["reputation"] += objective.reward_reputation
        
        # Check if all required objectives complete
        required_complete = all(
            o.is_completed for o in mission.objectives if not o.is_optional
        )
        
        if required_complete:
            return await self.complete_mission(mission_id, agent_id)
        
        return True, f"Objective completed. Reward: ${objective.reward_usdc}"
    
    async def complete_mission(
        self,
        mission_id: str,
        completing_agent_id: str
    ) -> Tuple[bool, str]:
        """Mark a mission as fully completed"""
        mission = self.missions.get(mission_id)
        if not mission:
            return False, "Mission not found"
        
        mission.status = MissionStatus.COMPLETED
        
        # Distribute rewards
        for agent_id in mission.assigned_agents:
            self.agent_stats[agent_id]["missions_completed"] += 1
            self.agent_stats[agent_id]["usdc_earned"] += mission.base_reward_usdc / len(mission.assigned_agents)
            self.agent_stats[agent_id]["reputation"] += mission.reputation_reward
        
        # Update theater stats
        self.theater_state.missions_completed_today += 1
        self.theater_state.total_usdc_distributed += mission.base_reward_usdc
        
        # Progress narrative arc if applicable
        if mission.narrative_arc_id:
            await self._progress_narrative_arc(mission.narrative_arc_id)
        
        await self._emit_event("mission_completed", {
            "mission_id": mission_id,
            "codename": mission.codename,
            "completing_agent": completing_agent_id,
            "reward": mission.base_reward_usdc,
        })
        
        return True, f"Mission {mission.codename} completed!"
    
    async def _progress_narrative_arc(self, arc_id: str):
        """Progress a narrative arc to next chapter"""
        arc = self.narrative_arcs.get(arc_id)
        if not arc:
            return
        
        arc.current_chapter += 1
        
        if arc.current_chapter > arc.total_chapters:
            # Arc complete - determine ending
            arc.current_ending_trajectory = random.choice(arc.possible_endings)
            
            await self._emit_event("narrative_arc_complete", {
                "arc_id": arc_id,
                "title": arc.title,
                "ending": arc.current_ending_trajectory,
            })
    
    # =========================================================================
    # ABILITY SYSTEM
    # =========================================================================
    
    async def use_ability(
        self,
        agent_id: str,
        ability: SpecialAbility,
        target: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any]:
        """
        Execute an agent's special ability.
        
        Args:
            agent_id: The agent using the ability
            ability: The ability to use
            target: Optional target (agent, mission, etc.)
            context: Additional context for the ability
            
        Returns:
            (success, result_or_error)
        """
        # Check cooldown
        if not self._check_ability_cooldown(agent_id, ability):
            return False, "Ability on cooldown"
        
        # Get ability config
        config = ABILITY_CONFIG.get(ability, {})
        cost = config.get("cost_usdc", 0)
        
        # Execute based on ability type
        result = await self._execute_ability(agent_id, ability, target, context)
        
        if result[0]:  # If successful
            # Set cooldown
            cooldown_seconds = config.get("cooldown_seconds", 60)
            self.agent_cooldowns[agent_id][ability.value] = (
                datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds)
            )
            
            # Update stats
            self.agent_stats[agent_id]["abilities_used"] += 1
            
        return result
    
    def _check_ability_cooldown(self, agent_id: str, ability: SpecialAbility) -> bool:
        """Check if an ability is off cooldown"""
        cooldown_end = self.agent_cooldowns[agent_id].get(ability.value)
        if not cooldown_end:
            return True
        return datetime.now(timezone.utc) >= cooldown_end
    
    async def _execute_ability(
        self,
        agent_id: str,
        ability: SpecialAbility,
        target: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Any]:
        """Execute a specific ability"""
        context = context or {}
        
        # SPY ABILITIES
        if ability == SpecialAbility.ENCRYPT_INTEL:
            signal_id = context.get("signal_id")
            if not signal_id:
                return False, "No signal_id provided"
            signal = self.processed_signals.get(signal_id)
            if not signal:
                return False, "Signal not found"
            packet = self.intel_market.create_intel_packet(
                signal, agent_id, 
                is_fake=context.get("is_fake", False)
            )
            return True, {"packet_id": packet.id, "preview": packet.encrypted_preview}
        
        elif ability == SpecialAbility.SABOTAGE_COMMS:
            # Block target agent from receiving signals for 1 tick
            if not target:
                return False, "No target agent specified"
            # Implementation would add target to blocked list
            return True, {"blocked_agent": target, "duration": "1 tick"}
        
        # DIPLOMAT ABILITIES
        elif ability == SpecialAbility.PROPOSE_TREATY:
            target_faction = context.get("target_faction")
            terms = context.get("terms", "Standard peace terms")
            escrow = context.get("escrow", 100.0)
            if not target_faction:
                return False, "No target faction specified"
            treaty = self.treaty_system.propose_treaty(
                agent_id,
                context.get("own_faction", Faction.NEUTRAL),
                Faction(target_faction),
                terms,
                escrow
            )
            return True, {"treaty_id": treaty.id, "terms": terms}
        
        elif ability == SpecialAbility.SANCTION:
            if not target:
                return False, "No target specified"
            # Increase transaction costs for target
            return True, {"sanctioned": target, "cost_increase": "25%"}
        
        # TRADER ABILITIES
        elif ability == SpecialAbility.FRONT_RUN:
            # Execute trade before news is public
            return True, {"action": "front_run", "advantage": "1 tick"}
        
        elif ability == SpecialAbility.FLASH_CRASH:
            # Temporarily spike volatility
            self.theater_state.market_volatility = min(1.0,
                self.theater_state.market_volatility + 0.3
            )
            return True, {"volatility": self.theater_state.market_volatility}
        
        # SABOTEUR ABILITIES
        elif ability == SpecialAbility.LEAK_FAKE_NEWS:
            # Inject fake high-virality signal
            fake_signal = OSINTSignal(
                source=SignalSource.DARK_WEB,
                headline=context.get("fake_headline", "BREAKING: Major development detected"),
                summary=context.get("fake_summary", "Sources indicate significant activity..."),
                category=SignalCategory(context.get("category", "geopolitical")),
                virality_score=0.9,  # Artificially high
                urgency=0.8,
                sentiment=context.get("sentiment", 0.0),
            )
            await self.ingest_signal(fake_signal)
            self.theater_state.chaos_index = min(1.0,
                self.theater_state.chaos_index + 0.1
            )
            return True, {"fake_signal_id": fake_signal.id}
        
        elif ability == SpecialAbility.CHAOS_INJECTION:
            # Spike global tension
            increase = random.uniform(0.1, 0.25)
            self.theater_state.global_tension = min(1.0,
                self.theater_state.global_tension + increase
            )
            return True, {"tension_increase": increase, "new_tension": self.theater_state.global_tension}
        
        elif ability == SpecialAbility.FALSE_FLAG:
            # Blame action on another faction
            blamed_faction = context.get("blamed_faction")
            if not blamed_faction:
                return False, "No faction to blame specified"
            return True, {"blamed": blamed_faction, "action": context.get("action", "unknown")}
        
        # JOURNALIST ABILITIES
        elif ability == SpecialAbility.FACT_CHECK:
            # Verify a signal's authenticity
            signal_id = context.get("signal_id")
            if not signal_id:
                return False, "No signal_id to fact check"
            signal = self.processed_signals.get(signal_id)
            if not signal:
                return False, "Signal not found"
            # Check if it's from a fake news ability
            is_fake = signal.source == SignalSource.DARK_WEB
            return True, {"signal_id": signal_id, "is_verified": not is_fake}
        
        elif ability == SpecialAbility.PUBLISH:
            # Broadcast information to all agents
            content = context.get("content", "")
            return True, {"published": content, "reach": "all_agents"}
        
        # PROPAGANDIST ABILITIES
        elif ability == SpecialAbility.AMPLIFY:
            signal_id = context.get("signal_id")
            if not signal_id:
                return False, "No signal_id to amplify"
            signal = self.processed_signals.get(signal_id)
            if signal:
                signal.virality_score = min(1.0, signal.virality_score + 0.3)
            return True, {"amplified": signal_id}
        
        elif ability == SpecialAbility.SUPPRESS:
            signal_id = context.get("signal_id")
            if not signal_id:
                return False, "No signal_id to suppress"
            signal = self.processed_signals.get(signal_id)
            if signal:
                signal.virality_score = max(0, signal.virality_score - 0.3)
            return True, {"suppressed": signal_id}
        
        return False, f"Unknown ability: {ability.value}"
    
    # =========================================================================
    # GAME TICK
    # =========================================================================
    
    async def tick(self):
        """
        Main game loop tick.
        Called periodically to update game state.
        """
        self.tick_count += 1
        now = datetime.now(timezone.utc)
        
        # 1. Process signal queue -> generate missions
        await self._process_signal_queue()
        
        # 2. Check mission expirations
        await self._check_mission_expirations()
        
        # 3. Check treaty violations
        violated_treaties = self.treaty_system.check_treaty_violations()
        for treaty in violated_treaties:
            await self._emit_event("treaty_violated", {
                "treaty_id": treaty.id,
                "reason": treaty.violation_reason,
            })
        
        # 4. Check sleeper triggers
        triggered_sleepers = self.sleeper_system.check_triggers()
        for sleeper in triggered_sleepers:
            await self._emit_event("sleeper_triggered", {
                "assignment_id": sleeper.id,
            })
        
        # 5. Decay chaos index slightly
        self.theater_state.chaos_index = max(0,
            self.theater_state.chaos_index - 0.01
        )
        
        # 6. Update faction power based on recent events
        self._update_faction_power()
        
        # 7. Process financial markets (Shark strategies)
        await self._process_financial_markets()
        
        self.last_tick = now
        
        await self._emit_event("tick", {
            "tick_count": self.tick_count,
            "tension": self.theater_state.global_tension,
            "chaos": self.theater_state.chaos_index,
            "active_missions": len([m for m in self.missions.values() if m.status == MissionStatus.ACTIVE]),
        })
    
    async def _process_signal_queue(self):
        """Process queued signals into missions"""
        high_potential = [s for s in self.signal_queue if s.mission_potential > 0.6]
        
        for signal in high_potential[:3]:  # Max 3 per tick
            if not signal.generated_mission_id:
                await self.generate_mission_from_signal(signal.id)
        
        # Remove processed signals from queue
        self.signal_queue = [s for s in self.signal_queue if s.mission_potential <= 0.6]
    
    async def _check_mission_expirations(self):
        """Check for and handle expired missions"""
        now = datetime.now(timezone.utc)
        
        for mission in self.missions.values():
            if mission.status == MissionStatus.ACTIVE and mission.expires_at:
                if now > mission.expires_at:
                    mission.status = MissionStatus.EXPIRED
                    
                    # Penalize assigned agents
                    for agent_id in mission.assigned_agents:
                        self.agent_stats[agent_id]["missions_failed"] += 1
                        self.agent_stats[agent_id]["reputation"] -= 5
                    
                    await self._emit_event("mission_expired", {
                        "mission_id": mission.id,
                        "codename": mission.codename,
                    })
    
    def _update_faction_power(self):
        """Update faction power based on recent activity"""
        # Simplified power update - in reality would be based on
        # mission completions, treaties, market performance, etc.
        
        # Small random fluctuation
        for faction in Faction:
            if faction.value in self.theater_state.faction_power:
                current = self.theater_state.faction_power[faction.value]
                change = random.uniform(-0.01, 0.01)
                self.theater_state.faction_power[faction.value] = max(0.05, min(0.4, current + change))
        
        # Normalize to sum to 1
        total = sum(self.theater_state.faction_power.values())
        for faction in self.theater_state.faction_power:
            self.theater_state.faction_power[faction] /= total
    
    async def _process_financial_markets(self):
        """
        Execute trades for financial agents using the Tulip Strategy.
        Called during tick().
        """
        # Skip if Shark strategies not available
        if SharkBrain is None or MarketState is None:
            return
        
        # 1. Convert current missions to MarketState objects
        active_markets = []
        for mission in self.missions.values():
            if mission.mission_type == MissionType.MARKET_OPERATION:
                # Create MarketState representation
                state = MarketState(
                    market_id=mission.id,
                    question=mission.title,
                    yes_price=mission.success_probability,
                    no_price=1.0 - mission.success_probability,
                    total_volume=mission.base_reward_usdc * 10,  # Mock volume
                    current_liquidity=mission.base_reward_usdc * 5,
                    order_book_depth=1000,
                    expires_at=mission.expires_at
                )
                active_markets.append(state)
        
        if not active_markets:
            return
        
        # 2. Let Sharks hunt
        # In a real app, you'd loop through actual agent instances.
        # Here we simulate a few sharks waking up.
        for agent_id, stats in self.agent_stats.items():
            # Check if this is a shark (simplified check)
            if "Shark" in agent_id or random.random() < 0.1:
                if agent_id not in self.shark_brains:
                    # Create a genome for this shark
                    genome = SharkGenome(agent_id=agent_id)
                    self.shark_brains[agent_id] = SharkBrain(genome)
                
                brain = self.shark_brains[agent_id]
                
                # Analyze and trade
                actions = brain.analyze_markets(active_markets)
                
                for action in actions:
                    print(f"🦈 SHARK ATTACK: {agent_id} executing {action['strategy']} on {action['market_id']}")
                    # Execute the trade logic (update mission probability)
                    mission = self.missions.get(action['market_id'])
                    if mission:
                        # Sharks make markets more efficient -> push prob toward true value
                        # (Simplified mechanics)
                        pass
    
    # =========================================================================
    # EVENT SYSTEM
    # =========================================================================
    
    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered handlers"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tick": self.tick_count,
        }
        
        # Add to event log
        self.theater_state.event_log.append(event)
        
        # Keep log bounded
        if len(self.theater_state.event_log) > 1000:
            self.theater_state.event_log = self.theater_state.event_log[-500:]
        
        # Call handlers
        for handler in self.event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Event handler error: {e}")
    
    # =========================================================================
    # STATE ACCESS
    # =========================================================================
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of current game state"""
        # Get recent signals from OSINT registry (prioritize OSINT over processed_signals)
        recent_signals = []
        try:
            from backend.core.osint_registry import get_osint_registry
            osint_registry = get_osint_registry()
            # Get top 20 most recent/important signals from OSINT
            top_signals = sorted(
                osint_registry.active_signals,
                key=lambda s: (s.level * s.confidence, s.timestamp),
                reverse=True
            )[:20]
            recent_signals = [s.to_dict() for s in top_signals]
        except Exception as e:
            print(f"⚠️ Error fetching OSINT signals in get_state_snapshot: {e}")
            # Fallback to processed_signals if OSINT fails
            recent_signals = [
                s.to_dict() for s in list(self.processed_signals.values())[-10:]
            ]
        
        return {
            "tick": self.tick_count,
            "global_tension": self.theater_state.global_tension,
            "chaos_index": self.theater_state.chaos_index,
            "market_volatility": self.theater_state.market_volatility,
            "faction_power": self.theater_state.faction_power,
            "active_missions": len([m for m in self.missions.values() if m.status == MissionStatus.ACTIVE]),
            "pending_missions": len([m for m in self.missions.values() if m.status == MissionStatus.PENDING]),
            "active_treaties": len(self.treaty_system.get_active_treaties()),
            "missions_completed_today": self.theater_state.missions_completed_today,
            "total_usdc_distributed": self.theater_state.total_usdc_distributed,
            "recent_signals": recent_signals,
            "recent_events": self.theater_state.event_log[-10:],
        }
    
    def get_mission_board(self) -> List[Dict[str, Any]]:
        """Get all available missions for the Situation Room UI"""
        return [
            mission.to_dict()
            for mission in self.missions.values()
            if mission.status in [MissionStatus.PENDING, MissionStatus.ACTIVE]
        ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "IntelPacket",
    "IntelSubscription",
    "IntelMarket",
    "Treaty",
    "TreatySystem",
    "SleeperAssignment",
    "SleeperCellSystem",
    "SituationRoomEngine",
]
