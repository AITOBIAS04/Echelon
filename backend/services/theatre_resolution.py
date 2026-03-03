"""Theatre Resolution Engine -- Composed Oracle resolution for Theatres.

Takes OracleOutput from Scorer + market state, determines winning outcome
based on composite_score and evidence, maps n-outcome markets to resolution
results. Uses existing ResolutionEngine from backend/market for settlement.

Cycle-012, Sprint 2 -- Task 2.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from backend.osint.canonical import canonical_json
from backend.osint.engine.corroboration import CorroborationEngine, CorroborationResult
from backend.osint.engine.counter_signal import CounterSignalEvaluator, CounterSignalResult
from backend.osint.engine.scorer import CriterionScore, OracleOutput, Scorer
from backend.osint.models.evidence import CollectionResult, EvidenceBundle
from backend.services.theatre_evidence import EvidenceSnapshot, TheatreEvidenceCollector


@dataclass
class TheatreResolutionResult:
    """Complete resolution result for a Theatre."""

    theatre_id: str
    oracle_output_id: str
    composite_score: float
    winning_outcome_index: int
    winning_outcome_label: str
    evidence_bundle_hash: str
    evidence_snapshots: list[EvidenceSnapshot]
    corroboration_result: CorroborationResult | None
    counter_signal_results: list[CounterSignalResult]
    criterion_scores: list[CriterionScore]
    source_manifest: dict[str, Any]


class TheatreResolutionEngine:
    """Triggers resolution for a Theatre using the Composed Oracle pipeline.

    Flow:
        1. Collect final evidence snapshot
        2. CorroborationEngine.evaluate() (provisional: 0.7 penalty)
        3. CounterSignalEvaluator.evaluate() (all UNAVAILABLE, INTELLIGENCE_GAP)
        4. Scorer.score() -> OracleOutput with composite_score
        5. _determine_winning_outcome() -> discrete winning_outcome_index
        6. Build TheatreResolutionResult
    """

    def __init__(
        self,
        evidence_collector: TheatreEvidenceCollector,
        scorer: Scorer,
        corroboration_engine: CorroborationEngine,
        counter_signal_evaluator: CounterSignalEvaluator,
        source_manifest: dict[str, Any],
        oracle_config: dict,
    ) -> None:
        self._evidence_collector = evidence_collector
        self._scorer = scorer
        self._corroboration = corroboration_engine
        self._counter_signal = counter_signal_evaluator
        self._source_manifest = source_manifest
        self._oracle_config = oracle_config

    def resolve(
        self,
        theatre_id: str,
        n_outcomes: int,
        outcome_labels: list[str],
        collection_results: list[CollectionResult] | None = None,
    ) -> TheatreResolutionResult:
        """Execute full Composed Oracle resolution for a Theatre.

        If collection_results is None, uses evidence from the collector's
        latest snapshot (mock-based collection).
        """
        # 1. Collect final evidence snapshot
        final_snapshot = self._evidence_collector.collect_heartbeat(theatre_id)
        all_snapshots = self._evidence_collector.get_evidence_history()

        # Build or use provided collection results
        if collection_results is None:
            collection_results = self._build_mock_collection_results(final_snapshot)

        # 2. Corroboration evaluation
        oracle_config = dict(self._oracle_config)
        oracle_config["theatre_id"] = theatre_id

        corroboration_result = self._corroboration.evaluate(
            collection_results, oracle_config
        )

        # 3. Counter-signal evaluation
        counter_signal_results = self._counter_signal.evaluate(
            collection_results, self._oracle_config
        )

        # 4. Scoring
        oracle_output = self._scorer.score(
            corroboration=corroboration_result,
            counter_signals=counter_signal_results,
            collection_results=collection_results,
            oracle_config=self._oracle_config,
            theatre_id=theatre_id,
        )

        # 5. Determine winning outcome
        winning_idx = self._determine_winning_outcome(
            oracle_output.composite_score, n_outcomes, outcome_labels
        )

        # Build oracle_output_id
        epoch_ms = int(oracle_output.scored_at.timestamp() * 1000)
        oracle_output_id = f"{theatre_id}_{epoch_ms}"

        # Compute evidence bundle hash
        evidence_bundle_hash = oracle_output.bundle_hash

        return TheatreResolutionResult(
            theatre_id=theatre_id,
            oracle_output_id=oracle_output_id,
            composite_score=oracle_output.composite_score,
            winning_outcome_index=winning_idx,
            winning_outcome_label=outcome_labels[winning_idx],
            evidence_bundle_hash=evidence_bundle_hash,
            evidence_snapshots=all_snapshots,
            corroboration_result=corroboration_result,
            counter_signal_results=counter_signal_results,
            criterion_scores=list(oracle_output.criterion_scores),
            source_manifest=self._source_manifest,
        )

    @staticmethod
    def _determine_winning_outcome(
        composite_score: float, n_outcomes: int, outcome_labels: list[str]
    ) -> int:
        """Map composite_score to a discrete winning outcome index.

        Companies House Theatre (3 outcomes):
            score >= 0.7 -> outcome 0 ("Filed on time")
            0.3 <= score < 0.7 -> outcome 1 ("Filed late")
            score < 0.3 -> outcome 2 ("Not filed")

        Generic n-outcome markets: divide [0, 1] into n equal buckets,
        with highest score mapping to outcome 0.
        """
        if n_outcomes == 3:
            # Companies House Theatre scoring thresholds
            if composite_score >= 0.7:
                return 0
            elif composite_score >= 0.3:
                return 1
            else:
                return 2

        # Generic n-outcome: divide [0, 1] into n buckets
        # Score 1.0 -> outcome 0, score 0.0 -> outcome n-1
        if composite_score >= 1.0:
            return 0
        bucket_size = 1.0 / n_outcomes
        idx = int((1.0 - composite_score) / bucket_size)
        return min(idx, n_outcomes - 1)

    @staticmethod
    def _build_mock_collection_results(
        snapshot: EvidenceSnapshot,
    ) -> list[CollectionResult]:
        """Build CollectionResult list from an EvidenceSnapshot.

        Used when no real collection was performed (mock mode).
        """
        results: list[CollectionResult] = []
        for bundle in snapshot.evidence_bundles:
            results.append(
                CollectionResult(
                    source_id=bundle.source_id,
                    bundle=bundle,
                    raw_payload=b"mock_payload",
                    fetch_duration_ms=0.0,
                    success=True,
                )
            )
        return results
