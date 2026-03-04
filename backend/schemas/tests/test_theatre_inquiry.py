"""Tests for inquiry_class integration in Theatre schemas.

Cycle-014, Sprint 1 — Task 2.
"""
from __future__ import annotations

import pytest

from backend.schemas.theatre import (
    TemplateResponse,
    TheatreCertificateResponse,
    TheatreCreate,
    TheatreResponse,
)


class TestTheatreCreateInquiryClass:
    """TheatreCreate handles inquiry_class from body and template_json."""

    def _make_template_json(self, **overrides: object) -> dict:
        base = {
            "theatre_id": "test-001",
            "execution_path": "market",
            "template_family": "counterfactual",
        }
        base.update(overrides)
        return base

    def test_explicit_inquiry_class(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(),
            inquiry_class="COUNTERFACTUAL",
        )
        assert tc.inquiry_class == "COUNTERFACTUAL"

    def test_inquiry_class_from_template_json(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(inquiry_class="INSPECTION"),
        )
        assert tc.inquiry_class == "INSPECTION"

    def test_explicit_overrides_template_json(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(inquiry_class="INSPECTION"),
            inquiry_class="SCRUTINY",
        )
        assert tc.inquiry_class == "SCRUTINY"

    def test_alias_resolved_in_explicit(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(),
            inquiry_class="INVESTIGATION",
        )
        assert tc.inquiry_class == "INVESTIGATIVE"

    def test_alias_resolved_from_template_json(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(inquiry_class="AUDIT"),
        )
        assert tc.inquiry_class == "SCRUTINY"

    def test_omitted_inquiry_class_defaults_to_counterfactual(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(),
        )
        assert tc.inquiry_class == "COUNTERFACTUAL"

    def test_explicit_null_inquiry_class_raises_422(self) -> None:
        with pytest.raises(Exception):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=self._make_template_json(),
                inquiry_class=None,
            )

    def test_invalid_inquiry_class_raises(self) -> None:
        with pytest.raises(Exception):
            TheatreCreate(
                template_id="t1",
                construct_id="c1",
                template_json=self._make_template_json(),
                inquiry_class="INVALID",
            )

    def test_case_insensitive(self) -> None:
        tc = TheatreCreate(
            template_id="t1",
            construct_id="c1",
            template_json=self._make_template_json(),
            inquiry_class="survey",
        )
        assert tc.inquiry_class == "SURVEY"


class TestTheatreResponseInquiryClass:
    """TheatreResponse includes inquiry_class."""

    def test_response_includes_inquiry_class(self) -> None:
        from datetime import datetime
        r = TheatreResponse(
            id="t1", user_id="u1", template_id="tpl1",
            state="DRAFT", construct_id="c1",
            inquiry_class="INVESTIGATIVE",
            commitment_hash=None, committed_at=None,
            progress=0, total_episodes=0, failure_count=0,
            error=None, resolved_at=None, certificate_id=None,
            created_at=datetime.now(), updated_at=datetime.now(),
        )
        assert r.inquiry_class == "INVESTIGATIVE"

    def test_response_null_coalesces_to_counterfactual(self) -> None:
        from datetime import datetime
        r = TheatreResponse(
            id="t1", user_id="u1", template_id="tpl1",
            state="DRAFT", construct_id="c1",
            commitment_hash=None, committed_at=None,
            progress=0, total_episodes=0, failure_count=0,
            error=None, resolved_at=None, certificate_id=None,
            created_at=datetime.now(), updated_at=datetime.now(),
        )
        assert r.inquiry_class == "COUNTERFACTUAL"


class TestCertificateResponseInquiryClass:
    """TheatreCertificateResponse includes inquiry_class."""

    def _make_cert_response(self, **overrides: object) -> TheatreCertificateResponse:
        from datetime import datetime
        defaults = dict(
            id="cert1", theatre_id="t1", template_id="tpl1",
            construct_id="c1", inquiry_class="INSPECTION",
            criteria_json={}, scores_json={}, composite_score=0.9,
            precision=0.8, recall=0.7, brier_score=0.1, ece=0.05,
            replay_count=10, evidence_bundle_hash="a" * 64,
            ground_truth_hash="b" * 64, construct_version="1.0",
            construct_chain_versions=None, scorer_version="1.0",
            methodology_version="1.0", dataset_hash="c" * 64,
            verification_tier="BACKTESTED", commitment_hash="d" * 64,
            issued_at=datetime.now(), expires_at=None,
            theatre_committed_at=datetime.now(),
            theatre_resolved_at=datetime.now(),
            ground_truth_source="test", execution_path="replay",
        )
        defaults.update(overrides)
        return TheatreCertificateResponse(**defaults)

    def test_certificate_response_has_inquiry_class(self) -> None:
        r = self._make_cert_response(inquiry_class="INSPECTION")
        assert r.inquiry_class == "INSPECTION"

    def test_certificate_null_coalesces_to_counterfactual(self) -> None:
        r = self._make_cert_response(inquiry_class=None)
        assert r.inquiry_class == "COUNTERFACTUAL"


class TestTemplateResponseInquiryClass:
    """TemplateResponse includes inquiry_class."""

    def test_template_response_has_inquiry_class(self) -> None:
        from datetime import datetime
        r = TemplateResponse(
            id="tpl1", template_family="product",
            execution_path="replay", display_name="Test",
            description=None, schema_version="2.0",
            inquiry_class="SURVEY",
            created_at=datetime.now(),
        )
        assert r.inquiry_class == "SURVEY"

    def test_template_null_coalesces_to_counterfactual(self) -> None:
        from datetime import datetime
        r = TemplateResponse(
            id="tpl1", template_family="product",
            execution_path="replay", display_name="Test",
            description=None, schema_version="2.0",
            created_at=datetime.now(),
        )
        assert r.inquiry_class == "COUNTERFACTUAL"
