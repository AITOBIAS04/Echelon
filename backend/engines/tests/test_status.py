"""Market Status Snapshot tests — snapshot assembly from all engines."""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.heartbeat import HeartbeatConfig, HeartbeatScheduler
from backend.engines.logic_gap import LogicGapCalculator
from backend.engines.paradox import ParadoxConfig, ParadoxEngine, ParadoxMode
from backend.engines.reality_signal import StubRealityProvider
from backend.engines.status import MarketStatusSnapshot, market_status_snapshot
from backend.market.lifecycle import MarketLifecycle

TOLERANCE = 1e-9


def _make_market(n_outcomes: int = 2, b: float = 100.0):
    """Create a market in TRADING phase."""
    labels = ["Yes", "No", "Maybe"][:n_outcomes]
    market = MarketLifecycle.create_market(
        "test_mkt", "theatre_01", b, n_outcomes, labels,
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    return market


class TestSnapshotBasicFields:
    """market_status_snapshot assembles correct fields."""

    def test_basic_snapshot(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert isinstance(snap, MarketStatusSnapshot)
        assert snap.theatre_id == "theatre_01"
        assert snap.market_phase == "TRADING"
        assert len(snap.current_prices) == 2
        # Uniform prices for [0.0, 0.0]
        assert abs(snap.current_prices[0] - 0.5) < TOLERANCE
        assert abs(snap.current_prices[1] - 0.5) < TOLERANCE

    def test_total_trades_from_butterfly(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        # Record some flaps
        butterfly.record_flap(WingFlapType.TRADE, "theatre_01", "a1", -0.01, {"cost": 5.0})
        butterfly.record_flap(WingFlapType.TRADE, "theatre_01", "a2", -0.02, {"cost": 10.0})

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert snap.total_trades == 2

    def test_timeline_stability(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        # Destabilise
        butterfly.record_flap(WingFlapType.TRADE, "theatre_01", "a1", -0.05, {"cost": 5.0})

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert abs(snap.timeline_stability - 0.95) < TOLERANCE


class TestSnapshotWithoutParadox:
    """Snapshot without Paradox — logic gap fields are None."""

    def test_no_paradox(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert snap.logic_gap_status is None
        assert snap.logic_gap_value is None


class TestSnapshotWithParadox:
    """Snapshot with Paradox — logic gap fields populated."""

    def test_with_paradox_reading(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        # Create Paradox with enabled mode and a reality signal
        config = ParadoxConfig(mode=ParadoxMode.ENABLED)
        calc = LogicGapCalculator()
        # Seed a price observation for the smoothing window
        calc.record_price("theatre_01", 0.7, 1000.0)
        provider = StubRealityProvider(p_reality=0.3)
        paradox = ParadoxEngine(config, butterfly, calc, provider)

        # Trigger a scan to populate last_reading
        paradox.scan("theatre_01")

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
            paradox=paradox,
        )
        assert snap.logic_gap_status is not None
        assert snap.logic_gap_value is not None
        # Logic gap = abs(0.7 - 0.3) = 0.4
        assert abs(snap.logic_gap_value - 0.4) < TOLERANCE


class TestSnapshotOnChainFields:
    """On-chain commitment fields."""

    def test_commitment_hash_and_on_chain(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
            commitment_hash="0xdeadbeef",
            on_chain=True,
        )
        assert snap.commitment_hash == "0xdeadbeef"
        assert snap.on_chain is True

    def test_default_off_chain(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        assert snap.commitment_hash == ""
        assert snap.on_chain is False


class TestSnapshotHeartbeat:
    """Heartbeat tick counts in snapshot."""

    def test_heartbeat_ticks_default(self) -> None:
        market = _make_market()
        butterfly = ButterflyEngine()
        heartbeat = HeartbeatScheduler(HeartbeatConfig())

        snap = market_status_snapshot(
            theatre_id="theatre_01",
            market=market,
            butterfly=butterfly,
            heartbeat=heartbeat,
        )
        # No heartbeat started — all zeros
        ticks = snap.heartbeat_ticks
        assert isinstance(ticks, dict)
        for cadence in ["agent", "market", "paradox", "entropy"]:
            assert ticks[cadence] == 0
