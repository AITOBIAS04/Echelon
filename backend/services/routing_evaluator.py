"""Deployability Routing Evaluator — Cycle-017 Policy Surface.

Computes routing hints for certificates based on configurable rules.
Each certificate receives one of: ALLOWED, REVIEW_REQUIRED, BLOCKED.

Rules are evaluated in priority order; first match wins.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RoutingHint(str, Enum):
    ALLOWED = "ALLOWED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RoutingDecision:
    hint: RoutingHint
    reason_code: str
    rule_name: str


@dataclass(frozen=True)
class RoutingPolicy:
    """Configurable thresholds for routing evaluation."""

    block_below_score: float = 0.3
    review_below_score: float = 0.6
    blocked_tiers: frozenset = field(
        default_factory=lambda: frozenset({"REJECTED"})
    )
    review_tiers: frozenset = field(
        default_factory=lambda: frozenset({"DRAFT", "CONTESTED"})
    )
    always_review_inquiry_classes: frozenset = field(
        default_factory=lambda: frozenset({"INVESTIGATIVE", "SCRUTINY"})
    )


class RoutingEvaluator:
    """Evaluates routing hints for certificates.

    Rules are evaluated in priority order. First matching rule wins.
    """

    def __init__(self, policy: Optional[RoutingPolicy] = None):
        self.policy = policy or RoutingPolicy()

    def evaluate(
        self,
        composite_score: float,
        verification_tier: str,
        inquiry_class: Optional[str] = None,
    ) -> RoutingDecision:
        """Evaluate routing for a certificate.

        Args:
            composite_score: The certificate's composite score (0-1).
            verification_tier: The verification tier string.
            inquiry_class: The inquiry class (COUNTERFACTUAL, INVESTIGATIVE, etc.).

        Returns:
            RoutingDecision with hint, reason_code, and rule_name.
        """
        # Rule 1: Blocked tiers
        if verification_tier in self.policy.blocked_tiers:
            return RoutingDecision(
                hint=RoutingHint.BLOCKED,
                reason_code=f"tier_{verification_tier.lower()}",
                rule_name="blocked_tier",
            )

        # Rule 2: Score below block threshold
        if composite_score < self.policy.block_below_score:
            return RoutingDecision(
                hint=RoutingHint.BLOCKED,
                reason_code=f"score_below_{self.policy.block_below_score}",
                rule_name="block_threshold",
            )

        # Rule 3: Review tiers
        if verification_tier in self.policy.review_tiers:
            return RoutingDecision(
                hint=RoutingHint.REVIEW_REQUIRED,
                reason_code=f"tier_{verification_tier.lower()}",
                rule_name="review_tier",
            )

        # Rule 4: Score below review threshold
        if composite_score < self.policy.review_below_score:
            return RoutingDecision(
                hint=RoutingHint.REVIEW_REQUIRED,
                reason_code=f"score_below_{self.policy.review_below_score}",
                rule_name="review_threshold",
            )

        # Rule 5: Always-review inquiry classes
        if inquiry_class and inquiry_class in self.policy.always_review_inquiry_classes:
            return RoutingDecision(
                hint=RoutingHint.REVIEW_REQUIRED,
                reason_code=f"inquiry_class_{inquiry_class.lower()}",
                rule_name="always_review_inquiry_class",
            )

        # Rule 6: Default — ALLOWED
        return RoutingDecision(
            hint=RoutingHint.ALLOWED,
            reason_code="default_pass",
            rule_name="default",
        )
