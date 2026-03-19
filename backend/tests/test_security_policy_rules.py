"""Tests for SecurityPolicyRules — security domain registration + reference extraction.

Cycle 037c: Security + Domain Pack Verification.
"""

import pytest

from backend.services.domain_pack_loader import CorpusSkill
from backend.services.policy_normalizer import (
    KNOWN_PRECISE_DOMAINS,
    KNOWN_VAGUE_TERMS,
    _classify_claim,
    normalize,
)
from backend.services.security_policy_rules import (
    SECURITY_PRECISE_DOMAINS,
    classify_security_claim,
    extract_security_references,
    register_security_domains,
)
from backend.services.spec_loader import ConstructSpec


# ── Fixtures ────────────────────────────────────────────────────────


def _make_skill(references: list[str]) -> CorpusSkill:
    """Create a minimal CorpusSkill with given references."""
    return CorpusSkill(
        name="Test Skill",
        description="Test",
        domain="vulnerability_analysis",
        references=references,
        verification_steps=[],
        workflow_body="",
        raw_frontmatter={},
    )


def _make_spec(domain_claims: list[str]) -> ConstructSpec:
    """Create a minimal ConstructSpec for normalization testing."""
    return ConstructSpec(
        slug="test-construct",
        version="1.0.0",
        domain_claims=domain_claims,
        refusals=[],
        skill_manifest=[{"name": "test"}],
        raw_yaml="slug: test-construct\nversion: '1.0.0'\ndomain_claims:\n- test\nskill_manifest:\n- name: test",
        spec_hash="sha256:test",
    )


# ── Test: register_security_domains ─────────────────────────────────


class TestRegisterSecurityDomains:
    def test_all_domains_registered(self):
        """All 10 security domains are present in KNOWN_PRECISE_DOMAINS."""
        # Registration happens at import time, so domains should already be there
        for domain in SECURITY_PRECISE_DOMAINS:
            assert domain in KNOWN_PRECISE_DOMAINS, f"{domain} not registered"

    def test_idempotent_registration(self):
        """Calling register_security_domains() again adds 0 new domains."""
        added = register_security_domains()
        assert added == 0

    def test_known_precise_domains_grew(self):
        """KNOWN_PRECISE_DOMAINS has at least 28 entries (18 base + 10 security)."""
        assert len(KNOWN_PRECISE_DOMAINS) >= 28


# ── Test: precise domains pass normalization ────────────────────────


class TestPreciseSecurityDomains:
    def test_vulnerability_analysis_is_precise(self):
        """vulnerability_analysis passes as precise, not vague."""
        result = _classify_claim("vulnerability_analysis")
        assert result["is_vague"] is False
        assert result["matched_category"] == "vulnerability_analysis"

    def test_threat_modeling_is_precise(self):
        """threat_modeling passes as precise, not vague."""
        result = _classify_claim("threat_modeling")
        assert result["is_vague"] is False

    def test_all_security_domains_are_precise(self):
        """Every registered security domain classifies as precise."""
        for domain in SECURITY_PRECISE_DOMAINS:
            result = _classify_claim(domain)
            assert result["is_vague"] is False, f"{domain} is vague but should be precise"


# ── Test: broad "security" stays vague ──────────────────────────────


class TestBroadSecurityStaysVague:
    def test_security_still_vague(self):
        """Broad 'security' claim still tier-caps to UNVERIFIED."""
        assert "security" in KNOWN_VAGUE_TERMS
        result = _classify_claim("security")
        assert result["is_vague"] is True

    def test_security_expert_still_vague(self):
        """Compound claim 'security expert' with 'security' token is still vague."""
        result = _classify_claim("security expert")
        assert result["is_vague"] is True

    def test_normalize_with_vague_security(self):
        """A spec with broad 'security' claim gets tier_cap = UNVERIFIED."""
        spec = _make_spec(["security"])
        norm = normalize(spec)
        assert norm.tier_cap == "UNVERIFIED"
        assert norm.has_vague_claims is True

    def test_normalize_with_precise_security(self):
        """A spec with precise 'vulnerability_analysis' has no tier_cap."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        assert norm.tier_cap is None
        assert norm.has_vague_claims is False


# ── Test: extract_security_references ───────────────────────────────


class TestExtractSecurityReferences:
    def test_attack_technique_extraction(self):
        """Extracts ATT&CK T-codes from references."""
        skill = _make_skill([
            "T1059.001 PowerShell execution",
            "T1566 Phishing",
        ])
        refs = extract_security_references(skill)

        attack_refs = [r for r in refs if r["framework"] == "ATT&CK"]
        assert len(attack_refs) == 2
        assert attack_refs[0]["id"] == "T1059.001"  # Full sub-technique ID
        assert attack_refs[1]["id"] == "T1566"

    def test_cwe_extraction(self):
        """Extracts CWE IDs from references."""
        skill = _make_skill([
            "CWE-79: Cross-site Scripting (XSS)",
            "CWE-89: SQL Injection",
        ])
        refs = extract_security_references(skill)

        cwe_refs = [r for r in refs if r["framework"] == "CWE"]
        assert len(cwe_refs) == 2
        assert cwe_refs[0]["id"] == "CWE-79"
        assert cwe_refs[1]["id"] == "CWE-89"

    def test_owasp_extraction(self):
        """Extracts OWASP Top 10 references."""
        skill = _make_skill([
            "OWASP A03:2021 Injection",
            "A01:2021 Broken Access Control",
        ])
        refs = extract_security_references(skill)

        owasp_refs = [r for r in refs if r["framework"] == "OWASP"]
        assert len(owasp_refs) == 2
        assert owasp_refs[0]["id"] == "A03:2021"
        assert owasp_refs[1]["id"] == "A01:2021"

    def test_mixed_references(self):
        """Extracts mixed framework references from single list."""
        skill = _make_skill([
            "CWE-79: XSS (see also T1059)",
            "A03:2021 Injection",
        ])
        refs = extract_security_references(skill)

        frameworks = {r["framework"] for r in refs}
        assert "ATT&CK" in frameworks
        assert "CWE" in frameworks
        assert "OWASP" in frameworks

    def test_no_references(self):
        """Returns empty list when no framework IDs found."""
        skill = _make_skill(["General security guidance", "Best practices"])
        refs = extract_security_references(skill)
        assert refs == []


# ── Test: classify_security_claim ───────────────────────────────────


class TestClassifySecurityClaim:
    def test_reference_backed(self):
        """Claim with references classified as reference_backed."""
        refs = [{"framework": "CWE", "id": "CWE-79", "raw_reference": "..."}]
        result = classify_security_claim("vulnerability_analysis", refs)

        assert result["has_references"] is True
        assert result["framework_count"] == 1
        assert result["classification"] == "reference_backed"

    def test_unanchored(self):
        """Claim without references classified as unanchored."""
        result = classify_security_claim("vulnerability_analysis", [])

        assert result["has_references"] is False
        assert result["framework_count"] == 0
        assert result["classification"] == "unanchored"
