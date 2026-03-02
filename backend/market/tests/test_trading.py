"""Trade execution engine tests."""
from __future__ import annotations

import math

import pytest

from backend.market.exceptions import (
    InsufficientBalance,
    InsufficientShares,
    InvalidMarketParameters,
    TradingHalted,
)
from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


def _make_trading_market(b: float = 100.0, n: int = 3):
    """Helper — creates a market in TRADING phase with a position manager."""
    labels = [f"O{i}" for i in range(n)]
    market = MarketLifecycle.create_market("mkt_test", "theatre_test", b, n, labels)
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    pm = PositionManager(n, market.market_id)
    engine = TradingEngine(pm)
    return market, pm, engine


class TestExecuteTrade:
    """Trade execution correctness."""

    def test_execute_trade_updates_x_vector(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        trade = engine.execute_trade(market, "agent_01", 0, 50.0)

        assert market.x[0] == 50.0
        assert market.x[1] == 0.0
        assert market.x[2] == 0.0

    def test_execute_trade_cost_matches_lmsr(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        x_before = list(market.x)
        trade = engine.execute_trade(market, "agent_01", 0, 50.0)

        expected_cost = LMSREngine.trade_cost(x_before, [50.0, 0.0, 0.0], 100.0)
        assert abs(trade.cost - expected_cost) < TOLERANCE

    def test_execute_trade_captures_prices(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        pre_expected = LMSREngine.prices(market.x, market.b)
        trade = engine.execute_trade(market, "agent_01", 0, 50.0)
        post_expected = LMSREngine.prices(market.x, market.b)

        for a, e in zip(trade.pre_trade_prices, pre_expected):
            assert abs(a - e) < TOLERANCE
        for a, e in zip(trade.post_trade_prices, post_expected):
            assert abs(a - e) < TOLERANCE

    def test_quote_returns_cost_without_mutation(self) -> None:
        market, pm, engine = _make_trading_market()

        x_before = list(market.x)
        cost = engine.quote(market, 0, 50.0)
        assert market.x == x_before  # no mutation

        expected = LMSREngine.trade_cost([0.0, 0.0, 0.0], [50.0, 0.0, 0.0], 100.0)
        assert abs(cost - expected) < TOLERANCE

    def test_sell_trade_returns_cash(self) -> None:
        """Sell has negative cost (trader receives money)."""
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        # Buy first
        engine.execute_trade(market, "agent_01", 0, 50.0)
        # Sell back
        sell = engine.execute_trade(market, "agent_01", 0, -25.0)
        assert sell.cost < 0  # trader gets money back

    def test_multiple_trades_accumulate(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        engine.execute_trade(market, "agent_01", 0, 20.0)
        engine.execute_trade(market, "agent_01", 1, 10.0)

        assert market.x[0] == 20.0
        assert market.x[1] == 10.0
        assert market.x[2] == 0.0

    def test_trade_ids_increment(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        t1 = engine.execute_trade(market, "agent_01", 0, 10.0)
        t2 = engine.execute_trade(market, "agent_01", 1, 10.0)
        assert t1.trade_id == "trd_000001"
        assert t2.trade_id == "trd_000002"


class TestTradeValidation:
    """Trade rejection tests."""

    def test_trading_halted_when_not_trading(self) -> None:
        market = MarketLifecycle.create_market(
            "m", "t", 100.0, 2, ["A", "B"]
        )
        MarketLifecycle.commit(market)
        # Market is COMMITTED, not TRADING
        pm = PositionManager(2, market.market_id)
        engine = TradingEngine(pm)

        with pytest.raises(TradingHalted) as exc_info:
            engine.execute_trade(market, "agent_01", 0, 10.0)
        assert exc_info.value.current_phase == MarketPhase.COMMITTED

    def test_invalid_outcome_index_raises(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        with pytest.raises(InvalidMarketParameters, match="outcome_index"):
            engine.execute_trade(market, "agent_01", 5, 10.0)

    def test_zero_shares_raises(self) -> None:
        market, pm, engine = _make_trading_market()

        with pytest.raises(InvalidMarketParameters, match="non-zero"):
            engine.execute_trade(market, "agent_01", 0, 0.0)

    def test_insufficient_balance_rejects_buy(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1.0)  # too little

        with pytest.raises(InsufficientBalance) as exc_info:
            engine.execute_trade(market, "agent_01", 0, 50.0)
        assert exc_info.value.available == 1.0
        assert exc_info.value.required > 1.0

    def test_insufficient_shares_rejects_sell(self) -> None:
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1000.0)

        # Agent holds 0 shares — can't sell
        with pytest.raises(InsufficientShares) as exc_info:
            engine.execute_trade(market, "agent_01", 0, -10.0)
        assert exc_info.value.outcome_index == 0
        assert exc_info.value.available == 0.0

    def test_atomic_execution_on_failure(self) -> None:
        """Market state unchanged after failed trade."""
        market, pm, engine = _make_trading_market()
        pm.set_balance("agent_01", 1.0)  # can't afford

        x_before = list(market.x)

        with pytest.raises(InsufficientBalance):
            engine.execute_trade(market, "agent_01", 0, 50.0)

        assert market.x == x_before  # unchanged
