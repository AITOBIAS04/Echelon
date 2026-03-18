"""Cycle 026c Sprint 0 — Policy + Catalog Extension tests.

Tests:
1. New human-centred assets are classified as SNAPSHOT
2. New assets are R2-eligible
3. Existing 026a/026b assets still classified correctly
4. STANDARDS_CATALOG has correct count (9 entries)
5. New catalog entries have valid structure
"""
from __future__ import annotations

import pytest

from backend.services.eval_asset_policy import (
    SNAPSHOT_ASSETS,
    LIVE_ONLY_ASSETS,
    AssetDisposition,
    classify_asset,
    is_r2_eligible,
    validate_snapshot_candidate,
)
from backend.services.r2_manifest_builder import STANDARDS_CATALOG


# ── New human-centred assets ──────────────────────────────────────

CYCLE_026C_ASSETS = [
    "user-research-methods",
    "journey-patterns",
    "recovery-guidance",
]


class TestNewAssetClassification:
    """Test 1: new human-centred assets are classified as SNAPSHOT."""

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_classified_as_snapshot(self, asset_id: str):
        assert classify_asset(asset_id) == AssetDisposition.SNAPSHOT

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_in_snapshot_frozenset(self, asset_id: str):
        assert asset_id in SNAPSHOT_ASSETS

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_not_in_live_only(self, asset_id: str):
        assert asset_id not in LIVE_ONLY_ASSETS


class TestNewAssetR2Eligibility:
    """Test 2: new assets are R2-eligible."""

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_r2_eligible(self, asset_id: str):
        assert is_r2_eligible(asset_id) is True

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_validate_snapshot_candidate_accepted(self, asset_id: str):
        ok, reason = validate_snapshot_candidate(asset_id)
        assert ok is True
        assert reason == "accepted"


class TestExistingAssetsRegression:
    """Test 3: existing 026a/026b assets still classified correctly."""

    # 026a snapshot assets
    @pytest.mark.parametrize("asset_id", [
        "humaneval", "mbpp", "hellaswag", "mmlu", "mmlu-pro",
        "swe-bench-verified", "wcag", "aria-apg", "react-docs",
        "tailwind-docs", "owasp-top10", "cwe-subset", "arxiv-ml-metadata",
    ])
    def test_original_snapshots_still_valid(self, asset_id: str):
        assert classify_asset(asset_id) == AssetDisposition.SNAPSHOT

    # 026b live-only assets
    @pytest.mark.parametrize("asset_id", [
        "sec-edgar", "ofac", "un-sanctions", "gdelt",
        "global-fishing-watch", "semantic-scholar",
    ])
    def test_live_only_still_valid(self, asset_id: str):
        assert classify_asset(asset_id) == AssetDisposition.LIVE

    def test_snapshot_count(self):
        """SNAPSHOT_ASSETS now has 16 entries (13 original + 3 new)."""
        assert len(SNAPSHOT_ASSETS) == 16

    def test_live_only_count(self):
        """LIVE_ONLY_ASSETS still has 6 entries."""
        assert len(LIVE_ONLY_ASSETS) == 6


class TestStandardsCatalog:
    """Test 4: STANDARDS_CATALOG has correct count."""

    def test_catalog_count(self):
        """STANDARDS_CATALOG now has 9 entries (6 original + 3 new)."""
        assert len(STANDARDS_CATALOG) == 9

    def test_new_entries_present(self):
        catalog_ids = {entry[0] for entry in STANDARDS_CATALOG}
        for asset_id in CYCLE_026C_ASSETS:
            assert asset_id in catalog_ids, f"{asset_id} missing from STANDARDS_CATALOG"


class TestNewCatalogEntryStructure:
    """Test 5: new catalog entries have valid structure."""

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_entry_has_four_fields(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert len(entry) == 4, f"{asset_id} entry should be (id, url, version, license)"

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_entry_has_gov_uk_url(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert "gov.uk" in entry[1], f"{asset_id} should reference GOV.UK"

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_entry_has_ogl_license(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert entry[3] == "OGL-3.0", f"{asset_id} should use OGL-3.0 license"

    @pytest.mark.parametrize("asset_id", CYCLE_026C_ASSETS)
    def test_entry_version(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert entry[2] == "2026-03"
