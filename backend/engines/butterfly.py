"""Butterfly Engine — causal state transition recording via Wing Flaps.

Every action that modifies market state passes through the Butterfly Engine.
Stability is clamped at write time: post_stability = clamp(pre + impact, 0, 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WingFlapType(str, Enum):
    """Types of causal state transitions.

    Kept in sync with backend.database.models.WingFlapType.
    """

    # --- Original 010b types ---
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"  # schema only — seed fixtures
    PARADOX = "PARADOX"
    ENTROPY = "ENTROPY"
    FOUNDER_YIELD = "FOUNDER_YIELD"
    # --- 016 Coherence Lock additions ---
    MIRROR_SYNC = "MIRROR_SYNC"
    MIRROR_TRADE = "MIRROR_TRADE"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    COUNTER_SIGNAL = "COUNTER_SIGNAL"
    CORROBORATION = "CORROBORATION"
    DETONATION = "DETONATION"
    FORK_SPAWN = "FORK_SPAWN"
    STOP_CONDITION = "STOP_CONDITION"
    CERTIFICATE = "CERTIFICATE"


class FlapDirection(str, Enum):
    """Direction of a Wing Flap's stability impact."""
    STABILISE = "STABILISE"
    DESTABILISE = "DESTABILISE"
    NEUTRAL = "NEUTRAL"


@dataclass
class WingFlap:
    """Record of a single causal state transition."""

    flap_id: str
    theatre_id: str
    flap_type: WingFlapType
    agent_id: str | None  # None for system flaps (ENTROPY, RIPPLE)
    stability_impact: float  # signed: positive = stabilising
    pre_stability: float
    post_stability: float
    direction: FlapDirection  # STABILISE / DESTABILISE / NEUTRAL
    trigger_detail: dict
    timestamp: str


@dataclass
class TimelineState:
    """Mutable per-Theatre timeline state."""

    theatre_id: str
    stability: float = 1.0  # 0.0–1.0, starts at 1.0
    volume: float = 0.0  # cumulative trade volume (abs cost)
    flap_count: int = 0
    founders_yield_accrued: float = 0.0


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


class ButterflyEngine:
    """Records causal state transitions. Tracks TimelineState per Theatre."""

    def __init__(self) -> None:
        self._timelines: dict[str, TimelineState] = {}
        self._flaps: dict[str, list[WingFlap]] = {}
        self._flap_counter: int = 0

    def record_flap(
        self,
        flap_type: WingFlapType,
        theatre_id: str,
        agent_id: str | None,
        impact: float,
        trigger_detail: dict,
    ) -> WingFlap:
        """Record a Wing Flap. Updates TimelineState. Returns the flap."""
        timeline = self._get_or_create_timeline(theatre_id)

        pre_stability = timeline.stability
        post_stability = _clamp(pre_stability + impact, 0.0, 1.0)

        timeline.stability = post_stability
        timeline.flap_count += 1

        # Track trade volume
        if flap_type == WingFlapType.TRADE and "cost" in trigger_detail:
            timeline.volume += abs(trigger_detail["cost"])

        # Derive direction from impact
        if impact > 0:
            direction = FlapDirection.STABILISE
        elif impact < 0:
            direction = FlapDirection.DESTABILISE
        else:
            direction = FlapDirection.NEUTRAL

        self._flap_counter += 1
        flap = WingFlap(
            flap_id=f"flp_{self._flap_counter:06d}",
            theatre_id=theatre_id,
            flap_type=flap_type,
            agent_id=agent_id,
            stability_impact=impact,
            pre_stability=pre_stability,
            post_stability=post_stability,
            direction=direction,
            trigger_detail=trigger_detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if theatre_id not in self._flaps:
            self._flaps[theatre_id] = []
        self._flaps[theatre_id].append(flap)

        return flap

    def get_timeline_state(self, theatre_id: str) -> TimelineState:
        """Get timeline state for a Theatre. Creates default if not exists."""
        return self._get_or_create_timeline(theatre_id)

    def get_flaps(self, theatre_id: str) -> list[WingFlap]:
        """Get all Wing Flaps for a Theatre (audit trail)."""
        return list(self._flaps.get(theatre_id, []))

    def compute_founders_yield(self, theatre_id: str) -> float:
        """Founder's Yield = stability × volume × 0.005."""
        timeline = self._get_or_create_timeline(theatre_id)
        return timeline.stability * timeline.volume * 0.005

    def compute_fork_divergence(
        self, anchor_theatre_id: str, fork_theatre_id: str
    ) -> float:
        """Compute |anchor.stability - fork.stability| as divergence metric.

        Returns 0.0 if either theatre has no recorded flaps.
        """
        anchor = self._get_or_create_timeline(anchor_theatre_id)
        fork = self._get_or_create_timeline(fork_theatre_id)
        return abs(anchor.stability - fork.stability)

    def _get_or_create_timeline(self, theatre_id: str) -> TimelineState:
        """Get existing timeline or create default."""
        if theatre_id not in self._timelines:
            self._timelines[theatre_id] = TimelineState(theatre_id=theatre_id)
        return self._timelines[theatre_id]
