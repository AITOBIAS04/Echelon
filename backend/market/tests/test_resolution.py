"""Resolution and settlement tests."""
from __future__ import annotations

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine
from backend.market.state import MarketPhase
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


def _make_settled_market(trades: list[tuple[str, int, float]], b: float = 100.0):
    """Helper — create market, trade, resolve, settle. Returns (report, market)."""
    n = 3
    labels = ["Yes", "No", "Maybe"]
    market = MarketLifecycle.create_market("mkt_test", "theatre_test", b, n, labels)
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    pm = PositionManager(n, market.market_id)
    engine = TradingEngine(pm)

    for agent_id, outcome, shares in trades:
        pm.set_balance(agent_id, pm.get_balance(agent_id) + 10000.0)
        engine.execute_trade(market, agent_id, outcome, shares)

    MarketLifecycle.begin_resolution(market, winning_outcome=0)
    report = ResolutionEngine.settle(market, pm)
    return report, market


class TestSettleBasics:
    """Basic settlement correctness."""

    def test_settle_computes_correct_payouts(self) -> None:
        report, _ = _make_settled_market([
            ("agent_01", 0, 50.0),  # buys 50 of winning outcome
            ("agent_02", 1, 30.0),  # buys 30 of losing outcome
        ])

        a1 = next(s for s in report.agent_settlements if s.agent_id == "agent_01")
        a2 = next(s for s in report.agent_settlements if s.agent_id == "agent_02")

        assert a1.payout == 50.0  # 50 winning shares
        assert a2.payout == 0.0   # 0 winning shares

    def test_settlement_hash_deterministic(self) -> None:
        trades = [("agent_01", 0, 50.0), ("agent_02", 1, 30.0)]

        r1, _ = _make_settled_market(trades, b=100.0)
        r2, _ = _make_settled_market(trades, b=100.0)

        assert r1.settlement_hash == r2.settlement_hash
        assert len(r1.settlement_hash) == 64

    def test_settle_transitions_to_settled(self) -> None:
        _, market = _make_settled_market([("agent_01", 0, 10.0)])
        assert market.phase == MarketPhase.SETTLED

    def test_winning_label_correct(self) -> None:
        report, _ = _make_settled_market([("agent_01", 0, 10.0)])
        assert report.winning_label == "Yes"
        assert report.winning_outcome == 0
