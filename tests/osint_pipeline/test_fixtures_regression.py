"""Fixture regression tests.

Verifies that existing validation scripts and registry fixtures
continue to work correctly after pipeline changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from osint_pipeline.models.registry import RegistryLoader


REGISTRY_PATH = Path(
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/"
    "echelon_osint_source_registry_v0_4_0.json"
)


@pytest.fixture
def registry():
    """Load the actual registry fixture."""
    if not REGISTRY_PATH.exists():
        pytest.skip("Registry fixture not available")
    return RegistryLoader.from_file(REGISTRY_PATH)


class TestRegistryFixtureRegression:
    """Verify registry fixture loads and validates correctly."""

    def test_registry_loads(self, registry):
        assert registry.version == "0.4.0"

    def test_registry_has_sources(self, registry):
        assert registry.total_sources > 0

    def test_known_sources_present(self, registry):
        """Verify sources used by pipeline collectors exist."""
        known = [
            "companies_house_api",
            "sec_edgar",
            "ecb_data_api",
            "fred_api",
            "boe_rates",
            "uk_gazette",
        ]
        for source_id in known:
            source = registry.get(source_id)
            assert source is not None, f"Missing source: {source_id}"

    def test_settlement_eligible_subset(self, registry):
        eligible = registry.settlement_eligible()
        assert len(eligible) > 0
        for source in eligible:
            assert source.settlement_eligible is True

    def test_free_public_sources(self, registry):
        free = registry.free_public_sources()
        assert len(free) > 0
        for source in free:
            assert source.cost_model == "free"

    def test_upstream_groups(self, registry):
        groups = registry.upstream_groups()
        assert len(groups) > 0
        # Each group should have at least one source
        for upstream_id, source_ids in groups.items():
            assert len(source_ids) >= 1

    def test_by_jurisdiction(self, registry):
        gb_sources = registry.by_jurisdiction("GB")
        assert len(gb_sources) > 0
        for source in gb_sources:
            assert source.jurisdiction == "GB"


class TestCollectorRegistryAlignment:
    """Verify collector properties match registry entries."""

    def test_companies_house_alignment(self, registry):
        source = registry.get("companies_house_api")
        assert source is not None
        assert source.independence_upstream_id == "uk_companies_house_backend"
        assert source.jurisdiction == "GB"
        assert source.source_group == "official_gov"

    def test_sec_edgar_alignment(self, registry):
        source = registry.get("sec_edgar")
        assert source is not None
        assert source.independence_upstream_id == "us_sec_edgar_backend"
        assert source.jurisdiction == "US"
        assert source.source_group == "official_gov"

    def test_ecb_data_alignment(self, registry):
        source = registry.get("ecb_data_api")
        assert source is not None
        assert source.independence_upstream_id == "eu_ecb_sdw_backend"
        assert source.jurisdiction == "EU"
        assert source.source_group == "market_data"

    def test_fred_alignment(self, registry):
        source = registry.get("fred_api")
        assert source is not None
        assert source.independence_upstream_id == "us_stlouisfed_fred_backend"
        assert source.jurisdiction == "US"
        assert source.source_group == "market_data"

    def test_boe_alignment(self, registry):
        source = registry.get("boe_rates")
        assert source is not None
        assert source.independence_upstream_id == "uk_boe_statistics_backend"
        assert source.jurisdiction == "GB"
        assert source.source_group == "market_data"

    def test_gazette_alignment(self, registry):
        source = registry.get("uk_gazette")
        assert source is not None
        assert source.independence_upstream_id == "uk_tso_gazette_backend"
        assert source.jurisdiction == "GB"
        assert source.source_group == "official_gov"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
