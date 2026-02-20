"""Tests for TheatreCriteria model — weight validation, subset enforcement."""

import pytest
from pydantic import ValidationError

from theatre.engine.models import TheatreCriteria


class TestTheatreCriteria:
    def test_valid_criteria_with_weights(self):
        criteria = TheatreCriteria(
            criteria_ids=["source_fidelity", "signal_classification"],
            criteria_human="Evaluate source accuracy and signal classification",
            weights={"source_fidelity": 0.6, "signal_classification": 0.4},
        )
        assert len(criteria.criteria_ids) == 2
        assert sum(criteria.weights.values()) == pytest.approx(1.0)

    def test_valid_criteria_empty_weights(self):
        criteria = TheatreCriteria(
            criteria_ids=["hex_grid_accuracy"],
            criteria_human="Evaluate hex grid accuracy",
            weights={},
        )
        assert criteria.weights == {}

    def test_valid_criteria_default_weights(self):
        criteria = TheatreCriteria(
            criteria_ids=["hex_grid_accuracy"],
            criteria_human="Evaluate hex grid accuracy",
        )
        assert criteria.weights == {}

    def test_extra_weight_key_rejected(self):
        with pytest.raises(ValidationError, match="not in criteria_ids"):
            TheatreCriteria(
                criteria_ids=["source_fidelity"],
                criteria_human="Test",
                weights={"source_fidelity": 0.5, "nonexistent": 0.5},
            )

    def test_weight_sum_not_one_rejected(self):
        with pytest.raises(ValidationError, match="sum to 1.0"):
            TheatreCriteria(
                criteria_ids=["a", "b"],
                criteria_human="Test",
                weights={"a": 0.3, "b": 0.3},
            )

    def test_weight_sum_tolerance(self):
        """Weight sum within 1e-6 tolerance should pass."""
        criteria = TheatreCriteria(
            criteria_ids=["a", "b", "c"],
            criteria_human="Test",
            weights={"a": 0.33333333, "b": 0.33333333, "c": 0.33333334},
        )
        assert sum(criteria.weights.values()) == pytest.approx(1.0, abs=1e-6)

    def test_single_criterion(self):
        criteria = TheatreCriteria(
            criteria_ids=["only_one"],
            criteria_human="Single criterion",
            weights={"only_one": 1.0},
        )
        assert criteria.weights["only_one"] == 1.0

    def test_empty_criteria_ids_rejected(self):
        with pytest.raises(ValidationError):
            TheatreCriteria(
                criteria_ids=[],
                criteria_human="Test",
            )

    def test_three_criteria_three_weights(self):
        criteria = TheatreCriteria(
            criteria_ids=["vocabulary_adherence", "tdr_propagation_fidelity", "downstream_compliance"],
            criteria_human="Evaluate Easel creative direction fidelity",
            weights={
                "vocabulary_adherence": 0.4,
                "tdr_propagation_fidelity": 0.35,
                "downstream_compliance": 0.25,
            },
        )
        assert len(criteria.criteria_ids) == 3
        assert sum(criteria.weights.values()) == pytest.approx(1.0)

    def test_partial_weights_rejected(self):
        """Weights for only some criteria — still must sum to 1.0."""
        with pytest.raises(ValidationError, match="sum to 1.0"):
            TheatreCriteria(
                criteria_ids=["a", "b", "c"],
                criteria_human="Test",
                weights={"a": 0.5},  # Only one key, sums to 0.5
            )
