"""Tests for cycle-038c: Orchestrated Scanner Handoff.

Covers scan result schemas, classification adapter, end-to-end paths,
and provenance hardening.
"""

import pytest

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreExecutionSummary,
    TheatreScopeKey,
)
from backend.schemas.external_theatre_scan import (
    CandidateScanOutcome,
    ExternalTheatreScanRequest,
    ExternalTheatreScanResult,
    ParadoxFinding,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bundle(slug: str, **overrides) -> ExecutedTheatreComparisonBundle:
    """Create a minimal bundle for testing."""
    defaults = {
        "construct_slug": slug,
        "construct_version": "1.0.0",
        "event_keys": ["btc-usd-2026-03"],
        "scope_keys": [TheatreScopeKey(scope_type="region", scope_value="us-equities")],
        "settlement_state": "SETTLED",
        "settlement_outcomes": {"primary": "YES"},
        "oracle_values": {"btc-usd": 68000.0},
        "execution_summary": TheatreExecutionSummary(
            executed_count=3, passed_count=3, failed_count=0, skipped_count=0,
        ),
    }
    defaults.update(overrides)
    return ExecutedTheatreComparisonBundle(**defaults)


def _make_candidate(
    slug_a: str = "tremor",
    slug_b: str = "corona",
    candidate_type: str = "same_event",
    match_strength: str = "EXACT",
    **bundle_overrides_b,
) -> ComparisonCandidateSet:
    """Create a minimal ComparisonCandidateSet."""
    bundle_a = _make_bundle(slug_a)
    bundle_b = _make_bundle(slug_b, **bundle_overrides_b)
    return ComparisonCandidateSet(
        candidate_type=candidate_type,
        bundle_a=bundle_a,
        bundle_b=bundle_b,
        matching_keys=["btc-usd-2026-03"],
        match_strength=match_strength,
    )


# ===========================================================================
# Sprint 0 — Scan Result Schemas
# ===========================================================================

class TestParadoxFinding:
    """Task 0.1: ParadoxFinding schema."""

    def test_paradox_finding_construction(self):
        """ParadoxFinding accepts all 4 paradox_type values and all severity levels."""
        types = [
            "SETTLEMENT_DIVERGENCE",
            "ORACLE_INCONSISTENCY",
            "TEMPORAL_DRIFT",
            "SCOPE_OVERLAP_GAP",
        ]
        severities = ["INFO", "WATCH", "MATERIAL", "CRITICAL"]

        for pt in types:
            for sev in severities:
                finding = ParadoxFinding(
                    paradox_type=pt,
                    severity=sev,
                    description=f"Test {pt} at {sev}",
                    evidence={"key": "value"},
                    construct_a_slug="tremor",
                    construct_b_slug="corona",
                )
                assert finding.paradox_type == pt
                assert finding.severity == sev
                assert finding.evidence == {"key": "value"}


class TestCandidateScanOutcome:
    """Task 0.2: CandidateScanOutcome schema."""

    def test_candidate_scan_outcome_no_findings(self):
        """Empty findings list yields has_paradox=False, scanned=True."""
        outcome = CandidateScanOutcome(
            construct_a_slug="tremor",
            construct_b_slug="corona",
            candidate_type="same_event",
            match_strength="EXACT",
            matching_keys=["btc-usd-2026-03"],
            findings=[],
        )
        assert outcome.has_paradox is False
        assert outcome.scanned is True
        assert outcome.findings == []

    def test_candidate_scan_outcome_with_findings(self):
        """Non-empty findings list yields has_paradox=True."""
        finding = ParadoxFinding(
            paradox_type="SETTLEMENT_DIVERGENCE",
            severity="MATERIAL",
            description="Test divergence",
            evidence={"a_state": "SETTLED", "b_state": "DISPUTED"},
            construct_a_slug="tremor",
            construct_b_slug="corona",
        )
        outcome = CandidateScanOutcome(
            construct_a_slug="tremor",
            construct_b_slug="corona",
            candidate_type="same_event",
            match_strength="EXACT",
            matching_keys=["btc-usd-2026-03"],
            findings=[finding],
        )
        assert outcome.has_paradox is True
        assert len(outcome.findings) == 1


class TestScanRequestResult:
    """Tasks 0.3 + 0.4: ExternalTheatreScanRequest and ExternalTheatreScanResult."""

    def test_scan_request_from_candidates(self):
        """ExternalTheatreScanRequest accepts ComparisonCandidateSet list."""
        candidate = _make_candidate()
        request = ExternalTheatreScanRequest(
            candidates=[candidate],
            event_keys=["btc-usd-2026-03"],
        )
        assert len(request.candidates) == 1
        assert request.candidates[0].candidate_type == "same_event"
        assert request.event_keys == ["btc-usd-2026-03"]

    def test_scan_result_totals(self):
        """ExternalTheatreScanResult computes correct totals."""
        clean_outcome = CandidateScanOutcome(
            construct_a_slug="tremor",
            construct_b_slug="corona",
            candidate_type="same_event",
            match_strength="EXACT",
            matching_keys=["btc-usd-2026-03"],
            findings=[],
        )
        paradox_outcome = CandidateScanOutcome(
            construct_a_slug="tremor",
            construct_b_slug="corona",
            candidate_type="same_event",
            match_strength="EXACT",
            matching_keys=["btc-usd-2026-03"],
            findings=[
                ParadoxFinding(
                    paradox_type="SETTLEMENT_DIVERGENCE",
                    severity="MATERIAL",
                    description="Divergence",
                    evidence={},
                    construct_a_slug="tremor",
                    construct_b_slug="corona",
                ),
            ],
        )
        result = ExternalTheatreScanResult(
            outcomes=[clean_outcome, paradox_outcome],
            total_scanned=2,
            total_with_findings=1,
            total_clean=1,
        )
        assert result.total_scanned == 2
        assert result.total_with_findings == 1
        assert result.total_clean == 1
        assert result.outcomes[0].has_paradox is False
        assert result.outcomes[1].has_paradox is True
