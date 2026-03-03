"""Tests for stub agent spawning, strategy correctness, and trade execution.

Covers: agent population spawning, per-archetype strategy, trade execution,
balance tracking, determinism with fixed seed.

Cycle-012, Sprint 1 — Task 10.
"""
from __future__ import annotations

import random

import pytest

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import FeeSchedule, MarketPhase
from backend.market.trading import TradingEngine
from backend.services.stub_agents import (
    AgentArchetype,
    StubAgentSpawner,
    TradeDecisionTrace,
    TradeIntent,
)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def spawner() -> StubAgentSpawner:
    """Create a StubAgentSpawner."""
    return StubAgentSpawner()


@pytest.fixture
def trading_setup():
    """Create a market in TRADING phase with position manager and trading engine."""
    market = MarketLifecycle.create_market(
        market_id="mkt_test",
        theatre_id="theatre_stub_test",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["Yes", "No", "Maybe"],
        fee_schedule=FeeSchedule(),
    )
    # Transition to TRADING
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    position_manager = PositionManager(n_outcomes=3, market_id="mkt_test")
    trading_engine = TradingEngine(position_manager=position_manager)

    return market, position_manager, trading_engine


# ===================================================================
# Tests
# ===================================================================


class TestStubAgentSpawner:
    """Tests for agent spawning infrastructure."""

    def test_spawn_produces_6_agents(self, spawner):
        """spawn() produces 6 agents with correct archetypes."""
        agents = spawner.spawn("theatre_test_001")

        assert len(agents) == 6
        archetypes = [a.archetype for a in agents]
        assert AgentArchetype.SHARK in archetypes
        assert AgentArchetype.SPY in archetypes
        assert AgentArchetype.DIPLOMAT in archetypes
        assert AgentArchetype.SABOTEUR in archetypes
        assert AgentArchetype.WHALE in archetypes
        assert AgentArchetype.DEGEN in archetypes

    def test_deterministic_agent_ids(self, spawner):
        """Agent IDs follow {theatre_id}_{archetype} format."""
        agents = spawner.spawn("theatre_abc")

        ids = [a.agent_id for a in agents]
        assert "theatre_abc_shark" in ids
        assert "theatre_abc_spy" in ids
        assert "theatre_abc_diplomat" in ids
        assert "theatre_abc_saboteur" in ids
        assert "theatre_abc_whale" in ids
        assert "theatre_abc_degen" in ids

    def test_agents_have_default_balance(self, spawner):
        """Agents have default initial balance of 1000.0."""
        agents = spawner.spawn("theatre_test")

        for agent in agents:
            assert agent.initial_balance == 1000.0

    def test_custom_balance(self, spawner):
        """Custom initial balance is applied to all agents."""
        agents = spawner.spawn("theatre_test", initial_balance=500.0)

        for agent in agents:
            assert agent.initial_balance == 500.0


class TestSharkStrategy:
    """Tests for Shark archetype strategy."""

    def test_shark_buys_leading_outcome_below_threshold(self, spawner, trading_setup):
        """Shark buys leading outcome when price < 0.7."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_shark_test")
        shark = [a for a in agents if a.archetype == AgentArchetype.SHARK][0]

        # At initial state, all prices are ~0.333 (< 0.7)
        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = shark.strategy(market, prices, None, 0, rng)

        assert intent is not None
        assert intent.shares > 0
        assert intent.trigger.startswith("leading_price=")

    def test_shark_no_trade_above_threshold(self, spawner, trading_setup):
        """Shark does not trade when leading price >= 0.7."""
        market, pm, te = trading_setup

        # Push one outcome above 0.7 by trading heavily
        pm.set_balance("setup_agent", 10000.0)
        for _ in range(50):
            te.execute_trade(market, "setup_agent", 0, 10.0)

        prices = LMSREngine.prices(market.x, market.b)
        assert prices[0] >= 0.7  # Confirm setup worked

        agents = spawner.spawn("theatre_shark_test")
        shark = [a for a in agents if a.archetype == AgentArchetype.SHARK][0]
        rng = random.Random(42)

        intent = shark.strategy(market, prices, None, 0, rng)
        assert intent is None


class TestSpyStrategy:
    """Tests for Spy archetype strategy."""

    def test_spy_trades_with_evidence(self, spawner, trading_setup):
        """Spy trades when evidence is provided."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_spy_test")
        spy = [a for a in agents if a.archetype == AgentArchetype.SPY][0]

        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = spy.strategy(market, prices, {"some": "evidence"}, 0, rng)

        assert intent is not None
        assert intent.trigger == "evidence_arrived"

    def test_spy_no_trade_without_evidence(self, spawner, trading_setup):
        """Spy does NOT trade when evidence is None."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_spy_test")
        spy = [a for a in agents if a.archetype == AgentArchetype.SPY][0]

        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = spy.strategy(market, prices, None, 0, rng)

        assert intent is None


class TestDiplomatStrategy:
    """Tests for Diplomat archetype strategy."""

    def test_diplomat_buys_trailing_when_spread_high(self, spawner, trading_setup):
        """Diplomat buys trailing outcome when spread > 0.4."""
        market, pm, te = trading_setup

        # Create spread > 0.4 by buying outcome 0
        pm.set_balance("setup_agent", 10000.0)
        for _ in range(30):
            te.execute_trade(market, "setup_agent", 0, 10.0)

        prices = LMSREngine.prices(market.x, market.b)
        spread = max(prices) - min(prices)
        assert spread > 0.4  # Confirm setup worked

        agents = spawner.spawn("theatre_diplomat_test")
        diplomat = [a for a in agents if a.archetype == AgentArchetype.DIPLOMAT][0]
        rng = random.Random(42)

        intent = diplomat.strategy(market, prices, None, 0, rng)

        assert intent is not None
        # Should buy the trailing (cheapest) outcome
        min_idx = prices.index(min(prices))
        assert intent.outcome_index == min_idx
        assert intent.trigger.startswith("spread=")


class TestSaboteurStrategy:
    """Tests for Saboteur archetype strategy."""

    def test_saboteur_low_volume_contrary(self, spawner, trading_setup):
        """Saboteur produces low-volume (1-3 shares) contrary trades."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_saboteur_test")
        saboteur = [a for a in agents if a.archetype == AgentArchetype.SABOTEUR][0]

        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = saboteur.strategy(market, prices, None, 0, rng)

        assert intent is not None
        assert 1 <= intent.shares <= 3
        # Should NOT trade the leading outcome
        leading_idx = prices.index(max(prices))
        assert intent.outcome_index != leading_idx


class TestWhaleStrategy:
    """Tests for Whale archetype strategy."""

    def test_whale_large_position_tick_0(self, spawner, trading_setup):
        """Whale places single large position (50+ shares) on tick 0."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_whale_test")
        whale = [a for a in agents if a.archetype == AgentArchetype.WHALE][0]

        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = whale.strategy(market, prices, None, 0, rng)

        assert intent is not None
        assert intent.shares >= 50.0
        assert intent.trigger == "tick_0_large_position"

    def test_whale_holds_after_tick_0(self, spawner, trading_setup):
        """Whale does not trade after tick 0."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_whale_test")
        whale = [a for a in agents if a.archetype == AgentArchetype.WHALE][0]

        prices = LMSREngine.prices(market.x, market.b)
        rng = random.Random(42)

        intent = whale.strategy(market, prices, None, 1, rng)
        assert intent is None

        intent = whale.strategy(market, prices, None, 5, rng)
        assert intent is None


class TestDegenStrategy:
    """Tests for Degen archetype strategy."""

    def test_degen_trades_every_tick(self, spawner, trading_setup):
        """Degen trades every tick with random outcome/volume."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_degen_test")
        degen = [a for a in agents if a.archetype == AgentArchetype.DEGEN][0]

        prices = LMSREngine.prices(market.x, market.b)

        for tick in range(5):
            rng = random.Random(42 + tick)
            intent = degen.strategy(market, prices, None, tick, rng)
            assert intent is not None
            assert 1 <= intent.shares <= 10

    def test_degen_deterministic_with_fixed_seed(self, spawner, trading_setup):
        """Degen is deterministic with fixed seed."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_degen_test")
        degen = [a for a in agents if a.archetype == AgentArchetype.DEGEN][0]

        prices = LMSREngine.prices(market.x, market.b)

        # Same seed produces same result
        rng1 = random.Random(42)
        intent1 = degen.strategy(market, prices, None, 0, rng1)

        rng2 = random.Random(42)
        intent2 = degen.strategy(market, prices, None, 0, rng2)

        assert intent1.outcome_index == intent2.outcome_index
        assert intent1.shares == intent2.shares


class TestExecuteTick:
    """Tests for execute_tick() — full tick execution."""

    def test_execute_tick_produces_traces(self, spawner, trading_setup):
        """execute_tick() produces TradeDecisionTrace for each agent."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_tick_test")

        # Set balances for all agents
        for agent in agents:
            pm.set_balance(agent.agent_id, agent.initial_balance)

        traces = spawner.execute_tick(
            agents=agents,
            market=market,
            trading_engine=te,
            position_manager=pm,
            evidence=None,
            tick=0,
        )

        assert len(traces) == 6
        for trace in traces:
            assert isinstance(trace, TradeDecisionTrace)
            assert trace.tick == 0

    def test_execute_tick_executes_trades(self, spawner, trading_setup):
        """execute_tick() actually executes trades via TradingEngine."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_tick_test")

        for agent in agents:
            pm.set_balance(agent.agent_id, agent.initial_balance)

        traces = spawner.execute_tick(
            agents=agents,
            market=market,
            trading_engine=te,
            position_manager=pm,
            evidence=None,
            tick=0,
        )

        # At least some agents should have executed trades
        executed = [t for t in traces if t.executed_trade is not None]
        assert len(executed) > 0

    def test_agent_balance_tracking_through_trades(self, spawner, trading_setup):
        """Agent balance tracking works through multiple ticks."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_balance_test")

        for agent in agents:
            pm.set_balance(agent.agent_id, agent.initial_balance)

        initial_balances = {
            a.agent_id: pm.get_balance(a.agent_id) for a in agents
        }

        # Execute a few ticks
        for tick in range(3):
            spawner.execute_tick(
                agents=agents,
                market=market,
                trading_engine=te,
                position_manager=pm,
                evidence=None,
                tick=tick,
            )

        # Some agents should have spent money
        agents_with_trades = [
            a for a in agents
            if pm.get_balance(a.agent_id) < initial_balances[a.agent_id]
        ]
        assert len(agents_with_trades) > 0

    def test_trace_completeness(self, spawner, trading_setup):
        """TradeDecisionTrace records complete information."""
        market, pm, te = trading_setup
        agents = spawner.spawn("theatre_trace_test")

        for agent in agents:
            pm.set_balance(agent.agent_id, agent.initial_balance)

        traces = spawner.execute_tick(
            agents=agents,
            market=market,
            trading_engine=te,
            position_manager=pm,
            evidence=None,
            tick=0,
        )

        for trace in traces:
            assert trace.agent_id != ""
            assert trace.archetype != ""
            assert trace.tick == 0
            assert trace.pattern_name != ""
            assert len(trace.market_prices_at_decision) == 3
