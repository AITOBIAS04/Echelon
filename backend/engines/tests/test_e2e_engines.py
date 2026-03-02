"""End-to-end engine lifecycle tests — full create→commit→trade→status→settle."""
from __future__ import annotations

from backend.chain.sepolia import MockSepoliaClient
from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.config import EngineConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import HeartbeatConfig, HeartbeatScheduler
from backend.engines.integration import EngineOrchestrator
from backend.engines.logic_gap import LogicGapCalculator
from backend.engines.paradox import ParadoxConfig, ParadoxEngine, ParadoxMode
from backend.engines.reality_signal import StubRealityProvider
from backend.engines.status import market_status_snapshot
from backend.engines.vrf import VRFConfig, VRFProvider
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


def _full_stack(
    b: float = 100.0,
    n_outcomes: int = 2,
    vrf_seed: str = "e2e_test_seed",
    paradox_mode: ParadoxMode = ParadoxMode.ENABLED,
):
    """Wire all Sprint 1-3 engines for end-to-end testing."""
    labels = ["Yes", "No", "Maybe"][:n_outcomes]
    market = MarketLifecycle.create_market(
        "test_e2e", "e2e_theatre", b, n_outcomes, labels,
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    position_manager = PositionManager(n_outcomes, "test_e2e")
    position_manager.set_balance("agent_01", 10_000.0)
    trading_engine = TradingEngine(position_manager)

    butterfly = ButterflyEngine()
    engine_config = EngineConfig()
    entropy = EntropyEngine(engine_config.entropy, butterfly)
    heartbeat = HeartbeatScheduler(HeartbeatConfig())

    # VRF
    vrf_config = VRFConfig(mode="local", seed=vrf_seed)
    vrf = VRFProvider(vrf_config)
    engine_config.vrf = vrf_config

    # Paradox
    paradox_config = ParadoxConfig(mode=paradox_mode)
    calc = LogicGapCalculator()
    provider = StubRealityProvider(p_reality=0.5)
    paradox = ParadoxEngine(paradox_config, butterfly, calc, provider)
    engine_config.paradox = paradox_config

    orchestrator = EngineOrchestrator(
        market=market,
        trading_engine=trading_engine,
        position_manager=position_manager,
        butterfly=butterfly,
        entropy=entropy,
        engine_config=engine_config,
        heartbeat=heartbeat,
        paradox=paradox,
        vrf=vrf,
    )

    return {
        "orchestrator": orchestrator,
        "market": market,
        "butterfly": butterfly,
        "entropy": entropy,
        "heartbeat": heartbeat,
        "paradox": paradox,
        "vrf": vrf,
        "engine_config": engine_config,
        "calc": calc,
    }


class TestFullLifecycle:
    """Full lifecycle: create → commit → trade → flaps → status → settle."""

    def test_trade_produces_flap_and_status(self) -> None:
        stack = _full_stack()
        orch = stack["orchestrator"]
        butterfly = stack["butterfly"]
        market = stack["market"]
        heartbeat = stack["heartbeat"]

        # Execute trade
        trade = orch.execute_trade_with_flap("agent_01", 0, 10.0)
        assert trade.trade_id is not None

        # Verify Wing Flap
        flaps = butterfly.get_flaps("test_e2e")
        assert len(flaps) == 1
        assert flaps[0].flap_type == WingFlapType.TRADE

        # Verify status snapshot
        snap = market_status_snapshot(
            theatre_id="test_e2e",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert snap.total_trades == 1
        assert snap.timeline_stability < 1.0  # Destabilised by trade

    def test_multiple_trades_accumulate(self) -> None:
        stack = _full_stack()
        orch = stack["orchestrator"]
        butterfly = stack["butterfly"]

        orch.execute_trade_with_flap("agent_01", 0, 5.0)
        orch.execute_trade_with_flap("agent_01", 1, 3.0)
        orch.execute_trade_with_flap("agent_01", 0, -2.0)

        flaps = butterfly.get_flaps("test_e2e")
        assert len(flaps) == 3

        state = butterfly.get_timeline_state("test_e2e")
        assert state.flap_count == 3
        assert 0.0 <= state.stability <= 1.0


class TestLifecycleWithVRF:
    """VRF randomness wired into lifecycle."""

    def test_vrf_deterministic_in_lifecycle(self) -> None:
        stack = _full_stack(vrf_seed="seed_A")
        vrf = stack["vrf"]

        r1 = vrf.request_randomness("e2e_theatre", "sabotage_impact")
        r2 = vrf.request_randomness("e2e_theatre", "threshold_offset")

        # Different purposes → different values
        assert r1.random_value != r2.random_value
        assert r1.verified is True
        assert r2.verified is True

    def test_vrf_scale_to_range(self) -> None:
        stack = _full_stack(vrf_seed="seed_B")
        vrf = stack["vrf"]

        result = vrf.request_randomness("e2e_theatre", "sabotage_impact")
        scaled = VRFProvider.scale_to_range(result.random_value, -0.15, -0.05)
        assert -0.15 <= scaled <= -0.05

    def test_vrf_config_in_commitment_hash(self) -> None:
        stack = _full_stack()
        engine_config = stack["engine_config"]
        d = engine_config.to_commitment_dict()
        assert "vrf" in d
        assert d["vrf"]["mode"] == "local"
        assert d["vrf"]["seed"] == "e2e_test_seed"


class TestLifecycleWithChain:
    """MockSepoliaClient in lifecycle."""

    def test_commit_and_settle_on_chain(self) -> None:
        stack = _full_stack()
        engine_config = stack["engine_config"]
        client = MockSepoliaClient()

        # Publish commitment
        commitment_hash = str(hash(str(engine_config.to_commitment_dict())))
        receipt = client.publish_commitment("e2e_theatre", commitment_hash)
        assert receipt.status is True

        # Execute trades
        orch = stack["orchestrator"]
        orch.execute_trade_with_flap("agent_01", 0, 10.0)

        # Publish settlement
        settlement_hash = "settle_" + commitment_hash[:16]
        receipt = client.publish_settlement("e2e_theatre", settlement_hash, 0)
        assert receipt.status is True

        # Verify round-trip
        commit_rec = client.verify_commitment("e2e_theatre")
        settle_rec = client.verify_settlement("e2e_theatre")
        assert commit_rec is not None
        assert commit_rec.commitment_hash == commitment_hash
        assert settle_rec is not None
        assert settle_rec.winning_outcome == 0

    def test_status_with_on_chain_fields(self) -> None:
        stack = _full_stack()
        client = MockSepoliaClient()

        client.publish_commitment("e2e_theatre", "0xcommit")

        snap = market_status_snapshot(
            theatre_id="test_e2e",
            market=stack["market"],
            butterfly=stack["butterfly"],
            heartbeat=stack["heartbeat"],
            commitment_hash="0xcommit",
            on_chain=True,
        )
        assert snap.commitment_hash == "0xcommit"
        assert snap.on_chain is True


class TestLifecycleParadoxScan:
    """Paradox scanning in full lifecycle."""

    def test_paradox_scan_after_trade(self) -> None:
        stack = _full_stack(paradox_mode=ParadoxMode.ENABLED)
        orch = stack["orchestrator"]
        paradox = stack["paradox"]
        calc = stack["calc"]

        # Record a market price for Logic Gap calculation
        calc.record_price("e2e_theatre", 0.5, 1000.0)

        # Execute trade
        orch.execute_trade_with_flap("agent_01", 0, 10.0)

        # Scan — should produce a reading
        reading = paradox.scan("e2e_theatre")
        assert reading is not None
        # p_market=0.5, p_reality=0.5 → gap=0.0
        assert reading.logic_gap < 0.01

    def test_all_engines_in_commitment_dict(self) -> None:
        stack = _full_stack()
        engine_config = stack["engine_config"]
        d = engine_config.to_commitment_dict()

        assert "butterfly" in d
        assert "entropy" in d
        assert "vrf" in d
        assert "paradox" in d
