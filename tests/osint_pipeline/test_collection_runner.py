"""Tests for CollectionRunner (Stage 1 Orchestrator).

Tests: parallel execution, timeout budget, gap reporting,
required_source_ids filtering, allow_gaps_for, run_sequential mode.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.engine.collection_runner import CollectionRunner
from osint_pipeline.models.evidence import (
    CollectionResult,
    CollectionStatus,
    GapKind,
)
from tests.osint_pipeline.conftest import make_bundle


# ---------------------------------------------------------------------------
# Stub collectors for testing
# ---------------------------------------------------------------------------

class FastCollector(BaseCollector):
    """Collector that succeeds instantly."""

    def __init__(self, sid: str, group: str = "official_gov", **kwargs):
        super().__init__()
        self._sid = sid
        self._group = group

    @property
    def source_id(self) -> str:
        return self._sid

    @property
    def source_group(self) -> str:
        return self._group

    @property
    def independence_upstream_id(self) -> str:
        return f"upstream_{self._sid}"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(self, query_context):
        return "GET", "http://test", {}, None

    def extract(self, raw_body, status_code, query_context):
        return {"data": "test"}, 1.0

    def collect(self, query_context, theatre_id=None, registry_source=None):
        bundle = make_bundle(
            source_id=self._sid,
            upstream_id=f"upstream_{self._sid}",
            source_group=self._group,
        )
        return CollectionResult(
            source_id=self._sid,
            status=CollectionStatus.SUCCESS,
            bundle=bundle,
            duration_ms=10,
        )


class FailingCollector(FastCollector):
    """Collector that always fails."""

    def collect(self, query_context, theatre_id=None, registry_source=None):
        return CollectionResult(
            source_id=self.source_id,
            status=CollectionStatus.SOURCE_ERROR,
            error_message="Test error",
            duration_ms=5,
        )


class SlowCollector(FastCollector):
    """Collector that sleeps (for timeout tests)."""

    def __init__(self, sid: str, sleep_seconds: float = 10.0, **kwargs):
        super().__init__(sid, **kwargs)
        self._sleep = sleep_seconds

    def collect(self, query_context, theatre_id=None, registry_source=None):
        time.sleep(self._sleep)
        return super().collect(query_context, theatre_id, registry_source)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCollectionRunnerParallel:
    """Test parallel execution."""

    def test_all_succeed(self):
        collectors = [FastCollector("src_a"), FastCollector("src_b", "market_data")]
        runner = CollectionRunner(collectors, max_workers=2)
        summary = runner.run({"q": "test"}, "theatre_1")

        assert summary.total_sources_attempted == 2
        assert summary.total_sources_succeeded == 2
        assert summary.total_sources_failed == 0
        assert len(summary.bundles) == 2
        assert len(summary.gaps) == 0
        assert summary.coverage_ratio == 1.0

    def test_one_fails(self):
        collectors = [FastCollector("src_a"), FailingCollector("src_b")]
        runner = CollectionRunner(collectors, max_workers=2)
        summary = runner.run({"q": "test"})

        assert summary.total_sources_succeeded == 1
        assert summary.total_sources_failed == 1
        assert len(summary.bundles) == 1
        assert len(summary.gaps) == 1
        assert summary.gaps[0].source_id == "src_b"


class TestCollectionRunnerTimeout:
    """Test timeout budget handling (Concern 6)."""

    def test_timeout_produces_gap_reports(self):
        """Slow collector times out and produces a gap report with INTELLIGENCE_GAP."""
        collectors = [
            FastCollector("fast_a"),
            FastCollector("fast_b"),
            SlowCollector("slow_c", sleep_seconds=10.0),
        ]
        runner = CollectionRunner(collectors, max_workers=3, timeout_budget_seconds=0.5)
        summary = runner.run({"q": "test"})

        # Two fast should succeed, one slow should timeout
        assert summary.total_sources_succeeded == 2
        assert summary.total_sources_failed == 1
        assert len(summary.gaps) == 1

        gap = summary.gaps[0]
        assert gap.source_id == "slow_c"
        assert gap.reason == CollectionStatus.TIMEOUT
        assert gap.gap_kind == GapKind.INTELLIGENCE_GAP
        assert "budget exhausted" in gap.error_detail

    def test_timeout_gap_has_correct_jurisdiction(self):
        collectors = [SlowCollector("slow_src", sleep_seconds=10.0)]
        runner = CollectionRunner(collectors, max_workers=1, timeout_budget_seconds=0.2)
        summary = runner.run({"q": "test"})

        assert len(summary.gaps) == 1
        assert summary.gaps[0].jurisdiction == "GB"


class TestCollectionRunnerFiltering:
    """Test required_source_ids filtering."""

    def test_required_source_ids_filters(self):
        collectors = [
            FastCollector("src_a"),
            FastCollector("src_b"),
            FastCollector("src_c"),
        ]
        runner = CollectionRunner(collectors, max_workers=3)
        summary = runner.run({"q": "test"}, required_source_ids=["src_a", "src_c"])

        assert summary.total_sources_succeeded == 2
        source_ids = {b.source_id for b in summary.bundles}
        assert source_ids == {"src_a", "src_c"}

    def test_missing_required_source_produces_gap(self):
        collectors = [FastCollector("src_a")]
        runner = CollectionRunner(collectors, max_workers=1)
        summary = runner.run(
            {"q": "test"}, required_source_ids=["src_a", "missing_src"]
        )

        assert summary.total_sources_succeeded == 1
        gaps = [g for g in summary.gaps if g.source_id == "missing_src"]
        assert len(gaps) == 1
        assert "No configured collector" in gaps[0].error_detail


class TestCollectionRunnerAllowGaps:
    """Test allow_gaps_for propagation."""

    def test_allow_gaps_propagated(self):
        collectors = [FailingCollector("src_a"), FastCollector("src_b")]
        runner = CollectionRunner(collectors, max_workers=2)
        summary = runner.run(
            {"q": "test"}, allow_gaps_for=["src_a"]
        )

        gap = [g for g in summary.gaps if g.source_id == "src_a"][0]
        assert gap.allow_gap is True

    def test_no_allow_gap_by_default(self):
        collectors = [FailingCollector("src_a")]
        runner = CollectionRunner(collectors, max_workers=1)
        summary = runner.run({"q": "test"})

        assert summary.gaps[0].allow_gap is False


class TestCollectionRunnerSequential:
    """Test run_sequential mode."""

    def test_sequential_all_succeed(self):
        collectors = [FastCollector("src_a"), FastCollector("src_b")]
        runner = CollectionRunner(collectors, max_workers=2)
        summary = runner.run_sequential({"q": "test"})

        assert summary.total_sources_succeeded == 2
        assert len(summary.bundles) == 2

    def test_sequential_with_failure(self):
        collectors = [FastCollector("src_a"), FailingCollector("src_b")]
        runner = CollectionRunner(collectors, max_workers=2)
        summary = runner.run_sequential({"q": "test"})

        assert summary.total_sources_succeeded == 1
        assert summary.total_sources_failed == 1


class TestCollectionRunnerCloseAll:
    """Test close_all."""

    def test_close_all(self):
        collectors = [FastCollector("src_a"), FastCollector("src_b")]
        runner = CollectionRunner(collectors, max_workers=2)
        # Should not raise
        runner.close_all()


class TestCollectionRunnerReturns:
    """Test OracleCollectionSummary structure."""

    def test_returns_summary(self):
        collectors = [FastCollector("src_a")]
        runner = CollectionRunner(collectors, max_workers=1)
        summary = runner.run({"q": "test"}, theatre_id="t1")

        assert summary.theatre_id == "t1"
        assert summary.query_window_start is not None
        assert summary.query_window_end is not None
        assert summary.query_window_end >= summary.query_window_start

    def test_empty_collectors(self):
        runner = CollectionRunner([], max_workers=1)
        summary = runner.run({"q": "test"})
        assert summary.total_sources_attempted == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
