"""Constraint Yielding Gate — enforces review escalation for UNVERIFIED constructs.

Rule: UNVERIFIED + review:skip -> review:full. No override.
BACKTESTED and PROVEN constructs honour their declared preference.
"""

from __future__ import annotations


class ConstraintYieldingGate:
    """Enforces: UNVERIFIED + review:skip -> review:full. No override."""

    @staticmethod
    def resolve_review_preference(
        tier: str,
        declared_preference: str,
    ) -> str:
        """Resolve actual review level.

        UNVERIFIED constructs always get review:full regardless of declared preference.
        BACKTESTED/PROVEN constructs honour their declared preference.
        """
        if tier == "UNVERIFIED" and declared_preference == "skip":
            return "full"
        return declared_preference
