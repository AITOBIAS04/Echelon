"""Tests for Scorer (Stage 3).

Tests: per-criterion scores, composite weighted average, bundle hash
determinism, coverage percentage, OracleOutput assembly.
"""

from __future__ import annotations

import pytest

from osint_pipeline.engine.scorer import DEFAULT_WEIGHTS, Scorer
from osint_pipeline.models.evidence import (
    CollectionStatus,
    GapReport,
    OracleCollectionSummary,
    ReceiptMode,
)
from osint_pipeline.models.oracle_output import (
    CorroborationResult,
    CounterSignalResult,
    OracleOutput,
)
from tests.osint_pipeline.conftest import make_bundle


def _make_collection(n_success: int = 3, n_fail: int = 0) -> OracleCollectionSummary:
    """Build a test collection summary."""
    bundles = [
        make_bundle(
            source_id=f"src_{i}",
            upstream_id=f"up_{i}",
            source_group=["official_gov", "market_data", "regulatory"][i % 3],
            confidence=0.9,
            resolution_role="primary_evidence",
        )
        for i in range(n_success)
    ]
    gaps = [
        GapReport(
            source_id=f"gap_{i}",
            source_group="unknown",
            jurisdiction="GB",
            reason=CollectionStatus.TIMEOUT,
        )
        for i in range(n_fail)
    ]
    return OracleCollectionSummary(
        theatre_id="test_theatre",
        bundles=bundles,
        gaps=gaps,
        total_sources_attempted=n_success + n_fail,
        total_sources_succeeded=n_success,
        total_sources_failed=n_fail,
    )


def _make_corr(passed: bool = True) -> CorroborationResult:
    return CorroborationResult(
        claim_id="claim_0",
        primary_source_id="src_0",
        primary_source_group="official_gov",
        distinct_corroborating_groups=2 if passed else 0,
        corroboration_minimum=2,
    )


def _make_cs(
    cs_class: str, checked: bool = True, found: bool = False, allow_gap: bool = False
) -> CounterSignalResult:
    return CounterSignalResult(
        counter_signal_class=cs_class,
        source_id=f"cs_{cs_class}",
        checked=checked,
        signal_found=found,
        allow_gap=allow_gap,
    )


class TestScorerCriteria:
    """Test individual criterion scores."""

    def test_source_coverage_score(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2, n_fail=1)
        output = scorer.score(collection, [], [])

        cov = next(c for c in output.criterion_scores if c.criterion_id == "source_coverage")
        assert abs(cov.score - 2 / 3) < 0.001
        assert cov.passed is True

    def test_receipt_validity_all_http_transcript(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        output = scorer.score(collection, [], [])

        rv = next(c for c in output.criterion_scores if c.criterion_id == "receipt_validity")
        assert rv.score == 1.0
        assert rv.passed is True

    def test_corroboration_met_all_passed(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        corr = [_make_corr(True)]
        output = scorer.score(collection, corr, [])

        cm = next(c for c in output.criterion_scores if c.criterion_id == "corroboration_met")
        assert cm.score == 1.0
        assert cm.passed is True

    def test_corroboration_met_some_failed(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        corr = [_make_corr(True), _make_corr(False)]
        output = scorer.score(collection, corr, [])

        cm = next(c for c in output.criterion_scores if c.criterion_id == "corroboration_met")
        assert abs(cm.score - 0.5) < 0.001
        assert cm.passed is False

    def test_counter_signal_clear(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        cs = [
            _make_cs("calendar_holiday", checked=True, found=False),
            _make_cs("force_majeure", checked=True, found=False),
        ]
        output = scorer.score(collection, [], cs)

        csc = next(c for c in output.criterion_scores if c.criterion_id == "counter_signal_clear")
        assert csc.score == 1.0

    def test_counter_signal_clear_with_found(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        cs = [
            _make_cs("calendar_holiday", checked=True, found=False),
            _make_cs("force_majeure", checked=True, found=True),  # fails
        ]
        output = scorer.score(collection, [], cs)

        csc = next(c for c in output.criterion_scores if c.criterion_id == "counter_signal_clear")
        assert abs(csc.score - 0.5) < 0.001

    def test_confidence_weighted(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        output = scorer.score(collection, [], [])

        cw = next(c for c in output.criterion_scores if c.criterion_id == "confidence_weighted")
        assert abs(cw.score - 0.9) < 0.001  # All bundles have confidence 0.9


class TestScorerComposite:
    """Test weighted composite score."""

    def test_composite_in_range(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        corr = [_make_corr(True)]
        cs = [_make_cs("calendar_holiday", checked=True, found=False)]
        output = scorer.score(collection, corr, cs)

        assert 0.0 <= output.composite_score <= 1.0

    def test_perfect_score(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3, n_fail=0)
        corr = [_make_corr(True)]
        cs = [_make_cs("calendar_holiday", checked=True, found=False)]
        output = scorer.score(collection, corr, cs)

        # All criteria should score 1.0 or ~0.9 (confidence)
        assert output.composite_score > 0.8

    def test_custom_weights(self):
        scorer = Scorer(weights={
            "source_coverage": 1.0,
            "receipt_validity": 0.0,
            "corroboration_met": 0.0,
            "counter_signal_clear": 0.0,
            "confidence_weighted": 0.0,
        })
        collection = _make_collection(n_success=2, n_fail=1)
        output = scorer.score(collection, [], [])

        # Composite should equal source_coverage score (2/3 * 1.0)
        assert abs(output.composite_score - 2 / 3) < 0.001


class TestScorerBundleHash:
    """Test bundle hash determinism."""

    def test_bundle_hash_deterministic(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3)
        output_1 = scorer.score(collection, [], [])
        output_2 = scorer.score(collection, [], [])

        assert output_1.bundle_hash == output_2.bundle_hash

    def test_bundle_hash_is_hex(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2)
        output = scorer.score(collection, [], [])

        assert len(output.bundle_hash) == 64
        assert all(c in "0123456789abcdef" for c in output.bundle_hash)

    def test_different_bundles_different_hash(self):
        scorer = Scorer()
        c1 = _make_collection(n_success=2)
        c2 = _make_collection(n_success=3)
        o1 = scorer.score(c1, [], [])
        o2 = scorer.score(c2, [], [])

        assert o1.bundle_hash != o2.bundle_hash

    def test_empty_bundles_hash(self):
        scorer = Scorer()
        collection = _make_collection(n_success=0)
        output = scorer.score(collection, [], [])

        assert len(output.bundle_hash) == 64


class TestScorerCoveragePercentage:
    """Test coverage percentage."""

    def test_full_coverage(self):
        scorer = Scorer()
        collection = _make_collection(n_success=3, n_fail=0)
        output = scorer.score(collection, [], [])
        assert output.coverage_percentage == 100.0

    def test_partial_coverage(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2, n_fail=1)
        output = scorer.score(collection, [], [])
        assert abs(output.coverage_percentage - 200 / 3) < 0.1

    def test_zero_coverage(self):
        scorer = Scorer()
        collection = _make_collection(n_success=0, n_fail=3)
        output = scorer.score(collection, [], [])
        assert output.coverage_percentage == 0.0


class TestScorerOracleOutput:
    """Test OracleOutput assembly."""

    def test_oracle_output_structure(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2)
        corr = [_make_corr(True)]
        cs = [_make_cs("calendar_holiday")]
        output = scorer.score(collection, corr, cs, theatre_id="t1")

        assert isinstance(output, OracleOutput)
        assert output.theatre_id == "t1"
        assert output.oracle_id  # Non-empty UUID
        assert output.evaluated_at is not None
        assert len(output.criterion_scores) == 5
        assert output.collection is collection
        assert output.corroboration_results == corr
        assert output.counter_signal_results == cs

    def test_counter_signal_summary(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2)
        cs = [
            _make_cs("a", checked=True, found=False),
            _make_cs("b", checked=True, found=True),
            _make_cs("c", checked=False),
        ]
        output = scorer.score(collection, [], cs)

        assert output.counter_signals_checked == 2
        assert output.counter_signals_found == 1

    def test_gap_report_populated(self):
        scorer = Scorer()
        collection = _make_collection(n_success=2, n_fail=1)
        output = scorer.score(collection, [], [])

        assert len(output.gap_report) == 1
        assert output.gap_report[0].source_id == "gap_0"


class TestSettlementSafe:
    """E2: Settlement eligibility policy guard."""

    def test_secondary_only_not_settlement_safe(self):
        """Collection with only secondary_corroboration -> settlement_safe=False."""
        bundles = [
            make_bundle(
                source_id="sec_src",
                upstream_id="sec_up",
                resolution_role="secondary_corroboration",
            ),
        ]
        collection = OracleCollectionSummary(
            theatre_id="test",
            bundles=bundles,
            gaps=[],
            total_sources_attempted=1,
            total_sources_succeeded=1,
            total_sources_failed=0,
        )
        scorer = Scorer()
        output = scorer.score(collection, [], [])
        assert output.settlement_safe is False

    def test_primary_and_secondary_is_settlement_safe(self):
        """Collection with primary_evidence + secondary -> settlement_safe=True."""
        bundles = [
            make_bundle(
                source_id="pri_src",
                upstream_id="pri_up",
                resolution_role="primary_evidence",
            ),
            make_bundle(
                source_id="sec_src",
                upstream_id="sec_up",
                resolution_role="secondary_corroboration",
            ),
        ]
        collection = OracleCollectionSummary(
            theatre_id="test",
            bundles=bundles,
            gaps=[],
            total_sources_attempted=2,
            total_sources_succeeded=2,
            total_sources_failed=0,
        )
        scorer = Scorer()
        output = scorer.score(collection, [], [])
        assert output.settlement_safe is True

    def test_settlement_safe_does_not_change_composite(self):
        """settlement_safe is advisory; composite score unchanged."""
        bundles = [
            make_bundle(
                source_id="sec_src",
                upstream_id="sec_up",
                resolution_role="secondary_corroboration",
            ),
        ]
        collection = OracleCollectionSummary(
            theatre_id="test",
            bundles=bundles,
            gaps=[],
            total_sources_attempted=1,
            total_sources_succeeded=1,
            total_sources_failed=0,
        )
        scorer = Scorer()
        output = scorer.score(collection, [], [])
        # Composite should still be > 0 even though settlement_safe=False
        assert output.composite_score > 0.0
        assert output.settlement_safe is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
