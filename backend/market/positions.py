"""Agent position tracking — shares, cashflow, P&L per agent per market.

In-memory storage for 010a. One PositionManager instance per market session.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentPosition:
    """Net position for a single agent in a single market."""

    agent_id: str
    market_id: str
    shares: list[float]
    net_cashflow: float = 0.0
    realised_pnl: float = 0.0
    trade_count: int = 0


class PositionManager:
    """In-memory position tracking for a single market."""

    def __init__(self, n_outcomes: int, market_id: str) -> None:
        self._n_outcomes = n_outcomes
        self._market_id = market_id
        self._positions: dict[str, AgentPosition] = {}
        self._initial_balances: dict[str, float] = {}

    def set_balance(self, agent_id: str, balance: float) -> None:
        """Set initial cash balance for an agent."""
        self._initial_balances[agent_id] = balance

    def get_balance(self, agent_id: str) -> float:
        """Current cash balance = initial - net_cashflow."""
        initial = self._initial_balances.get(agent_id, 0.0)
        pos = self._positions.get(agent_id)
        if pos is None:
            return initial
        return initial - pos.net_cashflow

    def get_position(self, agent_id: str) -> AgentPosition:
        """Get existing position or create zero-filled one."""
        if agent_id not in self._positions:
            self._positions[agent_id] = AgentPosition(
                agent_id=agent_id,
                market_id=self._market_id,
                shares=[0.0] * self._n_outcomes,
            )
        return self._positions[agent_id]

    def update_position(self, trade: "Trade") -> AgentPosition:
        """Apply a trade to the agent's position.

        Updates shares at the traded outcome, net_cashflow, and trade_count.
        """
        pos = self.get_position(trade.agent_id)
        pos.shares[trade.outcome_index] += trade.shares
        pos.net_cashflow += trade.cost
        pos.trade_count += 1
        return pos

    def compute_settlement_payout(
        self, position: AgentPosition, resolved_outcome: int
    ) -> float:
        """Winning shares pay 1:1. Losing shares pay 0. Min 0.0."""
        return max(0.0, position.shares[resolved_outcome])

    def all_positions(self) -> list[AgentPosition]:
        """All tracked agent positions."""
        return list(self._positions.values())
