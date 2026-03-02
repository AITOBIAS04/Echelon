"""Settlement invariant tests — bounded loss, payout conservation, P&L."""
from __future__ import annotations

import math

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


def _run_scenario(
    trades: list[tuple[str, int, float]],
    winning_outcome: int = 0,
    b: float = 100.0,
    n: int = 3,
):
    """Helper — full lifecycle returning (report, market, pm)."""
    labels = [f"O{i}" for i in range(n)]
    market = MarketLifecycle.create_market("mkt_test", "theatre_test", b, n, labels)
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    pm = PositionManager(n, market.market_id)
    engine = TradingEngine(pm)

    for agent_id, outcome, shares in trades:
        # Ensure agent has enough balance
        current_bal = pm.get_balance(agent_id)
        if current_bal < 10000.0:
            pm.set_balance(agent_id, current_bal + 10000.0)
        engine.execute_trade(market, agent_id, outcome, shares)

    MarketLifecycle.begin_resolution(market, winning_outcome=winning_outcome)
    report = ResolutionEngine.settle(market, pm)
    return report, market, pm


class TestBoundedLossGuarantee:
    """Market maker P&L never exceeds -b*ln(n)."""

    def test_bounded_loss_single_agent(self) -> None:
        report, _, _ = _run_scenario(
            [("agent_01", 0, 50.0)], b=100.0
        )
        worst = LMSREngine.worst_case_loss(100.0, 3)
        assert report.market_maker_pnl >= -worst - TOLERANCE

    def test_bounded_loss_multiple_agents(self) -> None:
        report, _, _ = _run_scenario([
            ("agent_01", 0, 50.0),
            ("agent_02", 1, 30.0),
            ("agent_03", 2, 20.0),
        ], b=50.0)
        worst = LMSREngine.worst_case_loss(50.0, 3)
        assert report.market_maker_pnl >= -worst - TOLERANCE

    def test_bounded_loss_all_on_winner(self) -> None:
        """Worst case: all agents bet on the winning outcome."""
        report, _, _ = _run_scenario([
            ("agent_01", 0, 100.0),
            ("agent_02", 0, 50.0),
        ], b=100.0)
        worst = LMSREngine.worst_case_loss(100.0, 3)
        assert report.market_maker_pnl >= -worst - TOLERANCE

    def test_bounded_loss_small_b(self) -> None:
        report, _, _ = _run_scenario(
            [("agent_01", 0, 10.0)], b=5.0
        )
        worst = LMSREngine.worst_case_loss(5.0, 3)
        assert report.market_maker_pnl >= -worst - TOLERANCE


class TestPayoutConservation:
    """Settlement accounting identities."""

    def test_total_payout_equals_sum_of_agents(self) -> None:
        report, _, _ = _run_scenario([
            ("agent_01", 0, 50.0),
            ("agent_02", 1, 30.0),
        ])
        manual_sum = sum(s.payout for s in report.agent_settlements)
        assert abs(report.total_payout - manual_sum) < TOLERANCE

    def test_market_maker_pnl_formula(self) -> None:
        report, _, _ = _run_scenario([
            ("agent_01", 0, 50.0),
            ("agent_02", 1, 30.0),
            ("agent_03", 2, 20.0),
        ])
        total_cashflow = sum(s.net_cashflow for s in report.agent_settlements)
        expected_mm_pnl = total_cashflow - report.total_payout
        assert abs(report.market_maker_pnl - expected_mm_pnl) < TOLERANCE

    def test_realised_pnl_equals_payout_minus_cashflow(self) -> None:
        report, _, _ = _run_scenario([
            ("agent_01", 0, 50.0),
            ("agent_02", 1, 30.0),
        ])
        for s in report.agent_settlements:
            expected = s.payout - s.net_cashflow
            assert abs(s.realised_pnl - expected) < TOLERANCE

    def test_zero_trade_market_zero_payout(self) -> None:
        """No trades means no positions means zero payout."""
        report, _, _ = _run_scenario([], b=100.0)
        assert report.total_payout == 0.0
        assert report.market_maker_pnl == 0.0
        assert len(report.agent_settlements) == 0
