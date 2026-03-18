"""Cycle 026c Sprint 3 — Regression + Final Verification tests.

Tests:
1. 026a snapshot assets still manifest correctly
2. 026b assets still map correctly (collector, policy, mapper)
3. Cross-cycle counts are consistent
4. Full test suite regression (all 026c tests pass together)
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from backend.services.eval_asset_policy import (
    SNAPSHOT_ASSETS,
    LIVE_ONLY_ASSETS,
    AssetDisposition,
    classify_asset,
    is_r2_eligible,
    reject_live_as_immutable,
)
from backend.services.r2_manifest_builder import (
    BENCHMARK_CATALOG,
    STANDARDS_CATALOG,
    build_manifest,
)
from backend.services.construct_anchor_mapper import (
    _MAPPING_RULES,
    map_dimension_anchors,
    map_contract_anchors,
)


# ── Test 1: 026a snapshot assets still manifest correctly ───────────

class TestCycle026aRegression:
    """026a snapshot assets still work end-to-end."""

    def test_benchmark_catalog_count(self):
        """BENCHMARK_CATALOG still has 7 entries."""
        assert len(BENCHMARK_CATALOG) == 7

    def test_original_standards_still_in_catalog(self):
        """Original 6 standards (026a) still present."""
        catalog_ids = {e[0] for e in STANDARDS_CATALOG}
        original = {"wcag", "aria-apg", "react-docs", "tailwind-docs", "owasp-top10", "cwe-subset"}
        assert original.issubset(catalog_ids)

    @pytest.mark.parametrize("asset_id", [
        "humaneval", "mbpp", "hellaswag", "mmlu", "mmlu-pro",
        "swe-bench-verified", "arxiv-ml-metadata",
    ])
    def test_benchmark_assets_still_snapshot(self, asset_id: str):
        assert classify_asset(asset_id) == AssetDisposition.SNAPSHOT

    def test_original_4_anchor_rules_still_work(self):
        """Original 026a mapping rules still resolve correctly."""
        test_cases = [
            ("code_quality", "code_verification"),
            ("benchmark_eval_score", "benchmark_suite"),
            ("wcag_accessibility", "public_standard_check"),
            ("real_world_factual", "live_evidence_feed"),
        ]
        for dimension, expected_anchor in test_cases:
            result = map_dimension_anchors(dimension)
            anchor_ids = {a.anchor_id for a in result.anchors}
            assert expected_anchor in anchor_ids, f"{dimension} → {expected_anchor} missing"

    def test_manifest_generation_still_works(self):
        """build_manifest still produces valid entries for 026a assets."""
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "data.jsonl").write_text('{"task": "test"}\n')
            entry = build_manifest(
                p, asset_id="humaneval", asset_class="benchmark",
                source_url="https://github.com/openai/human-eval", version="v1.0",
            )
            assert entry.asset_id == "humaneval"
            assert entry.content_hash.startswith("sha256:")


# ── Test 2: 026b assets still map correctly ─────────────────────────

class TestCycle026bRegression:
    """026b assets — policy, collector, mapper all intact."""

    def test_semantic_scholar_still_live(self):
        assert classify_asset("semantic-scholar") == AssetDisposition.LIVE

    def test_semantic_scholar_not_r2_eligible(self):
        assert is_r2_eligible("semantic-scholar") is False

    def test_semantic_scholar_rejected_for_snapshot(self):
        with pytest.raises(ValueError, match="live-only"):
            reject_live_as_immutable("semantic-scholar")

    def test_026b_frontend_anchor_still_works(self):
        result = map_dimension_anchors("frontend_component")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "frontend_standards" in anchor_ids

    def test_026b_security_anchor_still_works(self):
        result = map_dimension_anchors("security_vulnerability")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "security_standards" in anchor_ids

    def test_026b_research_dual_anchor_still_works(self):
        result = map_dimension_anchors("research_paper_citation")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "research_metadata" in anchor_ids
        assert "research_evidence" in anchor_ids


# ── Test 3: Cross-cycle counts are consistent ───────────────────────

class TestCrossCycleCounts:
    """Ensure all counts are consistent across 026a/026b/026c."""

    def test_total_snapshot_assets(self):
        """16 total: 13 (026a) + 3 (026c)."""
        assert len(SNAPSHOT_ASSETS) == 16

    def test_total_live_only_assets(self):
        """6 total: 5 (026a) + 1 (026b)."""
        assert len(LIVE_ONLY_ASSETS) == 6

    def test_total_benchmark_catalog(self):
        """7 benchmark entries (026a only, unchanged)."""
        assert len(BENCHMARK_CATALOG) == 7

    def test_total_standards_catalog(self):
        """9 standards: 6 (026a) + 3 (026c)."""
        assert len(STANDARDS_CATALOG) == 9

    def test_total_mapping_rules(self):
        """11 rules: 4 (026a) + 4 (026b) + 3 (026c)."""
        assert len(_MAPPING_RULES) == 11

    def test_snapshot_and_live_disjoint(self):
        """No asset ID appears in both SNAPSHOT and LIVE sets."""
        overlap = SNAPSHOT_ASSETS & LIVE_ONLY_ASSETS
        assert len(overlap) == 0, f"Overlap: {overlap}"

    def test_all_catalog_assets_are_snapshot_eligible(self):
        """Every asset in STANDARDS_CATALOG and BENCHMARK_CATALOG is in SNAPSHOT_ASSETS."""
        all_catalog_ids = {e[0] for e in STANDARDS_CATALOG} | {e[0] for e in BENCHMARK_CATALOG}
        for asset_id in all_catalog_ids:
            assert asset_id in SNAPSHOT_ASSETS, f"{asset_id} in catalog but not in SNAPSHOT_ASSETS"


# ── Test 4: Full contract batch test ────────────────────────────────

class TestFullContractBatch:
    """map_contract_anchors handles a representative batch from all cycles."""

    def test_mixed_batch_all_cycles(self):
        """Process dimensions from 026a, 026b, and 026c in one call."""
        dims = [
            # 026a
            "code_quality",
            "benchmark_eval_score",
            "wcag_accessibility",
            # 026b
            "frontend_component",
            "security_vulnerability",
            # 026c
            "user_research_quality",
            "journey_mapping",
            "recovery_flow",
            # unrecognized
            "aesthetic_taste",
        ]
        results = map_contract_anchors(dims)
        assert len(results) == 9

        # All recognized dimensions have anchors
        for i in range(8):
            assert not results[i].weakly_anchored, f"Dimension {dims[i]} should be anchored"

        # Unrecognized is weakly anchored
        assert results[8].weakly_anchored is True
        assert results[8].dimension == "aesthetic_taste"
