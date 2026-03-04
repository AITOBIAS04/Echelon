"""Tests for inquiry-class-aware evidence accumulation rules.

Cycle-014, Sprint 2 — Task 2.
"""
from __future__ import annotations

import pytest

from backend.services.evidence_service import EvidenceValidation, InquiryEvidenceRules


class TestEvidenceValidationDataclass:
    """EvidenceValidation has expected fields."""

    def test_defaults(self):
        v = EvidenceValidation(valid=True, inquiry_class="TEST", reason="ok")
        assert v.valid is True
        assert v.coverage_pct == 0.0
        assert v.distinct_source_count == 0
        assert v.criteria_evaluated == 0
        assert v.criteria_total == 0
        assert v.participation_count == 0

    def test_frozen(self):
        v = EvidenceValidation(valid=True, inquiry_class="TEST", reason="ok")
        with pytest.raises(AttributeError):
            v.valid = False


class TestCounterfactualEvidence:
    """COUNTERFACTUAL: any evidence present is valid."""

    def test_evidence_present(self):
        result = InquiryEvidenceRules.validate_evidence(
            "COUNTERFACTUAL",
            {"source_coverage_pct": 0.5, "evidence_bundles": [{"source_id": "s1"}]},
            {},
        )
        assert result.valid is True
        assert result.inquiry_class == "COUNTERFACTUAL"
        assert "present" in result.reason.lower()

    def test_no_evidence(self):
        result = InquiryEvidenceRules.validate_evidence(
            "COUNTERFACTUAL",
            {"source_coverage_pct": 0.0, "evidence_bundles": []},
            {},
        )
        assert result.valid is False


class TestInvestigativeEvidence:
    """INVESTIGATIVE: requires corroboration_minimum distinct sources."""

    def test_corroboration_met(self):
        result = InquiryEvidenceRules.validate_evidence(
            "INVESTIGATIVE",
            {
                "source_coverage_pct": 0.8,
                "evidence_bundles": [
                    {"source_id": "wm_news"},
                    {"source_id": "wm_market"},
                    {"source_id": "wm_social"},
                ],
            },
            {"corroboration_minimum": 2},
        )
        assert result.valid is True
        assert result.distinct_source_count == 3

    def test_corroboration_unmet(self):
        result = InquiryEvidenceRules.validate_evidence(
            "INVESTIGATIVE",
            {
                "source_coverage_pct": 0.3,
                "evidence_bundles": [{"source_id": "wm_news"}],
            },
            {"corroboration_minimum": 2},
        )
        assert result.valid is False
        assert result.distinct_source_count == 1
        assert "insufficient" in result.reason.lower()

    def test_default_corroboration_minimum(self):
        """Default corroboration_minimum is 2."""
        result = InquiryEvidenceRules.validate_evidence(
            "INVESTIGATIVE",
            {
                "source_coverage_pct": 0.5,
                "evidence_bundles": [{"source_id": "s1"}],
            },
            {},  # no corroboration_minimum specified
        )
        assert result.valid is False  # 1 < 2 (default)


class TestInspectionEvidence:
    """INSPECTION: single-source acceptable, binary pass/fail."""

    def test_single_source_valid(self):
        result = InquiryEvidenceRules.validate_evidence(
            "INSPECTION",
            {
                "source_coverage_pct": 1.0,
                "evidence_bundles": [{"source_id": "companies_house", "criteria_evaluated": 3}],
            },
            {"criteria_total": 5},
        )
        assert result.valid is True
        assert result.inquiry_class == "INSPECTION"

    def test_no_evidence(self):
        result = InquiryEvidenceRules.validate_evidence(
            "INSPECTION",
            {"source_coverage_pct": 0.0, "evidence_bundles": []},
            {"criteria_total": 5},
        )
        assert result.valid is False


class TestSurveyEvidence:
    """SURVEY: position distribution as evidence."""

    def test_participation_threshold_met(self):
        result = InquiryEvidenceRules.validate_evidence(
            "SURVEY",
            {"source_coverage_pct": 0.0, "evidence_bundles": []},
            {"participation_count": 15, "participation_threshold": 10},
        )
        assert result.valid is True
        assert result.participation_count == 15

    def test_participation_below_threshold(self):
        result = InquiryEvidenceRules.validate_evidence(
            "SURVEY",
            {"source_coverage_pct": 0.0, "evidence_bundles": []},
            {"participation_count": 5, "participation_threshold": 10},
        )
        assert result.valid is False

    def test_default_threshold(self):
        """Default participation_threshold is 10."""
        result = InquiryEvidenceRules.validate_evidence(
            "SURVEY",
            {"source_coverage_pct": 0.0},
            {"participation_count": 0},
        )
        assert result.valid is False


class TestScrutinyEvidence:
    """SCRUTINY: adversarial audit against committed evidence."""

    def test_adversarial_confirmation_met(self):
        result = InquiryEvidenceRules.validate_evidence(
            "SCRUTINY",
            {
                "source_coverage_pct": 0.9,
                "evidence_bundles": [
                    {"source_id": "claim_source"},
                    {"source_id": "verifier_source"},
                ],
            },
            {"corroboration_minimum": 2},
        )
        assert result.valid is True

    def test_no_adversarial(self):
        result = InquiryEvidenceRules.validate_evidence(
            "SCRUTINY",
            {
                "source_coverage_pct": 0.5,
                "evidence_bundles": [{"source_id": "claim_only"}],
            },
            {"corroboration_minimum": 2},
        )
        assert result.valid is False
        assert "unmet" in result.reason.lower()


class TestCaseInsensitivity:
    """inquiry_class parameter is case-insensitive."""

    def test_lowercase(self):
        result = InquiryEvidenceRules.validate_evidence(
            "counterfactual",
            {"source_coverage_pct": 0.5, "evidence_bundles": [{"source_id": "s1"}]},
            {},
        )
        assert result.valid is True
        assert result.inquiry_class == "COUNTERFACTUAL"

    def test_mixed_case(self):
        result = InquiryEvidenceRules.validate_evidence(
            "Survey",
            {"source_coverage_pct": 0.0},
            {"participation_count": 20, "participation_threshold": 10},
        )
        assert result.valid is True


class TestUnknownInquiryClass:
    """Unknown inquiry class falls back to counterfactual behaviour."""

    def test_unknown_with_evidence(self):
        result = InquiryEvidenceRules.validate_evidence(
            "UNKNOWN",
            {"source_coverage_pct": 0.5, "evidence_bundles": [{"source_id": "s1"}]},
            {},
        )
        assert result.valid is True
