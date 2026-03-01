"""
Evidence scoring engine — applies multiplicative penalties per source.

Replaces the old BaseCollector.should_cap_confidence() / FREE_SOURCE_CONFIDENCE_CAP
approach with a structured, auditable scoring model.

Penalties:
- Revision policy: immutable (1.0), as_of_timestamp (0.95), latest_only (0.80)
- Rate-limit instability: 0.90 when source has unstable rate-limit policy
- Receipt at minimum (not exceeding): 0.95
- Single-source cap: 0.95 (composite_confidence can exceed this)
"""

from __future__ import annotations

import math
from typing import Any

from osint_pipeline.models.evidence import (
    EvidenceBundle,
    ReceiptMode,
    meets_receipt_minimum,
)
from osint_pipeline.models.registry import RegistrySource


class EvidenceScorer:
    """Score individual evidence bundles and compute composite confidence."""

    # Revision policy penalties (multiplicative).
    REVISION_PENALTY: dict[str, float] = {
        "immutable": 1.0,
        "as_of_timestamp": 0.95,
        "latest_only": 0.80,
    }

    # Applied when the registry source has an unstable rate-limit policy.
    RATE_LIMIT_INSTABILITY_PENALTY: float = 0.90

    # Applied when the bundle's receipt mode merely meets (but does not
    # exceed) the registry minimum.
    RECEIPT_AT_MINIMUM_PENALTY: float = 0.95

    # No single source can exceed this confidence score.
    SINGLE_SOURCE_CAP: float = 0.95

    def score_bundle(
        self,
        bundle: EvidenceBundle,
        registry_source: RegistrySource | None = None,
    ) -> float:
        """Score a single evidence bundle, applying multiplicative penalties.

        Returns a float in [0.0, 0.95].
        """
        score = bundle.confidence_score

        if registry_source is not None:
            # Revision policy penalty
            revision = registry_source.revision_policy
            penalty = self.REVISION_PENALTY.get(revision, 0.80)
            score *= penalty

            # Rate-limit instability penalty
            if self._is_rate_limited_unstable(registry_source):
                score *= self.RATE_LIMIT_INSTABILITY_PENALTY

            # Receipt at minimum (not exceeding) penalty
            if not self._receipt_exceeds_minimum(bundle, registry_source):
                score *= self.RECEIPT_AT_MINIMUM_PENALTY

        # Single-source cap
        return min(score, self.SINGLE_SOURCE_CAP)

    def composite_confidence(
        self, scored_bundles: list[tuple[EvidenceBundle, float]]
    ) -> float:
        """Compute composite confidence from multiple scored bundles.

        Uses the formula: 1 - product(1 - score_i).
        This CAN exceed SINGLE_SOURCE_CAP when multiple independent
        sources corroborate.
        """
        if not scored_bundles:
            return 0.0
        product = math.prod(1.0 - score for _, score in scored_bundles)
        return 1.0 - product

    @staticmethod
    def _is_rate_limited_unstable(registry_source: RegistrySource) -> bool:
        """Check if the registry source has an unstable rate-limit policy.

        Looks for 'unstable' in the rate_limit_policy field if present.
        """
        rate_limit_policy = getattr(registry_source, "rate_limit_policy", None)
        if rate_limit_policy is None:
            return False
        return "unstable" in str(rate_limit_policy).lower()

    @staticmethod
    def _receipt_exceeds_minimum(
        bundle: EvidenceBundle, registry_source: RegistrySource
    ) -> bool:
        """Check if the bundle's receipt mode strictly exceeds the registry minimum.

        Returns True only when the produced mode is ABOVE the minimum,
        not merely equal to it.
        """
        from osint_pipeline.models.evidence import RECEIPT_MODE_ORDER

        minimum = ReceiptMode(registry_source.receipt_mode_minimum)
        produced = bundle.receipt_mode
        produced_idx = RECEIPT_MODE_ORDER.index(produced)
        minimum_idx = RECEIPT_MODE_ORDER.index(minimum)
        return produced_idx > minimum_idx
