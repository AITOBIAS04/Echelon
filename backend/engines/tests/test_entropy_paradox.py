"""Entropy←Paradox wiring tests — real Logic Gap status drives decay rates."""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.config import EngineConfig, EntropyConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import HeartbeatConfig, HeartbeatScheduler
from backend.engines.integration import EngineOrchestrator
from backend.engines.logic_gap import LogicGapCalculator, LogicGapStatus
from backend.engines.paradox import (
    ParadoxAction,
    ParadoxConfig,
    ParadoxEngine,
    ParadoxMode,
)
from backend.engines.reality_signal import StubRealityProvider
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


def _make_wired_system(
    p_reality: float = 0.5,
    paradox_mode: ParadoxMode = ParadoxMode.ENABLED,
) -> tuple[EngineOrchestrator, ButterflyEngine, LogicGapCalculator, ParadoxEngine]:
    """Create full system with Paradox→Entropy wiring."""
    market = MarketLifecycle.create_market(
        "test_theatre", "theatre_01", 100.0, 2, ["Yes", "No"],
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    position_manager = PositionManager(2, "test_theatre")
    position_manager.set_balance("agent_01", 10_000.0)
    trading_engine = TradingEngine(position_manager)
    butterfly = ButterflyEngine()
    engine_config = EngineConfig()
    entropy = EntropyEngine(engine_config.entropy, butterfly)
    heartbeat = HeartbeatScheduler(HeartbeatConfig())

    paradox_config = ParadoxConfig(mode=paradox_mode)
    calc = LogicGapCalculator()
    provider = StubRealityProvider(p_reality=p_reality)
    paradox = ParadoxEngine(paradox_config, butterfly, calc, provider)

    orchestrator = EngineOrchestrator(
        market=market,
        trading_engine=trading_engine,
        position_manager=position_manager,
        butterfly=butterfly,
        entropy=entropy,
        engine_config=engine_config,
        heartbeat=heartbeat,
        paradox=paradox,
    )
    return orchestrator, butterfly, calc, paradox


class TestEntropyReceivesLogicGapStatus:
    """Entropy decay rate responds to Paradox Logic Gap status."""

    def test_healthy_gap_uses_base_decay(self) -> None:
        orch, butterfly, calc, paradox = _make_wired_system(p_reality=0.50)
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.0 → healthy
        # Simulate paradox tick → updates _last_logic_gap_status
        reading = paradox.scan("t1")
        assert reading.status == LogicGapStatus.HEALTHY
        orch._last_logic_gap_status = reading.status.value

        # Now entropy tick uses the updated status
        orch._entropy.tick("t1", orch._last_logic_gap_status)
        state = butterfly.get_timeline_state("t1")
        # Entropy at healthy = -0.01 base rate, stability should be 1.0 - 0.01 = 0.99
        # But paradox scan also recorded a flap, so need to account for that
        # Actually paradox scan does NOT record a flap — only execute_action does
        assert abs(state.stability - 0.99) < TOLERANCE

    def test_stressed_gap_escalates_decay(self) -> None:
        orch, butterfly, calc, paradox = _make_wired_system(p_reality=0.25)
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.25 → stressed
        reading = paradox.scan("t1")
        assert reading.status == LogicGapStatus.STRESSED
        orch._last_logic_gap_status = reading.status.value

        orch._entropy.tick("t1", orch._last_logic_gap_status)
        state = butterfly.get_timeline_state("t1")
        # stressed decay = 0.01 * 1.5 = 0.015
        assert abs(state.stability - (1.0 - 0.015)) < TOLERANCE

    def test_critical_gap_maximum_decay(self) -> None:
        orch, butterfly, calc, paradox = _make_wired_system(p_reality=0.05)
        calc.record_price("t1", 0.70, timestamp_s=100.0)  # gap=0.65 → critical
        reading = paradox.scan("t1")
        assert reading.status == LogicGapStatus.CRITICAL
        orch._last_logic_gap_status = reading.status.value

        orch._entropy.tick("t1", orch._last_logic_gap_status)
        state = butterfly.get_timeline_state("t1")
        # critical decay = 0.01 * 3.0 = 0.03
        assert abs(state.stability - (1.0 - 0.03)) < TOLERANCE


class TestEndToEndDecayEscalation:
    """End-to-end: trade → price moves → Logic Gap diverges → decay escalates."""

    def test_trade_causes_price_divergence_and_increased_decay(self) -> None:
        orch, butterfly, calc, paradox = _make_wired_system(p_reality=0.50)

        # Initial price at market opening: 0.50 (both outcomes equal)
        calc.record_price("t1", 0.50, timestamp_s=100.0)

        # Trade pushes market price to ~0.73 (buy 10 shares of outcome 0)
        orch.execute_trade_with_flap("agent_01", 0, 10.0)
        # After trade, p_market for outcome 0 is higher — let's record the new price
        from backend.market.lmsr import LMSREngine
        prices = LMSREngine.prices(orch._market.x, orch._market.b)
        calc.record_price("t1", prices[0], timestamp_s=110.0)

        # Scan: Logic Gap should be significant (market diverged from reality)
        reading = paradox.scan("t1")
        assert reading is not None
        assert reading.logic_gap > 0  # some divergence

        # Update orchestrator with real Logic Gap status
        orch._last_logic_gap_status = reading.status.value

        # Entropy tick uses real status
        flap = orch._entropy.tick("t1", orch._last_logic_gap_status)
        # If gap is stressed/danger/critical, decay should be > base rate
        if reading.status != LogicGapStatus.HEALTHY:
            assert abs(flap.stability_impact) > 0.01

    def test_orchestrator_paradox_handler_updates_status(self) -> None:
        """Verify _paradox_tick_handler updates _last_logic_gap_status."""
        orch, butterfly, calc, paradox = _make_wired_system(p_reality=0.20)
        calc.record_price("t1", 0.50, timestamp_s=100.0)  # gap=0.30 → stressed

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            orch._paradox_tick_handler("t1")
        )
        assert orch._last_logic_gap_status == "stressed"


class TestParadoxConfigInCommitmentHash:
    """Paradox config included in EngineConfig commitment hash."""

    def test_paradox_in_commitment_dict(self) -> None:
        config = EngineConfig()
        paradox_config = ParadoxConfig(mode=ParadoxMode.ENABLED)
        config.paradox = paradox_config
        d = config.to_commitment_dict()
        assert "paradox" in d
        assert d["paradox"]["mode"] == "enabled"

    def test_no_paradox_no_key(self) -> None:
        config = EngineConfig()
        d = config.to_commitment_dict()
        assert "paradox" not in d
