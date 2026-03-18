"""Convergence Policy — compute per-dimension and run-level convergence outcomes.

Cycle 037b: Multi-Evaluator Orchestration + Residual Scoring.

Encodes convergence thresholds:
- 3/3 agreement on required dimensions → CONVERGED_PASS or CONVERGED_FAIL (HIGH)
- 2/3 agreement → converged with LOWER confidence
- 1/3 or fully split → DIVERGENT
- All ABSTAIN → SKIPPED

Produces DimensionConvergence per dimension and RunConvergenceSummary for the run.
"""

import logging
from collections import Counter
from typing import Optional

from backend.schemas.evaluator_orchestration import (
    DimensionConvergence,
    EvaluatorScoreRecord,
    RunConvergenceSummary,
)

logger = logging.getLogger(__name__)


def compute_dimension_convergence(
    dimension: str,
    records: list[EvaluatorScoreRecord],
) -> DimensionConvergence:
    """Compute convergence outcome for a single dimension.

    Rules:
    - All non-ABSTAIN verdicts agree → CONVERGED_PASS or CONVERGED_FAIL
    - Supermajority (≥2/3) agree → converged with LOWER confidence
    - No majority → DIVERGENT
    - All ABSTAIN → SKIPPED

    Args:
        dimension: Dimension name.
        records: Score records from all evaluators for this dimension.

    Returns:
        DimensionConvergence with outcome, confidence, and evaluator details.
    """
    evaluator_ids = [r.evaluator_id for r in records]
    verdicts = [r.verdict for r in records]
    scores = [r.score for r in records]

    # Filter out ABSTAINs for convergence computation
    active_verdicts = [v for v in verdicts if v != "ABSTAIN"]

    if not active_verdicts:
        return DimensionConvergence(
            dimension=dimension,
            outcome="SKIPPED",
            evaluator_ids=evaluator_ids,
            verdicts=verdicts,
            scores=scores,
        )

    # Count verdict frequencies
    counts = Counter(active_verdicts)
    total_active = len(active_verdicts)
    most_common_verdict, most_common_count = counts.most_common(1)[0]

    # Unanimous agreement
    if most_common_count == total_active:
        outcome = "CONVERGED_PASS" if most_common_verdict == "PASS" else "CONVERGED_FAIL"
        return DimensionConvergence(
            dimension=dimension,
            outcome=outcome,
            evaluator_ids=evaluator_ids,
            verdicts=verdicts,
            scores=scores,
            confidence="HIGH",
        )

    # Supermajority (≥2/3 of active)
    if most_common_count >= 2 and most_common_count / total_active >= 2 / 3:
        outcome = "CONVERGED_PASS" if most_common_verdict == "PASS" else "CONVERGED_FAIL"
        return DimensionConvergence(
            dimension=dimension,
            outcome=outcome,
            evaluator_ids=evaluator_ids,
            verdicts=verdicts,
            scores=scores,
            confidence="LOWER",
        )

    # No convergence
    return DimensionConvergence(
        dimension=dimension,
        outcome="DIVERGENT",
        evaluator_ids=evaluator_ids,
        verdicts=verdicts,
        scores=scores,
    )


def compute_run_convergence(
    dimension_results: list[DimensionConvergence],
    evaluator_ids: list[str],
    rubric_version: Optional[str] = None,
) -> RunConvergenceSummary:
    """Compute run-level convergence summary from per-dimension results.

    Escalation is required if any required dimension is DIVERGENT.

    Args:
        dimension_results: Per-dimension convergence outcomes.
        evaluator_ids: All evaluator IDs that participated.
        rubric_version: Optional rubric version string.

    Returns:
        RunConvergenceSummary with counts and escalation flag.
    """
    converged_pass = 0
    converged_fail = 0
    divergent = 0
    skipped = 0

    for dr in dimension_results:
        if dr.outcome == "CONVERGED_PASS":
            converged_pass += 1
        elif dr.outcome == "CONVERGED_FAIL":
            converged_fail += 1
        elif dr.outcome == "DIVERGENT":
            divergent += 1
        elif dr.outcome == "SKIPPED":
            skipped += 1

    escalation_required = divergent > 0

    summary = RunConvergenceSummary(
        evaluator_ids=evaluator_ids,
        total_dimensions=len(dimension_results),
        converged_pass=converged_pass,
        converged_fail=converged_fail,
        divergent=divergent,
        skipped=skipped,
        escalation_required=escalation_required,
        dimension_results=dimension_results,
        rubric_version=rubric_version,
    )

    logger.info(
        "Run convergence: %d dims — %d pass, %d fail, %d divergent, %d skipped (escalation=%s)",
        summary.total_dimensions, converged_pass, converged_fail,
        divergent, skipped, escalation_required,
    )
    return summary


def build_orchestration_persistence(
    records: list[EvaluatorScoreRecord],
    summary: RunConvergenceSummary,
) -> dict:
    """Build persistence payload for construct_meta_json storage.

    Returns a dict suitable for merging into investigation_evidence_items.construct_meta_json.

    Keys:
    - evaluator_scores: list of per-evaluator score record dicts
    - dimension_convergence: list of per-dimension convergence dicts
    - run_convergence_summary: run-level summary dict
    - rubric_version: version string
    - escalation_required: bool
    """
    return {
        "evaluator_scores": [
            {
                "evaluator_id": r.evaluator_id,
                "dimension": r.dimension,
                "verdict": r.verdict,
                "score": r.score,
                "rationale": r.rationale,
            }
            for r in records
        ],
        "dimension_convergence": [
            {
                "dimension": dc.dimension,
                "outcome": dc.outcome,
                "evaluator_ids": dc.evaluator_ids,
                "verdicts": dc.verdicts,
                "scores": dc.scores,
                "confidence": dc.confidence,
            }
            for dc in summary.dimension_results
        ],
        "run_convergence_summary": {
            "evaluator_ids": summary.evaluator_ids,
            "total_dimensions": summary.total_dimensions,
            "converged_pass": summary.converged_pass,
            "converged_fail": summary.converged_fail,
            "divergent": summary.divergent,
            "skipped": summary.skipped,
            "escalation_required": summary.escalation_required,
        },
        "rubric_version": summary.rubric_version,
        "escalation_required": summary.escalation_required,
    }
