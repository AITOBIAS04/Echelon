"""Tests for inquiry_class alignment in CalibrationCertificate.

Cycle-014, Sprint 1 — Task 6.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from osint_pipeline.models.certificate import CalibrationCertificate


def _cert_kwargs(**overrides: object) -> dict:
    """Minimal valid kwargs for CalibrationCertificate."""
    base = dict(
        theatre_id="test-theatre",
        inquiry_class="INSPECTION",
        execution_path="replay",
        verification_tier="UNVERIFIED",
        composite_score=0.85,
        all_criteria_passed=True,
        evidence_bundle_hash="a" * 64,
        commitment_hash="b" * 64,
        oracle_id="oracle-1",
    )
    base.update(overrides)
    return base


class TestCertificateInquiryClass:
    """CalibrationCertificate validates inquiry_class to canonical 5 values."""

    @pytest.mark.parametrize(
        "ic",
        ["COUNTERFACTUAL", "INVESTIGATIVE", "INSPECTION", "SURVEY", "SCRUTINY"],
    )
    def test_all_canonical_values_accepted(self, ic: str) -> None:
        cert = CalibrationCertificate(**_cert_kwargs(inquiry_class=ic))
        assert cert.inquiry_class == ic

    def test_case_insensitive(self) -> None:
        cert = CalibrationCertificate(**_cert_kwargs(inquiry_class="inspection"))
        assert cert.inquiry_class == "INSPECTION"

    def test_whitespace_stripped(self) -> None:
        cert = CalibrationCertificate(**_cert_kwargs(inquiry_class="  SURVEY  "))
        assert cert.inquiry_class == "SURVEY"

    def test_stale_investigation_rejected(self) -> None:
        with pytest.raises(ValidationError, match="inquiry_class"):
            CalibrationCertificate(**_cert_kwargs(inquiry_class="INVESTIGATION"))

    def test_stale_audit_rejected(self) -> None:
        with pytest.raises(ValidationError, match="inquiry_class"):
            CalibrationCertificate(**_cert_kwargs(inquiry_class="AUDIT"))

    def test_unknown_rejected(self) -> None:
        with pytest.raises(ValidationError, match="inquiry_class"):
            CalibrationCertificate(**_cert_kwargs(inquiry_class="BOGUS"))


class TestCertificateResolutionTriggerReason:
    """CalibrationCertificate includes resolution_trigger_reason."""

    def test_default_empty(self) -> None:
        cert = CalibrationCertificate(**_cert_kwargs())
        assert cert.resolution_trigger_reason == ""

    def test_explicit_reason(self) -> None:
        cert = CalibrationCertificate(
            **_cert_kwargs(resolution_trigger_reason="criteria_complete")
        )
        assert cert.resolution_trigger_reason == "criteria_complete"

    def test_trigger_matches_inquiry_class(self) -> None:
        """Trigger reason must be valid for the inquiry class."""
        # INSPECTION + criteria_complete is valid
        cert = CalibrationCertificate(
            **_cert_kwargs(
                inquiry_class="INSPECTION",
                resolution_trigger_reason="criteria_complete",
            )
        )
        assert cert.resolution_trigger_reason == "criteria_complete"

    def test_trigger_mismatch_rejected(self) -> None:
        """Wrong trigger for inquiry class is rejected."""
        with pytest.raises(ValidationError, match="not valid for inquiry class"):
            CalibrationCertificate(
                **_cert_kwargs(
                    inquiry_class="INSPECTION",
                    resolution_trigger_reason="evidence_threshold_met",
                )
            )

    def test_time_window_closed_always_valid(self) -> None:
        """time_window_closed is valid for all inquiry classes."""
        for ic in ["COUNTERFACTUAL", "INVESTIGATIVE", "INSPECTION", "SURVEY", "SCRUTINY"]:
            cert = CalibrationCertificate(
                **_cert_kwargs(
                    inquiry_class=ic,
                    resolution_trigger_reason="time_window_closed",
                )
            )
            assert cert.resolution_trigger_reason == "time_window_closed"
