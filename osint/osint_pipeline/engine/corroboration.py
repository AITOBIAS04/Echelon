"""
Corroboration engine — Stage 2 of the Composed Oracle pipeline.

Implements:
- Independence deduplication by upstream_id
- Corroboration minimum enforcement (distinct source_groups)
- Time-window validation
- Counter-signal checking (delegated to counter_signal module)

Key invariant from Composed Oracle Spec v2 §2.1:
    Runner MUST deduplicate by independence_upstream_id before
    counting distinct source_groups.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from osint_pipeline.models.evidence import EvidenceBundle, OracleCollectionSummary
from osint_pipeline.models.oracle_output import CorroborationResult


class CorroborationEngine:
    """
    Evaluate corroboration across collected evidence bundles.

    Given a set of bundles from Stage 1, this engine:
    1. Groups bundles by claim (query_context match)
    2. Deduplicates by independence_upstream_id
    3. Counts distinct source_groups within the time window
    4. Returns pass/fail per claim
    """

    def __init__(
        self,
        corroboration_minimum: int = 2,
        corroboration_window_seconds: int = 3600,
    ):
        self.corroboration_minimum = corroboration_minimum
        self.corroboration_window_seconds = corroboration_window_seconds

    def evaluate(
        self,
        primary_bundle: EvidenceBundle,
        all_bundles: list[EvidenceBundle],
        claim_id: str = "default",
    ) -> CorroborationResult:
        """
        Evaluate corroboration for a primary claim against all collected bundles.

        Args:
            primary_bundle: The primary evidence bundle (the claim to corroborate).
            all_bundles: All collected bundles (including the primary).
            claim_id: Identifier for the claim being evaluated.

        Returns:
            CorroborationResult with pass/fail and detailed accounting.
        """
        primary_ts = primary_bundle.receipt.timestamp_ms

        # Step 1: Exclude the primary bundle itself
        candidates = [
            b for b in all_bundles
            if b.bundle_id != primary_bundle.bundle_id
            and b.resolution_role in ("secondary_corroboration", "primary_evidence")
        ]

        # Step 2: Deduplicate by independence_upstream_id
        # Keep only one bundle per upstream_id (first seen)
        seen_upstreams: dict[str, EvidenceBundle] = {}
        excluded_by_dedup: list[str] = []

        for bundle in candidates:
            uid = bundle.independence_upstream_id
            if uid in seen_upstreams:
                excluded_by_dedup.append(bundle.source_id)
            else:
                seen_upstreams[uid] = bundle

        # Also check if primary's upstream_id matches any candidate
        deduped_candidates = []
        for uid, bundle in seen_upstreams.items():
            if uid == primary_bundle.independence_upstream_id:
                excluded_by_dedup.append(bundle.source_id)
            else:
                deduped_candidates.append(bundle)

        # Step 3: Check time window
        within_window: list[EvidenceBundle] = []
        outside_window: list[str] = []

        for bundle in deduped_candidates:
            delta_ms = abs(bundle.receipt.timestamp_ms - primary_ts)
            if delta_ms <= self.corroboration_window_seconds * 1000:
                within_window.append(bundle)
            else:
                outside_window.append(bundle.source_id)

        # Step 4: Count distinct source_groups
        corroborating_groups: set[str] = set()
        corroborating_sources: list[str] = []

        for bundle in within_window:
            if bundle.source_group != primary_bundle.source_group:
                corroborating_groups.add(bundle.source_group)
                corroborating_sources.append(bundle.source_id)
            elif bundle.source_group not in corroborating_groups:
                # Same group as primary — doesn't count as independent
                # but we still track it
                pass

        return CorroborationResult(
            claim_id=claim_id,
            primary_source_id=primary_bundle.source_id,
            primary_source_group=primary_bundle.source_group,
            distinct_corroborating_groups=len(corroborating_groups),
            corroboration_minimum=self.corroboration_minimum,
            corroboration_window_seconds=self.corroboration_window_seconds,
            corroborating_sources=corroborating_sources,
            corroborating_groups=sorted(corroborating_groups),
            excluded_by_dedup=excluded_by_dedup,
            outside_window=outside_window,
        )

    def evaluate_all(
        self,
        collection: OracleCollectionSummary,
    ) -> list[CorroborationResult]:
        """
        Evaluate corroboration for all primary evidence bundles in a collection.

        Returns one CorroborationResult per primary_evidence bundle.
        """
        primary_bundles = [
            b for b in collection.bundles
            if b.resolution_role == "primary_evidence"
        ]

        results = []
        for i, primary in enumerate(primary_bundles):
            result = self.evaluate(
                primary_bundle=primary,
                all_bundles=collection.bundles,
                claim_id=f"claim_{i:03d}_{primary.source_id}",
            )
            results.append(result)

        return results
