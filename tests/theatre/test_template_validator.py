"""Tests for TemplateValidator — JSON Schema + runtime validation rules."""

import copy
import json
from pathlib import Path

import pytest

from theatre.engine.template_validator import TemplateValidator


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "schemas" / "echelon_theatre_schema_v2.json"


def _make_valid_product_template() -> dict:
    """Build a minimal valid Product Theatre template."""
    return {
        "schema_version": "2.0.1",
        "theatre_id": "product_observer_v1",
        "template_family": "PRODUCT",
        "execution_path": "replay",
        "display_name": "Observer Verification",
        "criteria": {
            "criteria_ids": ["source_fidelity", "signal_classification"],
            "criteria_human": "Evaluate source accuracy and signal classification quality",
            "weights": {"source_fidelity": 0.6, "signal_classification": 0.4},
        },
        "fork_definitions": [
            {
                "fork_id": "f_01",
                "options": [
                    {"option_id": "pass", "label": "Pass"},
                    {"option_id": "fail", "label": "Fail"},
                ],
            }
        ],
        "scoring": {
            "holdout_split": 0.2,
        },
        "resolution_programme": [
            {
                "step_id": "invoke_observer",
                "type": "construct_invocation",
                "construct_id": "observer",
                "timeout_seconds": 30,
            },
            {
                "step_id": "aggregate",
                "type": "aggregation",
            },
        ],
        "version_pins": {
            "constructs": {"observer": "abc123def456789012345678901234567890abcd"},
            "scorer_version": "anthropic-claude-3.5-sonnet",
        },
        "dataset_hashes": {
            "provenance": "a" * 64,
        },
        "product_theatre_config": {
            "ground_truth_source": "PROVENANCE_JSONL",
            "construct_under_test": "observer",
            "adapter_type": "http",
            "adapter_endpoint": "https://observer.example.com/invoke",
            "replay_dataset_id": "provenance",
        },
    }


def _make_valid_market_template() -> dict:
    """Build a minimal valid Market Theatre template."""
    return {
        "schema_version": "2.0.1",
        "theatre_id": "geopolitical_military_v1",
        "template_family": "GEOPOLITICAL",
        "execution_path": "market",
        "display_name": "Military Conflict Theatre",
        "criteria": {
            "criteria_ids": ["prediction_accuracy"],
            "criteria_human": "Prediction accuracy against ground truth",
        },
        "fork_definitions": [
            {
                "fork_id": "f_01",
                "options": [
                    {"option_id": "escalation", "label": "Escalation"},
                    {"option_id": "de_escalation", "label": "De-escalation"},
                ],
            }
        ],
        "scoring": {},
        "resolution_programme": [
            {
                "step_id": "resolve",
                "type": "deterministic_computation",
            }
        ],
        "version_pins": {
            "scorer_version": "v1.0",
        },
        "market_theatre_config": {
            "lmsr_config": {
                "liquidity_b": 100,
                "duration_seconds": 3600,
            },
            "geopolitical_category": "MILITARY",
        },
    }


@pytest.fixture
def validator():
    return TemplateValidator(schema_path=SCHEMA_PATH)


class TestSchemaValidation:
    def test_valid_product_template(self, validator):
        errors = validator.validate(_make_valid_product_template(), is_certificate_run=False)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_valid_market_template(self, validator):
        errors = validator.validate(_make_valid_market_template(), is_certificate_run=False)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_required_field(self, validator):
        template = _make_valid_product_template()
        del template["theatre_id"]
        errors = validator.validate(template, is_certificate_run=False)
        assert any("theatre_id" in e for e in errors)

    def test_invalid_execution_path(self, validator):
        template = _make_valid_product_template()
        template["execution_path"] = "invalid"
        errors = validator.validate(template, is_certificate_run=False)
        assert len(errors) > 0

    def test_invalid_template_family(self, validator):
        template = _make_valid_product_template()
        template["template_family"] = "UNKNOWN"
        errors = validator.validate(template, is_certificate_run=False)
        assert len(errors) > 0


class TestRuntimeRule1WeightKeysSubset:
    def test_extra_weight_key(self, validator):
        template = _make_valid_product_template()
        template["criteria"]["weights"]["nonexistent"] = 0.0
        template["criteria"]["weights"]["source_fidelity"] = 0.6
        template["criteria"]["weights"]["signal_classification"] = 0.4
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 1" in e for e in errors)


class TestRuntimeRule2WeightSum:
    def test_weights_not_summing_to_one(self, validator):
        template = _make_valid_product_template()
        template["criteria"]["weights"] = {
            "source_fidelity": 0.3,
            "signal_classification": 0.3,
        }
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 2" in e for e in errors)


class TestRuntimeRule3ConstructPinLinkage:
    def test_resolution_construct_without_pin(self, validator):
        template = _make_valid_product_template()
        template["resolution_programme"].insert(0, {
            "step_id": "invoke_missing",
            "type": "construct_invocation",
            "construct_id": "missing_construct",
        })
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 3" in e for e in errors)


class TestRuntimeRule4ConstructChainPins:
    def test_chain_member_without_pin(self, validator):
        template = _make_valid_product_template()
        template["product_theatre_config"]["construct_chain"] = ["observer", "unpinned"]
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 4" in e for e in errors)


class TestRuntimeRule5HitlStepLinkage:
    def test_hitl_step_without_resolution_match(self, validator):
        template = _make_valid_product_template()
        template["hitl_steps"] = [
            {
                "step_id": "orphan_hitl",
                "rubric": "Taste evaluation",
                "scoring_scale": {"min": 0, "max": 10},
            }
        ]
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 5" in e for e in errors)


class TestRuntimeRule6MockAdapterRejection:
    def test_mock_adapter_rejected_for_certificate_run(self, validator):
        template = _make_valid_product_template()
        template["product_theatre_config"]["adapter_type"] = "mock"
        # Remove adapter_endpoint since mock doesn't need it
        template["product_theatre_config"].pop("adapter_endpoint", None)
        errors = validator.validate(template, is_certificate_run=True)
        assert any("rule 6" in e for e in errors)

    def test_mock_adapter_allowed_for_non_certificate_run(self, validator):
        template = _make_valid_product_template()
        template["product_theatre_config"]["adapter_type"] = "mock"
        template["product_theatre_config"].pop("adapter_endpoint", None)
        errors = validator.validate(template, is_certificate_run=False)
        assert not any("rule 6" in e for e in errors)


class TestRuntimeRule7DatasetHashPresence:
    def test_missing_replay_dataset_id_in_hashes(self, validator):
        template = _make_valid_product_template()
        template["product_theatre_config"]["replay_dataset_id"] = "missing_dataset"
        errors = validator.validate(template, is_certificate_run=False)
        assert any("rule 7" in e for e in errors)
