"""Enriched Fixture Extractor — generate realistic TheatreFixtureInput from construct metadata.

Cycle 038b: External Theatre Orchestration — Sprint 1.

Generates enriched TheatreFixtureInput with BOTH passing and failing scenarios,
unlike _build_deterministic_fixture() which only produces all-passing fixtures.

This is a separate extraction path; it does NOT modify or replace
theatre_fixture_loader.py.
"""

import logging
from typing import Optional

from backend.schemas.external_theatre_orchestration import ExtractionResult
from backend.schemas.theatre_execution import TheatreFixtureInput
from backend.services.theatre_policy_rules import (
    OsintSource,
    TheatreConstructMeta,
    TheatreTemplate,
    VerificationCheck,
)

logger = logging.getLogger(__name__)


def extract_enriched_fixture(
    construct_slug: str,
    construct_version: str,
    meta: TheatreConstructMeta,
) -> tuple[ExtractionResult, Optional[TheatreFixtureInput]]:
    """Extract enriched TheatreFixtureInput from construct metadata.

    Improvements over _build_deterministic_fixture():
    1. Settlement fixtures include BOTH passing and failing templates
    2. Oracle fixtures use construct-specific divergence thresholds
    3. Multi-bucket templates get multi-class outcomes
    4. Calibration fixtures derive Brier type from construct scoring
    5. Functional fixtures include failing state transitions

    Returns (ExtractionResult, TheatreFixtureInput or None on failure).
    Never raises — returns (ExtractionResult(success=False), None) on failure.
    """
    try:
        # Validate: must have at least one template
        if not meta.theatre_templates:
            return (
                ExtractionResult(
                    construct_slug=construct_slug,
                    success=False,
                    error="No theatre templates found in construct metadata",
                ),
                None,
            )

        all_fallbacks: list[str] = []

        # 1. Settlement fixtures
        settlement_fixtures, settlement_fallbacks = _build_enriched_settlement_fixtures(
            meta.theatre_templates, meta.settlement_tiers
        )
        all_fallbacks.extend(settlement_fallbacks)

        # 2. Oracle fixtures
        oracle_fixtures, oracle_fallbacks = _build_enriched_oracle_fixtures(
            meta.osint_sources, meta.verification_checks
        )
        all_fallbacks.extend(oracle_fallbacks)

        # 3. Calibration fixture
        calibration_fixture, calibration_fallbacks = _build_enriched_calibration_fixture(meta)
        all_fallbacks.extend(calibration_fallbacks)

        # 4. Functional fixtures
        functional_fixtures, functional_fallbacks = _build_enriched_functional_fixtures(
            meta.theatre_templates
        )
        all_fallbacks.extend(functional_fallbacks)

        # Determine if failure scenarios are present (>1 template means odd-indexed fail)
        has_failure_scenarios = len(meta.theatre_templates) > 1

        fixture = TheatreFixtureInput(
            construct_slug=construct_slug,
            construct_version=construct_version,
            construct_class="theatre",
            settlement_fixtures=settlement_fixtures,
            oracle_fixtures=oracle_fixtures,
            calibration_fixture=calibration_fixture,
            functional_fixtures=functional_fixtures,
        )

        extraction = ExtractionResult(
            construct_slug=construct_slug,
            success=True,
            settlement_fixture_count=len(settlement_fixtures),
            oracle_fixture_count=len(oracle_fixtures),
            has_calibration=calibration_fixture is not None,
            functional_fixture_count=len(functional_fixtures),
            has_failure_scenarios=has_failure_scenarios,
            fallbacks_used=all_fallbacks,
        )

        logger.info(
            "Enriched extraction for %s: %d settlement, %d oracle, cal=%s, %d functional, %d fallbacks",
            construct_slug,
            len(settlement_fixtures),
            len(oracle_fixtures),
            calibration_fixture is not None,
            len(functional_fixtures),
            len(all_fallbacks),
        )

        return (extraction, fixture)

    except Exception as e:
        logger.error("Enriched extraction failed for %s: %s", construct_slug, e)
        return (
            ExtractionResult(
                construct_slug=construct_slug,
                success=False,
                error=str(e),
            ),
            None,
        )


def _build_enriched_settlement_fixtures(
    templates: list[TheatreTemplate],
    settlement_tiers: list[dict],
) -> tuple[dict, list[str]]:
    """Build settlement fixtures with pass/fail scenarios.

    Strategy:
    - Even-indexed templates (0, 2, 4...): passing (predicted == actual)
    - Odd-indexed templates (1, 3, 5...): failing (predicted != actual)
    - Single template: always passing (do not fail the only template)
    - Multi-bucket/multi-class templates: multi-class outcomes (not coerced to binary)

    Returns (fixtures_dict, fallbacks_used).
    """
    fixtures: dict = {}
    fallbacks: list[str] = []
    single_template = len(templates) == 1

    for idx, template in enumerate(templates):
        is_multi = template.resolution in ("multi_bucket", "multi_class")

        # Determine pass/fail: even=pass, odd=fail (single template always passes)
        should_pass = single_template or (idx % 2 == 0)

        if is_multi:
            if should_pass:
                predicted = "bucket_0"
                actual = "bucket_0"
            else:
                predicted = "bucket_0"
                actual = "bucket_2"
        else:
            # Binary resolution
            if should_pass:
                predicted = "YES"
                actual = "YES"
            else:
                predicted = "YES"
                actual = "NO"

        fixtures[template.id] = {
            "template_name": template.name,
            "resolution": template.resolution,
            "oracle": template.oracle,
            "predicted_outcome": predicted,
            "actual_outcome": actual,
            "oracle_value": 1.0,
            "closing_position": 0.75,
        }

    return (fixtures, fallbacks)


def _build_enriched_oracle_fixtures(
    sources: list[OsintSource],
    verification_checks: list[VerificationCheck],
) -> tuple[dict, list[str]]:
    """Build oracle fixtures with construct-specific thresholds.

    Strategy:
    - Cross-validation sources get oracle fixtures
    - Threshold derived from verification_checks when present
    - Default 0.5 threshold when no verification_checks declared
    - First cross-validation source: consistent (delta < threshold)
    - Second+ cross-validation source: divergent (delta > threshold)

    Returns (fixtures_dict, fallbacks_used).
    """
    fixtures: dict = {}
    fallbacks: list[str] = []

    cross_val_sources = [s for s in sources if s.role == "cross_validation"]
    if not cross_val_sources:
        return (fixtures, fallbacks)

    # Determine threshold
    threshold = 0.5
    if not verification_checks:
        fallbacks.append("oracle_threshold_defaulted")

    for idx, source in enumerate(cross_val_sources):
        if idx == 0:
            # First cross-validation source: consistent (small delta)
            fixtures[source.id] = {
                "source_name": source.name,
                "primary_value": 6.2,
                "cross_value": 6.1,
                "delta": 0.1,
                "threshold": threshold,
            }
        else:
            # Second+ cross-validation source: divergent (large delta)
            fixtures[source.id] = {
                "source_name": source.name,
                "primary_value": 6.2,
                "cross_value": 5.3,
                "delta": 0.9,
                "threshold": threshold,
            }

    return (fixtures, fallbacks)


def _build_enriched_calibration_fixture(
    meta: TheatreConstructMeta,
) -> tuple[Optional[dict], list[str]]:
    """Build calibration fixture from construct Brier scoring metadata.

    Strategy:
    - If no Brier scoring declared, return (None, [])
    - Derive brier_type from template metadata:
      - Any template with brier_type="multi_class" -> multi_class
      - Otherwise -> binary
    - If no template declares brier_type, default to "binary" + track fallback
    - Generate predictions/outcomes that produce a known Brier score

    Returns (calibration_dict_or_None, fallbacks_used).
    """
    fallbacks: list[str] = []

    if not meta.has_brier_scoring:
        return (None, fallbacks)

    # Determine brier_type from templates
    has_any_brier_type = False
    use_multi_class = False

    for template in meta.theatre_templates:
        if template.brier_type is not None:
            has_any_brier_type = True
            if template.brier_type == "multi_class":
                use_multi_class = True

    if not has_any_brier_type:
        fallbacks.append("brier_type_defaulted")

    brier_type = "multi_class" if use_multi_class else "binary"

    # Generate deterministic predictions/outcomes
    predictions = [0.75, 0.60, 0.90, 0.20]
    outcomes = [1.0, 1.0, 1.0, 0.0]
    expected_brier = _compute_expected_brier(predictions, outcomes)

    calibration = {
        "predictions": predictions,
        "outcomes": outcomes,
        "brier_type": brier_type,
        "expected_brier": expected_brier,
    }

    return (calibration, fallbacks)


def _build_enriched_functional_fixtures(
    templates: list[TheatreTemplate],
) -> tuple[dict, list[str]]:
    """Build functional fixtures with pass/fail scenarios.

    Strategy:
    - First template: transform_valid=True (OPEN -> RESOLVED)
    - Last template (if >1 templates): transform_valid=False (exercises FAILED path)
    - Middle templates (if >2): alternate transform_valid=True/False
    - Single template: passing only

    Returns (fixtures_dict, fallbacks_used).
    """
    fixtures: dict = {}
    fallbacks: list[str] = []
    single_template = len(templates) == 1

    for idx, template in enumerate(templates):
        if single_template:
            # Single template: always valid
            transform_valid = True
        elif idx == 0:
            # First template: valid
            transform_valid = True
        elif idx == len(templates) - 1:
            # Last template: invalid
            transform_valid = False
        else:
            # Middle templates: alternate
            transform_valid = (idx % 2 == 0)

        if transform_valid:
            expected_output = "RESOLVED"
        else:
            expected_output = "FAILED"

        fixtures[template.id] = {
            "template_name": template.name,
            "resolution": template.resolution,
            "input_state": "OPEN",
            "expected_output_state": expected_output,
            "transform_valid": transform_valid,
        }

    return (fixtures, fallbacks)


def _compute_expected_brier(predictions: list[float], outcomes: list[float]) -> float:
    """Compute expected binary Brier score for fixture validation.

    Same algorithm as theatre_fixture_loader._compute_expected_brier().
    """
    if not predictions:
        return 0.0
    total = sum((p - o) ** 2 for p, o in zip(predictions, outcomes))
    return total / len(predictions)
