"""Market Status Snapshot — assembles live state from all engines.

Single function to query all engine state for a theatre.
Used by MCP echelon_status tool.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.engines.butterfly import ButterflyEngine
from backend.engines.heartbeat import HeartbeatScheduler
from backend.engines.paradox import ParadoxEngine
from backend.market.lmsr import LMSREngine
from backend.market.state import MarketState


@dataclass
class MarketStatusSnapshot:
    """Complete market status at a point in time."""

    theatre_id: str
    market_phase: str
    current_prices: list[float]
    total_trades: int
    timeline_stability: float
    logic_gap_status: str | None
    logic_gap_value: float | None
    heartbeat_ticks: dict[str, int]
    commitment_hash: str
    on_chain: bool


def market_status_snapshot(
    theatre_id: str,
    market: MarketState,
    butterfly: ButterflyEngine,
    heartbeat: HeartbeatScheduler,
    paradox: ParadoxEngine | None = None,
    commitment_hash: str = "",
    on_chain: bool = False,
) -> MarketStatusSnapshot:
    """Assemble live market state from all engines into a single snapshot."""
    # Market prices from LMSR
    prices = list(LMSREngine.prices(market.x, market.b))

    # Timeline state from Butterfly
    state = butterfly.get_timeline_state(theatre_id)

    # Logic Gap from Paradox (if wired)
    logic_gap_status = None
    logic_gap_value = None
    if paradox is not None:
        reading = paradox.get_last_reading(theatre_id)
        if reading is not None:
            logic_gap_status = reading.status.value
            logic_gap_value = reading.logic_gap

    # Heartbeat tick counts
    ticks = heartbeat.tick_count(theatre_id)

    return MarketStatusSnapshot(
        theatre_id=theatre_id,
        market_phase=market.phase.value,
        current_prices=prices,
        total_trades=state.flap_count,
        timeline_stability=state.stability,
        logic_gap_status=logic_gap_status,
        logic_gap_value=logic_gap_value,
        heartbeat_ticks=ticks,
        commitment_hash=commitment_hash,
        on_chain=on_chain,
    )
