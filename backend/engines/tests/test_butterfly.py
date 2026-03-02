"""Butterfly Engine tests — Wing Flap recording, stability tracking, yield."""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, TimelineState, WingFlapType

TOLERANCE = 1e-9


class TestRecordFlap:
    """Wing Flap recording and stability updates."""

    def test_record_flap_updates_stability(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            WingFlapType.TRADE, "theatre_01", "agent_01", -0.05,
            {"cost": 10.0, "trade_id": "trd_1"},
        )
        assert flap.pre_stability == 1.0
        assert abs(flap.post_stability - 0.95) < TOLERANCE
        assert engine.get_timeline_state("theatre_01").stability == flap.post_stability

    def test_stability_clamped_at_zero(self) -> None:
        engine = ButterflyEngine()
        # Drive stability to near zero
        for _ in range(25):
            engine.record_flap(WingFlapType.ENTROPY, "t1", None, -0.05, {})
        state = engine.get_timeline_state("t1")
        assert state.stability >= 0.0
        # One more big hit
        flap = engine.record_flap(WingFlapType.ENTROPY, "t1", None, -1.0, {})
        assert flap.post_stability == 0.0

    def test_stability_clamped_at_one(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            WingFlapType.SHIELD, "t1", "agent_01", 0.50, {"tier": "hard"},
        )
        assert flap.post_stability == 1.0  # clamped — started at 1.0

    def test_volume_tracks_trade_cost(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(
            WingFlapType.TRADE, "t1", "agent_01", -0.01,
            {"cost": 25.5, "trade_id": "trd_1"},
        )
        engine.record_flap(
            WingFlapType.TRADE, "t1", "agent_01", 0.01,
            {"cost": -10.0, "trade_id": "trd_2"},  # sell (negative cost)
        )
        state = engine.get_timeline_state("t1")
        assert abs(state.volume - 35.5) < TOLERANCE  # abs(25.5) + abs(-10.0)

    def test_non_trade_flap_does_not_add_volume(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(WingFlapType.ENTROPY, "t1", None, -0.01, {})
        state = engine.get_timeline_state("t1")
        assert state.volume == 0.0


class TestFoundersYield:
    """Founder's Yield computation."""

    def test_founders_yield_formula(self) -> None:
        engine = ButterflyEngine()
        # Set up state: stability=0.8, volume=1000
        engine.record_flap(
            WingFlapType.TRADE, "t1", "a1", -0.20,
            {"cost": 1000.0, "trade_id": "trd_1"},
        )
        # stability = 1.0 - 0.20 = 0.80, volume = 1000.0
        expected = 0.80 * 1000.0 * 0.005
        assert abs(engine.compute_founders_yield("t1") - expected) < TOLERANCE

    def test_founders_yield_zero_volume(self) -> None:
        engine = ButterflyEngine()
        assert engine.compute_founders_yield("t1") == 0.0


class TestMultiTheatreIsolation:
    """Separate TimelineState per theatre."""

    def test_multi_theatre_isolation(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(WingFlapType.ENTROPY, "t1", None, -0.10, {})
        engine.record_flap(WingFlapType.ENTROPY, "t2", None, -0.05, {})

        s1 = engine.get_timeline_state("t1")
        s2 = engine.get_timeline_state("t2")

        assert abs(s1.stability - 0.90) < TOLERANCE
        assert abs(s2.stability - 0.95) < TOLERANCE
        assert s1.flap_count == 1
        assert s2.flap_count == 1


class TestAuditTrail:
    """Wing Flap audit trail."""

    def test_flap_audit_trail_append_only(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(WingFlapType.TRADE, "t1", "a1", -0.01, {"cost": 5.0, "trade_id": "t1"})
        engine.record_flap(WingFlapType.ENTROPY, "t1", None, -0.01, {})

        flaps = engine.get_flaps("t1")
        assert len(flaps) == 2
        assert flaps[0].flap_type == WingFlapType.TRADE
        assert flaps[1].flap_type == WingFlapType.ENTROPY

    def test_flap_ids_increment(self) -> None:
        engine = ButterflyEngine()
        f1 = engine.record_flap(WingFlapType.TRADE, "t1", "a1", -0.01, {"cost": 1.0, "trade_id": "t1"})
        f2 = engine.record_flap(WingFlapType.ENTROPY, "t1", None, -0.01, {})
        assert f1.flap_id == "flp_000001"
        assert f2.flap_id == "flp_000002"

    def test_empty_theatre_returns_empty_flaps(self) -> None:
        engine = ButterflyEngine()
        assert engine.get_flaps("nonexistent") == []
