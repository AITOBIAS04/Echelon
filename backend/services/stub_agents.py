"""Stub Agent Spawner — deterministic agent stubs for Theatre testing.

Creates a population of 6 agent stubs (one per archetype) with simple
deterministic strategies. Each stub calls TradingEngine.execute_trade()
directly — no agent runtime, no LLM, no autonomous decisions.

Throwaway code replaced by the agent runtime in Cycle-013.

Cycle-012, Sprint 1 — Theatre Creation + LMSR Wiring.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import MarketState
from backend.market.trading import Trade, TradingEngine


class AgentArchetype(str, Enum):
    """Agent archetype identifiers."""

    SHARK = "shark"
    SPY = "spy"
    DIPLOMAT = "diplomat"
    SABOTEUR = "saboteur"
    WHALE = "whale"
    DEGEN = "degen"


@dataclass
class TradeIntent:
    """An agent's intended trade before execution."""

    outcome_index: int
    shares: float
    trigger: str
    confidence: float


@dataclass
class TradeDecisionTrace:
    """Complete trace of an agent's trading decision for RLMF export."""

    agent_id: str
    archetype: str
    tick: int
    trigger_condition: str
    market_prices_at_decision: list[float]
    confidence: float
    intent: TradeIntent | None
    executed_trade: Trade | None
    pattern_name: str


@dataclass
class StubAgent:
    """A deterministic agent stub for Theatre testing.

    strategy is a callable: (market, prices, evidence, tick, rng) -> TradeIntent | None
    """

    agent_id: str
    archetype: AgentArchetype
    initial_balance: float
    strategy: Callable[..., TradeIntent | None]


class StubAgentSpawner:
    """Spawns and executes a population of stub agents for a Theatre."""

    DEFAULT_AGENT_COUNT = 6
    DEFAULT_INITIAL_BALANCE = 1000.0

    def spawn(
        self,
        theatre_id: str,
        agent_count: int | None = None,
        initial_balance: float | None = None,
    ) -> list[StubAgent]:
        """Spawn agent stubs — one per archetype with deterministic IDs.

        agent_id format: {theatre_id}_{archetype_value}
        """
        count = agent_count or self.DEFAULT_AGENT_COUNT
        balance = initial_balance or self.DEFAULT_INITIAL_BALANCE

        archetypes = list(AgentArchetype)[:count]
        agents: list[StubAgent] = []

        for archetype in archetypes:
            agent_id = f"{theatre_id}_{archetype.value}"
            strategy = self._get_strategy(archetype)
            agents.append(
                StubAgent(
                    agent_id=agent_id,
                    archetype=archetype,
                    initial_balance=balance,
                    strategy=strategy,
                )
            )

        return agents

    def execute_tick(
        self,
        agents: list[StubAgent],
        market: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        evidence: Any | None,
        tick: int,
        seed: int = 42,
    ) -> list[TradeDecisionTrace]:
        """Execute one tick for all agents.

        Each agent's strategy produces a TradeIntent (or None).
        Non-None intents are executed via TradingEngine.execute_trade().
        Returns a list of TradeDecisionTrace records for RLMF export.
        """
        rng = random.Random(seed + tick)
        prices = LMSREngine.prices(market.x, market.b)
        traces: list[TradeDecisionTrace] = []

        for agent in agents:
            intent = agent.strategy(market, prices, evidence, tick, rng)

            executed_trade: Trade | None = None
            if intent is not None:
                try:
                    executed_trade = trading_engine.execute_trade(
                        market=market,
                        agent_id=agent.agent_id,
                        outcome_index=intent.outcome_index,
                        shares=intent.shares,
                    )
                except Exception:
                    # Agent's trade failed — record the attempt but continue
                    pass

            traces.append(
                TradeDecisionTrace(
                    agent_id=agent.agent_id,
                    archetype=agent.archetype.value,
                    tick=tick,
                    trigger_condition=intent.trigger if intent else "no_action",
                    market_prices_at_decision=list(prices),
                    confidence=intent.confidence if intent else 0.0,
                    intent=intent,
                    executed_trade=executed_trade,
                    pattern_name=self._pattern_name(agent.archetype),
                )
            )

        return traces

    def _get_strategy(
        self, archetype: AgentArchetype
    ) -> Callable[..., TradeIntent | None]:
        """Return the deterministic strategy function for an archetype."""
        strategies = {
            AgentArchetype.SHARK: _shark_strategy,
            AgentArchetype.SPY: _spy_strategy,
            AgentArchetype.DIPLOMAT: _diplomat_strategy,
            AgentArchetype.SABOTEUR: _saboteur_strategy,
            AgentArchetype.WHALE: _whale_strategy,
            AgentArchetype.DEGEN: _degen_strategy,
        }
        return strategies[archetype]

    def _pattern_name(self, archetype: AgentArchetype) -> str:
        """Return the BEAUVOIR pattern name for an archetype."""
        patterns = {
            AgentArchetype.SHARK: "momentum_exploitation",
            AgentArchetype.SPY: "intel_arbitrage",
            AgentArchetype.DIPLOMAT: "stability_maintenance",
            AgentArchetype.SABOTEUR: "chaos_creation",
            AgentArchetype.WHALE: "market_moving",
            AgentArchetype.DEGEN: "volatility_harvesting",
        }
        return patterns[archetype]


# ===================================================================
# Strategy functions — one per archetype
# Each receives: (market, prices, evidence, tick, rng) -> TradeIntent | None
# ===================================================================


def _shark_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: momentum_exploitation — buy leading outcome if price < 0.7."""
    leading_idx = prices.index(max(prices))
    leading_price = prices[leading_idx]

    if leading_price < 0.7:
        shares = 10.0
        return TradeIntent(
            outcome_index=leading_idx,
            shares=shares,
            trigger=f"leading_price={leading_price:.3f}<0.7",
            confidence=0.8,
        )
    return None


def _spy_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: intel_arbitrage — trade only when evidence is provided."""
    if evidence is None:
        return None

    # When evidence arrives, buy the first outcome (simplistic stub)
    return TradeIntent(
        outcome_index=0,
        shares=5.0,
        trigger="evidence_arrived",
        confidence=0.6,
    )


def _diplomat_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: stability_maintenance — buy trailing outcome if spread > 0.4."""
    if len(prices) < 2:
        return None

    max_price = max(prices)
    min_price = min(prices)
    spread = max_price - min_price

    if spread > 0.4:
        trailing_idx = prices.index(min_price)
        return TradeIntent(
            outcome_index=trailing_idx,
            shares=8.0,
            trigger=f"spread={spread:.3f}>0.4",
            confidence=0.5,
        )
    return None


def _saboteur_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: chaos_creation — random contrary trades at low volume (1-3 shares)."""
    # Trade the opposite of the leading outcome
    leading_idx = prices.index(max(prices))
    # Pick a non-leading outcome
    other_indices = [i for i in range(len(prices)) if i != leading_idx]
    if not other_indices:
        return None

    contrary_idx = rng.choice(other_indices)
    shares = float(rng.randint(1, 3))

    return TradeIntent(
        outcome_index=contrary_idx,
        shares=shares,
        trigger=f"chaos_contrary_to_leading_{leading_idx}",
        confidence=0.3,
    )


def _whale_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: market_moving — single large position (50+ shares) on tick 0, hold."""
    if tick != 0:
        return None

    # Buy the first outcome with a large position
    return TradeIntent(
        outcome_index=0,
        shares=50.0,
        trigger="tick_0_large_position",
        confidence=0.9,
    )


def _degen_strategy(
    market: MarketState,
    prices: list[float],
    evidence: Any | None,
    tick: int,
    rng: random.Random,
) -> TradeIntent | None:
    """PATTERN: volatility_harvesting — random outcome, random volume (1-10), every tick."""
    outcome_index = rng.randint(0, len(prices) - 1)
    shares = float(rng.randint(1, 10))

    return TradeIntent(
        outcome_index=outcome_index,
        shares=shares,
        trigger=f"random_trade_tick_{tick}",
        confidence=0.2,
    )
