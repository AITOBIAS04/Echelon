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
