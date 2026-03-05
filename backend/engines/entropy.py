"""Entropy Engine — temporal decay of timeline stability.

Runs on ENTROPY heartbeat tick (60s cadence). Decay rate scales with
Logic Gap reading. Sprint 1 defaults to "healthy".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.engines.butterfly import ButterflyEngine, WingFlap, WingFlapType
from backend.engines.config import EntropyConfig


@dataclass
class LogicGapReading:
    """Structured Logic Gap measurement from OSINT evidence engine.

    Attributes:
        status: One of "healthy", "stressed", "danger", "critical".
        magnitude: Raw gap value 0.0–1.0 (0 = perfect alignment).
    """
    status: str = "healthy"
    magnitude: float = 0.0


# Named thresholds for status → multiplier (config values injected at init)
_STATUS_MAP = {
    "healthy",
    "stressed",
    "danger",
    "critical",
}


class EntropyEngine:
    """Temporal decay of timeline stability."""

    def __init__(self, config: EntropyConfig, butterfly: ButterflyEngine) -> None:
        self._config = config
        self._butterfly = butterfly

    def tick(
        self,
        theatre_id: str,
        reading: Optional[LogicGapReading] = None,
        *,
        # Legacy convenience — will be removed in 017
        logic_gap_status: str = "healthy",
    ) -> WingFlap:
        """Apply decay to timeline stability. Returns ENTROPY WingFlap.

        Accepts either a ``LogicGapReading`` (preferred) or a plain string
        ``logic_gap_status`` for backwards compatibility.
        """
        if reading is not None:
            # Support legacy callers passing a string as positional arg
            if isinstance(reading, str):
                status = reading
                reading = None  # clear so magnitude defaults to 0.0
            else:
                status = reading.status
        else:
            status = logic_gap_status

        rate = self.get_effective_decay_rate(status)
        impact = -rate  # always negative — decay is destabilising

        return self._butterfly.record_flap(
            flap_type=WingFlapType.ENTROPY,
            theatre_id=theatre_id,
            agent_id=None,
            impact=impact,
            trigger_detail={
                "logic_gap_status": status,
                "logic_gap_magnitude": reading.magnitude if reading else 0.0,
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
