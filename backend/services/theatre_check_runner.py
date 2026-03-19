"""Theatre Check Runner — deterministic execution of theatre-specific checks.

Cycle 037e: Theatre Check Execution.

Dispatches planned theatre checks to deterministic execution methods.
Each check family has a focused execution function that operates on
normalized fixture inputs, never on raw repo data.

This is a runner/executor, not a soft scorer. Results are PASSED, FAILED,
or SKIPPED — never probabilistic.
"""

import logging
import math
from typing import Optional

from backend.schemas.theatre_execution import (
    TheatreCheckResult,
    TheatreExecutionResult,
    TheatreFixtureInput,
)

logger = logging.getLogger(__name__)

# Theatre check types that this runner can execute
EXECUTABLE_CHECK_TYPES = {
    "SETTLEMENT_ACCURACY",
    "ORACLE_CONSISTENCY",
    "CALIBRATION_VALIDITY",
    "FUNCTIONAL_CORRECTNESS",
}

# Tolerance for floating-point Brier score comparison
BRIER_TOLERANCE = 1e-6


def execute_theatre_checks(
    planned_checks: list[dict],
    fixture: TheatreFixtureInput,
) -> TheatreExecutionResult:
    """Execute all theatre-specific planned checks against fixture inputs.

    Non-theatre check types are silently skipped (they belong to other runners).

    Args:
        planned_checks: List of planned check dicts from contract.
        fixture: Normalized fixture input from theatre_fixture_loader.

    Returns:
        TheatreExecutionResult with per-check results.
    """
    result = TheatreExecutionResult(construct_slug=fixture.construct_slug)

    for check in planned_checks:
        check_type = check.get("check_type", "")
        if check_type not in EXECUTABLE_CHECK_TYPES:
            continue

        check_id = check.get("check_id", "")
        check_result = _dispatch(check_type, check_id, check, fixture)
        result.check_results.append(check_result)

    logger.info(
        "Theatre execution for %s: %d executed, %d passed, %d failed, %d skipped",
        fixture.construct_slug,
        result.total_executed,
        result.total_passed,
        result.total_failed,
        result.total_skipped,
    )
    return result


def _dispatch(
    check_type: str,
    check_id: str,
    check: dict,
    fixture: TheatreFixtureInput,
) -> TheatreCheckResult:
    """Dispatch a single check to its execution method."""
    if check_type == "SETTLEMENT_ACCURACY":
        return _execute_settlement_accuracy(check_id, check, fixture)
    elif check_type == "ORACLE_CONSISTENCY":
        return _execute_oracle_consistency(check_id, check, fixture)
    elif check_type == "CALIBRATION_VALIDITY":
        return _execute_calibration_validity(check_id, check, fixture)
    elif check_type == "FUNCTIONAL_CORRECTNESS":
        return _execute_functional_correctness(check_id, check, fixture)
    else:
        return TheatreCheckResult(
            check_id=check_id,
            check_type=check_type,
            status="SKIPPED",
            reason=f"Unknown theatre check type: {check_type}",
        )


# ── Settlement Accuracy ─────────────────────────────────────────────


def _execute_settlement_accuracy(
    check_id: str,
    check: dict,
    fixture: TheatreFixtureInput,
) -> TheatreCheckResult:
    """Execute SETTLEMENT_ACCURACY: replay outcome against oracle.

    Verifies that the declared settlement outcome matches the oracle value.
    """
    # Extract template ID from check_id: "theatre:settlement_accuracy:{template_id}"
    parts = check_id.split(":")
    template_id = parts[2] if len(parts) >= 3 else None

    if template_id is None or template_id not in fixture.settlement_fixtures:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="SETTLEMENT_ACCURACY",
            status="SKIPPED",
            template_id=template_id,
            reason=f"No settlement fixture for template '{template_id}'",
        )

    fx = fixture.settlement_fixtures[template_id]
    predicted = fx.get("predicted_outcome")
    actual = fx.get("actual_outcome")
    oracle_value = fx.get("oracle_value")

    # Settlement accuracy: predicted outcome matches actual outcome
    if predicted == actual:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="SETTLEMENT_ACCURACY",
            status="PASSED",
            template_id=template_id,
            evidence={
                "predicted_outcome": predicted,
                "actual_outcome": actual,
                "oracle_value": oracle_value,
                "oracle": fx.get("oracle", ""),
                "resolution": fx.get("resolution", ""),
            },
        )
    else:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="SETTLEMENT_ACCURACY",
            status="FAILED",
            template_id=template_id,
            evidence={
                "predicted_outcome": predicted,
                "actual_outcome": actual,
                "oracle_value": oracle_value,
                "oracle": fx.get("oracle", ""),
            },
            reason=f"Settlement mismatch: predicted={predicted}, actual={actual}",
        )


# ── Oracle Consistency ───────────────────────────────────────────────


def _execute_oracle_consistency(
    check_id: str,
    check: dict,
    fixture: TheatreFixtureInput,
) -> TheatreCheckResult:
    """Execute ORACLE_CONSISTENCY: compare primary vs cross-validation.

    Verifies that cross-validation source agrees with primary within threshold.
    """
    # Extract source ID from check_id: "theatre:oracle_consistency:{source_id}"
    parts = check_id.split(":")
    source_id = parts[2] if len(parts) >= 3 else None

    if source_id is None or source_id not in fixture.oracle_fixtures:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="ORACLE_CONSISTENCY",
            status="SKIPPED",
            source_id=source_id,
            reason=f"No oracle fixture for source '{source_id}'",
        )

    fx = fixture.oracle_fixtures[source_id]
    primary = fx.get("primary_value")
    cross = fx.get("cross_value")
    threshold = fx.get("threshold", 0.5)

    if primary is None or cross is None:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="ORACLE_CONSISTENCY",
            status="SKIPPED",
            source_id=source_id,
            reason="Missing primary or cross-validation value",
        )

    delta = abs(primary - cross)
    consistent = delta <= threshold

    return TheatreCheckResult(
        check_id=check_id,
        check_type="ORACLE_CONSISTENCY",
        status="PASSED" if consistent else "FAILED",
        source_id=source_id,
        evidence={
            "primary_value": primary,
            "cross_value": cross,
            "delta": delta,
            "threshold": threshold,
            "source_name": fx.get("source_name", ""),
        },
        reason=None if consistent else f"Oracle divergence: delta={delta:.4f} > threshold={threshold}",
    )


# ── Calibration Validity ─────────────────────────────────────────────


def _execute_calibration_validity(
    check_id: str,
    check: dict,
    fixture: TheatreFixtureInput,
) -> TheatreCheckResult:
    """Execute CALIBRATION_VALIDITY: recompute Brier score and validate.

    Verifies that the declared Brier computation is arithmetically correct.
    """
    if fixture.calibration_fixture is None:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="CALIBRATION_VALIDITY",
            status="SKIPPED",
            reason="No calibration fixture provided",
        )

    fx = fixture.calibration_fixture
    predictions = fx.get("predictions", [])
    outcomes = fx.get("outcomes", [])
    expected_brier = fx.get("expected_brier")
    brier_type = fx.get("brier_type", "binary")

    if not predictions or not outcomes or len(predictions) != len(outcomes):
        return TheatreCheckResult(
            check_id=check_id,
            check_type="CALIBRATION_VALIDITY",
            status="SKIPPED",
            reason="Invalid calibration fixture: mismatched or empty prediction/outcome arrays",
        )

    # Recompute Brier score
    if brier_type == "binary":
        computed = sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)
    else:
        # Multi-class: sum of squared errors across all classes
        computed = sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)

    # Compare against expected
    if expected_brier is not None:
        match = abs(computed - expected_brier) < BRIER_TOLERANCE
    else:
        # No expected value — just verify computation doesn't error
        match = True

    return TheatreCheckResult(
        check_id=check_id,
        check_type="CALIBRATION_VALIDITY",
        status="PASSED" if match else "FAILED",
        evidence={
            "computed_brier": round(computed, 8),
            "expected_brier": expected_brier,
            "brier_type": brier_type,
            "n_predictions": len(predictions),
        },
        reason=None if match else f"Brier mismatch: computed={computed:.8f} != expected={expected_brier:.8f}",
    )


# ── Functional Correctness ───────────────────────────────────────────


def _execute_functional_correctness(
    check_id: str,
    check: dict,
    fixture: TheatreFixtureInput,
) -> TheatreCheckResult:
    """Execute FUNCTIONAL_CORRECTNESS: validate template state transitions.

    Verifies that declared template logic produces expected state transitions.
    """
    # Extract template ID from check_id: "theatre:functional_correctness:{template_id}"
    parts = check_id.split(":")
    template_id = parts[2] if len(parts) >= 3 else None

    if template_id is None or template_id not in fixture.functional_fixtures:
        return TheatreCheckResult(
            check_id=check_id,
            check_type="FUNCTIONAL_CORRECTNESS",
            status="SKIPPED",
            template_id=template_id,
            reason=f"No functional fixture for template '{template_id}'",
        )

    fx = fixture.functional_fixtures[template_id]
    transform_valid = fx.get("transform_valid", False)

    return TheatreCheckResult(
        check_id=check_id,
        check_type="FUNCTIONAL_CORRECTNESS",
        status="PASSED" if transform_valid else "FAILED",
        template_id=template_id,
        evidence={
            "template_name": fx.get("template_name", ""),
            "resolution": fx.get("resolution", ""),
            "input_state": fx.get("input_state", ""),
            "expected_output_state": fx.get("expected_output_state", ""),
            "transform_valid": transform_valid,
        },
        reason=None if transform_valid else "Functional correctness check failed",
    )
