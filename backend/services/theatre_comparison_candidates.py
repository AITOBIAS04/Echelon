"""Candidate-set generator — identifies comparable theatre bundle pairs.

Cycle 038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

Generates same-event and overlap-scope comparison candidates from
normalized ExecutedTheatreComparisonBundle instances per SDD §2.3.
"""

from itertools import combinations
from typing import Optional

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
)


def generate_candidates(
    bundles: list[ExecutedTheatreComparisonBundle],
) -> list[ComparisonCandidateSet]:
    """Generate comparison candidates from a set of bundles.

    For each distinct-construct pair:
    1. Same-event matching on shared event_keys
    2. Overlap-scope matching (only if no same-event match)
    3. Same-construct pairs are skipped

    Returns list of ComparisonCandidateSet ordered by candidate_type.
    """
    candidates: list[ComparisonCandidateSet] = []

    for bundle_a, bundle_b in combinations(bundles, 2):
        # Skip same-construct pairs
        if bundle_a.construct_slug == bundle_b.construct_slug:
            continue

        # Try same-event matching first
        same_event = _match_same_event(bundle_a, bundle_b)
        if same_event is not None:
            candidates.append(same_event)
            continue

        # Fall back to overlap-scope matching
        overlap_scope = _match_overlap_scope(bundle_a, bundle_b)
        if overlap_scope is not None:
            candidates.append(overlap_scope)

    return candidates


def _match_same_event(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ComparisonCandidateSet]:
    """Match bundles by shared event keys.

    Match strength:
    - EXACT: all event keys shared (both sides identical sets)
    - PARTIAL: some but not all event keys shared
    """
    events_a = set(bundle_a.event_keys)
    events_b = set(bundle_b.event_keys)
    shared = events_a & events_b

    if not shared:
        return None

    all_events = events_a | events_b
    strength = "EXACT" if shared == all_events else "PARTIAL"

    return ComparisonCandidateSet(
        candidate_type="same_event",
        bundle_a=bundle_a,
        bundle_b=bundle_b,
        matching_keys=sorted(shared),
        match_strength=strength,
    )


def _match_overlap_scope(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ComparisonCandidateSet]:
    """Match bundles by shared scope keys (normalized).

    Uses TheatreScopeKey.key() for normalized comparison to prevent
    case-mismatch false negatives (SDD §4.4).

    Match strength:
    - EXACT: all scope keys shared (both sides identical sets)
    - PARTIAL: >50% of the union is shared
    - WEAK: ≤50% of the union is shared
    """
    scopes_a = {sk.key() for sk in bundle_a.scope_keys}
    scopes_b = {sk.key() for sk in bundle_b.scope_keys}
    shared = scopes_a & scopes_b

    if not shared:
        return None

    all_scopes = scopes_a | scopes_b
    ratio = len(shared) / len(all_scopes)

    if shared == all_scopes:
        strength = "EXACT"
    elif ratio > 0.5:
        strength = "PARTIAL"
    else:
        strength = "WEAK"

    return ComparisonCandidateSet(
        candidate_type="overlap_scope",
        bundle_a=bundle_a,
        bundle_b=bundle_b,
        matching_keys=sorted(shared),
        match_strength=strength,
    )
