"""Deterministic fixture factories for cross-theatre comparison testing.

Cycle 038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

TREMOR and CORONA share:
- One event key: "us-equities-q1-2026"
- One scope key: TheatreScopeKey(scope_type="region", scope_value="us-equities")

This enables both same-event and overlap-scope candidate generation in tests.
"""

from backend.schemas.theatre_execution import (
    TheatreCheckResult,
    TheatreExecutionResult,
    TheatreFixtureInput,
)
from backend.schemas.theatre_comparison_bundle import (
    ExecutedTheatreComparisonBundle,
    TheatreCheckSummary,
    TheatreExecutionSummary,
    TheatreScopeKey,
)

# ── Shared constants ──

SHARED_EVENT_KEY = "us-equities-q1-2026"
SHARED_SCOPE_KEY = TheatreScopeKey(scope_type="region", scope_value="us-equities")


# ── TREMOR fixtures ──

def make_tremor_execution_result() -> TheatreExecutionResult:
    """TREMOR: 2 settlement checks (1 PASSED, 1 FAILED), 1 oracle PASSED."""
    return TheatreExecutionResult(
        construct_slug="tremor",
        check_results=[
            TheatreCheckResult(
                check_id="theatre:SETTLEMENT_ACCURACY:tmpl-eq-001",
                check_type="SETTLEMENT_ACCURACY",
                status="PASSED",
                template_id="tmpl-eq-001",
                evidence={
                    "predicted_outcome": "UP",
                    "actual_outcome": "UP",
                    "oracle_value": 1.02,
                    "oracle": "chainlink-eth-usd",
                    "resolution": "CORRECT",
                },
            ),
            TheatreCheckResult(
                check_id="theatre:SETTLEMENT_ACCURACY:tmpl-eq-002",
                check_type="SETTLEMENT_ACCURACY",
                status="FAILED",
                template_id="tmpl-eq-002",
                evidence={
                    "predicted_outcome": "DOWN",
                    "actual_outcome": "UP",
                    "oracle_value": 1.05,
                    "oracle": "chainlink-btc-usd",
                    "resolution": "INCORRECT",
                },
                reason="Predicted DOWN but actual was UP",
            ),
            TheatreCheckResult(
                check_id="theatre:ORACLE_CONSISTENCY:src-chainlink",
                check_type="ORACLE_CONSISTENCY",
                status="PASSED",
                source_id="src-chainlink",
                evidence={
                    "primary_value": 1.02,
                    "cross_value": 1.021,
                    "delta": 0.001,
                    "threshold": 0.05,
                    "source_name": "chainlink",
                },
            ),
        ],
    )


def make_tremor_fixture_input() -> TheatreFixtureInput:
    """Matching fixture input for TREMOR execution."""
    return TheatreFixtureInput(
        construct_slug="tremor",
        construct_version="1.0.0",
        construct_class="theatre",
        settlement_fixtures={
            "tmpl-eq-001": {
                "predicted_outcome": "UP",
                "actual_outcome": "UP",
                "oracle_value": 1.02,
                "oracle": "chainlink-eth-usd",
                "resolution": "CORRECT",
            },
            "tmpl-eq-002": {
                "predicted_outcome": "DOWN",
                "actual_outcome": "UP",
                "oracle_value": 1.05,
                "oracle": "chainlink-btc-usd",
                "resolution": "INCORRECT",
            },
        },
        oracle_fixtures={
            "src-chainlink": {
                "primary_value": 1.02,
                "cross_value": 1.021,
                "threshold": 0.05,
                "source_name": "chainlink",
            },
        },
    )


# ── CORONA fixtures ──

def make_corona_execution_result() -> TheatreExecutionResult:
    """CORONA: 1 settlement PASSED, 1 oracle PASSED, 1 calibration PASSED."""
    return TheatreExecutionResult(
        construct_slug="corona",
        check_results=[
            TheatreCheckResult(
                check_id="theatre:SETTLEMENT_ACCURACY:tmpl-pandemic-001",
                check_type="SETTLEMENT_ACCURACY",
                status="PASSED",
                template_id="tmpl-pandemic-001",
                evidence={
                    "predicted_outcome": "CONTAINED",
                    "actual_outcome": "CONTAINED",
                    "oracle_value": 0.85,
                    "oracle": "who-disease-tracker",
                    "resolution": "CORRECT",
                },
            ),
            TheatreCheckResult(
                check_id="theatre:ORACLE_CONSISTENCY:src-who",
                check_type="ORACLE_CONSISTENCY",
                status="PASSED",
                source_id="src-who",
                evidence={
                    "primary_value": 0.85,
                    "cross_value": 0.84,
                    "delta": 0.01,
                    "threshold": 0.1,
                    "source_name": "who",
                },
            ),
            TheatreCheckResult(
                check_id="theatre:CALIBRATION_VALIDITY:brier",
                check_type="CALIBRATION_VALIDITY",
                status="PASSED",
                evidence={
                    "computed_brier": 0.18,
                    "expected_brier": 0.25,
                    "brier_type": "standard",
                    "n_predictions": 50,
                },
            ),
        ],
    )


def make_corona_fixture_input() -> TheatreFixtureInput:
    """Matching fixture input for CORONA execution."""
    return TheatreFixtureInput(
        construct_slug="corona",
        construct_version="2.1.0",
        construct_class="theatre",
        settlement_fixtures={
            "tmpl-pandemic-001": {
                "predicted_outcome": "CONTAINED",
                "actual_outcome": "CONTAINED",
                "oracle_value": 0.85,
                "oracle": "who-disease-tracker",
                "resolution": "CORRECT",
            },
        },
        oracle_fixtures={
            "src-who": {
                "primary_value": 0.85,
                "cross_value": 0.84,
                "threshold": 0.1,
                "source_name": "who",
            },
        },
        calibration_fixture={
            "predictions": [0.7, 0.8, 0.9],
            "outcomes": [1, 1, 0],
            "expected_brier": 0.25,
            "brier_type": "standard",
        },
    )


# ── Pre-built comparison bundles ──

def make_tremor_bundle() -> ExecutedTheatreComparisonBundle:
    """Pre-built TREMOR comparison bundle with shared event/scope keys."""
    return ExecutedTheatreComparisonBundle(
        construct_slug="tremor",
        construct_version="1.0.0",
        certificate_id="cert-tremor-001",
        template_ids=["tmpl-eq-001", "tmpl-eq-002"],
        oracle_source_ids=["src-chainlink"],
        event_keys=[SHARED_EVENT_KEY, "btc-futures-q1-2026"],
        scope_keys=[
            SHARED_SCOPE_KEY,
            TheatreScopeKey(scope_type="entity", scope_value="btc-usd"),
        ],
        settlement_state="DISPUTED",
        settlement_outcomes={
            "tmpl-eq-001": {
                "predicted_outcome": "UP",
                "actual_outcome": "UP",
                "resolution": "CORRECT",
            },
            "tmpl-eq-002": {
                "predicted_outcome": "DOWN",
                "actual_outcome": "UP",
                "resolution": "INCORRECT",
            },
        },
        oracle_values={
            "src-chainlink": {
                "value": 1.02,
                "queried_at": None,
                "is_provisional": False,
            },
        },
        execution_summary=TheatreExecutionSummary(
            checks=[
                TheatreCheckSummary(
                    check_type="SETTLEMENT_ACCURACY",
                    status="PASSED",
                    is_critical=True,
                    evidence={"resolution": "CORRECT"},
                ),
                TheatreCheckSummary(
                    check_type="SETTLEMENT_ACCURACY",
                    status="FAILED",
                    is_critical=True,
                    evidence={"resolution": "INCORRECT"},
                ),
                TheatreCheckSummary(
                    check_type="ORACLE_CONSISTENCY",
                    status="PASSED",
                    is_critical=True,
                    evidence={"delta": 0.001},
                ),
            ],
            executed_count=3,
            passed_count=2,
            failed_count=1,
            skipped_count=0,
            has_critical_failures=True,
        ),
        provenance_refs=[
            "theatre:SETTLEMENT_ACCURACY:tmpl-eq-001",
            "theatre:SETTLEMENT_ACCURACY:tmpl-eq-002",
            "theatre:ORACLE_CONSISTENCY:src-chainlink",
        ],
        confidence_signals={},
    )


def make_corona_bundle() -> ExecutedTheatreComparisonBundle:
    """Pre-built CORONA comparison bundle with shared event/scope keys."""
    return ExecutedTheatreComparisonBundle(
        construct_slug="corona",
        construct_version="2.1.0",
        certificate_id="cert-corona-001",
        template_ids=["tmpl-pandemic-001"],
        oracle_source_ids=["src-who"],
        event_keys=[SHARED_EVENT_KEY],
        scope_keys=[
            SHARED_SCOPE_KEY,
            TheatreScopeKey(scope_type="entity", scope_value="covid-variant-x"),
        ],
        settlement_state="SETTLED",
        settlement_outcomes={
            "tmpl-pandemic-001": {
                "predicted_outcome": "CONTAINED",
                "actual_outcome": "CONTAINED",
                "resolution": "CORRECT",
            },
        },
        oracle_values={
            "src-who": {
                "value": 0.85,
                "queried_at": None,
                "is_provisional": False,
            },
        },
        execution_summary=TheatreExecutionSummary(
            checks=[
                TheatreCheckSummary(
                    check_type="SETTLEMENT_ACCURACY",
                    status="PASSED",
                    is_critical=True,
                    evidence={"resolution": "CORRECT"},
                ),
                TheatreCheckSummary(
                    check_type="ORACLE_CONSISTENCY",
                    status="PASSED",
                    is_critical=True,
                    evidence={"delta": 0.01},
                ),
                TheatreCheckSummary(
                    check_type="CALIBRATION_VALIDITY",
                    status="PASSED",
                    is_critical=False,
                    evidence={"computed_brier": 0.18},
                ),
            ],
            executed_count=3,
            passed_count=3,
            failed_count=0,
            skipped_count=0,
            has_critical_failures=False,
        ),
        provenance_refs=[
            "theatre:SETTLEMENT_ACCURACY:tmpl-pandemic-001",
            "theatre:ORACLE_CONSISTENCY:src-who",
            "theatre:CALIBRATION_VALIDITY:brier",
        ],
        confidence_signals={
            "brier_score": 0.18,
            "calibration_valid": True,
        },
    )
