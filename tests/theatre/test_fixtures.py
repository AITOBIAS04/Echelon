"""Tests for Theatre fixture loading and template validation."""

import json
from pathlib import Path

import pytest

from theatre.engine.canonical_json import canonical_json
from theatre.engine.commitment import CommitmentProtocol
from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.template_validator import TemplateValidator
from theatre.fixtures import (
    CARTOGRAPH_GROUND_TRUTH,
    CARTOGRAPH_TEMPLATE,
    EASEL_GROUND_TRUTH,
    EASEL_TEMPLATE,
    OBSERVER_GROUND_TRUTH,
    OBSERVER_TEMPLATE,
    load_ground_truth,
    load_template,
)

SCHEMA_PATH = Path(__file__).parent.parent.parent / "docs" / "schemas" / "echelon_theatre_schema_v2.json"


@pytest.fixture
def validator() -> TemplateValidator:
    """Create template validator from project schema."""
    return TemplateValidator(schema_path=SCHEMA_PATH)


# ============================================
# TEMPLATE LOADING
# ============================================


class TestTemplateLoading:
    """Verify all fixture templates load without error."""

    def test_load_observer_template(self):
        template = load_template(OBSERVER_TEMPLATE)
        assert template["theatre_id"] == "product_observer_v1"
        assert template["execution_path"] == "replay"
        assert template["template_family"] == "PRODUCT"

    def test_load_easel_template(self):
        template = load_template(EASEL_TEMPLATE)
        assert template["theatre_id"] == "product_easel_v1"
        assert template["execution_path"] == "replay"
        assert "construct_chain" in template["product_theatre_config"]
        assert len(template["product_theatre_config"]["construct_chain"]) == 3

    def test_load_cartograph_template(self):
        template = load_template(CARTOGRAPH_TEMPLATE)
        assert template["theatre_id"] == "product_cartograph_v1"
        assert template["execution_path"] == "replay"


# ============================================
# TEMPLATE VALIDATION
# ============================================


class TestTemplateValidation:
    """Verify all fixtures pass TemplateValidator (schema + runtime rules)."""

    def test_observer_passes_validation(self, validator: TemplateValidator):
        template = load_template(OBSERVER_TEMPLATE)
        errors = validator.validate(template, is_certificate_run=False)
        assert errors == [], f"Observer validation errors: {errors}"

    def test_easel_passes_validation(self, validator: TemplateValidator):
        template = load_template(EASEL_TEMPLATE)
        errors = validator.validate(template, is_certificate_run=False)
        assert errors == [], f"Easel validation errors: {errors}"

    def test_cartograph_passes_validation(self, validator: TemplateValidator):
        template = load_template(CARTOGRAPH_TEMPLATE)
        errors = validator.validate(template, is_certificate_run=False)
        assert errors == [], f"Cartograph validation errors: {errors}"

    def test_observer_rejects_certificate_with_mock(self, validator: TemplateValidator):
        """Mock adapter should be rejected for certificate runs."""
        template = load_template(OBSERVER_TEMPLATE)
        errors = validator.validate(template, is_certificate_run=True)
        assert any("mock" in e.lower() for e in errors)

    def test_easel_criteria_weights_sum_to_one(self):
        template = load_template(EASEL_TEMPLATE)
        weights = template["criteria"]["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_cartograph_criteria_weights_sum_to_one(self):
        template = load_template(CARTOGRAPH_TEMPLATE)
        weights = template["criteria"]["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_observer_criteria_weights_sum_to_one(self):
        template = load_template(OBSERVER_TEMPLATE)
        weights = template["criteria"]["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-6


# ============================================
# GROUND TRUTH LOADING
# ============================================


class TestGroundTruthLoading:
    """Verify ground truth JSONL files load correctly."""

    def test_observer_ground_truth_loads(self):
        episodes = load_ground_truth(OBSERVER_GROUND_TRUTH)
        assert len(episodes) >= 5
        assert all(isinstance(ep, GroundTruthEpisode) for ep in episodes)

    def test_easel_ground_truth_loads(self):
        episodes = load_ground_truth(EASEL_GROUND_TRUTH)
        assert len(episodes) >= 5
        assert all(isinstance(ep, GroundTruthEpisode) for ep in episodes)

    def test_cartograph_ground_truth_loads(self):
        episodes = load_ground_truth(CARTOGRAPH_GROUND_TRUTH)
        assert len(episodes) >= 5
        assert all(isinstance(ep, GroundTruthEpisode) for ep in episodes)

    def test_observer_episode_ids_unique(self):
        episodes = load_ground_truth(OBSERVER_GROUND_TRUTH)
        ids = [ep.episode_id for ep in episodes]
        assert len(ids) == len(set(ids))

    def test_easel_episode_ids_unique(self):
        episodes = load_ground_truth(EASEL_GROUND_TRUTH)
        ids = [ep.episode_id for ep in episodes]
        assert len(ids) == len(set(ids))

    def test_cartograph_episode_ids_unique(self):
        episodes = load_ground_truth(CARTOGRAPH_GROUND_TRUTH)
        ids = [ep.episode_id for ep in episodes]
        assert len(ids) == len(set(ids))


# ============================================
# COMMITMENT HASH DETERMINISM
# ============================================


class TestCommitmentHashDeterminism:
    """Verify commitment hashes are deterministic across runs."""

    def _compute_hash(self, template_name: str) -> str:
        template = load_template(template_name)
        version_pins = template.get("version_pins", {})
        dataset_hashes = template.get("dataset_hashes", {})
        return CommitmentProtocol.compute_hash(template, version_pins, dataset_hashes)

    def test_observer_hash_deterministic(self):
        h1 = self._compute_hash(OBSERVER_TEMPLATE)
        h2 = self._compute_hash(OBSERVER_TEMPLATE)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_easel_hash_deterministic(self):
        h1 = self._compute_hash(EASEL_TEMPLATE)
        h2 = self._compute_hash(EASEL_TEMPLATE)
        assert h1 == h2

    def test_cartograph_hash_deterministic(self):
        h1 = self._compute_hash(CARTOGRAPH_TEMPLATE)
        h2 = self._compute_hash(CARTOGRAPH_TEMPLATE)
        assert h1 == h2

    def test_different_templates_produce_different_hashes(self):
        h_obs = self._compute_hash(OBSERVER_TEMPLATE)
        h_easel = self._compute_hash(EASEL_TEMPLATE)
        h_carto = self._compute_hash(CARTOGRAPH_TEMPLATE)
        assert h_obs != h_easel
        assert h_easel != h_carto
        assert h_obs != h_carto


# ============================================
# CRITERIA MODEL COMPATIBILITY
# ============================================


class TestCriteriaModelCompatibility:
    """Verify fixture criteria are compatible with TheatreCriteria model."""

    def test_observer_criteria_creates_model(self):
        template = load_template(OBSERVER_TEMPLATE)
        criteria = TheatreCriteria(**template["criteria"])
        assert len(criteria.criteria_ids) == 3
        assert "source_fidelity" in criteria.criteria_ids

    def test_easel_criteria_creates_model(self):
        template = load_template(EASEL_TEMPLATE)
        criteria = TheatreCriteria(**template["criteria"])
        assert len(criteria.criteria_ids) == 3
        assert "tdr_propagation_fidelity" in criteria.criteria_ids

    def test_cartograph_criteria_creates_model(self):
        template = load_template(CARTOGRAPH_TEMPLATE)
        criteria = TheatreCriteria(**template["criteria"])
        assert len(criteria.criteria_ids) == 3
        assert "hex_grid_accuracy" in criteria.criteria_ids
