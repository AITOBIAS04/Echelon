"""Deterministic Artefact Writers — canonical JSON serialisation with SHA-256 hashing.

Supports all 9 artefact types produced by the investigation toolset:
deltabrief, scanner_manifest, entity_profile, evidence_manifest,
corroboration_results, counter_signals, claim_graph, drift_events, market_summary.

Same inputs → byte-identical output (uses canonical_json for deterministic ordering).
"""

from __future__ import annotations

import hashlib

from backend.utils.canonical_json import canonical_json


# Supported artefact types
ARTEFACT_TYPES = frozenset({
    "deltabrief",
    "scanner_manifest",
    "entity_profile",
    "evidence_manifest",
    "corroboration_results",
    "counter_signals",
    "claim_graph",
    "drift_events",
    "market_summary",
})


def write_artifact(name: str, data: dict) -> tuple[str, str]:
    """Serialise an artefact to canonical JSON and compute its SHA-256 hash.

    Args:
        name: Artefact type name (must be one of ARTEFACT_TYPES).
        data: Artefact data as a dict.

    Returns:
        (json_string, sha256_hash) — the canonical JSON string and its SHA-256 hex digest.

    Raises:
        ValueError: If name is not a recognised artefact type.
    """
    if name not in ARTEFACT_TYPES:
        raise ValueError(
            f"Unknown artefact type: {name}. "
            f"Must be one of: {sorted(ARTEFACT_TYPES)}"
        )

    json_string = canonical_json(data)
    sha256_hash = hashlib.sha256(json_string.encode()).hexdigest()

    return json_string, sha256_hash
