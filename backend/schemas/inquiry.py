"""Canonical InquiryClass enum — single source of truth.

Every backend surface that needs an inquiry class value imports from here.
Aliases handle backward compatibility with stale values from pre-014 code.

Cycle-014, Sprint 1 — Task 1.
"""
from __future__ import annotations

from enum import Enum


class InquiryClass(str, Enum):
    """Five inquiry classes from System Bible v13 §X."""

    COUNTERFACTUAL = "COUNTERFACTUAL"
    INVESTIGATIVE = "INVESTIGATIVE"
    INSPECTION = "INSPECTION"
    SURVEY = "SURVEY"
    SCRUTINY = "SCRUTINY"

    def __str__(self) -> str:
        return self.value


# Backward-compatible aliases for stale values.
INQUIRY_CLASS_ALIASES: dict[str, InquiryClass] = {
    "INVESTIGATION": InquiryClass.INVESTIGATIVE,
    "AUDIT": InquiryClass.SCRUTINY,
}

# Valid values for use in Field descriptions / error messages.
VALID_INQUIRY_CLASSES = [e.value for e in InquiryClass]


def resolve_inquiry_class(raw: str) -> InquiryClass:
    """Resolve a raw string to a canonical InquiryClass.

    Accepts canonical values and aliases (case-insensitive).
    Raises ValueError on unknown input.
    """
    upper = raw.upper().strip()
    if upper in InquiryClass.__members__:
        return InquiryClass(upper)
    alias = INQUIRY_CLASS_ALIASES.get(upper)
    if alias is not None:
        return alias
    raise ValueError(
        f"Unknown inquiry class '{raw}'. "
        f"Valid: {VALID_INQUIRY_CLASSES}. "
        f"Aliases: {list(INQUIRY_CLASS_ALIASES.keys())}"
    )
