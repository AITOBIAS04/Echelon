"""Theatre Fixture Loader — load and normalize TREMOR / CORONA fixtures.

Cycle 037e: Theatre Check Execution.

Isolates repo-specific fixture shapes from the generic runner. Each repo
adapter reads the construct.json and builds normalized TheatreFixtureInput
that the runner consumes without repo-specific branching.

V1 uses deterministic replay fixtures embedded here, not live network calls.
"""

import json
import math
from typing import Optional

from backend.schemas.theatre_execution import TheatreFixtureInput
from backend.services.theatre_policy_rules import parse_construct_json, TheatreConstructMeta


def load_fixture(
    construct_slug: str,
    construct_version: str,
    construct_json: str,
    replay_data: Optional[dict] = None,
) -> TheatreFixtureInput:
    """Load and normalize fixture input for a theatre construct.

    Args:
        construct_slug: Construct slug (e.g. "tremor", "corona").
        construct_version: Construct version.
        construct_json: Raw construct.json content.
        replay_data: Optional explicit replay data. When None, uses
            built-in deterministic fixtures.

    Returns:
        TheatreFixtureInput normalized for the runner.
    """
    meta = parse_construct_json(construct_json)

    if replay_data is not None:
        return _from_replay_data(construct_slug, construct_version, meta, replay_data)

    return _build_deterministic_fixture(construct_slug, construct_version, meta)


def _from_replay_data(
    slug: str,
    version: str,
    meta: TheatreConstructMeta,
    data: dict,
) -> TheatreFixtureInput:
    """Build fixture from explicit replay data."""
    return TheatreFixtureInput(
        construct_slug=slug,
        construct_version=version,
        construct_class="theatre",
        settlement_fixtures=data.get("settlement_fixtures", {}),
        oracle_fixtures=data.get("oracle_fixtures", {}),
        calibration_fixture=data.get("calibration_fixture"),
        functional_fixtures=data.get("functional_fixtures", {}),
    )


def _build_deterministic_fixture(
    slug: str,
    version: str,
    meta: TheatreConstructMeta,
) -> TheatreFixtureInput:
    """Build deterministic replay fixtures from construct metadata.

    Generates fixture data from the declared templates and sources.
    Each template gets a settlement fixture; each cross-validation
    source gets an oracle fixture.
    """
    settlement_fixtures = {}
    for template in meta.theatre_templates:
        settlement_fixtures[template.id] = {
            "template_name": template.name,
            "resolution": template.resolution,
            "oracle": template.oracle,
            "predicted_outcome": "YES" if template.resolution == "binary" else "bucket_0",
            "actual_outcome": "YES" if template.resolution == "binary" else "bucket_0",
            "oracle_value": 1.0,
            "closing_position": 0.75,
        }

    oracle_fixtures = {}
    for source in meta.osint_sources:
        if source.role == "cross_validation":
            oracle_fixtures[source.id] = {
                "source_name": source.name,
                "primary_value": 6.2,
                "cross_value": 6.1,
                "delta": 0.1,
                "threshold": 0.5,
            }

    calibration_fixture = None
    if meta.has_brier_scoring:
        calibration_fixture = {
            "brier_type": "binary",
            "predictions": [0.75, 0.60, 0.90, 0.20],
            "outcomes": [1.0, 1.0, 1.0, 0.0],
            # Expected binary Brier: mean of (0.75-1)^2, (0.6-1)^2, (0.9-1)^2, (0.2-0)^2
            # = mean(0.0625, 0.16, 0.01, 0.04) = 0.068125
            "expected_brier": _compute_expected_brier(
                [0.75, 0.60, 0.90, 0.20], [1.0, 1.0, 1.0, 0.0]
            ),
        }

    functional_fixtures = {}
    for template in meta.theatre_templates:
        functional_fixtures[template.id] = {
            "template_name": template.name,
            "resolution": template.resolution,
            "input_state": "OPEN",
            "expected_output_state": "RESOLVED",
            "transform_valid": True,
        }

    return TheatreFixtureInput(
        construct_slug=slug,
        construct_version=version,
        construct_class="theatre",
        settlement_fixtures=settlement_fixtures,
        oracle_fixtures=oracle_fixtures,
        calibration_fixture=calibration_fixture,
        functional_fixtures=functional_fixtures,
    )


def _compute_expected_brier(predictions: list[float], outcomes: list[float]) -> float:
    """Compute expected binary Brier score for fixture validation."""
    if not predictions:
        return 0.0
    total = sum((p - o) ** 2 for p, o in zip(predictions, outcomes))
    return total / len(predictions)
