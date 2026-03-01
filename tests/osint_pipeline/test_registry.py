"""Tests for registry loader.

T1.4: load from actual fixture file, version validation, get(),
settlement_eligible(), free_public_sources(), upstream_groups().
All K-fixes verified.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from osint_pipeline.models.registry import RegistryLoader, RegistrySource


REGISTRY_PATH = Path(
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/"
    "echelon_osint_source_registry_v0_6_0.json"
)


class TestRegistryLoading:
    """Registry loading and validation tests."""

    def test_load_from_real_fixture(self):
        """Successfully loads the actual v0.6.0 registry fixture."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        assert registry.version == "0.6.0"
        assert registry.total_sources == 65

    def test_version_validation_rejects_mismatch(self, tmp_path):
        """K-7: from_file() validates version == '0.6.0'."""
        bad_registry = tmp_path / "bad.json"
        bad_registry.write_text('{"version": "0.4.0", "sources": []}')
        with pytest.raises(ValueError, match="version mismatch"):
            RegistryLoader.from_file(bad_registry)

    def test_get_existing_source(self):
        """get() returns correct source."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        source = registry.get("companies_house_api")
        assert source is not None
        assert source.source_id == "companies_house_api"
        assert source.jurisdiction == "GB"
        assert source.source_group == "official_gov"

    def test_get_nonexistent_source(self):
        """get() returns None for unknown source_id."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        assert registry.get("nonexistent_source") is None

    def test_exists(self):
        """exists() and __contains__ work."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        assert registry.exists("companies_house_api")
        assert "companies_house_api" in registry
        assert not registry.exists("fake_source")


class TestRegistrySourceFields:
    """Verify all K-8 fields are present."""

    def test_all_fields_populated(self):
        """K-8: RegistrySource includes all registry fields."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        source = registry.get("companies_house_api")
        assert source is not None

        # K-2: cost_model field exists
        assert source.cost_model == "free"

        # K-8: all additional fields present
        assert source.source_name == "UK Companies House API"
        assert isinstance(source.replayability, str)
        assert isinstance(source.legal_risk, str)
        assert isinstance(source.rate_limit_notes, str)
        assert isinstance(source.gap_policy_default, bool)
        assert isinstance(source.evidence_capture, dict)
        assert isinstance(source.notes, str)
        assert isinstance(source.theatre_families, list)

    def test_independence_upstream_id(self):
        """Companies House upstream_id matches K-6 expected value."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        source = registry.get("companies_house_api")
        assert source is not None
        assert source.independence_upstream_id == "uk_companies_house_backend"


class TestRegistryQueries:
    """Registry query method tests."""

    def test_settlement_eligible(self):
        """settlement_eligible() returns only settlement-eligible sources."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        eligible = registry.settlement_eligible()
        assert len(eligible) > 0
        assert all(s.settlement_eligible for s in eligible)

    def test_by_jurisdiction_gb(self):
        """by_jurisdiction('GB') returns GB sources only."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        gb = registry.by_jurisdiction("GB")
        assert len(gb) > 0
        assert all(s.jurisdiction == "GB" for s in gb)

    def test_free_public_sources(self):
        """K-1: free_public_sources() returns correctly filtered set."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        free = registry.free_public_sources()
        assert len(free) > 0
        for s in free:
            assert s.access_surface == "public_api"
            assert s.cost_model == "free"
            assert s.settlement_eligible is True
            assert any(
                m in ("none", "api_key", "user_agent_header")
                for m in s.auth_methods
            )

    def test_free_public_sources_excludes_paid(self):
        """K-1: paid sources excluded from free_public_sources()."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        free_ids = {s.source_id for s in registry.free_public_sources()}
        all_ids = {s.source_id for s in registry.all_sources()}
        # There should be sources NOT in the free set
        assert len(all_ids - free_ids) > 0

    def test_upstream_groups(self):
        """upstream_groups() maps upstream_id to source_ids."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        groups = registry.upstream_groups()
        assert isinstance(groups, dict)
        assert len(groups) > 0
        # Companies House should be in its group
        ch_upstream = "uk_companies_house_backend"
        assert ch_upstream in groups
        assert "companies_house_api" in groups[ch_upstream]

    def test_counter_signal_sources(self):
        """counter_signal_sources() returns counter_signal role sources."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        cs = registry.counter_signal_sources()
        assert all(s.resolution_role == "counter_signal" for s in cs)

    def test_len(self):
        """__len__ returns source count."""
        registry = RegistryLoader.from_file(REGISTRY_PATH)
        assert len(registry) == 65


class TestSourceGroupTaxonomy:
    """E1: Source group taxonomy drift detection."""

    def test_non_committed_groups_have_mapping(self):
        """Every source with a non-committed group must have mapped_source_group."""
        import json

        with open(REGISTRY_PATH) as f:
            raw = json.load(f)
        committed = set(raw["source_group_enum"]["committed_values"])

        registry = RegistryLoader.from_file(REGISTRY_PATH)
        for source in registry.all_sources():
            if source.source_group not in committed:
                assert source.mapped_source_group is not None, (
                    f"{source.source_id} has non-committed group "
                    f"'{source.source_group}' but no mapped_source_group"
                )

    def test_mapped_groups_are_valid(self):
        """All mapped_source_group values are in proposed_source_groups or committed enum."""
        import json

        with open(REGISTRY_PATH) as f:
            raw = json.load(f)
        committed = set(raw["source_group_enum"]["committed_values"])
        proposed = set(raw.get("proposed_source_groups", []))
        valid = committed | proposed

        registry = RegistryLoader.from_file(REGISTRY_PATH)
        for source in registry.all_sources():
            if source.mapped_source_group is not None:
                assert source.mapped_source_group in valid, (
                    f"{source.source_id} mapped_source_group "
                    f"'{source.mapped_source_group}' not in valid set"
                )
