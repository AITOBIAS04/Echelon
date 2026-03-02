"""Market-specific exceptions."""
from __future__ import annotations

from enum import Enum


class MarketError(Exception):
    """Base exception for all market errors."""


class InvalidPhaseTransition(MarketError):
    """Raised when a market phase transition is not permitted."""

    def __init__(self, current: Enum, target: Enum) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid transition: {current.value} -> {target.value}"
        )


class InvalidMarketParameters(MarketError):
    """Raised when market creation parameters are invalid."""


class ParameterMutationAfterCommit(MarketError):
    """Raised when attempting to modify committed parameters."""


class TradingHalted(MarketError):
    """Raised when a trade is attempted outside the TRADING phase."""

    def __init__(self, current_phase: Enum) -> None:
        self.current_phase = current_phase
        super().__init__(f"Trading halted: market is in {current_phase.value} phase")


class InsufficientBalance(MarketError):
    """Raised when an agent cannot cover the trade cost."""

    def __init__(self, required: float, available: float) -> None:
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient balance: required {required:.4f}, available {available:.4f}"
        )


class InsufficientShares(MarketError):
    """Raised when a sell exceeds the agent's held shares."""

    def __init__(
        self, outcome_index: int, required: float, available: float
    ) -> None:
        self.outcome_index = outcome_index
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient shares at outcome {outcome_index}: "
            f"required {required:.4f}, available {available:.4f}"
        )
