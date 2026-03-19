"""Evaluator Orchestrator — multi-scorer execution over residual dimensions.

Cycle 037b: Multi-Evaluator Orchestration + Residual Scoring.

Calls N independent scorers over the residual dimension set, collects
EvaluatorScoreRecord outputs, and produces a per-dimension + run-level summary.
"""

import asyncio
import logging
from typing import Protocol, runtime_checkable

from backend.schemas.evaluator_orchestration import (
    EvaluatorScoreRecord,
)
from backend.services.residual_dimension_filter import ResidualDimension

logger = logging.getLogger(__name__)


# ── Scorer Adapter Protocol ──

@runtime_checkable
class ResidualScorer(Protocol):
    """Protocol for pluggable residual dimension scorers.

    Each scorer independently evaluates residual dimensions and returns
    a list of EvaluatorScoreRecord entries (one per dimension).
    """

    @property
    def evaluator_id(self) -> str: ...

    async def score_dimensions(
        self,
        *,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]: ...


# ── Orchestrator ──

class EvaluatorOrchestrator:
    """Executes multiple scorers over residual dimensions concurrently.

    Collects all EvaluatorScoreRecord outputs, normalizes them, and
    groups by dimension for downstream convergence analysis.
    """

    def __init__(self, scorers: list[ResidualScorer]) -> None:
        if not scorers:
            raise ValueError("At least one scorer is required")
        self._scorers = scorers

    @property
    def evaluator_ids(self) -> list[str]:
        return [s.evaluator_id for s in self._scorers]

    async def execute(
        self,
        *,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        """Execute all scorers concurrently and return merged record list.

        Each scorer receives the same dimension set and episode payload.
        Results are merged into a single flat list of EvaluatorScoreRecord.

        Args:
            dimensions: Residual dimensions to score.
            episode_payload: Construct episode data for scorer context.

        Returns:
            Flat list of EvaluatorScoreRecord from all scorers.
        """
        if not dimensions:
            logger.info("No residual dimensions to score, returning empty")
            return []

        dimension_names = [d.dimension for d in dimensions]
        logger.info(
            "Orchestrating %d scorers over %d dimensions: %s",
            len(self._scorers), len(dimensions), dimension_names,
        )

        # Run all scorers concurrently
        tasks = [
            self._invoke_scorer(scorer, dimensions, episode_payload)
            for scorer in self._scorers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results, log failures
        all_records: list[EvaluatorScoreRecord] = []
        for scorer, result in zip(self._scorers, results):
            if isinstance(result, Exception):
                logger.error(
                    "Scorer %s failed: %s", scorer.evaluator_id, result,
                )
                # Emit ABSTAIN records for failed scorers
                for dim in dimensions:
                    all_records.append(EvaluatorScoreRecord(
                        evaluator_id=scorer.evaluator_id,
                        dimension=dim.dimension,
                        verdict="ABSTAIN",
                        rationale=f"Scorer error: {type(result).__name__}",
                    ))
            else:
                all_records.extend(result)

        logger.info(
            "Orchestration complete: %d records from %d scorers",
            len(all_records), len(self._scorers),
        )
        return all_records

    @staticmethod
    async def _invoke_scorer(
        scorer: ResidualScorer,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        """Invoke a single scorer and normalize output."""
        records = await scorer.score_dimensions(
            dimensions=dimensions,
            episode_payload=episode_payload,
        )
        # Validate that evaluator_id matches
        normalized: list[EvaluatorScoreRecord] = []
        for record in records:
            if record.evaluator_id != scorer.evaluator_id:
                logger.warning(
                    "Scorer %s returned record with evaluator_id=%s, correcting",
                    scorer.evaluator_id, record.evaluator_id,
                )
                record = EvaluatorScoreRecord(
                    evaluator_id=scorer.evaluator_id,
                    dimension=record.dimension,
                    verdict=record.verdict,
                    score=record.score,
                    rationale=record.rationale,
                    raw_output=record.raw_output,
                )
            normalized.append(record)
        return normalized

    def group_by_dimension(
        self, records: list[EvaluatorScoreRecord],
    ) -> dict[str, list[EvaluatorScoreRecord]]:
        """Group score records by dimension name.

        Returns:
            Dict mapping dimension → list of EvaluatorScoreRecord from each scorer.
        """
        grouped: dict[str, list[EvaluatorScoreRecord]] = {}
        for record in records:
            grouped.setdefault(record.dimension, []).append(record)
        return grouped
