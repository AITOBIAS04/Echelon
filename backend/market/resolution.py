"""Resolution and settlement — deterministic payout computation.

Resolution (TRADING → RESOLVING) is handled by MarketLifecycle.begin_resolution().
This module handles settlement: computing payouts and generating SettlementReport.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from theatre.engine.canonical_json import canonical_json

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase, MarketState


@dataclass
class AgentSettlement:
    """Per-agent settlement record."""

    agent_id: str
    shares_held: list[float]
    winning_shares: float
    payout: float
    net_cashflow: float
    realised_pnl: float


@dataclass
class SettlementReport:
    """Deterministic settlement report for a resolved market."""

    market_id: str
    winning_outcome: int
    winning_label: str
    total_payout: float
    market_maker_pnl: float
    agent_settlements: list[AgentSettlement]
    commitment_hash: str
    settlement_hash: str


class ResolutionEngine:
    """Deterministic market settlement."""

    @staticmethod
    def settle(
        market: MarketState,
        position_manager: PositionManager,
    ) -> SettlementReport:
        """Compute payouts, transition to SETTLED, return report.

        Preconditions: market.phase == RESOLVING, resolved_outcome is set.
        """
        resolved_outcome = market.resolved_outcome

        # Build per-agent settlements
        agent_settlements: list[AgentSettlement] = []
        total_payout = 0.0
        total_cashflow = 0.0

        for position in position_manager.all_positions():
            winning_shares = position_manager.compute_settlement_payout(
                position, resolved_outcome
            )
            payout = winning_shares
            realised_pnl = payout - position.net_cashflow

            agent_settlements.append(
                AgentSettlement(
                    agent_id=position.agent_id,
                    shares_held=list(position.shares),
                    winning_shares=winning_shares,
                    payout=payout,
                    net_cashflow=position.net_cashflow,
                    realised_pnl=realised_pnl,
                )
            )

            total_payout += payout
            total_cashflow += position.net_cashflow

        market_maker_pnl = total_cashflow - total_payout

        # Compute settlement hash
        settlement_composite = {
            "market_id": market.market_id,
            "winning_outcome": resolved_outcome,
            "agent_settlements": [
                {
                    "agent_id": s.agent_id,
                    "winning_shares": s.winning_shares,
                    "payout": s.payout,
                    "net_cashflow": s.net_cashflow,
                    "realised_pnl": s.realised_pnl,
                }
                for s in agent_settlements
            ],
        }
        canonical = canonical_json(settlement_composite)
        settlement_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        # Transition to SETTLED
        MarketLifecycle.settle(market)

        return SettlementReport(
            market_id=market.market_id,
            winning_outcome=resolved_outcome,
            winning_label=market.outcome_labels[resolved_outcome],
            total_payout=total_payout,
            market_maker_pnl=market_maker_pnl,
            agent_settlements=agent_settlements,
            commitment_hash=market.commitment_hash or "",
            settlement_hash=settlement_hash,
        )
