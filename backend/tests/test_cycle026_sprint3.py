"""Cycle 026 Sprint 3 — Integration + Remaining Collectors + Path 2 Regression tests.

Tests (8 total):
OpenAQ: success, no measurements
Calendarific: success, non-holiday date
Integration: CollectionRunner runs all 14 collectors, collector_map count
Path 2 regression: no Cycle-026 files import worldmonitor path-2 internals
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.osint.collectors.openaq import OpenAQCollector
from backend.osint.collectors.calendarific import CalendarificCollector
from backend.osint.collectors.collector_map import build_collector_map
from backend.osint.engine.collection_runner import CollectionPlan, CollectionRunner


# ── Mock Responses ──

OPENAQ_SUCCESS = json.dumps({
    "results": [
        {
            "location": "US Embassy",
            "parameter": "pm25",
            "value": 12.5,
            "coordinates": {"latitude": 38.9, "longitude": -77.0},
        },
        {
            "location": "Downtown",
            "parameter": "pm25",
            "value": 18.3,
            "coordinates": {"latitude": 38.91, "longitude": -77.01},
        },
    ]
}).encode()

OPENAQ_EMPTY = json.dumps({
    "results": []
}).encode()

CALENDARIFIC_SUCCESS = json.dumps({
    "response": {
        "holidays": [
            {"name": "New Year's Day", "date": {"iso": "2026-01-01"}},
            {"name": "Martin Luther King Jr. Day", "date": {"iso": "2026-01-19"}},
        ]
    }
}).encode()

CALENDARIFIC_NO_HOLIDAYS = json.dumps({
    "response": {
        "holidays": []
    }
}).encode()


# ── OpenAQ Tests ──

class TestOpenAQCollector:
    """Test OpenAQCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """OpenAQ success: PM2.5 measurements returns valid CollectionResult."""
        collector = OpenAQCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENAQ_SUCCESS
            result = await collector._fetch(
                {"country": "US", "parameter": "pm25"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "openaq_api"
        # Average of 12.5 and 18.3 = 15.4
        assert abs(result.bundle.normalised_event.measure.value - 15.4) < 0.01
        # Geo from first measurement
        assert abs(result.bundle.normalised_event.geo.lat - 38.9) < 0.01

    @pytest.mark.asyncio
    async def test_no_measurements(self):
        """OpenAQ empty: no results returns success with 0.0 value."""
        collector = OpenAQCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENAQ_EMPTY
            result = await collector._fetch(
                {"country": "US", "parameter": "pm25"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 0.0


# ── Calendarific Tests ──

class TestCalendarificCollector:
    """Test CalendarificCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Calendarific success: US holidays returns valid CollectionResult."""
        collector = CalendarificCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = CALENDARIFIC_SUCCESS
            result = await collector._fetch(
                {"country": "US", "year": "2026"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "calendarific_api"
        assert result.bundle.normalised_event.measure.value == 2.0  # 2 holidays
        assert result.bundle.resolution_role == "counter_signal"

    @pytest.mark.asyncio
    async def test_non_holiday_date(self):
        """Calendarific non-holiday: empty holidays still returns success (0 is valid)."""
        collector = CalendarificCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = CALENDARIFIC_NO_HOLIDAYS
            result = await collector._fetch(
                {"country": "US", "year": "2026", "month": "3", "day": "17"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 0.0


# ── Integration Tests ──

class TestCollectorMapIntegration:
    """Integration: collector_map and CollectionRunner."""

    def test_collector_map_has_14_entries(self):
        """Collector map returns all 14 source_ids."""
        cmap = build_collector_map()
        assert len(cmap) == 14
        expected_ids = {
            "worldmonitor_cii", "worldmonitor_finance", "worldmonitor_maritime",
            "companies_house_api",
            "fred_api", "alpha_vantage_api", "opencorporates_api", "etherscan_api",
            "coingecko_api", "opensky_api",
            "usgs_earthquake_api", "carbon_intensity_api", "openaq_api",
            "calendarific_api",
        }
        assert set(cmap.keys()) == expected_ids

    @pytest.mark.asyncio
    async def test_collection_runner_executes_all(self):
        """CollectionRunner.collect() runs all 14 collectors concurrently.

        All collectors have no API keys, so they should return success=False
        with appropriate error messages (not raise).
        """
        cmap = build_collector_map()
        runner = CollectionRunner(collectors=cmap)
        plan = CollectionPlan(
            theatre_id="theatre-integration",
            sources=list(cmap.keys()),
            evaluation_window=(__import__("datetime").datetime(2026, 3, 17),
                               __import__("datetime").datetime(2026, 3, 17)),
            timeout_s=5.0,
        )
        results = await runner.collect(plan)
        # All 14 collectors should return results (not raise)
        assert len(results) == 14
        # Each result is a CollectionResult with a source_id
        source_ids = {r.source_id for r in results}
        assert len(source_ids) == 14


# ── Path 2 Regression ──

class TestPath2Regression:
    """Verify Cycle-026 files don't import Path-2 internals."""

    def test_no_path2_imports_in_batch1_collectors(self):
        """Cycle-026 collector files must not import worldmonitor internals."""
        import importlib
        import inspect

        batch1_modules = [
            "backend.osint.collectors.fred",
            "backend.osint.collectors.alpha_vantage",
            "backend.osint.collectors.opencorporates",
            "backend.osint.collectors.etherscan",
            "backend.osint.collectors.coingecko",
            "backend.osint.collectors.opensky",
            "backend.osint.collectors.usgs_earthquake",
            "backend.osint.collectors.carbon_intensity",
            "backend.osint.collectors.openaq",
            "backend.osint.collectors.calendarific",
        ]

        for mod_name in batch1_modules:
            mod = importlib.import_module(mod_name)
            source = inspect.getsource(mod)
            assert "from backend.osint.collectors.worldmonitor" not in source, (
                f"{mod_name} imports worldmonitor internals"
            )
            assert "from backend.osint.engine" not in source, (
                f"{mod_name} imports engine internals"
            )
