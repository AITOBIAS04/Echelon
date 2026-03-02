"""Paradox Engine tests — threshold evaluation, activation gates, modes."""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.logic_gap import LogicGapCalculator, LogicGapStatus
from backend.engines.paradox import (
    ParadoxAction,
    ParadoxConfig,
    ParadoxEngine,
    ParadoxMode,
)
from backend.engines.reality_signal import StubRealityProvider

TOLERANCE = 1e-9


def _make_paradox(
    mode: ParadoxMode = ParadoxMode.ENABLED,
    p_reality: float = 0.5,
    activation_gate: dict | None = None,
) -> tuple[ParadoxEngine, ButterflyEngine, LogicGapCalculator]:
    """Create a wired Paradox Engine for testing."""
    config = ParadoxConfig(
        mode=mode,
        warn_threshold=0.20,
        breach_threshold=0.40,
        critical_threshold=0.60,
        activation_gate=activation_gate or {"type": "none"},
    )
    butterfly = ButterflyEngine()
    calc = LogicGapCalculator(smoothing_window_s=60.0)
    provider = StubRealityProvider(p_reality=p_reality)
    engine = ParadoxEngine(config, butterfly, calc, provider)
    return engine, butterfly, calc


class TestScan:
    """Scan for Logic Gap."""

    def test_disabled_returns_none(self) -> None:
        engine, _, _ = _make_paradox(mode=ParadoxMode.DISABLED)
        assert engine.scan("t1") is None

    def test_enabled_returns_reading(self) -> None:
        engine, _, calc = _make_paradox()
        calc.record_price("t1", 0.70, timestamp_s=100.0)
        reading = engine.scan("t1")
        assert reading is not None
        assert abs(reading.logic_gap - 0.20) < TOLERANCE

    def test_scan_increments_count(self) -> None:
        engine, _, calc = _make_paradox()
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        engine.scan("t1")
        engine.scan("t1")
        runtime = engine._runtime["t1"]
        assert runtime.scan_count == 2

    def test_scan_stores_last_reading(self) -> None:
        engine, _, calc = _make_paradox()
        calc.record_price("t1", 0.60, timestamp_s=100.0)
        reading = engine.scan("t1")
        assert engine.get_last_reading("t1") is reading


class TestThresholds:
    """Threshold evaluation in ENABLED mode."""

    def test_healthy_no_action(self) -> None:
        engine, _, calc = _make_paradox(p_reality=0.55)
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) is None

    def test_warn_at_20(self) -> None:
        engine, _, calc = _make_paradox(p_reality=0.30)
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.20
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.WARN

    def test_trading_pause_at_40(self) -> None:
        engine, _, calc = _make_paradox(p_reality=0.10)
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.40
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.TRADING_PAUSE

    def test_forced_resolution_at_60(self) -> None:
        engine, _, calc = _make_paradox(p_reality=0.05)
        calc.record_price("t1", 0.70, timestamp_s=100.0)  # gap=0.65
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.FORCED_RESOLUTION

    def test_highest_severity_wins(self) -> None:
        # gap=0.65 crosses all three thresholds, should return highest
        engine, _, calc = _make_paradox(p_reality=0.05)
        calc.record_price("t1", 0.70, timestamp_s=100.0)
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.FORCED_RESOLUTION


class TestModes:
    """Mode-dependent threshold behaviour."""

    def test_advisory_caps_at_warn(self) -> None:
        engine, _, calc = _make_paradox(
            mode=ParadoxMode.ADVISORY, p_reality=0.05,
        )
        calc.record_price("t1", 0.70, timestamp_s=100.0)  # gap=0.65
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.WARN

    def test_advisory_below_warn_returns_none(self) -> None:
        engine, _, calc = _make_paradox(
            mode=ParadoxMode.ADVISORY, p_reality=0.55,
        )
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.05
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) is None

    def test_circuit_breaker_only_critical(self) -> None:
        engine, _, calc = _make_paradox(
            mode=ParadoxMode.CIRCUIT_BREAKER, p_reality=0.10,
        )
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.40 (DANGER)
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) is None  # below critical

    def test_circuit_breaker_fires_at_critical(self) -> None:
        engine, _, calc = _make_paradox(
            mode=ParadoxMode.CIRCUIT_BREAKER, p_reality=0.05,
        )
        calc.record_price("t1", 0.70, timestamp_s=100.0)  # gap=0.65
        reading = engine.scan("t1")
        assert engine.evaluate_thresholds(reading) == ParadoxAction.FORCED_RESOLUTION


class TestActivationGate:
    """Activation gate latch semantics."""

    def test_none_gate_always_satisfied(self) -> None:
        engine, _, calc = _make_paradox(activation_gate={"type": "none"})
        assert engine.check_activation_gate("t1") is True

    def test_min_observations_gate_blocks_initially(self) -> None:
        engine, _, calc = _make_paradox(
            activation_gate={"type": "min_observations", "value": 3},
        )
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        assert engine.scan("t1") is None  # blocked, scan_count=0

    def test_min_observations_gate_satisfied_after_scans(self) -> None:
        engine, _, calc = _make_paradox(
            activation_gate={"type": "min_observations", "value": 2},
        )
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        # Need to manually satisfy the gate by incrementing scan_count
        runtime = engine._get_or_create_runtime("t1")
        runtime.scan_count = 2  # simulate previous scans
        reading = engine.scan("t1")
        assert reading is not None

    def test_latch_stays_true_once_satisfied(self) -> None:
        engine, _, calc = _make_paradox(
            activation_gate={"type": "min_observations", "value": 1},
        )
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        runtime = engine._get_or_create_runtime("t1")
        runtime.scan_count = 1
        engine.scan("t1")  # satisfies gate
        assert runtime.activation_gate_satisfied is True
        # Subsequent scans should pass even if scan_count were reset
        reading = engine.scan("t1")
        assert reading is not None


class TestExecuteAction:
    """Action execution and Wing Flap generation."""

    def test_warn_produces_paradox_flap(self) -> None:
        engine, butterfly, calc = _make_paradox()
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.WARN, "t1")
        assert flap.flap_type == WingFlapType.PARADOX
        assert flap.stability_impact == -0.10

    def test_trading_pause_impact(self) -> None:
        engine, butterfly, calc = _make_paradox()
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.TRADING_PAUSE, "t1")
        assert flap.stability_impact == -0.20

    def test_forced_resolution_impact(self) -> None:
        engine, butterfly, calc = _make_paradox()
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.FORCED_RESOLUTION, "t1")
        assert flap.stability_impact == -0.30

    def test_trigger_detail_contains_action(self) -> None:
        engine, butterfly, calc = _make_paradox()
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        engine.scan("t1")
        flap = engine.execute_action(ParadoxAction.WARN, "t1")
        assert flap.trigger_detail["action"] == "warn"
        assert flap.trigger_detail["mode"] == "enabled"


class TestCommitmentDict:
    """Paradox config in commitment hash."""

    def test_commitment_dict_keys(self) -> None:
        engine, _, _ = _make_paradox()
        d = engine.to_commitment_dict()
        assert d["mode"] == "enabled"
        assert d["critical_threshold"] == 0.60
        assert d["warn_threshold"] == 0.20
        assert d["breach_threshold"] == 0.40
        assert d["smoothing_window_s"] == 60.0
