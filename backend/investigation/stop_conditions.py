"""Stop Condition Evaluator — determines when an investigation is ready for resolution.

Only reads committed stop_config — no runtime overrides accepted.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.investigation.certificate import StopCondition
from backend.investigation.claim_graph import ClaimGraph, ClaimStatus
from backend.investigation.evidence_envelope import EvidenceEnvelope


class InvestigationStopConditionEvaluator:
    """Evaluate investigation stop conditions against current state.

    Stop condition types:
    - OUTCOME_RESOLUTION: ready when time_remaining <= 0
    - EVIDENCE_THRESHOLD: ready when claim graph meets stop_config thresholds
      (min_supported_claims, min_corroboration_score)
    - SPONSOR_DEFINED: ready when milestone_timestamp reached

    Only reads committed stop_config keys. No runtime overrides accepted.
    """

    def evaluate(
        self,
        stop_condition: str,
        stop_config: dict,
        claim_graph: ClaimGraph,
        evidence_envelope: EvidenceEnvelope,
        time_remaining: float,
    ) -> tuple[bool, str]:
        """Evaluate whether the investigation is ready for resolution.

        Args:
            stop_condition: One of StopCondition enum values.
            stop_config: Committed configuration for the stop condition.
            claim_graph: Current claim graph state.
            evidence_envelope: Current evidence envelope state.
            time_remaining: Seconds remaining until time-based deadline.
                           Negative means deadline has passed.

        Returns:
            (ready, reason) — True with reason if ready, False with reason if not.
        """
        condition = StopCondition(stop_condition)

        if condition == StopCondition.OUTCOME_RESOLUTION:
            return self._evaluate_outcome_resolution(time_remaining)
        elif condition == StopCondition.EVIDENCE_THRESHOLD:
            return self._evaluate_evidence_threshold(stop_config, claim_graph)
        elif condition == StopCondition.SPONSOR_DEFINED:
            return self._evaluate_sponsor_defined(stop_config)
        else:
            return False, f"unknown_stop_condition:{stop_condition}"

    def _evaluate_outcome_resolution(
        self,
        time_remaining: float,
    ) -> tuple[bool, str]:
        """OUTCOME_RESOLUTION: ready when time_remaining <= 0."""
        if time_remaining <= 0:
            return True, "time_window_expired"
        return False, f"time_remaining:{time_remaining:.0f}s"

    def _evaluate_evidence_threshold(
        self,
        stop_config: dict,
        claim_graph: ClaimGraph,
    ) -> tuple[bool, str]:
        """EVIDENCE_THRESHOLD: ready when claim graph meets thresholds.

        stop_config keys:
        - min_supported_claims: minimum number of SUPPORTED claims required
        - min_corroboration_score: minimum fraction of claims that are SUPPORTED (0-1)
        """
        min_supported = stop_config.get("min_supported_claims", 1)
        min_score = stop_config.get("min_corroboration_score", 0.0)

        status_summary = claim_graph.get_status_summary()
        supported_count = status_summary.get(ClaimStatus.SUPPORTED.value, 0)
        total_claims = len(claim_graph.claims)

        if total_claims == 0:
            return False, "no_claims_registered"

        corroboration_score = supported_count / total_claims

        if supported_count < min_supported:
            return False, (
                f"supported_claims:{supported_count}/{min_supported}"
            )

        if corroboration_score < min_score:
            return False, (
                f"corroboration_score:{corroboration_score:.2f}/{min_score:.2f}"
            )

        return True, "evidence_threshold_met"

    def _evaluate_sponsor_defined(
        self,
        stop_config: dict,
    ) -> tuple[bool, str]:
        """SPONSOR_DEFINED: ready when milestone_timestamp reached.

        stop_config keys:
        - milestone_timestamp: ISO 8601 timestamp string
        """
        milestone_str = stop_config.get("milestone_timestamp")
        if milestone_str is None:
            return False, "no_milestone_timestamp_configured"

        milestone = datetime.fromisoformat(milestone_str)
        # Strip timezone for naive comparison (DB uses TIMESTAMP WITHOUT TIME ZONE)
        if milestone.tzinfo is not None:
            milestone = milestone.replace(tzinfo=None)

        now = datetime.utcnow()
        if now >= milestone:
            return True, "milestone_reached"
        return False, f"milestone_not_reached:{milestone_str}"
