"""Cycle 026 Sprint 0 — Registry + Enum + Scaffold + Wiring tests.

Tests:
1. _VALID_SOURCE_GROUPS has all 37 values including 4 new ones
2. New source_group values are in the frozenset
3. RegistryLoader loads 16 entries from sources.json v0.5.0
4. RegistryLoader.validate() returns no errors
5. build_collector_map() returns all 14 source_ids (3 WM + 1 CH + 10 Batch 1)
"""
import os
import pathlib

import pytest

from backend.osint.models.registry import (
    RegistryLoader,
    _VALID_SOURCE_GROUPS,
)


# Path to sources.json relative to repo root
SOURCES_JSON = str(
    pathlib.Path(__file__).resolve().parents[1] / "osint" / "sources.json"
)


class TestSourceGroupExpansion:
    """Test _VALID_SOURCE_GROUPS enum expansion."""

    def test_valid_source_groups_has_37_values(self):
        """_VALID_SOURCE_GROUPS contains exactly 37 values after Batch 1 expansion."""
        assert len(_VALID_SOURCE_GROUPS) == 37

    def test_new_source_groups_present(self):
        """All 4 new source_group values from Cycle-026 are in the frozenset."""
        new_groups = {"blockchain_data", "geospatial", "environmental", "event_data"}
        for group in new_groups:
            assert group in _VALID_SOURCE_GROUPS, f"Missing: {group}"


class TestRegistryExpansion:
    """Test sources.json v0.5.0 with 16 entries."""

    def test_registry_loads_16_entries(self):
        """RegistryLoader loads all 16 sources from v0.5.0 registry."""
        loader = RegistryLoader(SOURCES_JSON)
        assert len(loader.sources) == 16

    def test_registry_validates_clean(self):
        """RegistryLoader.validate() returns no errors for v0.5.0 registry."""
        loader = RegistryLoader(SOURCES_JSON)
        errors = loader.validate()
        assert errors == [], f"Validation errors: {errors}"


class TestCollectorMap:
    """Test build_collector_map() wiring."""

    def test_collector_map_has_all_14_source_ids(self):
        """build_collector_map() returns all 14 collectors (3 WM + 1 CH + 10 Batch 1)."""
        # Import here to avoid triggering WM HTTP config at module level
        from backend.osint.collectors.collector_map import build_collector_map

        collector_map = build_collector_map()

        expected_source_ids = {
            # Existing
            "worldmonitor_cii",
            "worldmonitor_finance",
            "worldmonitor_maritime",
            "companies_house_api",
            # Batch 1
            "fred_api",
            "alpha_vantage_api",
            "opencorporates_api",
            "etherscan_api",
            "coingecko_api",
            "opensky_api",
            "usgs_earthquake_api",
            "carbon_intensity_api",
            "openaq_api",
            "calendarific_api",
        }

        assert set(collector_map.keys()) == expected_source_ids
        assert len(collector_map) == 14
