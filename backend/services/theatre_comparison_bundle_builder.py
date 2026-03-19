"""Bundle builder — transforms 037e theatre execution into comparison bundles.

Cycle 038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

Maps TheatreExecutionResult + TheatreFixtureInput → ExecutedTheatreComparisonBundle
using the 10-step algorithm from SDD §2.2.
"""

from typing import Optional

from backend.schemas.theatre_execution import (
    TheatreExecutionResult,
    TheatreFixtureInput,
)
from backend.schemas.theatre_comparison_bundle import (
    ExecutedTheatreComparisonBundle,
    TheatreCheckSummary,
    TheatreExecutionSummary,
    TheatreScopeKey,
)

CRITICAL_CHECK_TYPES = {"SETTLEMENT_ACCURACY", "ORACLE_CONSISTENCY"}


def build_comparison_bundle(
    execution_result: TheatreExecutionResult,
    fixture_input: TheatreFixtureInput,
    certificate_id: Optional[str] = None,
    event_keys: Optional[list[str]] = None,
    scope_keys: Optional[list[TheatreScopeKey]] = None,
) -> ExecutedTheatreComparisonBundle:
    """Transform 037e execution result into normalized comparison bundle.

    10-step mapping (SDD §2.2):
    1. Identity from execution_result / fixture_input
    2. Template IDs from fixture settlement + functional keys
    3. Oracle source IDs from fixture oracle keys
    4. Event keys — caller-provided shared event identifiers, with
       template IDs as fallback (template IDs are construct-specific
       and won't match across theatres)
    5. Scope keys — caller-provided or extracted from evidence
    6. Settlement state from check results
    7. Settlement outcomes from SETTLEMENT_ACCURACY evidence
    8. Oracle values from ORACLE_CONSISTENCY evidence
    9. Execution summary projected from TheatreExecutionResult
    10. Confidence signals from CALIBRATION_VALIDITY evidence

    Args:
        event_keys: Shared real-world event identifiers that are consistent
            across theatre constructs. When not provided, falls back to
            settlement template IDs (which are construct-specific).
        scope_keys: Shared scope identifiers (region, entity, time window).
            When not provided, attempts extraction from evidence metadata.
    """
    # 1. Identity
    slug = execution_result.construct_slug
    version = fixture_input.construct_version

    # 2. Template IDs
    template_ids = sorted(
        set(fixture_input.settlement_fixtures.keys())
        | set(fixture_input.functional_fixtures.keys())
    )

    # 3. Oracle source IDs
    oracle_source_ids = sorted(fixture_input.oracle_fixtures.keys())

    # 4. Event keys — prefer caller-provided shared keys over template IDs
    resolved_event_keys = (
        sorted(event_keys) if event_keys is not None
        else sorted(fixture_input.settlement_fixtures.keys())
    )

    # 5. Scope keys — prefer caller-provided over evidence extraction
    resolved_scope_keys = (
        scope_keys if scope_keys is not None
        else _extract_scope_keys(execution_result)
    )

    # 6. Settlement state
    settlement_state = _derive_settlement_state(execution_result)

    # 7. Settlement outcomes
    settlement_outcomes = _extract_settlement_outcomes(execution_result)

    # 8. Oracle values
    oracle_values = _extract_oracle_values(execution_result)

    # 9. Execution summary
    execution_summary = _build_execution_summary(execution_result)

    # 10. Confidence signals
    confidence_signals = _extract_confidence_signals(execution_result)

    # 11. Provenance refs — all executed check IDs
    provenance_refs = [r.check_id for r in execution_result.check_results]

    return ExecutedTheatreComparisonBundle(
        construct_slug=slug,
        construct_version=version,
        certificate_id=certificate_id,
        template_ids=template_ids,
        oracle_source_ids=oracle_source_ids,
        event_keys=resolved_event_keys,
        scope_keys=resolved_scope_keys,
        settlement_state=settlement_state,
        settlement_outcomes=settlement_outcomes,
        oracle_values=oracle_values,
        execution_summary=execution_summary,
        provenance_refs=provenance_refs,
        confidence_signals=confidence_signals,
    )


def _derive_settlement_state(result: TheatreExecutionResult) -> Optional[str]:
    """Derive settlement state from SETTLEMENT_ACCURACY check results.

    - Any FAILED → DISPUTED
    - All PASSED → SETTLED
    - No settlement checks → PENDING
    """
    settlement_checks = [
        r for r in result.check_results
        if r.check_type == "SETTLEMENT_ACCURACY"
    ]
    if not settlement_checks:
        return "PENDING"
    if any(r.status == "FAILED" for r in settlement_checks):
        return "DISPUTED"
    if all(r.status == "PASSED" for r in settlement_checks):
        return "SETTLED"
    return "PENDING"


def _extract_settlement_outcomes(result: TheatreExecutionResult) -> dict:
    """Map SETTLEMENT_ACCURACY evidence → {template_id: outcome_dict}."""
    outcomes = {}
    for r in result.check_results:
        if r.check_type == "SETTLEMENT_ACCURACY" and r.template_id and r.evidence:
            outcomes[r.template_id] = {
                "predicted_outcome": r.evidence.get("predicted_outcome"),
                "actual_outcome": r.evidence.get("actual_outcome"),
                "resolution": r.evidence.get("resolution"),
            }
    return outcomes


def _extract_oracle_values(result: TheatreExecutionResult) -> dict:
    """Map ORACLE_CONSISTENCY evidence → {source_id: value_dict}."""
    values = {}
    for r in result.check_results:
        if r.check_type == "ORACLE_CONSISTENCY" and r.source_id and r.evidence:
            values[r.source_id] = {
                "value": r.evidence.get("primary_value"),
                "queried_at": None,
                "is_provisional": False,
            }
    return values


def _extract_confidence_signals(result: TheatreExecutionResult) -> dict:
    """Extract from CALIBRATION_VALIDITY evidence."""
    signals = {}
    for r in result.check_results:
        if r.check_type == "CALIBRATION_VALIDITY" and r.evidence:
            signals["brier_score"] = r.evidence.get("computed_brier")
            signals["calibration_valid"] = r.status == "PASSED"
    return signals


def _extract_scope_keys(result: TheatreExecutionResult) -> list[TheatreScopeKey]:
    """Extract scope keys from evidence metadata when present.

    Currently returns empty — scope keys are populated by the caller
    or from external metadata, not from check evidence alone.
    Future cycles may extract region/entity from settlement evidence.
    """
    return []


def _build_execution_summary(result: TheatreExecutionResult) -> TheatreExecutionSummary:
    """Project TheatreExecutionResult properties into TheatreExecutionSummary."""
    checks = []
    for r in result.check_results:
        checks.append(TheatreCheckSummary(
            check_type=r.check_type,
            status=r.status,
            is_critical=r.check_type in CRITICAL_CHECK_TYPES,
            evidence=r.evidence or {},
        ))

    return TheatreExecutionSummary(
        checks=checks,
        executed_count=result.total_executed,
        passed_count=result.total_passed,
        failed_count=result.total_failed,
        skipped_count=result.total_skipped,
        has_critical_failures=result.has_critical_failures,
    )
