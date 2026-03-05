"""Scorer — Stage 3 of the evidence pipeline.

Produces composite_score that becomes p_reality in the Paradox Engine.
Per-criterion evaluation, confidence-weighted average, corroboration
bonus, counter-signal penalty, evidence completeness factor.

Bundle hash uses the manifest pattern: {bundle_id: raw_payload_hash}
sorted by bundle_id, SHA256(canonical_json(manifest)).

Composite score formula:
    composite_score = weighted_mean(confidence for primary bundles)
                    x corroboration_factor (1.0 if met, 0.7 if not)
                    x counter_signal_factor (1.0 if pass, 0.5 if fail)
                    x evidence_completeness
    Result clamped to [0.0, 1.0].
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.osint.canonical import canonical_json
from backend.osint.engine.corroboration import CorroborationResult
from backend.osint.engine.counter_signal import CounterSignalEvaluator, CounterSignalResult
from backend.osint.models.evidence import CollectionResult, EvidenceBundle
from backend.osint.models.registry import RegistryLoader


# ── Priority bucket weights ────────────────────────────────────────

_PRIORITY_WEIGHTS: dict[str, float] = {
    "settlement_grade": 3.0,
    "scoring_grade": 2.0,
    "triage_only": 1.0,
    "avoid": 0.0,
}


@dataclass
class CriterionScore:
    """Score for a single evaluation criterion."""

    criterion: str
    passed: bool
    score: float
    detail: str


@dataclass
class OracleOutput:
    """Full output of the scoring stage.

    This is the primary interchange between the OSINT pipeline and
    the Paradox Engine's LiveOSINTRealityProvider.
    """

    theatre_id: str
    composite_score: float                              # 0.0-1.0
    criterion_scores: list[CriterionScore]
    evidence_bundles: list[EvidenceBundle]
    corroboration_result: CorroborationResult
    counter_signal_results: list[CounterSignalResult]
    evidence_completeness: float                        # 0.0-1.0
    bundle_hash: str                                    # SHA-256
    scored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Scorer:
    """Stage 3: produce composite_score from corroboration + counter-signals.

    Factors:
        CORROBORATION_MET_FACTOR   = 1.0 (corroboration minimum met)
        CORROBORATION_UNMET_FACTOR = 0.7 (corroboration minimum not met)
        COUNTER_SIGNAL_PASS_FACTOR = 1.0 (no unexplained counter-signals)
        COUNTER_SIGNAL_FAIL_FACTOR = 0.5 (unexplained counter-signals present)
    """

    CORROBORATION_MET_FACTOR: float = 1.0
    CORROBORATION_UNMET_FACTOR: float = 0.7
    COUNTER_SIGNAL_PASS_FACTOR: float = 1.0
    COUNTER_SIGNAL_FAIL_FACTOR: float = 0.5

    def __init__(self, registry_loader: RegistryLoader) -> None:
        self._registry = registry_loader

    def score(
        self,
        corroboration: CorroborationResult,
        counter_signals: list[CounterSignalResult],
        collection_results: list[CollectionResult],
        oracle_config: dict,
        theatre_id: str,
    ) -> OracleOutput:
        """Produce OracleOutput from pipeline stage outputs.

        Args:
            corroboration: Result from CorroborationEngine.evaluate().
            counter_signals: Results from CounterSignalEvaluator.evaluate().
            collection_results: Raw CollectionResult list from Stage 1.
            oracle_config: Theatre oracle config dict.
            theatre_id: Theatre identifier.

        Returns:
            OracleOutput with composite_score and full audit trail.
        """
        # Evidence completeness
        required_sources = oracle_config.get(
            "sources",
            list(set(r.source_id for r in collection_results)),
        )
        required_count = len(required_sources) if required_sources else 1
        successful_count = sum(1 for r in collection_results if r.success)
        evidence_completeness = successful_count / required_count if required_count > 0 else 0.0
        evidence_completeness = min(evidence_completeness, 1.0)

        # Counter-signal criterion
        counter_signal_pass, counter_signal_detail = CounterSignalEvaluator.check_criterion(
            counter_signals
        )

        # All primary bundles from corroboration result
        primary_bundles = corroboration.primary_bundles

        # Compute composite score
        composite = self.compute_composite(
            bundles=primary_bundles,
            corroboration_met=corroboration.corroboration_met,
            counter_signal_pass=counter_signal_pass,
            evidence_completeness=evidence_completeness,
        )

        # Criterion scores for audit
        criterion_scores = [
            CriterionScore(
                criterion="corroboration_minimum_met",
                passed=corroboration.corroboration_met,
                score=(
                    self.CORROBORATION_MET_FACTOR
                    if corroboration.corroboration_met
                    else self.CORROBORATION_UNMET_FACTOR
                ),
                detail=(
                    f"distinct_source_groups={corroboration.distinct_source_groups}, "
                    f"minimum={corroboration.corroboration_minimum}, "
                    f"met={corroboration.corroboration_met}"
                ),
            ),
            CriterionScore(
                criterion="counter_signal_checked",
                passed=counter_signal_pass,
                score=(
                    self.COUNTER_SIGNAL_PASS_FACTOR
                    if counter_signal_pass
                    else self.COUNTER_SIGNAL_FAIL_FACTOR
                ),
                detail=counter_signal_detail,
            ),
        ]

        # Gather all evidence bundles for the output
        all_bundles = corroboration.primary_bundles + corroboration.corroborating_bundles

        # Feed convergence detector buffer (game loop drains every 120s)
        try:
            from backend.worker.tasks.convergence_tick import push_evidence_bundles
            push_evidence_bundles(all_bundles)
        except ImportError:
            pass

        # Bundle hash
        bundle_hash = self.compute_bundle_hash(all_bundles)

        return OracleOutput(
            theatre_id=theatre_id,
            composite_score=composite,
            criterion_scores=criterion_scores,
            evidence_bundles=all_bundles,
            corroboration_result=corroboration,
            counter_signal_results=counter_signals,
            evidence_completeness=evidence_completeness,
            bundle_hash=bundle_hash,
        )

    def compute_composite(
        self,
        bundles: list[EvidenceBundle],
        corroboration_met: bool,
        counter_signal_pass: bool,
        evidence_completeness: float,
    ) -> float:
        """Compute composite_score from factors.

        Formula:
            composite_score = weighted_mean(confidence)
                            x corroboration_factor
                            x counter_signal_factor
                            x evidence_completeness
        Result clamped to [0.0, 1.0].

        Empty bundles or zero completeness -> 0.0.
        """
        if not bundles or evidence_completeness <= 0.0:
            return 0.0

        # Confidence-weighted mean using priority_bucket weights
        weighted_confidence = self._weighted_mean_confidence(bundles)

        # Apply factors
        corroboration_factor = (
            self.CORROBORATION_MET_FACTOR
            if corroboration_met
            else self.CORROBORATION_UNMET_FACTOR
        )
        counter_signal_factor = (
            self.COUNTER_SIGNAL_PASS_FACTOR
            if counter_signal_pass
            else self.COUNTER_SIGNAL_FAIL_FACTOR
        )

        raw = (
            weighted_confidence
            * corroboration_factor
            * counter_signal_factor
            * evidence_completeness
        )

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, raw))

    def _weighted_mean_confidence(
        self, bundles: list[EvidenceBundle]
    ) -> float:
        """Compute weighted mean of bundle confidences by priority_bucket.

        Weights from registry priority_bucket:
            settlement_grade: 3.0
            scoring_grade:    2.0
            triage_only:      1.0
            avoid:            0.0 (excluded from mean)
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for bundle in bundles:
            source = self._registry.get_source(bundle.source_id)
            bucket = source.priority_bucket if source else "scoring_grade"
            weight = _PRIORITY_WEIGHTS.get(bucket, 1.0)
            if weight <= 0.0:
                continue  # Skip "avoid" bucket
            confidence = bundle.normalised_event.confidence
            weighted_sum += confidence * weight
            total_weight += weight

        if total_weight <= 0.0:
            return 0.0
        return weighted_sum / total_weight

    @staticmethod
    def compute_bundle_hash(bundles: list[EvidenceBundle]) -> str:
        """Manifest-pattern bundle hash.

        Builds manifest: {bundle_id: raw_payload_hash} sorted by bundle_id.
        Returns SHA-256(canonical_json(manifest)).

        Deterministic regardless of insertion order.
        """
        if not bundles:
            return hashlib.sha256(b"{}").hexdigest()

        manifest: dict[str, str] = {}
        for bundle in bundles:
            manifest[bundle.bundle_id] = bundle.raw_payload_hash

        canonical = canonical_json(manifest)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
