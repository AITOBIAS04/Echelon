"""CheckPlanner — Deterministic evaluation check plan from contract claims + available assets.

Cycle 037: Contract-Backed Verification Infrastructure.

Produces a sorted, reproducible list of PlannedCheck entries from:
1. RUBRIC checks: domains with registered rubric scorers
2. BENCHMARK checks: domains with matched benchmark datasets (future)
3. ANCHOR checks: fixed anchor classes (PUBLIC_STANDARD, DETERMINISTIC_CHECK)

Contract hash = SHA-256(spec_hash + canonical_checks_json)
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from backend.data.construct_rubrics import get_rubrics
from backend.services.policy_normalizer import NormalizationResult


@dataclass(frozen=True)
class PlannedCheck:
    """A single planned evaluation check."""
    check_id: str
    check_type: str  # RUBRIC | BENCHMARK | ANCHOR
    domain: str
    source: str
    critical: bool
    asset_id: Optional[str] = None
    anchor_class: Optional[str] = None


# Standard anchor classes applied to all constructs
_STANDARD_ANCHOR_CLASSES = [
    ("PUBLIC_STANDARD", True),       # Publicly verifiable standard
    ("DETERMINISTIC_CHECK", False),  # Deterministic reproducibility check
]


def plan_checks(
    slug: str,
    normalization_result: NormalizationResult,
    available_assets: Optional[dict] = None,
) -> list[PlannedCheck]:
    """Generate deterministic check plan from normalized claims and available assets.

    Args:
        slug: Construct slug for rubric lookup.
        normalization_result: Output from PolicyNormalizer.normalize().
        available_assets: Optional dict of available benchmark/anchor assets.
            Keys: "benchmarks" (list of {id, domain}), "anchors" (list of {id, class, domain}).

    Returns:
        Sorted list of PlannedCheck entries. Sort key: (check_type, domain, check_id).
    """
    assets = available_assets or {}
    checks: list[PlannedCheck] = []

    # 1. RUBRIC checks — for each precise domain that has a registered rubric
    rubrics = get_rubrics(slug)
    precise_claims = [
        c for c in normalization_result.normalized_claims if not c["is_vague"]
    ]

    for claim in precise_claims:
        domain = claim["domain"]
        matched = claim.get("matched_category", "")
        has_rubric = rubrics is not None and domain in (rubrics or {})
        checks.append(PlannedCheck(
            check_id=f"rubric:{slug}:{matched}",
            check_type="RUBRIC",
            domain=domain,
            source=f"rubric_registry:{slug}",
            critical=True,
            asset_id=f"rubric:{slug}:{matched}" if has_rubric else None,
        ))

    # 2. BENCHMARK checks — from available_assets["benchmarks"]
    benchmarks = assets.get("benchmarks", [])
    for benchmark in benchmarks:
        b_id = benchmark.get("id", "unknown")
        b_domain = benchmark.get("domain", "unknown")
        checks.append(PlannedCheck(
            check_id=f"benchmark:{b_id}",
            check_type="BENCHMARK",
            domain=b_domain,
            source=f"benchmark_dataset:{b_id}",
            critical=False,
            asset_id=b_id,
        ))

    # 3. ANCHOR checks — standard anchor classes
    for anchor_class, critical in _STANDARD_ANCHOR_CLASSES:
        checks.append(PlannedCheck(
            check_id=f"anchor:{anchor_class.lower()}",
            check_type="ANCHOR",
            domain="*",
            source=f"anchor_class:{anchor_class}",
            critical=critical,
            anchor_class=anchor_class,
        ))

    # Sort for determinism: (check_type, domain, check_id)
    checks.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return checks


def checks_to_dicts(checks: list[PlannedCheck]) -> list[dict]:
    """Convert PlannedCheck list to JSON-serializable dicts."""
    return [
        {
            "check_id": c.check_id,
            "check_type": c.check_type,
            "domain": c.domain,
            "source": c.source,
            "critical": c.critical,
            "asset_id": c.asset_id,
            "anchor_class": c.anchor_class,
        }
        for c in checks
    ]


def compute_contract_hash(spec_hash: str, planned_checks: list[PlannedCheck]) -> str:
    """Compute deterministic contract hash from spec_hash and planned checks.

    contract_hash = SHA-256(spec_hash + ":" + canonical_checks_json)
    """
    canonical = json.dumps(
        checks_to_dicts(planned_checks),
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = f"{spec_hash}:{canonical}"
    return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()}"
