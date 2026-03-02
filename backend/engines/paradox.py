"""Paradox Engine — self-policing integrity layer.

Scans for Logic Gap divergence between market prices and reality signals.
Four modes: disabled, enabled, advisory, circuit_breaker.
Actions: WARN, TRADING_PAUSE, FORCED_RESOLUTION.
Activation gates use latch semantics — once satisfied, never reverts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.engines.butterfly import ButterflyEngine, WingFlap, WingFlapType
from backend.engines.logic_gap import LogicGapCalculator, LogicGapReading
from backend.engines.reality_signal import RealitySignalProvider


class ParadoxMode(str, Enum):
    """Operating modes for the Paradox Engine."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    ADVISORY = "advisory"
    CIRCUIT_BREAKER = "circuit_breaker"


class ParadoxAction(str, Enum):
    """Actions triggered by threshold crossings."""

    WARN = "warn"
    TRADING_PAUSE = "trading_pause"
    FORCED_RESOLUTION = "forced_resolution"


@dataclass
class ParadoxConfig:
    """Committed configuration for the Paradox Engine."""

    mode: ParadoxMode = ParadoxMode.DISABLED
    inquiry_class: str = "binary"
    warn_threshold: float | None = 0.20
    breach_threshold: float | None = 0.40
    critical_threshold: float = 0.60
    activation_gate: dict = field(default_factory=lambda: {"type": "none"})
    logic_gap_source: str = "deterministic"
    smoothing_window_s: float = 60.0

    def to_commitment_dict(self) -> dict:
        """Serialisable dict for inclusion in EngineConfig commitment hash."""
        return {
            "mode": self.mode.value,
            "inquiry_class": self.inquiry_class,
            "warn_threshold": self.warn_threshold,
            "breach_threshold": self.breach_threshold,
            "critical_threshold": self.critical_threshold,
            "activation_gate": self.activation_gate,
            "logic_gap_source": self.logic_gap_source,
            "smoothing_window_s": self.smoothing_window_s,
        }


@dataclass
class ParadoxRuntimeState:
    """Per-theatre runtime state for the Paradox Engine."""

    activation_gate_satisfied: bool = False  # latch: once True, never reverts
    last_reading: LogicGapReading | None = None
    scan_count: int = 0


class ParadoxEngine:
    """Self-policing integrity layer for market-reality divergence."""

    def __init__(
        self,
        config: ParadoxConfig,
        butterfly: ButterflyEngine,
        logic_gap_calc: LogicGapCalculator,
        reality_provider: RealitySignalProvider,
    ) -> None:
        self._config = config
        self._butterfly = butterfly
        self._logic_gap_calc = logic_gap_calc
        self._reality_provider = reality_provider
        self._runtime: dict[str, ParadoxRuntimeState] = {}

    def scan(self, theatre_id: str) -> LogicGapReading | None:
        """Scan for Logic Gap divergence. Returns reading or None if disabled/gated."""
        if self._config.mode == ParadoxMode.DISABLED:
            return None

        runtime = self._get_or_create_runtime(theatre_id)

        # Check activation gate (latch semantics)
        if not self.check_activation_gate(theatre_id):
            return None

        # Get reality signal
        signal = self._reality_provider.get_signal(theatre_id)

        # Compute Logic Gap
        reading = self._logic_gap_calc.compute(theatre_id, signal.p_reality)

        # Store in runtime
        runtime.last_reading = reading
        runtime.scan_count += 1

        return reading

    def evaluate_thresholds(
        self, reading: LogicGapReading
    ) -> ParadoxAction | None:
        """Evaluate Logic Gap reading against mode-dependent thresholds.

        Returns highest applicable action, or None if below all thresholds.
        Evaluation order: critical first, then breach, then warn.
        """
        mode = self._config.mode
        gap = reading.logic_gap

        if mode == ParadoxMode.DISABLED:
            return None

        if mode == ParadoxMode.ADVISORY:
            # Advisory mode: all thresholds produce WARN only
            if (
                gap >= self._config.critical_threshold
                or (self._config.breach_threshold is not None
                    and gap >= self._config.breach_threshold)
                or (self._config.warn_threshold is not None
                    and gap >= self._config.warn_threshold)
            ):
                return ParadoxAction.WARN
            return None

        if mode == ParadoxMode.CIRCUIT_BREAKER:
            # Circuit breaker mode: only critical threshold
            if gap >= self._config.critical_threshold:
                return ParadoxAction.FORCED_RESOLUTION
            return None

        # ENABLED mode: check highest severity first
        if gap >= self._config.critical_threshold:
            return ParadoxAction.FORCED_RESOLUTION
        if (self._config.breach_threshold is not None
                and gap >= self._config.breach_threshold):
            return ParadoxAction.TRADING_PAUSE
        if (self._config.warn_threshold is not None
                and gap >= self._config.warn_threshold):
            return ParadoxAction.WARN
        return None

    def check_activation_gate(self, theatre_id: str) -> bool:
        """Check gate conditions. LATCH: once True, stays True forever."""
        runtime = self._get_or_create_runtime(theatre_id)

        # Latch: if already satisfied, return True immediately
        if runtime.activation_gate_satisfied:
            return True

        gate = self._config.activation_gate
        gate_type = gate.get("type", "none")

        if gate_type == "none":
            satisfied = True
        elif gate_type == "min_observations":
            satisfied = runtime.scan_count >= gate.get("value", 0)
        elif gate_type == "min_evidence_completeness":
            # Placeholder — evidence completeness not tracked in Sprint 2
            satisfied = False
        elif gate_type == "min_time_elapsed":
            # Placeholder — time tracking not wired in Sprint 2
            satisfied = False
        else:
            # Unknown gate type — default to not satisfied
            satisfied = False

        if satisfied:
            runtime.activation_gate_satisfied = True

        return satisfied

    def execute_action(
        self, action: ParadoxAction, theatre_id: str
    ) -> WingFlap:
        """Execute a Paradox action. Returns PARADOX Wing Flap.

        WARN: impact -0.10
        TRADING_PAUSE: impact -0.20
        FORCED_RESOLUTION: impact -0.30
        """
        impact_map = {
            ParadoxAction.WARN: -0.10,
            ParadoxAction.TRADING_PAUSE: -0.20,
            ParadoxAction.FORCED_RESOLUTION: -0.30,
        }
        impact = impact_map[action]

        runtime = self._get_or_create_runtime(theatre_id)
        reading = runtime.last_reading

        return self._butterfly.record_flap(
            flap_type=WingFlapType.PARADOX,
            theatre_id=theatre_id,
            agent_id=None,
            impact=impact,
            trigger_detail={
                "action": action.value,
                "logic_gap": reading.logic_gap if reading else None,
                "logic_gap_status": reading.status.value if reading else None,
                "mode": self._config.mode.value,
            },
        )

    def get_last_reading(self, theatre_id: str) -> LogicGapReading | None:
        """Get most recent Logic Gap reading for a theatre."""
        runtime = self._runtime.get(theatre_id)
        return runtime.last_reading if runtime else None

    def to_commitment_dict(self) -> dict:
        """Serialisable dict for inclusion in commitment hash."""
        return {
            "mode": self._config.mode.value,
            "inquiry_class": self._config.inquiry_class,
            "warn_threshold": self._config.warn_threshold,
            "breach_threshold": self._config.breach_threshold,
            "critical_threshold": self._config.critical_threshold,
            "activation_gate": self._config.activation_gate,
            "logic_gap_source": self._config.logic_gap_source,
            "smoothing_window_s": self._config.smoothing_window_s,
        }

    def _get_or_create_runtime(self, theatre_id: str) -> ParadoxRuntimeState:
        """Get existing runtime state or create default."""
        if theatre_id not in self._runtime:
            self._runtime[theatre_id] = ParadoxRuntimeState()
        return self._runtime[theatre_id]
