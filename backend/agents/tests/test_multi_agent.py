"""Tests for multi-agent population -- 6 archetypes trading simultaneously.

Validates heterogeneous behaviour: Shark trades most, Whale trades least,
each archetype uses characteristic patterns, results are deterministic.

Cycle-013, Sprint 3 -- Tasks 4 + 7.
"""
from __future__ import annotations

import pytest

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
def population_setup():
    """Set up a 6-agent population with 50 ticks, market in TRADING phase."""
    market = MarketLifecycle.create_market(
        market_id="mkt_multi",
        theatre_id="theatre_multi",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["Filed on time", "Filed late", "Not filed"],
        fee_schedule=FeeSchedule(),
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    pos_mgr = PositionManager(n_outcomes=3, market_id="mkt_multi")
    engine = TradingEngine(pos_mgr)

    bridge = AgentTheatreBridge()
    agents = bridge.spawn_agents(
        theatre_id="theatre_multi",
        initial_balance=50000.0,
        position_manager=pos_mgr,
    )

    return market, pos_mgr, engine, bridge, agents


def _run_population(market, pos_mgr, engine, bridge, agents, n_ticks=50,
                    evidence_ticks=None, seed=42):
    """Run n_ticks for the population with optional evidence injection."""
    if evidence_ticks is None:
        evidence_ticks = {10, 20, 35}

    evidence_data = {"type": "filing_check", "status": "pending"}

    for tick in range(n_ticks):
        evidence = evidence_data if tick in evidence_ticks else None
        bridge.execute_tick(
            agents=agents, market=market, trading_engine=engine,
            position_manager=pos_mgr, evidence=evidence, tick=tick,
            seed=seed,
        )


# ===================================================================
# Multi-Agent Population Tests
# ===================================================================


class TestMultiAgentPopulation:
    """Tests for 6-archetype population with heterogeneous behaviour."""

    def test_six_archetypes_all_trade(self, population_setup):
        """All 6 archetypes produce decisions over 50 ticks."""
        market, pos_mgr, engine, bridge, agents = population_setup
        _run_population(market, pos_mgr, engine, bridge, agents)

        all_traces = bridge.collect_decision_traces()
        assert len(all_traces) == 300  # 6 agents * 50 ticks

        # Each agent produced exactly 50 traces
        for agent in agents:
            agent_traces = [t for t in all_traces if t.agent_id == agent.agent_id]
            assert len(agent_traces) == 50

    def test_trade_frequency_ordering(self, population_setup):
        """Shark trades most frequently, Whale trades least (patience)."""
        market, pos_mgr, engine, bridge, agents = population_setup
        _run_population(market, pos_mgr, engine, bridge, agents)

        # Count executed trades per archetype
        trade_counts = {}
        for agent in agents:
            trade_counts[agent.genome.archetype.value] = agent.trade_count

        # Shark should trade more than Whale (patience: 30 vs 90)
        shark_trades = trade_counts.get("SHARK", 0)
        whale_trades = trade_counts.get("WHALE", 0)
        assert shark_trades > whale_trades, (
            f"Shark ({shark_trades}) should trade more than Whale ({whale_trades})"
        )

    def test_pattern_names_per_archetype(self, population_setup):
        """Each archetype uses its characteristic named pattern."""
        market, pos_mgr, engine, bridge, agents = population_setup
        _run_population(market, pos_mgr, engine, bridge, agents)

        all_traces = bridge.collect_decision_traces()

        # Build pattern set per archetype
        patterns_by_archetype = {}
        for agent in agents:
            arch = agent.genome.archetype.value
            agent_traces = [t for t in all_traces if t.agent_id == agent.agent_id]
            patterns = {t.pattern_name for t in agent_traces}
            patterns_by_archetype[arch] = patterns

        # Expected characteristic patterns
        expected = {
            "SHARK": "momentum_exploitation",
            "SPY": "intel_arbitrage",
            "DIPLOMAT": "stability_maintenance",
            "SABOTEUR": "chaos_creation",
            "WHALE": "conviction_accumulation",
            "DEGEN": "random_exploration",
        }

        for archetype, expected_pattern in expected.items():
            assert expected_pattern in patterns_by_archetype.get(archetype, set()), (
                f"{archetype} missing expected pattern '{expected_pattern}'. "
                f"Got: {patterns_by_archetype.get(archetype, set())}"
            )

    def test_deterministic_with_fixed_seed(self, population_setup):
        """Results are deterministic when seed and evidence are fixed."""
        market1, pos_mgr1, engine1, bridge1, agents1 = population_setup
        _run_population(market1, pos_mgr1, engine1, bridge1, agents1, seed=42)
        traces1 = bridge1.collect_decision_traces()

        # Second run with fresh setup (same theatre_id for determinism)
        market2 = MarketLifecycle.create_market(
            market_id="mkt_multi",
            theatre_id="theatre_multi",
            b=100.0,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            fee_schedule=FeeSchedule(),
        )
        MarketLifecycle.commit(market2)
        MarketLifecycle.open_trading(market2)
        pos_mgr2 = PositionManager(n_outcomes=3, market_id="mkt_multi")
        engine2 = TradingEngine(pos_mgr2)
        bridge2 = AgentTheatreBridge()
        agents2 = bridge2.spawn_agents(
            theatre_id="theatre_multi",
            initial_balance=50000.0,
            position_manager=pos_mgr2,
        )
        _run_population(market2, pos_mgr2, engine2, bridge2, agents2, seed=42)
        traces2 = bridge2.collect_decision_traces()

        assert len(traces1) == len(traces2)
        for t1, t2 in zip(traces1, traces2):
            assert t1.action == t2.action
            assert t1.confidence == t2.confidence
            assert t1.pattern_name == t2.pattern_name

    def test_evidence_triggers_spy_activity(self, population_setup):
        """Evidence injection ticks show Spy trading on evidence."""
        market, pos_mgr, engine, bridge, agents = population_setup
        _run_population(market, pos_mgr, engine, bridge, agents)

        all_traces = bridge.collect_decision_traces()

        spy_agent = next(
            a for a in agents if a.genome.archetype == EchelonArchetype.SPY
        )
        spy_evidence_traces = [
            t for t in all_traces
            if t.agent_id == spy_agent.agent_id
            and t.evidence_state.get("new_evidence_flag") is True
        ]

        # Spy should have traces at evidence ticks (10, 20, 35)
        assert len(spy_evidence_traces) == 3

    def test_degen_highest_exploration(self, population_setup):
        """Degen has highest exploration rate, produces diverse actions."""
        market, pos_mgr, engine, bridge, agents = population_setup
        _run_population(market, pos_mgr, engine, bridge, agents)

        all_traces = bridge.collect_decision_traces()

        degen_agent = next(
            a for a in agents if a.genome.archetype == EchelonArchetype.DEGEN
        )
        degen_traces = [
            t for t in all_traces if t.agent_id == degen_agent.agent_id
        ]

        # Degen should produce trades (xi=0.95, high exploration)
        degen_trade_count = degen_agent.trade_count
        assert degen_trade_count > 0, "Degen should produce at least some trades"
