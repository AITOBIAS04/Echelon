"""Tests for CorroborationEngine (Stage 2).

Tests: dedup by upstream, shared upstream exclusion, time window
enforcement, distinct group counting, pass/fail for minimum, evaluate_all.
"""

from __future__ import annotations

import pytest

from osint_pipeline.engine.corroboration import CorroborationEngine
from osint_pipeline.models.evidence import OracleCollectionSummary
from tests.osint_pipeline.conftest import make_bundle, make_receipt


def _bundle(
    source_id: str,
    upstream_id: str,
    source_group: str,
    timestamp_ms: int = 1000,
    role: str = "secondary_corroboration",
    **kwargs,
):
    """Build a bundle with a specific timestamp."""
    receipt = make_receipt()
    receipt_data = receipt.model_dump()
    receipt_data["timestamp_ms"] = timestamp_ms
    from osint_pipeline.models.evidence import HTTPTranscriptReceipt
    new_receipt = HTTPTranscriptReceipt(**receipt_data)
    return make_bundle(
        source_id=source_id,
        upstream_id=upstream_id,
        source_group=source_group,
        receipt=new_receipt,
        resolution_role=role,
        **kwargs,
    )


class TestCorroborationDedup:
    """Test independence deduplication."""

    def test_dedup_by_upstream_id(self):
        """Two bundles sharing upstream_id count as one."""
        engine = CorroborationEngine(corroboration_minimum=1)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b1 = _bundle("src_1", "upstream_B", "market_data")
        b2 = _bundle("src_2", "upstream_B", "regulatory")

        result = engine.evaluate(primary, [primary, b1, b2])

        # src_2 should be excluded by dedup (same upstream as src_1)
        assert "src_2" in result.excluded_by_dedup

    def test_exclude_shared_upstream_with_primary(self):
        """Candidate sharing upstream with primary is excluded."""
        engine = CorroborationEngine(corroboration_minimum=1)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b1 = _bundle("src_1", "upstream_A", "market_data")  # Same upstream as primary
        b2 = _bundle("src_2", "upstream_C", "regulatory")

        result = engine.evaluate(primary, [primary, b1, b2])

        assert "src_1" in result.excluded_by_dedup
        assert result.distinct_corroborating_groups == 1


class TestCorroborationTimeWindow:
    """Test time window enforcement."""

    def test_within_window_passes(self):
        engine = CorroborationEngine(
            corroboration_minimum=1, corroboration_window_seconds=3600
        )
        primary = _bundle(
            "primary", "upstream_A", "official_gov",
            timestamp_ms=1000000, role="primary_evidence"
        )
        b1 = _bundle(
            "src_1", "upstream_B", "market_data",
            timestamp_ms=1500000  # 500s delta, within 3600s window
        )

        result = engine.evaluate(primary, [primary, b1])
        assert result.distinct_corroborating_groups == 1
        assert len(result.outside_window) == 0

    def test_outside_window_excluded(self):
        engine = CorroborationEngine(
            corroboration_minimum=1, corroboration_window_seconds=1
        )
        primary = _bundle(
            "primary", "upstream_A", "official_gov",
            timestamp_ms=1000, role="primary_evidence"
        )
        b1 = _bundle(
            "src_1", "upstream_B", "market_data",
            timestamp_ms=5000000  # Way outside 1s window (1000ms)
        )

        result = engine.evaluate(primary, [primary, b1])
        assert result.distinct_corroborating_groups == 0
        assert "src_1" in result.outside_window


class TestCorroborationGroupCounting:
    """Test distinct group counting."""

    def test_same_group_as_primary_not_counted(self):
        """Candidates in the same source_group as primary don't count."""
        engine = CorroborationEngine(corroboration_minimum=1)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b1 = _bundle("src_1", "upstream_B", "official_gov")  # Same group as primary

        result = engine.evaluate(primary, [primary, b1])
        assert result.distinct_corroborating_groups == 0
        assert not result.passed

    def test_different_groups_counted(self):
        engine = CorroborationEngine(corroboration_minimum=2)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b1 = _bundle("src_1", "upstream_B", "market_data")
        b2 = _bundle("src_2", "upstream_C", "regulatory")

        result = engine.evaluate(primary, [primary, b1, b2])
        assert result.distinct_corroborating_groups == 2
        assert result.passed

    def test_minimum_not_met(self):
        engine = CorroborationEngine(corroboration_minimum=3)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b1 = _bundle("src_1", "upstream_B", "market_data")

        result = engine.evaluate(primary, [primary, b1])
        assert result.distinct_corroborating_groups == 1
        assert not result.passed


class TestCorroborationRoleFilter:
    """Test resolution_role filtering."""

    def test_only_eligible_roles_included(self):
        """Only secondary_corroboration and primary_evidence count."""
        engine = CorroborationEngine(corroboration_minimum=1)
        primary = _bundle("primary", "upstream_A", "official_gov", role="primary_evidence")
        b_ok = _bundle("src_1", "upstream_B", "market_data", role="secondary_corroboration")
        b_triage = _bundle("src_2", "upstream_C", "regulatory", role="triage_only")
        b_counter = _bundle("src_3", "upstream_D", "news", role="counter_signal")

        result = engine.evaluate(primary, [primary, b_ok, b_triage, b_counter])
        assert result.distinct_corroborating_groups == 1
        assert "src_1" in result.corroborating_sources


class TestCorroborationEvaluateAll:
    """Test evaluate_all across a collection."""

    def test_evaluate_all(self):
        engine = CorroborationEngine(corroboration_minimum=1)
        p1 = _bundle("primary_1", "up_A", "official_gov", role="primary_evidence")
        p2 = _bundle("primary_2", "up_B", "market_data", role="primary_evidence")
        b1 = _bundle("support_1", "up_C", "regulatory")

        collection = OracleCollectionSummary(
            bundles=[p1, p2, b1],
            total_sources_attempted=3,
            total_sources_succeeded=3,
        )
        results = engine.evaluate_all(collection)
        assert len(results) == 2
        assert results[0].primary_source_id == "primary_1"
        assert results[1].primary_source_id == "primary_2"

    def test_evaluate_all_no_primaries(self):
        engine = CorroborationEngine()
        collection = OracleCollectionSummary(
            bundles=[_bundle("src_1", "up_A", "market_data", role="secondary_corroboration")],
            total_sources_attempted=1,
            total_sources_succeeded=1,
        )
        results = engine.evaluate_all(collection)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
