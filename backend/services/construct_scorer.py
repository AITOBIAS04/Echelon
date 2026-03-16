"""Construct Scorer — rubric scoring engine and composite aggregation.

Scores captured outputs against committed rubrics. Each domain has a registered
rubric function. Aggregation pipeline: episode → domain → composite → verdict.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default thresholds (used when template_config_json is NULL)
_DEFAULT_VERDICT_THRESHOLD = 0.60
_DEFAULT_COVERAGE_THRESHOLD = 0.70


class ConstructScorer:
    """Scores construct episodes and computes aggregates + verdicts.

    Domain rubrics are callables: (skill_command, domain, prompt_text, output_text) -> dict[str, float]
    """

    def __init__(self, rubrics: Optional[dict[str, callable]] = None):
        self._rubrics = rubrics or {}

    def score_episode(
        self,
        skill_command: str,
        domain: str,
        prompt_text: str,
        output_text: str,
    ) -> dict[str, float]:
        """Apply domain rubric to a single episode output.

        Returns dict of criteria -> score (0.0–1.0).
        If no rubric registered for domain, returns empty scores.
        """
        rubric_fn = self._rubrics.get(domain)
        if rubric_fn is None:
            logger.warning("No rubric registered for domain '%s'", domain)
            return {}

        return rubric_fn(skill_command, domain, prompt_text, output_text)

    def aggregate_domain(
        self,
        episode_scores: list[dict[str, float]],
        domain: str,
    ) -> float:
        """Compute mean score across episodes within a domain.

        Averages all criteria scores within each episode, then averages
        across episodes.
        """
        if not episode_scores:
            return 0.0

        episode_means = []
        for scores in episode_scores:
            if scores:
                episode_means.append(sum(scores.values()) / len(scores))

        if not episode_means:
            return 0.0

        return sum(episode_means) / len(episode_means)

    def aggregate_composite(
        self,
        domain_scores: dict[str, float],
        weights: Optional[dict[str, float]] = None,
    ) -> float:
        """Compute weighted mean of domain scores.

        In V1, all domains have equal weight (weights=None).
        """
        if not domain_scores:
            return 0.0

        if weights is None:
            # Equal weights
            return sum(domain_scores.values()) / len(domain_scores)

        total_weight = sum(weights.get(d, 1.0) for d in domain_scores)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            score * weights.get(d, 1.0)
            for d, score in domain_scores.items()
        )
        return weighted_sum / total_weight

    def compute_skill_coverage(
        self,
        declared_skills: list[dict],
        tested_skills: set[str],
    ) -> float:
        """Compute ratio of skills with ≥1 episode / total declared skills.

        Args:
            declared_skills: registration.skill_manifest entries (list of {command, domain})
            tested_skills: set of unique skill_command values from evidence items
        """
        if not declared_skills:
            return 0.0

        unique_declared = {e["command"] for e in declared_skills}
        covered = unique_declared & tested_skills
        return len(covered) / len(unique_declared)

    def compute_verdict(
        self,
        composite: float,
        skill_coverage: float,
        template_config: Optional[dict] = None,
    ) -> str:
        """Compute PASS/FAIL verdict against template thresholds.

        Reads thresholds from template_config_json. Falls back to defaults
        if template_config is None (legacy templates).

        PASS requires BOTH:
        - composite >= verdict_threshold
        - skill_coverage >= coverage_threshold
        """
        config = template_config or {}
        verdict_threshold = config.get("verdict_threshold", _DEFAULT_VERDICT_THRESHOLD)
        coverage_threshold = config.get("coverage_threshold", _DEFAULT_COVERAGE_THRESHOLD)

        if composite >= verdict_threshold and skill_coverage >= coverage_threshold:
            return "PASS"
        return "FAIL"

    def compute_tier(self, episode_count: int) -> str:
        """Compute verification tier based on episode count.

        - < 50 episodes → UNVERIFIED
        - >= 50 episodes → BACKTESTED
        - PROVEN requires 3 months production telemetry (not achievable in V1)
        """
        if episode_count >= 50:
            return "BACKTESTED"
        return "UNVERIFIED"

    def compute_routing_hint(self, verdict: str, tier: str) -> str:
        """Compute Hounfour routing hint from verdict + tier.

        - PASS + BACKTESTED → ALLOWED
        - PASS + UNVERIFIED → REVIEW_REQUIRED
        - FAIL + any → BLOCKED
        """
        if verdict == "FAIL":
            return "BLOCKED"
        if verdict == "PASS" and tier == "BACKTESTED":
            return "ALLOWED"
        return "REVIEW_REQUIRED"
