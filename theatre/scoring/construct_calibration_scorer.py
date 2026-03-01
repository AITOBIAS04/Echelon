"""Construct Calibration Scorer — semantic accuracy metrics for construct outputs.

Three criteria scored against pre-annotated fixtures:
- precision: fraction of oracle claims supported by ground truth
- recall: fraction of important changes surfaced by the construct
- reply_accuracy: fraction of follow-up answers that are factually grounded

Uses float arithmetic (not Decimal) — semantic accuracy, not financial precision.
"""

from __future__ import annotations

from typing import Any


class ConstructCalibrationScorer:
    """Deterministic scorer for construct calibration theatres."""

    CRITERIA = {"precision", "recall", "reply_accuracy"}

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        """Score a single criterion for a single record.

        ground_truth contains pre-annotated pass/fail per claim.
        Returns pass_rate (0.0-1.0) for the criterion.
        """
        expected = ground_truth.get("expected_output", {})

        checks = {
            "precision": self._check_precision,
            "recall": self._check_recall,
            "reply_accuracy": self._check_reply_accuracy,
        }

        check_fn = checks.get(criteria_id)
        if check_fn is None:
            return 0.0

        return check_fn(expected)

    def _check_precision(self, expected: dict[str, Any]) -> float:
        """Precision = supported_claims / total_claims."""
        annotations = expected.get("precision_annotations", {})
        claims = annotations.get("claims", [])

        if not claims:
            return 0.0

        supported = sum(1 for c in claims if c.get("supported", False))
        return supported / len(claims)

    def _check_recall(self, expected: dict[str, Any]) -> float:
        """Recall = surfaced_changes / total_important_changes."""
        annotations = expected.get("recall_annotations", {})
        changes = annotations.get("important_changes", [])

        if not changes:
            return 0.0

        surfaced = sum(1 for c in changes if c.get("surfaced", False))
        return surfaced / len(changes)

    def _check_reply_accuracy(self, expected: dict[str, Any]) -> float:
        """Reply accuracy = grounded_answers / total_answers."""
        annotations = expected.get("reply_accuracy_annotations", {})
        answers = annotations.get("answers", [])

        if not answers:
            return 0.0

        grounded = sum(1 for a in answers if a.get("grounded", False))
        return grounded / len(answers)
