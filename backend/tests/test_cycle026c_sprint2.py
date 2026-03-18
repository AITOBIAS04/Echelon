"""Cycle 026c Sprint 2 — Anchor Mapper Expansion tests.

Tests:
1. User-research dimensions anchor to user_research_methods
2. Journey-pattern dimensions anchor to journey_patterns
3. Recovery/gap-analysis dimensions anchor to recovery_guidance
4. Weak-anchor fallback for out-of-scope dimensions
5. Regression: existing 026a/026b rules still match
"""
from __future__ import annotations

import pytest

from backend.services.construct_anchor_mapper import (
    map_dimension_anchors,
    map_contract_anchors,
)
from backend.schemas.construct_anchor_schema import AnchorClass


# ── Test 1: User-research dimensions ────────────────────────────────

class TestUserResearchAnchors:
    """User-research methodology dimensions anchor to user_research_methods."""

    @pytest.mark.parametrize("dimension", [
        "user_research_quality",
        "hypothesis_framing",
        "interview_technique",
        "survey_design",
        "usability_testing",
        "evidence_discipline_score",
        "confidence_label_accuracy",
    ])
    def test_dimension_anchors_to_user_research(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert not result.weakly_anchored, f"{dimension} should not be weakly anchored"
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "user_research_methods" in anchor_ids

    @pytest.mark.parametrize("dimension", [
        "user_research_quality",
        "hypothesis_framing",
        "evidence_discipline_score",
        "confidence_label_accuracy",
    ])
    def test_anchor_class_is_public_standard(self, dimension: str):
        result = map_dimension_anchors(dimension)
        urm_anchors = [a for a in result.anchors if a.anchor_id == "user_research_methods"]
        assert len(urm_anchors) == 1
        assert urm_anchors[0].anchor_class == AnchorClass.PUBLIC_STANDARD


# ── Test 2: Journey-pattern dimensions ──────────────────────────────

class TestJourneyPatternAnchors:
    """Journey and flow dimensions anchor to journey_patterns."""

    @pytest.mark.parametrize("dimension", [
        "journey_mapping",
        "flow_quality",
        "step_by_step_navigation",
        "task_list_completeness",
        "check_answers_pattern",
        "onboarding_flow",
        "flow_extraction_coverage",
    ])
    def test_dimension_anchors_to_journey(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert not result.weakly_anchored, f"{dimension} should not be weakly anchored"
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "journey_patterns" in anchor_ids

    @pytest.mark.parametrize("dimension", [
        "journey_mapping",
        "flow_quality",
        "step_by_step_navigation",
    ])
    def test_anchor_class_is_public_standard(self, dimension: str):
        result = map_dimension_anchors(dimension)
        jp_anchors = [a for a in result.anchors if a.anchor_id == "journey_patterns"]
        assert len(jp_anchors) == 1
        assert jp_anchors[0].anchor_class == AnchorClass.PUBLIC_STANDARD


# ── Test 3: Recovery / gap-analysis dimensions ──────────────────────

class TestRecoveryGapAnalysisAnchors:
    """Recovery and gap-analysis dimensions anchor to recovery_guidance."""

    @pytest.mark.parametrize("dimension", [
        "recovery_flow",
        "validation_design",
        "error_handling_quality",
        "error_message_clarity",
        "gap_analysis_coverage",
        "recovery_reasoning_depth",
    ])
    def test_dimension_anchors_to_recovery(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert not result.weakly_anchored, f"{dimension} should not be weakly anchored"
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "recovery_guidance" in anchor_ids

    @pytest.mark.parametrize("dimension", [
        "recovery_flow",
        "validation_design",
        "gap_analysis_coverage",
    ])
    def test_anchor_class_is_public_standard(self, dimension: str):
        result = map_dimension_anchors(dimension)
        rg_anchors = [a for a in result.anchors if a.anchor_id == "recovery_guidance"]
        assert len(rg_anchors) == 1
        assert rg_anchors[0].anchor_class == AnchorClass.PUBLIC_STANDARD


# ── Test 4: Weak-anchor fallback ────────────────────────────────────

class TestWeakAnchorFallback:
    """Out-of-scope dimensions still fall back to weakly anchored."""

    @pytest.mark.parametrize("dimension", [
        "creativity_score",
        "philosophical_depth",
        "musical_harmony",
        "color_palette_taste",
    ])
    def test_unrecognized_is_weakly_anchored(self, dimension: str):
        result = map_dimension_anchors(dimension)
        assert result.weakly_anchored is True
        assert len(result.anchors) == 0

    def test_available_anchors_filter(self):
        """When available_anchors excludes the match, dimension becomes weak."""
        result = map_dimension_anchors("journey_mapping", available_anchors=["code_verification"])
        assert result.weakly_anchored is True


# ── Test 5: Regression for 026a/026b rules ──────────────────────────

class TestRegressionExistingRules:
    """Existing anchor rules from 026a and 026b still work."""

    # 026a original rules
    def test_code_dimension_still_matches(self):
        result = map_dimension_anchors("code_quality")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "code_verification" in anchor_ids

    def test_benchmark_dimension_still_matches(self):
        result = map_dimension_anchors("benchmark_eval_score")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "benchmark_suite" in anchor_ids

    def test_accessibility_dimension_still_matches(self):
        result = map_dimension_anchors("wcag_accessibility")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "public_standard_check" in anchor_ids

    def test_factual_dimension_still_matches(self):
        result = map_dimension_anchors("real_world_factual")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "live_evidence_feed" in anchor_ids

    # 026b rules
    def test_frontend_dimension_still_matches(self):
        result = map_dimension_anchors("frontend_component")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "frontend_standards" in anchor_ids

    def test_security_dimension_still_matches(self):
        result = map_dimension_anchors("security_vulnerability")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "security_standards" in anchor_ids

    def test_research_dimension_dual_anchor(self):
        """Research dimensions anchor to both benchmark (arXiv) and live (Semantic Scholar)."""
        result = map_dimension_anchors("research_paper_citation")
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "research_metadata" in anchor_ids
        assert "research_evidence" in anchor_ids

    def test_mapping_rules_count(self):
        """_MAPPING_RULES now has 11 entries (8 from 026a/b + 3 from 026c)."""
        from backend.services.construct_anchor_mapper import _MAPPING_RULES
        assert len(_MAPPING_RULES) == 11

    def test_map_contract_anchors_batch(self):
        """map_contract_anchors processes a mixed batch correctly."""
        dims = [
            "code_quality",
            "journey_mapping",
            "user_research_quality",
            "recovery_flow",
            "creativity_score",
        ]
        results = map_contract_anchors(dims)
        assert len(results) == 5
        assert not results[0].weakly_anchored  # code
        assert not results[1].weakly_anchored  # journey
        assert not results[2].weakly_anchored  # user research
        assert not results[3].weakly_anchored  # recovery
        assert results[4].weakly_anchored      # creativity (no anchor)
