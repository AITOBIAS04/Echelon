"""Entropy Engine — temporal decay of timeline stability.

Runs on ENTROPY heartbeat tick (60s cadence). Decay rate scales with
Logic Gap status. Sprint 1 defaults to "healthy".
"""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlap, WingFlapType
from backend.engines.config import EntropyConfig

_MULTIPLIERS = {
    "healthy": 1.0,
    "stressed": None,  # filled from config
    "danger": None,
    "critical": None,
}


class EntropyEngine:
    """Temporal decay of timeline stability."""

    def __init__(self, config: EntropyConfig, butterfly: ButterflyEngine) -> None:
        self._config = config
        self._butterfly = butterfly

    def tick(
        self, theatre_id: str, logic_gap_status: str = "healthy"
    ) -> WingFlap:
        """Apply decay to timeline stability. Returns ENTROPY WingFlap."""
        rate = self.get_effective_decay_rate(logic_gap_status)
        impact = -rate  # always negative — decay is destabilising

        return self._butterfly.record_flap(
            flap_type=WingFlapType.ENTROPY,
            theatre_id=theatre_id,
            agent_id=None,
            impact=impact,
            trigger_detail={
                "logic_gap_status": logic_gap_status,
                "effective_decay_rate": rate,
            },
        )

    def get_effective_decay_rate(self, logic_gap_status: str) -> float:
        """Compute decay rate scaled by Logic Gap status."""
        base = self._config.base_decay_rate
        status = logic_gap_status.lower()

        if status == "healthy":
            return base
        if status == "stressed":
            return base * self._config.stressed_multiplier
        if status == "danger":
            return base * self._config.danger_multiplier
        if status == "critical":
            return base * self._config.critical_multiplier

        # Unknown status — defensive default
        return base
