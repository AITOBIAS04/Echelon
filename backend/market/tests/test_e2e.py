"""End-to-end lifecycle tests — full market lifecycle integration."""
from __future__ import annotations

import math

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine
from backend.market.state import MarketPhase
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9


class TestFullLifecycleSingleAgent:
    """Single agent: create → commit → trade → resolve → settle."""

    def test_full_lifecycle_single_agent(self) -> None:
        # Create market
        market = MarketLifecycle.create_market(
            "mkt_001", "theatre_001", 100.0, 3, ["Yes", "No", "Maybe"]
        )
        assert market.phase == MarketPhase.CREATED

        # Commit
        MarketLifecycle.commit(market)
        assert market.phase == MarketPhase.COMMITTED

        # Open trading
        MarketLifecycle.open_trading(market)
        assert market.phase == MarketPhase.TRADING

        # Set up trading
        pm = PositionManager(3, market.market_id)
        engine = TradingEngine(pm)
        pm.set_balance("agent_01", 500.0)

        # Execute trade: buy 50 shares of outcome 0
        trade = engine.execute_trade(market, "agent_01", 0, 50.0)
        assert trade.cost > 0

        # Verify position
        pos = pm.get_position("agent_01")
        assert pos.shares[0] == 50.0
        assert pos.trade_count == 1

        # Resolve: outcome 0 wins
        MarketLifecycle.begin_resolution(market, winning_outcome=0)
        assert market.phase == MarketPhase.RESOLVING

        # Settle
        report = ResolutionEngine.settle(market, pm)
        assert market.phase == MarketPhase.SETTLED

        # Verify P&L
        a1 = report.agent_settlements[0]
        assert a1.payout == 50.0  # 50 winning shares
        assert abs(a1.realised_pnl - (50.0 - a1.net_cashflow)) < TOLERANCE


class TestFullLifecycleMultipleAgents:
    """Three agents trade, one wins."""

    def test_full_lifecycle_multiple_agents(self) -> None:
        market = MarketLifecycle.create_market(
            "mkt_002", "theatre_002", 100.0, 3, ["Yes", "No", "Maybe"]
        )
        MarketLifecycle.commit(market)
        MarketLifecycle.open_trading(market)

        pm = PositionManager(3, market.market_id)
        engine = TradingEngine(pm)
        pm.set_balance("agent_01", 500.0)
        pm.set_balance("agent_02", 500.0)
        pm.set_balance("agent_03", 500.0)

        # Agent 1 bets on outcome 0 (will win)
        engine.execute_trade(market, "agent_01", 0, 40.0)
        # Agent 2 bets on outcome 1 (will lose)
        engine.execute_trade(market, "agent_02", 1, 30.0)
        # Agent 3 bets on outcome 2 (will lose)
        engine.execute_trade(market, "agent_03", 2, 20.0)

        # Resolve: outcome 0 wins
        MarketLifecycle.begin_resolution(market, winning_outcome=0)
        report = ResolutionEngine.settle(market, pm)

        # Agent 1 wins
        a1 = next(s for s in report.agent_settlements if s.agent_id == "agent_01")
        assert a1.payout == 40.0
        assert a1.realised_pnl > 0  # profit

        # Agent 2 loses
        a2 = next(s for s in report.agent_settlements if s.agent_id == "agent_02")
        assert a2.payout == 0.0
        assert a2.realised_pnl < 0  # loss

        # Agent 3 loses
        a3 = next(s for s in report.agent_settlements if s.agent_id == "agent_03")
        assert a3.payout == 0.0
        assert a3.realised_pnl < 0  # loss

        # Market maker bounded loss
        worst = LMSREngine.worst_case_loss(100.0, 3)
        assert report.market_maker_pnl >= -worst - TOLERANCE


class TestLifecycleWithBuysAndSells:
    """Agent buys then sells, verify correct settlement."""

    def test_lifecycle_with_buys_and_sells(self) -> None:
        market = MarketLifecycle.create_market(
            "mkt_003", "theatre_003", 100.0, 2, ["Yes", "No"]
        )
        MarketLifecycle.commit(market)
        MarketLifecycle.open_trading(market)

        pm = PositionManager(2, market.market_id)
        engine = TradingEngine(pm)
        pm.set_balance("agent_01", 500.0)

        # Buy 50 shares of outcome 0
        buy = engine.execute_trade(market, "agent_01", 0, 50.0)
        # Sell 20 back
        sell = engine.execute_trade(market, "agent_01", 0, -20.0)

        pos = pm.get_position("agent_01")
        assert abs(pos.shares[0] - 30.0) < TOLERANCE
        assert abs(pos.net_cashflow - (buy.cost + sell.cost)) < TOLERANCE

        # Resolve: outcome 0 wins
        MarketLifecycle.begin_resolution(market, winning_outcome=0)
        report = ResolutionEngine.settle(market, pm)

        a1 = report.agent_settlements[0]
        assert abs(a1.payout - 30.0) < TOLERANCE  # 30 winning shares
        assert abs(a1.realised_pnl - (30.0 - pos.net_cashflow)) < TOLERANCE


class TestMultipleOutcomesMarket:
    """5-outcome market with mixed trades."""

    def test_multiple_outcomes_market(self) -> None:
        market = MarketLifecycle.create_market(
            "mkt_004", "theatre_004", 200.0, 5,
            ["A", "B", "C", "D", "E"]
        )
        MarketLifecycle.commit(market)
        MarketLifecycle.open_trading(market)

        pm = PositionManager(5, market.market_id)
        engine = TradingEngine(pm)
        pm.set_balance("agent_01", 5000.0)
        pm.set_balance("agent_02", 5000.0)

        # Agent 1 buys across multiple outcomes
        engine.execute_trade(market, "agent_01", 0, 10.0)
        engine.execute_trade(market, "agent_01", 2, 20.0)
        engine.execute_trade(market, "agent_01", 4, 15.0)

        # Agent 2 concentrates on one outcome
        engine.execute_trade(market, "agent_02", 3, 50.0)

        # Resolve: outcome 2 wins
        MarketLifecycle.begin_resolution(market, winning_outcome=2)
        report = ResolutionEngine.settle(market, pm)

        a1 = next(s for s in report.agent_settlements if s.agent_id == "agent_01")
        a2 = next(s for s in report.agent_settlements if s.agent_id == "agent_02")

        # Agent 1 has 20 shares on winning outcome 2
        assert abs(a1.payout - 20.0) < TOLERANCE
        # Agent 2 has 0 shares on winning outcome 2
        assert a2.payout == 0.0

        # All identities hold
        total_cf = sum(s.net_cashflow for s in report.agent_settlements)
        assert abs(report.market_maker_pnl - (total_cf - report.total_payout)) < TOLERANCE
