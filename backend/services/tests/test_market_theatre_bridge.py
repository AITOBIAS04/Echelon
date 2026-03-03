"""Tests for MarketTheatreBridge — LMSR <-> Theatre integration.

Covers: market creation from Theatre config, phase transitions,
state serialisation roundtrip, parameter mutation rejection.

Cycle-012, Sprint 1 — Task 9.
"""
from __future__ import annotations

import pytest

from backend.market.exceptions import InvalidPhaseTransition
from backend.market.state import FeeSchedule, MarketPhase
from backend.services.market_theatre_bridge import MarketTheatreBridge


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def bridge() -> MarketTheatreBridge:
    """Create a fresh MarketTheatreBridge."""
    return MarketTheatreBridge()


@pytest.fixture
def theatre_market(bridge):
    """Create a Theatre market and return (bridge, theatre_id)."""
    theatre_id = "theatre_test_001"
    bridge.create_market_for_theatre(
        theatre_id=theatre_id,
        market_id="mkt_test_001",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["Yes", "No", "Maybe"],
        fee_schedule=FeeSchedule(trade_fee_bps=50, resolution_fee_bps=100),
    )
    return bridge, theatre_id


# ===================================================================
# Tests
# ===================================================================


class TestMarketTheatreBridge:
    """Tests for MarketTheatreBridge."""

    def test_create_market_produces_correct_state(self, bridge):
        """Market creation from Theatre config produces correct MarketState."""
        theatre_id = "theatre_create_001"
        state = bridge.create_market_for_theatre(
            theatre_id=theatre_id,
            market_id="mkt_create_001",
            b=100.0,
            n_outcomes=3,
            outcome_labels=["A", "B", "C"],
            fee_schedule=FeeSchedule(trade_fee_bps=50),
        )

        assert state.market.b == 100.0
        assert state.market.n_outcomes == 3
        assert state.market.outcome_labels == ["A", "B", "C"]
        assert state.market.phase == MarketPhase.CREATED
        assert state.market.theatre_id == theatre_id
        assert state.position_manager is not None
        assert state.trading_engine is not None

    def test_transition_created_to_committed(self, theatre_market):
        """Phase transition CREATED -> COMMITTED works via bridge."""
        bridge, theatre_id = theatre_market

        market = bridge.transition_market(theatre_id, MarketPhase.COMMITTED)

        assert market.phase == MarketPhase.COMMITTED
        assert market.commitment_hash is not None

    def test_transition_committed_to_trading(self, theatre_market):
        """Phase transition COMMITTED -> TRADING works via bridge."""
        bridge, theatre_id = theatre_market

        bridge.transition_market(theatre_id, MarketPhase.COMMITTED)
        market = bridge.transition_market(theatre_id, MarketPhase.TRADING)

        assert market.phase == MarketPhase.TRADING

    def test_invalid_transition_raises(self, theatre_market):
        """Invalid phase transition raises InvalidPhaseTransition."""
        bridge, theatre_id = theatre_market

        with pytest.raises(InvalidPhaseTransition):
            # Cannot go CREATED -> TRADING directly
            bridge.transition_market(theatre_id, MarketPhase.TRADING)

    def test_serialise_deserialise_roundtrip(self, theatre_market):
        """Serialisation roundtrip preserves all MarketState fields."""
        bridge, theatre_id = theatre_market

        serialised = bridge.serialise_state(theatre_id)
        restored = bridge.deserialise_state(serialised)

        original = bridge.get_market_state(theatre_id).market
        assert restored.market_id == original.market_id
        assert restored.theatre_id == original.theatre_id
        assert restored.b == original.b
        assert restored.n_outcomes == original.n_outcomes
        assert restored.outcome_labels == original.outcome_labels
        assert restored.x == original.x
        assert restored.phase == original.phase
        assert restored.fee_schedule.trade_fee_bps == original.fee_schedule.trade_fee_bps
        assert restored.fee_schedule.resolution_fee_bps == original.fee_schedule.resolution_fee_bps

    def test_nonexistent_theatre_returns_none(self, bridge):
        """get_market_state for non-existent theatre returns None."""
        assert bridge.get_market_state("nonexistent") is None

    def test_settle_market(self, theatre_market):
        """settle_market executes begin_resolution + settle in one call."""
        bridge, theatre_id = theatre_market

        # Transition through to TRADING
        bridge.transition_market(theatre_id, MarketPhase.COMMITTED)
        bridge.transition_market(theatre_id, MarketPhase.TRADING)

        # Settle
        report = bridge.settle_market(theatre_id, winning_outcome=0)

        assert report.winning_outcome == 0
        assert report.winning_label == "Yes"
        assert report.market_id == "mkt_test_001"

        # Market should now be SETTLED
        state = bridge.get_market_state(theatre_id)
        assert state.market.phase == MarketPhase.SETTLED

    def test_serialise_after_transitions(self, theatre_market):
        """Serialisation preserves state after phase transitions."""
        bridge, theatre_id = theatre_market

        bridge.transition_market(theatre_id, MarketPhase.COMMITTED)

        serialised = bridge.serialise_state(theatre_id)
        assert serialised["phase"] == "COMMITTED"
        assert serialised["commitment_hash"] is not None

    def test_bridge_stores_state_by_theatre_id(self, bridge):
        """Bridge stores state keyed by theatre_id — multiple theatres coexist."""
        bridge.create_market_for_theatre(
            theatre_id="theatre_a",
            market_id="mkt_a",
            b=50.0,
            n_outcomes=2,
            outcome_labels=["X", "Y"],
        )
        bridge.create_market_for_theatre(
            theatre_id="theatre_b",
            market_id="mkt_b",
            b=200.0,
            n_outcomes=4,
            outcome_labels=["A", "B", "C", "D"],
        )

        state_a = bridge.get_market_state("theatre_a")
        state_b = bridge.get_market_state("theatre_b")

        assert state_a.market.b == 50.0
        assert state_b.market.b == 200.0
        assert state_a.market.n_outcomes == 2
        assert state_b.market.n_outcomes == 4
