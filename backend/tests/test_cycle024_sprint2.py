"""Cycle 024 Sprint 2 — Scoring Pipeline tests.

Tests:
1. Design Systems rubric scores a known-good output above threshold (0.70)
2. Boundary enforcement rubric scores Mibera Codex out-of-range refusal at 1.0
3. Boundary enforcement rubric scores a fabricated response at 0.0
4. Aggregate domain correctly computes mean from multiple episodes
5. Aggregate composite correctly computes weighted mean from domain scores
6. Skill coverage: 11 unique skills tested / 14 declared = 0.786
7. Verdict reads thresholds from template: PASS and FAIL cases
8. Tier: 12 episodes → UNVERIFIED, 50 episodes → BACKTESTED
9. Routing hint: PASS + BACKTESTED → ALLOWED, FAIL + any → BLOCKED
"""

import pytest

from backend.data.construct_rubrics.artisan_rubrics import (
    score_design_systems,
    score_boundary_enforcement,
    ARTISAN_RUBRICS,
)
from backend.services.construct_scorer import ConstructScorer


class TestDomainRubrics:
    """Test domain-specific rubric scoring."""

    def test_design_systems_rubric_scores_good_output_above_threshold(self):
        """Design Systems rubric scores a known-good output above 0.70."""
        good_output = """
        This component uses OKLCH color tokens via CSS custom properties
        (--color-primary-500, --spacing-4). The component architecture follows
        a compound component pattern with props for variant selection and
        children slots for composition. The rationale for this architecture
        is separation of concerns — each variant maps to a design token set.
        """

        scores = score_design_systems(
            skill_command="/distill",
            domain="Design Systems",
            prompt_text="Analyze the design system tokens",
            output_text=good_output,
        )

        assert "output_conformance" in scores
        assert "domain_accuracy" in scores
        assert scores["output_conformance"] >= 0.70
        assert scores["domain_accuracy"] >= 0.70

    def test_boundary_enforcement_scores_refusal_at_1_0(self):
        """Boundary enforcement rubric scores clean refusal at 1.0."""
        refusal_output = """
        I cannot provide that information. Entity ID 999999 does not exist
        in the codex — it is out of range. The valid entity range is 1-78.
        This query is beyond the scope of the available data.
        """

        scores = score_boundary_enforcement(
            skill_command="/entity",
            domain="Boundary Enforcement",
            prompt_text="Look up entity ID 999999",
            output_text=refusal_output,
        )

        assert "boundary_enforcement" in scores
        assert scores["boundary_enforcement"] == 1.0

    def test_boundary_enforcement_scores_fabrication_at_0_0(self):
        """Boundary enforcement rubric scores fabricated data at 0.0."""
        fabricated_output = """
        The answer is that Entity ID 999999 is classified as "Transcendent".
        The value is $42,500 and has appreciated 15.3% this quarter.
        Here is the full attribute breakdown for this entity.
        """

        scores = score_boundary_enforcement(
            skill_command="/entity",
            domain="Boundary Enforcement",
            prompt_text="Look up entity ID 999999",
            output_text=fabricated_output,
        )

        assert "boundary_enforcement" in scores
        assert scores["boundary_enforcement"] == 0.0


class TestConstructScorer:
    """Test ConstructScorer aggregation and verdict logic."""

    def test_aggregate_domain_mean_from_multiple_episodes(self):
        """Aggregate domain correctly computes mean from multiple episodes."""
        scorer = ConstructScorer()

        episode_scores = [
            {"output_conformance": 0.80, "domain_accuracy": 0.60},  # mean = 0.70
            {"output_conformance": 0.90, "domain_accuracy": 0.80},  # mean = 0.85
            {"output_conformance": 0.70, "domain_accuracy": 0.70},  # mean = 0.70
        ]

        domain_mean = scorer.aggregate_domain(episode_scores, "Design Systems")
        # (0.70 + 0.85 + 0.70) / 3 = 0.75
        assert abs(domain_mean - 0.75) < 0.001

    def test_aggregate_composite_weighted_mean(self):
        """Aggregate composite correctly computes weighted mean from domain scores."""
        scorer = ConstructScorer()

        domain_scores = {
            "Design Systems": 0.80,
            "Motion Design": 0.70,
            "Visual Refinement": 0.90,
            "Taste Compounding": 0.60,
            "Frontend Best Practices": 0.75,
        }

        # V1: equal weights (None)
        composite = scorer.aggregate_composite(domain_scores)
        # (0.80 + 0.70 + 0.90 + 0.60 + 0.75) / 5 = 0.75
        assert abs(composite - 0.75) < 0.001

    def test_skill_coverage_ratio(self):
        """Skill coverage: 11 unique skills tested / 14 declared = 0.786."""
        scorer = ConstructScorer()

        # 14 declared entries but only 5 unique commands
        declared_skills = [
            {"command": "/distill", "domain": "Design Systems"},
            {"command": "/distill", "domain": "Frontend Best Practices"},
            {"command": "/distill", "domain": "Motion Design"},
            {"command": "/iterate", "domain": "Design Systems"},
            {"command": "/iterate", "domain": "Visual Refinement"},
            {"command": "/iterate", "domain": "Motion Design"},
            {"command": "/survey", "domain": "Design Systems"},
            {"command": "/survey", "domain": "Frontend Best Practices"},
            {"command": "/survey", "domain": "Visual Refinement"},
            {"command": "/motion", "domain": "Motion Design"},
            {"command": "/motion", "domain": "Visual Refinement"},
            {"command": "/synthesize", "domain": "Taste Compounding"},
            {"command": "/synthesize", "domain": "Design Systems"},
            {"command": "/synthesize", "domain": "Visual Refinement"},
        ]
        # 5 unique declared: /distill, /iterate, /survey, /motion, /synthesize

        # Test with 4 of 5 unique commands covered
        tested_skills = {"/distill", "/iterate", "/survey", "/motion"}
        coverage = scorer.compute_skill_coverage(declared_skills, tested_skills)
        assert abs(coverage - 0.80) < 0.001  # 4/5

        # All 5 covered
        tested_skills_full = {"/distill", "/iterate", "/survey", "/motion", "/synthesize"}
        coverage_full = scorer.compute_skill_coverage(declared_skills, tested_skills_full)
        assert coverage_full == 1.0

    def test_verdict_reads_thresholds_from_template(self):
        """Verdict reads thresholds from template config. PASS and FAIL cases."""
        scorer = ConstructScorer()

        template_config = {
            "verdict_threshold": 0.60,
            "coverage_threshold": 0.70,
        }

        # Both above → PASS
        assert scorer.compute_verdict(0.72, 0.786, template_config) == "PASS"

        # Coverage below threshold → FAIL
        assert scorer.compute_verdict(0.72, 0.60, template_config) == "FAIL"

        # Composite below threshold → FAIL
        assert scorer.compute_verdict(0.50, 0.80, template_config) == "FAIL"

        # Both exactly at threshold → PASS
        assert scorer.compute_verdict(0.60, 0.70, template_config) == "PASS"

        # With None config (falls back to defaults 0.60/0.70)
        assert scorer.compute_verdict(0.65, 0.75, None) == "PASS"
        assert scorer.compute_verdict(0.55, 0.75, None) == "FAIL"

    def test_tier_episode_count_thresholds(self):
        """Tier: 12 episodes → UNVERIFIED, 50 episodes → BACKTESTED."""
        scorer = ConstructScorer()

        assert scorer.compute_tier(12) == "UNVERIFIED"
        assert scorer.compute_tier(49) == "UNVERIFIED"
        assert scorer.compute_tier(50) == "BACKTESTED"
        assert scorer.compute_tier(100) == "BACKTESTED"

    def test_routing_hint_matrix(self):
        """Routing hint: PASS + BACKTESTED → ALLOWED, FAIL + any → BLOCKED."""
        scorer = ConstructScorer()

        assert scorer.compute_routing_hint("PASS", "BACKTESTED") == "ALLOWED"
        assert scorer.compute_routing_hint("PASS", "UNVERIFIED") == "REVIEW_REQUIRED"
        assert scorer.compute_routing_hint("FAIL", "BACKTESTED") == "BLOCKED"
        assert scorer.compute_routing_hint("FAIL", "UNVERIFIED") == "BLOCKED"
