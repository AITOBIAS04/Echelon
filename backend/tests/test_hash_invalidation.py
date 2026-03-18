"""Tests for hash invalidation chain — spec change → supersession → run rejection.

Cycle 037: Contract-Backed Verification Infrastructure.

Tests the pure-logic hash chain without DB/asyncpg dependency.
"""

from backend.services.spec_loader import load as load_spec, compute_spec_hash
from backend.services.policy_normalizer import normalize
from backend.services.check_planner import plan_checks, compute_contract_hash


YAML_V1 = """
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
"""

YAML_V2 = """
slug: artisan
version: "1.4.0"
domain_claims:
  - Design Systems
  - Motion Design
  - Visual Refinement
skill_manifest:
  - command: /inscribe
    domain: Design Systems
  - command: /animate
    domain: Motion Design
  - command: /refine
    domain: Visual Refinement
"""


class TestHashInvalidation:
    def test_spec_change_produces_new_hash(self):
        """Spec content change → new spec_hash → old contract should be SUPERSEDED."""
        hash_v1 = compute_spec_hash(YAML_V1)
        hash_v2 = compute_spec_hash(YAML_V2)

        assert hash_v1 != hash_v2
        assert hash_v1.startswith("sha256:")
        assert hash_v2.startswith("sha256:")

    def test_check_plan_change_new_contract_hash(self):
        """New asset available → new check plan → new contract_hash."""
        spec = load_spec(YAML_V1)
        norm = normalize(spec)

        # Plan without benchmarks
        checks_v1 = plan_checks(spec.slug, norm)
        hash_v1 = compute_contract_hash(spec.spec_hash, checks_v1)

        # Plan with benchmark added
        checks_v2 = plan_checks(
            spec.slug, norm,
            available_assets={"benchmarks": [{"id": "humaneval", "domain": "Design Systems"}]}
        )
        hash_v2 = compute_contract_hash(spec.spec_hash, checks_v2)

        assert hash_v1 != hash_v2

    def test_superseded_contract_hash_differs(self):
        """Run against SUPERSEDED contract would be rejected because hashes differ."""
        # Old contract from v1
        spec_v1 = load_spec(YAML_V1)
        norm_v1 = normalize(spec_v1)
        checks_v1 = plan_checks(spec_v1.slug, norm_v1)
        old_hash = compute_contract_hash(spec_v1.spec_hash, checks_v1)

        # New contract from v2 (would supersede old)
        spec_v2 = load_spec(YAML_V2)
        norm_v2 = normalize(spec_v2)
        checks_v2 = plan_checks(spec_v2.slug, norm_v2)
        new_hash = compute_contract_hash(spec_v2.spec_hash, checks_v2)

        # Hashes differ → old contract is SUPERSEDED
        assert old_hash != new_hash

        # A run holding old_hash would fail validate_contract_active
        # (the contract with old_hash is now SUPERSEDED, not ACTIVE)

    def test_certificate_references_immutable_contract_hash(self):
        """Contract hash is computed at creation and immutable thereafter."""
        spec = load_spec(YAML_V1)
        norm = normalize(spec)
        checks = plan_checks(spec.slug, norm)

        # Compute contract hash at creation time
        original_hash = compute_contract_hash(spec.spec_hash, checks)

        # Recomputing from same inputs gives identical result
        recomputed = compute_contract_hash(spec.spec_hash, checks)
        assert recomputed == original_hash

        # New spec would produce a DIFFERENT hash (new contract)
        spec_v2 = load_spec(YAML_V2)
        norm_v2 = normalize(spec_v2)
        checks_v2 = plan_checks(spec_v2.slug, norm_v2)
        new_hash = compute_contract_hash(spec_v2.spec_hash, checks_v2)

        assert new_hash != original_hash
        # But the certificate stores original_hash — it's immutable
