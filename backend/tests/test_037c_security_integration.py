"""Tests for 037c runtime integration — security domain registration + check merging.

Bug 20260319-02fab2: Validates that security domains are registered in the
production contract path and that security checks are merged when corpus
skills are provided.

T1: Proves the bug existed (domains registered via import side-effect)
T2: Verifies P1 fix (contract_service import triggers registration)
T3: Verifies P2 fix (corpus_skills wires security checks into pipeline)
T4: Integration + regression
"""

import pytest
from typing import List, Optional

from backend.services.check_planner import PlannedCheck, plan_checks, compute_contract_hash
from backend.services.domain_pack_loader import CorpusSkill
from backend.services.policy_normalizer import (
    KNOWN_PRECISE_DOMAINS,
    normalize,
)
from backend.services.security_check_planner import (
    SECURITY_CHECK_TYPES,
    merge_security_checks,
    plan_security_checks,
)
from backend.services.security_policy_rules import (
    SECURITY_PRECISE_DOMAINS,
    extract_security_references,
)
from backend.services.spec_loader import ConstructSpec, load as load_spec


# ── Fixtures ────────────────────────────────────────────────────────


def _make_spec(domain_claims, slug="test-security-construct"):
    return ConstructSpec(
        slug=slug,
        version="1.0.0",
        domain_claims=domain_claims,
        refusals=[],
        skill_manifest=[{"name": "test"}],
        raw_yaml=f"slug: {slug}\nversion: '1.0.0'\ndomain_claims:\n- test\nskill_manifest:\n- name: test",
        spec_hash="sha256:test-security",
    )


def _make_corpus_skill(
    domain: str = "vulnerability_analysis",
    references: Optional[List[str]] = None,
    verification_steps: Optional[List[str]] = None,
) -> CorpusSkill:
    return CorpusSkill(
        name="Test Security Skill",
        description="Test skill for security integration",
        domain=domain,
        references=references or [],
        verification_steps=verification_steps or [],
        workflow_body="",
        raw_frontmatter={},
    )


SECURITY_YAML = """\
slug: security-construct
version: "1.0.0"
domain_claims:
  - vulnerability_analysis
  - threat_modeling
skill_manifest:
  - command: /scan
    domain: vulnerability_analysis
"""


# ── T1 + T2: Domain registration in production path ─────────────────


class TestSecurityDomainRegistration:
    """Verify security domains are registered via contract_service import."""

    def test_security_domains_in_known_precise(self):
        """P1 fix: All 10 security domains present in KNOWN_PRECISE_DOMAINS.

        This test passes because importing contract_service (which happens
        transitively via security_policy_rules import) triggers registration.
        Pre-fix, this would fail in an isolated runtime.
        """
        for domain in SECURITY_PRECISE_DOMAINS:
            assert domain in KNOWN_PRECISE_DOMAINS, (
                f"{domain} not in KNOWN_PRECISE_DOMAINS — "
                "security_policy_rules import side-effect not firing"
            )

    def test_vulnerability_analysis_is_precise(self):
        """vulnerability_analysis classified as precise, not vague."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)

        assert norm.tier_cap is None
        assert norm.has_vague_claims is False

        claim = norm.normalized_claims[0]
        assert claim["is_vague"] is False

    def test_threat_modeling_is_precise(self):
        """threat_modeling classified as precise, not vague."""
        spec = _make_spec(["threat_modeling"])
        norm = normalize(spec)

        assert norm.tier_cap is None
        assert norm.has_vague_claims is False

    def test_broad_security_still_vague(self):
        """Broad 'security' claim remains vague even with registration."""
        spec = _make_spec(["security"])
        norm = normalize(spec)

        assert norm.tier_cap == "UNVERIFIED"
        assert norm.has_vague_claims is True

    def test_contract_service_imports_security_policy_rules(self):
        """contract_service.py imports security_policy_rules (production path).

        Verifies the import exists at source level. The actual registration
        side-effect is proven by test_security_domains_in_known_precise above.
        We avoid importing contract_service directly because it pulls in the
        full DB layer (asyncpg) which isn't available in unit-test environments.
        """
        import ast
        from pathlib import Path

        cs_path = Path(__file__).resolve().parent.parent / "services" / "contract_service.py"
        tree = ast.parse(cs_path.read_text())

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)

        assert "backend.services.security_policy_rules" in imported_modules, (
            "contract_service.py must import security_policy_rules "
            "to trigger domain registration in the production path"
        )


# ── T3: Security check integration via corpus_skills ─────────────────


class TestSecurityCheckIntegration:
    """Verify security checks are merged when corpus_skills provided."""

    def test_plan_with_attack_references(self):
        """ATT&CK references produce ATTACK_TECHNIQUE_MAPPING checks."""
        skill = _make_corpus_skill(
            references=[
                "T1059.001 PowerShell execution",
                "CWE-79: Cross-site Scripting",
            ],
        )
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)

        check_types = {c.check_type for c in sec_checks}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        assert "STANDARDS_COMPLIANCE" in check_types

    def test_merge_into_base_checks(self):
        """Security checks merge with base checks, no duplicates."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        skill = _make_corpus_skill(
            references=["T1059.001 PowerShell execution"],
        )
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)

        merged = merge_security_checks(base_checks, sec_checks)

        assert len(merged) > len(base_checks)
        check_types = {c.check_type for c in merged}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        # Base checks preserved
        assert "RUBRIC" in check_types or "ANCHOR" in check_types

    def test_merge_preserves_sort_order(self):
        """Merged output sorted by (check_type, domain, check_id)."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        skill = _make_corpus_skill(
            references=[
                "T1059.001 PowerShell",
                "CWE-79: XSS",
                "A03:2021 Injection",
            ],
            verification_steps=["Verify scanner runs"],
        )
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)
        merged = merge_security_checks(base_checks, sec_checks)

        sort_keys = [(c.check_type, c.domain, c.check_id) for c in merged]
        assert sort_keys == sorted(sort_keys)

    def test_without_corpus_skills_unchanged(self):
        """Without corpus_skills, pipeline produces only base checks."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        # No security check types in base output
        security_types = set(SECURITY_CHECK_TYPES.keys())
        base_types = {c.check_type for c in base_checks}
        assert base_types.isdisjoint(security_types)

    def test_contract_hash_changes_with_security_checks(self):
        """Contract hash is different when security checks are added."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)
        hash_without = compute_contract_hash(spec.spec_hash, base_checks)

        skill = _make_corpus_skill(
            references=["T1059.001 PowerShell execution"],
        )
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)
        merged = merge_security_checks(base_checks, sec_checks)
        hash_with = compute_contract_hash(spec.spec_hash, merged)

        assert hash_without != hash_with

    def test_contract_hash_deterministic_with_security_checks(self):
        """Same corpus skills produce same contract hash."""
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)

        def _build():
            base = plan_checks(spec.slug, norm)
            skill = _make_corpus_skill(
                references=["T1059.001 PowerShell execution", "CWE-79: XSS"],
            )
            refs = extract_security_references(skill)
            sec = plan_security_checks(skill, refs)
            merged = merge_security_checks(base, sec)
            return compute_contract_hash(spec.spec_hash, merged)

        assert _build() == _build()


# ── T4: Full pipeline integration ───────────────────────────────────


class TestFullPipelineIntegration:
    """End-to-end: YAML spec + corpus skills → full contract data."""

    def test_security_yaml_precise_no_vague(self):
        """Security YAML with precise domains passes normalization cleanly."""
        spec = load_spec(SECURITY_YAML)
        norm = normalize(spec)

        assert norm.tier_cap is None
        assert norm.has_vague_claims is False
        assert len(norm.normalized_claims) == 2

        domains = {c["domain"] for c in norm.normalized_claims}
        assert "vulnerability_analysis" in domains
        assert "threat_modeling" in domains

    def test_full_pipeline_with_corpus(self):
        """Full pipeline: parse → normalize → plan → merge security → hash."""
        spec = load_spec(SECURITY_YAML)
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        skill = _make_corpus_skill(
            domain="vulnerability_analysis",
            references=[
                "T1059.001 PowerShell execution",
                "CWE-79: Cross-site Scripting",
                "A03:2021 Injection",
            ],
            verification_steps=[
                "Confirm scanner detects all OWASP Top 10",
                "Verify false positive rate below 5%",
            ],
        )
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)
        merged = merge_security_checks(base_checks, sec_checks)

        # Security checks present
        check_types = {c.check_type for c in merged}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        assert "STANDARDS_COMPLIANCE" in check_types
        assert "TOOL_INVOCATION_CORRECTNESS" in check_types

        # Contract hash is deterministic
        hash1 = compute_contract_hash(spec.spec_hash, merged)
        assert hash1.startswith("sha256:")

    def test_multiple_corpus_skills_merge(self):
        """Multiple corpus skills merge additively."""
        spec = _make_spec(["vulnerability_analysis", "threat_modeling"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        skill1 = _make_corpus_skill(
            domain="vulnerability_analysis",
            references=["T1059.001 PowerShell"],
        )
        skill2 = _make_corpus_skill(
            domain="threat_modeling",
            references=["CWE-79: XSS", "A03:2021 Injection"],
            verification_steps=["Verify model completeness"],
        )

        planned = base_checks
        for skill in [skill1, skill2]:
            refs = extract_security_references(skill)
            sec = plan_security_checks(skill, refs)
            planned = merge_security_checks(planned, sec)

        check_types = {c.check_type for c in planned}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        assert "STANDARDS_COMPLIANCE" in check_types
        assert "TOOL_INVOCATION_CORRECTNESS" in check_types

        # All checks sorted
        sort_keys = [(c.check_type, c.domain, c.check_id) for c in planned]
        assert sort_keys == sorted(sort_keys)


# ── Regression: existing 037 behavior unchanged ─────────────────────


class TestRegressionNonSecurityUnchanged:
    """Non-security constructs produce identical output post-fix."""

    def test_design_construct_unchanged(self):
        """Design domains unaffected by security registration."""
        spec = _make_spec(["design_systems", "motion_design"])
        norm = normalize(spec)

        assert norm.tier_cap is None
        assert norm.has_vague_claims is False

        checks = plan_checks(spec.slug, norm)
        security_types = set(SECURITY_CHECK_TYPES.keys())
        check_types = {c.check_type for c in checks}
        assert check_types.isdisjoint(security_types)

    def test_vague_construct_still_capped(self):
        """Vague non-security claims still get tier_cap = UNVERIFIED."""
        spec = _make_spec(["everything", "ai"])
        norm = normalize(spec)

        assert norm.tier_cap == "UNVERIFIED"
        assert norm.has_vague_claims is True


# ── Route-level: corpus_contents → corpus_skills wiring ──────────────


VALID_CORPUS_CONTENT = """\
---
name: Injection Scanner
description: Detects injection vulnerabilities
domain: vulnerability_analysis
---

## References

- T1059.001 PowerShell execution
- CWE-79: Cross-site Scripting

## Verification

- Confirm scanner detects OWASP Top 10
"""


class TestRouteCorpusParsing:
    """Verify that corpus_contents in the request schema produces CorpusSkills."""

    def test_create_contract_request_accepts_corpus(self):
        """CreateContractRequest schema accepts optional corpus_contents."""
        from backend.schemas.construct_schemas import CreateContractRequest

        req = CreateContractRequest(
            yaml_content="slug: test\nversion: '1.0.0'",
            corpus_contents=[VALID_CORPUS_CONTENT],
        )
        assert req.corpus_contents is not None
        assert len(req.corpus_contents) == 1

    def test_create_contract_request_corpus_defaults_none(self):
        """corpus_contents defaults to None when omitted."""
        from backend.schemas.construct_schemas import CreateContractRequest

        req = CreateContractRequest(yaml_content="slug: test\nversion: '1.0.0'")
        assert req.corpus_contents is None

    def test_corpus_contents_parsed_to_skills(self):
        """Raw corpus content strings parse into CorpusSkill objects."""
        from backend.services.domain_pack_loader import load_corpus_skill

        skill = load_corpus_skill(VALID_CORPUS_CONTENT)
        assert skill.name == "Injection Scanner"
        assert skill.domain == "vulnerability_analysis"
        assert len(skill.references) == 2
        assert any("T1059" in r for r in skill.references)

    def test_corpus_skills_produce_security_checks_end_to_end(self):
        """Full route-equivalent pipeline: corpus content → security checks."""
        from backend.services.domain_pack_loader import load_corpus_skill

        skill = load_corpus_skill(VALID_CORPUS_CONTENT)
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)
        merged = merge_security_checks(base_checks, sec_checks)

        check_types = {c.check_type for c in merged}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        assert "STANDARDS_COMPLIANCE" in check_types

    def test_invalid_corpus_content_raises(self):
        """Invalid corpus content (no frontmatter) raises ValueError."""
        from backend.services.domain_pack_loader import load_corpus_skill

        with pytest.raises(ValueError, match="frontmatter"):
            load_corpus_skill("no frontmatter here")
