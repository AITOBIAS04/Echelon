"""Theatre Scoring Provider — scores construct outputs against committed criteria.

Wraps scoring logic to produce per-criteria scores and weighted composite aggregates
using the TheatreCriteria structure from the committed template.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import OracleInvocationResponse


class ScoringFunction(Protocol):
    """Protocol for episode scoring — matches ScoringProvider contract."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float: ...


class SimpleScoringFunction:
    """Default scoring function for testing — exact match on expected_output keys."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        expected = ground_truth.get("expected_output", {})
        if not expected:
            return 0.5  # No expected output — neutral score
        matches = sum(
            1 for k, v in expected.items() if oracle_output.get(k) == v
        )
        return matches / len(expected) if expected else 0.0


class TheatreScoringProvider:
    """Scores construct outputs against committed criteria_ids."""

    def __init__(
        self,
        criteria: TheatreCriteria,
        scorer: ScoringFunction | None = None,
    ):
        self._criteria = criteria
        self._scorer = scorer or SimpleScoringFunction()

    async def score_episode(
        self,
        ground_truth: GroundTruthEpisode,
        oracle_response: OracleInvocationResponse,
    ) -> dict[str, float]:
        """Score a single episode against all criteria_ids.

        Returns dict of criteria_id -> score (0.0-1.0).
        If oracle response has no output_data (TIMEOUT/ERROR), returns 0.0 for all criteria.
        """
        if oracle_response.output_data is None:
            return {cid: 0.0 for cid in self._criteria.criteria_ids}

        gt_dict = {
            "input_data": ground_truth.input_data,
            "expected_output": ground_truth.expected_output or {},
            "labels": ground_truth.labels or {},
            "metadata": ground_truth.metadata,
        }

        scores: dict[str, float] = {}
        for criteria_id in self._criteria.criteria_ids:
            score = await self._scorer.score(
                criteria_id=criteria_id,
                ground_truth=gt_dict,
                oracle_output=oracle_response.output_data,
            )
            scores[criteria_id] = max(0.0, min(1.0, score))  # Clamp to [0, 1]

        return scores

    def compute_composite(self, scores: dict[str, float]) -> float:
        """Weighted aggregate: sum(weight_i * score_i).

        If weights dict is empty, uses equal weight fallback.
        Missing criteria get score 0.0.
        """
        if not self._criteria.weights:
            # Equal weight fallback
            if not scores:
                return 0.0
            return sum(scores.values()) / len(scores)

        return sum(
            self._criteria.weights.get(cid, 0.0) * scores.get(cid, 0.0)
            for cid in self._criteria.criteria_ids
        )
