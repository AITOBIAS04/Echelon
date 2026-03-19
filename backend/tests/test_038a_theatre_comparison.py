"""Tests for cycle-038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

Sprint 0: Schema validation + provenance preservation (7 tests).
Sprint 1: Bundle builder (8 tests).
Sprint 2: Candidate sets (8 tests).
Sprint 3: 038 compatibility + e2e regression (7 tests).
"""

import pytest

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreCheckSummary,
    TheatreExecutionSummary,
    TheatreScopeKey,
)
from backend.tests.fixtures.theatre_comparison_fixtures import (
    SHARED_EVENT_KEY,
    SHARED_SCOPE_KEY,
    make_corona_bundle,
    make_corona_execution_result,
    make_corona_fixture_input,
    make_tremor_bundle,
    make_tremor_execution_result,
    make_tremor_fixture_input,
)


# ═══════════════════════════════════════════════════════════════════
# Sprint 0 — Schema Validation (4 tests)
# ═══════════════════════════════════════════════════════════════════

class TestSchemaValidation:
    """Verify all models construct and serialize correctly."""

    def test_bundle_constructs_with_minimal_fields(self):
        """ExecutedTheatreComparisonBundle accepts minimal required fields."""
        bundle = ExecutedTheatreComparisonBundle(
            construct_slug="test",
            construct_version="1.0.0",
        )
        assert bundle.construct_slug == "test"
        assert bundle.template_ids == []
        assert bundle.event_keys == []
        assert bundle.scope_keys == []
        assert bundle.settlement_state is None
        assert bundle.execution_summary.executed_count == 0

    def test_bundle_serializes_to_dict(self):
        """Bundle round-trips through model_dump."""
        bundle = make_tremor_bundle()
        d = bundle.model_dump()
        assert d["construct_slug"] == "tremor"
        assert len(d["template_ids"]) == 2
        assert len(d["execution_summary"]["checks"]) == 3
        # Round-trip
        restored = ExecutedTheatreComparisonBundle.model_validate(d)
        assert restored.construct_slug == bundle.construct_slug
        assert len(restored.execution_summary.checks) == 3

    def test_execution_summary_defaults(self):
        """TheatreExecutionSummary defaults to zero counts."""
        summary = TheatreExecutionSummary()
        assert summary.executed_count == 0
        assert summary.passed_count == 0
        assert summary.failed_count == 0
        assert summary.skipped_count == 0
        assert summary.has_critical_failures is False
        assert summary.checks == []

    def test_scope_key_normalization(self):
        """TheatreScopeKey normalizes to lowercase-hyphenated."""
        sk = TheatreScopeKey(scope_type="Region", scope_value="US_Equities")
        normalized = sk.normalized()
        assert normalized.scope_type == "region"
        assert normalized.scope_value == "us-equities"
        assert normalized.key() == "region:us-equities"

        # Already normalized stays the same
        sk2 = TheatreScopeKey(scope_type="entity", scope_value="btc-usd")
        assert sk2.key() == "entity:btc-usd"


# ═══════════════════════════════════════════════════════════════════
# Sprint 0 — Provenance Preservation (3 tests)
# ═══════════════════════════════════════════════════════════════════

class TestProvenancePreservation:
    """Verify execution provenance survives bundle projection."""

    def test_execution_summary_counts_correct(self):
        """TREMOR bundle has correct execution counts (2 passed, 1 failed)."""
        bundle = make_tremor_bundle()
        summary = bundle.execution_summary
        assert summary.executed_count == 3
        assert summary.passed_count == 2
        assert summary.failed_count == 1
        assert summary.skipped_count == 0
        assert summary.has_critical_failures is True

    def test_check_evidence_preserved_in_summary(self):
        """Individual check evidence dicts survive in TheatreCheckSummary."""
        bundle = make_corona_bundle()
        checks = bundle.execution_summary.checks
        assert len(checks) == 3

        cal_check = next(c for c in checks if c.check_type == "CALIBRATION_VALIDITY")
        assert cal_check.evidence["computed_brier"] == 0.18
        assert cal_check.is_critical is False

        settlement_check = next(
            c for c in checks if c.check_type == "SETTLEMENT_ACCURACY"
        )
        assert settlement_check.evidence["resolution"] == "CORRECT"
        assert settlement_check.is_critical is True

    def test_provenance_refs_populated(self):
        """provenance_refs captures all executed check_ids."""
        tremor = make_tremor_bundle()
        assert len(tremor.provenance_refs) == 3
        assert "theatre:SETTLEMENT_ACCURACY:tmpl-eq-001" in tremor.provenance_refs
        assert "theatre:ORACLE_CONSISTENCY:src-chainlink" in tremor.provenance_refs

        corona = make_corona_bundle()
        assert len(corona.provenance_refs) == 3
        assert "theatre:CALIBRATION_VALIDITY:brier" in corona.provenance_refs


# ═══════════════════════════════════════════════════════════════════
# Sprint 1 — TREMOR Bundle Builder (4 tests)
# ═══════════════════════════════════════════════════════════════════

from backend.services.theatre_comparison_bundle_builder import build_comparison_bundle


class TestTremorBundleBuilder:
    """Verify TREMOR execution → bundle mapping."""

    def test_identity_mapping(self):
        """Builder extracts slug from result, version from fixture."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture, certificate_id="cert-t-001")

        assert bundle.construct_slug == "tremor"
        assert bundle.construct_version == "1.0.0"
        assert bundle.certificate_id == "cert-t-001"

    def test_settlement_outcomes_from_evidence(self):
        """Settlement outcomes extracted from SETTLEMENT_ACCURACY checks."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.settlement_outcomes) == 2
        assert bundle.settlement_outcomes["tmpl-eq-001"]["resolution"] == "CORRECT"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["resolution"] == "INCORRECT"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["predicted_outcome"] == "DOWN"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["actual_outcome"] == "UP"

        # TREMOR has 1 FAILED settlement → DISPUTED
        assert bundle.settlement_state == "DISPUTED"

    def test_oracle_values_from_evidence(self):
        """Oracle values extracted from ORACLE_CONSISTENCY checks."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.oracle_values) == 1
        assert bundle.oracle_values["src-chainlink"]["value"] == 1.02
        assert bundle.oracle_values["src-chainlink"]["is_provisional"] is False
        assert bundle.oracle_source_ids == ["src-chainlink"]

    def test_execution_summary_projection(self):
        """Execution summary counts and checks projected from result."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        summary = bundle.execution_summary
        assert summary.executed_count == 3  # 2 PASSED + 1 FAILED
        assert summary.passed_count == 2    # tmpl-eq-001 + oracle
        assert summary.failed_count == 1    # tmpl-eq-002
        assert summary.has_critical_failures is True
        assert len(summary.checks) == 3
        assert len(bundle.provenance_refs) == 3


# ═══════════════════════════════════════════════════════════════════
# Sprint 1 — CORONA Bundle Builder (4 tests)
# ═══════════════════════════════════════════════════════════════════

class TestCoronaBundleBuilder:
    """Verify CORONA execution → bundle mapping."""

    def test_identity_mapping(self):
        """Builder extracts slug from result, version from fixture."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert bundle.construct_slug == "corona"
        assert bundle.construct_version == "2.1.0"
        assert bundle.certificate_id is None

    def test_settlement_outcomes_all_passed(self):
        """CORONA has 1 settlement check, all PASSED → SETTLED."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.settlement_outcomes) == 1
        assert bundle.settlement_outcomes["tmpl-pandemic-001"]["resolution"] == "CORRECT"
        assert bundle.settlement_state == "SETTLED"

    def test_oracle_values_corona(self):
        """CORONA oracle values extracted correctly."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.oracle_values) == 1
        assert bundle.oracle_values["src-who"]["value"] == 0.85
        assert bundle.oracle_source_ids == ["src-who"]

    def test_confidence_signals_from_calibration(self):
        """Confidence signals extracted from CALIBRATION_VALIDITY evidence."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert bundle.confidence_signals["brier_score"] == 0.18
        assert bundle.confidence_signals["calibration_valid"] is True

        # TREMOR has no calibration → empty signals
        tremor_result = make_tremor_execution_result()
        tremor_fixture = make_tremor_fixture_input()
        tremor_bundle = build_comparison_bundle(tremor_result, tremor_fixture)
        assert tremor_bundle.confidence_signals == {}
