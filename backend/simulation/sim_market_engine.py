"""
Enhanced Market Simulation Engine for Project Seed
===================================================
A "Living Engine" market simulation using the Universal Agent Schema.

Features:
- Full FinancialAgent archetype system (Whale, Shark, Degen, Value, Momentum, Noise)
- Multiple assets (stocks, crypto)
- Provably fair via seed-based determinism
- Rich event generation for betting opportunities
- Tick-based persistence support
- Detailed simulation logs for transparency

Usage:
    python sim_market_engine.py <server_seed> <client_seed> <nonce>

    # Or with options:
    python sim_market_engine.py <server_seed> <client_seed> <nonce> --ticks 100 --verbose
"""

import sys
import os
import hashlib
import random
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.schemas import (
    FinancialAgent,
    FinancialArchetype,
    create_random_financial_agent,
    AgentStatus
)

# Use the new Multi-Provider Brain
try:
    from backend.agents.multi_brain import AgentBrain, BrainConfig
except ImportError:
    from agents.multi_brain import AgentBrain, BrainConfig

import asyncio


# =============================================================================
# CONFIGURATION
# =============================================================================

class MarketConfig:
    """Simulation parameters - tweak these to balance the game."""

    # Population mix (should sum to 1.0)
    ARCHETYPE_DISTRIBUTION = {
        FinancialArchetype.WHALE: 0.05,      # 5% - Big money, moves markets
        FinancialArchetype.SHARK: 0.10,      # 10% - Smart money
        FinancialArchetype.VALUE: 0.15,      # 15% - Patient buyers
        FinancialArchetype.MOMENTUM: 0.20,   # 20% - Trend followers
        FinancialArchetype.DEGEN: 0.30,      # 30% - Retail/news followers
        FinancialArchetype.NOISE: 0.20,      # 20% - Random chaos
    }

    # Market mechanics
    TOTAL_AGENTS = 100
    DEFAULT_TICKS = 100
    PRICE_IMPACT_DIVISOR = 500  # Higher = less volatile (was 50)
    BASE_VOLATILITY = 0.002    # Random noise per tick (was 0.005)

    # Whale impact multiplier (their trades move markets more)
    WHALE_IMPACT = 5   # (was 10)
    SHARK_IMPACT = 2   # (was 3)


# =============================================================================
# MARKET STRUCTURES
# =============================================================================

class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    COMMODITY = "commodity"


@dataclass
class Asset:
    """Represents a tradeable asset in the simulation."""

    symbol: str
    name: str
    asset_type: AssetType
    price: float
    price_history: List[float] = field(default_factory=list)
    volume_history: List[int] = field(default_factory=list)

    # Derived metrics (updated each tick)
    high_24h: float = 0.0
    low_24h: float = 0.0

    def __post_init__(self):
        if not self.price_history:
            self.price_history = [self.price]
        self.high_24h = self.price
        self.low_24h = self.price

    @property
    def change_pct(self) -> float:
        """Percentage change from start."""
        if len(self.price_history) < 2:
            return 0.0
        return (self.price - self.price_history[0]) / self.price_history[0]

    @property
    def trend(self) -> float:
        """Recent trend: positive = up, negative = down."""
        if len(self.price_history) < 3:
            return 0.0
        recent = self.price_history[-3:]
        return (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0

    @property
    def volatility(self) -> float:
        """Recent price volatility."""
        if len(self.price_history) < 5:
            return 0.0
        recent = self.price_history[-5:]
        avg = sum(recent) / len(recent)
        variance = sum((p - avg) ** 2 for p in recent) / len(recent)
        return (variance ** 0.5) / avg if avg > 0 else 0

    def update_price(self, buy_pressure: float, sell_pressure: float,
                     base_volatility: float = 0.002) -> float:
        """
        Update price based on order flow.
        Returns the price change percentage.
        """
        # Net pressure (normalized)
        net_pressure = (buy_pressure - sell_pressure) / MarketConfig.PRICE_IMPACT_DIVISOR

        # Add random volatility (seeded)
        noise = random.uniform(-base_volatility, base_volatility)

        # Crypto is more volatile
        if self.asset_type == AssetType.CRYPTO:
            noise *= 1.5
            net_pressure *= 1.2

        # Mean reversion: prices tend to drift back toward start
        # This prevents runaway trends
        if len(self.price_history) > 0:
            start_price = self.price_history[0]
            deviation = (self.price - start_price) / start_price
            mean_reversion = -deviation * 0.01  # 1% pull back toward start
            net_pressure += mean_reversion

        # Calculate change
        price_change_pct = net_pressure + noise

        # Cap maximum single-tick move at 5%
        price_change_pct = max(-0.05, min(0.05, price_change_pct))

        new_price = self.price * (1 + price_change_pct)

        # Floor at $0.01
        new_price = max(0.01, new_price)

        # Update state
        old_price = self.price
        self.price = new_price
        self.price_history.append(new_price)
        self.volume_history.append(int(buy_pressure + sell_pressure))

        # Update high/low
        self.high_24h = max(self.high_24h, new_price)
        self.low_24h = min(self.low_24h, new_price)

        return (new_price - old_price) / old_price if old_price > 0 else 0


@dataclass
class NewsEvent:
    """A market-moving news event."""

    headline: str
    sentiment: float  # -1.0 to +1.0
    affected_assets: List[str]  # Asset symbols
    magnitude: float = 1.0  # Impact multiplier

    def to_dict(self) -> Dict:
        return {
            "headline": self.headline,
            "sentiment": self.sentiment,
            "affected": self.affected_assets,
            "magnitude": self.magnitude
        }


@dataclass
class MarketEvent:
    """A logged event for betting/transparency."""

    tick: int
    event_type: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "tick": self.tick,
            "type": self.event_type,
            "description": self.description,
            "data": self.data
        }


# =============================================================================
# NEWS GENERATION
# =============================================================================

def generate_news_queue(assets: List[Asset], num_ticks: int) -> List[Optional[NewsEvent]]:
    """
    Generate a deterministic queue of news events.
    Most ticks have no news; occasional events move markets.
    """

    # News templates
    positive_news = [
        ("🚀 {symbol} announces record quarterly earnings!", 0.7),
        ("📈 Analysts upgrade {symbol} to 'Strong Buy'", 0.5),
        ("💰 {symbol} announces surprise dividend", 0.4),
        ("🤝 {symbol} announces major partnership", 0.6),
        ("📊 {symbol} beats revenue expectations by 20%", 0.65),
        ("🌟 {symbol} product wins industry award", 0.3),
    ]

    negative_news = [
        ("📉 {symbol} misses earnings estimates", -0.6),
        ("⚠️ {symbol} faces regulatory investigation", -0.7),
        ("🔴 {symbol} CEO resigns unexpectedly", -0.8),
        ("💔 {symbol} loses major contract", -0.5),
        ("📰 Short seller releases damaging report on {symbol}", -0.6),
        ("⬇️ Analysts downgrade {symbol} to 'Sell'", -0.4),
    ]

    macro_news = [
        ("🏦 Fed signals interest rate hike", -0.3),
        ("🏦 Fed hints at rate cuts", 0.4),
        ("📊 Jobs report beats expectations", 0.3),
        ("📉 Inflation data worse than expected", -0.4),
        ("🌍 Geopolitical tensions escalate", -0.5),
        ("✅ Trade deal announced", 0.5),
    ]

    queue: List[Optional[NewsEvent]] = [None] * num_ticks

    # Distribute news events (roughly 15-20% of ticks have news)
    num_events = int(num_ticks * random.uniform(0.15, 0.25))
    event_ticks = random.sample(range(num_ticks), num_events)

    for tick in event_ticks:
        # 60% asset-specific, 40% macro
        if random.random() < 0.6:
            asset = random.choice(assets)
            if random.random() < 0.5:
                template, sentiment = random.choice(positive_news)
            else:
                template, sentiment = random.choice(negative_news)

            headline = template.format(symbol=asset.symbol)
            queue[tick] = NewsEvent(
                headline=headline,
                sentiment=sentiment,
                affected_assets=[asset.symbol],
                magnitude=random.uniform(0.8, 1.5)
            )
        else:
            template, sentiment = random.choice(macro_news)
            queue[tick] = NewsEvent(
                headline=template,
                sentiment=sentiment,
                affected_assets=[a.symbol for a in assets],  # Affects all
                magnitude=random.uniform(0.5, 1.0)
            )

    return queue


# =============================================================================
# MARKET SIMULATION ENGINE
# =============================================================================

class MarketSimulation:
    """
    The Living Engine for market simulation.

    Provably fair: All randomness is seeded from the game hash.
    """

    def __init__(self, game_hash: str, config: MarketConfig = MarketConfig()):
        self.game_hash = game_hash
        self.config = config

        # Seed all randomness
        random.seed(game_hash)

        # State
        self.tick = 0
        self.assets: Dict[str, Asset] = {}
        self.agents: List[FinancialAgent] = []
        self.news_queue: List[Optional[NewsEvent]] = []
        self.event_log: List[MarketEvent] = []

        # Derived from hash for provable fairness
        hash_int = int(game_hash, 16)
        self.market_mood = (hash_int % 100) / 100  # 0-1, affects overall sentiment
        
        # Initialize Multi-Brain (10% chance of using LLM/Ollama)
        self.brain = AgentBrain(BrainConfig(llm_probability=0.1))

    def initialize(self, assets: Optional[List[Dict]] = None):
        """Set up initial market state."""

        # Default assets if none provided
        if assets is None:
            assets = [
                {"symbol": "SAPL", "name": "Sim-Apple", "type": AssetType.STOCK, "price": 150.0},
                {"symbol": "STSLA", "name": "Sim-Tesla", "type": AssetType.STOCK, "price": 250.0},
                {"symbol": "SBTC", "name": "Sim-Bitcoin", "type": AssetType.CRYPTO, "price": 45000.0},
                {"symbol": "SETH", "name": "Sim-Ethereum", "type": AssetType.CRYPTO, "price": 3000.0},
            ]

        # Create assets
        for a in assets:
            asset = Asset(
                symbol=a["symbol"],
                name=a["name"],
                asset_type=a.get("type", AssetType.STOCK),
                price=a["price"]
            )
            self.assets[asset.symbol] = asset

        # Create agent population based on distribution
        for archetype, ratio in self.config.ARCHETYPE_DISTRIBUTION.items():
            count = int(self.config.TOTAL_AGENTS * ratio)
            for _ in range(count):
                agent = create_random_financial_agent(archetype)

                # Whales get more money
                if archetype == FinancialArchetype.WHALE:
                    agent.bankroll *= 100
                elif archetype == FinancialArchetype.SHARK:
                    agent.bankroll *= 10

                self.agents.append(agent)

        # Generate news queue
        self.news_queue = generate_news_queue(
            list(self.assets.values()),
            self.config.DEFAULT_TICKS
        )

        # Log initialization
        self._log_event("INIT", "Market initialized", {
            "assets": [a.symbol for a in self.assets.values()],
            "agents": len(self.agents),
            "market_mood": f"{self.market_mood:.0%}"
        })

    def _log_event(self, event_type: str, description: str, data: Dict = None):
        """Add event to log."""
        self.event_log.append(MarketEvent(
            tick=self.tick,
            event_type=event_type,
            description=description,
            data=data or {}
        ))

    def _calculate_agent_impact(self, agent: FinancialAgent) -> float:
        """Determine how much this agent's trades move the market."""
        if agent.archetype == FinancialArchetype.WHALE:
            return self.config.WHALE_IMPACT
        elif agent.archetype == FinancialArchetype.SHARK:
            return self.config.SHARK_IMPACT
        return 1.0

    def run_tick(self) -> Dict[str, Any]:
        """
        Execute one market tick.
        Returns summary of what happened.
        """
        tick_summary = {
            "tick": self.tick,
            "news": None,
            "price_changes": {},
            "notable_trades": [],
            "market_events": [],
            "social_feed": []  # NEW: Agent social posts from LLM decisions
        }

        # Get news for this tick
        news = self.news_queue[self.tick] if self.tick < len(self.news_queue) else None
        if news:
            tick_summary["news"] = news.to_dict()
            self._log_event("NEWS", news.headline, news.to_dict())

        # Calculate sentiment for each asset
        asset_sentiment = {}
        for symbol, asset in self.assets.items():
            base_sentiment = self.market_mood - 0.5  # -0.5 to +0.5

            if news and symbol in news.affected_assets:
                base_sentiment += news.sentiment * news.magnitude

            asset_sentiment[symbol] = max(-1, min(1, base_sentiment))

        # Each asset gets traded
        for symbol, asset in self.assets.items():
            buy_pressure = 0.0
            sell_pressure = 0.0

            sentiment = asset_sentiment[symbol]
            trend = asset.trend

            # Each agent decides using BRAIN
            for agent in self.agents:
                if agent.status != AgentStatus.ACTIVE:
                    continue

                # 1. Gather Context for the Brain
                market_context = {
                    "sentiment": sentiment,
                    "trend": trend,
                    "price": asset.price
                }
                
                # 2. ASK THE BRAIN (Hybrid Decision: Rules vs. Ollama vs. Groq)
                # This replaces agent.decide_action()
                # Now the brain decides the action AND the reasoning!
                try:
                    # Run async brain in sync context
                    # asyncio.run() creates a new event loop, safe for sync methods
                    decision = asyncio.run(
                        self.brain.decide(
                            agent_id=agent.id, 
                            archetype=agent.archetype.value, 
                            market_data=market_context
                        )
                    )
                except RuntimeError as e:
                    # If there's already a running event loop, use rule-based fallback
                    if "asyncio.run() cannot be called" in str(e):
                        from backend.agents.multi_brain import RuleBasedBrain
                        rule_brain = RuleBasedBrain()
                        # Use sync wrapper - create a new event loop in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                rule_brain.decide({**market_context, "archetype": agent.archetype.value})
                            )
                            decision = future.result(timeout=1)
                    else:
                        raise
                except Exception as e:
                    print(f"⚠️ Brain error for {agent.id}: {e}")
                    # Fallback to simple rule
                    decision = type('Decision', (), {
                        'action': 'HOLD',
                        'reasoning': 'Brain error',
                        'provider_used': 'error'
                    })()
                
                action = decision.action
                impact = self._calculate_agent_impact(agent)
                trade_happened = False

                # 3. Execute Logic (Same as before)
                if action == "BUY":
                    if agent.execute_trade("BUY", symbol, asset.price, quantity=1):
                        buy_pressure += impact
                        trade_happened = True

                        # Log notable trades (whales, sharks)
                        if impact > 1:
                            tick_summary["notable_trades"].append({
                                "agent": agent.archetype.value,
                                "action": "BUY",
                                "asset": symbol,
                                "price": asset.price
                            })

                elif action == "SELL":
                    if agent.execute_trade("SELL", symbol, asset.price, quantity=1):
                        sell_pressure += impact
                        trade_happened = True

                        if impact > 1:
                            tick_summary["notable_trades"].append({
                                "agent": agent.archetype.value,
                                "action": "SELL",
                                "asset": symbol,
                                "price": asset.price
                            })
                
                # 4. Social Feed (Using the reasoning we just got for free!)
                # If the brain used an LLM (Ollama/Groq), the reasoning is high-quality.
                # We post it to the feed.
                if trade_happened and decision.provider_used != "rule_based":
                    social_post = {
                        "agent": agent.name,
                        "archetype": agent.archetype.value,
                        "message": decision.reasoning,  # "Buying the dip because..."
                        "provider": decision.provider_used  # e.g. "ollama"
                    }
                    tick_summary["social_feed"].append(social_post)
                    self._log_event("SOCIAL", f"{agent.name}: {decision.reasoning}", social_post)

            # Update price
            old_price = asset.price
            change_pct = asset.update_price(buy_pressure, sell_pressure)
            tick_summary["price_changes"][symbol] = {
                "old": round(old_price, 2),
                "new": round(asset.price, 2),
                "change_pct": round(change_pct * 100, 2),
                "buy_pressure": buy_pressure,
                "sell_pressure": sell_pressure
            }

            # Detect significant events
            if abs(change_pct) > 0.03:  # 3% move
                event_type = "PUMP" if change_pct > 0 else "DUMP"
                self._log_event(
                    event_type,
                    f"{symbol} moves {change_pct*100:+.1f}%",
                    {"symbol": symbol, "change": change_pct}
                )
                tick_summary["market_events"].append(f"{symbol} {event_type}")

            # Detect new highs/lows
            if asset.price >= asset.high_24h:
                self._log_event("NEW_HIGH", f"{symbol} hits new high: ${asset.price:.2f}")
                tick_summary["market_events"].append(f"{symbol} NEW HIGH")
            elif asset.price <= asset.low_24h:
                self._log_event("NEW_LOW", f"{symbol} hits new low: ${asset.price:.2f}")
                tick_summary["market_events"].append(f"{symbol} NEW LOW")

        self.tick += 1
        return tick_summary

    def run_full_simulation(self, num_ticks: int = None) -> Dict[str, Any]:
        """
        Run the complete simulation.
        Returns final results for bet settlement.
        """
        if num_ticks is None:
            num_ticks = self.config.DEFAULT_TICKS

        # Run all ticks
        for _ in range(num_ticks):
            self.run_tick()

        # Calculate final results
        results = {
            "ticks_run": self.tick,
            "assets": {},
            "outcomes": {},
            "agent_performance": self._calculate_agent_performance(),
            "notable_events": [e.to_dict() for e in self.event_log[-20:]]  # Last 20 events
        }

        for symbol, asset in self.assets.items():
            change_pct = asset.change_pct

            results["assets"][symbol] = {
                "start_price": asset.price_history[0],
                "end_price": asset.price,
                "change_pct": round(change_pct * 100, 2),
                "high": asset.high_24h,
                "low": asset.low_24h,
                "volatility": round(asset.volatility * 100, 2)
            }

            # Determine outcome for betting
            if change_pct > 0.05:
                results["outcomes"][symbol] = "UP"
            elif change_pct < -0.05:
                results["outcomes"][symbol] = "DOWN"
            else:
                results["outcomes"][symbol] = "FLAT"

        return results

    def _calculate_agent_performance(self) -> Dict[str, Any]:
        """Calculate how each archetype performed."""
        performance = {}

        for archetype in FinancialArchetype:
            agents_of_type = [a for a in self.agents if a.archetype == archetype]
            if not agents_of_type:
                continue

            # Calculate total portfolio value
            total_value = 0
            initial_value = 0

            for agent in agents_of_type:
                # Cash
                total_value += agent.bankroll

                # Positions at current prices
                for symbol, shares in agent.positions.items():
                    if symbol in self.assets:
                        total_value += shares * self.assets[symbol].price

                # Estimate initial value (rough - based on archetype)
                if archetype == FinancialArchetype.WHALE:
                    initial_value += 100000
                elif archetype == FinancialArchetype.SHARK:
                    initial_value += 10000
                else:
                    initial_value += 1000

            pnl = total_value - initial_value
            pnl_pct = (pnl / initial_value * 100) if initial_value > 0 else 0

            performance[archetype.value] = {
                "agents": len(agents_of_type),
                "total_value": round(total_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            }

        return performance

    def get_betting_outcome(self, asset_symbol: str = "SAPL") -> str:
        """
        Get the simple outcome string for legacy bet settlement.
        Compatible with existing main.py integration.
        """
        if asset_symbol not in self.assets:
            asset_symbol = list(self.assets.keys())[0]

        asset = self.assets[asset_symbol]
        change_pct = asset.change_pct

        if change_pct > 0.05:
            return f"{asset_symbol}_UP"
        elif change_pct < -0.05:
            return f"{asset_symbol}_DOWN"
        else:
            return f"{asset_symbol}_FLAT"


# =============================================================================
# PROVABLY FAIR SEED LOGIC
# =============================================================================

def get_provable_game_hash(server_seed: str, client_seed: str, nonce: str) -> str:
    """Generate deterministic hash from seeds."""
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    return hashlib.sha256(combined_string.encode()).hexdigest()


# =============================================================================
# CLI INTERFACE (Compatible with main.py)
# =============================================================================

def run_simulation(server_seed: str, client_seed: str, nonce: str,
                   verbose: bool = False) -> str:
    """
    Main entry point - compatible with existing main.py subprocess call.

    Returns simple outcome string for bet settlement.
    """
    # Generate provably fair hash
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)

    # Create and run simulation
    sim = MarketSimulation(game_hash)
    sim.initialize()
    results = sim.run_full_simulation()

    if verbose:
        print(json.dumps(results, indent=2))

    # Return primary outcome (SAPL for backwards compatibility)
    return sim.get_betting_outcome("SAPL")


if __name__ == "__main__":
    # Parse arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if len(args) < 3:
        print("Usage: python sim_market_engine.py <server_seed> <client_seed> <nonce> [--verbose]")
        print("\nExample:")
        print("  python sim_market_engine.py abc123 xyz789 1 --verbose")
        sys.exit(1)

    SERVER_SEED = args[0]
    CLIENT_SEED = args[1]
    NONCE = args[2]

    result = run_simulation(SERVER_SEED, CLIENT_SEED, NONCE, verbose=verbose)

    if not verbose:
        # Only print result for main.py compatibility
        print(result)
