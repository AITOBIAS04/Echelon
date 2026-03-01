"""Tests for construct calibration scorer, fixtures, and template."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_fixtures() -> dict:
    path = _ROOT / "theatre" / "fixtures" / "construct_calibration" / "datasets" / "community_oracle_v1_fixtures.json"
    return json.loads(path.read_text())


def _load_template() -> dict:
    path = _ROOT / "theatre" / "fixtures" / "construct_calibration" / "templates" / "CONSTRUCT_CALIBRATION_V1.template.json"
    return json.loads(path.read_text())


def _run_async(coro):
    """Run async function synchronously (no pytest-asyncio dependency)."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Scorer Tests
# ---------------------------------------------------------------------------

class TestConstructCalibrationScorer:
    @pytest.fixture(autouse=True)
    def setup(self):
        from theatre.scoring.construct_calibration_scorer import ConstructCalibrationScorer
        self.scorer = ConstructCalibrationScorer()

    def test_precision_all_supported(self):
        gt = {"expected_output": {"precision_annotations": {"claims": [
            {"claim": "a", "supported": True},
            {"claim": "b", "supported": True},
        ]}}}
        result = _run_async(self.scorer.score("precision", gt, {}))
        assert result == 1.0

    def test_precision_partial(self):
        gt = {"expected_output": {"precision_annotations": {"claims": [
            {"claim": "a", "supported": True},
            {"claim": "b", "supported": False},
            {"claim": "c", "supported": True},
            {"claim": "d", "supported": False},
            {"claim": "e", "supported": True},
        ]}}}
        result = _run_async(self.scorer.score("precision", gt, {}))
        assert result == pytest.approx(0.6)

    def test_recall_partial(self):
        gt = {"expected_output": {"recall_annotations": {"important_changes": [
            {"change": "x", "surfaced": True},
            {"change": "y", "surfaced": False},
            {"change": "z", "surfaced": True},
            {"change": "w", "surfaced": False},
        ]}}}
        result = _run_async(self.scorer.score("recall", gt, {}))
        assert result == pytest.approx(0.5)

    def test_reply_accuracy_all_grounded(self):
        gt = {"expected_output": {"reply_accuracy_annotations": {"answers": [
            {"question": "q1", "grounded": True},
            {"question": "q2", "grounded": True},
        ]}}}
        result = _run_async(self.scorer.score("reply_accuracy", gt, {}))
        assert result == 1.0

    def test_unknown_criteria_returns_zero(self):
        result = _run_async(self.scorer.score("unknown_criteria", {}, {}))
        assert result == 0.0

    def test_empty_annotations_returns_zero(self):
        gt = {"expected_output": {"precision_annotations": {"claims": []}}}
        result = _run_async(self.scorer.score("precision", gt, {}))
        assert result == 0.0

    def test_missing_expected_output_returns_zero(self):
        result = _run_async(self.scorer.score("precision", {}, {}))
        assert result == 0.0


# ---------------------------------------------------------------------------
# Fixture Dataset Tests
# ---------------------------------------------------------------------------

class TestFixtureDataset:
    def test_record_count(self):
        fixtures = _load_fixtures()
        assert len(fixtures["records"]) >= 10

    def test_record_structure(self):
        fixtures = _load_fixtures()
        for record in fixtures["records"]:
            assert "record_id" in record
            assert "input_data" in record
            assert "expected_output" in record
            eo = record["expected_output"]
            assert "precision_annotations" in eo
            assert "recall_annotations" in eo
            assert "reply_accuracy_annotations" in eo
            assert "claims" in eo["precision_annotations"]
            assert "important_changes" in eo["recall_annotations"]
            assert "answers" in eo["reply_accuracy_annotations"]

    def test_annotations_are_binary(self):
        fixtures = _load_fixtures()
        for record in fixtures["records"]:
            eo = record["expected_output"]
            for claim in eo["precision_annotations"]["claims"]:
                assert isinstance(claim["supported"], bool)
            for change in eo["recall_annotations"]["important_changes"]:
                assert isinstance(change["surfaced"], bool)
            for answer in eo["reply_accuracy_annotations"]["answers"]:
                assert isinstance(answer["grounded"], bool)


# ---------------------------------------------------------------------------
# Template Tests
# ---------------------------------------------------------------------------

class TestTemplate:
    def test_template_fields(self):
        t = _load_template()
        assert t["template_family"] == "PRODUCT"
        assert t["execution_path"] == "replay"
        assert t["inquiry_class"] == "INSPECTION"
        assert t["template_id"] == "CONSTRUCT_CALIBRATION_V1"

    def test_criteria_weights_sum_to_one(self):
        t = _load_template()
        weights = t["criteria"]["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_criteria_ids_match_weights(self):
        t = _load_template()
        criteria_ids = set(t["criteria"]["criteria_ids"])
        weight_keys = set(t["criteria"]["weights"].keys())
        assert criteria_ids == weight_keys

    def test_dataset_hash_present(self):
        t = _load_template()
        hashes = t["dataset_hashes"]
        assert "community_oracle_v1_fixtures.json" in hashes
        h = hashes["community_oracle_v1_fixtures.json"]
        assert len(h) == 64  # SHA-256 hex
        assert h != "PLACEHOLDER"


# ---------------------------------------------------------------------------
# Score Distribution Tests
# ---------------------------------------------------------------------------

class TestScoreDistribution:
    """Verify that fixture annotations produce the expected score distributions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from theatre.scoring.construct_calibration_scorer import ConstructCalibrationScorer
        self.scorer = ConstructCalibrationScorer()
        self.fixtures = _load_fixtures()

    def _score_all(self, criteria_id: str) -> list:
        scores = []
        for r in self.fixtures["records"]:
            gt = {"input_data": r["input_data"], "expected_output": r["expected_output"]}
            score = _run_async(self.scorer.score(criteria_id, gt, {}))
            scores.append(score)
        return scores

    def test_precision_mean_approximately_0_8(self):
        scores = self._score_all("precision")
        mean = sum(scores) / len(scores)
        assert abs(mean - 0.80) < 0.05

    def test_recall_mean_approximately_0_55(self):
        scores = self._score_all("recall")
        mean = sum(scores) / len(scores)
        assert abs(mean - 0.55) < 0.05

    def test_reply_accuracy_mean_approximately_0_8(self):
        scores = self._score_all("reply_accuracy")
        mean = sum(scores) / len(scores)
        assert abs(mean - 0.80) < 0.05

    def test_composite_approximately_0_70(self):
        p_scores = self._score_all("precision")
        r_scores = self._score_all("recall")
        ra_scores = self._score_all("reply_accuracy")
        mp = sum(p_scores) / len(p_scores)
        mr = sum(r_scores) / len(r_scores)
        mra = sum(ra_scores) / len(ra_scores)
        composite = 0.40 * mp + 0.40 * mr + 0.20 * mra
        assert abs(composite - 0.70) < 0.05

    def test_all_scores_in_unit_interval(self):
        for criteria in ("precision", "recall", "reply_accuracy"):
            for score in self._score_all(criteria):
                assert 0.0 <= score <= 1.0
