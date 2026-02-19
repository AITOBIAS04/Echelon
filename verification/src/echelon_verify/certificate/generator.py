"""Certificate generator — aggregation math for CalibrationCertificate."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from echelon_verify.models import CalibrationCertificate

if TYPE_CHECKING:
    from echelon_verify.models import ReplayScore


class CertificateGenerator:
    """Aggregates ReplayScores into a CalibrationCertificate."""

    def __init__(
        self,
        construct_id: str,
        ground_truth_source: str,
        commit_range: str,
        scoring_model: str,
        methodology_version: str = "v1",
        composite_weights: dict[str, float] | None = None,
    ) -> None:
        self._construct_id = construct_id
        self._ground_truth_source = ground_truth_source
        self._commit_range = commit_range
        self._scoring_model = scoring_model
        self._methodology_version = methodology_version
        self._weights = composite_weights or {
            "precision": 1.0,
            "recall": 1.0,
            "reply_accuracy": 1.0,
        }

    def generate(self, scores: list[ReplayScore]) -> CalibrationCertificate:
        """Aggregate scores into a calibration certificate.

        Raises:
            ValueError: If scores list is empty.
        """
        if not scores:
            raise ValueError("Cannot generate certificate from empty scores")

        n = len(scores)
        mean_precision = sum(s.precision for s in scores) / n
        mean_recall = sum(s.recall for s in scores) / n
        mean_reply_accuracy = sum(s.reply_accuracy for s in scores) / n

        # Weighted composite with normalized weights
        total_weight = sum(self._weights.values())
        if total_weight == 0:
            raise ValueError("Composite weights must not all be zero")

        composite = (
            self._weights.get("precision", 0.0) * mean_precision
            + self._weights.get("recall", 0.0) * mean_recall
            + self._weights.get("reply_accuracy", 0.0) * mean_reply_accuracy
        ) / total_weight

        # Brier score mapped to RLMF [0, 0.5] range
        brier = (1 - composite) * 0.5

        return CalibrationCertificate(
            construct_id=self._construct_id,
            replay_count=n,
            precision=round(mean_precision, 6),
            recall=round(mean_recall, 6),
            reply_accuracy=round(mean_reply_accuracy, 6),
            composite_score=round(composite, 6),
            brier=round(brier, 6),
            sample_size=n,
            timestamp=datetime.now(timezone.utc),
            ground_truth_source=self._ground_truth_source,
            commit_range=self._commit_range,
            methodology_version=self._methodology_version,
            scoring_model=self._scoring_model,
            individual_scores=scores,
        )
