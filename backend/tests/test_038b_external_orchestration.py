"""Tests for Cycle 038b: External Theatre Orchestration.

Sprint 0: Schemas + extraction contracts (7 tests).
Sprint 1: Enriched fixture extraction (11 tests).
Sprint 2: Orchestrator composition (8 tests).
Sprint 3: 038 Scanner compatibility + builder feedback (8 tests).
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


# ═══════════════════════════════════════════════════════════════════
# Sprint 2 — Orchestrator Composition (8 tests)
# ═══════════════════════════════════════════════════════════════════

from backend.services.external_theatre_orchestrator import (
    prepare_external_theatres,
    _build_builder_feedback,
)


class TestOrchestratorComposition(unittest.TestCase):
    """Sprint 2: Orchestrator composition tests (8 tests)."""

    def test_orchestrator_single_theatre(self):
        """Single TREMOR input -> 1 bundle, 0 candidates (need 2+ for cross-comparison)."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_theatres, 1)
        self.assertEqual(result.total_successful, 1)
        self.assertEqual(result.total_failed, 0)
        self.assertIsNotNone(result.theatres[0].bundle)
        self.assertEqual(result.theatres[0].bundle.construct_slug, "tremor")
        # Need 2+ bundles for cross-comparison candidates
        self.assertEqual(result.candidates, [])

    def test_orchestrator_paired_theatres(self):
        """TREMOR + CORONA with shared event_keys and scope_keys -> 2 bundles, 1+ candidates."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["earthquake_2026_01"],
            scope_keys=[
                TheatreScopeKey(scope_type="region", scope_value="pacific_ring"),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_theatres, 2)
        self.assertEqual(result.total_successful, 2)
        self.assertEqual(result.total_failed, 0)
        self.assertGreaterEqual(len(result.candidates), 1)
        # Both bundles should be present
        slugs = [t.bundle.construct_slug for t in result.theatres if t.bundle]
        self.assertIn("tremor", slugs)
        self.assertIn("corona", slugs)

    def test_orchestrator_shared_identity_threading(self):
        """Shared event_keys flow through to bundles and result echo."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["eq_7.2"],
        )
        result = prepare_external_theatres(request)

        # Echo in result
        self.assertEqual(result.event_keys_used, ["eq_7.2"])

        # Verify bundles contain the shared event keys
        for entry in result.theatres:
            self.assertIsNotNone(entry.bundle)
            self.assertIn("eq_7.2", entry.bundle.event_keys)

    def test_orchestrator_no_keys_fallback(self):
        """Empty keys -> template-ID fallback in bundles (None passed to builder)."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=[],
            scope_keys=[],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_successful, 2)

        # With no shared keys, bundles get template-ID fallback keys
        tremor_bundle = result.theatres[0].bundle
        corona_bundle = result.theatres[1].bundle
        self.assertIsNotNone(tremor_bundle)
        self.assertIsNotNone(corona_bundle)

        # TREMOR template IDs should be in event_keys (fallback)
        for tid in ["aftershock_cascade", "depth_regime", "magnitude_gate",
                     "oracle_divergence", "swarm_watch"]:
            self.assertIn(tid, tremor_bundle.event_keys)

        # CORONA template IDs should be in event_keys (fallback)
        for tid in ["T1", "T2", "T3", "T4", "T5"]:
            self.assertIn(tid, corona_bundle.event_keys)

        # No shared event keys -> no same_event candidates
        # Scope keys also empty -> no overlap_scope candidates
        self.assertEqual(result.candidates, [])

    def test_orchestrator_error_propagation(self):
        """One invalid theatre + one valid -> 1 bundle, error on first."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="invalid",
                    construct_version="0.0.1",
                    construct_json="{bad",
                ),
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_theatres, 2)
        self.assertEqual(result.total_successful, 1)
        self.assertEqual(result.total_failed, 1)

        # First entry: error
        self.assertIsNotNone(result.theatres[0].error)
        self.assertIsNone(result.theatres[0].bundle)

        # Second entry: success
        self.assertIsNone(result.theatres[1].error)
        self.assertIsNotNone(result.theatres[1].bundle)
        self.assertEqual(result.theatres[1].bundle.construct_slug, "tremor")

    def test_orchestrator_all_failures(self):
        """Both theatres have invalid JSON -> total_failed=2, candidates=[], total_successful=0."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="bad1",
                    construct_version="0.0.1",
                    construct_json="{invalid json 1",
                ),
                ExternalTheatreInput(
                    construct_slug="bad2",
                    construct_version="0.0.1",
                    construct_json="{invalid json 2",
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_theatres, 2)
        self.assertEqual(result.total_successful, 0)
        self.assertEqual(result.total_failed, 2)
        self.assertEqual(result.candidates, [])

        # Both entries have errors
        self.assertIsNotNone(result.theatres[0].error)
        self.assertIsNotNone(result.theatres[1].error)

    def test_orchestrator_certificate_id_threading(self):
        """certificate_id flows to bundles."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
            certificate_id="cert-abc",
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_successful, 1)
        self.assertIsNotNone(result.theatres[0].bundle)
        self.assertEqual(result.theatres[0].bundle.certificate_id, "cert-abc")

    def test_orchestrator_empty_request(self):
        """Empty theatres list -> result with total_theatres=0, empty everything."""
        request = ExternalTheatrePreparationRequest(theatres=[])
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_theatres, 0)
        self.assertEqual(result.total_successful, 0)
        self.assertEqual(result.total_failed, 0)
        self.assertEqual(result.theatres, [])
        self.assertEqual(result.candidates, [])
        self.assertEqual(result.feedback, [])


# ═══════════════════════════════════════════════════════════════════
# Sprint 3 — 038 Scanner Compatibility + Builder Feedback (8 tests)
# ═══════════════════════════════════════════════════════════════════


class TestScannerCompatibility(unittest.TestCase):
    """Sprint 3: Prove orchestrated output is consumable by the 038 paradox scanner."""

    def test_candidates_consumable_by_scanner_input(self):
        """Candidate bundles have fields the 038 CrossTheatreParadoxScanner expects.

        The scanner reads: construct_slug, settlement_state, execution_summary
        (with checks), event_keys, scope_keys, settlement_outcomes, oracle_values.
        Each ComparisonCandidateSet must have bundle_a and bundle_b with these fields.
        """
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["geomagnetic_event_2026"],
            scope_keys=[
                TheatreScopeKey(scope_type="region", scope_value="global"),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertGreaterEqual(len(result.candidates), 1)

        for candidate in result.candidates:
            self.assertIsInstance(candidate, ComparisonCandidateSet)
            self.assertIn(candidate.candidate_type, ("same_event", "overlap_scope"))

            for bundle in (candidate.bundle_a, candidate.bundle_b):
                self.assertIsInstance(bundle, ExecutedTheatreComparisonBundle)

                # Fields the 038 scanner pathway consumes
                self.assertIsInstance(bundle.construct_slug, str)
                self.assertTrue(len(bundle.construct_slug) > 0)
                self.assertIsInstance(bundle.construct_version, str)

                # Settlement state — scanner uses this for divergence detection
                self.assertIn(bundle.settlement_state, ("SETTLED", "DISPUTED", "PENDING"))

                # Execution summary — scanner uses check_summary for paradox evidence
                self.assertIsNotNone(bundle.execution_summary)
                self.assertIsInstance(bundle.execution_summary.checks, list)
                self.assertGreater(bundle.execution_summary.executed_count, 0)

                # Event keys — scanner matches bundles on shared events
                self.assertIsInstance(bundle.event_keys, list)
                self.assertGreater(len(bundle.event_keys), 0)

                # Scope keys — scanner matches bundles on scope overlap
                self.assertIsInstance(bundle.scope_keys, list)

                # Settlement outcomes — scanner reads per-template outcomes
                self.assertIsInstance(bundle.settlement_outcomes, dict)

                # Oracle values — scanner reads per-source values
                self.assertIsInstance(bundle.oracle_values, dict)

                # Provenance refs — audit trail
                self.assertIsInstance(bundle.provenance_refs, list)
                self.assertGreater(len(bundle.provenance_refs), 0)

    def test_disputed_bundle_from_enriched_fixtures(self):
        """Enriched fixtures with failing templates -> DISPUTED settlement_state.

        Because enriched extraction includes odd-indexed failing templates
        (predicted != actual), the bundle's settlement_state must be DISPUTED
        rather than SETTLED. This proves enriched extraction enables non-trivial
        bundle states that the all-passing deterministic fixtures could never produce.
        """
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_successful, 1)
        bundle = result.theatres[0].bundle
        self.assertIsNotNone(bundle)

        # TREMOR has 5 templates: indices 1 (aftershock_cascade) and 3 (depth_regime) fail.
        # Any FAILED SETTLEMENT_ACCURACY check -> DISPUTED settlement_state.
        self.assertEqual(bundle.settlement_state, "DISPUTED")

        # Verify the settlement outcomes contain both matching and mismatched results
        self.assertIn("magnitude_gate", bundle.settlement_outcomes)
        self.assertIn("aftershock_cascade", bundle.settlement_outcomes)

        # magnitude_gate (pass): predicted == actual
        mg = bundle.settlement_outcomes["magnitude_gate"]
        self.assertEqual(mg["predicted_outcome"], mg["actual_outcome"])

        # aftershock_cascade (fail): predicted != actual
        ac = bundle.settlement_outcomes["aftershock_cascade"]
        self.assertNotEqual(ac["predicted_outcome"], ac["actual_outcome"])

    def test_settled_vs_disputed_cross_comparison(self):
        """TREMOR + CORONA cross-theatre with shared event_keys -> at least one candidate.

        Both TREMOR and CORONA produce DISPUTED bundles (both have 5 templates
        with odd-indexed failures). This exercises the cross-comparison path
        that all-passing fixtures could never meaningfully reach, since shared
        event_keys enable same_event matching.
        """
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["shared_geomagnetic_event"],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(result.total_successful, 2)

        # Both bundles should be DISPUTED (enriched fixtures have failing templates)
        tremor_bundle = result.theatres[0].bundle
        corona_bundle = result.theatres[1].bundle
        self.assertIsNotNone(tremor_bundle)
        self.assertIsNotNone(corona_bundle)
        self.assertEqual(tremor_bundle.settlement_state, "DISPUTED")
        self.assertEqual(corona_bundle.settlement_state, "DISPUTED")

        # Shared event_keys -> same_event candidate generated
        self.assertGreaterEqual(len(result.candidates), 1)
        candidate = result.candidates[0]
        self.assertEqual(candidate.candidate_type, "same_event")
        self.assertIn("shared_geomagnetic_event", candidate.matching_keys)

        # Both bundles in the candidate are different constructs
        self.assertNotEqual(
            candidate.bundle_a.construct_slug,
            candidate.bundle_b.construct_slug,
        )

    def test_disputed_bundle_odd_index_fail_scanner_compatible(self):
        """DISPUTED bundle path (odd-index fail fixtures) -> candidates still scanner-compatible.

        Verifies that even with DISPUTED settlement state from failing odd-indexed
        templates, the candidate shape remains fully consumable by the scanner:
        all check summaries present, all evidence dict fields populated.
        """
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["scanner_compat_event"],
        )
        result = prepare_external_theatres(request)

        self.assertGreaterEqual(len(result.candidates), 1)

        for candidate in result.candidates:
            for bundle in (candidate.bundle_a, candidate.bundle_b):
                # Execution summary checks are populated
                summary = bundle.execution_summary
                self.assertGreater(len(summary.checks), 0)

                # Each check has the fields the scanner uses
                for check in summary.checks:
                    self.assertIsInstance(check.check_type, str)
                    self.assertIn(check.status, ("PASSED", "FAILED", "SKIPPED"))
                    self.assertIsInstance(check.is_critical, bool)
                    self.assertIsInstance(check.evidence, dict)

                # Settlement outcomes populated for SETTLEMENT_ACCURACY checks
                settlement_checks = [
                    c for c in summary.checks if c.check_type == "SETTLEMENT_ACCURACY"
                ]
                self.assertGreater(len(settlement_checks), 0)

                # Has both PASSED and FAILED settlement checks (enriched extraction)
                statuses = {c.status for c in settlement_checks}
                self.assertIn("PASSED", statuses)
                self.assertIn("FAILED", statuses)


class TestBuilderFeedback(unittest.TestCase):
    """Sprint 3: Builder feedback correctly distinguishes TREMOR vs CORONA metadata quality."""

    def test_tremor_feedback_required_present(self):
        """TREMOR feedback: all required items present, overall_readiness=READY."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(len(result.feedback), 1)
        feedback = result.feedback[0]
        self.assertEqual(feedback.construct_slug, "tremor")
        self.assertEqual(feedback.overall_readiness, "READY")

        # All required items should have status="present"
        for item in feedback.required_items:
            self.assertEqual(item.category, "required")
            self.assertEqual(item.status, "present",
                             f"Required item '{item.field}' should be present, got '{item.status}'")

        # TREMOR has verification_checks, settlement_tiers, brier_type — all optional present
        optional_fields = {item.field: item.status for item in feedback.optional_items}
        self.assertEqual(optional_fields.get("verification_checks"), "present")
        self.assertEqual(optional_fields.get("settlement_tiers"), "present")
        self.assertEqual(optional_fields.get("brier_type"), "present")

    def test_corona_feedback_optional_missing(self):
        """CORONA feedback: verification_checks and settlement_tiers missing -> DEGRADED."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(len(result.feedback), 1)
        feedback = result.feedback[0]
        self.assertEqual(feedback.construct_slug, "corona")
        self.assertEqual(feedback.overall_readiness, "DEGRADED")

        # CORONA is missing verification_checks and settlement_tiers
        optional_fields = {item.field: item.status for item in feedback.optional_items}
        self.assertEqual(optional_fields.get("verification_checks"), "missing")
        self.assertEqual(optional_fields.get("settlement_tiers"), "missing")

        # CORONA templates don't declare brier_type
        self.assertEqual(optional_fields.get("brier_type"), "missing")

        # Required items still present (CORONA has templates and name)
        for item in feedback.required_items:
            self.assertEqual(item.status, "present",
                             f"Required item '{item.field}' should be present for CORONA")

    def test_tremor_feedback_extraction_summary(self):
        """TREMOR feedback: extraction items list all fixture categories."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
            ],
        )
        result = prepare_external_theatres(request)

        self.assertEqual(len(result.feedback), 1)
        feedback = result.feedback[0]

        # Extraction items should cover all fixture categories
        extraction_fields = {item.field for item in feedback.extraction_items}
        self.assertIn("settlement_fixtures", extraction_fields)
        self.assertIn("oracle_fixtures", extraction_fields)
        self.assertIn("calibration_fixture", extraction_fields)
        self.assertIn("functional_fixtures", extraction_fields)
        self.assertIn("failure_scenarios", extraction_fields)

        # All extraction items should have category="extraction"
        for item in feedback.extraction_items:
            self.assertEqual(item.category, "extraction")

        # Enriched items should have status="enriched"
        enriched_items = [item for item in feedback.extraction_items if item.status == "enriched"]
        self.assertGreater(len(enriched_items), 0)

    def test_feedback_blocked_on_missing_templates(self):
        """Construct with no templates -> BLOCKED readiness via _build_builder_feedback."""
        meta = TheatreConstructMeta(
            name="blocked_construct",
            theatre_templates=[],
            osint_sources=[],
            verification_checks=[],
            settlement_tiers=[],
            has_brier_scoring=False,
            has_cross_validation=False,
            oracle_names=[],
        )
        extraction = ExtractionResult(
            construct_slug="blocked",
            success=False,
            error="No theatre templates found",
        )
        report = _build_builder_feedback("blocked", meta, extraction)

        self.assertEqual(report.overall_readiness, "BLOCKED")
        self.assertEqual(report.construct_slug, "blocked")

        # Required items should include a missing templates item
        template_items = [i for i in report.required_items if i.field == "theatre_templates"]
        self.assertEqual(len(template_items), 1)
        self.assertEqual(template_items[0].status, "missing")

    def test_end_to_end_tremor_corona_preparation(self):
        """Full pipeline: TREMOR + CORONA with shared identity -> candidates + feedback + echo."""
        request = ExternalTheatrePreparationRequest(
            theatres=[
                ExternalTheatreInput(
                    construct_slug="tremor",
                    construct_version="0.1.0",
                    construct_json=TREMOR_CONSTRUCT_JSON,
                ),
                ExternalTheatreInput(
                    construct_slug="corona",
                    construct_version="0.1.0",
                    construct_json=CORONA_CONSTRUCT_JSON,
                ),
            ],
            event_keys=["geomagnetic_storm_2026"],
            scope_keys=[
                TheatreScopeKey(scope_type="region", scope_value="global"),
                TheatreScopeKey(scope_type="entity", scope_value="noaa"),
                TheatreScopeKey(scope_type="time_window", scope_value="2026-03"),
            ],
        )
        result = prepare_external_theatres(request)

        # Aggregate counts
        self.assertEqual(result.total_theatres, 2)
        self.assertEqual(result.total_successful, 2)
        self.assertEqual(result.total_failed, 0)

        # Candidates: at least 1 (same_event from shared event_keys)
        self.assertGreaterEqual(len(result.candidates), 1)

        # Feedback: one per theatre
        self.assertEqual(len(result.feedback), 2)
        feedback_slugs = {f.construct_slug for f in result.feedback}
        self.assertIn("tremor", feedback_slugs)
        self.assertIn("corona", feedback_slugs)

        # TREMOR = READY, CORONA = DEGRADED
        tremor_fb = [f for f in result.feedback if f.construct_slug == "tremor"][0]
        corona_fb = [f for f in result.feedback if f.construct_slug == "corona"][0]
        self.assertEqual(tremor_fb.overall_readiness, "READY")
        self.assertEqual(corona_fb.overall_readiness, "DEGRADED")

        # Event keys echo
        self.assertEqual(result.event_keys_used, ["geomagnetic_storm_2026"])

        # Scope keys echo
        self.assertEqual(len(result.scope_keys_used), 3)
        scope_types = {sk.scope_type for sk in result.scope_keys_used}
        self.assertIn("region", scope_types)
        self.assertIn("entity", scope_types)
        self.assertIn("time_window", scope_types)

        # Both bundles have shared event keys and scope keys threaded
        for entry in result.theatres:
            self.assertIsNotNone(entry.bundle)
            self.assertIn("geomagnetic_storm_2026", entry.bundle.event_keys)
            self.assertEqual(len(entry.bundle.scope_keys), 3)

        # Both bundles are DISPUTED (enriched extraction includes failures)
        for entry in result.theatres:
            self.assertEqual(entry.bundle.settlement_state, "DISPUTED")

        # Candidate has the shared event key
        candidate = result.candidates[0]
        self.assertIn("geomagnetic_storm_2026", candidate.matching_keys)


if __name__ == "__main__":
    unittest.main()
