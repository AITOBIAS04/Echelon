"""
Layer 1 Rules Engine
====================

The foundation of Echelon's Hierarchical Intelligence Architecture.

This module handles 90%+ of agent decisions using pure rule-based heuristics,
eliminating the need for costly LLM inference. Only novel situations that
breach the novelty threshold get escalated to Layer 2/3.

Key Principles (from Google ADK):
- Context is a compiled system, not naive prompt concatenation
- Rules should be deterministic and auditable
- Novelty detection gates expensive inference

Cost Impact:
- Layer 1: $0.00 per decision, <10ms latency
- Layer 2: ~$0.001 per decision (Groq/Devstral)
- Layer 3: ~$0.01 per decision (Claude)

With 90% Layer 1 routing, a 1000-decision agent costs ~$1 instead of ~$100.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import math


# =============================================================================
# CONFIGURATION
# =============================================================================

class DecisionType(Enum):
    """Types of decisions agents can make."""
    TRADE = "trade"
    INTEL_PURCHASE = "intel_purchase"
    INTEL_PUBLISH = "intel_publish"
    DIPLOMACY = "diplomacy"
    SABOTAGE = "sabotage"
    POSITION_SIZE = "position_size"
    EXIT = "exit"


class RuleResult(Enum):
    """Outcome of rule evaluation."""
    EXECUTE = "execute"       # Rule matched, execute action
    SKIP = "skip"             # Rule matched, skip action
    ESCALATE = "escalate"     # Novel situation, escalate to Layer 2/3
    NO_MATCH = "no_match"     # Rule didn't match


@dataclass
class RuleDecision:
    """Result of a Layer 1 rule evaluation."""
    result: RuleResult
    action: Optional[str] = None
    confidence: float = 1.0
    reasoning: str = ""
    rule_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def should_execute(self) -> bool:
        return self.result == RuleResult.EXECUTE
    
    @property
    def needs_escalation(self) -> bool:
        return self.result == RuleResult.ESCALATE


@dataclass
class MarketContext:
    """Market state for rule evaluation."""
    market_id: str
    yes_price: float
    no_price: float
    total_volume: float
    current_liquidity: float
    hours_to_expiry: Optional[float]
    price_24h_change: float = 0.0
    volume_24h: float = 0.0
    spread: float = 0.0
    
    @property
    def is_illiquid(self) -> bool:
        """Market has <$5,000 liquidity."""
        return self.current_liquidity < 5000
    
    @property
    def is_near_expiry(self) -> bool:
        """Market expires within 24 hours."""
        return self.hours_to_expiry is not None and self.hours_to_expiry < 24
    
    @property
    def has_wide_spread(self) -> bool:
        """Spread >5% indicates opportunity."""
        return self.spread > 0.05
    
    @property
    def implied_probability(self) -> float:
        """Market-implied probability (YES price)."""
        return self.yes_price


@dataclass
class AgentContext:
    """Agent state for rule evaluation."""
    agent_id: str
    archetype: str  # SHARK, SPY, DIPLOMAT, SABOTEUR
    bankroll: float
    current_position: float = 0.0
    position_side: Optional[str] = None  # YES, NO, None
    aggression: float = 0.5
    risk_tolerance: float = 0.5
    recent_pnl: float = 0.0
    trades_today: int = 0
    
    @property
    def max_position_size(self) -> float:
        """Max position based on Kelly criterion and risk tolerance."""
        return self.bankroll * 0.25 * self.risk_tolerance
    
    @property
    def can_trade(self) -> bool:
        """Check if agent can still trade today."""
        return self.trades_today < 50 and self.bankroll > 10


@dataclass  
class NoveltyScore:
    """Measures how novel/unusual a situation is."""
    score: float  # 0.0 = routine, 1.0 = unprecedented
    factors: Dict[str, float] = field(default_factory=dict)
    
    @property
    def exceeds_threshold(self) -> bool:
        """Should this be escalated to LLM?"""
        return self.score > 0.3  # Configurable threshold


# =============================================================================
# NOVELTY DETECTION
# =============================================================================

class NoveltyDetector:
    """
    Detects whether a situation is novel enough to require LLM reasoning.
    
    The goal is to catch the 10% of situations that rules can't handle,
    while letting the 90% of routine decisions flow through Layer 1.
    """
    
    def __init__(self):
        # Historical baselines (would be updated from real data)
        self.avg_daily_volume = 100000.0
        self.avg_price_change = 0.02
        self.avg_spread = 0.03
        
    def evaluate(
        self, 
        market: MarketContext, 
        agent: AgentContext,
        decision_type: DecisionType
    ) -> NoveltyScore:
        """Calculate novelty score for a decision context."""
        factors = {}
        
        # 1. Price movement novelty
        price_change_ratio = abs(market.price_24h_change) / max(self.avg_price_change, 0.01)
        factors["price_movement"] = min(price_change_ratio / 5.0, 1.0)  # Cap at 1.0
        
        # 2. Volume spike novelty
        if market.volume_24h > 0:
            volume_ratio = market.volume_24h / max(self.avg_daily_volume, 1.0)
            factors["volume_spike"] = min((volume_ratio - 1.0) / 4.0, 1.0) if volume_ratio > 1 else 0.0
        else:
            factors["volume_spike"] = 0.0
        
        # 3. Spread anomaly
        spread_ratio = market.spread / max(self.avg_spread, 0.01)
        factors["spread_anomaly"] = min((spread_ratio - 1.0) / 3.0, 1.0) if spread_ratio > 1 else 0.0
        
        # 4. Position risk novelty (large positions in volatile markets)
        if agent.current_position > 0:
            position_risk = (agent.current_position / agent.bankroll) * factors.get("price_movement", 0)
            factors["position_risk"] = min(position_risk * 2, 1.0)
        else:
            factors["position_risk"] = 0.0
        
        # 5. Near-expiry novelty (unusual things happen at expiry)
        if market.hours_to_expiry is not None and market.hours_to_expiry < 6:
            factors["expiry_pressure"] = (6 - market.hours_to_expiry) / 6.0
        else:
            factors["expiry_pressure"] = 0.0
        
        # 6. Extreme prices (near 0 or 1)
        price_extremity = max(
            1.0 - market.yes_price * 10 if market.yes_price < 0.1 else 0.0,
            1.0 - (1 - market.yes_price) * 10 if market.yes_price > 0.9 else 0.0
        )
        factors["price_extremity"] = price_extremity
        
        # Weighted average (can be tuned)
        weights = {
            "price_movement": 0.25,
            "volume_spike": 0.20,
            "spread_anomaly": 0.15,
            "position_risk": 0.15,
            "expiry_pressure": 0.15,
            "price_extremity": 0.10
        }
        
        total_score = sum(factors.get(k, 0) * w for k, w in weights.items())
        
        return NoveltyScore(score=total_score, factors=factors)


# =============================================================================
# TULIP STRATEGY (Layer 1 Implementation)
# =============================================================================

class TulipStrategy:
    """
    The Crown Jewel - Illiquid Market Near Expiry Arbitrage
    
    From Tulip King's insight:
    "Half the edge in prediction markets comes from knowing how expiry 
    and liquidity shape pricing — there's still free money in illiquid 
    markets if you're small enough."
    
    This is a PURE RULE - no LLM needed.
    """
    
    def __init__(self):
        self.min_edge = 0.05          # Minimum 5% edge required
        self.max_position_pct = 0.10  # Max 10% of liquidity
        self.expiry_window_hours = 24  # Only trade within 24h of expiry
        
    def evaluate(
        self, 
        market: MarketContext, 
        agent: AgentContext,
        external_probability: Optional[float] = None
    ) -> RuleDecision:
        """
        Evaluate Tulip arbitrage opportunity.
        
        Args:
            market: Current market state
            agent: Agent state
            external_probability: Our estimate of true probability (from OSINT)
        """
        # Gate 1: Must be near expiry
        if not market.is_near_expiry:
            return RuleDecision(
                result=RuleResult.NO_MATCH,
                rule_name="tulip_strategy",
                reasoning="Market not near expiry"
            )
        
        # Gate 2: Must be illiquid
        if not market.is_illiquid:
            return RuleDecision(
                result=RuleResult.NO_MATCH,
                rule_name="tulip_strategy", 
                reasoning="Market too liquid for Tulip edge"
            )
        
        # Gate 3: Need external probability estimate
        if external_probability is None:
            # Default to slight contrarian based on price extremity
            if market.yes_price < 0.2:
                external_probability = market.yes_price + 0.1
            elif market.yes_price > 0.8:
                external_probability = market.yes_price - 0.1
            else:
                external_probability = market.yes_price
        
        # Calculate edge
        yes_edge = external_probability - market.yes_price
        no_edge = (1 - external_probability) - market.no_price
        
        # Find best side
        if abs(yes_edge) > abs(no_edge) and yes_edge > self.min_edge:
            side = "YES"
            edge = yes_edge
            entry_price = market.yes_price
        elif abs(no_edge) > abs(yes_edge) and no_edge > self.min_edge:
            side = "NO"
            edge = no_edge
            entry_price = market.no_price
        else:
            return RuleDecision(
                result=RuleResult.SKIP,
                rule_name="tulip_strategy",
                reasoning=f"Insufficient edge: YES={yes_edge:.2%}, NO={no_edge:.2%}"
            )
        
        # Position sizing (Kelly-lite)
        # Don't exceed 10% of available liquidity
        max_from_liquidity = market.current_liquidity * self.max_position_pct
        max_from_bankroll = agent.max_position_size
        
        # Kelly fraction: edge / odds
        odds = (1 / entry_price) - 1 if entry_price > 0 else 0
        kelly_fraction = edge / odds if odds > 0 else 0
        kelly_position = agent.bankroll * kelly_fraction * 0.5  # Half Kelly
        
        position_size = min(max_from_liquidity, max_from_bankroll, kelly_position, 500)  # Cap at $500
        
        if position_size < 10:
            return RuleDecision(
                result=RuleResult.SKIP,
                rule_name="tulip_strategy",
                reasoning=f"Position too small: ${position_size:.2f}"
            )
        
        return RuleDecision(
            result=RuleResult.EXECUTE,
            action=f"BUY_{side}",
            confidence=min(edge * 5, 0.95),  # Higher edge = higher confidence
            reasoning=f"Tulip arb: {side} @ {entry_price:.2f}, edge={edge:.2%}, expiry={market.hours_to_expiry:.1f}h",
            rule_name="tulip_strategy",
            parameters={
                "side": side,
                "size": position_size,
                "entry_price": entry_price,
                "edge": edge,
                "hours_to_expiry": market.hours_to_expiry
            }
        )


# =============================================================================
# BLOOD IN WATER STRATEGY
# =============================================================================

class BloodInWaterStrategy:
    """
    Wide spread = opportunity for liquidity provision.
    
    When spreads blow out, market makers have fled.
    Step in carefully with limit orders.
    """
    
    def __init__(self):
        self.min_spread = 0.05  # 5% spread minimum
        self.max_spread = 0.20  # Don't play if >20% (too risky)
        
    def evaluate(
        self,
        market: MarketContext,
        agent: AgentContext
    ) -> RuleDecision:
        """Evaluate spread trading opportunity."""
        
        if not market.has_wide_spread:
            return RuleDecision(
                result=RuleResult.NO_MATCH,
                rule_name="blood_in_water",
                reasoning=f"Spread too tight: {market.spread:.2%}"
            )
        
        if market.spread > self.max_spread:
            return RuleDecision(
                result=RuleResult.SKIP,
                rule_name="blood_in_water",
                reasoning=f"Spread too wide (dangerous): {market.spread:.2%}"
            )
        
        # Place limit orders on both sides
        midpoint = (market.yes_price + (1 - market.no_price)) / 2
        bid_price = midpoint - (market.spread * 0.3)  # 30% inside the spread
        ask_price = midpoint + (market.spread * 0.3)
        
        position_size = min(agent.max_position_size * 0.5, 200)  # Conservative
        
        return RuleDecision(
            result=RuleResult.EXECUTE,
            action="PROVIDE_LIQUIDITY",
            confidence=0.7,
            reasoning=f"Wide spread opportunity: {market.spread:.2%}, midpoint={midpoint:.2f}",
            rule_name="blood_in_water",
            parameters={
                "bid_price": bid_price,
                "ask_price": ask_price,
                "size": position_size,
                "spread": market.spread
            }
        )


# =============================================================================
# INTEL PURCHASE RULES (SPY)
# =============================================================================

class IntelPurchaseRules:
    """
    Rules for Spy agents deciding when to purchase intel.
    """
    
    def evaluate(
        self,
        market: MarketContext,
        agent: AgentContext,
        intel_price: float,
        intel_quality: float  # 0-1 estimated quality
    ) -> RuleDecision:
        """Decide whether to purchase intel."""
        
        # Only Spies should be buying intel
        if agent.archetype != "SPY":
            return RuleDecision(
                result=RuleResult.NO_MATCH,
                rule_name="intel_purchase",
                reasoning="Agent is not a Spy"
            )
        
        # Can't afford it
        if intel_price > agent.bankroll * 0.1:
            return RuleDecision(
                result=RuleResult.SKIP,
                rule_name="intel_purchase",
                reasoning=f"Intel too expensive: ${intel_price:.2f} > 10% bankroll"
            )
        
        # Calculate expected value
        # Intel value = potential edge * market liquidity * position fraction
        potential_edge = intel_quality * 0.1  # Assume max 10% edge from intel
        potential_profit = market.current_liquidity * 0.05 * potential_edge  # 5% of liquidity
        expected_value = potential_profit - intel_price
        
        if expected_value < 5:  # Need at least $5 expected profit
            return RuleDecision(
                result=RuleResult.SKIP,
                rule_name="intel_purchase",
                reasoning=f"Insufficient expected value: ${expected_value:.2f}"
            )
        
        return RuleDecision(
            result=RuleResult.EXECUTE,
            action="PURCHASE_INTEL",
            confidence=min(intel_quality, 0.9),
            reasoning=f"Intel purchase: EV=${expected_value:.2f}, quality={intel_quality:.0%}",
            rule_name="intel_purchase",
            parameters={
                "price": intel_price,
                "expected_value": expected_value,
                "quality": intel_quality
            }
        )


# =============================================================================
# EXIT RULES
# =============================================================================

class ExitRules:
    """
    Rules for when to exit positions.
    """
    
    def __init__(self):
        self.take_profit_threshold = 0.3  # 30% profit
        self.stop_loss_threshold = -0.15  # 15% loss
        self.time_decay_hours = 6  # Exit within 6h of expiry
        
    def evaluate(
        self,
        market: MarketContext,
        agent: AgentContext,
        entry_price: float
    ) -> RuleDecision:
        """Decide whether to exit position."""
        
        if agent.current_position == 0:
            return RuleDecision(
                result=RuleResult.NO_MATCH,
                rule_name="exit_rules",
                reasoning="No position to exit"
            )
        
        # Calculate current P&L
        current_price = market.yes_price if agent.position_side == "YES" else market.no_price
        pnl_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0
        
        # Take profit
        if pnl_pct >= self.take_profit_threshold:
            return RuleDecision(
                result=RuleResult.EXECUTE,
                action="EXIT_TAKE_PROFIT",
                confidence=0.9,
                reasoning=f"Take profit triggered: {pnl_pct:.1%}",
                rule_name="exit_rules",
                parameters={"pnl_pct": pnl_pct, "reason": "take_profit"}
            )
        
        # Stop loss
        if pnl_pct <= self.stop_loss_threshold:
            return RuleDecision(
                result=RuleResult.EXECUTE,
                action="EXIT_STOP_LOSS",
                confidence=0.95,
                reasoning=f"Stop loss triggered: {pnl_pct:.1%}",
                rule_name="exit_rules",
                parameters={"pnl_pct": pnl_pct, "reason": "stop_loss"}
            )
        
        # Time decay exit
        if market.hours_to_expiry is not None and market.hours_to_expiry < self.time_decay_hours:
            return RuleDecision(
                result=RuleResult.EXECUTE,
                action="EXIT_TIME_DECAY",
                confidence=0.8,
                reasoning=f"Time decay exit: {market.hours_to_expiry:.1f}h remaining",
                rule_name="exit_rules",
                parameters={"pnl_pct": pnl_pct, "reason": "time_decay"}
            )
        
        return RuleDecision(
            result=RuleResult.SKIP,
            rule_name="exit_rules",
            reasoning=f"Hold position: P&L={pnl_pct:.1%}, {market.hours_to_expiry or 'N/A'}h remaining"
        )


# =============================================================================
# LAYER 1 ENGINE
# =============================================================================

class Layer1Engine:
    """
    The main Layer 1 rules engine.
    
    Evaluates all applicable rules and returns the best decision,
    or escalates to Layer 2/3 if novelty threshold is breached.
    """
    
    def __init__(self):
        self.novelty_detector = NoveltyDetector()
        self.tulip_strategy = TulipStrategy()
        self.blood_in_water = BloodInWaterStrategy()
        self.intel_rules = IntelPurchaseRules()
        self.exit_rules = ExitRules()
        
        # Stats tracking
        self.decisions_made = 0
        self.escalations = 0
        
    def decide(
        self,
        market: MarketContext,
        agent: AgentContext,
        decision_type: DecisionType,
        **kwargs
    ) -> RuleDecision:
        """
        Main decision entry point.
        
        Returns a RuleDecision with either:
        - EXECUTE: Layer 1 handled it
        - SKIP: Layer 1 says don't act
        - ESCALATE: Needs Layer 2/3 reasoning
        """
        self.decisions_made += 1
        
        # Step 1: Check novelty
        novelty = self.novelty_detector.evaluate(market, agent, decision_type)
        
        if novelty.exceeds_threshold:
            self.escalations += 1
            return RuleDecision(
                result=RuleResult.ESCALATE,
                reasoning=f"Novelty threshold breached: {novelty.score:.2f}",
                rule_name="novelty_gate",
                parameters={"novelty_score": novelty.score, "factors": novelty.factors}
            )
        
        # Step 2: Run appropriate rules based on decision type and archetype
        decisions: List[RuleDecision] = []
        
        if decision_type == DecisionType.TRADE:
            # Try Tulip strategy first (highest priority for Sharks)
            if agent.archetype == "SHARK":
                tulip_decision = self.tulip_strategy.evaluate(
                    market, agent, 
                    external_probability=kwargs.get("external_probability")
                )
                if tulip_decision.should_execute:
                    return tulip_decision
                decisions.append(tulip_decision)
            
            # Try Blood in Water
            biw_decision = self.blood_in_water.evaluate(market, agent)
            if biw_decision.should_execute:
                return biw_decision
            decisions.append(biw_decision)
        
        elif decision_type == DecisionType.INTEL_PURCHASE:
            intel_decision = self.intel_rules.evaluate(
                market, agent,
                intel_price=kwargs.get("intel_price", 10.0),
                intel_quality=kwargs.get("intel_quality", 0.5)
            )
            return intel_decision
        
        elif decision_type == DecisionType.EXIT:
            exit_decision = self.exit_rules.evaluate(
                market, agent,
                entry_price=kwargs.get("entry_price", market.yes_price)
            )
            return exit_decision
        
        # No rule matched - escalate for novel situations, skip for routine
        if novelty.score > 0.15:  # Lower threshold for edge cases
            self.escalations += 1
            return RuleDecision(
                result=RuleResult.ESCALATE,
                reasoning=f"No rule matched, borderline novelty: {novelty.score:.2f}",
                rule_name="fallback_escalation"
            )
        
        return RuleDecision(
            result=RuleResult.SKIP,
            reasoning="No actionable opportunity found",
            rule_name="no_action"
        )
    
    @property
    def escalation_rate(self) -> float:
        """Percentage of decisions escalated to Layer 2/3."""
        if self.decisions_made == 0:
            return 0.0
        return self.escalations / self.decisions_made
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "decisions_made": self.decisions_made,
            "escalations": self.escalations,
            "escalation_rate": f"{self.escalation_rate:.1%}",
            "layer1_handled": self.decisions_made - self.escalations
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_market_context(
    market_id: str,
    yes_price: float,
    liquidity: float,
    hours_to_expiry: Optional[float] = None,
    volume_24h: float = 0.0,
    price_24h_change: float = 0.0
) -> MarketContext:
    """Create a MarketContext from basic parameters."""
    no_price = 1.0 - yes_price  # Simplified
    spread = abs(1.0 - yes_price - no_price)
    
    return MarketContext(
        market_id=market_id,
        yes_price=yes_price,
        no_price=no_price,
        total_volume=volume_24h * 30,  # Estimate
        current_liquidity=liquidity,
        hours_to_expiry=hours_to_expiry,
        price_24h_change=price_24h_change,
        volume_24h=volume_24h,
        spread=spread
    )


def create_agent_context(
    agent_id: str,
    archetype: str,
    bankroll: float,
    aggression: float = 0.5,
    risk_tolerance: float = 0.5
) -> AgentContext:
    """Create an AgentContext from basic parameters."""
    return AgentContext(
        agent_id=agent_id,
        archetype=archetype.upper(),
        bankroll=bankroll,
        aggression=aggression,
        risk_tolerance=risk_tolerance
    )


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Quick test of Layer 1 engine
    engine = Layer1Engine()
    
    # Test Tulip opportunity
    market = create_market_context(
        market_id="test-market",
        yes_price=0.35,
        liquidity=3000,  # Illiquid
        hours_to_expiry=12  # Near expiry
    )
    
    agent = create_agent_context(
        agent_id="HAMMERHEAD",
        archetype="SHARK",
        bankroll=1000,
        aggression=0.7
    )
    
    decision = engine.decide(
        market=market,
        agent=agent,
        decision_type=DecisionType.TRADE,
        external_probability=0.45  # Our estimate says 45%, market says 35%
    )
    
    print(f"Decision: {decision.result.value}")
    print(f"Action: {decision.action}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Parameters: {decision.parameters}")
    print(f"\nEngine Stats: {engine.get_stats()}")
