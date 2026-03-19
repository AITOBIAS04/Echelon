"""Evaluator Integration — bridges multi-evaluator orchestration into certificate flow.

Cycle 037b: Multi-Evaluator Orchestration + Residual Scoring.

Provides the top-level function that the construct certification endpoint calls
to run the full orchestration pipeline:
  residual filtering → scorer execution → convergence → persistence payload

Also extends ConstructCertificate with evaluator_outcome for certificate enrichment.
"""

import logging
from typing import Optional

from backend.schemas.evaluator_orchestration import (
    DimensionConvergence,
    EvaluatorOutcome,
    EvaluatorScoreRecord,
    RunConvergenceSummary,
)
from backend.services.convergence_policy import (
    build_orchestration_persistence,
    compute_dimension_convergence,
    compute_run_convergence,
)
from backend.services.evaluator_orchestrator import (
    EvaluatorOrchestrator,
    ResidualScorer,
)
from backend.services.residual_dimension_filter import (
    ResidualDimension,
    filter_residual_dimensions,
)

logger = logging.getLogger(__name__)


async def run_evaluator_orchestration(
    *,
    planned_checks: list[dict],
    executed_results: dict,
    scorers: list[ResidualScorer],
    episode_payload: dict,
    rubric_version: Optional[str] = None,
) -> Optional[EvaluatorOutcome]:
    """Run the full multi-evaluator orchestration pipeline.

    Steps:
    1. Filter residual dimensions from planned checks
    2. Execute scorers over residual dimensions
    3. Compute per-dimension convergence
    4. Compute run-level summary
    5. Determine issuance eligibility

    Args:
        planned_checks: Contract's planned_checks list.
        executed_results: Domain → score for deterministically executed checks.
        scorers: List of ResidualScorer implementations.
        episode_payload: Construct episode data for scorer context.
        rubric_version: Optional rubric version for provenance.

    Returns:
        EvaluatorOutcome if residual dimensions exist, None if all deterministic.
    """
    # Step 1: Filter residual dimensions
    residuals = filter_residual_dimensions(planned_checks, executed_results)

    if not residuals:
        logger.info("No residual dimensions — all checks are deterministic")
        return None

    # Step 2: Execute scorers
    orchestrator = EvaluatorOrchestrator(scorers=scorers)
    records = await orchestrator.execute(
        dimensions=residuals,
        episode_payload=episode_payload,
    )

    # Step 3: Compute per-dimension convergence
    # Ensure every residual dimension has a convergence entry, even if scorers
    # omitted it. Missing dimensions get SKIPPED so they participate in blocking.
    grouped = orchestrator.group_by_dimension(records)
    dimension_results = []
    for rd in residuals:
        dim_records = grouped.get(rd.dimension)
        if dim_records:
            dimension_results.append(
                compute_dimension_convergence(rd.dimension, dim_records)
            )
        else:
            # Scorers returned nothing for this dimension — treat as SKIPPED
            logger.warning(
                "No scorer records for residual dimension %s — marking SKIPPED",
                rd.dimension,
            )
            dimension_results.append(
                DimensionConvergence(
                    dimension=rd.dimension,
                    outcome="SKIPPED",
                    evaluator_ids=orchestrator.evaluator_ids,
                    verdicts=[],
                    scores=[],
                )
            )

    # Step 4: Run-level summary
    summary = compute_run_convergence(
        dimension_results,
        evaluator_ids=orchestrator.evaluator_ids,
        rubric_version=rubric_version,
    )

    # Step 5: Determine issuance eligibility
    # Eligible if no critical dimensions are DIVERGENT, CONVERGED_FAIL, or SKIPPED
    _blocking_outcomes = {"DIVERGENT", "CONVERGED_FAIL", "SKIPPED"}
    critical_dims = {rd.dimension for rd in residuals if rd.critical}
    blocked_dims = [
        dr.dimension
        for dr in dimension_results
        if dr.outcome in _blocking_outcomes and dr.dimension in critical_dims
    ]

    block_reason = None
    if blocked_dims:
        block_reason = f"Critical dimensions blocked: {', '.join(blocked_dims)}"

    return EvaluatorOutcome(
        convergence_summary=summary,
        evaluator_scores=records,
        issuance_eligible=len(blocked_dims) == 0,
        block_reason=block_reason,
    )


def enrich_certificate_json(
    cert_json: dict,
    outcome: EvaluatorOutcome,
    records: list[EvaluatorScoreRecord],
    summary: RunConvergenceSummary,
) -> dict:
    """Enrich certificate JSON with evaluator orchestration data.

    Adds evaluator provenance fields to the certificate JSON for
    persistence in InvestigationCertificateRecord.certificate_json.

    Args:
        cert_json: Existing certificate JSON dict.
        outcome: EvaluatorOutcome from orchestration.
        records: All EvaluatorScoreRecord entries.
        summary: RunConvergenceSummary.

    Returns:
        Updated certificate JSON dict with evaluator fields.
    """
    persistence = build_orchestration_persistence(records, summary)
    enriched = dict(cert_json)
    enriched["evaluator_orchestration"] = persistence
    enriched["evaluator_issuance_eligible"] = outcome.issuance_eligible
    if outcome.block_reason:
        enriched["evaluator_block_reason"] = outcome.block_reason
    return enriched


def compute_final_issuance_status(
    base_status: str,
    evaluator_outcome: Optional[EvaluatorOutcome],
) -> str:
    """Compute final issuance status combining base (037) with evaluator outcome (037b).

    Rules:
    - REJECTED from base → stays REJECTED (verdict != PASS)
    - DEFERRED from base → stays DEFERRED (missing coverage)
    - READY from base + evaluator ineligible → BLOCKED (divergent scorers)
    - READY from base + evaluator eligible → READY (full pass)
    - READY from base + no evaluator outcome → READY (no residual dims)

    This preserves DEFERRED for missing coverage only (PRD section 2.4).
    """
    if base_status == "REJECTED":
        return "REJECTED"
    if base_status == "DEFERRED":
        return "DEFERRED"
    if evaluator_outcome is None:
        return base_status  # No residual dims → base status (READY)
    if not evaluator_outcome.issuance_eligible:
        return "BLOCKED"
    return "READY"
