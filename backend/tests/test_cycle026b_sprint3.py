"""Cycle 026b Sprint 3 — Anchor Mapper Expansion + Verification tests.

Tests:
1. Frontend dimensions map to frontend_standards (React/Tailwind)
2. Security dimensions map to security_standards (OWASP/CWE)
3. Research dimensions map to both research_metadata AND research_evidence
4. 026a anchor rules still map correctly (regression)
5. Weakly anchored behavior still explicit for unknown dimensions
6. Full contract mapping with mixed old+new dimensions
"""
from __future__ import annotations

import pytest

from backend.schemas.construct_anchor_schema import AnchorClass
from backend.services.construct_anchor_mapper import (
    map_contract_anchors,
    map_dimension_anchors,
)


# ── Tests ────────────────────────────────────────────────────────────

class TestFrontendAnchors:
    """Test 1: frontend dimensions map to frontend_standards."""

    @pytest.mark.parametrize("dimension", [
        "frontend_quality",
        "react_component_patterns",
        "tailwind_layout",
        "responsive_ui_quality",
        "css_consistency",
        "component_accessibility",
    ])
    def test_frontend_dimensions_map(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert result.weakly_anchored is False
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "frontend_standards" in anchor_ids

    def test_frontend_anchor_class_is_public_standard(self):
        result = map_dimension_anchors("react_component_quality")
        frontend = next(a for a in result.anchors if a.anchor_id == "frontend_standards")
        assert frontend.anchor_class == AnchorClass.PUBLIC_STANDARD

    def test_frontend_anchor_has_rationale(self):
        result = map_dimension_anchors("tailwind_responsive")
        frontend = next(a for a in result.anchors if a.anchor_id == "frontend_standards")
        assert len(frontend.rationale) > 0


class TestSecurityAnchors:
    """Test 2: security dimensions map to security_standards."""

    @pytest.mark.parametrize("dimension", [
        "security_audit",
        "owasp_compliance",
        "vulnerability_scan",
        "cwe_coverage",
        "injection_prevention",
        "xss_protection",
        "csrf_defense",
        "auth_bypass_check",
    ])
    def test_security_dimensions_map(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert result.weakly_anchored is False
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "security_standards" in anchor_ids

    def test_security_anchor_class_is_public_standard(self):
        result = map_dimension_anchors("owasp_top10_compliance")
        security = next(a for a in result.anchors if a.anchor_id == "security_standards")
        assert security.anchor_class == AnchorClass.PUBLIC_STANDARD


class TestResearchAnchors:
    """Test 3: research dimensions map to BOTH research_metadata AND research_evidence."""

    @pytest.mark.parametrize("dimension", [
        "research_citation_quality",
        "paper_relevance",
        "scholarly_grounding",
        "citation_count_check",
    ])
    def test_research_dimensions_map_to_both(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert result.weakly_anchored is False
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "research_metadata" in anchor_ids
        assert "research_evidence" in anchor_ids

    def test_research_metadata_is_benchmark(self):
        result = map_dimension_anchors("arxiv_paper_analysis")
        metadata = next(a for a in result.anchors if a.anchor_id == "research_metadata")
        assert metadata.anchor_class == AnchorClass.BENCHMARK_DATASET

    def test_research_evidence_is_live(self):
        result = map_dimension_anchors("semantic_scholar_lookup")
        evidence = next(a for a in result.anchors if a.anchor_id == "research_evidence")
        assert evidence.anchor_class == AnchorClass.LIVE_EXTERNAL_EVIDENCE

    def test_arxiv_only_dimension(self):
        """A dimension with 'arxiv' but not 'scholarly' gets research_metadata."""
        result = map_dimension_anchors("arxiv_ml_method")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "research_metadata" in anchor_ids


class TestRegressionOldRules:
    """Test 4: 026a anchor rules still map correctly."""

    def test_code_dimension_still_maps(self):
        result = map_dimension_anchors("code_quality")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "code_verification" in anchor_ids

    def test_benchmark_dimension_still_maps(self):
        result = map_dimension_anchors("benchmark_eval_score")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "benchmark_suite" in anchor_ids

    def test_accessibility_dimension_still_maps(self):
        result = map_dimension_anchors("accessibility_compliance")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "public_standard_check" in anchor_ids

    def test_live_evidence_dimension_still_maps(self):
        result = map_dimension_anchors("real_world_factual_check")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "live_evidence_feed" in anchor_ids

    def test_wcag_still_public_standard(self):
        result = map_dimension_anchors("wcag_conformance")
        public_std = next(a for a in result.anchors if a.anchor_id == "public_standard_check")
        assert public_std.anchor_class == AnchorClass.PUBLIC_STANDARD

    def test_osint_still_live_evidence(self):
        result = map_dimension_anchors("osint_intelligence")
        live = next(a for a in result.anchors if a.anchor_id == "live_evidence_feed")
        assert live.anchor_class == AnchorClass.LIVE_EXTERNAL_EVIDENCE


class TestWeaklyAnchored:
    """Test 5: weakly anchored behavior for unknown dimensions."""

    @pytest.mark.parametrize("dimension", [
        "cooking_skills",
        "vibes_check",
        "artistic_merit",
        "emotional_intelligence",
    ])
    def test_unknown_dimensions_are_weakly_anchored(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert result.weakly_anchored is True
        assert len(result.anchors) == 0

    def test_weakly_anchored_preserves_dimension_name(self):
        result = map_dimension_anchors("unknown_dimension_xyz")
        assert result.dimension == "unknown_dimension_xyz"


class TestMixedContract:
    """Test 6: full contract mapping with mixed old+new dimensions."""

    def test_mixed_contract_all_mapped(self):
        dimensions = [
            "code_quality",           # old: code_verification
            "benchmark_eval",         # old: benchmark_suite
            "accessibility_audit",    # old: public_standard_check
            "frontend_react_quality", # new: frontend_standards
            "security_owasp_check",   # new: security_standards
            "research_paper_review",  # new: research_metadata + research_evidence
            "unknown_dimension",      # weakly anchored
        ]
        results = map_contract_anchors(dimensions)
        assert len(results) == 7

        # Each non-unknown dimension has at least one anchor
        for r in results[:6]:
            assert r.weakly_anchored is False, f"{r.dimension} unexpectedly weak"
            assert len(r.anchors) >= 1

        # The unknown dimension is weakly anchored
        assert results[6].weakly_anchored is True
        assert results[6].dimension == "unknown_dimension"

    def test_contract_preserves_order(self):
        dims = ["code_quality", "security_audit", "frontend_react"]
        results = map_contract_anchors(dims)
        assert [r.dimension for r in results] == dims

    def test_available_anchors_filter(self):
        """available_anchors filter still works with new rules."""
        result = map_dimension_anchors(
            "research_paper_check",
            available_anchors=["research_metadata"],
        )
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "research_metadata" in anchor_ids
        assert "research_evidence" not in anchor_ids
