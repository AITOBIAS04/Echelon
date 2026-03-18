"""Cycle 026a Sprint 3 — Construct Anchor Mapping tests.

Tests:
1. Fully anchored mapping (dimension with recognized keywords -> gets anchors, not weakly_anchored)
2. Mixed mapping (contract with both recognized and unrecognized dimensions)
3. Weak-only mapping (dimension with no matching rules -> weakly_anchored=True, empty anchors)
4. Multi-anchor dimension (keywords matching multiple rules)
5. Case-insensitive matching
6. Contract mapping preserves order and length
7. Available anchors filtering
"""

import pytest

from backend.schemas.construct_anchor_schema import (
    AnchorClass,
    AnchorReference,
    EvaluationDimensionAnchor,
)
from backend.services.construct_anchor_mapper import (
    map_contract_anchors,
    map_dimension_anchors,
)


# ── Test 1: Fully Anchored Mapping ──────────────────────────────────

class TestFullyAnchoredMapping:
    """Dimensions with recognized keywords resolve to anchors."""

    def test_code_quality_resolves_to_deterministic_check(self):
        """A dimension containing 'code' matches the deterministic_check rule."""
        result = map_dimension_anchors("code_quality")

        assert isinstance(result, EvaluationDimensionAnchor)
        assert result.dimension == "code_quality"
        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.DETERMINISTIC_CHECK in anchor_classes

    def test_benchmark_performance_resolves_to_benchmark_dataset(self):
        """A dimension containing 'benchmark' matches the benchmark_dataset rule."""
        result = map_dimension_anchors("benchmark_performance")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.BENCHMARK_DATASET in anchor_classes

    def test_accessibility_resolves_to_public_standard(self):
        """A dimension containing 'accessibility' matches the public_standard rule."""
        result = map_dimension_anchors("accessibility_audit")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.PUBLIC_STANDARD in anchor_classes

    def test_factual_accuracy_resolves_to_live_external(self):
        """A dimension containing 'factual' matches the live_external_evidence rule."""
        result = map_dimension_anchors("factual_accuracy")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.LIVE_EXTERNAL_EVIDENCE in anchor_classes

    def test_anchors_have_required_fields(self):
        """Every resolved anchor has a non-empty anchor_id and rationale."""
        result = map_dimension_anchors("code_correctness")

        for anchor in result.anchors:
            assert isinstance(anchor, AnchorReference)
            assert len(anchor.anchor_id) > 0
            assert len(anchor.rationale) > 0
            assert isinstance(anchor.anchor_class, AnchorClass)


# ── Test 2: Mixed Mapping ───────────────────────────────────────────

class TestMixedMapping:
    """Contract with both recognized and unrecognized dimensions."""

    def test_mixed_contract(self):
        """map_contract_anchors handles a mix of known and unknown dimensions."""
        dimensions = [
            "code_quality",           # recognized
            "creative_writing",       # unrecognized
            "benchmark_performance",  # recognized
            "vibes_alignment",        # unrecognized
        ]

        results = map_contract_anchors(dimensions)

        assert len(results) == 4

        # code_quality: anchored
        assert results[0].dimension == "code_quality"
        assert results[0].weakly_anchored is False
        assert len(results[0].anchors) >= 1

        # creative_writing: weakly anchored
        assert results[1].dimension == "creative_writing"
        assert results[1].weakly_anchored is True
        assert len(results[1].anchors) == 0

        # benchmark_performance: anchored
        assert results[2].dimension == "benchmark_performance"
        assert results[2].weakly_anchored is False
        assert len(results[2].anchors) >= 1

        # vibes_alignment: weakly anchored
        assert results[3].dimension == "vibes_alignment"
        assert results[3].weakly_anchored is True
        assert len(results[3].anchors) == 0

    def test_mixed_contract_counts(self):
        """Count of weakly vs. strongly anchored dimensions in a mixed contract."""
        dimensions = [
            "lint_pass_rate",        # recognized (lint → deterministic)
            "user_satisfaction",     # unrecognized
            "wcag_compliance",       # recognized (wcag → public_standard)
        ]

        results = map_contract_anchors(dimensions)

        weak_count = sum(1 for r in results if r.weakly_anchored)
        strong_count = sum(1 for r in results if not r.weakly_anchored)

        assert weak_count == 1
        assert strong_count == 2


# ── Test 3: Weak-Only Mapping ────────────────────────────────────────

class TestWeakOnlyMapping:
    """Dimensions with no matching rules are weakly anchored."""

    def test_unrecognized_dimension(self):
        """A completely unrecognized dimension is weakly anchored."""
        result = map_dimension_anchors("creative_writing")

        assert result.dimension == "creative_writing"
        assert result.weakly_anchored is True
        assert len(result.anchors) == 0

    def test_another_unrecognized_dimension(self):
        """Another unrecognized dimension is also weakly anchored."""
        result = map_dimension_anchors("emotional_resonance")

        assert result.weakly_anchored is True
        assert len(result.anchors) == 0

    def test_all_weak_contract(self):
        """A contract with only unrecognized dimensions is entirely weakly anchored."""
        dimensions = ["vibes_alignment", "creative_writing", "emotional_resonance"]

        results = map_contract_anchors(dimensions)

        assert all(r.weakly_anchored for r in results)
        assert all(len(r.anchors) == 0 for r in results)


# ── Test 4: Multi-Anchor Dimension ──────────────────────────────────

class TestMultiAnchorDimension:
    """A dimension can match multiple anchor rules."""

    def test_accessible_code_matches_two_rules(self):
        """'accessible_code' contains both 'accessibility' and 'code' keywords."""
        result = map_dimension_anchors("accessible_code")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 2

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.DETERMINISTIC_CHECK in anchor_classes
        assert AnchorClass.PUBLIC_STANDARD in anchor_classes

    def test_live_benchmark_matches_two_rules(self):
        """'live_benchmark_score' contains both 'live' and 'benchmark' keywords."""
        result = map_dimension_anchors("live_benchmark_score")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 2

        anchor_classes = {a.anchor_class for a in result.anchors}
        assert AnchorClass.BENCHMARK_DATASET in anchor_classes
        assert AnchorClass.LIVE_EXTERNAL_EVIDENCE in anchor_classes


# ── Test 5: Case-Insensitive Matching ───────────────────────────────

class TestCaseInsensitiveMatching:
    """Keyword matching is case-insensitive."""

    def test_uppercase_dimension(self):
        """An uppercase dimension name still matches."""
        result = map_dimension_anchors("CODE_QUALITY")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

    def test_mixed_case_dimension(self):
        """A mixed-case dimension name still matches."""
        result = map_dimension_anchors("Benchmark_Performance")

        assert result.weakly_anchored is False
        assert len(result.anchors) >= 1

    def test_case_preserves_original_name(self):
        """The original dimension name is preserved in the result."""
        result = map_dimension_anchors("CODE_QUALITY")
        assert result.dimension == "CODE_QUALITY"


# ── Test 6: Contract Mapping Semantics ──────────────────────────────

class TestContractMappingSemantics:
    """map_contract_anchors preserves input order and length."""

    def test_preserves_order(self):
        """Output order matches input order."""
        dimensions = ["factual_accuracy", "code_quality", "creative_writing"]
        results = map_contract_anchors(dimensions)

        assert [r.dimension for r in results] == dimensions

    def test_preserves_length(self):
        """One output per input dimension."""
        dimensions = ["a", "b", "c", "d"]
        results = map_contract_anchors(dimensions)
        assert len(results) == 4

    def test_empty_contract(self):
        """An empty contract produces an empty result."""
        results = map_contract_anchors([])
        assert results == []


# ── Test 7: Available Anchors Filtering ─────────────────────────────

class TestAvailableAnchorsFiltering:
    """The available_anchors parameter restricts which anchors are returned."""

    def test_filter_to_single_anchor(self):
        """Only anchors in available_anchors are returned."""
        # "accessible_code" normally matches both deterministic + public_standard
        result = map_dimension_anchors(
            "accessible_code",
            available_anchors=["code_verification"],
        )

        assert result.weakly_anchored is False
        assert len(result.anchors) == 1
        assert result.anchors[0].anchor_id == "code_verification"

    def test_filter_excludes_all_becomes_weak(self):
        """If available_anchors excludes all matches, dimension becomes weakly anchored."""
        result = map_dimension_anchors(
            "code_quality",
            available_anchors=["nonexistent_anchor"],
        )

        assert result.weakly_anchored is True
        assert len(result.anchors) == 0
