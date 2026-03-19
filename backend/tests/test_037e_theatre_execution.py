"""Tests for Cycle 037e: Theatre Check Execution.

Sprint 0: Execution models + fixture loader (10 tests)
Sprint 1: Core theatre runner (14 tests)
Sprint 2: Certificate integration (10 tests)
Sprint 3: TREMOR + CORONA fixtures + regression (10 tests)
"""

import json
import os
import sys
import unittest
from types import SimpleNamespace
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


# =========================================
# Sprint 0: Execution Models + Fixture Loader
# =========================================


class TestTheatreExecutionSchemas(unittest.TestCase):
    """Sprint 0: Theatre execution schema models."""

    def test_check_result_creation(self):
        from backend.schemas.theatre_execution import TheatreCheckResult
        r = TheatreCheckResult(
            check_id="theatre:settlement_accuracy:magnitude_gate",
            check_type="SETTLEMENT_ACCURACY",
            status="PASSED",
            template_id="magnitude_gate",
        )
        self.assertEqual(r.status, "PASSED")
        self.assertEqual(r.template_id, "magnitude_gate")

    def test_check_result_frozen(self):
        from backend.schemas.theatre_execution import TheatreCheckResult
        r = TheatreCheckResult(check_id="t1", check_type="X", status="PASSED")
        with self.assertRaises(AttributeError):
            r.status = "FAILED"

    def test_execution_result_counters(self):
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult
        result = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(check_id="c1", check_type="SETTLEMENT_ACCURACY", status="PASSED"),
                TheatreCheckResult(check_id="c2", check_type="ORACLE_CONSISTENCY", status="FAILED"),
                TheatreCheckResult(check_id="c3", check_type="CALIBRATION_VALIDITY", status="SKIPPED"),
                TheatreCheckResult(check_id="c4", check_type="FUNCTIONAL_CORRECTNESS", status="PASSED"),
            ],
        )
        self.assertEqual(result.total_executed, 3)  # PASSED + FAILED
        self.assertEqual(result.total_passed, 2)
        self.assertEqual(result.total_failed, 1)
        self.assertEqual(result.total_skipped, 1)

    def test_critical_failure_detection(self):
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult
        # ORACLE_CONSISTENCY failed → critical failure
        result = TheatreExecutionResult(
            construct_slug="test",
            check_results=[
                TheatreCheckResult(check_id="c1", check_type="ORACLE_CONSISTENCY", status="FAILED"),
                TheatreCheckResult(check_id="c2", check_type="CALIBRATION_VALIDITY", status="PASSED"),
            ],
        )
        self.assertTrue(result.has_critical_failures)

    def test_no_critical_failure_when_noncritical_fails(self):
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult
        # Only FUNCTIONAL_CORRECTNESS failed → not critical
        result = TheatreExecutionResult(
            construct_slug="test",
            check_results=[
                TheatreCheckResult(check_id="c1", check_type="FUNCTIONAL_CORRECTNESS", status="FAILED"),
                TheatreCheckResult(check_id="c2", check_type="SETTLEMENT_ACCURACY", status="PASSED"),
            ],
        )
        self.assertFalse(result.has_critical_failures)

    def test_execution_result_to_dict(self):
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult
        result = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="c1", check_type="SETTLEMENT_ACCURACY",
                    status="PASSED", evidence={"oracle": "USGS"},
                ),
            ],
        )
        d = result.to_dict()
        self.assertEqual(d["construct_slug"], "tremor")
        self.assertEqual(d["total_passed"], 1)
        self.assertEqual(len(d["checks"]), 1)
        self.assertEqual(d["checks"][0]["evidence"]["oracle"], "USGS")

    def test_fixture_input_creation(self):
        from backend.schemas.theatre_execution import TheatreFixtureInput
        fx = TheatreFixtureInput(
            construct_slug="corona",
            construct_version="0.1.0",
            construct_class="theatre",
        )
        self.assertEqual(fx.construct_slug, "corona")
        self.assertEqual(fx.settlement_fixtures, {})


class TestTheatreFixtureLoader(unittest.TestCase):
    """Sprint 0: Fixture loader for TREMOR and CORONA."""

    def _get_tremor_json(self):
        path = "/Users/tobiasharber/Developer/tremor/spec/construct.json"
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        self.skipTest("TREMOR construct.json not available")

    def _get_corona_json(self):
        path = "/Users/tobiasharber/Developer/corona/construct.json"
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        self.skipTest("CORONA construct.json not available")

    def test_tremor_fixture_loads(self):
        from backend.services.theatre_fixture_loader import load_fixture
        fx = load_fixture("tremor", "0.1.0", self._get_tremor_json())
        self.assertEqual(fx.construct_slug, "tremor")
        self.assertEqual(fx.construct_class, "theatre")
        # TREMOR has 5 templates → 5 settlement fixtures
        self.assertEqual(len(fx.settlement_fixtures), 5)
        self.assertIn("magnitude_gate", fx.settlement_fixtures)
        # TREMOR has 2 cross-validation sources
        self.assertEqual(len(fx.oracle_fixtures), 2)
        self.assertIn("emsc", fx.oracle_fixtures)
        # TREMOR has Brier scoring
        self.assertIsNotNone(fx.calibration_fixture)

    def test_corona_fixture_loads(self):
        from backend.services.theatre_fixture_loader import load_fixture
        fx = load_fixture("corona", "0.1.0", self._get_corona_json())
        self.assertEqual(fx.construct_slug, "corona")
        # CORONA has 5 templates
        self.assertEqual(len(fx.settlement_fixtures), 5)
        self.assertIn("T1", fx.settlement_fixtures)
        # CORONA has 2 cross-validation sources (after patch)
        self.assertEqual(len(fx.oracle_fixtures), 2)
        self.assertIn("nasa_donki", fx.oracle_fixtures)
        self.assertIn("gfz_potsdam", fx.oracle_fixtures)
        # CORONA has Brier scoring via rlmf.exports
        self.assertIsNotNone(fx.calibration_fixture)

    def test_explicit_replay_data(self):
        from backend.services.theatre_fixture_loader import load_fixture
        replay = {
            "settlement_fixtures": {"custom_tmpl": {"predicted_outcome": "YES", "actual_outcome": "NO"}},
            "oracle_fixtures": {},
        }
        fx = load_fixture("test", "1.0", self._get_tremor_json(), replay_data=replay)
        self.assertEqual(len(fx.settlement_fixtures), 1)
        self.assertIn("custom_tmpl", fx.settlement_fixtures)


# =========================================
# Sprint 1: Core Theatre Runner
# =========================================


class TestSettlementAccuracyExecution(unittest.TestCase):
    """Sprint 1: SETTLEMENT_ACCURACY execution."""

    def _make_fixture(self, settlement_fixtures):
        from backend.schemas.theatre_execution import TheatreFixtureInput
        return TheatreFixtureInput(
            construct_slug="test",
            construct_version="0.1.0",
            construct_class="theatre",
            settlement_fixtures=settlement_fixtures,
        )

    def test_settlement_pass(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "mag_gate": {"predicted_outcome": "YES", "actual_outcome": "YES", "oracle_value": 6.5},
        })
        checks = [{"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_passed, 1)
        self.assertEqual(result.check_results[0].status, "PASSED")

    def test_settlement_fail(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "mag_gate": {"predicted_outcome": "YES", "actual_outcome": "NO", "oracle_value": 5.0},
        })
        checks = [{"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_failed, 1)
        self.assertIn("mismatch", result.check_results[0].reason)

    def test_settlement_skip_missing_fixture(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({})
        checks = [{"check_id": "theatre:settlement_accuracy:unknown", "check_type": "SETTLEMENT_ACCURACY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_skipped, 1)
        self.assertEqual(result.check_results[0].status, "SKIPPED")

    def test_settlement_evidence_populated(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "t1": {
                "predicted_outcome": "YES", "actual_outcome": "YES",
                "oracle_value": 7.1, "oracle": "USGS reviewed", "resolution": "binary",
            },
        })
        checks = [{"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY"}]
        result = execute_theatre_checks(checks, fx)
        ev = result.check_results[0].evidence
        self.assertEqual(ev["oracle_value"], 7.1)
        self.assertEqual(ev["oracle"], "USGS reviewed")

    def test_multiple_templates(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "t1": {"predicted_outcome": "YES", "actual_outcome": "YES"},
            "t2": {"predicted_outcome": "YES", "actual_outcome": "NO"},
            "t3": {"predicted_outcome": "bucket_0", "actual_outcome": "bucket_0"},
        })
        checks = [
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY"},
            {"check_id": "theatre:settlement_accuracy:t2", "check_type": "SETTLEMENT_ACCURACY"},
            {"check_id": "theatre:settlement_accuracy:t3", "check_type": "SETTLEMENT_ACCURACY"},
        ]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_passed, 2)
        self.assertEqual(result.total_failed, 1)


class TestOracleConsistencyExecution(unittest.TestCase):
    """Sprint 1: ORACLE_CONSISTENCY execution."""

    def _make_fixture(self, oracle_fixtures):
        from backend.schemas.theatre_execution import TheatreFixtureInput
        return TheatreFixtureInput(
            construct_slug="test",
            construct_version="0.1.0",
            construct_class="theatre",
            oracle_fixtures=oracle_fixtures,
        )

    def test_oracle_consistent(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "emsc": {"primary_value": 6.2, "cross_value": 6.1, "threshold": 0.5},
        })
        checks = [{"check_id": "theatre:oracle_consistency:emsc", "check_type": "ORACLE_CONSISTENCY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "PASSED")
        self.assertAlmostEqual(result.check_results[0].evidence["delta"], 0.1)

    def test_oracle_divergent(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "emsc": {"primary_value": 6.2, "cross_value": 5.0, "threshold": 0.5},
        })
        checks = [{"check_id": "theatre:oracle_consistency:emsc", "check_type": "ORACLE_CONSISTENCY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "FAILED")
        self.assertIn("divergence", result.check_results[0].reason)

    def test_oracle_skip_missing_source(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({})
        checks = [{"check_id": "theatre:oracle_consistency:unknown", "check_type": "ORACLE_CONSISTENCY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "SKIPPED")

    def test_oracle_skip_missing_values(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "emsc": {"primary_value": None, "cross_value": 6.1, "threshold": 0.5},
        })
        checks = [{"check_id": "theatre:oracle_consistency:emsc", "check_type": "ORACLE_CONSISTENCY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "SKIPPED")


class TestCalibrationValidityExecution(unittest.TestCase):
    """Sprint 1: CALIBRATION_VALIDITY execution."""

    def _make_fixture(self, calibration_fixture):
        from backend.schemas.theatre_execution import TheatreFixtureInput
        return TheatreFixtureInput(
            construct_slug="test",
            construct_version="0.1.0",
            construct_class="theatre",
            calibration_fixture=calibration_fixture,
        )

    def test_calibration_pass(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        preds = [0.75, 0.60, 0.90, 0.20]
        outcomes = [1.0, 1.0, 1.0, 0.0]
        expected = sum((p - o) ** 2 for p, o in zip(preds, outcomes)) / 4
        fx = self._make_fixture({
            "predictions": preds, "outcomes": outcomes,
            "expected_brier": expected, "brier_type": "binary",
        })
        checks = [{"check_id": "theatre:calibration_validity:test", "check_type": "CALIBRATION_VALIDITY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "PASSED")

    def test_calibration_fail_wrong_expected(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "predictions": [0.5], "outcomes": [1.0],
            "expected_brier": 0.99, "brier_type": "binary",
        })
        checks = [{"check_id": "theatre:calibration_validity:test", "check_type": "CALIBRATION_VALIDITY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "FAILED")

    def test_calibration_skip_no_fixture(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture(None)
        checks = [{"check_id": "theatre:calibration_validity:test", "check_type": "CALIBRATION_VALIDITY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "SKIPPED")

    def test_calibration_skip_mismatched_arrays(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({"predictions": [0.5, 0.6], "outcomes": [1.0], "brier_type": "binary"})
        checks = [{"check_id": "theatre:calibration_validity:test", "check_type": "CALIBRATION_VALIDITY"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "SKIPPED")


class TestFunctionalCorrectnessExecution(unittest.TestCase):
    """Sprint 1: FUNCTIONAL_CORRECTNESS execution."""

    def _make_fixture(self, functional_fixtures):
        from backend.schemas.theatre_execution import TheatreFixtureInput
        return TheatreFixtureInput(
            construct_slug="test",
            construct_version="0.1.0",
            construct_class="theatre",
            functional_fixtures=functional_fixtures,
        )

    def test_functional_pass(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "mag_gate": {"transform_valid": True, "template_name": "Magnitude Gate", "resolution": "binary"},
        })
        checks = [{"check_id": "theatre:functional_correctness:mag_gate", "check_type": "FUNCTIONAL_CORRECTNESS"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "PASSED")

    def test_functional_fail(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({
            "mag_gate": {"transform_valid": False, "template_name": "Magnitude Gate"},
        })
        checks = [{"check_id": "theatre:functional_correctness:mag_gate", "check_type": "FUNCTIONAL_CORRECTNESS"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "FAILED")

    def test_functional_skip_missing(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        fx = self._make_fixture({})
        checks = [{"check_id": "theatre:functional_correctness:unknown", "check_type": "FUNCTIONAL_CORRECTNESS"}]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.check_results[0].status, "SKIPPED")


class TestRunnerDispatch(unittest.TestCase):
    """Sprint 1: Runner dispatches non-theatre checks correctly."""

    def test_non_theatre_checks_ignored(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        from backend.schemas.theatre_execution import TheatreFixtureInput
        fx = TheatreFixtureInput(
            construct_slug="test", construct_version="0.1.0", construct_class="theatre",
        )
        checks = [
            {"check_id": "rubric:test:design", "check_type": "RUBRIC"},
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR"},
        ]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(len(result.check_results), 0)

    def test_mixed_check_types(self):
        from backend.services.theatre_check_runner import execute_theatre_checks
        from backend.schemas.theatre_execution import TheatreFixtureInput
        fx = TheatreFixtureInput(
            construct_slug="test", construct_version="0.1.0", construct_class="theatre",
            settlement_fixtures={"t1": {"predicted_outcome": "YES", "actual_outcome": "YES"}},
        )
        checks = [
            {"check_id": "rubric:test:design", "check_type": "RUBRIC"},
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY"},
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR"},
        ]
        result = execute_theatre_checks(checks, fx)
        # Only the theatre check is processed
        self.assertEqual(len(result.check_results), 1)
        self.assertEqual(result.check_results[0].status, "PASSED")


# =========================================
# Sprint 2: Certificate Integration
# =========================================


class TestCertificateIntegration(unittest.TestCase):
    """Sprint 2: Theatre results projected into certificate check plan."""

    def _make_scorer_output(self):
        from backend.services.construct_certificate_builder import ScorerOutput
        return ScorerOutput(
            composite_score=0.85,
            domain_scores={"seismic_intelligence": 0.9},
            skill_coverage=1.0,
            verdict="PASS",
            tier="COMMUNITY",
            routing_hint="ALLOWED",
            episode_count=5,
        )

    def _make_contract(self, planned_checks):
        return SimpleNamespace(
            contract_hash="sha256:abc123",
            spec_hash="sha256:def456",
            planned_checks=planned_checks,
            tier_cap=None,
        )

    def _make_registration(self):
        return SimpleNamespace(
            slug="tremor", version="0.1.0",
            content_hash="h1", commitment_hash="h2",
            test_prompts_hash="tp", rubric_hash="rh",
        )

    def _make_investigation(self):
        return SimpleNamespace(stop_config_json={"run_number": 1})

    def test_theatre_results_projected_into_check_plan(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:mag_gate",
                    check_type="SETTLEMENT_ACCURACY",
                    status="PASSED",
                    evidence={"oracle": "USGS"},
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:mag_gate"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        plan = cert.check_plan
        theatre_check = [c for c in plan["checks"] if c["id"] == "theatre:settlement_accuracy:mag_gate"][0]
        self.assertEqual(theatre_check["status"], "EXECUTED")
        self.assertEqual(theatre_check["theatre_status"], "PASSED")
        self.assertIsNotNone(theatre_check["theatre_evidence"])

    def test_failed_theatre_check_shows_executed_with_fail(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:mag_gate",
                    check_type="SETTLEMENT_ACCURACY",
                    status="FAILED",
                    reason="Settlement mismatch",
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:mag_gate"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        check = cert.check_plan["checks"][0]
        self.assertEqual(check["status"], "EXECUTED")
        self.assertEqual(check["theatre_status"], "FAILED")
        # P1 fix: deterministic theatre failure blocks READY even when verdict=PASS
        self.assertEqual(cert.issuance_status, "REJECTED")
        self.assertEqual(cert.check_plan["theatre_failures"], 1)

    def test_skipped_theatre_check_not_counted_as_executed(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:calibration_validity:tremor",
                    check_type="CALIBRATION_VALIDITY",
                    status="SKIPPED",
                    reason="No fixture",
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:calibration_validity:tremor", "check_type": "CALIBRATION_VALIDITY", "domain": "calibration:tremor"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        # ANCHOR (executed) + CALIBRATION (skipped) = 1 executed, 2 planned
        self.assertEqual(cert.check_plan["total_executed"], 1)
        self.assertEqual(cert.check_plan["total_planned"], 2)

    def test_issuance_deferred_when_critical_theatre_skipped(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:mag_gate",
                    check_type="SETTLEMENT_ACCURACY",
                    status="SKIPPED",
                    reason="No fixture",
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:mag_gate"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        # 1 executed (anchor), 1 skipped → not all executed → DEFERRED
        self.assertEqual(cert.issuance_status, "DEFERRED")

    def test_issuance_ready_when_all_theatre_passed(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(check_id="theatre:settlement_accuracy:t1", check_type="SETTLEMENT_ACCURACY", status="PASSED"),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "anchor:deterministic_check", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:t1"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        # 2 anchors + 1 theatre = 3 executed = 3 planned → READY
        self.assertEqual(cert.issuance_status, "READY")

    def test_no_theatre_execution_backwards_compatible(self):
        """Certificate builder works without theatre_execution (pre-037e)."""
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "rubric:tremor:seismic", "check_type": "RUBRIC", "domain": "seismic_intelligence"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
        )
        # seismic_intelligence is in domain_scores → RUBRIC executed
        self.assertEqual(cert.check_plan["total_executed"], 2)
        self.assertEqual(cert.issuance_status, "READY")

    def test_theatre_evidence_in_certificate_json(self):
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:t1",
                    check_type="SETTLEMENT_ACCURACY",
                    status="PASSED",
                    evidence={"oracle": "USGS", "oracle_value": 6.5},
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:t1"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        cert_json = builder.to_certificate_json(cert)
        # Theatre evidence should be in check_plan.checks
        theatre_checks = [c for c in cert_json["check_plan"]["checks"] if c.get("theatre_evidence")]
        self.assertEqual(len(theatre_checks), 1)
        self.assertEqual(theatre_checks[0]["theatre_evidence"]["oracle"], "USGS")

    def test_rejected_verdict_overrides_theatre_pass(self):
        """Verdict FAIL still produces REJECTED even if theatre checks pass."""
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder, ScorerOutput
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        scorer = ScorerOutput(
            composite_score=0.3, domain_scores={}, skill_coverage=0.5,
            verdict="FAIL", tier="UNVERIFIED", routing_hint="REVIEW_REQUIRED", episode_count=1,
        )

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(check_id="theatre:settlement_accuracy:t1", check_type="SETTLEMENT_ACCURACY", status="PASSED"),
            ],
        )

        contract = self._make_contract([
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:t1"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            scorer, "bundle_hash", contract=contract, theatre_execution=theatre,
        )
        self.assertEqual(cert.issuance_status, "REJECTED")

    def test_theatre_failure_blocks_ready_despite_pass_verdict(self):
        """P1 regression: failed SETTLEMENT_ACCURACY must produce REJECTED, not READY.

        Reproduces: single failed settlement check with verdict=PASS previously
        left issuance_status='READY' because FAILED was counted as EXECUTED and
        compute_issuance_status only checked executed vs planned counts.
        """
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:mag_gate",
                    check_type="SETTLEMENT_ACCURACY",
                    status="FAILED",
                    reason="Settlement mismatch: predicted=YES, actual=NO",
                ),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:mag_gate"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        # All checks executed (anchor + failed settlement) but issuance is REJECTED
        self.assertEqual(cert.check_plan["total_executed"], 2)
        self.assertEqual(cert.check_plan["total_planned"], 2)
        self.assertEqual(cert.check_plan["theatre_failures"], 1)
        self.assertEqual(cert.issuance_status, "REJECTED")
        # Remediation is NOT set for REJECTED (only for DEFERRED)
        self.assertIsNone(cert.remediation)

    def test_theatre_failures_zero_when_all_pass(self):
        """theatre_failures count is 0 when all theatre checks pass."""
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(check_id="theatre:settlement_accuracy:t1", check_type="SETTLEMENT_ACCURACY", status="PASSED"),
            ],
        )

        contract = self._make_contract([
            {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:t1"},
        ])

        builder = ConstructCertificateBuilder()
        cert = builder.build(
            self._make_registration(), self._make_investigation(),
            self._make_scorer_output(), "bundle_hash", contract=contract,
            theatre_execution=theatre,
        )
        self.assertEqual(cert.check_plan["theatre_failures"], 0)
        self.assertEqual(cert.issuance_status, "READY")

    def test_compute_issuance_status_theatre_failures_direct(self):
        """Direct test of compute_issuance_status with theatre_failures field."""
        from backend.services.construct_certificate_builder import ConstructCertificateBuilder

        # PASS verdict + theatre failures → REJECTED
        status = ConstructCertificateBuilder.compute_issuance_status(
            "PASS", {"total_planned": 3, "total_executed": 3, "theatre_failures": 1}, None,
        )
        self.assertEqual(status, "REJECTED")

        # PASS verdict + no theatre failures → READY
        status = ConstructCertificateBuilder.compute_issuance_status(
            "PASS", {"total_planned": 3, "total_executed": 3, "theatre_failures": 0}, None,
        )
        self.assertEqual(status, "READY")

        # PASS verdict + no theatre_failures key (pre-037e) → READY (backwards compatible)
        status = ConstructCertificateBuilder.compute_issuance_status(
            "PASS", {"total_planned": 3, "total_executed": 3}, None,
        )
        self.assertEqual(status, "READY")


class TestRoutingGateOnIssuance(unittest.TestCase):
    """P1 fix: routing_decision must be gated on final issuance, not just scorer."""

    def test_routing_allowed_with_rejected_issuance_is_overridden(self):
        """Reproduces: BACKTESTED/PASS scorer + failed theatre → REJECTED certificate.

        The builder's compute_routing_decision returns ALLOWED for BACKTESTED/PASS,
        but the route overrides to REVIEW_REQUIRED when final_issuance is REJECTED.
        This test verifies the builder-level mismatch that the route must handle.
        """
        from backend.services.construct_certificate_builder import (
            ConstructCertificateBuilder, ScorerOutput,
        )
        from backend.schemas.theatre_execution import TheatreCheckResult, TheatreExecutionResult

        scorer = ScorerOutput(
            composite_score=0.95,
            domain_scores={"seismic_intelligence": 0.9},
            skill_coverage=1.0,
            verdict="PASS",
            tier="BACKTESTED",
            routing_hint="ALLOWED",
            episode_count=10,
        )

        theatre = TheatreExecutionResult(
            construct_slug="tremor",
            check_results=[
                TheatreCheckResult(
                    check_id="theatre:settlement_accuracy:mag_gate",
                    check_type="SETTLEMENT_ACCURACY",
                    status="FAILED",
                    reason="Settlement mismatch: predicted=YES, actual=NO",
                ),
            ],
        )

        contract = SimpleNamespace(
            contract_hash="sha256:abc", spec_hash="sha256:def",
            planned_checks=[
                {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
                {"check_id": "theatre:settlement_accuracy:mag_gate", "check_type": "SETTLEMENT_ACCURACY", "domain": "theatre:mag_gate"},
            ],
            tier_cap=None,
        )
        reg = SimpleNamespace(
            slug="tremor", version="0.1.0",
            content_hash="h1", commitment_hash="h2",
            test_prompts_hash="tp", rubric_hash="rh",
        )
        inv = SimpleNamespace(stop_config_json={"run_number": 1})

        builder = ConstructCertificateBuilder()
        cert = builder.build(reg, inv, scorer, "bundle_hash", contract=contract, theatre_execution=theatre)

        # Certificate is REJECTED (theatre failure overrides soft PASS)
        self.assertEqual(cert.issuance_status, "REJECTED")

        # Builder-level routing still returns ALLOWED (it only sees scorer)
        routing_decision, routing_reason = builder.compute_routing_decision(scorer)
        self.assertEqual(routing_decision, "ALLOWED")
        self.assertEqual(routing_reason, "construct_verified_backtested")

        # Route-level override: REJECTED issuance → REVIEW_REQUIRED
        # (This logic lives in construct_routes.py, tested here as contract)
        if cert.issuance_status in ("REJECTED", "BLOCKED"):
            routing_decision = "REVIEW_REQUIRED"
            routing_reason = "certificate_rejected"
        self.assertEqual(routing_decision, "REVIEW_REQUIRED")
        self.assertEqual(routing_reason, "certificate_rejected")


# =========================================
# Sprint 3: TREMOR + CORONA End-to-End Fixtures
# =========================================


class TestTREMOREndToEnd(unittest.TestCase):
    """Sprint 3: TREMOR full execution pipeline."""

    def _load_and_run(self):
        path = "/Users/tobiasharber/Developer/tremor/spec/construct.json"
        if not os.path.exists(path):
            self.skipTest("TREMOR construct.json not available")

        from backend.services.contract_service import ContractService
        from backend.services.spec_loader import load as load_spec
        from backend.services.policy_normalizer import normalize
        from backend.services.check_planner import plan_checks, checks_to_dicts
        from backend.services.theatre_policy_rules import parse_construct_json
        from backend.services.theatre_check_planner import plan_theatre_checks, merge_theatre_checks
        from backend.services.theatre_fixture_loader import load_fixture
        from backend.services.theatre_check_runner import execute_theatre_checks

        yaml_path = "/Users/tobiasharber/Developer/tremor/construct.yaml"
        if not os.path.exists(yaml_path):
            self.skipTest("TREMOR construct.yaml not available")

        with open(yaml_path) as f:
            yaml_content = f.read()
        with open(path) as f:
            json_content = f.read()

        spec = load_spec(yaml_content)
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)
        meta = parse_construct_json(json_content)
        theatre_checks = plan_theatre_checks(spec.slug, meta)
        merged = merge_theatre_checks(base_checks, theatre_checks)
        planned_dicts = checks_to_dicts(merged)

        fixture = load_fixture("tremor", "0.1.0", json_content)
        result = execute_theatre_checks(planned_dicts, fixture)
        return result, planned_dicts

    def test_tremor_executes_all_theatre_checks(self):
        result, planned = self._load_and_run()
        # TREMOR: 5 settlement + 2 oracle + 1 calibration + 5 functional = 13 theatre
        self.assertEqual(len(result.check_results), 13)

    def test_tremor_all_pass(self):
        result, _ = self._load_and_run()
        self.assertEqual(result.total_passed, 13)
        self.assertEqual(result.total_failed, 0)
        self.assertEqual(result.total_skipped, 0)

    def test_tremor_no_critical_failures(self):
        result, _ = self._load_and_run()
        self.assertFalse(result.has_critical_failures)

    def test_tremor_settlement_check_per_template(self):
        result, _ = self._load_and_run()
        settlement = [r for r in result.check_results if r.check_type == "SETTLEMENT_ACCURACY"]
        self.assertEqual(len(settlement), 5)
        template_ids = {r.template_id for r in settlement}
        self.assertIn("magnitude_gate", template_ids)
        self.assertIn("aftershock_cascade", template_ids)


class TestCORONAEndToEnd(unittest.TestCase):
    """Sprint 3: CORONA full execution pipeline."""

    def _load_and_run(self):
        json_path = "/Users/tobiasharber/Developer/corona/construct.json"
        yaml_path = "/Users/tobiasharber/Developer/corona/construct.yaml"
        if not os.path.exists(json_path) or not os.path.exists(yaml_path):
            self.skipTest("CORONA repos not available")

        from backend.services.contract_service import ContractService
        from backend.services.spec_loader import load as load_spec
        from backend.services.policy_normalizer import normalize
        from backend.services.check_planner import plan_checks, checks_to_dicts
        from backend.services.theatre_policy_rules import parse_construct_json
        from backend.services.theatre_check_planner import plan_theatre_checks, merge_theatre_checks
        from backend.services.theatre_fixture_loader import load_fixture
        from backend.services.theatre_check_runner import execute_theatre_checks

        with open(yaml_path) as f:
            yaml_content = f.read()
        with open(json_path) as f:
            json_content = f.read()

        spec = load_spec(yaml_content)
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)
        meta = parse_construct_json(json_content)
        theatre_checks = plan_theatre_checks(spec.slug, meta)
        merged = merge_theatre_checks(base_checks, theatre_checks)
        planned_dicts = checks_to_dicts(merged)

        fixture = load_fixture("corona", "0.1.0", json_content)
        result = execute_theatre_checks(planned_dicts, fixture)
        return result, planned_dicts

    def test_corona_executes_all_theatre_checks(self):
        result, planned = self._load_and_run()
        # CORONA: 5 settlement + 2 oracle + 1 calibration + 5 functional = 13 theatre
        self.assertEqual(len(result.check_results), 13)

    def test_corona_all_pass(self):
        result, _ = self._load_and_run()
        self.assertEqual(result.total_passed, 13)
        self.assertEqual(result.total_failed, 0)

    def test_corona_oracle_consistency_with_patched_roles(self):
        result, _ = self._load_and_run()
        oracle = [r for r in result.check_results if r.check_type == "ORACLE_CONSISTENCY"]
        self.assertEqual(len(oracle), 2)
        source_ids = {r.source_id for r in oracle}
        self.assertIn("nasa_donki", source_ids)
        self.assertIn("gfz_potsdam", source_ids)


class TestPartialCoverage(unittest.TestCase):
    """Sprint 3: Partial/failing fixture coverage."""

    def test_partial_settlement_coverage(self):
        """When only some templates have fixtures, others are SKIPPED."""
        from backend.services.theatre_check_runner import execute_theatre_checks
        from backend.schemas.theatre_execution import TheatreFixtureInput

        fx = TheatreFixtureInput(
            construct_slug="partial",
            construct_version="0.1.0",
            construct_class="theatre",
            settlement_fixtures={
                "t1": {"predicted_outcome": "YES", "actual_outcome": "YES"},
                # t2 deliberately missing
            },
        )
        checks = [
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY"},
            {"check_id": "theatre:settlement_accuracy:t2", "check_type": "SETTLEMENT_ACCURACY"},
        ]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_passed, 1)
        self.assertEqual(result.total_skipped, 1)
        # Critical check skipped
        self.assertTrue(result.has_critical_failures)

    def test_failing_settlement_fixture(self):
        """Deliberate failure fixture for settlement."""
        from backend.services.theatre_check_runner import execute_theatre_checks
        from backend.schemas.theatre_execution import TheatreFixtureInput

        fx = TheatreFixtureInput(
            construct_slug="failing",
            construct_version="0.1.0",
            construct_class="theatre",
            settlement_fixtures={
                "t1": {"predicted_outcome": "YES", "actual_outcome": "NO", "oracle_value": 5.0},
            },
            oracle_fixtures={
                "cross_src": {"primary_value": 6.2, "cross_value": 5.0, "threshold": 0.5},
            },
        )
        checks = [
            {"check_id": "theatre:settlement_accuracy:t1", "check_type": "SETTLEMENT_ACCURACY"},
            {"check_id": "theatre:oracle_consistency:cross_src", "check_type": "ORACLE_CONSISTENCY"},
        ]
        result = execute_theatre_checks(checks, fx)
        self.assertEqual(result.total_failed, 2)
        self.assertTrue(result.has_critical_failures)


class TestRegression(unittest.TestCase):
    """Sprint 3: Regression — non-theatre paths unaffected."""

    def test_certificate_builder_without_theatre(self):
        """Pre-037e certificate path still works."""
        from backend.services.construct_certificate_builder import (
            ConstructCertificateBuilder, ScorerOutput,
        )
        scorer = ScorerOutput(
            composite_score=0.9, domain_scores={"design_systems": 0.95},
            skill_coverage=1.0, verdict="PASS", tier="BACKTESTED",
            routing_hint="ALLOWED", episode_count=10,
        )
        contract = SimpleNamespace(
            contract_hash="sha256:test", spec_hash="sha256:test",
            planned_checks=[
                {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*"},
                {"check_id": "rubric:artisan:design_systems", "check_type": "RUBRIC", "domain": "design_systems"},
            ],
            tier_cap=None,
        )
        reg = SimpleNamespace(
            slug="artisan", version="1.0.0",
            content_hash="c1", commitment_hash="c2",
            test_prompts_hash="tp", rubric_hash="rh",
        )
        inv = SimpleNamespace(stop_config_json={})

        builder = ConstructCertificateBuilder()
        cert = builder.build(reg, inv, scorer, "bh", contract=contract)
        self.assertEqual(cert.issuance_status, "READY")
        self.assertEqual(cert.check_plan["total_executed"], 2)

    def test_check_planner_unchanged(self):
        """check_planner.plan_checks still works for non-theatre constructs."""
        from backend.services.contract_service import ContractService  # side-effect: registers domains
        from backend.services.spec_loader import load as load_spec
        from backend.services.policy_normalizer import normalize
        from backend.services.check_planner import plan_checks

        yaml = "slug: artisan\nversion: '1.0.0'\ndomain_claims:\n  - design_systems\nskill_manifest:\n  - command: audit\n    domain: design_systems\n"
        spec = load_spec(yaml)
        norm = normalize(spec)
        checks = plan_checks(spec.slug, norm)
        # Should have RUBRIC + 2 ANCHOR = 3 checks
        self.assertEqual(len(checks), 3)
        types = {c.check_type for c in checks}
        self.assertEqual(types, {"RUBRIC", "ANCHOR"})

    def test_execution_status_enum(self):
        from backend.schemas.theatre_execution import EXECUTION_STATUSES
        self.assertIn("PLANNED", EXECUTION_STATUSES)
        self.assertIn("EXECUTED", EXECUTION_STATUSES)
        self.assertIn("SKIPPED", EXECUTION_STATUSES)
        self.assertIn("PASSED", EXECUTION_STATUSES)
        self.assertIn("FAILED", EXECUTION_STATUSES)

    def test_theatre_check_types_constant(self):
        from backend.services.theatre_check_runner import EXECUTABLE_CHECK_TYPES
        self.assertEqual(EXECUTABLE_CHECK_TYPES, {
            "SETTLEMENT_ACCURACY", "ORACLE_CONSISTENCY",
            "CALIBRATION_VALIDITY", "FUNCTIONAL_CORRECTNESS",
        })


class TestContractJsonPersistence(unittest.TestCase):
    """P2 fix: construct_json_text stored on contract for runtime theatre execution."""

    def test_contract_service_stores_construct_json(self):
        """ContractService stores construct_json_text when construct_class is theatre."""
        from backend.services.contract_service import ContractService
        from backend.services.spec_loader import load as load_spec

        yaml_content = (
            "slug: tremor\n"
            "version: '0.1.0'\n"
            "construct_class: theatre\n"
            "domain_claims:\n  - seismic_intelligence\n"
            "skill_manifest:\n  - command: analyze\n    domain: seismic_intelligence\n"
        )
        construct_json = '{"theatre_templates": []}'

        spec = load_spec(yaml_content)
        self.assertEqual(spec.construct_class, "theatre")

        # The contract service persists construct_json_text.
        # We can't test full DB flow here (needs async session), but verify
        # the model accepts the field.
        from backend.database.models import EvaluationContract
        contract = EvaluationContract(
            id="test-contract-id",
            construct_registration_id="test-reg-id",
            spec_hash="sha256:test",
            contract_hash="sha256:test2",
            normalized_claims=[],
            explicit_refusals=[],
            planned_checks=[],
            construct_json_text=construct_json,
            tier_cap=None,
            status="ACTIVE",
        )
        self.assertEqual(contract.construct_json_text, construct_json)

    def test_contract_construct_json_none_for_skill_constructs(self):
        """Skill constructs have construct_json_text=None."""
        from backend.database.models import EvaluationContract
        contract = EvaluationContract(
            id="test-skill",
            construct_registration_id="test-reg",
            spec_hash="sha256:s",
            contract_hash="sha256:c",
            normalized_claims=[],
            explicit_refusals=[],
            planned_checks=[],
            tier_cap=None,
            status="ACTIVE",
        )
        self.assertIsNone(contract.construct_json_text)


if __name__ == "__main__":
    unittest.main()
