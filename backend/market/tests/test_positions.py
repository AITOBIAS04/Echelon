"""Position tracking tests."""
from __future__ import annotations

import pytest

from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import AgentPosition, PositionManager
from backend.market.trading import Trade, TradingEngine

TOLERANCE = 1e-9


def _make_trading_setup(b: float = 100.0, n: int = 3):
    """Helper — creates a market in TRADING phase with pm and engine."""
    labels = [f"O{i}" for i in range(n)]
    market = MarketLifecycle.create_market("mkt_test", "theatre_test", b, n, labels)
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    pm = PositionManager(n, market.market_id)
    engine = TradingEngine(pm)
    return market, pm, engine


class TestPositionManager:
    """Position creation and tracking."""

    def test_new_agent_zero_position(self) -> None:
        pm = PositionManager(3, "mkt_test")
        pos = pm.get_position("agent_01")
        assert pos.shares == [0.0, 0.0, 0.0]
        assert pos.net_cashflow == 0.0
        assert pos.trade_count == 0

    def test_update_position_accumulates_shares(self) -> None:
        market, pm, engine = _make_trading_setup()
        pm.set_balance("agent_01", 1000.0)

        engine.execute_trade(market, "agent_01", 0, 20.0)
        engine.execute_trade(market, "agent_01", 0, 30.0)

        pos = pm.get_position("agent_01")
        assert pos.shares[0] == 50.0
        assert pos.trade_count == 2

    def test_update_position_decrements_on_sell(self) -> None:
        market, pm, engine = _make_trading_setup()
        pm.set_balance("agent_01", 1000.0)

        engine.execute_trade(market, "agent_01", 0, 50.0)
        engine.execute_trade(market, "agent_01", 0, -20.0)

        pos = pm.get_position("agent_01")
        assert abs(pos.shares[0] - 30.0) < TOLERANCE

    def test_net_cashflow_tracks_buys_and_sells(self) -> None:
        market, pm, engine = _make_trading_setup()
        pm.set_balance("agent_01", 1000.0)

        t1 = engine.execute_trade(market, "agent_01", 0, 50.0)
        t2 = engine.execute_trade(market, "agent_01", 0, -25.0)

        pos = pm.get_position("agent_01")
        assert abs(pos.net_cashflow - (t1.cost + t2.cost)) < TOLERANCE

    def test_balance_decreases_on_buy(self) -> None:
        market, pm, engine = _make_trading_setup()
        pm.set_balance("agent_01", 1000.0)

        trade = engine.execute_trade(market, "agent_01", 0, 10.0)
        expected_balance = 1000.0 - trade.cost
        assert abs(pm.get_balance("agent_01") - expected_balance) < TOLERANCE

    def test_settlement_payout_winning_outcome(self) -> None:
        pm = PositionManager(3, "mkt_test")
        pos = AgentPosition(
            agent_id="agent_01",
            market_id="mkt_test",
            shares=[50.0, 10.0, 0.0],
        )
        payout = pm.compute_settlement_payout(pos, resolved_outcome=0)
        assert payout == 50.0

    def test_settlement_payout_losing_outcome(self) -> None:
        pm = PositionManager(3, "mkt_test")
        pos = AgentPosition(
            agent_id="agent_01",
            market_id="mkt_test",
            shares=[50.0, 10.0, 0.0],
        )
        payout = pm.compute_settlement_payout(pos, resolved_outcome=2)
        assert payout == 0.0

    def test_all_positions_returns_tracked(self) -> None:
        market, pm, engine = _make_trading_setup()
        pm.set_balance("agent_01", 1000.0)
        pm.set_balance("agent_02", 1000.0)

        engine.execute_trade(market, "agent_01", 0, 10.0)
        engine.execute_trade(market, "agent_02", 1, 10.0)

        positions = pm.all_positions()
        assert len(positions) == 2
        ids = {p.agent_id for p in positions}
        assert ids == {"agent_01", "agent_02"}
