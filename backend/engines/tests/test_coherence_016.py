"""016 Engine Coherence Lock — verification tests.

Sprint-0 acceptance gates:
  A. WingFlapType enum parity between engines/ and database/models
  B. Stability scale 0-1 throughout engines layer
  C. FlapDirection enum exists with STABILISE/DESTABILISE/NEUTRAL
  D. ButterflyEngine.record_flap sets direction automatically
  E. EntropyEngine accepts LogicGapReading
  F. Fork divergence computation
  G. Pattern A: decay_multiplier semantics (no double-application)

NOTE: DB model imports use backend.database.models directly (not the
package __init__) to avoid triggering the asyncpg engine creation.
"""
from __future__ import annotations

import sys
import types
import pytest

from backend.engines.butterfly import (
    ButterflyEngine,
    FlapDirection,
    TimelineState,
    WingFlapType as EngineWingFlapType,
)
from backend.engines.entropy import EntropyEngine, LogicGapReading
from backend.engines.config import EntropyConfig

# Stub the database.connection module to avoid triggering asyncpg
# engine creation. models.py only needs `Base` from connection.
if "backend.database.connection" not in sys.modules:
    from sqlalchemy.orm import DeclarativeBase

    class _StubBase(DeclarativeBase):
        pass

    _conn_stub = types.ModuleType("backend.database.connection")
    _conn_stub.Base = _StubBase  # type: ignore[attr-defined]
    # Provide all names that database/__init__.py expects
    _conn_stub.engine = None  # type: ignore[attr-defined]
    _conn_stub.async_session_maker = None  # type: ignore[attr-defined]
    _conn_stub.get_session = None  # type: ignore[attr-defined]
    _conn_stub.get_db = None  # type: ignore[attr-defined]
    _conn_stub.init_db = None  # type: ignore[attr-defined]
    _conn_stub.close_db = None  # type: ignore[attr-defined]
    sys.modules["backend.database.connection"] = _conn_stub

from backend.database.models import (  # noqa: E402
    WingFlapType as DBWingFlapType,
    FlapDirection as DBFlapDirection,
)

TOLERANCE = 1e-9


# ============================================
# Gate A: Enum parity
# ============================================

class TestEnumParity:
    """Engine WingFlapType must be a superset of DB WingFlapType."""

    def test_all_db_flap_types_exist_in_engine(self) -> None:
        db_values = {e.value for e in DBWingFlapType}
        engine_values = {e.value for e in EngineWingFlapType}
        missing = db_values - engine_values
        assert not missing, f"DB enum values missing from engine: {missing}"

    def test_all_engine_flap_types_exist_in_db(self) -> None:
        db_values = {e.value for e in DBWingFlapType}
        engine_values = {e.value for e in EngineWingFlapType}
        missing = engine_values - db_values
        assert not missing, f"Engine enum values missing from DB: {missing}"

    def test_new_016_flap_types_present(self) -> None:
        expected_new = {
            "MIRROR_SYNC", "MIRROR_TRADE", "EVIDENCE", "CLAIM",
            "COUNTER_SIGNAL", "CORROBORATION", "DETONATION",
            "FORK_SPAWN", "STOP_CONDITION", "CERTIFICATE",
        }
        engine_values = {e.value for e in EngineWingFlapType}
        missing = expected_new - engine_values
        assert not missing, f"New 016 types missing: {missing}"


# ============================================
# Gate B: Stability scale 0-1
# ============================================

class TestStabilityScale:
    """All stability values must stay in [0, 1]."""

    def test_default_stability_is_one(self) -> None:
        engine = ButterflyEngine()
        state = engine.get_timeline_state("t1")
        assert state.stability == 1.0

    def test_stability_never_exceeds_one(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.SHIELD, "t1", "a1", 0.50, {"tier": "hard"}
        )
        assert flap.post_stability <= 1.0

    def test_stability_never_below_zero(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.ENTROPY, "t1", None, -2.0, {}
        )
        assert flap.post_stability >= 0.0


# ============================================
# Gate C: FlapDirection enum
# ============================================

class TestFlapDirection:
    """FlapDirection must have STABILISE, DESTABILISE, NEUTRAL."""

    def test_engine_direction_values(self) -> None:
        assert FlapDirection.STABILISE.value == "STABILISE"
        assert FlapDirection.DESTABILISE.value == "DESTABILISE"
        assert FlapDirection.NEUTRAL.value == "NEUTRAL"

    def test_db_direction_values(self) -> None:
        assert DBFlapDirection.STABILISE.value == "STABILISE"
        assert DBFlapDirection.DESTABILISE.value == "DESTABILISE"
        assert DBFlapDirection.NEUTRAL.value == "NEUTRAL"


# ============================================
# Gate D: record_flap auto-direction
# ============================================

class TestAutoDirection:
    """record_flap should set direction from impact sign."""

    def test_positive_impact_stabilises(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.SHIELD, "t1", "a1", 0.05, {"tier": "easy"}
        )
        assert flap.direction == FlapDirection.STABILISE

    def test_negative_impact_destabilises(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.ENTROPY, "t1", None, -0.01, {}
        )
        assert flap.direction == FlapDirection.DESTABILISE

    def test_zero_impact_neutral(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.MIRROR_SYNC, "t1", None, 0.0,
            {"source": "polymarket"}
        )
        assert flap.direction == FlapDirection.NEUTRAL


# ============================================
# Gate E: EntropyEngine + LogicGapReading
# ============================================

class TestLogicGapReading:
    """EntropyEngine must accept LogicGapReading."""

    def test_reading_default_healthy(self) -> None:
        config = EntropyConfig()
        butterfly = ButterflyEngine()
        entropy = EntropyEngine(config, butterfly)

        reading = LogicGapReading(status="healthy", magnitude=0.0)
        flap = entropy.tick("t1", reading=reading)

        assert flap.flap_type == EngineWingFlapType.ENTROPY
        assert flap.stability_impact < 0  # decay is negative
        assert flap.trigger_detail["logic_gap_status"] == "healthy"
        assert flap.trigger_detail["logic_gap_magnitude"] == 0.0

    def test_reading_critical_higher_decay(self) -> None:
        config = EntropyConfig()
        butterfly = ButterflyEngine()
        entropy = EntropyEngine(config, butterfly)

        healthy_flap = entropy.tick("t1", reading=LogicGapReading("healthy", 0.0))
        critical_flap = entropy.tick("t2", reading=LogicGapReading("critical", 0.8))

        # Critical should have higher magnitude decay
        assert abs(critical_flap.stability_impact) > abs(healthy_flap.stability_impact)

    def test_legacy_string_still_works(self) -> None:
        config = EntropyConfig()
        butterfly = ButterflyEngine()
        entropy = EntropyEngine(config, butterfly)

        flap = entropy.tick("t1", logic_gap_status="stressed")
        assert flap.trigger_detail["logic_gap_status"] == "stressed"


# ============================================
# Gate F: Fork divergence
# ============================================

class TestForkDivergence:
    """ButterflyEngine.compute_fork_divergence."""

    def test_divergence_zero_for_identical(self) -> None:
        engine = ButterflyEngine()
        # Both start at 1.0, no flaps
        div = engine.compute_fork_divergence("anchor", "fork")
        assert div == 0.0

    def test_divergence_reflects_stability_gap(self) -> None:
        engine = ButterflyEngine()
        # Decay fork by 0.3
        engine.record_flap(EngineWingFlapType.ENTROPY, "fork", None, -0.30, {})
        # Anchor stays at 1.0
        div = engine.compute_fork_divergence("anchor", "fork")
        assert abs(div - 0.30) < TOLERANCE


# ============================================
# Gate G: Pattern A — no double-application
# ============================================

class TestPatternADecay:
    """Verify that decay_multiplier is applied exactly once.

    This is a design-level test. The actual DB-layer test requires
    integration testing, but we verify the engine contract here.
    """

    def test_entropy_config_multipliers_sane(self) -> None:
        config = EntropyConfig()
        assert config.base_decay_rate == 0.01
        assert config.stressed_multiplier == 1.5
        assert config.danger_multiplier == 2.0
        assert config.critical_multiplier == 3.0

    def test_effective_rate_scales_by_status(self) -> None:
        config = EntropyConfig()
        butterfly = ButterflyEngine()
        entropy = EntropyEngine(config, butterfly)

        rates = {
            "healthy": entropy.get_effective_decay_rate("healthy"),
            "stressed": entropy.get_effective_decay_rate("stressed"),
            "danger": entropy.get_effective_decay_rate("danger"),
            "critical": entropy.get_effective_decay_rate("critical"),
        }
        # Each level should be strictly higher than previous
        assert rates["healthy"] < rates["stressed"]
        assert rates["stressed"] < rates["danger"]
        assert rates["danger"] < rates["critical"]

    def test_unknown_status_defaults_to_base(self) -> None:
        config = EntropyConfig()
        butterfly = ButterflyEngine()
        entropy = EntropyEngine(config, butterfly)
        rate = entropy.get_effective_decay_rate("banana")
        assert rate == config.base_decay_rate


# ============================================
# Existing tests still pass (regression)
# ============================================

class TestRegressionRecordFlap:
    """Ensure existing butterfly tests still pass with new direction field."""

    def test_record_flap_updates_stability(self) -> None:
        engine = ButterflyEngine()
        flap = engine.record_flap(
            EngineWingFlapType.TRADE, "theatre_01", "agent_01", -0.05,
            {"cost": 10.0, "trade_id": "trd_1"},
        )
        assert flap.pre_stability == 1.0
        assert abs(flap.post_stability - 0.95) < TOLERANCE
        assert flap.direction == FlapDirection.DESTABILISE

    def test_volume_tracks_trade_cost(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(
            EngineWingFlapType.TRADE, "t1", "agent_01", -0.01,
            {"cost": 25.5, "trade_id": "trd_1"},
        )
        engine.record_flap(
            EngineWingFlapType.TRADE, "t1", "agent_01", 0.01,
            {"cost": -10.0, "trade_id": "trd_2"},
        )
        state = engine.get_timeline_state("t1")
        assert abs(state.volume - 35.5) < TOLERANCE

    def test_founders_yield_formula(self) -> None:
        engine = ButterflyEngine()
        engine.record_flap(
            EngineWingFlapType.TRADE, "t1", "a1", -0.20,
            {"cost": 1000.0, "trade_id": "trd_1"},
        )
        expected = 0.80 * 1000.0 * 0.005
        assert abs(engine.compute_founders_yield("t1") - expected) < TOLERANCE
