"""Eval Asset Classification Policy.

Classifies assets as snapshot (R2-eligible) or live-only.
Rejects attempts to treat live feeds as immutable ground truth.
Used by the construct evidence anchoring pipeline (Cycle-026a).
"""

from enum import Enum
from typing import Literal


class AssetDisposition(str, Enum):
    """Result of classifying an asset."""

    SNAPSHOT = "snapshot"
    LIVE = "live"
    UNKNOWN = "unknown"


# ── Allowlists / Denylists ──────────────────────────────────────────

SNAPSHOT_ASSETS: frozenset[str] = frozenset({
    "humaneval",
    "mbpp",
    "hellaswag",
    "mmlu",
    "mmlu-pro",
    "swe-bench-verified",
    "wcag",
    "aria-apg",
    "react-docs",
    "tailwind-docs",
    "owasp-top10",
    "cwe-subset",
    "arxiv-ml-metadata",
    # ── Cycle-026c: User Research + Journey Anchors ──
    "user-research-methods",
    "journey-patterns",
    "recovery-guidance",
})

LIVE_ONLY_ASSETS: frozenset[str] = frozenset({
    "sec-edgar",
    "ofac",
    "un-sanctions",
    "gdelt",
    "global-fishing-watch",
    "semantic-scholar",
})


# ── Classification ───────────────────────────────────────────────────

def classify_asset(asset_id: str) -> AssetDisposition:
    """Classify an asset as snapshot, live, or unknown.

    Returns:
        AssetDisposition.SNAPSHOT if the asset is on the snapshot allowlist.
        AssetDisposition.LIVE if the asset is on the live-only denylist.
        AssetDisposition.UNKNOWN if the asset is not recognized.
    """
    normalized = asset_id.strip().lower()
    if normalized in SNAPSHOT_ASSETS:
        return AssetDisposition.SNAPSHOT
    if normalized in LIVE_ONLY_ASSETS:
        return AssetDisposition.LIVE
    return AssetDisposition.UNKNOWN


def is_r2_eligible(asset_id: str) -> bool:
    """Check whether an asset is eligible for R2 snapshot storage.

    Only assets on the snapshot allowlist may be stored in R2 as
    immutable evaluation inputs.
    """
    return classify_asset(asset_id) == AssetDisposition.SNAPSHOT


def validate_snapshot_candidate(asset_id: str) -> tuple[bool, str]:
    """Validate that an asset can be treated as a snapshot.

    Returns (ok, reason) tuple.
    - (True, "accepted") if the asset is a valid snapshot candidate.
    - (False, reason) if the asset is live-only or unknown.
    """
    disposition = classify_asset(asset_id)

    if disposition == AssetDisposition.SNAPSHOT:
        return True, "accepted"

    if disposition == AssetDisposition.LIVE:
        return False, (
            f"Asset '{asset_id}' is classified as live-only and must not be "
            f"treated as immutable ground truth. Use a live collector instead."
        )

    return False, (
        f"Asset '{asset_id}' is not recognized. Add it to SNAPSHOT_ASSETS "
        f"or LIVE_ONLY_ASSETS before use."
    )


def reject_live_as_immutable(asset_id: str) -> None:
    """Raise ValueError if a live-only asset is being treated as immutable.

    This is the enforcement gate: call it before writing any asset
    into R2 or generating a snapshot manifest for it.
    """
    disposition = classify_asset(asset_id)
    if disposition == AssetDisposition.LIVE:
        raise ValueError(
            f"Policy violation: '{asset_id}' is a live-only asset and must not "
            f"be snapshotted into R2. Live feeds must remain API/collector-driven."
        )
