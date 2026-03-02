"""Logic Gap Calculator — market vs reality divergence measurement.

Computes abs(p_market - p_reality) with trailing-window smoothing for p_market.
Classifies gap into four severity tiers: healthy, stressed, danger, critical.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class LogicGapStatus(str, Enum):
    """Severity classification of the market-reality divergence."""

    HEALTHY = "healthy"        # < 20%
    STRESSED = "stressed"      # 20-40%
    DANGER = "danger"          # 40-60%
    CRITICAL = "critical"      # >= 60%


@dataclass
class LogicGapReading:
    """Single snapshot of the Logic Gap measurement."""

    theatre_id: str
    p_market: float
    p_reality: float
    logic_gap: float           # abs(p_market - p_reality)
    gap_direction: float       # signed: p_market - p_reality
    status: LogicGapStatus
    smoothing_window_s: float
    timestamp: str


class LogicGapCalculator:
    """Computes Logic Gap from smoothed market price vs reality signal."""

    def __init__(self, smoothing_window_s: float = 60.0) -> None:
        self._smoothing_window_s = smoothing_window_s
        self._price_history: dict[str, list[tuple[float, float]]] = {}
        # theatre_id → [(timestamp_s, p_market), ...]

    def record_price(
        self, theatre_id: str, p_market: float, timestamp_s: float
    ) -> None:
        """Append price observation. Prune entries older than window."""
        if theatre_id not in self._price_history:
            self._price_history[theatre_id] = []
        history = self._price_history[theatre_id]
        history.append((timestamp_s, p_market))
        # Prune entries outside the window
        cutoff = timestamp_s - self._smoothing_window_s
        self._price_history[theatre_id] = [
            (ts, p) for ts, p in history if ts >= cutoff
        ]

    def get_smoothed_p_market(self, theatre_id: str) -> float:
        """Simple average over trailing window. Falls back to latest if < 2."""
        history = self._price_history.get(theatre_id, [])
        if not history:
            return 0.5  # default midpoint if no observations
        if len(history) == 1:
            return history[0][1]
        total = sum(p for _, p in history)
        return total / len(history)

    def compute(self, theatre_id: str, p_reality: float) -> LogicGapReading:
        """Compute Logic Gap reading from smoothed p_market and p_reality."""
        p_market = self.get_smoothed_p_market(theatre_id)
        logic_gap = abs(p_market - p_reality)
        gap_direction = p_market - p_reality
        status = self.classify(logic_gap)

        return LogicGapReading(
            theatre_id=theatre_id,
            p_market=p_market,
            p_reality=p_reality,
            logic_gap=logic_gap,
            gap_direction=gap_direction,
            status=status,
            smoothing_window_s=self._smoothing_window_s,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def classify(logic_gap: float) -> LogicGapStatus:
        """Classify Logic Gap magnitude into severity tier."""
        if logic_gap < 0.20:
            return LogicGapStatus.HEALTHY
        if logic_gap < 0.40:
            return LogicGapStatus.STRESSED
        if logic_gap < 0.60:
            return LogicGapStatus.DANGER
        return LogicGapStatus.CRITICAL
