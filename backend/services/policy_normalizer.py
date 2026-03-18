"""PolicyNormalizer — Validate domain claims, extract refusals, flag vagueness.

Cycle 037: Contract-Backed Verification Infrastructure.

Vague claims are accepted but tier-capped at UNVERIFIED. Precise claims pass through
uncapped. Classification uses snake_case normalization and allowlists.
"""

import re
from dataclasses import dataclass
from typing import Optional

from backend.services.spec_loader import ConstructSpec


KNOWN_PRECISE_DOMAINS: set[str] = {
    "design_systems",
    "motion_design",
    "visual_refinement",
    "taste_compounding",
    "frontend_best_practices",
    "code_generation",
    "code_review",
    "testing",
    "documentation",
    "api_design",
    "data_analysis",
    "investigation",
    "market_analysis",
    "risk_assessment",
    "accessibility",
    "performance_optimization",
    "database_design",
    "devops",
    "infrastructure",
}

KNOWN_VAGUE_TERMS: set[str] = {
    "security",
    "ai",
    "general",
    "everything",
    "all",
    "coding",
    "development",
    "engineering",
    "tech",
    "technology",
    "software",
    "programming",
}


@dataclass(frozen=True)
class NormalizationResult:
    """Result of normalizing a construct's domain claims and refusals."""
    normalized_claims: list[dict]
    explicit_refusals: list[dict]
    tier_cap: Optional[str]
    has_vague_claims: bool


def _to_snake_case(s: str) -> str:
    """Convert a string to snake_case."""
    s = s.strip()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    return s.lower().strip("_")


def _classify_claim(domain: str) -> dict:
    """Classify a single domain claim as precise or vague."""
    original = domain
    normalized = _to_snake_case(domain)

    if normalized in KNOWN_PRECISE_DOMAINS:
        return {
            "domain": domain,
            "original": original,
            "is_vague": False,
            "matched_category": normalized,
        }

    # Check if any token in the domain matches a known vague term
    tokens = set(normalized.split("_"))
    vague_matches = tokens & KNOWN_VAGUE_TERMS
    if vague_matches:
        return {
            "domain": domain,
            "original": original,
            "is_vague": True,
            "matched_category": None,
            "vagueness_reason": "broad_category",
        }

    # No match in either set
    return {
        "domain": domain,
        "original": original,
        "is_vague": True,
        "matched_category": None,
        "vagueness_reason": "unrecognized_domain",
    }


def normalize(spec: ConstructSpec) -> NormalizationResult:
    """Normalize a construct's claims and refusals.

    Returns NormalizationResult with classified claims, extracted refusals,
    and tier_cap if any vague claims detected.
    """
    normalized_claims = [_classify_claim(domain) for domain in spec.domain_claims]
    has_vague = any(c["is_vague"] for c in normalized_claims)
    tier_cap = "UNVERIFIED" if has_vague else None

    # Extract refusals from spec (already parsed by SpecLoader)
    explicit_refusals = []
    for r in spec.refusals:
        if isinstance(r, dict) and "scope" in r:
            explicit_refusals.append({
                "scope": str(r["scope"]),
                "reason": str(r.get("reason", "")),
            })

    return NormalizationResult(
        normalized_claims=normalized_claims,
        explicit_refusals=explicit_refusals,
        tier_cap=tier_cap,
        has_vague_claims=has_vague,
    )
