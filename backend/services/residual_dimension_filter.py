"""Residual Dimension Filter — separates deterministic from rubric-scored dimensions.

Cycle 037b: Multi-Evaluator Orchestration + Residual Scoring.

Given an EvaluationContract's planned checks and a set of deterministic execution
results, this filter returns only the dimensions that still require multi-evaluator
scoring. Deterministic-covered dimensions are excluded to prevent double-judging.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check types that are deterministic — their dimensions should NOT go to evaluators
_DETERMINISTIC_CHECK_TYPES = frozenset({"ANCHOR", "BENCHMARK"})


@dataclass(frozen=True)
class ResidualDimension:
    """A dimension that requires multi-evaluator scoring."""
    dimension: str
    source_check_id: str
    source_check_type: str
    critical: bool


def filter_residual_dimensions(
    planned_checks: list[dict],
    executed_results: dict,
) -> list[ResidualDimension]:
    """Filter planned checks down to dimensions needing evaluator orchestration.

    A dimension is residual if:
    1. Its check type is RUBRIC (non-deterministic)
    2. It was NOT already executed deterministically

    Args:
        planned_checks: Contract's planned_checks list from EvaluationContract.
            Each entry: {check_id, check_type, domain, source, critical, ...}
        executed_results: Dict mapping domain → score for deterministically
            executed checks. Domains present here are already covered.

    Returns:
        List of ResidualDimension entries for dimensions needing multi-evaluator scoring.
    """
    deterministic_domains = _collect_deterministic_domains(planned_checks, executed_results)
    residuals: list[ResidualDimension] = []

    for check in planned_checks:
        check_type = check.get("check_type", "")
        domain = check.get("domain", "")
        check_id = check.get("check_id", "")
        critical = check.get("critical", False)

        # Skip deterministic check types entirely
        if check_type in _DETERMINISTIC_CHECK_TYPES:
            continue

        # Skip wildcard-domain checks (structural, not dimension-scoped)
        if domain == "*":
            continue

        # Skip dimensions already covered by deterministic execution
        if domain in deterministic_domains:
            logger.debug(
                "Dimension %s covered by deterministic check, excluding from residual",
                domain,
            )
            continue

        residuals.append(ResidualDimension(
            dimension=domain,
            source_check_id=check_id,
            source_check_type=check_type,
            critical=critical,
        ))

    # Deduplicate by dimension name (preserve first occurrence)
    seen: set[str] = set()
    deduped: list[ResidualDimension] = []
    for r in residuals:
        if r.dimension not in seen:
            seen.add(r.dimension)
            deduped.append(r)

    logger.info(
        "Residual dimension filter: %d planned → %d deterministic, %d residual",
        len(planned_checks), len(deterministic_domains), len(deduped),
    )
    return deduped


def _collect_deterministic_domains(
    planned_checks: list[dict],
    executed_results: dict,
) -> set[str]:
    """Collect domains covered by deterministic checks that have execution results.

    A domain is deterministically covered if:
    - A planned check of type ANCHOR or BENCHMARK targets it
    - AND the domain has an execution result (score or status)
    """
    deterministic_domains: set[str] = set()

    for check in planned_checks:
        check_type = check.get("check_type", "")
        domain = check.get("domain", "")

        if check_type not in _DETERMINISTIC_CHECK_TYPES:
            continue
        if domain == "*":
            continue
        if domain in executed_results:
            deterministic_domains.add(domain)

    return deterministic_domains
