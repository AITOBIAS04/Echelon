"""Registry loader tests — load, query, validation, alignment.

Tests verify that RegistryLoader correctly loads the OSINT source registry,
queries by source_id/source_group/wm_domain, validates enum membership,
and verifies WorldMonitor source alignment.

Scope: Runtime registry is intentionally pinned to 3 WorldMonitor sources
(worldmonitor_cii, worldmonitor_finance, worldmonitor_maritime) as defined
in Cycle-011. The full 160+ source registry from Cycle-005 (v1.0.0) is
available in the Intelligence DB but is not loaded at runtime. Broader
runtime registry loading is deferred to Cycle-017 registry expansion.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from backend.osint.models.registry import RegistryLoader, RegistrySource


@pytest.fixture
def sources_json_path() -> str:
    """Path to the production WM sources registry JSON."""
    return str(Path(__file__).parent.parent / "sources.json")


@pytest.fixture
def loader(sources_json_path: str) -> RegistryLoader:
    """RegistryLoader loaded from production sources.json."""
    return RegistryLoader(sources_json_path)


class TestRegistryLoading:
    """Registry JSON loading and parsing."""

    def test_loads_all_sources(self, loader: RegistryLoader) -> None:
        """Loads all 4 sources (3 WM + 1 CH)."""
        sources = loader.sources
        assert len(sources) == 4
        assert "worldmonitor_cii" in sources
        assert "worldmonitor_finance" in sources
        assert "worldmonitor_maritime" in sources
        assert "companies_house_api" in sources

    def test_source_fields_populated(self, loader: RegistryLoader) -> None:
        """All RegistrySource fields are populated correctly."""
        source = loader.get_source("worldmonitor_cii")
        assert source is not None
        assert source.source_id == "worldmonitor_cii"
        assert source.display_name == "World Monitor Country Instability Index"
        assert source.source_group == "alt_data_behavioural"
        assert source.resolution_role == "primary_evidence"
        assert source.independence_upstream_id == "worldmonitor"
        assert source.receipt_mode_minimum == "http_transcript"
        assert source.world_monitor_domain == "intelligence"
        assert source.settlement_eligible is False
        assert source.jurisdiction == "GLOBAL"


class TestRegistryQueries:
    """Query methods — get_source, get_sources_by_group, etc."""

    def test_get_source_by_id(self, loader: RegistryLoader) -> None:
        """get_source returns correct source for valid source_id."""
        source = loader.get_source("worldmonitor_finance")
        assert source is not None
        assert source.source_id == "worldmonitor_finance"

    def test_get_source_returns_none(self, loader: RegistryLoader) -> None:
        """get_source returns None for unknown source_id."""
        assert loader.get_source("nonexistent") is None

    def test_get_sources_by_group(self, loader: RegistryLoader) -> None:
        """get_sources_by_group filters by source_group enum value."""
        alt_data = loader.get_sources_by_group("alt_data_behavioural")
        assert len(alt_data) == 1
        assert alt_data[0].source_id == "worldmonitor_cii"

        market = loader.get_sources_by_group("market_data")
        assert len(market) == 1
        assert market[0].source_id == "worldmonitor_finance"

        maritime = loader.get_sources_by_group("maritime_ais")
        assert len(maritime) == 1
        assert maritime[0].source_id == "worldmonitor_maritime"

    def test_get_sources_by_group_empty(self, loader: RegistryLoader) -> None:
        """get_sources_by_group returns empty for unmatched group."""
        assert loader.get_sources_by_group("cyber_threat_intel") == []

    def test_get_sources_by_domain(self, loader: RegistryLoader) -> None:
        """get_sources_by_domain filters by world_monitor_domain."""
        intel = loader.get_sources_by_domain("intelligence")
        assert len(intel) == 1
        assert intel[0].source_id == "worldmonitor_cii"

    def test_get_settlement_eligible(self, loader: RegistryLoader) -> None:
        """Companies House is the only settlement-eligible source."""
        eligible = loader.get_settlement_eligible()
        assert len(eligible) == 1
        assert eligible[0].source_id == "companies_house_api"


class TestRegistryValidation:
    """Structural validation — enum checks, invariants."""

    def test_valid_registry_no_errors(self, loader: RegistryLoader) -> None:
        """Production sources.json passes validation."""
        errors = loader.validate()
        assert errors == []

    def test_invalid_source_group_detected(self) -> None:
        """Invalid source_group produces validation error."""
        data = {
            "sources": [{
                "source_id": "test_bad",
                "source_name": "Bad Source",
                "source_group": "not_a_real_group",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "test",
                "receipt_mode_minimum": "http_transcript",
            }]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            loader = RegistryLoader(f.name)

        errors = loader.validate()
        os.unlink(f.name)
        assert len(errors) >= 1
        assert "invalid source_group" in errors[0]

    def test_invalid_resolution_role_detected(self) -> None:
        """Invalid resolution_role produces validation error."""
        data = {
            "sources": [{
                "source_id": "test_bad",
                "source_name": "Bad Source",
                "source_group": "market_data",
                "resolution_role": "invalid_role",
                "independence_upstream_id": "test",
                "receipt_mode_minimum": "http_transcript",
            }]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            loader = RegistryLoader(f.name)

        errors = loader.validate()
        os.unlink(f.name)
        assert any("invalid resolution_role" in e for e in errors)

    def test_empty_upstream_id_detected(self) -> None:
        """Empty independence_upstream_id produces validation error."""
        data = {
            "sources": [{
                "source_id": "test_bad",
                "source_name": "Bad Source",
                "source_group": "market_data",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "",
                "receipt_mode_minimum": "http_transcript",
            }]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            loader = RegistryLoader(f.name)

        errors = loader.validate()
        os.unlink(f.name)
        assert any("independence_upstream_id is empty" in e for e in errors)


class TestWorldMonitorAlignment:
    """Verify 3 WM source entries are aligned with PRD Section 4.6."""

    def test_cii_alignment(self, loader: RegistryLoader) -> None:
        """worldmonitor_cii has correct alignment fields."""
        s = loader.get_source("worldmonitor_cii")
        assert s.source_group == "alt_data_behavioural"
        assert s.resolution_role == "primary_evidence"
        assert s.world_monitor_domain == "intelligence"
        assert s.independence_upstream_id == "worldmonitor"
        assert s.receipt_mode_minimum == "http_transcript"

    def test_finance_alignment(self, loader: RegistryLoader) -> None:
        """worldmonitor_finance has correct alignment fields."""
        s = loader.get_source("worldmonitor_finance")
        assert s.source_group == "market_data"
        assert s.resolution_role == "primary_evidence"
        assert s.world_monitor_domain == "market"
        assert s.independence_upstream_id == "worldmonitor"
        assert s.receipt_mode_minimum == "http_transcript"

    def test_maritime_alignment(self, loader: RegistryLoader) -> None:
        """worldmonitor_maritime has correct alignment fields."""
        s = loader.get_source("worldmonitor_maritime")
        assert s.source_group == "maritime_ais"
        assert s.resolution_role == "primary_evidence"
        assert s.world_monitor_domain == "maritime"
        assert s.independence_upstream_id == "worldmonitor"
        assert s.receipt_mode_minimum == "http_transcript"

    def test_shared_upstream_id(self, loader: RegistryLoader) -> None:
        """All 3 WM sources share independence_upstream_id 'worldmonitor'."""
        cii = loader.get_source("worldmonitor_cii")
        fin = loader.get_source("worldmonitor_finance")
        mar = loader.get_source("worldmonitor_maritime")
        assert cii.independence_upstream_id == "worldmonitor"
        assert fin.independence_upstream_id == "worldmonitor"
        assert mar.independence_upstream_id == "worldmonitor"
        # All same — they are NOT independent corroborators
        assert cii.independence_upstream_id == fin.independence_upstream_id == mar.independence_upstream_id
