"""Cycle 026 Sprint 2 — Science + Environment + Aviation Collectors tests.

Tests (8 total):
CoinGecko: success, invalid coin_id
OpenSky: success, empty state vector
USGS Earthquake: success, no events in window
Carbon Intensity: success, degraded API (partial data)
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.osint.collectors.coingecko import CoinGeckoCollector
from backend.osint.collectors.opensky import OpenSkyCollector
from backend.osint.collectors.usgs_earthquake import USGSEarthquakeCollector
from backend.osint.collectors.carbon_intensity import CarbonIntensityCollector


# ── Mock Responses ──

COINGECKO_SUCCESS = json.dumps({
    "bitcoin": {"usd": 67500.42}
}).encode()

COINGECKO_INVALID = json.dumps({}).encode()

OPENSKY_SUCCESS = json.dumps({
    "time": 1710700000,
    "states": [
        ["abc123", "UAL123 ", "United States", 1710699990, 1710699990, -87.6, 41.9, 10000, False, 250, 180, 0, None, 10500, "1234", False, 0],
        ["def456", "DLH456 ", "Germany", 1710699991, 1710699991, 8.5, 50.1, 11000, False, 260, 90, 0, None, 11500, "5678", False, 0],
    ],
}).encode()

OPENSKY_EMPTY = json.dumps({
    "time": 1710700000,
    "states": None,
}).encode()

USGS_SUCCESS = json.dumps({
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"mag": 5.2, "place": "42km SSE of Hualien City, Taiwan"},
            "geometry": {"type": "Point", "coordinates": [121.65, 23.72, 10]},
        },
        {
            "type": "Feature",
            "properties": {"mag": 4.8, "place": "15km N of Tokyo, Japan"},
            "geometry": {"type": "Point", "coordinates": [139.7, 35.8, 25]},
        },
    ],
}).encode()

USGS_EMPTY = json.dumps({
    "type": "FeatureCollection",
    "features": [],
}).encode()

CARBON_INTENSITY_SUCCESS = json.dumps({
    "data": [
        {"from": "2026-03-17T00:00Z", "to": "2026-03-17T00:30Z", "intensity": {"forecast": 180, "actual": 175, "index": "moderate"}},
        {"from": "2026-03-17T00:30Z", "to": "2026-03-17T01:00Z", "intensity": {"forecast": 170, "actual": 168, "index": "moderate"}},
    ]
}).encode()

CARBON_INTENSITY_PARTIAL = json.dumps({
    "data": [
        {"from": "2026-03-17T00:00Z", "to": "2026-03-17T00:30Z", "intensity": {"forecast": 180, "index": "moderate"}},
    ]
}).encode()


# ── CoinGecko Tests ──

class TestCoinGeckoCollector:
    """Test CoinGeckoCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """CoinGecko success: bitcoin price returns valid CollectionResult."""
        collector = CoinGeckoCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = COINGECKO_SUCCESS
            result = await collector._fetch(
                {"coin_id": "bitcoin", "vs_currency": "usd"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "coingecko_api"
        assert result.bundle.normalised_event.measure.value == 67500.42

    @pytest.mark.asyncio
    async def test_invalid_coin_id(self):
        """CoinGecko invalid coin: empty response returns failure."""
        collector = CoinGeckoCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = COINGECKO_INVALID
            result = await collector._fetch(
                {"coin_id": "nonexistent_coin_xyz", "vs_currency": "usd"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "No data" in result.error


# ── OpenSky Tests ──

class TestOpenSkyCollector:
    """Test OpenSkyCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """OpenSky success: state vectors returns valid CollectionResult."""
        collector = OpenSkyCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENSKY_SUCCESS
            result = await collector._fetch(
                {"lamin": 40.0, "lamax": 50.0, "lomin": -90.0, "lomax": -80.0},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "opensky_api"
        assert result.bundle.normalised_event.measure.value == 2.0  # 2 aircraft

    @pytest.mark.asyncio
    async def test_empty_state_vector(self):
        """OpenSky empty box: null states still returns success (0 aircraft is valid)."""
        collector = OpenSkyCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENSKY_EMPTY
            result = await collector._fetch(
                {"lamin": 80.0, "lamax": 85.0, "lomin": 170.0, "lomax": 175.0},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 0.0


# ── USGS Earthquake Tests ──

class TestUSGSEarthquakeCollector:
    """Test USGSEarthquakeCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """USGS success: GeoJSON features returns valid CollectionResult with epicentre."""
        collector = USGSEarthquakeCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = USGS_SUCCESS
            result = await collector._fetch(
                {"starttime": "2026-03-16", "endtime": "2026-03-17", "minmagnitude": "4.0"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "usgs_earthquake_api"
        assert result.bundle.normalised_event.measure.value == 5.2
        # Verify epicentre geo from first feature
        assert abs(result.bundle.normalised_event.geo.lat - 23.72) < 0.01
        assert abs(result.bundle.normalised_event.geo.lon - 121.65) < 0.01

    @pytest.mark.asyncio
    async def test_no_events(self):
        """USGS no events: empty features still returns success (0 is valid data)."""
        collector = USGSEarthquakeCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = USGS_EMPTY
            result = await collector._fetch(
                {"starttime": "2026-03-16", "endtime": "2026-03-17", "minmagnitude": "8.0"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 0.0


# ── Carbon Intensity Tests ──

class TestCarbonIntensityCollector:
    """Test CarbonIntensityCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Carbon Intensity success: returns valid CollectionResult with latest actual."""
        collector = CarbonIntensityCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = CARBON_INTENSITY_SUCCESS
            result = await collector._fetch(
                {"date_from": "2026-03-17T00:00Z", "date_to": "2026-03-17T01:00Z"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "carbon_intensity_api"
        assert result.bundle.normalised_event.measure.value == 168.0  # Latest actual

    @pytest.mark.asyncio
    async def test_degraded_partial_data(self):
        """Carbon Intensity degraded: partial data (forecast only) still returns success."""
        collector = CarbonIntensityCollector()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = CARBON_INTENSITY_PARTIAL
            result = await collector._fetch(
                {"date_from": "2026-03-17T00:00Z", "date_to": "2026-03-17T00:30Z"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 180.0  # Falls back to forecast
