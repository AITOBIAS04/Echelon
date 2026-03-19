"""Tests for Cycle 038b: External Theatre Orchestration.

Sprint 0: Schemas + extraction contracts (7 tests).
Sprint 1: Enriched fixture extraction (11 tests).
"""

import json
import sys
import unittest
from unittest.mock import MagicMock

# Mock the database connection module before importing anything.
_mock_base_module = MagicMock()
from sqlalchemy.orm import declarative_base
_real_base = declarative_base()
_mock_base_module.Base = _real_base
sys.modules.setdefault("backend.database.connection", _mock_base_module)
sys.modules.setdefault("backend.database.config", MagicMock())
_mock_base_module.engine = MagicMock()
_mock_base_module.async_session_maker = MagicMock()
_mock_base_module.get_session = MagicMock()
_mock_base_module.get_db = MagicMock()
_mock_base_module.init_db = MagicMock()
_mock_base_module.close_db = MagicMock()

from backend.schemas.external_theatre_orchestration import (
    BuilderFeedbackItem,
    BuilderFeedbackReport,
    ExternalTheatreInput,
    ExternalTheatrePreparationRequest,
    ExternalTheatrePreparationResult,
    ExtractionResult,
    TheatrePreparationEntry,
)
from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreScopeKey,
)


# ═══════════════════════════════════════════════════════════════════
# Sprint 0 — Schemas + Extraction Contracts (7 tests)
# ═══════════════════════════════════════════════════════════════════


class TestExternalTheatreOrchestrationSchemas(unittest.TestCase):
    """Sprint 0: Validate all 7 Pydantic models for the orchestration surface."""

    def test_external_theatre_input_constructs(self):
        """ExternalTheatreInput accepts required fields; optional defaults to None."""
        inp = ExternalTheatreInput(
            construct_slug="tremor",
            construct_version="0.1.0",
            construct_json='{"name": "TREMOR"}',
        )
        self.assertEqual(inp.construct_slug, "tremor")
        self.assertEqual(inp.construct_version, "0.1.0")
        self.assertEqual(inp.construct_json, '{"name": "TREMOR"}')
        self.assertIsNone(inp.construct_json_path)

    def test_preparation_request_defaults(self):
        """ExternalTheatrePreparationRequest defaults event_keys=[], scope_keys=[], certificate_id=None."""
        inp = ExternalTheatreInput(
            construct_slug="tremor",
            construct_version="0.1.0",
            construct_json="{}",
        )
        req = ExternalTheatrePreparationRequest(theatres=[inp])
        self.assertEqual(req.event_keys, [])
        self.assertEqual(req.scope_keys, [])
        self.assertIsNone(req.certificate_id)
        self.assertEqual(len(req.theatres), 1)

    def test_preparation_result_serializes(self):
        """ExternalTheatrePreparationResult round-trips through model_dump."""
        entry = TheatrePreparationEntry(
            construct_slug="tremor",
            construct_version="0.1.0",
            execution_passed=True,
        )
        result = ExternalTheatrePreparationResult(
            theatres=[entry],
            total_theatres=1,
            total_successful=1,
        )
        dumped = result.model_dump()
        self.assertEqual(dumped["total_theatres"], 1)
        self.assertEqual(dumped["total_successful"], 1)
        self.assertEqual(len(dumped["theatres"]), 1)
        self.assertEqual(dumped["theatres"][0]["construct_slug"], "tremor")

        # Round-trip
        restored = ExternalTheatrePreparationResult(**dumped)
        self.assertEqual(restored.total_theatres, 1)
        self.assertEqual(restored.theatres[0].construct_slug, "tremor")
        self.assertEqual(restored.theatres[0].execution_passed, True)

    def test_extraction_result_success_shape(self):
        """ExtractionResult with success=True and fixture counts."""
        er = ExtractionResult(
            construct_slug="tremor",
            success=True,
            settlement_fixture_count=5,
            oracle_fixture_count=2,
            has_calibration=True,
            functional_fixture_count=5,
            has_failure_scenarios=True,
        )
        self.assertTrue(er.success)
        self.assertEqual(er.settlement_fixture_count, 5)
        self.assertEqual(er.oracle_fixture_count, 2)
        self.assertTrue(er.has_calibration)
        self.assertEqual(er.functional_fixture_count, 5)
        self.assertTrue(er.has_failure_scenarios)
        self.assertEqual(er.fallbacks_used, [])
        self.assertIsNone(er.error)

    def test_extraction_result_failure_shape(self):
        """ExtractionResult with success=False and error message."""
        er = ExtractionResult(
            construct_slug="tremor",
            success=False,
            error="parse failed",
        )
        self.assertFalse(er.success)
        self.assertEqual(er.error, "parse failed")
        self.assertEqual(er.settlement_fixture_count, 0)
        self.assertEqual(er.oracle_fixture_count, 0)
        self.assertFalse(er.has_calibration)
        self.assertEqual(er.functional_fixture_count, 0)
        self.assertFalse(er.has_failure_scenarios)

    def test_builder_feedback_report_categories(self):
        """BuilderFeedbackReport distinguishes required/optional/extraction items."""
        required = BuilderFeedbackItem(
            category="required",
            field="theatre_templates",
            status="present",
            message="Templates found",
        )
        optional = BuilderFeedbackItem(
            category="optional",
            field="verification_checks",
            status="missing",
            message="No verification checks declared",
        )
        extraction = BuilderFeedbackItem(
            category="extraction",
            field="settlement_fixtures",
            status="enriched",
            message="5 settlement fixtures generated",
        )
        report = BuilderFeedbackReport(
            construct_slug="tremor",
            required_items=[required],
            optional_items=[optional],
            extraction_items=[extraction],
            overall_readiness="DEGRADED",
        )
        self.assertEqual(len(report.required_items), 1)
        self.assertEqual(len(report.optional_items), 1)
        self.assertEqual(len(report.extraction_items), 1)
        self.assertEqual(report.required_items[0].category, "required")
        self.assertEqual(report.optional_items[0].category, "optional")
        self.assertEqual(report.extraction_items[0].category, "extraction")
        self.assertEqual(report.overall_readiness, "DEGRADED")

    def test_builder_feedback_readiness_states(self):
        """Readiness field accepts READY, DEGRADED, and BLOCKED."""
        for readiness in ("READY", "DEGRADED", "BLOCKED"):
            report = BuilderFeedbackReport(
                construct_slug="test",
                overall_readiness=readiness,
            )
            self.assertEqual(report.overall_readiness, readiness)
            # Verify default empty lists
            self.assertEqual(report.required_items, [])
            self.assertEqual(report.optional_items, [])
            self.assertEqual(report.extraction_items, [])


# ═══════════════════════════════════════════════════════════════════
# Sprint 1 — Enriched Fixture Extraction (11 tests)
# ═══════════════════════════════════════════════════════════════════

from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture
from backend.services.theatre_policy_rules import (
    parse_construct_json,
    TheatreConstructMeta,
    TheatreTemplate,
    OsintSource,
    VerificationCheck,
)


# ── Inline construct.json content for TREMOR and CORONA ───────────

TREMOR_CONSTRUCT_JSON = json.dumps({
    "name": "tremor",
    "version": "0.1.0",
    "echelon": {
        "verification_checks": [
            {
                "check": "evidence_bundle_accuracy",
                "ground_truth": "USGS reviewed catalog",
                "description": "Magnitude, location, and depth match USGS reviewed values",
            },
            {
                "check": "settlement_tier_correctness",
                "ground_truth": "USGS event status field",
                "description": "Settlement tier matches actual USGS review state",
            },
            {
                "check": "brier_score_computation",
                "ground_truth": "Theatre outcome vs closing position",
                "description": "Brier scores are mathematically correct",
            },
            {
                "check": "cross_validation_fidelity",
                "ground_truth": "EMSC magnitude for same event",
                "description": "Cross-validation divergence values match actual difference",
            },
            {
                "check": "theatre_resolution_integrity",
                "ground_truth": "USGS reviewed catalog query at close time",
                "description": "Theatre outcomes match USGS catalog",
            },
        ],
        "theatre_templates": [
            {
                "id": "magnitude_gate",
                "name": "Magnitude Gate",
                "resolution": "binary",
                "oracle": "USGS reviewed catalog",
                "brier_type": "binary",
            },
            {
                "id": "aftershock_cascade",
                "name": "Aftershock Cascade",
                "resolution": "multi_bucket",
                "oracle": "USGS reviewed catalog",
                "brier_type": "multi_class",
            },
            {
                "id": "swarm_watch",
                "name": "Swarm Watch",
                "resolution": "binary",
                "oracle": "USGS reviewed catalog",
                "brier_type": "binary",
            },
            {
                "id": "depth_regime",
                "name": "Depth Regime",
                "resolution": "binary",
                "oracle": "USGS reviewed depth",
                "brier_type": "binary",
            },
            {
                "id": "oracle_divergence",
                "name": "Oracle Divergence",
                "resolution": "binary",
                "oracle": "USGS automatic vs reviewed comparison",
                "brier_type": "binary",
            },
        ],
        "osint_sources": [
            {
                "id": "usgs_neic",
                "name": "USGS NEIC",
                "role": "primary",
            },
            {
                "id": "emsc",
                "name": "EMSC",
                "role": "cross_validation",
            },
            {
                "id": "iris_dmc",
                "name": "IRIS DMC",
                "role": "cross_validation",
            },
        ],
        "settlement_tiers": [
            {"tier": 1, "name": "oracle", "condition": "status=reviewed"},
            {"tier": 2, "name": "provisional_mature", "condition": "status=automatic AND age>2h"},
            {"tier": 3, "name": "market_freeze", "condition": "theatre_expiring"},
        ],
    },
    "rlmf": {
        "exports": ["brier_score", "position_history"],
    },
})


CORONA_CONSTRUCT_JSON = json.dumps({
    "slug": "corona",
    "name": "CORONA",
    "version": "0.1.0",
    "data_sources": [
        {
            "name": "NOAA SWPC",
            "role": "primary",
        },
        {
            "name": "NASA DONKI",
            "role": "cross_validation",
        },
        {
            "name": "GFZ Potsdam",
            "role": "cross_validation",
        },
    ],
    "theatre_templates": [
        {
            "id": "T1",
            "name": "flare_class_gate",
            "type": "binary",
            "resolution": "GOES X-ray + DONKI FLR",
        },
        {
            "id": "T2",
            "name": "geomagnetic_storm_gate",
            "type": "binary",
            "resolution": "Kp index + DONKI GST",
        },
        {
            "id": "T3",
            "name": "cme_arrival",
            "type": "binary",
            "resolution": "L1 solar wind shock signature",
        },
        {
            "id": "T4",
            "name": "proton_event_cascade",
            "type": "multi_class",
            "resolution": "Flare event count",
        },
        {
            "id": "T5",
            "name": "solar_wind_divergence",
            "type": "binary",
            "resolution": "Sustained Bz volatility threshold",
        },
    ],
    "rlmf": {
        "exports": ["brier_score", "position_history", "calibration_bucket", "temporal_analysis"],
    },
})


class TestTremorEnrichedExtraction(unittest.TestCase):
    """Sprint 1: TREMOR enriched fixture extraction (4 tests)."""

    @classmethod
    def setUpClass(cls):
        cls.meta = parse_construct_json(TREMOR_CONSTRUCT_JSON)
        cls.extraction, cls.fixture = extract_enriched_fixture(
            "tremor", "0.1.0", cls.meta
        )

    def test_tremor_enriched_settlement_pass_and_fail(self):
        """TREMOR settlement: 5 fixtures. Even-index pass, odd-index fail. Multi-bucket uses buckets."""
        fx = self.fixture.settlement_fixtures
        self.assertEqual(len(fx), 5)

        # Even-indexed templates PASS (predicted == actual)
        # magnitude_gate (index 0, binary): pass
        self.assertEqual(fx["magnitude_gate"]["predicted_outcome"], "YES")
        self.assertEqual(fx["magnitude_gate"]["actual_outcome"], "YES")

        # swarm_watch (index 2, binary): pass
        self.assertEqual(fx["swarm_watch"]["predicted_outcome"], "YES")
        self.assertEqual(fx["swarm_watch"]["actual_outcome"], "YES")

        # oracle_divergence (index 4, binary): pass
        self.assertEqual(fx["oracle_divergence"]["predicted_outcome"], "YES")
        self.assertEqual(fx["oracle_divergence"]["actual_outcome"], "YES")

        # Odd-indexed templates FAIL (predicted != actual)
        # aftershock_cascade (index 1, multi_bucket): fail with bucket outcomes
        self.assertEqual(fx["aftershock_cascade"]["predicted_outcome"], "bucket_0")
        self.assertEqual(fx["aftershock_cascade"]["actual_outcome"], "bucket_2")
        self.assertNotEqual(
            fx["aftershock_cascade"]["predicted_outcome"],
            fx["aftershock_cascade"]["actual_outcome"],
        )

        # depth_regime (index 3, binary): fail
        self.assertEqual(fx["depth_regime"]["predicted_outcome"], "YES")
        self.assertEqual(fx["depth_regime"]["actual_outcome"], "NO")

        # Verify extraction result counts
        self.assertTrue(self.extraction.success)
        self.assertEqual(self.extraction.settlement_fixture_count, 5)
        self.assertTrue(self.extraction.has_failure_scenarios)

    def test_tremor_enriched_oracle_consistent_and_divergent(self):
        """TREMOR oracle: emsc consistent (delta < threshold), iris_dmc divergent (delta > threshold)."""
        fx = self.fixture.oracle_fixtures
        self.assertEqual(len(fx), 2)

        # emsc (first cross_val): consistent
        self.assertIn("emsc", fx)
        self.assertLess(fx["emsc"]["delta"], fx["emsc"]["threshold"])
        self.assertEqual(fx["emsc"]["primary_value"], 6.2)
        self.assertEqual(fx["emsc"]["cross_value"], 6.1)

        # iris_dmc (second cross_val): divergent
        self.assertIn("iris_dmc", fx)
        self.assertGreater(fx["iris_dmc"]["delta"], fx["iris_dmc"]["threshold"])
        self.assertEqual(fx["iris_dmc"]["primary_value"], 6.2)
        self.assertEqual(fx["iris_dmc"]["cross_value"], 5.3)

        # TREMOR has verification_checks, so no threshold fallback
        self.assertNotIn("oracle_threshold_defaulted", self.extraction.fallbacks_used)

    def test_tremor_enriched_calibration_multi_class(self):
        """TREMOR calibration: brier_type=multi_class (aftershock_cascade declares it)."""
        cal = self.fixture.calibration_fixture
        self.assertIsNotNone(cal)
        self.assertEqual(cal["brier_type"], "multi_class")
        self.assertIsInstance(cal["expected_brier"], float)
        self.assertGreaterEqual(cal["expected_brier"], 0.0)
        self.assertIn("predictions", cal)
        self.assertIn("outcomes", cal)
        self.assertEqual(len(cal["predictions"]), len(cal["outcomes"]))
        self.assertTrue(self.extraction.has_calibration)

    def test_tremor_enriched_functional_pass_and_fail(self):
        """TREMOR functional: 5 fixtures. First valid, last invalid."""
        fx = self.fixture.functional_fixtures
        self.assertEqual(len(fx), 5)

        # First template (magnitude_gate): valid
        self.assertTrue(fx["magnitude_gate"]["transform_valid"])
        self.assertEqual(fx["magnitude_gate"]["input_state"], "OPEN")
        self.assertEqual(fx["magnitude_gate"]["expected_output_state"], "RESOLVED")

        # Last template (oracle_divergence): invalid
        self.assertFalse(fx["oracle_divergence"]["transform_valid"])
        self.assertEqual(fx["oracle_divergence"]["expected_output_state"], "FAILED")

        self.assertEqual(self.extraction.functional_fixture_count, 5)


class TestCoronaEnrichedExtraction(unittest.TestCase):
    """Sprint 1: CORONA enriched fixture extraction (4 tests)."""

    @classmethod
    def setUpClass(cls):
        cls.meta = parse_construct_json(CORONA_CONSTRUCT_JSON)
        cls.extraction, cls.fixture = extract_enriched_fixture(
            "corona", "0.1.0", cls.meta
        )

    def test_corona_enriched_settlement_pass_and_fail(self):
        """CORONA settlement: 5 fixtures. Even-index pass, odd-index fail. T4 (multi_class) uses buckets."""
        fx = self.fixture.settlement_fixtures
        self.assertEqual(len(fx), 5)

        # T1 (index 0, binary): pass
        self.assertEqual(fx["T1"]["predicted_outcome"], "YES")
        self.assertEqual(fx["T1"]["actual_outcome"], "YES")

        # T3 (index 2, binary): pass
        self.assertEqual(fx["T3"]["predicted_outcome"], "YES")
        self.assertEqual(fx["T3"]["actual_outcome"], "YES")

        # T5 (index 4, binary): pass
        self.assertEqual(fx["T5"]["predicted_outcome"], "YES")
        self.assertEqual(fx["T5"]["actual_outcome"], "YES")

        # T2 (index 1, binary): fail
        self.assertEqual(fx["T2"]["predicted_outcome"], "YES")
        self.assertEqual(fx["T2"]["actual_outcome"], "NO")

        # T4 (index 3, multi_class): fail with bucket outcomes
        self.assertEqual(fx["T4"]["predicted_outcome"], "bucket_0")
        self.assertEqual(fx["T4"]["actual_outcome"], "bucket_2")

    def test_corona_enriched_oracle_with_default_threshold(self):
        """CORONA oracle: nasa_donki consistent, gfz_potsdam divergent. Fallback recorded."""
        fx = self.fixture.oracle_fixtures
        self.assertEqual(len(fx), 2)

        # nasa_donki (first cross_val): consistent
        self.assertIn("nasa_donki", fx)
        self.assertLess(fx["nasa_donki"]["delta"], fx["nasa_donki"]["threshold"])

        # gfz_potsdam (second cross_val): divergent
        self.assertIn("gfz_potsdam", fx)
        self.assertGreater(fx["gfz_potsdam"]["delta"], fx["gfz_potsdam"]["threshold"])

        # CORONA has no verification_checks, so threshold defaulted
        self.assertIn("oracle_threshold_defaulted", self.extraction.fallbacks_used)

    def test_corona_enriched_calibration_binary(self):
        """CORONA calibration: brier_type=binary (no template declares brier_type directly)."""
        cal = self.fixture.calibration_fixture
        self.assertIsNotNone(cal)
        self.assertEqual(cal["brier_type"], "binary")
        self.assertIsInstance(cal["expected_brier"], float)
        self.assertGreaterEqual(cal["expected_brier"], 0.0)
        self.assertTrue(self.extraction.has_calibration)

        # CORONA templates don't declare brier_type, so it should be defaulted
        self.assertIn("brier_type_defaulted", self.extraction.fallbacks_used)

    def test_corona_enriched_functional_pass_and_fail(self):
        """CORONA functional: 5 fixtures. First (T1) valid, last (T5) invalid."""
        fx = self.fixture.functional_fixtures
        self.assertEqual(len(fx), 5)

        # T1 (first): valid
        self.assertTrue(fx["T1"]["transform_valid"])
        self.assertEqual(fx["T1"]["expected_output_state"], "RESOLVED")

        # T5 (last): invalid
        self.assertFalse(fx["T5"]["transform_valid"])
        self.assertEqual(fx["T5"]["expected_output_state"], "FAILED")


class TestExtractionEdgeCases(unittest.TestCase):
    """Sprint 1: Extraction edge cases (3 tests)."""

    def test_extraction_missing_construct_json(self):
        """parse_construct_json raises ValueError on empty/invalid JSON. Extraction handles gracefully."""
        # Verify parse_construct_json raises on invalid input
        with self.assertRaises(ValueError):
            parse_construct_json("")

        with self.assertRaises(ValueError):
            parse_construct_json("{bad json")

        # The extractor itself gets a meta; if meta were somehow broken,
        # it would return success=False. Here we test via a minimal
        # construct that has no templates (which parse_construct_json rejects).
        with self.assertRaises(ValueError):
            parse_construct_json('{"name": "empty"}')

    def test_extraction_empty_templates(self):
        """Extraction fails gracefully when construct has no templates."""
        # Construct a TheatreConstructMeta with empty templates
        meta = TheatreConstructMeta(
            name="empty_construct",
            theatre_templates=[],
            osint_sources=[],
            verification_checks=[],
            settlement_tiers=[],
            has_brier_scoring=False,
            has_cross_validation=False,
            oracle_names=[],
        )
        extraction, fixture = extract_enriched_fixture("empty", "0.0.1", meta)

        self.assertFalse(extraction.success)
        self.assertIn("templates", extraction.error.lower())
        self.assertIsNone(fixture)

    def test_extraction_malformed_metadata(self):
        """Extraction succeeds with empty oracle fixtures when no sources declared."""
        # Valid meta with templates but no OSINT sources
        meta = TheatreConstructMeta(
            name="minimal_construct",
            theatre_templates=[
                TheatreTemplate(
                    id="only_template",
                    name="Only Template",
                    resolution="binary",
                    oracle="test_oracle",
                ),
            ],
            osint_sources=[],
            verification_checks=[],
            settlement_tiers=[],
            has_brier_scoring=False,
            has_cross_validation=False,
            oracle_names=["test_oracle"],
        )
        extraction, fixture = extract_enriched_fixture("minimal", "0.0.1", meta)

        # Should succeed with degraded output
        self.assertTrue(extraction.success)
        self.assertIsNotNone(fixture)
        self.assertEqual(extraction.settlement_fixture_count, 1)
        self.assertEqual(extraction.oracle_fixture_count, 0)
        self.assertFalse(extraction.has_calibration)
        self.assertEqual(extraction.functional_fixture_count, 1)
        # Single template: no failure scenarios
        self.assertFalse(extraction.has_failure_scenarios)
        # Single template: settlement fixture passes
        self.assertEqual(
            fixture.settlement_fixtures["only_template"]["predicted_outcome"],
            fixture.settlement_fixtures["only_template"]["actual_outcome"],
        )
        # Single template: functional fixture is valid
        self.assertTrue(fixture.functional_fixtures["only_template"]["transform_valid"])


if __name__ == "__main__":
    unittest.main()
