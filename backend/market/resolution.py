"""Resolution and settlement — deterministic payout computation.

Resolution (TRADING → RESOLVING) is handled by MarketLifecycle.begin_resolution().
This module handles settlement: computing payouts and generating SettlementReport.

Cycle-014, Sprint 2 — Task 1: Inquiry-class-aware resolution triggers.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

from backend.utils.canonical_json import canonical_json

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase, MarketState


class ResolutionTrigger(str, Enum):
    """Why a market became ready for resolution.

    Each inquiry class has a primary trigger type, but time_window_closed
    is a universal fallback.
    """

    SIMULATION_TERMINAL = "simulation_terminal"
    EVIDENCE_THRESHOLD_MET = "evidence_threshold_met"
    CRITERIA_COMPLETE = "criteria_complete"
    PARTICIPATION_THRESHOLD = "participation_threshold"
    CLAIM_VERDICT = "claim_verdict"
    TIME_WINDOW_CLOSED = "time_window_closed"
    STOP_CONDITION_MET = "stop_condition_met"

    def __str__(self) -> str:
        return self.value


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
    inquiry_class: str = "COUNTERFACTUAL"
    resolution_trigger_reason: str = "simulation_terminal"


class ResolutionEngine:
    """Deterministic market settlement with inquiry-class-aware triggers."""

    @staticmethod
    def check_resolution_ready(
        inquiry_class: str,
        evidence_state: dict,
        theatre_config: dict,
        stop_condition: str | None = None,
        stop_config: dict | None = None,
        claim_graph: "ClaimGraph | None" = None,
        evidence_envelope: "EvidenceEnvelope | None" = None,
        time_remaining: float | None = None,
    ) -> Tuple[bool, ResolutionTrigger]:
        """Evaluate whether a market is ready for resolution.

        Each inquiry class has distinct resolution logic per SDD section 6.3.

        Args:
            inquiry_class: One of the 5 canonical inquiry classes.
            evidence_state: Dict with keys like evidence_coverage_pct,
                criteria_evaluated, criteria_total, participation_count,
                claim_verdict, time_window_expired.
            theatre_config: Theatre configuration dict with thresholds.
            stop_condition: Optional stop condition type from theatre record.
            stop_config: Optional stop condition config from theatre record.
            claim_graph: Optional ClaimGraph for stop-condition evaluation.
            evidence_envelope: Optional EvidenceEnvelope for stop-condition evaluation.
            time_remaining: Optional seconds remaining for time-based stop conditions.

        Returns:
            (ready, trigger_reason) tuple.
        """
        ic = inquiry_class.upper().strip()
        time_expired = evidence_state.get("time_window_expired", False)

        # Stop-condition evaluation — scoped to INVESTIGATIVE only.
        # Other inquiry classes ignore stop_condition/stop_config entirely.
        if stop_condition is not None and ic == "INVESTIGATIVE":
            # Object-graph path (unit/advanced use with full investigation runtime)
            if claim_graph is not None and evidence_envelope is not None:
                from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
                evaluator = InvestigationStopConditionEvaluator()
                sc_ready, _ = evaluator.evaluate(
                    stop_condition=stop_condition,
                    stop_config=stop_config or {},
                    claim_graph=claim_graph,
                    evidence_envelope=evidence_envelope,
                    time_remaining=time_remaining if time_remaining is not None else -1.0,
                )
                if sc_ready:
                    return True, ResolutionTrigger.STOP_CONDITION_MET
            else:
                # Scalar path (production settle flows using evidence_state dict)
                sc_ready = ResolutionEngine._evaluate_stop_condition_scalar(
                    stop_condition=stop_condition,
                    stop_config=stop_config or {},
                    evidence_state=evidence_state,
                    time_remaining=time_remaining,
                )
                if sc_ready:
                    return True, ResolutionTrigger.STOP_CONDITION_MET

        if ic == "COUNTERFACTUAL":
            # Simulation terminal state or evidence threshold
            if evidence_state.get("simulation_terminal", False):
                return True, ResolutionTrigger.SIMULATION_TERMINAL
            threshold = theatre_config.get("evidence_threshold", 0.8)
            coverage = evidence_state.get("evidence_coverage_pct", 0.0)
            if coverage >= threshold:
                return True, ResolutionTrigger.EVIDENCE_THRESHOLD_MET
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.TIME_WINDOW_CLOSED

        elif ic == "INVESTIGATIVE":
            # Evidence coverage >= corroboration_minimum OR time window closed
            corroboration_min = theatre_config.get("corroboration_minimum", 2)
            distinct_sources = evidence_state.get("distinct_source_count", 0)
            threshold = theatre_config.get("evidence_threshold", 0.8)
            coverage = evidence_state.get("evidence_coverage_pct", 0.0)
            if distinct_sources >= corroboration_min and coverage >= threshold:
                return True, ResolutionTrigger.EVIDENCE_THRESHOLD_MET
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.TIME_WINDOW_CLOSED

        elif ic == "INSPECTION":
            # All committed criteria evaluated
            evaluated = evidence_state.get("criteria_evaluated", 0)
            total = evidence_state.get("criteria_total", 0)
            if total > 0 and evaluated >= total:
                return True, ResolutionTrigger.CRITERIA_COMPLETE
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.CRITERIA_COMPLETE

        elif ic == "SURVEY":
            # Participation threshold or time window closes
            participation = evidence_state.get("participation_count", 0)
            threshold = theatre_config.get("participation_threshold", 10)
            if participation >= threshold:
                return True, ResolutionTrigger.PARTICIPATION_THRESHOLD
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.PARTICIPATION_THRESHOLD

        elif ic == "SCRUTINY":
            # Claim verdict reached (verified or falsified) or time window closed
            verdict = evidence_state.get("claim_verdict")
            if verdict in ("verified", "falsified"):
                return True, ResolutionTrigger.CLAIM_VERDICT
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.CLAIM_VERDICT

        else:
            # Unknown inquiry class — fall back to COUNTERFACTUAL behaviour
            if time_expired:
                return True, ResolutionTrigger.TIME_WINDOW_CLOSED
            return False, ResolutionTrigger.TIME_WINDOW_CLOSED

    @staticmethod
    def _evaluate_stop_condition_scalar(
        stop_condition: str,
        stop_config: dict,
        evidence_state: dict,
        time_remaining: float | None,
    ) -> bool:
        """Evaluate stop-condition readiness using scalar evidence_state fields.

        This is the production path — no ClaimGraph/EvidenceEnvelope required.
        Returns True if the stop condition is satisfied, False otherwise.
        Invalid/unknown stop_condition values fail safely (return False).
        """
        sc = stop_condition.upper().strip()

        if sc == "OUTCOME_RESOLUTION":
            if evidence_state.get("time_window_expired", False):
                return True
            if time_remaining is not None and time_remaining <= 0:
                return True
            return False

        if sc == "EVIDENCE_THRESHOLD":
            min_supported = stop_config.get("min_supported_claims", 1)
            min_score = stop_config.get("min_corroboration_score", 0.0)
            supported = evidence_state.get("supported_claims", 0)
            score = evidence_state.get("corroboration_score", 0.0)
            return supported >= min_supported and score >= min_score

        if sc == "SPONSOR_DEFINED":
            from datetime import datetime, timezone
            milestone_str = stop_config.get("milestone_timestamp")
            if milestone_str is None:
                return False
            try:
                milestone = datetime.fromisoformat(
                    str(milestone_str).replace("Z", "+00:00")
                )
                if milestone.tzinfo is None:
                    milestone = milestone.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return False
            # Allow deterministic test override via evidence_state
            current_time_str = evidence_state.get("current_time")
            if current_time_str is not None:
                try:
                    now = datetime.fromisoformat(
                        str(current_time_str).replace("Z", "+00:00")
                    )
                    if now.tzinfo is None:
                        now = now.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    now = datetime.utcnow()
            else:
                now = datetime.utcnow()
            return now >= milestone

        # Unknown stop condition — fail safely
        return False

    @staticmethod
    def settle(
        market: MarketState,
        position_manager: PositionManager,
        inquiry_class: str = "COUNTERFACTUAL",
        resolution_trigger_reason: str = "simulation_terminal",
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
            inquiry_class=inquiry_class,
            resolution_trigger_reason=resolution_trigger_reason,
        )
