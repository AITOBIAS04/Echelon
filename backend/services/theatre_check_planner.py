"""TheatreCheckPlanner — Theatre-specific deterministic check planning.

Cycle 037d: Theatre Construct Verification.

Generates theatre-specific PlannedCheck entries that extend the 037 contract
model. Uses the free-string check_type field — no schema changes needed.

The caller merges theatre checks with base checks. check_planner.plan_checks()
is NOT modified.

Follows the same pattern as security_check_planner.py (Cycle 037c).
"""

from backend.services.check_planner import PlannedCheck
from backend.services.theatre_policy_rules import TheatreConstructMeta


# Theatre check types with their anchor class mappings
THEATRE_CHECK_TYPES: dict[str, str] = {
    "SETTLEMENT_ACCURACY": "LIVE_EXTERNAL_EVIDENCE",
    "ORACLE_CONSISTENCY": "LIVE_EXTERNAL_EVIDENCE",
    "CALIBRATION_VALIDITY": "DETERMINISTIC_CHECK",
    "FUNCTIONAL_CORRECTNESS": "DETERMINISTIC_CHECK",
}


def plan_theatre_checks(
    spec_slug: str,
    meta: TheatreConstructMeta,
) -> list[PlannedCheck]:
    """Generate theatre-specific PlannedCheck entries from construct metadata.

    Args:
        spec_slug: Construct slug for check ID namespacing.
        meta: Parsed TheatreConstructMeta from construct.json.

    Returns:
        Sorted list of PlannedCheck entries compatible with
        check_planner.plan_checks() output format.
    """
    checks: list[PlannedCheck] = []
    seen_ids: set[str] = set()

    # 1. SETTLEMENT_ACCURACY — one per theatre template
    for template in meta.theatre_templates:
        check_id = f"theatre:settlement_accuracy:{template.id}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="SETTLEMENT_ACCURACY",
                domain=f"theatre:{template.id}",
                source=f"theatre_template:{template.id}:oracle:{template.oracle}",
                critical=True,
                anchor_class="LIVE_EXTERNAL_EVIDENCE",
            ))

    # 2. ORACLE_CONSISTENCY — one per cross-validation source
    if meta.has_cross_validation:
        cross_val = [s for s in meta.osint_sources if s.role == "cross_validation"]
        for source in cross_val:
            check_id = f"theatre:oracle_consistency:{source.id}"
            if check_id not in seen_ids:
                seen_ids.add(check_id)
                checks.append(PlannedCheck(
                    check_id=check_id,
                    check_type="ORACLE_CONSISTENCY",
                    domain=f"oracle:{source.id}",
                    source=f"osint_source:{source.id}:role:cross_validation",
                    critical=True,
                    anchor_class="LIVE_EXTERNAL_EVIDENCE",
                ))

    # 3. CALIBRATION_VALIDITY — single check if Brier scoring present
    if meta.has_brier_scoring:
        check_id = f"theatre:calibration_validity:{spec_slug}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="CALIBRATION_VALIDITY",
                domain=f"calibration:{spec_slug}",
                source=f"brier_scoring:{spec_slug}",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # 4. FUNCTIONAL_CORRECTNESS — one per theatre template
    for template in meta.theatre_templates:
        check_id = f"theatre:functional_correctness:{template.id}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="FUNCTIONAL_CORRECTNESS",
                domain=f"theatre:{template.id}",
                source=f"theatre_template:{template.id}:state_machine",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # Sort for determinism: (check_type, domain, check_id)
    checks.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return checks


def merge_theatre_checks(
    base_checks: list[PlannedCheck],
    theatre_checks: list[PlannedCheck],
) -> list[PlannedCheck]:
    """Merge base 037 checks with theatre-specific checks.

    Deduplicates by check_id. Preserves sort order: (check_type, domain, check_id).

    Args:
        base_checks: Output from check_planner.plan_checks() (possibly
            already merged with security checks).
        theatre_checks: Output from plan_theatre_checks().

    Returns:
        Merged, deduplicated, sorted list of PlannedCheck entries.
    """
    seen: set[str] = set()
    merged: list[PlannedCheck] = []

    for check in base_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    for check in theatre_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    merged.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return merged
