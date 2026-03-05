"""Tests for stop_condition / stop_config validation on TheatreCreate.

Cycle-014c codex remediation — F3.
"""
from __future__ import annotations

import pytest

from backend.schemas.theatre import TheatreCreate


def _make_template_json(**overrides: object) -> dict:
    base = {
        "theatre_id": "test-001",
        "execution_path": "market",
        "template_family": "counterfactual",
    }
    base.update(overrides)
    return base


class TestValidStopConditions:
    def test_valid_outcome_resolution(self):
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=_make_template_json(),
            inquiry_class="INVESTIGATIVE",
            stop_condition="OUTCOME_RESOLUTION",
        )
        assert tc.stop_condition == "OUTCOME_RESOLUTION"

    def test_valid_evidence_threshold(self):
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=_make_template_json(),
            inquiry_class="INVESTIGATIVE",
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3, "min_corroboration_score": 0.7},
        )
        assert tc.stop_condition == "EVIDENCE_THRESHOLD"

    def test_valid_sponsor_defined(self):
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=_make_template_json(),
            inquiry_class="INVESTIGATIVE",
            stop_condition="SPONSOR_DEFINED",
            stop_config={"milestone_timestamp": "2026-06-01T00:00:00Z"},
        )
        assert tc.stop_condition == "SPONSOR_DEFINED"


class TestStopConditionNormalisation:
    def test_invalid_stop_condition_rejected(self):
        with pytest.raises(Exception, match="stop_condition must be one of"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_condition="BANANA",
            )

    def test_case_insensitive(self):
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=_make_template_json(),
            inquiry_class="INVESTIGATIVE",
            stop_condition="evidence_threshold",
        )
        assert tc.stop_condition == "EVIDENCE_THRESHOLD"


class TestStopConfigValidation:
    def test_config_without_condition_rejected(self):
        with pytest.raises(Exception, match="stop_config requires stop_condition"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_config={"some_key": "value"},
            )

    def test_sponsor_missing_milestone_rejected(self):
        with pytest.raises(Exception, match="milestone_timestamp"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_condition="SPONSOR_DEFINED",
                stop_config={},
            )

    def test_sponsor_invalid_timestamp_rejected(self):
        with pytest.raises(Exception, match="ISO 8601"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_condition="SPONSOR_DEFINED",
                stop_config={"milestone_timestamp": "not-a-date"},
            )

    def test_evidence_invalid_min_claims_rejected(self):
        with pytest.raises(Exception, match="min_supported_claims must be int >= 1"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_condition="EVIDENCE_THRESHOLD",
                stop_config={"min_supported_claims": 0},
            )

    def test_evidence_invalid_corroboration_rejected(self):
        with pytest.raises(Exception, match="min_corroboration_score must be float 0-1"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class="INVESTIGATIVE",
                stop_condition="EVIDENCE_THRESHOLD",
                stop_config={"min_corroboration_score": 1.5},
            )


class TestStopConditionInquiryClassScoping:
    """Stop fields are only allowed for INVESTIGATIVE inquiry class."""

    @pytest.mark.parametrize("ic", ["COUNTERFACTUAL", "INSPECTION", "SURVEY", "SCRUTINY"])
    def test_stop_condition_rejected_for_non_investigative(self, ic):
        with pytest.raises(Exception, match="only allowed for INVESTIGATIVE"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class=ic,
                stop_condition="OUTCOME_RESOLUTION",
            )

    @pytest.mark.parametrize("ic", ["COUNTERFACTUAL", "INSPECTION", "SURVEY", "SCRUTINY"])
    def test_stop_config_rejected_for_non_investigative(self, ic):
        with pytest.raises(Exception, match="only allowed for INVESTIGATIVE"):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=_make_template_json(),
                inquiry_class=ic,
                stop_config={"some_key": "value"},
            )

    def test_stop_fields_accepted_for_investigative(self):
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=_make_template_json(),
            inquiry_class="INVESTIGATIVE",
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 2},
        )
        assert tc.inquiry_class == "INVESTIGATIVE"
        assert tc.stop_condition == "EVIDENCE_THRESHOLD"
