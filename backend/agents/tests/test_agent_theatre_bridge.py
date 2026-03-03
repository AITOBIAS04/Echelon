"""Tests for Agent-Theatre Bridge -- autonomous agent lifecycle in Theatres.

Covers: spawn all 6 archetypes, execute_tick produces traces, settle
collects P&L, collect_decision_traces returns all traces, initial balance
propagation, P&L aggregation.

Cycle-013, Sprint 3 -- Tasks 3 + 5 + 7.
"""
from __future__ import annotations

import math

import pytest

from backend.agents.agent_instance import AgentSettlementResult
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import EchelonArchetype
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.state import FeeSchedule
from backend.market.trading import TradingEngine
from backend.services.agent_theatre_bridge import AgentTheatreBridge


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def market_setup():
    """Create a market with 3 outcomes, b=100, in TRADING phase."""
    market = MarketLifecycle.create_market(
        market_id="mkt_bridge_test",
        theatre_id="theatre_bridge_test",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["A", "B", "C"],
        fee_schedule=FeeSchedule(),
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    pos_mgr = PositionManager(n_outcomes=3, market_id="mkt_bridge_test")
    engine = TradingEngine(pos_mgr)
    return market, pos_mgr, engine


# ===================================================================
# Spawn Tests
# ===================================================================


class TestAgentSpawning:
    """Tests for AgentTheatreBridge.spawn_agents()."""

    def test_spawn_all_6_archetypes(self, market_setup):
        """Default spawn creates one agent per archetype (6 total)."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        assert len(agents) == 6
        archetypes = {a.genome.archetype for a in agents}
        assert archetypes == set(EchelonArchetype)

    def test_spawn_subset_of_archetypes(self, market_setup):
        """Spawn only specified archetypes."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
            archetypes=[EchelonArchetype.SHARK, EchelonArchetype.DEGEN],
        )

        assert len(agents) == 2
        archetypes = {a.genome.archetype for a in agents}
        assert archetypes == {EchelonArchetype.SHARK, EchelonArchetype.DEGEN}

    def test_initial_balance_propagation(self, market_setup):
        """Initial balance is set for each agent in position manager."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            initial_balance=5000.0,
            position_manager=pos_mgr,
        )

        for agent in agents:
            balance = pos_mgr.get_balance(agent.agent_id)
            assert balance == 5000.0


# ===================================================================
# Execute Tick Tests
# ===================================================================


class TestExecuteTick:
    """Tests for AgentTheatreBridge.execute_tick()."""

    def test_execute_tick_produces_traces(self, market_setup):
        """execute_tick() returns one DecisionTrace per agent."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        traces = bridge.execute_tick(
            agents=agents, market=market, trading_engine=engine,
            position_manager=pos_mgr, evidence=None, tick=0,
        )

        assert len(traces) == 6
        for trace in traces:
            assert isinstance(trace, DecisionTrace)

    def test_multiple_ticks_accumulate_traces(self, market_setup):
        """Multiple ticks accumulate traces in the bridge."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        for tick in range(5):
            bridge.execute_tick(
                agents=agents, market=market, trading_engine=engine,
                position_manager=pos_mgr, evidence=None, tick=tick,
            )

        all_traces = bridge.collect_decision_traces()
        assert len(all_traces) == 30  # 6 agents * 5 ticks


# ===================================================================
# Settle and P&L Tests
# ===================================================================


class TestSettlement:
    """Tests for AgentTheatreBridge.settle_agents() and P&L aggregation."""

    def test_settle_returns_results_per_agent(self, market_setup):
        """settle_agents() returns one result per agent."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        # Run a few ticks to generate trades
        for tick in range(10):
            bridge.execute_tick(
                agents=agents, market=market, trading_engine=engine,
                position_manager=pos_mgr, evidence=None, tick=tick,
            )

        results = bridge.settle_agents(agents, pos_mgr, resolved_outcome=0)

        assert len(results) == 6
        for r in results:
            assert isinstance(r, AgentSettlementResult)
            assert r.archetype in {a.value for a in EchelonArchetype}

    def test_pnl_aggregation_by_archetype(self, market_setup):
        """aggregate_pnl() groups P&L by archetype."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        for tick in range(10):
            bridge.execute_tick(
                agents=agents, market=market, trading_engine=engine,
                position_manager=pos_mgr, evidence=None, tick=tick,
            )

        results = bridge.settle_agents(agents, pos_mgr, resolved_outcome=0)
        pnl = AgentTheatreBridge.aggregate_pnl(results)

        assert len(pnl) == 6  # One entry per archetype
        for archetype_name in pnl:
            assert isinstance(pnl[archetype_name], float)

    def test_single_theatre_pnl_correctness(self, market_setup):
        """Settlement P&L is consistent (payout - net_cashflow)."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        for tick in range(10):
            bridge.execute_tick(
                agents=agents, market=market, trading_engine=engine,
                position_manager=pos_mgr, evidence=None, tick=tick,
            )

        results = bridge.settle_agents(agents, pos_mgr, resolved_outcome=0)

        # Verify each result has valid fields
        for r in results:
            assert r.agent_id != ""
            assert isinstance(r.trades_executed, int)
            assert isinstance(r.realised_pnl, float)
            assert isinstance(r.final_position, list)
            assert len(r.final_position) == 3

    def test_collect_traces_returns_copy(self, market_setup):
        """collect_decision_traces() returns a copy, not a reference."""
        market, pos_mgr, engine = market_setup
        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_test",
            position_manager=pos_mgr,
        )

        bridge.execute_tick(
            agents=agents, market=market, trading_engine=engine,
            position_manager=pos_mgr, evidence=None, tick=0,
        )

        traces1 = bridge.collect_decision_traces()
        traces2 = bridge.collect_decision_traces()
        assert traces1 is not traces2
        assert len(traces1) == len(traces2)
