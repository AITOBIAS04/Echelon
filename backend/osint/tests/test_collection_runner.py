"""Collection runner tests — concurrent execution, timeout, partial failure.

Tests verify that CollectionRunner correctly orchestrates concurrent
collector execution with per-collector timeout, handles partial failures,
and assembles results from multiple collectors.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend.osint.collectors.worldmonitor import WorldMonitorCollector, WorldMonitorConfig
from backend.osint.engine.collection_runner import CollectionPlan, CollectionRunner
from backend.osint.models.evidence import CollectionResult, GeoPoint, WMDomain


def _make_success_result(source_id: str) -> CollectionResult:
    """Create a successful CollectionResult for testing."""
    return CollectionResult(
        source_id=source_id,
        bundle=None,  # Bundle details not needed for runner tests
        raw_payload=b'{"test": true}',
        fetch_duration_ms=50.0,
        success=True,
        retrieved_at=datetime.now(timezone.utc),
    )


def _make_failure_result(source_id: str, error: str) -> CollectionResult:
    """Create a failed CollectionResult for testing."""
    return CollectionResult(
        source_id=source_id,
        bundle=None,
        raw_payload=b"",
        fetch_duration_ms=0.0,
        success=False,
        error=error,
        retrieved_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def fast_config() -> WorldMonitorConfig:
    """Config with no retries for fast tests."""
    return WorldMonitorConfig(
        base_url="http://mock:8080",
        timeout_s=5.0,
        version="v0.1.0",
        retry_count=0,
        retry_delay_s=0.0,
    )


@pytest.fixture
def three_collectors(fast_config: WorldMonitorConfig) -> dict[str, WorldMonitorCollector]:
    """Three WM collectors keyed by source_id."""
    return {
        "worldmonitor_cii": WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config),
        "worldmonitor_finance": WorldMonitorCollector(WMDomain.MARKET, fast_config),
        "worldmonitor_maritime": WorldMonitorCollector(WMDomain.MARITIME, fast_config),
    }


@pytest.fixture
def test_plan() -> CollectionPlan:
    """Test collection plan with all three WM sources."""
    now = datetime.now(timezone.utc)
    return CollectionPlan(
        theatre_id="theatre_test_001",
        sources=["worldmonitor_cii", "worldmonitor_finance", "worldmonitor_maritime"],
        evaluation_window=(now, now),
        timeout_s=5.0,
    )


class TestCollectionRunnerConcurrency:
    """Concurrent collector execution via asyncio.gather."""

    @pytest.mark.asyncio
    async def test_all_three_collectors_run(
        self, three_collectors: dict, test_plan: CollectionPlan
    ) -> None:
        """All three collectors execute and return results."""
        runner = CollectionRunner(three_collectors)

        # Mock all three collectors to return success
        for sid, collector in three_collectors.items():
            collector.fetch = AsyncMock(return_value=_make_success_result(sid))

        results = await runner.collect(test_plan)

        assert len(results) == 3
        assert all(r.success for r in results)
        source_ids = {r.source_id for r in results}
        assert source_ids == {"worldmonitor_cii", "worldmonitor_finance", "worldmonitor_maritime"}

    @pytest.mark.asyncio
    async def test_partial_failure(
        self, three_collectors: dict, test_plan: CollectionPlan
    ) -> None:
        """1 of 3 fails, other 2 succeed — all 3 results returned."""
        runner = CollectionRunner(three_collectors)

        three_collectors["worldmonitor_cii"].fetch = AsyncMock(
            return_value=_make_success_result("worldmonitor_cii")
        )
        three_collectors["worldmonitor_finance"].fetch = AsyncMock(
            return_value=_make_failure_result("worldmonitor_finance", "Connection refused")
        )
        three_collectors["worldmonitor_maritime"].fetch = AsyncMock(
            return_value=_make_success_result("worldmonitor_maritime")
        )

        results = await runner.collect(test_plan)

        assert len(results) == 3
        success_count = sum(1 for r in results if r.success)
        failure_count = sum(1 for r in results if not r.success)
        assert success_count == 2
        assert failure_count == 1

    @pytest.mark.asyncio
    async def test_all_fail(
        self, three_collectors: dict, test_plan: CollectionPlan
    ) -> None:
        """All 3 fail — all 3 results returned with success=False."""
        runner = CollectionRunner(three_collectors)

        for sid, collector in three_collectors.items():
            collector.fetch = AsyncMock(
                return_value=_make_failure_result(sid, "Connection refused")
            )

        results = await runner.collect(test_plan)

        assert len(results) == 3
        assert all(not r.success for r in results)


class TestCollectionRunnerTimeout:
    """Per-collector timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_produces_failure_result(
        self, three_collectors: dict
    ) -> None:
        """Timeout on one collector produces failure result, others succeed."""
        plan = CollectionPlan(
            theatre_id="theatre_test",
            sources=["worldmonitor_cii", "worldmonitor_finance"],
            evaluation_window=(datetime.now(timezone.utc), datetime.now(timezone.utc)),
            timeout_s=0.1,  # Very short
        )
        runner = CollectionRunner(three_collectors)

        # CII collector times out
        async def _slow_fetch(request, theatre_id):
            await asyncio.sleep(10.0)
            return _make_success_result("worldmonitor_cii")

        three_collectors["worldmonitor_cii"].fetch = _slow_fetch
        three_collectors["worldmonitor_finance"].fetch = AsyncMock(
            return_value=_make_success_result("worldmonitor_finance")
        )

        results = await runner.collect(plan)

        assert len(results) == 2
        cii_result = next(r for r in results if r.source_id == "worldmonitor_cii")
        fin_result = next(r for r in results if r.source_id == "worldmonitor_finance")
        assert cii_result.success is False
        assert "Timeout" in cii_result.error
        assert fin_result.success is True


class TestCollectionRunnerMissingCollector:
    """Missing collector handling."""

    @pytest.mark.asyncio
    async def test_missing_collector_produces_failure(self) -> None:
        """Unknown source_id produces failure result, not exception."""
        runner = CollectionRunner({})  # No collectors registered
        plan = CollectionPlan(
            theatre_id="theatre_test",
            sources=["nonexistent_source"],
            evaluation_window=(datetime.now(timezone.utc), datetime.now(timezone.utc)),
            timeout_s=5.0,
        )

        results = await runner.collect(plan)

        assert len(results) == 1
        assert results[0].success is False
        assert "No collector registered" in results[0].error
        assert results[0].source_id == "nonexistent_source"


class TestCollectionRunnerBuildPlan:
    """Collection plan derivation from oracle_config."""

    def test_build_plan_from_config(self, three_collectors: dict) -> None:
        """build_plan extracts sources, window, geo from oracle_config."""
        runner = CollectionRunner(three_collectors)
        oracle_config = {
            "sources": ["worldmonitor_cii", "worldmonitor_finance"],
            "evaluation_window": {
                "start": "2026-03-03T00:00:00+00:00",
                "end": "2026-03-03T01:00:00+00:00",
            },
            "geo": {"lat": 32.4, "lon": 53.7, "radius_m": 500000},
            "timeout_s": 15.0,
        }

        plan = runner.build_plan(oracle_config, "theatre_iran_001")

        assert plan.theatre_id == "theatre_iran_001"
        assert plan.sources == ["worldmonitor_cii", "worldmonitor_finance"]
        assert plan.geo is not None
        assert plan.geo.lat == 32.4
        assert plan.timeout_s == 15.0

    def test_build_plan_defaults(self, three_collectors: dict) -> None:
        """build_plan uses defaults when oracle_config is minimal."""
        runner = CollectionRunner(three_collectors)
        plan = runner.build_plan({}, "theatre_test")

        # Defaults to all registered collectors
        assert set(plan.sources) == {"worldmonitor_cii", "worldmonitor_finance", "worldmonitor_maritime"}
        assert plan.geo is None
        assert plan.timeout_s == 30.0
