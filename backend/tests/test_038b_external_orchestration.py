"""Tests for Cycle 038b: External Theatre Orchestration.

Sprint 0: Schemas + extraction contracts (7 tests).
"""

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


if __name__ == "__main__":
    unittest.main()
