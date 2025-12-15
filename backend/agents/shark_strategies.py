"""
Shark Strategies
================

Advanced trading strategies for "Shark" class agents.

Inspired by Tulip King's insight:
"Half the edge in prediction markets comes from knowing how expiry 
and liquidity shape pricing — there's still free money in illiquid 
markets if you're small enough."

These strategies give Shark agents realistic alpha over Novice/Degen agents.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# STRATEGY TYPES
# =============================================================================

class SharkStrategy(Enum):
    """Available Shark strategies"""
    TULIP_ARBITRAGE = "tulip_arbitrage"       # Illiquid market near expiry
    INFORMATION_EDGE = "information_edge"     # Intel market advantage
    NARRATIVE_FADE = "narrative_fade"         # Bet against hype
    SMART_MONEY_FOLLOW = "smart_money_follow" # Follow high-rep agents
    EXPIRY_SQUEEZE = "expiry_squeeze"         # Squeeze positions at expiry
    LIQUIDITY_PROVISION = "liquidity_provide" # Market making for fees


# =============================================================================
# MARKET STATE MODEL
# =============================================================================

@dataclass
class MarketState:
    """Represents current state of a prediction market"""
    market_id: str
    question: str
    
    # Pricing
    yes_price: float              # 0-1, price of YES shares
    no_price: float               # 0-1, price of NO shares
    
    # Liquidity
    total_volume: float           # Total USDC traded
    current_liquidity: float      # Available liquidity in pool
    order_book_depth: float       # How much can be traded at current price
    
    # Time
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    # Participants
    unique_traders: int = 0
    whale_positions: Dict[str, float] = field(default_factory=dict)
    
    # Recent activity
    last_trade_time: Optional[datetime] = None
    price_24h_change: float = 0.0
    volume_24h: float = 0.0
    
    @property
    def time_to_expiry(self) -> Optional[timedelta]:
        """Time remaining until market expires"""
        if not self.expires_at:
            return None
        return self.expires_at - datetime.now(timezone.utc)
    
    @property
    def hours_to_expiry(self) -> Optional[float]:
        """Hours until expiry"""
        ttl = self.time_to_expiry
        if not ttl:
            return None
        return ttl.total_seconds() / 3600
    
    @property
    def is_illiquid(self) -> bool:
        """Is this market illiquid? (<$5,000 liquidity)"""
        return self.current_liquidity < 5000
    
    @property
    def implied_probability(self) -> float:
        """Market-implied probability (YES price)"""
        return self.yes_price
    
    @property
    def spread(self) -> float:
        """Bid-ask spread"""
        return abs(1.0 - self.yes_price - self.no_price)


# =============================================================================
# TULIP STRATEGY (The Crown Jewel)
# =============================================================================

@dataclass
class TulipOpportunity:
    """An arbitrage opportunity identified by the Tulip Strategy"""
    market_id: str
    market_question: str
    
    # Pricing analysis
    book_odds: float              # What the market says
    true_odds: float              # What we calculate
    edge: float                   # Our advantage
    
    # Market conditions
    liquidity: float
    hours_to_expiry: float
    
    # Trade recommendation
    recommended_side: str         # "YES" or "NO"
    recommended_size: float       # USDC to bet
    expected_return: float        # Expected profit
    confidence: float             # How confident we are
    
    # Risk
    max_slippage: float           # Expected price impact
    risk_score: float             # 0-1, higher = riskier


class TulipStrategy:
    """
    The Tulip King Strategy
    
    Hunts for illiquid markets near expiry where "Degen" agents
    have mispriced risk. Calculates true odds vs book odds and
    arbitrages the difference.
    
    Trigger Conditions:
    - Market Liquidity < $5,000
    - Time to Expiry < 24 hours
    - Edge > 5% (true odds vs book odds)
    
    This is REAL alpha that professional traders use.
    """
    
    def __init__(
        self,
        min_edge: float = 0.05,           # Minimum 5% edge to trade
        max_position_pct: float = 0.1,    # Max 10% of liquidity
        liquidity_threshold: float = 5000, # $5,000 max liquidity
        expiry_threshold_hours: float = 24, # 24 hours to expiry
    ):
        self.min_edge = min_edge
        self.max_position_pct = max_position_pct
        self.liquidity_threshold = liquidity_threshold
        self.expiry_threshold_hours = expiry_threshold_hours
        
        # Track our bets for P&L
        self.active_positions: Dict[str, Dict] = {}
        self.closed_positions: List[Dict] = []
        self.total_pnl: float = 0.0
    
    def scan_for_opportunities(
        self,
        markets: List[MarketState],
        external_signals: Optional[Dict[str, float]] = None,
    ) -> List[TulipOpportunity]:
        """
        Scan markets for Tulip opportunities.
        
        Args:
            markets: List of market states to analyze
            external_signals: Optional dict of market_id -> true_probability
                             (from intel market, news analysis, etc.)
        
        Returns:
            List of identified opportunities, sorted by expected return
        """
        opportunities = []
        
        for market in markets:
            opportunity = self._analyze_market(market, external_signals)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by expected return (best first)
        opportunities.sort(key=lambda x: x.expected_return, reverse=True)
        
        return opportunities
    
    def _analyze_market(
        self,
        market: MarketState,
        external_signals: Optional[Dict[str, float]] = None,
    ) -> Optional[TulipOpportunity]:
        """Analyze a single market for Tulip opportunity"""
        
        # Check trigger conditions
        if not self._meets_trigger_conditions(market):
            return None
        
        # Calculate true odds
        true_odds = self._calculate_true_odds(market, external_signals)
        book_odds = market.implied_probability
        
        # Calculate edge
        edge = abs(true_odds - book_odds)
        
        if edge < self.min_edge:
            return None
        
        # Determine trade direction
        if true_odds > book_odds:
            # Market underpricing YES - buy YES
            recommended_side = "YES"
            expected_payout = true_odds / book_odds
        else:
            # Market overpricing YES - buy NO
            recommended_side = "NO"
            expected_payout = (1 - true_odds) / (1 - book_odds)
        
        # Calculate position size (Kelly-inspired but conservative)
        kelly_fraction = (expected_payout - 1) / (expected_payout - 1 + 1)
        conservative_kelly = kelly_fraction * 0.25  # Quarter Kelly
        
        max_size = market.current_liquidity * self.max_position_pct
        recommended_size = min(max_size, market.current_liquidity * conservative_kelly)
        recommended_size = max(10, recommended_size)  # Minimum $10
        
        # Calculate expected return
        if recommended_side == "YES":
            win_prob = true_odds
            payout_if_win = recommended_size / book_odds
        else:
            win_prob = 1 - true_odds
            payout_if_win = recommended_size / (1 - book_odds)
        
        expected_return = (win_prob * payout_if_win) - recommended_size
        
        # Calculate slippage (larger orders = more slippage)
        slippage_factor = recommended_size / market.order_book_depth if market.order_book_depth > 0 else 0.5
        max_slippage = min(0.15, slippage_factor * 0.1)  # Cap at 15%
        
        # Risk score
        risk_score = self._calculate_risk_score(market, edge, recommended_size)
        
        return TulipOpportunity(
            market_id=market.market_id,
            market_question=market.question,
            book_odds=book_odds,
            true_odds=true_odds,
            edge=edge,
            liquidity=market.current_liquidity,
            hours_to_expiry=market.hours_to_expiry or 0,
            recommended_side=recommended_side,
            recommended_size=round(recommended_size, 2),
            expected_return=round(expected_return, 2),
            confidence=1 - risk_score,
            max_slippage=round(max_slippage, 3),
            risk_score=risk_score,
        )
    
    def _meets_trigger_conditions(self, market: MarketState) -> bool:
        """Check if market meets Tulip trigger conditions"""
        
        # Condition 1: Liquidity < threshold
        if market.current_liquidity >= self.liquidity_threshold:
            return False
        
        # Condition 2: Time to expiry < threshold
        hours = market.hours_to_expiry
        if hours is None or hours >= self.expiry_threshold_hours:
            return False
        
        # Condition 3: Market must have some activity
        if market.unique_traders < 3:
            return False
        
        # Condition 4: Reasonable spread
        if market.spread > 0.15:  # Skip markets with >15% spread
            return False
        
        return True
    
    def _calculate_true_odds(
        self,
        market: MarketState,
        external_signals: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate our estimate of true probability.
        
        This is where the REAL alpha comes from:
        - Intel market signals
        - News sentiment
        - Whale position analysis
        - Time decay modeling
        - Reversion to mean
        """
        
        # Start with market price as base
        base_prob = market.implied_probability
        
        # 1. External signal (strongest signal - from Intel Market)
        if external_signals and market.market_id in external_signals:
            intel_prob = external_signals[market.market_id]
            # Weight intel heavily (0.6) vs market (0.4)
            base_prob = intel_prob * 0.6 + base_prob * 0.4
        
        # 2. Whale analysis
        whale_adjustment = self._analyze_whale_positions(market)
        base_prob += whale_adjustment
        
        # 3. Time decay (markets tend toward extremes near expiry)
        time_adjustment = self._time_decay_adjustment(market)
        base_prob += time_adjustment
        
        # 4. Mean reversion (extreme prices revert)
        if base_prob < 0.1 or base_prob > 0.9:
            reversion_strength = 0.02
            if base_prob < 0.1:
                base_prob += reversion_strength
            else:
                base_prob -= reversion_strength
        
        # 5. Illiquidity premium (illiquid markets are less efficient)
        if market.is_illiquid:
            # Add noise - degen traders make mistakes
            noise = random.gauss(0, 0.03)  # 3% standard deviation
            base_prob += noise
        
        # Clamp to valid range
        return max(0.01, min(0.99, base_prob))
    
    def _analyze_whale_positions(self, market: MarketState) -> float:
        """
        Analyze whale positions for signal.
        Smart money tends to be right.
        """
        if not market.whale_positions:
            return 0.0
        
        # Calculate net whale position
        total_whale_yes = sum(
            pos for agent, pos in market.whale_positions.items() 
            if pos > 0
        )
        total_whale_no = sum(
            abs(pos) for agent, pos in market.whale_positions.items() 
            if pos < 0
        )
        
        total = total_whale_yes + total_whale_no
        if total == 0:
            return 0.0
        
        # If whales are net YES, adjust probability up
        whale_sentiment = (total_whale_yes - total_whale_no) / total
        
        # Small adjustment based on whale sentiment
        return whale_sentiment * 0.03  # Max 3% adjustment
    
    def _time_decay_adjustment(self, market: MarketState) -> float:
        """
        Near expiry, markets resolve to 0 or 1.
        Adjust probability based on momentum.
        """
        hours = market.hours_to_expiry
        if hours is None or hours > 24:
            return 0.0
        
        # Stronger adjustment as expiry approaches
        time_factor = 1 - (hours / 24)  # 0 at 24h, 1 at 0h
        
        # Use recent price change as momentum signal
        momentum = market.price_24h_change
        
        # Adjust toward extremes based on momentum
        adjustment = momentum * time_factor * 0.05
        
        return adjustment
    
    def _calculate_risk_score(
        self,
        market: MarketState,
        edge: float,
        position_size: float
    ) -> float:
        """Calculate risk score for the trade"""
        
        risk = 0.0
        
        # Low liquidity = higher risk
        liquidity_risk = 1 - (market.current_liquidity / self.liquidity_threshold)
        risk += liquidity_risk * 0.3
        
        # Position size relative to liquidity
        size_risk = position_size / market.current_liquidity
        risk += size_risk * 0.3
        
        # Time to expiry (less time = more risk of being wrong)
        hours = market.hours_to_expiry or 24
        time_risk = 1 - (hours / 24)
        risk += time_risk * 0.2
        
        # Edge confidence (smaller edge = less confident)
        edge_risk = 1 - min(1, edge / 0.15)  # Full confidence at 15% edge
        risk += edge_risk * 0.2
        
        return min(1.0, risk)
    
    def execute_opportunity(
        self,
        opportunity: TulipOpportunity,
        agent_id: str,
        available_capital: float,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a Tulip opportunity.
        
        Returns (success, details)
        """
        # Check capital
        if available_capital < opportunity.recommended_size:
            return False, {"error": "Insufficient capital"}
        
        # Check risk limits
        if opportunity.risk_score > 0.7:
            return False, {"error": "Risk too high", "risk_score": opportunity.risk_score}
        
        # Record position
        position = {
            "market_id": opportunity.market_id,
            "agent_id": agent_id,
            "side": opportunity.recommended_side,
            "size": opportunity.recommended_size,
            "entry_price": opportunity.book_odds if opportunity.recommended_side == "YES" else 1 - opportunity.book_odds,
            "true_odds": opportunity.true_odds,
            "edge": opportunity.edge,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "open",
        }
        
        self.active_positions[opportunity.market_id] = position
        
        return True, {
            "success": True,
            "position": position,
            "expected_return": opportunity.expected_return,
            "message": f"Tulip arb: {opportunity.recommended_side} @ {opportunity.book_odds:.1%} "
                      f"(true: {opportunity.true_odds:.1%}, edge: {opportunity.edge:.1%})"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        return {
            "strategy": "tulip_arbitrage",
            "active_positions": len(self.active_positions),
            "closed_positions": len(self.closed_positions),
            "total_pnl": self.total_pnl,
            "win_rate": self._calculate_win_rate(),
            "avg_edge": self._calculate_avg_edge(),
        }
    
    def _calculate_win_rate(self) -> float:
        if not self.closed_positions:
            return 0.0
        wins = len([p for p in self.closed_positions if p.get("pnl", 0) > 0])
        return wins / len(self.closed_positions)
    
    def _calculate_avg_edge(self) -> float:
        if not self.closed_positions:
            return 0.0
        edges = [p.get("edge", 0) for p in self.closed_positions]
        return sum(edges) / len(edges)


# =============================================================================
# SHARK AGENT GENOME INTEGRATION
# =============================================================================

@dataclass
class SharkGenome:
    """
    Genetic configuration for a Shark agent.
    Controls which strategies they use and how aggressively.
    """
    agent_id: str
    
    # Strategy weights (which strategies to use)
    tulip_weight: float = 0.8          # Highly favor Tulip strategy
    info_edge_weight: float = 0.6
    narrative_fade_weight: float = 0.4
    smart_money_weight: float = 0.3
    
    # Risk parameters
    max_position_size: float = 500.0   # Max single position
    max_portfolio_risk: float = 0.3    # Max 30% of capital at risk
    min_edge_threshold: float = 0.05   # Only trade with 5%+ edge
    
    # Tulip-specific parameters
    tulip_liquidity_max: float = 5000  # Only hunt <$5k markets
    tulip_expiry_max_hours: float = 24 # Only near-expiry
    tulip_aggressive: bool = True      # Aggressive vs conservative execution
    
    # Behavioral traits
    patience: float = 0.7              # Wait for good setups
    contrarian: float = 0.5            # Bet against crowd
    intel_utilization: float = 0.9     # Use Intel Market info
    
    def get_active_strategies(self) -> List[SharkStrategy]:
        """Get list of strategies this shark uses"""
        strategies = []
        
        if self.tulip_weight > 0.3:
            strategies.append(SharkStrategy.TULIP_ARBITRAGE)
        if self.info_edge_weight > 0.3:
            strategies.append(SharkStrategy.INFORMATION_EDGE)
        if self.narrative_fade_weight > 0.3:
            strategies.append(SharkStrategy.NARRATIVE_FADE)
        if self.smart_money_weight > 0.3:
            strategies.append(SharkStrategy.SMART_MONEY_FOLLOW)
        
        return strategies


class SharkBrain:
    """
    Decision-making brain for Shark agents.
    Integrates multiple strategies including Tulip.
    """
    
    def __init__(self, genome: SharkGenome):
        self.genome = genome
        self.tulip = TulipStrategy(
            min_edge=genome.min_edge_threshold,
            max_position_pct=0.1 if not genome.tulip_aggressive else 0.2,
            liquidity_threshold=genome.tulip_liquidity_max,
            expiry_threshold_hours=genome.tulip_expiry_max_hours,
        )
        self.capital = 10000.0  # Starting capital
        self.positions: Dict[str, Dict] = {}
    
    def analyze_markets(
        self,
        markets: List[MarketState],
        intel_signals: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyze all markets and return recommended actions.
        """
        actions = []
        
        # 1. Tulip Strategy (highest priority for Sharks)
        if SharkStrategy.TULIP_ARBITRAGE in self.genome.get_active_strategies():
            tulip_opportunities = self.tulip.scan_for_opportunities(
                markets, intel_signals
            )
            
            for opp in tulip_opportunities[:3]:  # Max 3 Tulip trades
                if opp.expected_return > 0:
                    actions.append({
                        "strategy": "tulip_arbitrage",
                        "market_id": opp.market_id,
                        "action": "BET",
                        "side": opp.recommended_side,
                        "size": opp.recommended_size,
                        "edge": opp.edge,
                        "confidence": opp.confidence,
                        "reasoning": f"Illiquid market ({opp.liquidity:.0f} USDC), "
                                   f"{opp.hours_to_expiry:.1f}h to expiry, "
                                   f"{opp.edge:.1%} edge identified",
                    })
        
        # 2. Other strategies would go here...
        
        # Sort by expected value
        actions.sort(key=lambda x: x.get("edge", 0) * x.get("confidence", 0), reverse=True)
        
        return actions
    
    def should_buy_intel(
        self,
        intel_price: float,
        market_exposure: float,
    ) -> bool:
        """Decide whether to buy intel from Intel Market"""
        
        # Sharks highly value information
        if self.genome.intel_utilization < 0.5:
            return False
        
        # Worth it if exposure is high enough
        potential_edge_value = market_exposure * 0.1  # Assume 10% edge from intel
        
        return potential_edge_value > intel_price * 2  # 2x expected return minimum


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def demo_tulip_strategy():
    """Demonstrate the Tulip Strategy"""
    
    print("=" * 60)
    print("🌷 TULIP STRATEGY DEMO")
    print("=" * 60)
    
    # Create some test markets
    markets = [
        MarketState(
            market_id="market-001",
            question="Will Taiwan crisis escalate this week?",
            yes_price=0.35,
            no_price=0.68,
            total_volume=8500,
            current_liquidity=3200,  # ILLIQUID ✓
            order_book_depth=1000,
            unique_traders=15,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=8),  # <24h ✓
            price_24h_change=0.05,
        ),
        MarketState(
            market_id="market-002",
            question="Will Fed raise rates in December?",
            yes_price=0.72,
            no_price=0.30,
            total_volume=150000,
            current_liquidity=45000,  # LIQUID - skip
            order_book_depth=15000,
            unique_traders=89,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=120),
        ),
        MarketState(
            market_id="market-003",
            question="Will mystery assassin be identified?",
            yes_price=0.15,
            no_price=0.88,
            total_volume=2100,
            current_liquidity=1800,  # VERY ILLIQUID ✓
            order_book_depth=500,
            unique_traders=8,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),  # EXPIRING ✓
            price_24h_change=-0.08,
        ),
    ]
    
    # Initialize strategy
    tulip = TulipStrategy(min_edge=0.05)
    
    # Simulate having intel from the Intel Market
    intel_signals = {
        "market-001": 0.55,  # Intel says TRUE prob is 55%, market says 35%
        "market-003": 0.25,  # Intel says TRUE prob is 25%, market says 15%
    }
    
    # Scan for opportunities
    opportunities = tulip.scan_for_opportunities(markets, intel_signals)
    
    print(f"\n📊 Scanned {len(markets)} markets")
    print(f"🎯 Found {len(opportunities)} opportunities\n")
    
    for opp in opportunities:
        print(f"Market: {opp.market_question[:50]}...")
        print(f"  📈 Book Odds: {opp.book_odds:.1%}")
        print(f"  🎯 True Odds: {opp.true_odds:.1%}")
        print(f"  ⚡ Edge: {opp.edge:.1%}")
        print(f"  💰 Liquidity: ${opp.liquidity:,.0f}")
        print(f"  ⏰ Expires in: {opp.hours_to_expiry:.1f}h")
        print(f"  🎲 Recommendation: BET {opp.recommended_side} ${opp.recommended_size:.2f}")
        print(f"  💵 Expected Return: ${opp.expected_return:.2f}")
        print(f"  🛡️ Confidence: {opp.confidence:.0%}")
        print()


if __name__ == "__main__":
    demo_tulip_strategy()

