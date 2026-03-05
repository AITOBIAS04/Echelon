"""Tests for Investigation Corroboration Checker — independence enforcement."""

from backend.investigation.claim_graph import (
    ClaimNode,
    ClaimStatus,
    ClaimType,
    CorroborationCheck,
)
from backend.investigation.corroboration_checker import (
    InvestigationCorroborationChecker,
)


def _make_claim() -> ClaimNode:
    return ClaimNode(
        claim_id="C001",
        claim_text="Company X filed for bankruptcy",
        claim_type=ClaimType.FACT,
        evidence_refs=["E001"],
    )


class TestIndependenceInvariant:
    def test_supported_requires_two_independent_upstreams(self):
        """Single upstream group cannot yield SUPPORTED."""
        checker = InvestigationCorroborationChecker()
        claim = _make_claim()

        checks = [
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC1",
                upstream_group="group_a",
                status="confirmed",
                confidence=0.9,
            ),
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC2",
                upstream_group="group_a",  # Same group
                status="confirmed",
                confidence=0.85,
            ),
        ]

        result = checker.evaluate_claim(claim, checks)
        assert result == ClaimStatus.PARTIALLY_SUPPORTED

    def test_supported_with_two_independent_upstreams(self):
        """Two distinct upstream groups with confirmed → SUPPORTED."""
        checker = InvestigationCorroborationChecker()
        claim = _make_claim()

        checks = [
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC1",
                upstream_group="group_a",
                status="confirmed",
                confidence=0.9,
            ),
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC2",
                upstream_group="group_b",
                status="confirmed",
                confidence=0.85,
            ),
        ]

        result = checker.evaluate_claim(claim, checks)
        assert result == ClaimStatus.SUPPORTED


class TestPrivateLeakRule:
    def test_private_leak_only_remains_unconfirmed(self):
        """PRIVATE_LEAK-only evidence cannot achieve SUPPORTED — no confirmed checks."""
        checker = InvestigationCorroborationChecker()
        claim = _make_claim()

        # No confirmed checks at all → UNCONFIRMED
        checks = [
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC_LEAK",
                upstream_group="leak_channel",
                status="unavailable",
                confidence=0.0,
            ),
        ]

        result = checker.evaluate_claim(claim, checks)
        assert result == ClaimStatus.UNCONFIRMED


class TestPartialStatus:
    def test_partial_status_with_single_upstream(self):
        """Single confirmed upstream group → PARTIALLY_SUPPORTED."""
        checker = InvestigationCorroborationChecker()
        claim = _make_claim()

        checks = [
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC1",
                upstream_group="group_a",
                status="confirmed",
                confidence=0.9,
            ),
        ]

        result = checker.evaluate_claim(claim, checks)
        assert result == ClaimStatus.PARTIALLY_SUPPORTED


class TestDeterminism:
    def test_checker_output_deterministic(self):
        """Same inputs → same output."""
        checker = InvestigationCorroborationChecker()
        claim = _make_claim()

        checks = [
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC1",
                upstream_group="wm",
                status="confirmed",
                confidence=0.9,
            ),
            CorroborationCheck(
                claim_id="C001",
                source_id="SRC2",
                upstream_group="ch",
                status="confirmed",
                confidence=0.85,
            ),
        ]

        r1 = checker.evaluate_claim(claim, checks)
        r2 = checker.evaluate_claim(claim, checks)
        assert r1 == r2 == ClaimStatus.SUPPORTED
