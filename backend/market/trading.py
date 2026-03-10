"""Trade execution engine — validates and executes trades against LMSR markets.

Not pure: mutates MarketState.x and updates positions via PositionManager.
Execution is atomic: if any validation fails, no state is mutated.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.market.exceptions import (
    InsufficientBalance,
    InsufficientShares,
    InvalidMarketParameters,
    TradingHalted,
)
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase, MarketState


@dataclass
class Trade:
    """Record of an executed trade."""

    trade_id: str
    market_id: str
    agent_id: str
    outcome_index: int
    shares: float
    cost: float
    pre_trade_prices: list[float]
    post_trade_prices: list[float]
    timestamp: str


class TradingEngine:
    """Executes trades against LMSR markets."""

    def __init__(self, position_manager: PositionManager) -> None:
        self._position_manager = position_manager
        self._trade_counter = 0

    def execute_trade(
        self,
        market: MarketState,
        agent_id: str,
        outcome_index: int,
        shares: float,
    ) -> Trade:
        """Validate → compute cost → update x → update position → return Trade.

        Atomic: if any validation fails, no state is mutated.
        """
        # 1. Phase check
        if market.phase != MarketPhase.TRADING:
            raise TradingHalted(market.phase)

        # 2. Outcome index range
        if not (0 <= outcome_index < market.n_outcomes):
            raise InvalidMarketParameters(
                f"outcome_index must be in [0, {market.n_outcomes}), "
                f"got {outcome_index}"
            )

        # 3. Non-zero shares
        if shares == 0.0:
            raise InvalidMarketParameters("shares must be non-zero")

        # 4. Build one-hot delta and compute cost
        delta = [0.0] * market.n_outcomes
        delta[outcome_index] = shares
        cost = LMSREngine.trade_cost(market.x, delta, market.b)

        # 5. Sell inventory check
        if shares < 0:
            position = self._position_manager.get_position(agent_id)
            held = position.shares[outcome_index]
            required = abs(shares)
            if held < required:
                raise InsufficientShares(outcome_index, required, held)

        # 6. Buy balance check
        if cost > 0:
            available = self._position_manager.get_balance(agent_id)
            if available < cost:
                raise InsufficientBalance(cost, available)

        # --- All validation passed. Mutate state. ---

        pre_trade_prices = LMSREngine.prices(market.x, market.b)

        # Update market x vector
        market.x[outcome_index] += shares

        post_trade_prices = LMSREngine.prices(market.x, market.b)

        # Create trade record
        self._trade_counter += 1
        trade = Trade(
            trade_id=f"trd_{self._trade_counter:06d}",
            market_id=market.market_id,
            agent_id=agent_id,
            outcome_index=outcome_index,
            shares=shares,
            cost=cost,
            pre_trade_prices=pre_trade_prices,
            post_trade_prices=post_trade_prices,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Update position
        self._position_manager.update_position(trade)

        return trade

    def quote(
        self,
        market: MarketState,
        outcome_index: int,
        shares: float,
    ) -> float:
        """Pre-trade cost quote. Pure — does not execute or validate balances."""
        delta = [0.0] * market.n_outcomes
        delta[outcome_index] = shares
        return LMSREngine.trade_cost(market.x, delta, market.b)
