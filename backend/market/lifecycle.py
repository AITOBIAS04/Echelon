"""Market lifecycle state machine — forward-only phase transitions.

Phases: CREATED -> COMMITTED -> TRADING -> RESOLVING -> SETTLED
No transition is reversible. Parameters are immutable after COMMITTED.
"""
from __future__ import annotations

from datetime import datetime

from backend.market.commitment import MarketCommitment
from backend.market.exceptions import (
    InvalidMarketParameters,
    InvalidPhaseTransition,
)
from backend.market.state import FeeSchedule, MarketPhase, MarketState


class MarketLifecycle:
    """Factory and transition methods for market lifecycle."""

    @staticmethod
    def create_market(
        market_id: str,
        theatre_id: str,
        b: float,
        n_outcomes: int,
        outcome_labels: list[str],
        fee_schedule: FeeSchedule | None = None,
    ) -> MarketState:
        """Factory — creates a MarketState in CREATED phase.

        Validates: b > 0, n_outcomes >= 2, len(outcome_labels) == n_outcomes.
        Initialises x to [0.0] * n_outcomes.
        """
        if b <= 0:
            raise InvalidMarketParameters(f"b must be positive, got {b}")
        if n_outcomes < 2:
            raise InvalidMarketParameters(
                f"n_outcomes must be >= 2, got {n_outcomes}"
            )
        if len(outcome_labels) != n_outcomes:
            raise InvalidMarketParameters(
                f"outcome_labels length ({len(outcome_labels)}) "
                f"!= n_outcomes ({n_outcomes})"
            )

        return MarketState(
            market_id=market_id,
            theatre_id=theatre_id,
            b=b,
            n_outcomes=n_outcomes,
            outcome_labels=list(outcome_labels),
            x=[0.0] * n_outcomes,
            phase=MarketPhase.CREATED,
            fee_schedule=fee_schedule or FeeSchedule(),
            created_at=datetime.utcnow().isoformat(),
        )

    @staticmethod
    def commit(market: MarketState) -> MarketState:
        """CREATED -> COMMITTED. Computes and stores commitment hash."""
        if market.phase != MarketPhase.CREATED:
            raise InvalidPhaseTransition(
                current=market.phase, target=MarketPhase.COMMITTED
            )
        market.commitment_hash = MarketCommitment.compute_hash(market)
        market.phase = MarketPhase.COMMITTED
        market.committed_at = datetime.utcnow().isoformat()
        return market

    @staticmethod
    def open_trading(market: MarketState) -> MarketState:
        """COMMITTED -> TRADING."""
        if market.phase != MarketPhase.COMMITTED:
            raise InvalidPhaseTransition(
                current=market.phase, target=MarketPhase.TRADING
            )
        market.phase = MarketPhase.TRADING
        market.trading_opened_at = datetime.utcnow().isoformat()
        return market

    @staticmethod
    def begin_resolution(
        market: MarketState, winning_outcome: int
    ) -> MarketState:
        """TRADING -> RESOLVING. Records winning outcome."""
        if market.phase != MarketPhase.TRADING:
            raise InvalidPhaseTransition(
                current=market.phase, target=MarketPhase.RESOLVING
            )
        if not (0 <= winning_outcome < market.n_outcomes):
            raise InvalidMarketParameters(
                f"winning_outcome must be in [0, {market.n_outcomes}), "
                f"got {winning_outcome}"
            )
        market.resolved_outcome = winning_outcome
        market.phase = MarketPhase.RESOLVING
        market.resolved_at = datetime.utcnow().isoformat()
        return market

    @staticmethod
    def settle(market: MarketState) -> MarketState:
        """RESOLVING -> SETTLED."""
        if market.phase != MarketPhase.RESOLVING:
            raise InvalidPhaseTransition(
                current=market.phase, target=MarketPhase.SETTLED
            )
        market.phase = MarketPhase.SETTLED
        market.settled_at = datetime.utcnow().isoformat()
        return market
