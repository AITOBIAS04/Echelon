"""Regression and integration tests for Cycle 037c.

Validates:
1. Base 037 plan_checks() unchanged for non-security claims
2. Base normalize() unchanged for non-security specs
3. All 11 original _MAPPING_RULES preserved
4. Full integration: corpus → domain pack → policy → checks → anchors
"""

import pytest

from backend.services.check_planner import PlannedCheck, plan_checks
from backend.services.construct_anchor_mapper import (
    _MAPPING_RULES,
    map_dimension_anchors,
)
from backend.services.domain_pack_loader import load_corpus_skill, load_domain_pack
from backend.services.policy_normalizer import (
    KNOWN_PRECISE_DOMAINS,
    normalize,
)
from backend.services.security_check_planner import (
    merge_security_checks,
    plan_security_checks,
)
from backend.services.security_policy_rules import (
    extract_security_references,
    register_security_domains,
)
from backend.services.spec_loader import ConstructSpec


# ── Fixtures ────────────────────────────────────────────────────────


def _make_spec(domain_claims, slug="test-construct"):
    return ConstructSpec(
        slug=slug,
        version="1.0.0",
        domain_claims=domain_claims,
        refusals=[],
        skill_manifest=[{"name": "test"}],
        raw_yaml=f"slug: {slug}\nversion: '1.0.0'\ndomain_claims:\n- test\nskill_manifest:\n- name: test",
        spec_hash="sha256:test",
    )


SECURITY_CORPUS = """\
---
name: Vulnerability Scanner
description: Automated vulnerability scanning workflow
domain: vulnerability_analysis
---

# Vulnerability Scanner Workflow

Run automated scans against target infrastructure.

## References

- CWE-79: Cross-site Scripting
- T1059.001 PowerShell execution
- OWASP A03:2021 Injection

## Verification

1. Confirm scanner detects all OWASP Top 10 categories
2. Verify false positive rate below 5%
3. Check remediation suggestions are actionable
"""


# ── Test: base plan_checks() unchanged ──────────────────────────────


class TestBasePlanChecksRegression:
    def test_non_security_claims_unchanged(self):
        """plan_checks() output is identical for non-security domain claims."""
        spec = _make_spec(["design_systems", "motion_design"])
        norm = normalize(spec)

        checks = plan_checks("test-construct", norm)

        # Should have RUBRIC checks + standard ANCHOR checks
        check_types = {c.check_type for c in checks}
        assert "RUBRIC" in check_types
        assert "ANCHOR" in check_types

        # No security check types should appear
        security_types = {
            "ATTACK_TECHNIQUE_MAPPING",
            "TOOL_INVOCATION_CORRECTNESS",
            "STANDARDS_COMPLIANCE",
            "DEPENDENCY_VULNERABILITY_CHECK",
            "SECRET_LEAK_CHECK",
        }
        assert check_types.isdisjoint(security_types)

    def test_sort_order_preserved(self):
        """plan_checks() output is still sorted by (check_type, domain, check_id)."""
        spec = _make_spec(["design_systems"])
        norm = normalize(spec)

        checks = plan_checks("test-construct", norm)

        sort_keys = [(c.check_type, c.domain, c.check_id) for c in checks]
        assert sort_keys == sorted(sort_keys)


# ── Test: base normalize() unchanged ────────────────────────────────


class TestBaseNormalizationRegression:
    def test_non_security_precise_claims(self):
        """Non-security precise claims still pass without tier_cap."""
        spec = _make_spec(["design_systems", "testing", "api_design"])
        norm = normalize(spec)

        assert norm.tier_cap is None
        assert norm.has_vague_claims is False

    def test_non_security_vague_claims(self):
        """Non-security vague claims still get tier_cap = UNVERIFIED."""
        spec = _make_spec(["everything", "ai"])
        norm = normalize(spec)

        assert norm.tier_cap == "UNVERIFIED"
        assert norm.has_vague_claims is True


# ── Test: original anchor rules preserved ───────────────────────────


class TestOriginalAnchorRulesRegression:
    def test_all_original_rules_present(self):
        """All 11 original _MAPPING_RULES entries are still present."""
        original_anchor_ids = {
            "code_verification",
            "benchmark_suite",
            "public_standard_check",
            "live_evidence_feed",
            "frontend_standards",
            "security_standards",
            "research_metadata",
            "research_evidence",
            "user_research_methods",
            "journey_patterns",
            "recovery_guidance",
        }
        current_anchor_ids = {rule[2] for rule in _MAPPING_RULES}
        assert original_anchor_ids.issubset(current_anchor_ids)

    def test_total_rules_count(self):
        """_MAPPING_RULES has exactly 13 entries (11 original + 2 new)."""
        assert len(_MAPPING_RULES) == 13


# ── Test: full integration path ─────────────────────────────────────


class TestSecurityCorpusIntegration:
    def test_full_path_corpus_to_contract(self):
        """Full integration: corpus → domain pack → policy → checks → anchors."""
        # Step 1: Parse corpus
        skill = load_corpus_skill(SECURITY_CORPUS)
        assert skill.name == "Vulnerability Scanner"
        assert skill.domain == "vulnerability_analysis"
        assert len(skill.references) == 3
        assert len(skill.verification_steps) == 3

        # Step 2: Domain pack
        pack = load_domain_pack("security-v1", "security", [SECURITY_CORPUS])
        assert len(pack.skills) == 1

        # Step 3: Security domain is precise (registered at import time)
        assert "vulnerability_analysis" in KNOWN_PRECISE_DOMAINS
        spec = _make_spec(["vulnerability_analysis"])
        norm = normalize(spec)
        assert norm.tier_cap is None  # Not vague

        # Step 4: Extract references
        refs = extract_security_references(skill)
        assert len(refs) >= 3  # CWE-79, T1059.001, A03:2021

        # Step 5: Plan security checks
        security_checks = plan_security_checks(skill, refs)
        assert len(security_checks) > 0
        check_types = {c.check_type for c in security_checks}
        assert "ATTACK_TECHNIQUE_MAPPING" in check_types
        assert "STANDARDS_COMPLIANCE" in check_types
        assert "TOOL_INVOCATION_CORRECTNESS" in check_types  # Has verification steps

        # Step 6: Merge with base checks
        base_checks = plan_checks("test-construct", norm)
        all_checks = merge_security_checks(base_checks, security_checks)
        assert len(all_checks) > len(base_checks)

        # Step 7: Anchor mapping
        vuln_anchor = map_dimension_anchors("vulnerability_analysis")
        assert vuln_anchor.weakly_anchored is False

        attack_anchor = map_dimension_anchors("attack_technique_mapping")
        attack_ids = {a.anchor_id for a in attack_anchor.anchors}
        assert "attack_framework" in attack_ids

    def test_broad_security_still_blocked(self):
        """Broad 'security' claim still tier-caps even with domain pack loaded."""
        spec = _make_spec(["security"])
        norm = normalize(spec)
        assert norm.tier_cap == "UNVERIFIED"
        assert norm.has_vague_claims is True
