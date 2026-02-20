"""Scoring provider abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from echelon_verify.models import GroundTruthRecord, OracleOutput


class ScoringProvider(ABC):
    """Interface for LLM-based verification scoring."""

    @abstractmethod
    async def score_precision(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict[str, Any]]:
        """Score precision.

        Returns:
            (score, claims_total, claims_supported, raw_output)
        """

    @abstractmethod
    async def score_recall(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict[str, Any]]:
        """Score recall.

        Returns:
            (score, changes_total, changes_surfaced, raw_output)
        """

    @abstractmethod
    async def score_reply_accuracy(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, dict[str, Any]]:
        """Score reply accuracy.

        Returns:
            (score, raw_output)
        """

    @abstractmethod
    async def generate_follow_up_question(
        self, ground_truth: GroundTruthRecord
    ) -> str:
        """Generate a factual follow-up question about the PR."""
