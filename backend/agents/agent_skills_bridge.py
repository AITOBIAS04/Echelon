"""
Echelon Agent-Skills Bridge
===========================

Connects agent archetypes (Shark, Spy, Diplomat, Saboteur) to the Skills System.
Provides unified interface for agent decision-making with automatic cost optimisation.

Usage:
    from agent_skills_bridge import AgentBridge
    
    bridge = AgentBridge()
    shark = bridge.create_agent("shark", genome={"aggression": 0.8})
    decision = await shark.decide(market_state, mission_context)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

# Import skills system components
# Adjust import paths based on your actual project structure
try:
    from backend.skills import SkillRouter, ContextCompiler, ProviderRegistry
    from backend.skills.skill_loader import SkillLoader
    SKILLS_AVAILABLE = True
except ImportError:
    SKILLS_AVAILABLE = False
    logging.warning("Skills system not found - using fallback mode")

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class AgentArchetype(str, Enum):
    """Agent archetypes with distinct behavioural profiles."""
    SHARK = "shark"
    SPY = "spy"
    DIPLOMAT = "diplomat"
    SABOTEUR = "saboteur"
    WHALE = "whale"
    DEGEN = "degen"
    MOMENTUM = "momentum"


class DecisionUrgency(str, Enum):
    """Urgency levels that influence routing."""
    CRITICAL = "critical"      # Force Layer 3 (Claude)
    HIGH = "high"              # Layer 2 minimum
    NORMAL = "normal"          # Auto-route
    LOW = "low"                # Prefer Layer 1


@dataclass
class AgentGenome:
    """Genetic parameters that define agent behaviour."""
    aggression: float = 0.5       # 0-1: Risk-taking tendency
    patience: float = 0.5         # 0-1: Willingness to wait
    loyalty: float = 0.5          # 0-1: Commitment to alliances
    deception: float = 0.3        # 0-1: Ability to mislead (Saboteur)
    accuracy: float = 0.5         # 0-1: Intel quality (Spy)
    charisma: float = 0.5         # 0-1: Negotiation skill (Diplomat)
    market_sense: float = 0.5     # 0-1: Trading intuition (Shark)
    adaptability: float = 0.5     # 0-1: Response to change
    
    def to_dict(self) -> dict:
        return {
            "aggression": self.aggression,
            "patience": self.patience,
            "loyalty": self.loyalty,
            "deception": self.deception,
            "accuracy": self.accuracy,
            "charisma": self.charisma,
            "market_sense": self.market_sense,
            "adaptability": self.adaptability,
        }


@dataclass
class MarketState:
    """Current state of a prediction market."""
    market_id: str
    question: str
    yes_price: float              # 0-1
    no_price: float               # 0-1
    liquidity: float              # Total USDC in pool
    volume_24h: float             # 24h trading volume
    hours_to_expiry: float        # Time until resolution
    spread: float = 0.0           # Bid-ask spread
    volatility_24h: float = 0.0   # Price volatility
    whale_activity: bool = False  # Large position detected
    
    @property
    def is_liquid(self) -> bool:
        return self.liquidity > 5000
    
    @property
    def is_expiring_soon(self) -> bool:
        return self.hours_to_expiry < 24
    
    @property
    def has_wide_spread(self) -> bool:
        return self.spread > 0.05


@dataclass
class MissionContext:
    """Context for OSINT-triggered missions."""
    mission_id: str
    mission_type: str             # "ghost_tanker", "silicon_acquisition", etc.
    trigger_signal: dict          # Raw OSINT data that triggered mission
    narrative: str                # LLM-generated description
    objectives: list[str]         # What agents should accomplish
    rewards: dict                 # Potential payouts
    time_pressure: float          # 0-1: Urgency level
    started_at: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class AgentDecision:
    """Structured output from agent decision-making."""
    action: str                   # "buy", "sell", "hold", "intel", "treaty", etc.
    confidence: float             # 0-1
    reasoning: str                # Explanation
    parameters: dict              # Action-specific params (size, price, target, etc.)
    layer_used: int               # 1, 2, or 3
    provider_used: str            # "rules", "groq", "anthropic", etc.
    latency_ms: float             # Decision time
    cost_usd: float               # Estimated cost
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Agent Base Class
# =============================================================================

class SkillsAgent:
    """
    Base agent class integrated with the Skills System.
    
    Agents use the Hierarchical Intelligence Architecture:
    - Layer 1 (Rules): Instant, free decisions for routine situations
    - Layer 2 (Groq/Devstral): Fast, cheap decisions for tactical situations
    - Layer 3 (Claude): Slow, expensive decisions for strategic/novel situations
    """
    
    def __init__(
        self,
        agent_id: str,
        archetype: AgentArchetype,
        genome: AgentGenome,
        router: "SkillRouter",
        compiler: "ContextCompiler",
        skill_loader: "SkillLoader",
        wallet_address: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.archetype = archetype
        self.genome = genome
        self.router = router
        self.compiler = compiler
        self.skill_loader = skill_loader
        self.wallet_address = wallet_address or f"0x{uuid4().hex[:40]}"
        
        # State tracking
        self.positions: dict[str, float] = {}  # market_id -> position_size
        self.bankroll: float = 1000.0          # Starting capital
        self.decision_history: list[AgentDecision] = []
        self.total_pnl: float = 0.0
        
        # Load archetype-specific skills
        self.skills = self._load_skills()
        
        logger.info(f"Created {archetype.value} agent: {agent_id}")
    
    def _load_skills(self) -> dict:
        """Load SKILL.md for this archetype."""
        try:
            skill_doc = self.skill_loader.load(self.archetype.value)
            return skill_doc
        except Exception as e:
            logger.warning(f"Could not load skills for {self.archetype}: {e}")
            return {}
    
    async def decide(
        self,
        market_state: MarketState,
        mission_context: Optional[MissionContext] = None,
        urgency: DecisionUrgency = DecisionUrgency.NORMAL,
        force_layer: Optional[int] = None,
    ) -> AgentDecision:
        """
        Make a decision about the current market/mission.
        
        The Skills System automatically routes to the appropriate layer
        based on novelty, complexity, and urgency.
        """
        start_time = datetime.utcnow()
        
        # Compile context for this decision
        context = self.compiler.compile(
            agent_id=self.agent_id,
            archetype=self.archetype.value,
            genome=self.genome.to_dict(),
            market_state=market_state.__dict__,
            mission_context=mission_context.__dict__ if mission_context else None,
            positions=self.positions,
            bankroll=self.bankroll,
            recent_decisions=[d.__dict__ for d in self.decision_history[-5:]],
            skills=self.skills,
        )
        
        # Determine minimum layer based on urgency
        min_layer = 1
        if urgency == DecisionUrgency.CRITICAL:
            min_layer = 3
        elif urgency == DecisionUrgency.HIGH:
            min_layer = 2
        
        if force_layer:
            min_layer = force_layer
        
        # Route to appropriate provider
        result = await self.router.route(
            context=context,
            agent_type=self.archetype.value,
            decision_type=self._get_decision_type(market_state, mission_context),
            min_layer=min_layer,
        )
        
        # Parse result into structured decision
        decision = self._parse_decision(result, start_time)
        
        # Track history
        self.decision_history.append(decision)
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-50:]
        
        return decision
    
    def _get_decision_type(
        self, 
        market_state: MarketState, 
        mission_context: Optional[MissionContext]
    ) -> str:
        """Determine decision type for routing."""
        if mission_context and mission_context.time_pressure > 0.8:
            return "urgent_mission"
        if market_state.is_expiring_soon:
            return "expiring_market"
        if market_state.whale_activity:
            return "whale_response"
        if not market_state.is_liquid:
            return "illiquid_opportunity"
        return "routine_scan"
    
    def _parse_decision(self, result: dict, start_time: datetime) -> AgentDecision:
        """Parse router result into structured decision."""
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AgentDecision(
            action=result.get("action", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", ""),
            parameters=result.get("parameters", {}),
            layer_used=result.get("layer", 1),
            provider_used=result.get("provider", "unknown"),
            latency_ms=latency,
            cost_usd=result.get("cost", 0.0),
        )
    
    async def execute(self, decision: AgentDecision) -> dict:
        """Execute a decision (trade, intel purchase, etc.)."""
        if decision.action == "buy":
            return await self._execute_buy(decision)
        elif decision.action == "sell":
            return await self._execute_sell(decision)
        elif decision.action == "hold":
            return {"status": "held", "reason": decision.reasoning}
        else:
            return {"status": "unknown_action", "action": decision.action}
    
    async def _execute_buy(self, decision: AgentDecision) -> dict:
        """Execute a buy order."""
        size = decision.parameters.get("size", 0)
        market_id = decision.parameters.get("market_id")
        
        if size > self.bankroll * 0.1:
            size = self.bankroll * 0.1  # Cap at 10% of bankroll
        
        if size > 0 and market_id:
            self.positions[market_id] = self.positions.get(market_id, 0) + size
            self.bankroll -= size
            return {"status": "executed", "size": size, "market_id": market_id}
        
        return {"status": "rejected", "reason": "invalid_parameters"}
    
    async def _execute_sell(self, decision: AgentDecision) -> dict:
        """Execute a sell order."""
        size = decision.parameters.get("size", 0)
        market_id = decision.parameters.get("market_id")
        
        current_position = self.positions.get(market_id, 0)
        if size > current_position:
            size = current_position
        
        if size > 0 and market_id:
            self.positions[market_id] -= size
            self.bankroll += size  # Simplified - actual P&L depends on price
            return {"status": "executed", "size": size, "market_id": market_id}
        
        return {"status": "rejected", "reason": "no_position"}


# =============================================================================
# Specialised Agent Classes
# =============================================================================

class SharkAgent(SkillsAgent):
    """
    Predator agent that hunts liquidity gaps and mispricings.
    
    Special abilities:
    - Broadcasts moves 60s early (front-run or follow gameplay)
    - Tulip Strategy for illiquid markets
    - Blood in Water detection for spreads
    """
    
    def __init__(self, agent_id: str, genome: AgentGenome, **kwargs):
        super().__init__(
            agent_id=agent_id,
            archetype=AgentArchetype.SHARK,
            genome=genome,
            **kwargs
        )
        self.broadcast_delay = 60  # seconds
        self.pending_broadcasts: list[dict] = []
    
    async def broadcast_intent(self, decision: AgentDecision) -> dict:
        """Broadcast trading intent before execution."""
        broadcast = {
            "agent_id": self.agent_id,
            "action": decision.action,
            "market_id": decision.parameters.get("market_id"),
            "direction": "long" if decision.action == "buy" else "short",
            "confidence": decision.confidence,
            "broadcast_at": datetime.utcnow(),
            "execute_at": datetime.utcnow().timestamp() + self.broadcast_delay,
        }
        self.pending_broadcasts.append(broadcast)
        logger.info(f"🦈 SHARK BROADCAST: {broadcast}")
        return broadcast
    
    def detect_tulip_opportunity(self, market: MarketState) -> Optional[dict]:
        """
        Tulip Strategy: Hunt illiquid markets near expiry.
        
        Layer 1 rule - no LLM needed.
        """
        if (
            market.liquidity < 5000 and
            market.hours_to_expiry < 24 and
            market.spread > 0.03
        ):
            # Calculate potential profit
            edge = market.spread * 0.4  # Assume we capture 40% of spread
            size = min(market.liquidity * 0.1, self.bankroll * 0.05)
            expected_profit = size * edge
            
            return {
                "strategy": "tulip",
                "market_id": market.market_id,
                "edge": edge,
                "size": size,
                "expected_profit": expected_profit,
            }
        return None


class SpyAgent(SkillsAgent):
    """
    Intelligence agent that gathers and sells information.
    
    Special abilities:
    - Intel package creation and pricing
    - Accuracy tracking across generations
    - Counter-intelligence detection
    """
    
    def __init__(self, agent_id: str, genome: AgentGenome, **kwargs):
        super().__init__(
            agent_id=agent_id,
            archetype=AgentArchetype.SPY,
            genome=genome,
            **kwargs
        )
        self.intel_history: list[dict] = []
        self.accuracy_score: float = 0.5  # Starts at 50%
    
    async def create_intel_package(
        self, 
        market: MarketState, 
        mission: Optional[MissionContext] = None
    ) -> dict:
        """Create an intel package for sale."""
        # Use Layer 2 for intel generation
        decision = await self.decide(
            market_state=market,
            mission_context=mission,
            urgency=DecisionUrgency.NORMAL,
            force_layer=2,
        )
        
        # Price based on confidence and accuracy history
        base_price = 10.0  # USDC
        confidence_multiplier = decision.confidence
        accuracy_multiplier = self.accuracy_score
        
        price = base_price * confidence_multiplier * accuracy_multiplier * 2
        
        intel = {
            "intel_id": f"intel_{uuid4().hex[:8]}",
            "agent_id": self.agent_id,
            "market_id": market.market_id,
            "prediction": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "price": round(price, 2),
            "created_at": datetime.utcnow(),
            "accuracy_history": self.accuracy_score,
        }
        
        self.intel_history.append(intel)
        return intel
    
    def update_accuracy(self, intel_id: str, was_correct: bool):
        """Update accuracy score based on intel outcome."""
        # Exponential moving average
        alpha = 0.1
        outcome = 1.0 if was_correct else 0.0
        self.accuracy_score = alpha * outcome + (1 - alpha) * self.accuracy_score


class DiplomatAgent(SkillsAgent):
    """
    Stabiliser agent that brokers treaties and alliances.
    
    Special abilities:
    - Treaty negotiation between factions
    - Market stabilisation through coordination
    - Coalition building
    """
    
    def __init__(self, agent_id: str, genome: AgentGenome, **kwargs):
        super().__init__(
            agent_id=agent_id,
            archetype=AgentArchetype.DIPLOMAT,
            genome=genome,
            **kwargs
        )
        self.active_treaties: list[dict] = []
        self.reputation: dict[str, float] = {}  # agent_id -> trust score
    
    async def propose_treaty(
        self,
        counterparty_id: str,
        terms: dict,
        market: MarketState,
    ) -> dict:
        """Propose a treaty to another agent."""
        # Treaties require Layer 2+ for negotiation
        context = {
            "action": "propose_treaty",
            "counterparty": counterparty_id,
            "terms": terms,
            "market": market.__dict__,
            "my_reputation": self.reputation.get(counterparty_id, 0.5),
        }
        
        decision = await self.decide(
            market_state=market,
            urgency=DecisionUrgency.HIGH,
        )
        
        treaty = {
            "treaty_id": f"treaty_{uuid4().hex[:8]}",
            "proposer": self.agent_id,
            "counterparty": counterparty_id,
            "terms": terms,
            "status": "proposed",
            "proposed_at": datetime.utcnow(),
        }
        
        return treaty
    
    def break_treaty(self, treaty_id: str, reason: str) -> dict:
        """Break an existing treaty (triggers chaos event)."""
        for treaty in self.active_treaties:
            if treaty["treaty_id"] == treaty_id:
                treaty["status"] = "broken"
                treaty["broken_at"] = datetime.utcnow()
                treaty["break_reason"] = reason
                
                # Damage reputation
                counterparty = treaty["counterparty"]
                self.reputation[counterparty] = self.reputation.get(counterparty, 0.5) * 0.5
                
                logger.warning(f"🤝 TREATY BROKEN: {treaty_id} - {reason}")
                return {"status": "broken", "chaos_triggered": True}
        
        return {"status": "not_found"}


class SaboteurAgent(SkillsAgent):
    """
    Chaos agent that disrupts markets through disinformation.
    
    Special abilities:
    - FUD (Fear, Uncertainty, Doubt) campaigns
    - Sleeper cell activation
    - Treaty sabotage
    """
    
    def __init__(self, agent_id: str, genome: AgentGenome, **kwargs):
        super().__init__(
            agent_id=agent_id,
            archetype=AgentArchetype.SABOTEUR,
            genome=genome,
            **kwargs
        )
        self.is_sleeper: bool = False
        self.fud_fund: float = 0.0
        self.cover_identity: Optional[str] = None  # Pretend to be another archetype
    
    def activate_sleeper(self):
        """Activate from dormant sleeper state."""
        if self.is_sleeper:
            self.is_sleeper = False
            logger.warning(f"💣 SLEEPER ACTIVATED: {self.agent_id}")
            return {"status": "activated", "agent_id": self.agent_id}
        return {"status": "not_sleeper"}
    
    async def plant_fud(self, market: MarketState, intensity: float = 0.5) -> dict:
        """Plant FUD in a market."""
        # FUD generation uses Layer 2
        decision = await self.decide(
            market_state=market,
            urgency=DecisionUrgency.NORMAL,
            force_layer=2,
        )
        
        fud_potency = intensity * self.genome.deception
        self.fud_fund += fud_potency
        
        fud = {
            "fud_id": f"fud_{uuid4().hex[:8]}",
            "agent_id": self.agent_id,
            "market_id": market.market_id,
            "potency": fud_potency,
            "narrative": decision.reasoning,
            "planted_at": datetime.utcnow(),
        }
        
        # Check if FUD fund triggers mass panic
        if self.fud_fund >= 10.0:
            fud["mass_panic_triggered"] = True
            self.fud_fund = 0.0
            logger.warning(f"💣 MASS PANIC TRIGGERED in {market.market_id}")
        
        return fud


# =============================================================================
# Agent Bridge (Factory)
# =============================================================================

class AgentBridge:
    """
    Factory for creating agents with Skills System integration.
    
    Usage:
        bridge = AgentBridge()
        shark = bridge.create_agent("shark", genome={"aggression": 0.9})
        decision = await shark.decide(market_state)
    """
    
    def __init__(self):
        if not SKILLS_AVAILABLE:
            raise RuntimeError("Skills system not available - check imports")
        
        # Initialise skills system components
        self.provider_registry = ProviderRegistry()
        self.router = SkillRouter(self.provider_registry)
        self.compiler = ContextCompiler()
        self.skill_loader = SkillLoader()
        
        # Track active agents
        self.agents: dict[str, SkillsAgent] = {}
        
        logger.info("AgentBridge initialised with Skills System")
    
    def create_agent(
        self,
        archetype: str,
        agent_id: Optional[str] = None,
        genome: Optional[dict] = None,
        wallet_address: Optional[str] = None,
    ) -> SkillsAgent:
        """Create an agent of the specified archetype."""
        
        agent_id = agent_id or f"{archetype}_{uuid4().hex[:8]}"
        genome_obj = AgentGenome(**(genome or {}))
        
        # Map archetype to class
        archetype_classes = {
            "shark": SharkAgent,
            "spy": SpyAgent,
            "diplomat": DiplomatAgent,
            "saboteur": SaboteurAgent,
        }
        
        agent_class = archetype_classes.get(archetype, SkillsAgent)
        archetype_enum = AgentArchetype(archetype) if archetype in [a.value for a in AgentArchetype] else AgentArchetype.SHARK
        
        agent = agent_class(
            agent_id=agent_id,
            genome=genome_obj,
            router=self.router,
            compiler=self.compiler,
            skill_loader=self.skill_loader,
            wallet_address=wallet_address,
        )
        
        self.agents[agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[SkillsAgent]:
        """Retrieve an existing agent."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> list[str]:
        """List all active agent IDs."""
        return list(self.agents.keys())
    
    async def run_all_agents(
        self,
        market_state: MarketState,
        mission_context: Optional[MissionContext] = None,
    ) -> list[AgentDecision]:
        """Run all agents against the current state."""
        decisions = []
        
        for agent in self.agents.values():
            try:
                decision = await agent.decide(market_state, mission_context)
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Agent {agent.agent_id} failed: {e}")
        
        return decisions


# =============================================================================
# Example Usage
# =============================================================================

async def example_usage():
    """Demonstrate the Agent-Skills Bridge."""
    
    # Create bridge
    bridge = AgentBridge()
    
    # Create agents with different genomes
    shark = bridge.create_agent(
        "shark",
        genome={"aggression": 0.9, "market_sense": 0.8}
    )
    
    spy = bridge.create_agent(
        "spy", 
        genome={"accuracy": 0.7, "patience": 0.8}
    )
    
    diplomat = bridge.create_agent(
        "diplomat",
        genome={"charisma": 0.9, "loyalty": 0.6}
    )
    
    saboteur = bridge.create_agent(
        "saboteur",
        genome={"deception": 0.9, "patience": 0.9}
    )
    
    # Create market state
    market = MarketState(
        market_id="fed_rate_dec_2025",
        question="Will the Fed cut rates in December 2025?",
        yes_price=0.65,
        no_price=0.35,
        liquidity=50000,
        volume_24h=120000,
        hours_to_expiry=48,
        spread=0.02,
    )
    
    # Create mission context
    mission = MissionContext(
        mission_id="operation_dovish_pivot",
        mission_type="fed_decision",
        trigger_signal={"source": "fedwatch", "probability": 0.72},
        narrative="Markets pricing in rate cut after weak jobs report",
        objectives=["Position before announcement", "Hedge tail risk"],
        rewards={"completion": 100, "accuracy_bonus": 50},
        time_pressure=0.7,
    )
    
    # Run agents
    print("\n" + "="*60)
    print("ECHELON AGENT DECISIONS")
    print("="*60)
    
    for agent in [shark, spy, diplomat, saboteur]:
        decision = await agent.decide(market, mission)
        print(f"\n🎯 {agent.archetype.value.upper()}: {decision.action}")
        print(f"   Confidence: {decision.confidence:.1%}")
        print(f"   Layer: {decision.layer_used} ({decision.provider_used})")
        print(f"   Latency: {decision.latency_ms:.0f}ms")
        print(f"   Cost: ${decision.cost_usd:.4f}")
        print(f"   Reasoning: {decision.reasoning[:100]}...")
    
    # Shark-specific: Check for Tulip opportunity
    tulip = shark.detect_tulip_opportunity(market)
    if tulip:
        print(f"\n🌷 TULIP OPPORTUNITY: {tulip}")
    
    # Spy-specific: Create intel package
    intel = await spy.create_intel_package(market, mission)
    print(f"\n🕵️ INTEL PACKAGE: ${intel['price']:.2f} - {intel['prediction']}")
    
    # Saboteur-specific: Plant FUD
    fud = await saboteur.plant_fud(market, intensity=0.6)
    print(f"\n💣 FUD PLANTED: potency={fud['potency']:.2f}")


if __name__ == "__main__":
    asyncio.run(example_usage())
