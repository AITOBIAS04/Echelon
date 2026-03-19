"""TheatrePolicyRules — Theatre-specific domain registration and construct.json parsing.

Cycle 037d: Theatre Construct Verification.

Extends policy normalization with precise theatre sub-domains. Parses external
theatre construct.json files (TREMOR, CORONA) into structured metadata for the
theatre check planner.

Follows the same pattern as security_policy_rules.py (Cycle 037c).
"""

import json
from dataclasses import dataclass
from typing import Optional

from backend.services.policy_normalizer import KNOWN_PRECISE_DOMAINS


THEATRE_PRECISE_DOMAINS: set[str] = {
    "seismic_intelligence",
    "space_weather",
    "oracle_verification",
    "settlement_verification",
    "calibration_analysis",
    "prediction_markets",
    "evidence_bundles",
    "ground_truth_export",
    "rlmf_export",
    "theatre_management",
}


def register_theatre_domains() -> int:
    """Register theatre-specific precise domains with the policy normalizer.

    Mutates policy_normalizer.KNOWN_PRECISE_DOMAINS by adding theatre domains.
    Returns count of newly added domains (for logging/testing).
    """
    before = len(KNOWN_PRECISE_DOMAINS)
    KNOWN_PRECISE_DOMAINS.update(THEATRE_PRECISE_DOMAINS)
    return len(KNOWN_PRECISE_DOMAINS) - before


# ── construct.json Data Models ──────────────────────────────────────────


@dataclass(frozen=True)
class TheatreTemplate:
    """A single theatre template from construct.json."""
    id: str
    name: str
    resolution: str          # "binary" | "multi_bucket" | "multi_class"
    oracle: str              # oracle name or resolution method
    brier_type: Optional[str] = None  # "binary" | "multi_class"


@dataclass(frozen=True)
class OsintSource:
    """An OSINT data source from construct.json."""
    id: str
    name: str
    role: str                # "primary" | "cross_validation"


@dataclass(frozen=True)
class VerificationCheck:
    """A declared verification check from construct.json."""
    check: str
    ground_truth: str
    description: str


@dataclass(frozen=True)
class TheatreConstructMeta:
    """Parsed metadata from a theatre construct.json."""
    name: str
    theatre_templates: list[TheatreTemplate]
    osint_sources: list[OsintSource]
    verification_checks: list[VerificationCheck]
    settlement_tiers: list[dict]
    has_brier_scoring: bool
    has_cross_validation: bool
    oracle_names: list[str]


# ── construct.json Parser ───────────────────────────────────────────────


def parse_construct_json(raw_json: str) -> TheatreConstructMeta:
    """Parse a theatre construct.json into structured metadata.

    Handles both TREMOR-style (echelon.* nested) and CORONA-style
    (root-level) construct.json layouts.

    Raises ValueError on invalid JSON.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("construct.json must be a JSON object")

    name = data.get("name") or data.get("slug") or "unknown"
    echelon = data.get("echelon", {})
    rlmf = data.get("rlmf", {})

    # Theatre templates: TREMOR nests under echelon, CORONA at root
    raw_templates = echelon.get("theatre_templates") or data.get("theatre_templates", [])
    templates = []
    for t in raw_templates:
        # Resolution type: TREMOR uses "resolution" directly, CORONA uses "type"
        resolution = t.get("resolution") or t.get("type") or "binary"
        # Normalize CORONA's "resolution" field (which is actually the oracle)
        # TREMOR: resolution="binary", oracle="USGS reviewed catalog"
        # CORONA: type="binary", resolution="GOES X-ray + DONKI FLR"
        # Detect: if "type" exists, then "resolution" is the oracle
        if "type" in t:
            oracle = t.get("resolution", "")
            resolution = t["type"]
        else:
            oracle = t.get("oracle", "")

        templates.append(TheatreTemplate(
            id=t.get("id", ""),
            name=t.get("name", ""),
            resolution=resolution,
            oracle=oracle,
            brier_type=t.get("brier_type"),
        ))

    # OSINT sources: TREMOR uses echelon.osint_sources, CORONA uses data_sources
    raw_sources = echelon.get("osint_sources") or data.get("data_sources", [])
    sources = []
    for s in raw_sources:
        source_id = s.get("id") or s.get("name", "").lower().replace(" ", "_")
        source_name = s.get("name", "")
        source_role = s.get("role", "primary")
        sources.append(OsintSource(
            id=source_id,
            name=source_name,
            role=source_role,
        ))

    # Verification checks: TREMOR only (echelon.verification_checks)
    raw_checks = echelon.get("verification_checks", [])
    v_checks = []
    for vc in raw_checks:
        v_checks.append(VerificationCheck(
            check=vc.get("check", ""),
            ground_truth=vc.get("ground_truth", ""),
            description=vc.get("description", ""),
        ))

    # Settlement tiers: TREMOR only (echelon.settlement_tiers)
    settlement_tiers = echelon.get("settlement_tiers", [])

    # Derived: has_brier_scoring
    has_brier_from_templates = any(t.brier_type is not None for t in templates)
    rlmf_exports = rlmf.get("exports", [])
    has_brier_from_rlmf = "brier_score" in rlmf_exports
    has_brier_scoring = has_brier_from_templates or has_brier_from_rlmf

    # Derived: has_cross_validation
    has_cross_validation = any(s.role == "cross_validation" for s in sources)

    # Derived: oracle_names (deduplicated, ordered)
    seen_oracles: set[str] = set()
    oracle_names: list[str] = []
    for t in templates:
        if t.oracle and t.oracle not in seen_oracles:
            seen_oracles.add(t.oracle)
            oracle_names.append(t.oracle)

    return TheatreConstructMeta(
        name=str(name),
        theatre_templates=templates,
        osint_sources=sources,
        verification_checks=v_checks,
        settlement_tiers=settlement_tiers,
        has_brier_scoring=has_brier_scoring,
        has_cross_validation=has_cross_validation,
        oracle_names=oracle_names,
    )


# Register theatre domains at import time so they are available
# to the policy normalizer immediately.
_REGISTERED_COUNT = register_theatre_domains()
