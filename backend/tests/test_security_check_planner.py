"""Tests for SecurityCheckPlanner — security-specific deterministic check planning.

Cycle 037c: Security + Domain Pack Verification.
"""

import pytest

from typing import List, Optional

from backend.services.check_planner import PlannedCheck, plan_checks
from backend.services.domain_pack_loader import CorpusSkill
from backend.services.policy_normalizer import NormalizationResult
from backend.services.security_check_planner import (
    SECURITY_CHECK_TYPES,
    merge_security_checks,
    plan_security_checks,
)


# ── Fixtures ────────────────────────────────────────────────────────


def _make_skill(
    domain: str = "vulnerability_analysis",
    verification_steps: Optional[List[str]] = None,
) -> CorpusSkill:
    return CorpusSkill(
        name="Test Security Skill",
        description="Test",
        domain=domain,
        references=[],
        verification_steps=verification_steps or [],
        workflow_body="",
        raw_frontmatter={},
    )


def _make_refs(*frameworks: tuple[str, str]) -> list[dict]:
    """Create reference dicts from (framework, id) tuples."""
    return [
        {"framework": fw, "id": ref_id, "raw_reference": f"{fw} {ref_id}"}
        for fw, ref_id in frameworks
    ]


# ── Test: plan_security_checks ──────────────────────────────────────


class TestPlanSecurityChecks:
    def test_attack_technique_check(self):
        """ATT&CK reference generates ATTACK_TECHNIQUE_MAPPING check."""
        skill = _make_skill()
        refs = _make_refs(("ATT&CK", "T1059.001"))

        checks = plan_security_checks(skill, refs)

        attack_checks = [c for c in checks if c.check_type == "ATTACK_TECHNIQUE_MAPPING"]
        assert len(attack_checks) == 1
        assert attack_checks[0].anchor_class == "PUBLIC_STANDARD"
        assert attack_checks[0].critical is True
        assert "t1059.001" in attack_checks[0].check_id

    def test_tool_invocation_check(self):
        """Skill with verification steps generates TOOL_INVOCATION_CORRECTNESS check."""
        skill = _make_skill(verification_steps=["Verify tool output matches spec"])
        refs = []

        checks = plan_security_checks(skill, refs)

        tool_checks = [c for c in checks if c.check_type == "TOOL_INVOCATION_CORRECTNESS"]
        assert len(tool_checks) == 1
        assert tool_checks[0].anchor_class == "DETERMINISTIC_CHECK"
        assert tool_checks[0].critical is False

    def test_standards_compliance_check(self):
        """CWE/OWASP references generate STANDARDS_COMPLIANCE checks."""
        skill = _make_skill()
        refs = _make_refs(("CWE", "CWE-79"), ("OWASP", "A03:2021"))

        checks = plan_security_checks(skill, refs)

        std_checks = [c for c in checks if c.check_type == "STANDARDS_COMPLIANCE"]
        assert len(std_checks) == 2
        assert all(c.anchor_class == "PUBLIC_STANDARD" for c in std_checks)
        assert all(c.critical is True for c in std_checks)

    def test_dependency_vulnerability_check(self):
        """Dependency-related skill generates DEPENDENCY_VULNERABILITY_CHECK."""
        skill = _make_skill(domain="dependency_scanning")
        refs = []

        checks = plan_security_checks(skill, refs)

        dep_checks = [c for c in checks if c.check_type == "DEPENDENCY_VULNERABILITY_CHECK"]
        assert len(dep_checks) == 1
        assert dep_checks[0].anchor_class == "DETERMINISTIC_CHECK"

    def test_secret_leak_check(self):
        """Secret-detection skill generates SECRET_LEAK_CHECK."""
        skill = _make_skill(domain="secret_detection")
        refs = []

        checks = plan_security_checks(skill, refs)

        secret_checks = [c for c in checks if c.check_type == "SECRET_LEAK_CHECK"]
        assert len(secret_checks) == 1
        assert secret_checks[0].anchor_class == "DETERMINISTIC_CHECK"

    def test_checks_sorted(self):
        """Output is sorted by (check_type, domain, check_id)."""
        skill = _make_skill(verification_steps=["Check this"])
        refs = _make_refs(("ATT&CK", "T1059"), ("CWE", "CWE-79"))

        checks = plan_security_checks(skill, refs)

        sort_keys = [(c.check_type, c.domain, c.check_id) for c in checks]
        assert sort_keys == sorted(sort_keys)

    def test_no_duplicate_check_ids(self):
        """Duplicate references don't produce duplicate checks."""
        skill = _make_skill()
        refs = _make_refs(("CWE", "CWE-79"), ("CWE", "CWE-79"))

        checks = plan_security_checks(skill, refs)

        cwe_checks = [c for c in checks if "cwe-79" in c.check_id]
        assert len(cwe_checks) == 1


# ── Test: merge_security_checks ─────────────────────────────────────


class TestMergeSecurityChecks:
    def test_merge_deduplication(self):
        """Merged checks are deduplicated by check_id."""
        base = [
            PlannedCheck(
                check_id="rubric:test:design",
                check_type="RUBRIC",
                domain="design",
                source="rubric_registry:test",
                critical=True,
            ),
            PlannedCheck(
                check_id="anchor:public_standard",
                check_type="ANCHOR",
                domain="*",
                source="anchor_class:PUBLIC_STANDARD",
                critical=True,
                anchor_class="PUBLIC_STANDARD",
            ),
        ]
        security = [
            PlannedCheck(
                check_id="security:attack_technique_mapping:t1059",
                check_type="ATTACK_TECHNIQUE_MAPPING",
                domain="vulnerability_analysis",
                source="security_corpus:Test",
                critical=True,
                anchor_class="PUBLIC_STANDARD",
            ),
        ]

        merged = merge_security_checks(base, security)

        assert len(merged) == 3
        ids = {c.check_id for c in merged}
        assert "rubric:test:design" in ids
        assert "anchor:public_standard" in ids
        assert "security:attack_technique_mapping:t1059" in ids

    def test_merge_preserves_sort_order(self):
        """Merged output is sorted by (check_type, domain, check_id)."""
        base = [
            PlannedCheck(
                check_id="rubric:test:design",
                check_type="RUBRIC",
                domain="design",
                source="test",
                critical=True,
            ),
        ]
        security = [
            PlannedCheck(
                check_id="security:attack_technique_mapping:t1059",
                check_type="ATTACK_TECHNIQUE_MAPPING",
                domain="vuln",
                source="test",
                critical=True,
                anchor_class="PUBLIC_STANDARD",
            ),
        ]

        merged = merge_security_checks(base, security)

        sort_keys = [(c.check_type, c.domain, c.check_id) for c in merged]
        assert sort_keys == sorted(sort_keys)

    def test_merge_base_priority_on_conflict(self):
        """Base check wins when both have the same check_id."""
        shared_id = "shared:check:id"
        base = [
            PlannedCheck(
                check_id=shared_id,
                check_type="RUBRIC",
                domain="test",
                source="base",
                critical=True,
            ),
        ]
        security = [
            PlannedCheck(
                check_id=shared_id,
                check_type="ATTACK_TECHNIQUE_MAPPING",
                domain="test",
                source="security",
                critical=False,
                anchor_class="PUBLIC_STANDARD",
            ),
        ]

        merged = merge_security_checks(base, security)

        assert len(merged) == 1
        assert merged[0].source == "base"  # Base wins


# ── Test: SECURITY_CHECK_TYPES completeness ─────────────────────────


class TestSecurityCheckTypes:
    def test_five_check_types(self):
        """All 5 security check types are defined."""
        assert len(SECURITY_CHECK_TYPES) == 5
        assert "ATTACK_TECHNIQUE_MAPPING" in SECURITY_CHECK_TYPES
        assert "TOOL_INVOCATION_CORRECTNESS" in SECURITY_CHECK_TYPES
        assert "STANDARDS_COMPLIANCE" in SECURITY_CHECK_TYPES
        assert "DEPENDENCY_VULNERABILITY_CHECK" in SECURITY_CHECK_TYPES
        assert "SECRET_LEAK_CHECK" in SECURITY_CHECK_TYPES

    def test_anchor_class_mappings(self):
        """Check types map to correct anchor classes."""
        assert SECURITY_CHECK_TYPES["ATTACK_TECHNIQUE_MAPPING"] == "PUBLIC_STANDARD"
        assert SECURITY_CHECK_TYPES["TOOL_INVOCATION_CORRECTNESS"] == "DETERMINISTIC_CHECK"
        assert SECURITY_CHECK_TYPES["STANDARDS_COMPLIANCE"] == "PUBLIC_STANDARD"
        assert SECURITY_CHECK_TYPES["DEPENDENCY_VULNERABILITY_CHECK"] == "DETERMINISTIC_CHECK"
        assert SECURITY_CHECK_TYPES["SECRET_LEAK_CHECK"] == "DETERMINISTIC_CHECK"
