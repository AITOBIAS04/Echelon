"""Cycle 026b Sprint 0 — Extended Eval Asset Policy + Registry Catalog tests.

Tests:
1. New snapshot assets (react-docs, tailwind-docs, owasp-top10, cwe-subset, arxiv-ml-metadata) accepted
2. semantic-scholar classified as LIVE
3. semantic-scholar rejected as immutable (reject_live_as_immutable raises)
4. 026a assets still classified correctly (regression)
5. STANDARDS_CATALOG has 6 entries (wcag, aria-apg, react-docs, tailwind-docs, owasp-top10, cwe-subset)
6. BENCHMARK_CATALOG has 7 entries (6 original + arxiv-ml-metadata)
7. New catalog entries have non-empty source_url and version
"""

from __future__ import annotations

import pytest

from backend.services.eval_asset_policy import (
    AssetDisposition,
    classify_asset,
    is_r2_eligible,
    reject_live_as_immutable,
    validate_snapshot_candidate,
)
from backend.services.r2_manifest_builder import (
    BENCHMARK_CATALOG,
    STANDARDS_CATALOG,
)


# ── New Snapshot Assets ─────────────────────────────────────────────

class TestNewSnapshotAssets:
    """Cycle 026b new snapshot assets are accepted by classify_asset."""

    @pytest.mark.parametrize("asset_id", [
        "react-docs",
        "tailwind-docs",
        "owasp-top10",
        "cwe-subset",
        "arxiv-ml-metadata",
    ])
    def test_new_snapshot_assets_classified(self, asset_id: str) -> None:
        """New snapshot assets are classified as SNAPSHOT and R2-eligible."""
        disposition = classify_asset(asset_id)
        assert disposition == AssetDisposition.SNAPSHOT, (
            f"{asset_id} should be SNAPSHOT, got {disposition}"
        )
        assert is_r2_eligible(asset_id), f"{asset_id} should be R2-eligible"

        ok, reason = validate_snapshot_candidate(asset_id)
        assert ok is True, f"{asset_id}: {reason}"
        assert reason == "accepted"


# ── semantic-scholar Live Classification ────────────────────────────

class TestSemanticScholarLive:
    """semantic-scholar is classified as LIVE and rejected as immutable."""

    def test_semantic_scholar_classified_live(self) -> None:
        """semantic-scholar is classified as LIVE."""
        disposition = classify_asset("semantic-scholar")
        assert disposition == AssetDisposition.LIVE
        assert not is_r2_eligible("semantic-scholar")

        ok, reason = validate_snapshot_candidate("semantic-scholar")
        assert ok is False
        assert "live-only" in reason.lower()

    def test_semantic_scholar_rejected_as_immutable(self) -> None:
        """reject_live_as_immutable raises ValueError for semantic-scholar."""
        with pytest.raises(ValueError, match="Policy violation"):
            reject_live_as_immutable("semantic-scholar")


# ── 026a Regression ─────────────────────────────────────────────────

class TestCycle026aRegression:
    """Original 026a assets still classify correctly after 026b additions."""

    @pytest.mark.parametrize("asset_id", [
        "humaneval",
        "mbpp",
        "hellaswag",
        "mmlu",
        "mmlu-pro",
        "swe-bench-verified",
        "wcag",
        "aria-apg",
    ])
    def test_original_snapshot_assets(self, asset_id: str) -> None:
        """All original snapshot assets remain SNAPSHOT after 026b."""
        assert classify_asset(asset_id) == AssetDisposition.SNAPSHOT

    @pytest.mark.parametrize("asset_id", [
        "sec-edgar",
        "ofac",
        "un-sanctions",
        "gdelt",
        "global-fishing-watch",
    ])
    def test_original_live_assets(self, asset_id: str) -> None:
        """All original live-only assets remain LIVE after 026b."""
        assert classify_asset(asset_id) == AssetDisposition.LIVE


# ── Catalog Counts ──────────────────────────────────────────────────

class TestCatalogCounts:
    """Registry catalogs have the expected number of entries after 026b."""

    def test_standards_catalog_count(self) -> None:
        """STANDARDS_CATALOG has 6 entries (wcag, aria-apg, react-docs, tailwind-docs, owasp-top10, cwe-subset)."""
        assert len(STANDARDS_CATALOG) == 6
        asset_ids = [entry[0] for entry in STANDARDS_CATALOG]
        expected = {"wcag", "aria-apg", "react-docs", "tailwind-docs", "owasp-top10", "cwe-subset"}
        assert set(asset_ids) == expected

    def test_benchmark_catalog_count(self) -> None:
        """BENCHMARK_CATALOG has 7 entries (6 original + arxiv-ml-metadata)."""
        assert len(BENCHMARK_CATALOG) == 7
        asset_ids = [entry[0] for entry in BENCHMARK_CATALOG]
        assert "arxiv-ml-metadata" in asset_ids

        # Verify all original benchmarks still present
        original = {"humaneval", "mbpp", "hellaswag", "mmlu", "mmlu-pro", "swe-bench-verified"}
        assert original.issubset(set(asset_ids))


# ── Catalog Entry Integrity ────────────────────────────────────────

class TestCatalogEntryIntegrity:
    """New catalog entries have non-empty source_url and version."""

    @pytest.mark.parametrize("catalog,asset_id", [
        (STANDARDS_CATALOG, "react-docs"),
        (STANDARDS_CATALOG, "tailwind-docs"),
        (STANDARDS_CATALOG, "owasp-top10"),
        (STANDARDS_CATALOG, "cwe-subset"),
        (BENCHMARK_CATALOG, "arxiv-ml-metadata"),
    ])
    def test_new_entries_have_source_url_and_version(
        self,
        catalog: list,
        asset_id: str,
    ) -> None:
        """New catalog entries have non-empty source_url and version."""
        entry = next((e for e in catalog if e[0] == asset_id), None)
        assert entry is not None, f"{asset_id} not found in catalog"

        _id, source_url, version, _license = entry
        assert source_url, f"{asset_id} has empty source_url"
        assert version, f"{asset_id} has empty version"
        assert source_url.startswith("http"), f"{asset_id} source_url should be a URL"
