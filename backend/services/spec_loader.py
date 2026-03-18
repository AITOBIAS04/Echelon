"""SpecLoader — Parse construct.yaml content into normalized ConstructSpec.

Cycle 037: Contract-Backed Verification Infrastructure.
"""

import hashlib
import json
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class ConstructSpec:
    """Normalized construct specification parsed from YAML."""
    slug: str
    version: str
    domain_claims: list[str]
    refusals: list[dict]
    skill_manifest: list[dict]
    raw_yaml: str
    spec_hash: str


def compute_spec_hash(yaml_content: str) -> str:
    """Compute deterministic SHA-256 hash of normalized YAML content."""
    parsed = yaml.safe_load(yaml_content)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"


def load(yaml_content: str) -> ConstructSpec:
    """Parse YAML content into a validated ConstructSpec.

    Raises ValueError on missing required fields, invalid YAML, or empty domain_claims.
    """
    try:
        parsed = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}") from e

    if not isinstance(parsed, dict):
        raise ValueError("YAML content must be a mapping")

    # Required fields
    for field in ("slug", "version", "domain_claims", "skill_manifest"):
        if field not in parsed:
            raise ValueError(f"Missing required field: {field}")

    slug = parsed["slug"]
    version = parsed["version"]
    domain_claims = parsed["domain_claims"]
    skill_manifest = parsed["skill_manifest"]

    if not isinstance(domain_claims, list) or len(domain_claims) == 0:
        raise ValueError("domain_claims must be a non-empty list")

    if not isinstance(skill_manifest, list) or len(skill_manifest) == 0:
        raise ValueError("skill_manifest must be a non-empty list")

    # Optional fields
    refusals = parsed.get("refusals", [])
    if not isinstance(refusals, list):
        refusals = []

    spec_hash = compute_spec_hash(yaml_content)

    return ConstructSpec(
        slug=str(slug),
        version=str(version),
        domain_claims=[str(c) for c in domain_claims],
        refusals=refusals,
        skill_manifest=skill_manifest,
        raw_yaml=yaml_content,
        spec_hash=spec_hash,
    )
