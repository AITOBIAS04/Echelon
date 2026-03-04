"""Tests for InquiryClass enum and alias resolution.

Cycle-014, Sprint 1 — Task 1.
"""
from __future__ import annotations

import pytest

from backend.schemas.inquiry import (
    INQUIRY_CLASS_ALIASES,
    VALID_INQUIRY_CLASSES,
    InquiryClass,
    resolve_inquiry_class,
)


class TestInquiryClassEnum:
    """InquiryClass enum has exactly 5 canonical values."""

    def test_exactly_five_members(self) -> None:
        assert len(InquiryClass) == 5

    def test_canonical_values(self) -> None:
        assert InquiryClass.COUNTERFACTUAL == "COUNTERFACTUAL"
        assert InquiryClass.INVESTIGATIVE == "INVESTIGATIVE"
        assert InquiryClass.INSPECTION == "INSPECTION"
        assert InquiryClass.SURVEY == "SURVEY"
        assert InquiryClass.SCRUTINY == "SCRUTINY"

    def test_str_enum_serialises_as_string(self) -> None:
        """StrEnum values serialise without .value."""
        assert str(InquiryClass.COUNTERFACTUAL) == "COUNTERFACTUAL"
        assert f"{InquiryClass.INSPECTION}" == "INSPECTION"

    def test_valid_classes_list(self) -> None:
        assert len(VALID_INQUIRY_CLASSES) == 5
        assert "COUNTERFACTUAL" in VALID_INQUIRY_CLASSES
        assert "SURVEY" in VALID_INQUIRY_CLASSES


class TestAliasMap:
    """Alias map resolves stale values to canonical ones."""

    def test_investigation_maps_to_investigative(self) -> None:
        assert INQUIRY_CLASS_ALIASES["INVESTIGATION"] == InquiryClass.INVESTIGATIVE

    def test_audit_maps_to_scrutiny(self) -> None:
        assert INQUIRY_CLASS_ALIASES["AUDIT"] == InquiryClass.SCRUTINY

    def test_exactly_two_aliases(self) -> None:
        assert len(INQUIRY_CLASS_ALIASES) == 2


class TestResolveInquiryClass:
    """resolve_inquiry_class() handles canonical, aliases, and rejects unknowns."""

    @pytest.mark.parametrize("raw,expected", [
        ("COUNTERFACTUAL", InquiryClass.COUNTERFACTUAL),
        ("INVESTIGATIVE", InquiryClass.INVESTIGATIVE),
        ("INSPECTION", InquiryClass.INSPECTION),
        ("SURVEY", InquiryClass.SURVEY),
        ("SCRUTINY", InquiryClass.SCRUTINY),
    ])
    def test_canonical_values(self, raw: str, expected: InquiryClass) -> None:
        assert resolve_inquiry_class(raw) == expected

    @pytest.mark.parametrize("raw,expected", [
        ("INVESTIGATION", InquiryClass.INVESTIGATIVE),
        ("AUDIT", InquiryClass.SCRUTINY),
    ])
    def test_alias_resolution(self, raw: str, expected: InquiryClass) -> None:
        assert resolve_inquiry_class(raw) == expected

    @pytest.mark.parametrize("raw,expected", [
        ("counterfactual", InquiryClass.COUNTERFACTUAL),
        ("Investigative", InquiryClass.INVESTIGATIVE),
        ("inspection", InquiryClass.INSPECTION),
        ("investigation", InquiryClass.INVESTIGATIVE),
        ("audit", InquiryClass.SCRUTINY),
    ])
    def test_case_insensitive(self, raw: str, expected: InquiryClass) -> None:
        assert resolve_inquiry_class(raw) == expected

    def test_whitespace_stripped(self) -> None:
        assert resolve_inquiry_class("  SURVEY  ") == InquiryClass.SURVEY

    @pytest.mark.parametrize("raw", [
        "UNKNOWN",
        "BINARY",
        "",
        "INSPECT",
        "COUNTERFACTUALLY",
    ])
    def test_unknown_raises_value_error(self, raw: str) -> None:
        with pytest.raises(ValueError, match="Unknown inquiry class"):
            resolve_inquiry_class(raw)

    def test_error_message_includes_valid_values(self) -> None:
        with pytest.raises(ValueError, match="COUNTERFACTUAL") as exc_info:
            resolve_inquiry_class("INVALID")
        assert "Aliases" in str(exc_info.value)
