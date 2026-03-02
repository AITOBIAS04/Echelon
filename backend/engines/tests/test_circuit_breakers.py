"""Circuit breaker tests — action determinism, mode overrides."""
from __future__ import annotations

import pytest

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.logic_gap import LogicGapCalculator
from backend.engines.paradox import (
    ParadoxAction,
    ParadoxConfig,
    ParadoxEngine,
    ParadoxMode,
)
from backend.engines.reality_signal import StubRealityProvider


def _make_system(
    mode: ParadoxMode,
    p_reality: float,
    p_market: float,
) -> tuple[ParadoxEngine, ButterflyEngine]:
    """Create Paradox system with a single price observation."""
    config = ParadoxConfig(
        mode=mode,
        warn_threshold=0.20,
        breach_threshold=0.40,
        critical_threshold=0.60,
    )
    butterfly = ButterflyEngine()
    calc = LogicGapCalculator()
    calc.record_price("t1", p_market, timestamp_s=100.0)
    provider = StubRealityProvider(p_reality=p_reality)
    engine = ParadoxEngine(config, butterfly, calc, provider)
    return engine, butterfly


class TestActionDeterminism:
    """Each action produces exactly the expected impact."""

    def test_warn_impact_minus_010(self) -> None:
        engine, butterfly = _make_system(ParadoxMode.ENABLED, 0.30, 0.50)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.WARN, "t1")
        assert flap.stability_impact == -0.10
        assert flap.flap_type == WingFlapType.PARADOX

    def test_trading_pause_impact_minus_020(self) -> None:
        engine, butterfly = _make_system(ParadoxMode.ENABLED, 0.10, 0.50)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.TRADING_PAUSE, "t1")
        assert flap.stability_impact == -0.20

    def test_forced_resolution_impact_minus_030(self) -> None:
        engine, butterfly = _make_system(ParadoxMode.ENABLED, 0.05, 0.70)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.FORCED_RESOLUTION, "t1")
        assert flap.stability_impact == -0.30


class TestModeOverrides:
    """Mode-dependent action filtering."""

    def test_advisory_never_pauses(self) -> None:
        """Advisory mode: breach-level gap still produces WARN, not TRADING_PAUSE."""
        engine, _ = _make_system(ParadoxMode.ADVISORY, 0.10, 0.50)  # gap=0.40
        reading = engine.scan("t1")
        action = engine.evaluate_thresholds(reading)
        assert action == ParadoxAction.WARN

    def test_advisory_never_force_resolves(self) -> None:
        """Advisory mode: critical gap still produces WARN, not FORCED_RESOLUTION."""
        engine, _ = _make_system(ParadoxMode.ADVISORY, 0.05, 0.70)  # gap=0.65
        reading = engine.scan("t1")
        action = engine.evaluate_thresholds(reading)
        assert action == ParadoxAction.WARN

    def test_circuit_breaker_skips_warn_and_breach(self) -> None:
        """Circuit breaker mode: danger gap (below critical) returns None."""
        engine, _ = _make_system(ParadoxMode.CIRCUIT_BREAKER, 0.10, 0.50)  # gap=0.40
        reading = engine.scan("t1")
        action = engine.evaluate_thresholds(reading)
        assert action is None

    def test_circuit_breaker_only_fires_at_critical(self) -> None:
        """Circuit breaker mode: critical gap returns FORCED_RESOLUTION."""
        engine, _ = _make_system(ParadoxMode.CIRCUIT_BREAKER, 0.05, 0.70)  # gap=0.65
        reading = engine.scan("t1")
        action = engine.evaluate_thresholds(reading)
        assert action == ParadoxAction.FORCED_RESOLUTION

    def test_disabled_mode_scan_returns_none(self) -> None:
        engine, _ = _make_system(ParadoxMode.DISABLED, 0.50, 0.50)
        assert engine.scan("t1") is None

    def test_enabled_full_escalation(self) -> None:
        """Enabled mode: each threshold level returns the correct action."""
        # WARN (gap=0.20)
        engine, _ = _make_system(ParadoxMode.ENABLED, 0.30, 0.50)
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.WARN

        # TRADING_PAUSE (gap=0.40)
        engine2, _ = _make_system(ParadoxMode.ENABLED, 0.10, 0.50)
        reading2 = engine2.scan("t1")
        assert engine2.evaluate_thresholds(reading2) == ParadoxAction.TRADING_PAUSE

        # FORCED_RESOLUTION (gap=0.65)
        engine3, _ = _make_system(ParadoxMode.ENABLED, 0.05, 0.70)
        reading3 = engine3.scan("t1")
        assert engine3.evaluate_thresholds(reading3) == ParadoxAction.FORCED_RESOLUTION
