"""Tests for TheatreAgentInstance lifecycle and LMSR integration.

Covers spawn -> tick -> settle lifecycle, P&L computation, multi-instance
per identity, trade count accumulation, decision trace completeness,
failed trade handling, and LMSR integration correctness.

Cycle-013, Sprint 1 -- Task 7.
"""
from __future__ import annotations

import pytest

from backend.agents.agent_instance import (
    AgentSettlementResult,
    TheatreAgentInstance,
    TradeIntent,
)
from backend.agents.genome import (
    EchelonArchetype,
    create_degen_genome,
    create_genome,
    create_megalodon_genome,
    create_shark_genome,
    create_spy_genome,
)
from backend.agents.rules_engine import RulesEngine
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase, MarketState
from backend.market.trading import TradingEngine


# ===================================================================
# Fixtures
# ===================================================================


def _make_market(
    n_outcomes: int = 3,
    b: float = 100.0,
) -> MarketState:
    """Create a TRADING market with uniform initial state."""
    return MarketState(
        market_id="mkt_test",
        theatre_id="theatre_test",
        b=b,
        n_outcomes=n_outcomes,
        outcome_labels=[f"outcome_{i}" for i in range(n_outcomes)],
        x=[0.0] * n_outcomes,
        phase=MarketPhase.TRADING,
    )


def _make_engine(market: MarketState, initial_balance: float = 1000.0):
    """Create a PositionManager + TradingEngine pair."""
    pm = PositionManager(n_outcomes=market.n_outcomes, market_id=market.market_id)
    te = TradingEngine(position_manager=pm)
    return pm, te


# ===================================================================
# Tests
# ===================================================================


class TestTheatreAgentInstance:
    """Tests for agent instance lifecycle."""

    def test_spawn_creates_instance(self) -> None:
        """spawn() creates an instance with correct agent_id."""
        genome = create_shark_genome()
        instance = TheatreAgentInstance.spawn(genome, "theatre_ch")
        assert instance.agent_id == "theatre_ch_shark"
        assert instance.genome == genome
        assert instance.theatre_id == "theatre_ch"
        assert instance.trade_count == 0
        assert instance.decision_traces == []
        assert instance.is_settled is False

    def test_spawn_with_variant(self) -> None:
        """spawn() with variant includes variant in agent_id."""
        genome = create_megalodon_genome()
        instance = TheatreAgentInstance.spawn(genome, "theatre_mega")
        assert instance.agent_id == "theatre_mega_shark_megalodon"

    def test_full_lifecycle_spawn_tick_settle(self) -> None:
        """Complete lifecycle: spawn -> 10 ticks -> settle with P&L."""
        genome = create_shark_genome()
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_test")
        pm.set_balance(instance.agent_id, 1000.0)

        # Run 10 ticks
        for tick in range(10):
            trade, trace = instance.tick(market, pm, te, None, tick, seed=42)
            assert trace is not None
            assert trace.tick_id == f"tick_{tick:04d}"
            assert trace.agent_id == instance.agent_id

        assert len(instance.decision_traces) == 10

        # Settle
        result = instance.settle(pm, resolved_outcome=0)
        assert isinstance(result, AgentSettlementResult)
        assert result.agent_id == instance.agent_id
        assert result.archetype == "SHARK"
        assert result.trades_executed == instance.trade_count
        assert instance.is_settled is True

    def test_trade_count_accumulation(self) -> None:
        """Trade count accumulates correctly across ticks."""
        genome = create_degen_genome()  # Degen trades frequently
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_degen")
        pm.set_balance(instance.agent_id, 5000.0)

        trades_executed = 0
        for tick in range(20):
            trade, trace = instance.tick(market, pm, te, None, tick, seed=42)
            if trade is not None:
                trades_executed += 1

        assert instance.trade_count == trades_executed
        assert instance.trade_count >= 0

    def test_decision_traces_completeness(self) -> None:
        """Decision traces accumulate and contain all required fields."""
        genome = create_spy_genome()
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_spy")
        pm.set_balance(instance.agent_id, 1000.0)

        for tick in range(5):
            instance.tick(market, pm, te, None, tick, seed=42)

        traces = instance.decision_traces
        assert len(traces) == 5

        for trace in traces:
            assert trace.tier_used == "T1-RULES"
            assert trace.theatre_id == "theatre_spy"
            assert trace.pattern_name == "intel_arbitrage"
            assert trace.t0_context_hash != ""
            assert trace.reasoning_summary != ""
            # RLMF compatibility
            d = trace.to_rlmf_dict()
            assert isinstance(d, dict)
            assert "pattern_name" in d

    def test_multi_instance_per_identity(self) -> None:
        """Multiple instances can be spawned from the same genome."""
        genome = create_shark_genome()

        i1 = TheatreAgentInstance.spawn(genome, "theatre_a")
        i2 = TheatreAgentInstance.spawn(genome, "theatre_b")

        assert i1.agent_id != i2.agent_id
        assert i1.agent_id == "theatre_a_shark"
        assert i2.agent_id == "theatre_b_shark"
        assert i1.genome == i2.genome  # Same genome

    def test_failed_trade_graceful_handling(self) -> None:
        """Failed trades (insufficient balance) handled gracefully."""
        genome = create_shark_genome()
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_broke")
        pm.set_balance(instance.agent_id, 0.01)  # Near-zero balance

        # Should not crash even with insufficient funds
        trade, trace = instance.tick(market, pm, te, None, 0, seed=42)

        # Trace is always recorded regardless of trade success
        assert trace is not None
        assert trace.agent_id == instance.agent_id
        # Trade may be None if failed
        assert len(instance.decision_traces) == 1

    def test_pnl_correctness_winning_outcome(self) -> None:
        """P&L is correct when agent holds winning outcome shares."""
        genome = create_shark_genome()
        market = _make_market(n_outcomes=2, b=100.0)
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_pnl")
        pm.set_balance(instance.agent_id, 1000.0)

        # Manually execute a trade to set up a known position
        trade = te.execute_trade(
            market=market,
            agent_id=instance.agent_id,
            outcome_index=0,
            shares=10.0,
        )
        assert trade is not None

        # Get position and check
        position = pm.get_position(instance.agent_id)
        assert position.shares[0] == 10.0
        cost = position.net_cashflow
        assert cost > 0  # Buying costs money

        # Settle with outcome 0 winning
        result = instance.settle(pm, resolved_outcome=0)

        # Winning shares pay 1:1, so payout = 10.0
        # Realised P&L = payout - net_cashflow
        expected_pnl = 10.0 - cost
        assert abs(result.realised_pnl - expected_pnl) < 1e-9
        assert result.unrealised_pnl == 0.0

    def test_position_updates_visible_in_next_tick(self) -> None:
        """After a trade, position state is visible in the next tick's T0Context."""
        genome = create_shark_genome()
        market = _make_market(n_outcomes=2, b=100.0)
        # Make prices non-uniform so Shark actually trades
        market.x = [20.0, 0.0]
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_pos")
        pm.set_balance(instance.agent_id, 5000.0)

        # First tick
        trade1, trace1 = instance.tick(market, pm, te, None, 0, seed=42)

        # Second tick -- position from first trade should be visible
        trade2, trace2 = instance.tick(market, pm, te, None, 1, seed=42)

        # Both traces should have non-empty context hashes
        assert trace1.t0_context_hash != ""
        assert trace2.t0_context_hash != ""

        # If first trade executed, hashes should differ (position changed)
        if trade1 is not None:
            assert trace1.t0_context_hash != trace2.t0_context_hash

    def test_balance_decrements_after_trade(self) -> None:
        """Balance decrements correctly after trade execution."""
        genome = create_shark_genome()
        market = _make_market(n_outcomes=2, b=100.0)
        market.x = [20.0, 0.0]  # Non-uniform for trading
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_bal")
        initial_balance = 5000.0
        pm.set_balance(instance.agent_id, initial_balance)

        trade, trace = instance.tick(market, pm, te, None, 0, seed=42)

        if trade is not None:
            remaining = pm.get_balance(instance.agent_id)
            assert remaining < initial_balance
            assert remaining == initial_balance - trade.cost

    def test_rlmf_dict_from_lifecycle(self) -> None:
        """Decision traces from lifecycle produce valid RLMF dicts."""
        genome = create_shark_genome()
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_rlmf")
        pm.set_balance(instance.agent_id, 1000.0)

        for tick in range(3):
            instance.tick(market, pm, te, None, tick, seed=42)

        for trace in instance.decision_traces:
            d = trace.to_rlmf_dict()
            assert isinstance(d, dict)
            assert d["tier_used"] == "T1-RULES"
            assert "pattern_name" in d
            assert "options_considered" in d
            assert "reasoning_summary" in d
            assert isinstance(d["evidence_refs"], list)


class TestAllArchetypesLifecycle:
    """Integration test: all 6 archetypes complete a full lifecycle."""

    @pytest.mark.parametrize("archetype", list(EchelonArchetype))
    def test_archetype_lifecycle(self, archetype: EchelonArchetype) -> None:
        """Each archetype completes spawn -> 5 ticks -> settle."""
        genome = create_genome(archetype)
        market = _make_market()
        pm, te = _make_engine(market)

        instance = TheatreAgentInstance.spawn(genome, "theatre_all")
        pm.set_balance(instance.agent_id, 2000.0)

        for tick in range(5):
            trade, trace = instance.tick(market, pm, te, None, tick, seed=42)
            assert trace is not None

        result = instance.settle(pm, resolved_outcome=0)
        assert result.archetype == archetype.value
        assert len(instance.decision_traces) == 5
