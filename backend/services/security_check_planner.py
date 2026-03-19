"""SecurityCheckPlanner — Security-specific deterministic check planning.

Cycle 037c: Security + Domain Pack Verification.

Generates security-specific PlannedCheck entries that extend the 037 contract
model. Uses the free-string check_type field — no schema changes needed.

The caller merges security checks with base checks. check_planner.plan_checks()
is NOT modified.
"""

from backend.services.check_planner import PlannedCheck
from backend.services.domain_pack_loader import CorpusSkill


# Security check types with their anchor class mappings
SECURITY_CHECK_TYPES: dict[str, str] = {
    "ATTACK_TECHNIQUE_MAPPING": "PUBLIC_STANDARD",
    "TOOL_INVOCATION_CORRECTNESS": "DETERMINISTIC_CHECK",
    "STANDARDS_COMPLIANCE": "PUBLIC_STANDARD",
    "DEPENDENCY_VULNERABILITY_CHECK": "DETERMINISTIC_CHECK",
    "SECRET_LEAK_CHECK": "DETERMINISTIC_CHECK",
}

# Framework-to-check-type mapping
_FRAMEWORK_CHECK_MAP: dict[str, str] = {
    "ATT&CK": "ATTACK_TECHNIQUE_MAPPING",
    "CWE": "STANDARDS_COMPLIANCE",
    "OWASP": "STANDARDS_COMPLIANCE",
}


def plan_security_checks(
    skill: CorpusSkill,
    references: list[dict],
) -> list[PlannedCheck]:
    """Generate security-specific PlannedCheck entries from a CorpusSkill.

    Maps extracted framework references to appropriate check types.
    Uses SECURITY_CHECK_TYPES for anchor class resolution.

    Args:
        skill: Parsed corpus skill with domain and metadata.
        references: Output from extract_security_references().

    Returns:
        Sorted list of PlannedCheck entries compatible with
        check_planner.plan_checks() output format.
    """
    checks: list[PlannedCheck] = []
    seen_ids: set[str] = set()

    # Generate checks from framework references
    for ref in references:
        framework = ref["framework"]
        ref_id = ref["id"]
        check_type = _FRAMEWORK_CHECK_MAP.get(framework)

        if check_type is None:
            continue

        anchor_class = SECURITY_CHECK_TYPES[check_type]
        check_id = f"security:{check_type.lower()}:{ref_id.lower()}"

        if check_id in seen_ids:
            continue
        seen_ids.add(check_id)

        checks.append(PlannedCheck(
            check_id=check_id,
            check_type=check_type,
            domain=skill.domain,
            source=f"security_corpus:{skill.name}",
            critical=anchor_class == "PUBLIC_STANDARD",
            anchor_class=anchor_class,
        ))

    # Add tool invocation check if skill has verification steps
    if skill.verification_steps:
        tool_check_id = f"security:tool_invocation_correctness:{skill.domain}"
        if tool_check_id not in seen_ids:
            seen_ids.add(tool_check_id)
            checks.append(PlannedCheck(
                check_id=tool_check_id,
                check_type="TOOL_INVOCATION_CORRECTNESS",
                domain=skill.domain,
                source=f"security_corpus:{skill.name}",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # Add dependency vulnerability check for dependency-related skills
    if "dependency" in skill.domain or "supply_chain" in skill.domain:
        dep_check_id = f"security:dependency_vulnerability_check:{skill.domain}"
        if dep_check_id not in seen_ids:
            seen_ids.add(dep_check_id)
            checks.append(PlannedCheck(
                check_id=dep_check_id,
                check_type="DEPENDENCY_VULNERABILITY_CHECK",
                domain=skill.domain,
                source=f"security_corpus:{skill.name}",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # Add secret leak check for secret-detection-related skills
    if "secret" in skill.domain or "leak" in skill.domain:
        secret_check_id = f"security:secret_leak_check:{skill.domain}"
        if secret_check_id not in seen_ids:
            seen_ids.add(secret_check_id)
            checks.append(PlannedCheck(
                check_id=secret_check_id,
                check_type="SECRET_LEAK_CHECK",
                domain=skill.domain,
                source=f"security_corpus:{skill.name}",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # Sort for determinism: (check_type, domain, check_id)
    checks.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return checks


def merge_security_checks(
    base_checks: list[PlannedCheck],
    security_checks: list[PlannedCheck],
) -> list[PlannedCheck]:
    """Merge base 037 checks with security-specific checks.

    Deduplicates by check_id. Preserves sort order: (check_type, domain, check_id).

    Args:
        base_checks: Output from check_planner.plan_checks().
        security_checks: Output from plan_security_checks().

    Returns:
        Merged, deduplicated, sorted list of PlannedCheck entries.
    """
    seen: set[str] = set()
    merged: list[PlannedCheck] = []

    for check in base_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    for check in security_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    merged.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return merged
