"""Tests for ADK integration layer -- FakeADKRunner and EchelonAgent.

Covers: FakeADKRunner lifecycle (run_tick, run_all), evidence schedule
injection, decision log accumulation, EchelonAgent initialise without ADK,
tool binding registration, state persistence between ticks.

Cycle-013, Sprint 3 -- Task 1 + Task 7.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from backend.agents.adk import FakeADKRunner
from backend.agents.adk.echelon_agent import EchelonAgent, HAS_ADK
from backend.agents.agent_instance import TheatreAgentInstance
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import EchelonArchetype, create_genome
from backend.agents.rules_engine import RulesEngine
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.state import FeeSchedule
from backend.market.trading import TradingEngine


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def market_setup():
    """Create a market with 3 outcomes, b=100, in TRADING phase."""
    market = MarketLifecycle.create_market(
        market_id="mkt_test",
        theatre_id="theatre_test",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["A", "B", "C"],
        fee_schedule=FeeSchedule(),
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    pos_mgr = PositionManager(n_outcomes=3, market_id="mkt_test")
    engine = TradingEngine(pos_mgr)
    return market, pos_mgr, engine


@pytest.fixture
def shark_instance():
    """Create a Shark agent instance."""
    genome = create_genome(EchelonArchetype.SHARK, variant="MEGALODON")
    return TheatreAgentInstance.spawn(
        genome=genome,
        theatre_id="theatre_test",
        rules_engine=RulesEngine(),
    )


# ===================================================================
# FakeADKRunner Tests
# ===================================================================


class TestFakeADKRunner:
    """Tests for FakeADKRunner synchronous execution."""

    def test_run_tick_produces_trace(self, shark_instance, market_setup):
        """run_tick() returns a trade and decision trace."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        runner = FakeADKRunner(agent_instance=shark_instance, max_ticks=50)
        trade, trace = runner.run_tick(market, pos_mgr, engine)

        assert isinstance(trace, DecisionTrace)
        assert trace.agent_id == shark_instance.agent_id
        assert runner.tick_count == 1

    def test_run_tick_increments_tick_count(self, shark_instance, market_setup):
        """Tick count increments with each run_tick() call."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        runner = FakeADKRunner(agent_instance=shark_instance, max_ticks=50)
        runner.run_tick(market, pos_mgr, engine)
        runner.run_tick(market, pos_mgr, engine)
        runner.run_tick(market, pos_mgr, engine)

        assert runner.tick_count == 3
        assert len(runner.decision_log) == 3

    def test_run_all_executes_max_ticks(self, shark_instance, market_setup):
        """run_all() executes exactly max_ticks ticks."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        runner = FakeADKRunner(agent_instance=shark_instance, max_ticks=10)
        results = runner.run_all(market, pos_mgr, engine)

        assert len(results) == 10
        assert len(runner.decision_log) == 10

    def test_evidence_schedule_injection(self, shark_instance, market_setup):
        """Evidence schedule injects evidence at specified ticks."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        evidence_schedule = {
            3: {"type": "filing_check", "status": "pending"},
            7: {"type": "filing_check", "status": "confirmed"},
        }

        runner = FakeADKRunner(agent_instance=shark_instance, max_ticks=10)
        results = runner.run_all(
            market, pos_mgr, engine, evidence_schedule=evidence_schedule
        )

        # Evidence ticks should have new_evidence_flag=True
        for i, (trade, trace) in enumerate(results):
            if i in (3, 7):
                assert trace.evidence_state["new_evidence_flag"] is True
            else:
                assert trace.evidence_state["new_evidence_flag"] is False

    def test_decision_log_accumulates(self, shark_instance, market_setup):
        """Decision log accumulates traces across all ticks."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        runner = FakeADKRunner(agent_instance=shark_instance, max_ticks=5)
        runner.run_all(market, pos_mgr, engine)

        assert len(runner.decision_log) == 5
        for trace in runner.decision_log:
            assert isinstance(trace, DecisionTrace)
            assert trace.tier_used == "T1-RULES"


# ===================================================================
# EchelonAgent Tests
# ===================================================================


class TestEchelonAgent:
    """Tests for EchelonAgent ADK wrapper."""

    def test_initialise_without_adk_raises(self, shark_instance):
        """initialise() raises RuntimeError when ADK not installed."""
        agent = EchelonAgent(agent_instance=shark_instance)
        if not HAS_ADK:
            with pytest.raises(RuntimeError, match="Google ADK not available"):
                agent.initialise()

    def test_tool_binding_registration(self, shark_instance):
        """register_tools() stores tool references."""
        agent = EchelonAgent(agent_instance=shark_instance)
        mock_status = lambda: None
        mock_verify = lambda: None
        mock_trade = lambda: None

        agent.register_tools(
            echelon_status=mock_status,
            echelon_verify=mock_verify,
            execute_trade=mock_trade,
        )

        assert agent._tools["echelon_status"] is mock_status
        assert agent._tools["echelon_verify"] is mock_verify
        assert agent._tools["execute_trade"] is mock_trade

    def test_on_heartbeat_produces_trace(self, shark_instance, market_setup):
        """on_heartbeat() delegates to instance.tick() and records trace."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        agent = EchelonAgent(agent_instance=shark_instance)
        trade, trace = agent.on_heartbeat(
            tick=0, market=market, position_manager=pos_mgr,
            trading_engine=engine,
        )

        assert isinstance(trace, DecisionTrace)
        assert len(agent.decision_history) == 1

    def test_state_persists_between_ticks(self, shark_instance, market_setup):
        """Decision history accumulates across heartbeat ticks."""
        market, pos_mgr, engine = market_setup
        pos_mgr.set_balance(shark_instance.agent_id, 1000.0)

        agent = EchelonAgent(agent_instance=shark_instance)
        for tick in range(5):
            agent.on_heartbeat(
                tick=tick, market=market, position_manager=pos_mgr,
                trading_engine=engine,
            )

        assert len(agent.decision_history) == 5

    def test_agent_id_from_instance(self, shark_instance):
        """agent_id property delegates to wrapped instance."""
        agent = EchelonAgent(agent_instance=shark_instance)
        assert agent.agent_id == shark_instance.agent_id
