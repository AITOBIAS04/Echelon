"""Integration tests — EngineOrchestrator wiring, trade flaps, circuit breaker."""
from __future__ import annotations

import pytest

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.config import EngineConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import HeartbeatConfig, HeartbeatScheduler
from backend.engines.integration import EngineOrchestrator
from backend.market.exceptions import ParameterMutationAfterCommit, TradingHalted
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.state import MarketState
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(
    n_outcomes: int = 2,
    b: float = 100.0,
    trade_impact_k: float = 0.1,
) -> tuple[EngineOrchestrator, ButterflyEngine, MarketState]:
    """Create a wired EngineOrchestrator for testing."""
    labels = ["Yes", "No", "Maybe"][:n_outcomes]
    market = MarketLifecycle.create_market(
        "test_theatre", "theatre_01", b, n_outcomes, labels,
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    position_manager = PositionManager(n_outcomes, "test_theatre")
    position_manager.set_balance("agent_01", 10_000.0)
    trading_engine = TradingEngine(position_manager)
    butterfly = ButterflyEngine()
    engine_config = EngineConfig()
    engine_config.butterfly.trade_impact_k = trade_impact_k
    entropy = EntropyEngine(engine_config.entropy, butterfly)
    heartbeat = HeartbeatScheduler(HeartbeatConfig())

    orchestrator = EngineOrchestrator(
        market=market,
        trading_engine=trading_engine,
        position_manager=position_manager,
        butterfly=butterfly,
        entropy=entropy,
        engine_config=engine_config,
        heartbeat=heartbeat,
    )
    return orchestrator, butterfly, market


# ---------------------------------------------------------------------------
# Trade with Wing Flap
# ---------------------------------------------------------------------------

class TestTradeWithFlap:
    """execute_trade_with_flap produces Trade + TRADE Wing Flap."""

    def test_trade_returns_trade_object(self) -> None:
        orch, butterfly, market = _make_orchestrator()
        trade = orch.execute_trade_with_flap("agent_01", 0, 10.0)
        assert trade.trade_id is not None
        assert trade.cost != 0.0

    def test_trade_records_wing_flap(self) -> None:
        orch, butterfly, market = _make_orchestrator()
        orch.execute_trade_with_flap("agent_01", 0, 10.0)
        flaps = butterfly.get_flaps("test_theatre")
        assert len(flaps) == 1
        assert flaps[0].flap_type == WingFlapType.TRADE
        assert flaps[0].agent_id == "agent_01"

    def test_buy_produces_negative_impact(self) -> None:
        orch, butterfly, _ = _make_orchestrator()
        orch.execute_trade_with_flap("agent_01", 0, 10.0)  # buy
        flaps = butterfly.get_flaps("test_theatre")
        assert flaps[0].stability_impact < 0  # destabilising

    def test_sell_produces_positive_impact(self) -> None:
        orch, butterfly, _ = _make_orchestrator()
        # First buy to have shares to sell
        orch.execute_trade_with_flap("agent_01", 0, 10.0)
        orch.execute_trade_with_flap("agent_01", 0, -5.0)  # sell
        flaps = butterfly.get_flaps("test_theatre")
        assert flaps[1].stability_impact > 0  # stabilising

    def test_impact_clamped(self) -> None:
        # Small b to amplify impact beyond clamp
        orch, butterfly, _ = _make_orchestrator(b=1.0, trade_impact_k=10.0)
        orch.execute_trade_with_flap("agent_01", 0, 10.0)
        flaps = butterfly.get_flaps("test_theatre")
        assert flaps[0].stability_impact >= -0.05
        assert flaps[0].stability_impact <= 0.05

    def test_flap_trigger_detail_contains_trade_info(self) -> None:
        orch, butterfly, _ = _make_orchestrator()
        trade = orch.execute_trade_with_flap("agent_01", 0, 5.0)
        flaps = butterfly.get_flaps("test_theatre")
        detail = flaps[0].trigger_detail
        assert detail["trade_id"] == trade.trade_id
        assert detail["outcome_index"] == 0
        assert detail["shares"] == 5.0
        assert "cost" in detail


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    """Halt / resume trading."""

    def test_halt_blocks_trading(self) -> None:
        orch, _, _ = _make_orchestrator()
        orch.halt_trading("test_theatre")
        with pytest.raises(TradingHalted):
            orch.execute_trade_with_flap("agent_01", 0, 10.0)

    def test_resume_allows_trading(self) -> None:
        orch, _, _ = _make_orchestrator()
        orch.halt_trading("test_theatre")
        orch.resume_trading("test_theatre")
        # Should not raise
        trade = orch.execute_trade_with_flap("agent_01", 0, 10.0)
        assert trade.trade_id is not None


# ---------------------------------------------------------------------------
# Config immutability
# ---------------------------------------------------------------------------

class TestConfigImmutability:
    """EngineConfig freeze / assert_not_committed."""

    def test_freeze_sets_committed(self) -> None:
        config = EngineConfig()
        assert config.committed is False
        config.freeze()
        assert config.committed is True

    def test_double_freeze_raises(self) -> None:
        config = EngineConfig()
        config.freeze()
        with pytest.raises(ParameterMutationAfterCommit):
            config.freeze()

    def test_assert_not_committed_before_freeze(self) -> None:
        config = EngineConfig()
        config.assert_not_committed()  # should not raise

    def test_assert_not_committed_after_freeze(self) -> None:
        config = EngineConfig()
        config.freeze()
        with pytest.raises(ParameterMutationAfterCommit):
            config.assert_not_committed()

    def test_commitment_dict(self) -> None:
        config = EngineConfig()
        d = config.to_commitment_dict()
        assert d["butterfly"]["trade_impact_k"] == 0.1
        assert d["entropy"]["base_decay_rate"] == 0.01
        assert "shield_tiers" in d["butterfly"]


# ---------------------------------------------------------------------------
# Package exports
# ---------------------------------------------------------------------------

class TestPackageExports:
    """Verify __init__.py re-exports all public symbols."""

    def test_all_exports_importable(self) -> None:
        import backend.engines as engines

        # Butterfly
        assert hasattr(engines, "WingFlapType")
        assert hasattr(engines, "WingFlap")
        assert hasattr(engines, "TimelineState")
        assert hasattr(engines, "ButterflyEngine")

        # Entropy
        assert hasattr(engines, "EntropyEngine")

        # Heartbeat
        assert hasattr(engines, "HeartbeatConfig")
        assert hasattr(engines, "HeartbeatScheduler")
        assert hasattr(engines, "CADENCES")

        # Config
        assert hasattr(engines, "ButterflyConfig")
        assert hasattr(engines, "EntropyConfig")
        assert hasattr(engines, "EngineConfig")

        # Integration
        assert hasattr(engines, "EngineOrchestrator")

    def test_all_list_complete(self) -> None:
        import backend.engines as engines

        expected = {
            "WingFlapType", "WingFlap", "TimelineState", "ButterflyEngine",
            "EntropyEngine",
            "HeartbeatConfig", "HeartbeatScheduler", "CADENCES",
            "ButterflyConfig", "EntropyConfig", "EngineConfig",
            "EngineOrchestrator",
            # Sprint 2: Logic Gap + Reality Signal + Paradox
            "LogicGapStatus", "LogicGapReading", "LogicGapCalculator",
            "RealitySignal", "RealitySignalProvider",
            "OsintRealityProvider", "DeterministicRealityProvider", "StubRealityProvider",
            "ParadoxMode", "ParadoxAction", "ParadoxConfig",
            "ParadoxRuntimeState", "ParadoxEngine",
            # Sprint 3: VRF + Status
            "VRFConfig", "VRFResult", "VRFProvider",
            "MarketStatusSnapshot", "market_status_snapshot",
        }
        assert set(engines.__all__) == expected
