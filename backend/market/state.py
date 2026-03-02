"""Market state data structures — MarketPhase, FeeSchedule, MarketState."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MarketPhase(Enum):
    """Lifecycle phases for a market. Forward-only transitions."""

    CREATED = "CREATED"
    COMMITTED = "COMMITTED"
    TRADING = "TRADING"
    RESOLVING = "RESOLVING"
    SETTLED = "SETTLED"


@dataclass
class FeeSchedule:
    """Committed fee structure. Immutable after market commitment.

    Both fields default to 0 for 010a. Schema reserved for 010b+.
    """

    trade_fee_bps: int = 0
    resolution_fee_bps: int = 0


@dataclass
class MarketState:
    """Mutable state container for a single market instance."""

    market_id: str
    theatre_id: str
    b: float
    n_outcomes: int
    outcome_labels: list[str]
    x: list[float] = field(default_factory=list)
    phase: MarketPhase = MarketPhase.CREATED
    fee_schedule: FeeSchedule = field(default_factory=FeeSchedule)
    commitment_hash: str | None = None
    resolved_outcome: int | None = None
    created_at: str = ""
    committed_at: str | None = None
    trading_opened_at: str | None = None
    resolved_at: str | None = None
    settled_at: str | None = None
