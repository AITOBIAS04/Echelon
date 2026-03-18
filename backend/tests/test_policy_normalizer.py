"""Tests for PolicyNormalizer — claim classification, vagueness, tier cap.

Cycle 037: Contract-Backed Verification Infrastructure.
"""

from backend.services.spec_loader import ConstructSpec
from backend.services.policy_normalizer import normalize, _classify_claim


def _make_spec(domain_claims, refusals=None):
    """Helper to build a ConstructSpec for testing."""
    return ConstructSpec(
        slug="test",
        version="1.0.0",
        domain_claims=domain_claims,
        refusals=refusals or [],
        skill_manifest=[{"command": "/test", "domain": domain_claims[0]}],
        raw_yaml="test",
        spec_hash="sha256:test",
    )


class TestPolicyNormalizer:
    def test_precise_claim(self):
        claim = _classify_claim("Design Systems")
        assert claim["is_vague"] is False
        assert claim["matched_category"] == "design_systems"
        assert claim["original"] == "Design Systems"

    def test_vague_claim_broad_category(self):
        claim = _classify_claim("security")
        assert claim["is_vague"] is True
        assert claim["vagueness_reason"] == "broad_category"
        assert claim["matched_category"] is None

    def test_unrecognized_domain(self):
        claim = _classify_claim("quantum_cooking")
        assert claim["is_vague"] is True
        assert claim["vagueness_reason"] == "unrecognized_domain"

    def test_mixed_claims_tier_cap(self):
        spec = _make_spec(["Design Systems", "security", "Motion Design"])
        result = normalize(spec)
        assert result.tier_cap == "UNVERIFIED"
        assert result.has_vague_claims is True
        precise = [c for c in result.normalized_claims if not c["is_vague"]]
        vague = [c for c in result.normalized_claims if c["is_vague"]]
        assert len(precise) == 2
        assert len(vague) == 1

    def test_all_precise_no_tier_cap(self):
        spec = _make_spec(["Design Systems", "Motion Design", "Code Review"])
        result = normalize(spec)
        assert result.tier_cap is None
        assert result.has_vague_claims is False

    def test_refusals_extracted(self):
        spec = _make_spec(
            ["Design Systems"],
            refusals=[
                {"scope": "financial_advice", "reason": "Not licensed"},
                {"scope": "medical_diagnosis", "reason": "Out of domain"},
            ],
        )
        result = normalize(spec)
        assert len(result.explicit_refusals) == 2
        assert result.explicit_refusals[0]["scope"] == "financial_advice"
        assert result.explicit_refusals[1]["reason"] == "Out of domain"

    def test_empty_refusals(self):
        spec = _make_spec(["Design Systems"], refusals=[])
        result = normalize(spec)
        assert result.explicit_refusals == []

    def test_vague_term_in_compound_claim(self):
        claim = _classify_claim("AI Engineering")
        assert claim["is_vague"] is True
        assert claim["vagueness_reason"] == "broad_category"
