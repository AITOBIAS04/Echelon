"""Tests for SpecLoader — YAML parsing, hash stability, validation.

Cycle 037: Contract-Backed Verification Infrastructure.
"""

import pytest

from backend.services.spec_loader import load, compute_spec_hash


VALID_YAML = """
slug: artisan
version: "1.4.0"
domain_claims:
  - Design Systems
  - Motion Design
skill_manifest:
  - command: /inscribe
    domain: Design Systems
  - command: /animate
    domain: Motion Design
refusals:
  - scope: financial_advice
    reason: Not licensed
  - scope: medical_diagnosis
    reason: Out of domain
"""

VALID_YAML_NO_REFUSALS = """
slug: khole
version: "1.2.0"
domain_claims:
  - Investigation
skill_manifest:
  - command: /investigate
    domain: Investigation
"""


class TestSpecLoaderParsing:
    def test_parse_valid_yaml(self):
        spec = load(VALID_YAML)
        assert spec.slug == "artisan"
        assert spec.version == "1.4.0"
        assert spec.domain_claims == ["Design Systems", "Motion Design"]
        assert len(spec.skill_manifest) == 2
        assert spec.skill_manifest[0]["command"] == "/inscribe"
        assert spec.spec_hash.startswith("sha256:")

    def test_hash_stability(self):
        hash1 = compute_spec_hash(VALID_YAML)
        hash2 = compute_spec_hash(VALID_YAML)
        assert hash1 == hash2
        assert hash1.startswith("sha256:")
        assert len(hash1) > 10

    def test_refusals_extraction(self):
        spec = load(VALID_YAML)
        assert len(spec.refusals) == 2
        assert spec.refusals[0]["scope"] == "financial_advice"
        assert spec.refusals[1]["reason"] == "Out of domain"

    def test_missing_required_field(self):
        yaml_no_slug = """
version: "1.0.0"
domain_claims:
  - Testing
skill_manifest:
  - command: /test
    domain: Testing
"""
        with pytest.raises(ValueError, match="Missing required field: slug"):
            load(yaml_no_slug)

    def test_invalid_yaml_syntax(self):
        with pytest.raises(ValueError, match="Invalid YAML syntax"):
            load("{{invalid yaml: [")

    def test_empty_domain_claims(self):
        yaml_empty_claims = """
slug: test
version: "1.0.0"
domain_claims: []
skill_manifest:
  - command: /test
    domain: Testing
"""
        with pytest.raises(ValueError, match="domain_claims must be a non-empty list"):
            load(yaml_empty_claims)
