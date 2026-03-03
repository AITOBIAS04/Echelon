"""Corroboration Engine — Stage 2 of the evidence pipeline.

Separates primary from secondary evidence by resolution_role,
deduplicates by independence_upstream_id, counts distinct source_groups,
evaluates corroboration_minimum_met. Produces audit trail of dedup decisions.

011 constraint — provisional corroboration:
    All 3 WM endpoints share independence_upstream_id: "worldmonitor".
    After dedup, only 1 entry remains. corroboration_met is always false.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.osint.models.evidence import CollectionResult, EvidenceBundle
from backend.osint.models.registry import RegistryLoader


@dataclass
class CorroborationResult:
    """Output of the corroboration evaluation stage.

    Carries the primary/corroborating bundle separation, distinct
    upstream source counts, corroboration verdict, and an audit trail
    of every dedup decision.
    """

    theatre_id: str
    primary_bundles: list[EvidenceBundle]
    corroborating_bundles: list[EvidenceBundle]
    distinct_source_groups: int
    corroboration_minimum: int
    corroboration_met: bool
    dedup_log: list[str] = field(default_factory=list)


class CorroborationEngine:
    """Stage 2: evaluate evidence independence and corroboration.

    Groups CollectionResults by independence_upstream_id from the
    registry. Bundles sharing the same upstream_id are NOT independent
    and are deduplicated (strongest confidence retained). The remaining
    distinct groups are counted against the corroboration minimum.
    """

    def __init__(self, registry_loader: RegistryLoader) -> None:
        self._registry = registry_loader

    def evaluate(
        self,
        results: list[CollectionResult],
        oracle_config: dict,
    ) -> CorroborationResult:
        """Full corroboration evaluation.

        1. Filter to successful results with valid bundles.
        2. Separate primary from secondary bundles by resolution_role.
        3. Deduplicate by independence_upstream_id (keep strongest confidence).
        4. Count distinct source groups after dedup.
        5. Compare against corroboration_minimum from oracle_config.

        Args:
            results: CollectionResult list from CollectionRunner.
            oracle_config: Theatre oracle config dict. Must contain
                ``corroboration_minimum`` (int, default 2).

        Returns:
            CorroborationResult with verdict and audit trail.
        """
        theatre_id = oracle_config.get("theatre_id", "unknown")
        corroboration_minimum = oracle_config.get("corroboration_minimum", 2)

        # Filter to successful results with bundles
        successful = [r for r in results if r.success and r.bundle is not None]

        # Separate by resolution_role
        primary: list[EvidenceBundle] = []
        secondary: list[EvidenceBundle] = []
        for result in successful:
            bundle = result.bundle
            role = self._get_resolution_role(bundle)
            if role == "primary_evidence":
                primary.append(bundle)
            else:
                secondary.append(bundle)

        # Deduplicate primary bundles by independence_upstream_id
        deduped_primary, dedup_log = self.deduplicate_by_upstream_id(primary)

        # Deduplicate secondary bundles by independence_upstream_id
        deduped_secondary, dedup_log_sec = self.deduplicate_by_upstream_id(secondary)
        dedup_log.extend(dedup_log_sec)

        # Count distinct source groups after dedup (across primary + secondary)
        all_deduped = deduped_primary + deduped_secondary
        distinct_groups: set[str] = set()
        for bundle in all_deduped:
            upstream_id = self._get_upstream_id(bundle)
            distinct_groups.add(upstream_id)

        distinct_count = len(distinct_groups)
        corroboration_met = distinct_count >= corroboration_minimum

        return CorroborationResult(
            theatre_id=theatre_id,
            primary_bundles=deduped_primary,
            corroborating_bundles=deduped_secondary,
            distinct_source_groups=distinct_count,
            corroboration_minimum=corroboration_minimum,
            corroboration_met=corroboration_met,
            dedup_log=dedup_log,
        )

    def deduplicate_by_upstream_id(
        self,
        bundles: list[EvidenceBundle],
    ) -> tuple[list[EvidenceBundle], list[str]]:
        """Collapse bundles sharing independence_upstream_id.

        Keeps the entry with highest normalised_event.confidence per
        upstream_id group. Produces audit log entries for each dedup
        decision.

        Args:
            bundles: List of EvidenceBundle to deduplicate.

        Returns:
            Tuple of (deduplicated bundles, dedup log entries).
        """
        dedup_log: list[str] = []
        groups: dict[str, list[EvidenceBundle]] = {}

        for bundle in bundles:
            upstream_id = self._get_upstream_id(bundle)
            if upstream_id not in groups:
                groups[upstream_id] = []
            groups[upstream_id].append(bundle)

        deduped: list[EvidenceBundle] = []
        for upstream_id, group in groups.items():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                # Keep strongest confidence
                best = max(group, key=lambda b: b.normalised_event.confidence)
                deduped.append(best)
                dropped = [
                    b.source_id for b in group if b is not best
                ]
                dedup_log.append(
                    f"upstream_id={upstream_id}: kept {best.source_id} "
                    f"(confidence={best.normalised_event.confidence:.3f}), "
                    f"dropped {dropped}"
                )

        return deduped, dedup_log

    def _get_upstream_id(self, bundle: EvidenceBundle) -> str:
        """Resolve independence_upstream_id from registry or fall back to source_id."""
        source = self._registry.get_source(bundle.source_id)
        if source is not None:
            return source.independence_upstream_id
        return bundle.source_id

    def _get_resolution_role(self, bundle: EvidenceBundle) -> str:
        """Resolve resolution_role from registry or fall back to bundle field."""
        source = self._registry.get_source(bundle.source_id)
        if source is not None:
            return source.resolution_role
        return bundle.resolution_role
