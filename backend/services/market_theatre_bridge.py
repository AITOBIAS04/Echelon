"""Market-Theatre Bridge — LMSR engine <-> Theatre lifecycle integration.

Wraps MarketLifecycle, TradingEngine, PositionManager, and ResolutionEngine
behind a Theatre-aware facade. Stores TheatreMarketState triples keyed by
theatre_id. All LMSR access for a Theatre flows through this bridge.

Cycle-012, Sprint 1 — Theatre Creation + LMSR Wiring.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from backend.market.exceptions import InvalidPhaseTransition
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine, SettlementReport
from backend.market.state import FeeSchedule, MarketPhase, MarketState
from backend.market.trading import TradingEngine


@dataclass
class TheatreMarketState:
    """Bundled LMSR state for a single Theatre.

    Wraps MarketState + PositionManager + TradingEngine into a single
    object for Theatre-keyed access.
    """

    market: MarketState
    position_manager: PositionManager
    trading_engine: TradingEngine


class MarketTheatreBridge:
    """Bridge connecting the LMSR engine to the Theatre lifecycle.

    Stores Theatre-keyed market state and mediates all LMSR operations.
    In-memory only — no persistence layer.
    """

    def __init__(self) -> None:
        self._theatres: dict[str, TheatreMarketState] = {}

    def create_market_for_theatre(
        self,
        theatre_id: str,
        market_id: str,
        b: float,
        n_outcomes: int,
        outcome_labels: list[str],
        fee_schedule: FeeSchedule | None = None,
    ) -> TheatreMarketState:
        """Create an LMSR market for a Theatre.

        Delegates to MarketLifecycle.create_market() without modification.
        Returns the bundled TheatreMarketState.
        """
        market = MarketLifecycle.create_market(
            market_id=market_id,
            theatre_id=theatre_id,
            b=b,
            n_outcomes=n_outcomes,
            outcome_labels=outcome_labels,
            fee_schedule=fee_schedule,
        )

        position_manager = PositionManager(
            n_outcomes=n_outcomes,
            market_id=market_id,
        )

        trading_engine = TradingEngine(position_manager=position_manager)

        state = TheatreMarketState(
            market=market,
            position_manager=position_manager,
            trading_engine=trading_engine,
        )
        self._theatres[theatre_id] = state
        return state

    def get_market_state(self, theatre_id: str) -> TheatreMarketState | None:
        """Get the bundled market state for a Theatre."""
        return self._theatres.get(theatre_id)

    def transition_market(
        self, theatre_id: str, target_phase: MarketPhase
    ) -> MarketState:
        """Execute a phase transition for a Theatre's market.

        Delegates to the appropriate MarketLifecycle static method.
        Supports: CREATED->COMMITTED, COMMITTED->TRADING, TRADING->RESOLVING.
        """
        state = self._theatres.get(theatre_id)
        if state is None:
            raise ValueError(f"No market found for theatre '{theatre_id}'")

        market = state.market

        if target_phase == MarketPhase.COMMITTED:
            return MarketLifecycle.commit(market)
        elif target_phase == MarketPhase.TRADING:
            return MarketLifecycle.open_trading(market)
        else:
            raise InvalidPhaseTransition(
                current=market.phase, target=target_phase
            )

    def settle_market(
        self,
        theatre_id: str,
        winning_outcome: int,
        inquiry_class: str = "COUNTERFACTUAL",
        evidence_state: dict | None = None,
        theatre_config: dict | None = None,
        force: bool = False,
        stop_condition: str | None = None,
        stop_config: dict | None = None,
        claim_graph: object | None = None,
        evidence_envelope: object | None = None,
        time_remaining: float | None = None,
    ) -> SettlementReport:
        """Check resolution readiness, begin resolution, and settle.

        Calls check_resolution_ready() to determine the trigger reason.
        Refuses settlement if not ready unless force=True.

        Args:
            theatre_id: Theatre whose market to settle.
            winning_outcome: Index of the winning outcome.
            inquiry_class: Inquiry class from the theatre record.
            evidence_state: Evidence snapshot for check_resolution_ready().
                If None, defaults to time_window_expired=True (manual settle).
            theatre_config: Theatre configuration for resolution thresholds.
                If None, uses empty dict (defaults apply).
            force: If True, bypass readiness check (logged as warning).
        """
        state = self._theatres.get(theatre_id)
        if state is None:
            raise ValueError(f"No market found for theatre '{theatre_id}'")

        if evidence_state is None:
            evidence_state = {"time_window_expired": True}
        if theatre_config is None:
            theatre_config = {}

        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class=inquiry_class,
            evidence_state=evidence_state,
            theatre_config=theatre_config,
            stop_condition=stop_condition,
            stop_config=stop_config,
            claim_graph=claim_graph,
            evidence_envelope=evidence_envelope,
            time_remaining=time_remaining,
        )

        if not ready and not force:
            raise ValueError(
                f"Settlement refused: resolution not ready for "
                f"inquiry_class={inquiry_class}. Trigger={trigger}. "
                f"Pass force=True to override."
            )

        if not ready and force:
            import logging
            logging.getLogger(__name__).warning(
                "Theatre %s settled with force=True despite not ready "
                "(inquiry_class=%s, trigger=%s)",
                theatre_id, inquiry_class, trigger,
            )

        MarketLifecycle.begin_resolution(state.market, winning_outcome)
        return ResolutionEngine.settle(
            state.market,
            state.position_manager,
            inquiry_class=inquiry_class,
            resolution_trigger_reason=str(trigger),
        )

    def serialise_state(self, theatre_id: str) -> dict:
        """Serialise a Theatre's market state to a JSON-compatible dict.

        Preserves all MarketState fields for storage/recovery.
        """
        state = self._theatres.get(theatre_id)
        if state is None:
            raise ValueError(f"No market found for theatre '{theatre_id}'")

        market = state.market
        return {
            "market_id": market.market_id,
            "theatre_id": market.theatre_id,
            "b": market.b,
            "n_outcomes": market.n_outcomes,
            "outcome_labels": list(market.outcome_labels),
            "x": list(market.x),
            "phase": market.phase.value,
            "fee_schedule": {
                "trade_fee_bps": market.fee_schedule.trade_fee_bps,
                "resolution_fee_bps": market.fee_schedule.resolution_fee_bps,
            },
            "commitment_hash": market.commitment_hash,
            "resolved_outcome": market.resolved_outcome,
            "created_at": market.created_at,
            "committed_at": market.committed_at,
            "trading_opened_at": market.trading_opened_at,
            "resolved_at": market.resolved_at,
            "settled_at": market.settled_at,
        }

    def deserialise_state(self, data: dict) -> MarketState:
        """Reconstruct a MarketState from a serialised dict.

        Does not restore PositionManager or TradingEngine state —
        those are ephemeral and rebuilt per session.
        """
        return MarketState(
            market_id=data["market_id"],
            theatre_id=data["theatre_id"],
            b=data["b"],
            n_outcomes=data["n_outcomes"],
            outcome_labels=data["outcome_labels"],
            x=data["x"],
            phase=MarketPhase(data["phase"]),
            fee_schedule=FeeSchedule(
                trade_fee_bps=data["fee_schedule"]["trade_fee_bps"],
                resolution_fee_bps=data["fee_schedule"]["resolution_fee_bps"],
            ),
            commitment_hash=data.get("commitment_hash"),
            resolved_outcome=data.get("resolved_outcome"),
            created_at=data.get("created_at", ""),
            committed_at=data.get("committed_at"),
            trading_opened_at=data.get("trading_opened_at"),
            resolved_at=data.get("resolved_at"),
            settled_at=data.get("settled_at"),
        )
