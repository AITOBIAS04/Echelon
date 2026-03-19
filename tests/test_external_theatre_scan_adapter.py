"""Tests for cycle-038c: Orchestrated Scanner Handoff.

Covers scan result schemas, classification adapter, end-to-end paths,
and provenance hardening.
"""

import json

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


# ===========================================================================
# Sprint 2 — End-to-End Paths
# ===========================================================================

class TestEndToEndTremor:
    """Task 2.1: TREMOR end-to-end scan."""

    def test_e2e_tremor_scan(self):
        """TREMOR bundles through adapter; settlement divergence detected."""
        bundle_pass = ExecutedTheatreComparisonBundle(
            construct_slug="tremor",
            construct_version="1.0.0",
            event_keys=["eq-market-001"],
            scope_keys=[TheatreScopeKey(scope_type="event", scope_value="eq-market-001")],
            settlement_state="SETTLED",
            settlement_outcomes={"eq-market-001": {"resolution": "YES"}},
            oracle_values={"chainlink-btc": {"value": 68000.0, "is_provisional": False}},
            oracle_source_ids=["chainlink-btc"],
            execution_summary=TheatreExecutionSummary(
                executed_count=5, passed_count=5, failed_count=0, skipped_count=0,
            ),
        )
        bundle_fail = ExecutedTheatreComparisonBundle(
            construct_slug="tremor",
            construct_version="1.0.0",
            event_keys=["eq-market-001"],
            scope_keys=[TheatreScopeKey(scope_type="event", scope_value="eq-market-001")],
            settlement_state="DISPUTED",
            settlement_outcomes={"eq-market-001": {"resolution": "NO"}},
            oracle_values={"chainlink-btc": {"value": 68000.0, "is_provisional": False}},
            oracle_source_ids=["chainlink-btc"],
            execution_summary=TheatreExecutionSummary(
                executed_count=5, passed_count=3, failed_count=2, skipped_count=0,
            ),
        )
        candidate = ComparisonCandidateSet(
            candidate_type="same_event",
            bundle_a=bundle_pass,
            bundle_b=bundle_fail,
            matching_keys=["eq-market-001"],
            match_strength="EXACT",
        )
        request = ExternalTheatreScanRequest(candidates=[candidate])
        result = scan_candidates(request)

        assert result.total_scanned >= 1
        assert result.outcomes[0].construct_a_slug == "tremor"
        assert result.outcomes[0].has_paradox is True
        finding_types = [f.paradox_type for f in result.outcomes[0].findings]
        assert "SETTLEMENT_DIVERGENCE" in finding_types


class TestEndToEndCorona:
    """Task 2.2: CORONA end-to-end scan (no-paradox path)."""

    def test_e2e_corona_scan(self):
        """CORONA aligned bundles produce explicit no-paradox."""
        bundle_a = ExecutedTheatreComparisonBundle(
            construct_slug="corona",
            construct_version="2.1.0",
            event_keys=["pandemic-risk-2026-q1"],
            scope_keys=[TheatreScopeKey(scope_type="region", scope_value="global")],
            settlement_state="SETTLED",
            settlement_outcomes={"pandemic-risk-2026-q1": {"resolution": "LOW"}},
            oracle_values={"who-data": {"value": 0.12, "is_provisional": False}},
            oracle_source_ids=["who-data"],
            execution_summary=TheatreExecutionSummary(
                executed_count=4, passed_count=4, failed_count=0, skipped_count=0,
            ),
        )
        bundle_b = ExecutedTheatreComparisonBundle(
            construct_slug="corona",
            construct_version="2.1.0",
            event_keys=["pandemic-risk-2026-q1"],
            scope_keys=[TheatreScopeKey(scope_type="region", scope_value="global")],
            settlement_state="SETTLED",
            settlement_outcomes={"pandemic-risk-2026-q1": {"resolution": "LOW"}},
            oracle_values={"who-data": {"value": 0.13, "is_provisional": False}},
            oracle_source_ids=["who-data"],
            execution_summary=TheatreExecutionSummary(
                executed_count=4, passed_count=4, failed_count=0, skipped_count=0,
            ),
        )
        candidate = ComparisonCandidateSet(
            candidate_type="same_event",
            bundle_a=bundle_a,
            bundle_b=bundle_b,
            matching_keys=["pandemic-risk-2026-q1"],
            match_strength="EXACT",
        )
        request = ExternalTheatreScanRequest(candidates=[candidate])
        result = scan_candidates(request)

        assert result.total_scanned == 1
        assert result.total_clean == 1
        assert result.total_with_findings == 0
        outcome = result.outcomes[0]
        assert outcome.has_paradox is False
        assert outcome.findings == []
        assert outcome.scanned is True


class TestEndToEndCrossTheatre:
    """Task 2.3: TREMOR + CORONA cross-theatre scan."""

    def test_e2e_tremor_corona_cross_theatre(self):
        """TREMOR + CORONA candidates produce both settlement and oracle findings."""
        tremor_bundle = ExecutedTheatreComparisonBundle(
            construct_slug="tremor",
            construct_version="1.0.0",
            event_keys=["cross-market-001"],
            scope_keys=[TheatreScopeKey(scope_type="event", scope_value="cross-market-001")],
            settlement_state="SETTLED",
            settlement_outcomes={"cross-market-001": {"resolution": "YES"}},
            oracle_values={"shared-oracle": {"value": 1.0, "is_provisional": False}},
            oracle_source_ids=["shared-oracle"],
        )
        corona_bundle = ExecutedTheatreComparisonBundle(
            construct_slug="corona",
            construct_version="2.1.0",
            event_keys=["cross-market-001"],
            scope_keys=[TheatreScopeKey(scope_type="event", scope_value="cross-market-001")],
            settlement_state="DISPUTED",
            settlement_outcomes={"cross-market-001": {"resolution": "NO"}},
            oracle_values={"shared-oracle": {"value": 1.3, "is_provisional": False}},
            oracle_source_ids=["shared-oracle"],
        )
        candidate = ComparisonCandidateSet(
            candidate_type="same_event",
            bundle_a=tremor_bundle,
            bundle_b=corona_bundle,
            matching_keys=["cross-market-001"],
            match_strength="EXACT",
        )
        request = ExternalTheatreScanRequest(candidates=[candidate])
        result = scan_candidates(request)

        outcome = result.outcomes[0]
        assert outcome.has_paradox is True
        assert outcome.construct_a_slug == "tremor"
        assert outcome.construct_b_slug == "corona"
        finding_types = [f.paradox_type for f in outcome.findings]
        assert "SETTLEMENT_DIVERGENCE" in finding_types
        assert "ORACLE_INCONSISTENCY" in finding_types


class TestNoParadoxExplicit:
    """Task 2.4: No-paradox explicit results."""

    def test_aligned_bundles_produce_empty_findings(self):
        """Two aligned bundles produce explicit no-paradox outcome."""
        candidate = _make_candidate(
            slug_a="tremor",
            slug_b="corona",
            settlement_state="SETTLED",
            settlement_outcomes={"primary": "YES"},
            oracle_values={"btc-usd": 68000.0},
        )
        request = ExternalTheatreScanRequest(candidates=[candidate])
        result = scan_candidates(request)
        outcome = result.outcomes[0]
        assert outcome.has_paradox is False
        assert outcome.findings == []
        assert outcome.scanned is True

    def test_scan_result_total_clean_accurate(self):
        """Result with mixed outcomes has accurate totals."""
        # 1 divergent candidate + 2 aligned candidates
        divergent = _make_candidate(
            slug_a="tremor", slug_b="corona",
            settlement_state="DISPUTED",
        )
        aligned_1 = _make_candidate(
            slug_a="alpha", slug_b="beta",
            settlement_state="SETTLED",
            settlement_outcomes={"primary": "YES"},
            oracle_values={"btc-usd": 68000.0},
        )
        aligned_2 = _make_candidate(
            slug_a="gamma", slug_b="delta",
            settlement_state="SETTLED",
            settlement_outcomes={"primary": "YES"},
            oracle_values={"btc-usd": 68000.0},
        )
        request = ExternalTheatreScanRequest(
            candidates=[divergent, aligned_1, aligned_2],
        )
        result = scan_candidates(request)
        assert result.total_scanned == 3
        assert result.total_with_findings == 1
        assert result.total_clean == 2

    def test_no_candidates_produces_empty_result(self):
        """Empty candidates list produces empty result."""
        request = ExternalTheatreScanRequest(candidates=[])
        result = scan_candidates(request)
        assert result.total_scanned == 0
        assert result.outcomes == []


class TestProvenancePreservation:
    """Task 2.5: Provenance preservation end-to-end."""

    def test_e2e_provenance_preservation(self):
        """Scan results carry construct slugs, match keys, and evidence."""
        tremor = ExecutedTheatreComparisonBundle(
            construct_slug="tremor",
            construct_version="1.0.0",
            event_keys=["prov-event-001"],
            scope_keys=[],
            settlement_state="SETTLED",
            settlement_outcomes={"prov-event-001": {"resolution": "YES"}},
            oracle_values={},
            oracle_source_ids=[],
        )
        corona = ExecutedTheatreComparisonBundle(
            construct_slug="corona",
            construct_version="2.1.0",
            event_keys=["prov-event-001"],
            scope_keys=[],
            settlement_state="DISPUTED",
            settlement_outcomes={"prov-event-001": {"resolution": "NO"}},
            oracle_values={},
            oracle_source_ids=[],
        )
        candidate = ComparisonCandidateSet(
            candidate_type="same_event",
            bundle_a=tremor,
            bundle_b=corona,
            matching_keys=["prov-event-001"],
            match_strength="EXACT",
        )
        request = ExternalTheatreScanRequest(candidates=[candidate])
        result = scan_candidates(request)

        outcome = result.outcomes[0]
        # Outcome provenance
        assert outcome.construct_a_slug == "tremor"
        assert outcome.construct_b_slug == "corona"
        assert outcome.candidate_type == "same_event"
        assert outcome.matching_keys == ["prov-event-001"]

        # Finding provenance
        assert len(outcome.findings) >= 1
        finding = outcome.findings[0]
        assert finding.construct_a_slug == "tremor"
        assert finding.construct_b_slug == "corona"
        assert finding.evidence  # non-empty
        assert "construct_a_settlement_state" in finding.evidence


# ===========================================================================
# Sprint 3 — Provenance Hardening + Regression
# ===========================================================================

class TestEvidenceDetailAssertions:
    """Task 3.1: Evidence detail assertions."""

    def test_settlement_evidence_keys(self):
        """Settlement divergence evidence contains all specified keys."""
        a = _make_bundle("tremor", settlement_state="SETTLED",
                         settlement_outcomes={"k1": {"resolution": "YES"}})
        b = _make_bundle("corona", settlement_state="DISPUTED",
                         settlement_outcomes={"k1": {"resolution": "NO"}})
        finding = _detect_settlement_divergence(a, b)
        assert finding is not None
        expected_keys = {
            "construct_a_settlement_state",
            "construct_b_settlement_state",
            "construct_a_outcomes",
            "construct_b_outcomes",
            "divergent_keys",
        }
        assert expected_keys <= set(finding.evidence.keys())
        assert finding.evidence["construct_a_settlement_state"] == "SETTLED"
        assert finding.evidence["construct_b_settlement_state"] == "DISPUTED"

    def test_oracle_evidence_keys(self):
        """Oracle inconsistency evidence contains all specified keys + correct tolerance."""
        a = _make_bundle(
            "tremor",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.0, "is_provisional": False}},
        )
        b = _make_bundle(
            "corona",
            oracle_source_ids=["oracle-1"],
            oracle_values={"oracle-1": {"value": 1.5, "is_provisional": False}},
        )
        finding = _detect_oracle_inconsistency(a, b)
        assert finding is not None
        expected_keys = {
            "source_a", "source_b", "delta", "tolerance",
            "same_source", "value_a", "value_b",
            "is_provisional_a", "is_provisional_b",
        }
        assert expected_keys <= set(finding.evidence.keys())
        assert finding.evidence["tolerance"] == 0.1
        assert isinstance(finding.evidence["delta"], (int, float))

    def test_temporal_drift_evidence_keys(self):
        """Temporal drift evidence contains all specified keys + correct window."""
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
        expected_keys = {"delta_hours", "window_hours", "time_a", "time_b"}
        assert expected_keys <= set(finding.evidence.keys())
        assert finding.evidence["window_hours"] == 24.0
        assert isinstance(finding.evidence["delta_hours"], (int, float))


class TestRegression038:
    """Task 3.2: Regression against 038a/038b surfaces."""

    def test_existing_038a_bundle_builder_unchanged(self):
        """Import build_comparison_bundle and verify callable."""
        from backend.services.theatre_comparison_bundle_builder import (
            build_comparison_bundle,
        )
        assert callable(build_comparison_bundle)

    def test_existing_038a_candidate_generator_unchanged(self):
        """Import generate_candidates and verify callable."""
        from backend.services.theatre_comparison_candidates import (
            generate_candidates,
        )
        assert callable(generate_candidates)

    def test_038c_adapter_imports_cleanly(self):
        """038c adapter module imports without errors and is callable."""
        from backend.services.external_theatre_scan_adapter import scan_candidates
        assert callable(scan_candidates)
        # Verify it works with empty input (no side effects)
        request = ExternalTheatreScanRequest(candidates=[])
        result = scan_candidates(request)
        assert result.total_scanned == 0


# ===========================================================================
# Sprint 3+ — Real 038b→038c Integration (P1 Codex finding)
# ===========================================================================

# Two realistic construct.json payloads — TREMOR (echelon-nested) and CORONA (root-level).
# Both have cross-validation sources so the pipeline produces oracle checks,
# and both share event_keys so candidate generation pairs them as same_event.
_TREMOR_CONSTRUCT_JSON = json.dumps({
    "name": "TREMOR-EQ-USWEST",
    "echelon": {
        "theatre_templates": [
            {
                "id": "eq-magnitude-binary",
                "name": "EQ Magnitude Binary",
                "resolution": "binary",
                "oracle": "USGS reviewed catalog",
                "brier_type": "binary",
            },
            {
                "id": "eq-region-multi",
                "name": "EQ Region Multi",
                "resolution": "multi_class",
                "oracle": "USGS ShakeMap",
            },
        ],
        "osint_sources": [
            {"id": "usgs-primary", "name": "USGS Primary", "role": "primary"},
            {"id": "usgs-cross", "name": "USGS Cross Val", "role": "cross_validation"},
        ],
        "verification_checks": [
            {"check": "magnitude_threshold", "ground_truth": "USGS", "description": "Mag ≥ 4.5"},
        ],
        "settlement_tiers": [
            {"tier": 1, "label": "Primary settlement"},
        ],
    },
    "rlmf": {"exports": ["brier_score"]},
})

_CORONA_CONSTRUCT_JSON = json.dumps({
    "name": "CORONA-SOLAR-XCLASS",
    "theatre_templates": [
        {
            "id": "xray-flux-binary",
            "name": "X-Ray Flux Binary",
            "type": "binary",
            "resolution": "GOES X-ray + DONKI FLR",
        },
        {
            "id": "cme-arrival-multi",
            "name": "CME Arrival Multi",
            "type": "multi_class",
            "resolution": "DONKI CME catalog",
        },
    ],
    "data_sources": [
        {"name": "GOES Primary", "role": "primary"},
        {"name": "DONKI Cross", "role": "cross_validation"},
    ],
})


class TestIntegration038bTo038c:
    """P1 Codex finding: prove the real 038b→038c runtime handoff.

    These tests call prepare_external_theatres() with realistic construct.json
    payloads and feed the resulting candidates into scan_candidates(). No
    hand-constructed bundles — the entire pipeline is exercised end-to-end.
    """

    def _run_orchestrator(self, event_keys=None, scope_keys=None):
        """Run the full orchestrator with TREMOR + CORONA constructs."""
        from backend.services.external_theatre_orchestrator import (
            prepare_external_theatres,
        )
        from backend.schemas.external_theatre_orchestration import (
            ExternalTheatreInput,
            ExternalTheatrePreparationRequest,
        )

        theatres = [
            ExternalTheatreInput(
                construct_slug="tremor-eq-uswest",
                construct_version="0.1.0",
                construct_json=_TREMOR_CONSTRUCT_JSON,
            ),
            ExternalTheatreInput(
                construct_slug="corona-solar-xclass",
                construct_version="0.1.0",
                construct_json=_CORONA_CONSTRUCT_JSON,
            ),
        ]
        request = ExternalTheatrePreparationRequest(
            theatres=theatres,
            event_keys=event_keys or ["shared-event-2026-03"],
            scope_keys=scope_keys or [
                TheatreScopeKey(scope_type="region", scope_value="us-west"),
            ],
            certificate_id="cert-integration-test",
        )
        return prepare_external_theatres(request)

    def test_orchestrator_produces_successful_bundles(self):
        """Both theatres should parse, extract, execute, and bundle."""
        prep = self._run_orchestrator()

        assert prep.total_theatres == 2
        assert prep.total_successful == 2, (
            f"Expected 2 successful, got {prep.total_successful}. "
            f"Failures: {[e.error for e in prep.theatres if e.error]}"
        )
        assert prep.total_failed == 0

    def test_orchestrator_generates_candidates(self):
        """Two distinct-slug bundles should produce ≥1 candidate."""
        prep = self._run_orchestrator()

        assert len(prep.candidates) >= 1, (
            "Expected candidates from two successful bundles"
        )
        # Candidate should pair TREMOR and CORONA
        c = prep.candidates[0]
        slugs = {c.bundle_a.construct_slug, c.bundle_b.construct_slug}
        assert "tremor-eq-uswest" in slugs
        assert "corona-solar-xclass" in slugs

    def test_full_handoff_scan_produces_result(self):
        """End-to-end: orchestrator output feeds directly into scan adapter."""
        prep = self._run_orchestrator()

        # Build scan request from orchestrator output — the actual handoff
        scan_request = ExternalTheatreScanRequest(
            candidates=prep.candidates,
            event_keys=prep.event_keys_used,
            scope_keys=prep.scope_keys_used,
        )
        scan_result = scan_candidates(scan_request)

        # Structural integrity
        assert scan_result.total_scanned == len(prep.candidates)
        assert scan_result.total_scanned >= 1
        assert scan_result.total_with_findings + scan_result.total_clean == scan_result.total_scanned

        # Every outcome must have correct slug provenance from the real bundles
        for outcome in scan_result.outcomes:
            assert outcome.construct_a_slug in {"tremor-eq-uswest", "corona-solar-xclass"}
            assert outcome.construct_b_slug in {"tremor-eq-uswest", "corona-solar-xclass"}
            assert outcome.scanned is True
            assert outcome.candidate_type in {"same_event", "overlap_scope"}

    def test_handoff_findings_have_valid_structure(self):
        """Any findings from the real handoff must have valid paradox types and severity."""
        prep = self._run_orchestrator()
        scan_request = ExternalTheatreScanRequest(
            candidates=prep.candidates,
            event_keys=prep.event_keys_used,
            scope_keys=prep.scope_keys_used,
        )
        scan_result = scan_candidates(scan_request)

        valid_types = {
            "SETTLEMENT_DIVERGENCE", "ORACLE_INCONSISTENCY",
            "TEMPORAL_DRIFT", "SCOPE_OVERLAP_GAP",
        }
        valid_severities = {"INFO", "WATCH", "MATERIAL", "CRITICAL"}

        for outcome in scan_result.outcomes:
            for finding in outcome.findings:
                assert finding.paradox_type in valid_types, (
                    f"Unknown type: {finding.paradox_type}"
                )
                assert finding.severity in valid_severities, (
                    f"Unknown severity: {finding.severity}"
                )
                assert finding.evidence, "Finding must have non-empty evidence"
                assert finding.construct_a_slug, "Finding must trace construct_a"
                assert finding.construct_b_slug, "Finding must trace construct_b"

    def test_handoff_bundles_carry_certificate_id(self):
        """Certificate ID from request must propagate through bundles."""
        prep = self._run_orchestrator()

        for candidate in prep.candidates:
            assert candidate.bundle_a.certificate_id == "cert-integration-test"
            assert candidate.bundle_b.certificate_id == "cert-integration-test"

    def test_handoff_with_shared_event_keys_produces_same_event_candidate(self):
        """Shared event keys should produce same_event candidates."""
        prep = self._run_orchestrator(event_keys=["shared-eq-event"])

        same_event = [c for c in prep.candidates if c.candidate_type == "same_event"]
        assert len(same_event) >= 1, (
            f"Expected same_event candidate. Types: "
            f"{[c.candidate_type for c in prep.candidates]}"
        )
