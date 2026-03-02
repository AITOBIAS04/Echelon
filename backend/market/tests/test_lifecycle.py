"""Lifecycle state machine transition tests."""
from __future__ import annotations

import pytest

from backend.market.exceptions import (
    InvalidMarketParameters,
    InvalidPhaseTransition,
)
from backend.market.lifecycle import MarketLifecycle
from backend.market.state import MarketPhase


def _make_market() -> "MarketState":
    """Helper — creates a standard test market in CREATED phase."""
    from backend.market.state import MarketState

    return MarketLifecycle.create_market(
        market_id="mkt_test",
        theatre_id="theatre_test",
        b=100.0,
        n_outcomes=3,
        outcome_labels=["Yes", "No", "Maybe"],
    )


class TestValidTransitions:
    """Valid forward-only transitions."""

    def test_valid_transition_sequence(self) -> None:
        """CREATED -> COMMITTED -> TRADING -> RESOLVING -> SETTLED succeeds."""
        m = _make_market()
        assert m.phase == MarketPhase.CREATED

        MarketLifecycle.commit(m)
        assert m.phase == MarketPhase.COMMITTED

        MarketLifecycle.open_trading(m)
        assert m.phase == MarketPhase.TRADING

        MarketLifecycle.begin_resolution(m, winning_outcome=0)
        assert m.phase == MarketPhase.RESOLVING
        assert m.resolved_outcome == 0

        MarketLifecycle.settle(m)
        assert m.phase == MarketPhase.SETTLED

    def test_commit_sets_hash(self) -> None:
        """After commit(), commitment_hash is 64-char hex string."""
        m = _make_market()
        MarketLifecycle.commit(m)
        assert m.commitment_hash is not None
        assert len(m.commitment_hash) == 64
        assert all(c in "0123456789abcdef" for c in m.commitment_hash)

    def test_commit_sets_timestamp(self) -> None:
        """After commit(), committed_at is an ISO 8601 string."""
        m = _make_market()
        MarketLifecycle.commit(m)
        assert m.committed_at is not None
        assert "T" in m.committed_at  # ISO 8601 contains T separator


class TestInvalidTransitions:
    """Invalid transitions must raise InvalidPhaseTransition."""

    def test_skip_committed_raises(self) -> None:
        """CREATED -> TRADING raises InvalidPhaseTransition."""
        m = _make_market()
        with pytest.raises(InvalidPhaseTransition) as exc_info:
            MarketLifecycle.open_trading(m)
        assert exc_info.value.current == MarketPhase.CREATED
        assert exc_info.value.target == MarketPhase.TRADING

    def test_backward_transition_raises(self) -> None:
        """TRADING -> COMMITTED raises InvalidPhaseTransition."""
        m = _make_market()
        MarketLifecycle.commit(m)
        MarketLifecycle.open_trading(m)
        with pytest.raises(InvalidPhaseTransition) as exc_info:
            MarketLifecycle.commit(m)
        assert exc_info.value.current == MarketPhase.TRADING
        assert exc_info.value.target == MarketPhase.COMMITTED

    def test_double_commit_raises(self) -> None:
        """COMMITTED -> COMMITTED raises InvalidPhaseTransition."""
        m = _make_market()
        MarketLifecycle.commit(m)
        with pytest.raises(InvalidPhaseTransition):
            MarketLifecycle.commit(m)

    def test_settle_from_trading_raises(self) -> None:
        """TRADING -> SETTLED raises InvalidPhaseTransition."""
        m = _make_market()
        MarketLifecycle.commit(m)
        MarketLifecycle.open_trading(m)
        with pytest.raises(InvalidPhaseTransition):
            MarketLifecycle.settle(m)


class TestCreateMarketValidation:
    """Factory parameter validation."""

    def test_b_zero_raises(self) -> None:
        with pytest.raises(InvalidMarketParameters, match="b must be positive"):
            MarketLifecycle.create_market("m", "t", 0.0, 2, ["A", "B"])

    def test_b_negative_raises(self) -> None:
        with pytest.raises(InvalidMarketParameters, match="b must be positive"):
            MarketLifecycle.create_market("m", "t", -10.0, 2, ["A", "B"])

    def test_n_outcomes_one_raises(self) -> None:
        with pytest.raises(InvalidMarketParameters, match="n_outcomes"):
            MarketLifecycle.create_market("m", "t", 10.0, 1, ["A"])

    def test_label_count_mismatch_raises(self) -> None:
        with pytest.raises(InvalidMarketParameters, match="outcome_labels length"):
            MarketLifecycle.create_market("m", "t", 10.0, 2, ["A"])

    def test_create_market_initialises_x(self) -> None:
        m = MarketLifecycle.create_market("m", "t", 10.0, 3, ["A", "B", "C"])
        assert m.x == [0.0, 0.0, 0.0]
        assert m.created_at != ""


class TestResolutionValidation:
    """begin_resolution outcome index validation."""

    def test_negative_outcome_raises(self) -> None:
        m = _make_market()
        MarketLifecycle.commit(m)
        MarketLifecycle.open_trading(m)
        with pytest.raises(InvalidMarketParameters, match="winning_outcome"):
            MarketLifecycle.begin_resolution(m, -1)

    def test_outcome_out_of_bounds_raises(self) -> None:
        m = _make_market()
        MarketLifecycle.commit(m)
        MarketLifecycle.open_trading(m)
        with pytest.raises(InvalidMarketParameters, match="winning_outcome"):
            MarketLifecycle.begin_resolution(m, m.n_outcomes)
