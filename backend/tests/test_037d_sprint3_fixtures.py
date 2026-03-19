"""Tests for Cycle 037d Sprint 3 — TREMOR + CORONA Fixtures + Regression.

Tests cover:
- TREMOR fixture: full end-to-end with 5 templates, 3 sources, Brier scoring (4 tests)
- CORONA fixture: root-level layout, rlmf.exports Brier inference (2 tests)
- Regression: skill construct unchanged, hash determinism (2 tests)
"""

import json
import unittest

from backend.services.spec_loader import load
from backend.services.policy_normalizer import normalize
from backend.services.check_planner import plan_checks, compute_contract_hash
from backend.services.theatre_policy_rules import parse_construct_json
from backend.services.theatre_check_planner import (
    plan_theatre_checks,
    merge_theatre_checks,
)


# ── Fixtures ────────────────────────────────────────────────────────────

TREMOR_CONSTRUCT_JSON = json.dumps({
    "name": "tremor",
    "version": "0.1.0",
    "echelon": {
        "theatre_templates": [
            {"id": "magnitude_gate", "name": "Magnitude Gate",
             "resolution": "binary", "oracle": "USGS reviewed catalog",
             "brier_type": "binary"},
            {"id": "aftershock_cascade", "name": "Aftershock Cascade",
             "resolution": "multi_bucket", "oracle": "USGS reviewed catalog",
             "brier_type": "multi_class"},
            {"id": "swarm_watch", "name": "Swarm Watch",
             "resolution": "binary", "oracle": "USGS reviewed catalog",
             "brier_type": "binary"},
            {"id": "depth_regime", "name": "Depth Regime",
             "resolution": "binary", "oracle": "USGS reviewed depth",
             "brier_type": "binary"},
            {"id": "oracle_divergence", "name": "Oracle Divergence",
             "resolution": "binary", "oracle": "USGS automatic vs reviewed comparison",
             "brier_type": "binary"},
        ],
        "osint_sources": [
            {"id": "usgs_neic", "name": "USGS NEIC",
             "endpoint": "https://earthquake.usgs.gov/fdsnws/event/1",
             "role": "primary"},
            {"id": "emsc", "name": "EMSC",
             "endpoint": "https://seismicportal.eu/fdsnws/event/1",
             "role": "cross_validation"},
            {"id": "iris_dmc", "name": "IRIS DMC",
             "endpoint": "https://service.iris.edu/fdsnws/event/1",
             "role": "cross_validation"},
        ],
        "verification_checks": [
            {"check": "evidence_bundle_accuracy",
             "ground_truth": "USGS reviewed catalog",
             "description": "Magnitude and location match USGS reviewed values"},
            {"check": "settlement_tier_correctness",
             "ground_truth": "USGS event status field",
             "description": "Settlement tier matches USGS review state"},
            {"check": "brier_score_computation",
             "ground_truth": "Theatre outcome vs closing position",
             "description": "Brier scores mathematically correct"},
            {"check": "cross_validation_fidelity",
             "ground_truth": "EMSC magnitude for same event",
             "description": "Cross-validation divergence values correct"},
            {"check": "theatre_resolution_integrity",
             "ground_truth": "USGS reviewed catalog query at close time",
             "description": "Theatre outcomes match USGS catalog"},
        ],
        "settlement_tiers": [
            {"tier": 1, "name": "oracle", "condition": "status=reviewed",
             "evidence_class": "ground_truth", "brier_discount": 0},
            {"tier": 2, "name": "provisional_mature",
             "condition": "status=automatic AND age>2h",
             "evidence_class": "provisional_mature", "brier_discount": 0.10},
            {"tier": 3, "name": "market_freeze",
             "condition": "theatre_expiring AND quality<0.5",
             "evidence_class": "provisional", "brier_discount": 0.20},
        ],
    }
})

CORONA_CONSTRUCT_JSON = json.dumps({
    "slug": "corona",
    "name": "CORONA",
    "theatre_templates": [
        {"id": "T1", "name": "flare_class_gate",
         "type": "binary", "resolution": "GOES X-ray + DONKI FLR"},
        {"id": "T2", "name": "geomagnetic_storm_gate",
         "type": "binary", "resolution": "Kp index + DONKI GST"},
        {"id": "T3", "name": "cme_arrival",
         "type": "binary", "resolution": "L1 solar wind shock signature"},
        {"id": "T4", "name": "proton_event_cascade",
         "type": "multi_class", "resolution": "Flare event count",
         "buckets": ["0-1", "2-3", "4-6", "7-10", "11+"]},
        {"id": "T5", "name": "solar_wind_divergence",
         "type": "binary", "resolution": "Sustained Bz volatility threshold"},
    ],
    "data_sources": [
        {"name": "NOAA SWPC", "url": "https://services.swpc.noaa.gov",
         "auth": "none", "feeds": ["GOES X-ray flux", "Kp index"]},
        {"name": "NASA DONKI", "url": "https://api.nasa.gov/DONKI",
         "auth": "api_key", "feeds": ["Solar flares", "CMEs"]},
        {"name": "GFZ Potsdam", "url": "https://kp.gfz-potsdam.de",
         "auth": "none", "feeds": ["Definitive Kp/Hp index"]},
    ],
    "rlmf": {
        "certificate_schema": "echelon-rlmf-v0.1.0",
        "exports": ["brier_score", "position_history", "calibration_bucket", "temporal_analysis"],
    },
})


def _make_skill_yaml():
    """Standard skill construct YAML (no construct_class field)."""
    return (
        "slug: artisan\n"
        "version: '1.0.0'\n"
        "domain_claims:\n  - design_systems\n"
        "skill_manifest:\n  - name: test-skill\n"
    )


# ── Test: TREMOR Fixture ────────────────────────────────────────────────

class TestTremorFixture(unittest.TestCase):
    """T3.1: TREMOR fixture end-to-end."""

    @classmethod
    def setUpClass(cls):
        cls.meta = parse_construct_json(TREMOR_CONSTRUCT_JSON)
        cls.checks = plan_theatre_checks("tremor", cls.meta)

    def test_total_check_count(self):
        """TREMOR produces 13 theatre checks (5+2+1+5)."""
        self.assertEqual(len(self.checks), 13)

    def test_all_four_check_types_present(self):
        """All 4 theatre check types are produced."""
        check_types = {c.check_type for c in self.checks}
        self.assertEqual(check_types, {
            "SETTLEMENT_ACCURACY",
            "ORACLE_CONSISTENCY",
            "CALIBRATION_VALIDITY",
            "FUNCTIONAL_CORRECTNESS",
        })

    def test_check_id_format(self):
        """All check_ids follow theatre:{type}:{entity} format."""
        for check in self.checks:
            self.assertTrue(
                check.check_id.startswith("theatre:"),
                f"Bad check_id format: {check.check_id}",
            )
            parts = check.check_id.split(":")
            self.assertEqual(len(parts), 3, f"Expected 3 parts: {check.check_id}")

    def test_cross_validation_sources_detected(self):
        """EMSC and IRIS_DMC detected as cross-validation sources."""
        oracle_checks = [c for c in self.checks if c.check_type == "ORACLE_CONSISTENCY"]
        oracle_ids = {c.check_id for c in oracle_checks}
        self.assertEqual(len(oracle_checks), 2)
        self.assertIn("theatre:oracle_consistency:emsc", oracle_ids)
        self.assertIn("theatre:oracle_consistency:iris_dmc", oracle_ids)


# ── Test: CORONA Fixture ────────────────────────────────────────────────

class TestCoronaFixture(unittest.TestCase):
    """T3.2: CORONA fixture with root-level layout."""

    @classmethod
    def setUpClass(cls):
        cls.meta = parse_construct_json(CORONA_CONSTRUCT_JSON)
        cls.checks = plan_theatre_checks("corona", cls.meta)

    def test_parser_handles_root_level_layout(self):
        """CORONA root-level theatre_templates and data_sources parsed correctly."""
        self.assertEqual(self.meta.name, "CORONA")
        self.assertEqual(len(self.meta.theatre_templates), 5)
        self.assertEqual(len(self.meta.osint_sources), 3)
        # CORONA's "resolution" field is the oracle, "type" is the resolution
        self.assertEqual(self.meta.theatre_templates[0].resolution, "binary")
        self.assertEqual(self.meta.theatre_templates[0].oracle, "GOES X-ray + DONKI FLR")

    def test_brier_inferred_from_rlmf_exports(self):
        """Brier scoring inferred from rlmf.exports containing 'brier_score'."""
        self.assertTrue(self.meta.has_brier_scoring)
        # Should have CALIBRATION_VALIDITY check
        calib = [c for c in self.checks if c.check_type == "CALIBRATION_VALIDITY"]
        self.assertEqual(len(calib), 1)


# ── Test: Regression ────────────────────────────────────────────────────

class TestRegression(unittest.TestCase):
    """T3.3: Skill construct and hash determinism regression."""

    def test_skill_construct_unchanged(self):
        """Skill construct without construct_class produces same output as pre-037d."""
        spec = load(_make_skill_yaml())
        self.assertEqual(spec.construct_class, "skill")
        norm = normalize(spec)
        checks = plan_checks(spec.slug, norm)
        # Only base check types — no theatre types
        check_types = {c.check_type for c in checks}
        self.assertTrue(check_types.issubset({"RUBRIC", "BENCHMARK", "ANCHOR"}))
        # No theatre checks present
        theatre_types = {"SETTLEMENT_ACCURACY", "ORACLE_CONSISTENCY",
                         "CALIBRATION_VALIDITY", "FUNCTIONAL_CORRECTNESS"}
        self.assertEqual(check_types & theatre_types, set())

    def test_hash_determinism_across_runs(self):
        """Same TREMOR fixture produces identical contract hash across runs."""
        spec_yaml = (
            "slug: tremor\n"
            "version: '0.1.0'\n"
            "construct_class: theatre\n"
            "domain_claims:\n  - seismic_intelligence\n"
            "skill_manifest:\n  - name: poll\n"
        )
        hashes = set()
        for _ in range(5):
            spec = load(spec_yaml)
            norm = normalize(spec)
            base = plan_checks(spec.slug, norm)
            meta = parse_construct_json(TREMOR_CONSTRUCT_JSON)
            theatre = plan_theatre_checks(spec.slug, meta)
            merged = merge_theatre_checks(base, theatre)
            hashes.add(compute_contract_hash(spec.spec_hash, merged))
        self.assertEqual(len(hashes), 1)


if __name__ == "__main__":
    unittest.main()
