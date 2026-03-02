"""Entropy Engine tests — decay rates, multiplier scaling, boundary conditions."""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.config import EntropyConfig
from backend.engines.entropy import EntropyEngine

TOLERANCE = 1e-9


def _make_entropy(base_decay: float = 0.01) -> tuple[EntropyEngine, ButterflyEngine]:
    config = EntropyConfig(
        base_decay_rate=base_decay,
        stressed_multiplier=1.5,
        danger_multiplier=2.0,
        critical_multiplier=3.0,
    )
    butterfly = ButterflyEngine()
    return EntropyEngine(config, butterfly), butterfly


class TestDecayRates:
    """Decay rate computation."""

    def test_base_decay_rate_healthy(self) -> None:
        engine, _ = _make_entropy()
        assert engine.get_effective_decay_rate("healthy") == 0.01

    def test_stressed_multiplier(self) -> None:
        engine, _ = _make_entropy()
        assert abs(engine.get_effective_decay_rate("stressed") - 0.015) < TOLERANCE

    def test_danger_multiplier(self) -> None:
        engine, _ = _make_entropy()
        assert abs(engine.get_effective_decay_rate("danger") - 0.02) < TOLERANCE

    def test_critical_multiplier(self) -> None:
        engine, _ = _make_entropy()
        assert abs(engine.get_effective_decay_rate("critical") - 0.03) < TOLERANCE

    def test_unknown_status_defaults_to_base(self) -> None:
        engine, _ = _make_entropy()
        assert engine.get_effective_decay_rate("banana") == 0.01


class TestEntropyTick:
    """Entropy tick execution."""

    def test_tick_produces_entropy_wing_flap(self) -> None:
        engine, butterfly = _make_entropy()
        flap = engine.tick("t1")
        assert flap.flap_type == WingFlapType.ENTROPY
        assert flap.agent_id is None
        assert flap.stability_impact == -0.01

    def test_tick_decrements_stability(self) -> None:
        engine, butterfly = _make_entropy()
        engine.tick("t1")
        state = butterfly.get_timeline_state("t1")
        assert abs(state.stability - 0.99) < TOLERANCE

    def test_tick_with_critical_status(self) -> None:
        engine, butterfly = _make_entropy()
        flap = engine.tick("t1", "critical")
        assert abs(flap.stability_impact - (-0.03)) < TOLERANCE

    def test_decay_at_zero_stays_zero(self) -> None:
        engine, butterfly = _make_entropy(base_decay=0.5)
        # Drive stability to 0
        engine.tick("t1")  # 1.0 → 0.5
        engine.tick("t1")  # 0.5 → 0.0
        engine.tick("t1")  # 0.0 → still 0.0
        state = butterfly.get_timeline_state("t1")
        assert state.stability == 0.0

    def test_multiple_ticks_accumulate(self) -> None:
        engine, butterfly = _make_entropy()
        for _ in range(10):
            engine.tick("t1")
        state = butterfly.get_timeline_state("t1")
        assert abs(state.stability - 0.90) < TOLERANCE
