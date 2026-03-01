"""Scorer — Stage 3 of the Composed Oracle pipeline (K-4).

Assembles OracleOutput from Stages 1 and 2 results:
- Computes 5 criterion scores
- Calculates weighted composite
- Generates deterministic bundle hash
- Fills coverage and counter-signal metrics
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from osint_pipeline.engine.canonical import canonical_json, sha256_hex
from osint_pipeline.models.evidence import (
    OracleCollectionSummary,
    ReceiptMode,
)
from osint_pipeline.models.oracle_output import (
    CorroborationResult,
    CounterSignalResult,
    CriterionScore,
    OracleOutput,
)


# Default weights per SDD section 2.2.5
DEFAULT_WEIGHTS: dict[str, float] = {
    "source_coverage": 0.20,
    "receipt_validity": 0.15,
    "corroboration_met": 0.30,
    "counter_signal_clear": 0.15,
    "confidence_weighted": 0.20,
}


class Scorer:
    """Compute per-criterion scores and assemble OracleOutput.

    Usage::

        scorer = Scorer()
        output = scorer.score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
            theatre_id="theatre_gb_realestate_001",
        )
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)

    def score(
        self,
        collection: OracleCollectionSummary,
        corroboration_results: list[CorroborationResult],
        counter_signal_results: list[CounterSignalResult],
        theatre_id: str | None = None,
    ) -> OracleOutput:
        """Score the pipeline results and assemble OracleOutput."""
        bundles = collection.bundles
        bundle_ids = [b.bundle_id for b in bundles]

        # --- Criterion 1: source_coverage ---
        coverage = collection.coverage_ratio
        criterion_coverage = CriterionScore(
            criterion_id="source_coverage",
            score=coverage,
            passed=coverage > 0.0,
            detail=(
                f"{collection.total_sources_succeeded}/{collection.total_sources_attempted} "
                f"sources succeeded"
            ),
            evidence_bundle_ids=bundle_ids,
        )

        # --- Criterion 2: receipt_validity ---
        if bundles:
            valid_receipts = sum(
                1 for b in bundles if b.receipt_mode != ReceiptMode.NONE
            )
            receipt_score = valid_receipts / len(bundles)
        else:
            receipt_score = 0.0
        criterion_receipt = CriterionScore(
            criterion_id="receipt_validity",
            score=receipt_score,
            passed=receipt_score >= 0.5,
            detail=f"{int(receipt_score * 100)}% of bundles have valid receipts",
            evidence_bundle_ids=bundle_ids,
        )

        # --- Criterion 3: corroboration_met ---
        if corroboration_results:
            passed_count = sum(1 for c in corroboration_results if c.passed)
            corr_score = passed_count / len(corroboration_results)
        else:
            corr_score = 0.0
        criterion_corr = CriterionScore(
            criterion_id="corroboration_met",
            score=corr_score,
            passed=corr_score >= 1.0 if corroboration_results else False,
            detail=(
                f"{passed_count if corroboration_results else 0}/"
                f"{len(corroboration_results)} claims corroborated"
            ),
            evidence_bundle_ids=bundle_ids,
        )

        # --- Criterion 4: counter_signal_clear ---
        checked_results = [cs for cs in counter_signal_results if cs.checked]
        if checked_results:
            passed_cs = sum(1 for cs in checked_results if cs.passed)
            cs_score = passed_cs / len(checked_results)
        else:
            cs_score = 0.0
        criterion_cs = CriterionScore(
            criterion_id="counter_signal_clear",
            score=cs_score,
            passed=cs_score >= 1.0 if checked_results else False,
            detail=(
                f"{passed_cs if checked_results else 0}/"
                f"{len(checked_results)} checked classes passed"
            ),
            evidence_bundle_ids=bundle_ids,
        )

        # --- Criterion 5: confidence_weighted ---
        if bundles:
            mean_confidence = sum(b.confidence_score for b in bundles) / len(bundles)
        else:
            mean_confidence = 0.0
        criterion_confidence = CriterionScore(
            criterion_id="confidence_weighted",
            score=mean_confidence,
            passed=mean_confidence >= 0.5,
            detail=f"Mean confidence: {mean_confidence:.3f}",
            evidence_bundle_ids=bundle_ids,
        )

        # --- Weighted composite ---
        criteria = [
            criterion_coverage,
            criterion_receipt,
            criterion_corr,
            criterion_cs,
            criterion_confidence,
        ]
        composite = sum(
            cs.score * self.weights.get(cs.criterion_id, 0.0) for cs in criteria
        )
        # Clamp to [0.0, 1.0]
        composite = max(0.0, min(1.0, composite))

        # --- Bundle hash ---
        if bundles:
            bundle_dicts = sorted(
                [b.model_dump(mode="json") for b in bundles],
                key=lambda d: d["bundle_id"],
            )
            bundle_hash = sha256_hex(canonical_json(bundle_dicts))
        else:
            bundle_hash = sha256_hex("")

        # --- Coverage percentage ---
        if collection.total_sources_attempted > 0:
            coverage_pct = (
                collection.total_sources_succeeded
                / collection.total_sources_attempted
                * 100.0
            )
        else:
            coverage_pct = 0.0

        # --- Counter-signal summary ---
        cs_checked = sum(1 for cs in counter_signal_results if cs.checked)
        cs_found = sum(
            1 for cs in counter_signal_results if cs.checked and cs.signal_found
        )

        return OracleOutput(
            oracle_id=str(uuid.uuid4()),
            theatre_id=theatre_id,
            evaluated_at=datetime.now(timezone.utc),
            collection=collection,
            corroboration_results=corroboration_results,
            counter_signal_results=counter_signal_results,
            criterion_scores=criteria,
            composite_score=composite,
            bundle_hash=bundle_hash,
            gap_report=list(collection.gaps),
            coverage_percentage=coverage_pct,
            counter_signals_checked=cs_checked,
            counter_signals_found=cs_found,
        )
