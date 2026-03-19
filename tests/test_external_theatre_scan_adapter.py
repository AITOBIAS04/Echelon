"""Tests for cycle-038c: Orchestrated Scanner Handoff.

Covers scan result schemas, classification adapter, end-to-end paths,
and provenance hardening.
"""

import pytest

from backend.services.external_theatre_scan_adapter import (
    ORACLE_TOLERANCE,
    TEMPORAL_DRIFT_WINDOW,
    _detect_oracle_inconsistency,
    _detect_scope_overlap_gap,
    _detect_settlement_divergence,
    _detect_temporal_drift,
    scan_candidates,
)
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


# ===========================================================================
# Sprint 1 — Classification Adapter + Detection Functions
# ===========================================================================

class TestScanCandidatesAPI:
    """Task 1.1: scan_candidates() public API."""

    def test_empty_candidates_returns_empty_result(self):
        """Empty candidates input returns zero totals."""
        request = ExternalTheatreScanRequest(candidates=[])
        result = scan_candidates(request)
        assert result.total_scanned == 0
        assert result.total_clean == 0
        assert result.total_with_findings == 0

    def test_constants_match_real_scanner(self):
        """Module constants match real scanner values."""
        assert ORACLE_TOLERANCE == 0.1
        assert TEMPORAL_DRIFT_WINDOW == 24.0


class TestSettlementDivergence:
    """Task 1.2: _detect_settlement_divergence()."""

    def test_settlement_divergence_settled_vs_disputed(self):
        """SETTLED vs DISPUTED produces MATERIAL finding."""
        a = _make_bundle("tremor", settlement_state="SETTLED")
        b = _make_bundle("corona", settlement_state="DISPUTED")
        finding = _detect_settlement_divergence(a, b)
        assert finding is not None
        assert finding.paradox_type == "SETTLEMENT_DIVERGENCE"
        assert finding.severity == "MATERIAL"

    def test_settlement_divergence_same_state_no_paradox(self):
        """Both SETTLED with same outcomes produces None."""
        a = _make_bundle("tremor", settlement_state="SETTLED",
                         settlement_outcomes={"primary": "YES"})
        b = _make_bundle("corona", settlement_state="SETTLED",
                         settlement_outcomes={"primary": "YES"})
        finding = _detect_settlement_divergence(a, b)
        assert finding is None

    def test_settlement_divergence_pending_skipped(self):
        """Either PENDING produces None."""
        a = _make_bundle("tremor", settlement_state="PENDING")
        b = _make_bundle("corona", settlement_state="SETTLED")
        assert _detect_settlement_divergence(a, b) is None

    def test_settlement_divergence_none_state_skipped(self):
        """Either None state produces None."""
        a = _make_bundle("tremor", settlement_state=None)
        b = _make_bundle("corona", settlement_state="SETTLED")
        assert _detect_settlement_divergence(a, b) is None

    def test_settlement_divergence_outcome_values_differ(self):
        """Both SETTLED but different resolution values produces MATERIAL."""
        a = _make_bundle("tremor", settlement_state="SETTLED",
                         settlement_outcomes={"eq-001": {"resolution": "YES"}})
        b = _make_bundle("corona", settlement_state="SETTLED",
                         settlement_outcomes={"eq-001": {"resolution": "NO"}})
        finding = _detect_settlement_divergence(a, b)
        assert finding is not None
        assert finding.severity == "MATERIAL"
        assert "eq-001" in finding.evidence["divergent_keys"]

    def test_settlement_divergence_severity_always_material(self):
        """Confirm severity is always MATERIAL."""
        a = _make_bundle("tremor", settlement_state="SETTLED")
        b = _make_bundle("corona", settlement_state="DISPUTED")
        finding = _detect_settlement_divergence(a, b)
        assert finding.severity == "MATERIAL"


class TestOracleInconsistency:
    """Task 1.3: _detect_oracle_inconsistency()."""

    def test_oracle_delta_above_tolerance(self):
        """Delta 0.25 (same source) produces MATERIAL."""
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.0, "is_provisional": False}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.25, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is not None
        assert finding.paradox_type == "ORACLE_INCONSISTENCY"
        assert finding.severity == "MATERIAL"
        assert finding.evidence["delta"] == 0.25
        assert finding.evidence["same_source"] is True

    def test_oracle_delta_below_tolerance_no_paradox(self):
        """Delta 0.05 (same source) produces None."""
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.0, "is_provisional": False}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.05, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is None

    def test_oracle_delta_at_tolerance_no_paradox(self):
        """Delta exactly 0.1 produces None (tolerance is <=, not <).

        Uses 0.0 and 0.1 to avoid IEEE 754 precision issues at boundary
        (abs(1.0 - 1.1) = 0.10000000000000009 due to floating point).
        """
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 0.0, "is_provisional": False}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 0.1, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is None

    def test_oracle_cross_source_severity_watch(self):
        """Delta 0.3 (different sources) produces WATCH."""
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-a"],
            oracle_values={"oracle-a": {"value": 1.0, "is_provisional": False}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-b"],
            oracle_values={"oracle-b": {"value": 1.3, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is not None
        assert finding.severity == "WATCH"
        assert finding.evidence["same_source"] is False

    def test_oracle_provisional_revision_info(self):
        """Same source, one provisional produces INFO."""
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.0, "is_provisional": True}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.0, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is not None
        assert finding.severity == "INFO"

    def test_oracle_no_shared_sources_no_values(self):
        """No oracle_values in either bundle produces None."""
        a = _make_bundle("tremor", oracle_source_ids=[], oracle_values={})
        b = _make_bundle("corona", oracle_source_ids=[], oracle_values={})
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is None


class TestTemporalDrift:
    """Task 1.4a: _detect_temporal_drift()."""

    def test_temporal_drift_within_window_no_paradox(self):
        """Delta 12h produces None."""
        a = _make_bundle(
            "tremor",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-19T00:00:00Z"}},
        )
        b = _make_bundle(
            "corona",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-19T12:00:00Z"}},
        )
        assert _detect_temporal_drift(a, b) is None

    def test_temporal_drift_beyond_window_info(self):
        """Delta 30h produces INFO."""
        a = _make_bundle(
            "tremor",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-19T00:00:00Z"}},
        )
        b = _make_bundle(
            "corona",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-20T06:00:00Z"}},
        )
        finding = _detect_temporal_drift(a, b)
        assert finding is not None
        assert finding.severity == "INFO"
        assert finding.evidence["delta_hours"] == 30.0

    def test_temporal_drift_beyond_double_window_watch(self):
        """Delta 50h produces WATCH."""
        a = _make_bundle(
            "tremor",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-19T00:00:00Z"}},
        )
        b = _make_bundle(
            "corona",
            oracle_values={"src": {"value": 1.0, "queried_at": "2026-03-21T02:00:00Z"}},
        )
        finding = _detect_temporal_drift(a, b)
        assert finding is not None
        assert finding.severity == "WATCH"
        assert finding.evidence["delta_hours"] == 50.0


class TestScopeOverlapGap:
    """Task 1.4b: _detect_scope_overlap_gap()."""

    def test_scope_overlap_missing_coverage(self):
        """Bundle A has scope keys B lacks produces WATCH."""
        a = _make_bundle(
            "tremor",
            scope_keys=[
                TheatreScopeKey(scope_type="region", scope_value="us-equities"),
                TheatreScopeKey(scope_type="region", scope_value="eu-equities"),
            ],
        )
        b = _make_bundle(
            "corona",
            scope_keys=[
                TheatreScopeKey(scope_type="region", scope_value="us-equities"),
            ],
        )
        candidate = ComparisonCandidateSet(
            candidate_type="overlap_scope",
            bundle_a=a,
            bundle_b=b,
            matching_keys=["region:us-equities"],
            match_strength="PARTIAL",
        )
        finding = _detect_scope_overlap_gap(a, b, candidate)
        assert finding is not None
        assert finding.paradox_type == "SCOPE_OVERLAP_GAP"
        assert finding.severity == "WATCH"
        assert "region:eu-equities" in finding.evidence["missing_from_b"]

    def test_scope_overlap_full_coverage_no_paradox(self):
        """Identical scope keys produces None."""
        a = _make_bundle(
            "tremor",
            scope_keys=[TheatreScopeKey(scope_type="region", scope_value="us-equities")],
        )
        b = _make_bundle(
            "corona",
            scope_keys=[TheatreScopeKey(scope_type="region", scope_value="us-equities")],
        )
        candidate = ComparisonCandidateSet(
            candidate_type="overlap_scope",
            bundle_a=a,
            bundle_b=b,
            matching_keys=["region:us-equities"],
            match_strength="EXACT",
        )
        finding = _detect_scope_overlap_gap(a, b, candidate)
        assert finding is None
