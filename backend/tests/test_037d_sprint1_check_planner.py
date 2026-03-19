"""Tests for Cycle 037d Sprint 1 — Theatre Check Planner.

Tests cover:
- SETTLEMENT_ACCURACY generation (per template)
- ORACLE_CONSISTENCY generation (cross-validation only)
- CALIBRATION_VALIDITY generation (Brier scoring only)
- FUNCTIONAL_CORRECTNESS generation (per template)
- Sort determinism
- Dedup on duplicate template IDs
- Merge preserves both sets
- Merge dedup on overlapping check_ids
"""

import unittest

from backend.services.check_planner import PlannedCheck
from backend.services.theatre_check_planner import (
    THEATRE_CHECK_TYPES,
    plan_theatre_checks,
    merge_theatre_checks,
)
from backend.services.theatre_policy_rules import (
    TheatreConstructMeta,
    TheatreTemplate,
    OsintSource,
)


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_meta(
    name="test",
    templates=None,
    sources=None,
    has_brier=True,
    has_cross_val=True,
):
    """Build a TheatreConstructMeta for testing."""
    if templates is None:
        templates = [
            TheatreTemplate(id="t1", name="T1", resolution="binary",
                            oracle="Oracle A", brier_type="binary"),
            TheatreTemplate(id="t2", name="T2", resolution="multi_bucket",
                            oracle="Oracle B", brier_type="multi_class"),
        ]
    if sources is None:
        sources = [
            OsintSource(id="primary_src", name="Primary", role="primary"),
            OsintSource(id="cross_src", name="CrossVal", role="cross_validation"),
        ]
    oracle_names = list({t.oracle for t in templates if t.oracle})
    return TheatreConstructMeta(
        name=name,
        theatre_templates=templates,
        osint_sources=sources,
        verification_checks=[],
        settlement_tiers=[],
        has_brier_scoring=has_brier,
        has_cross_validation=has_cross_val,
        oracle_names=sorted(oracle_names),
    )


# ── Test: plan_theatre_checks ───────────────────────────────────────────

class TestPlanTheatreChecks(unittest.TestCase):
    """T1.1: plan_theatre_checks() generation rules."""

    def test_settlement_accuracy_per_template(self):
        """One SETTLEMENT_ACCURACY check per theatre template."""
        meta = _make_meta()
        checks = plan_theatre_checks("slug", meta)
        settlement = [c for c in checks if c.check_type == "SETTLEMENT_ACCURACY"]
        self.assertEqual(len(settlement), 2)
        self.assertTrue(all(c.critical for c in settlement))
        self.assertTrue(all(c.anchor_class == "LIVE_EXTERNAL_EVIDENCE" for c in settlement))
        ids = {c.check_id for c in settlement}
        self.assertIn("theatre:settlement_accuracy:t1", ids)
        self.assertIn("theatre:settlement_accuracy:t2", ids)

    def test_oracle_consistency_cross_validation_only(self):
        """ORACLE_CONSISTENCY checks only for cross-validation sources."""
        meta = _make_meta(has_cross_val=True)
        checks = plan_theatre_checks("slug", meta)
        oracle = [c for c in checks if c.check_type == "ORACLE_CONSISTENCY"]
        self.assertEqual(len(oracle), 1)
        self.assertEqual(oracle[0].check_id, "theatre:oracle_consistency:cross_src")
        self.assertTrue(oracle[0].critical)

    def test_no_oracle_consistency_without_cross_validation(self):
        """No ORACLE_CONSISTENCY when has_cross_validation is False."""
        meta = _make_meta(has_cross_val=False)
        checks = plan_theatre_checks("slug", meta)
        oracle = [c for c in checks if c.check_type == "ORACLE_CONSISTENCY"]
        self.assertEqual(len(oracle), 0)

    def test_calibration_validity_with_brier(self):
        """CALIBRATION_VALIDITY check generated when Brier scoring present."""
        meta = _make_meta(has_brier=True)
        checks = plan_theatre_checks("slug", meta)
        calib = [c for c in checks if c.check_type == "CALIBRATION_VALIDITY"]
        self.assertEqual(len(calib), 1)
        self.assertFalse(calib[0].critical)
        self.assertEqual(calib[0].anchor_class, "DETERMINISTIC_CHECK")

    def test_no_calibration_without_brier(self):
        """No CALIBRATION_VALIDITY when has_brier_scoring is False."""
        meta = _make_meta(has_brier=False)
        checks = plan_theatre_checks("slug", meta)
        calib = [c for c in checks if c.check_type == "CALIBRATION_VALIDITY"]
        self.assertEqual(len(calib), 0)

    def test_functional_correctness_per_template(self):
        """One FUNCTIONAL_CORRECTNESS check per theatre template."""
        meta = _make_meta()
        checks = plan_theatre_checks("slug", meta)
        func = [c for c in checks if c.check_type == "FUNCTIONAL_CORRECTNESS"]
        self.assertEqual(len(func), 2)
        self.assertTrue(all(not c.critical for c in func))
        self.assertTrue(all(c.anchor_class == "DETERMINISTIC_CHECK" for c in func))

    def test_sort_determinism(self):
        """Checks are sorted by (check_type, domain, check_id)."""
        meta = _make_meta()
        checks = plan_theatre_checks("slug", meta)
        keys = [(c.check_type, c.domain, c.check_id) for c in checks]
        self.assertEqual(keys, sorted(keys))

    def test_dedup_on_duplicate_template_ids(self):
        """Duplicate template IDs don't produce duplicate checks."""
        templates = [
            TheatreTemplate(id="dup", name="Dup1", resolution="binary",
                            oracle="Oracle", brier_type="binary"),
            TheatreTemplate(id="dup", name="Dup2", resolution="binary",
                            oracle="Oracle", brier_type="binary"),
        ]
        meta = _make_meta(templates=templates, has_cross_val=False, has_brier=False)
        checks = plan_theatre_checks("slug", meta)
        settlement = [c for c in checks if c.check_type == "SETTLEMENT_ACCURACY"]
        functional = [c for c in checks if c.check_type == "FUNCTIONAL_CORRECTNESS"]
        self.assertEqual(len(settlement), 1)
        self.assertEqual(len(functional), 1)


# ── Test: merge_theatre_checks ──────────────────────────────────────────

class TestMergeTheatreChecks(unittest.TestCase):
    """T1.2: merge_theatre_checks() dedup and sort."""

    def test_merge_preserves_both_sets(self):
        """Merged output contains checks from both base and theatre."""
        base = [
            PlannedCheck(check_id="rubric:test:a", check_type="RUBRIC",
                         domain="a", source="s", critical=True),
        ]
        theatre = [
            PlannedCheck(check_id="theatre:settlement_accuracy:t1",
                         check_type="SETTLEMENT_ACCURACY", domain="theatre:t1",
                         source="s", critical=True, anchor_class="LIVE_EXTERNAL_EVIDENCE"),
        ]
        merged = merge_theatre_checks(base, theatre)
        self.assertEqual(len(merged), 2)
        ids = {c.check_id for c in merged}
        self.assertIn("rubric:test:a", ids)
        self.assertIn("theatre:settlement_accuracy:t1", ids)

    def test_merge_dedup_overlapping(self):
        """Duplicate check_ids across sets are deduplicated."""
        shared_id = "theatre:settlement_accuracy:t1"
        base = [
            PlannedCheck(check_id=shared_id, check_type="SETTLEMENT_ACCURACY",
                         domain="theatre:t1", source="base", critical=True,
                         anchor_class="LIVE_EXTERNAL_EVIDENCE"),
        ]
        theatre = [
            PlannedCheck(check_id=shared_id, check_type="SETTLEMENT_ACCURACY",
                         domain="theatre:t1", source="theatre", critical=True,
                         anchor_class="LIVE_EXTERNAL_EVIDENCE"),
        ]
        merged = merge_theatre_checks(base, theatre)
        self.assertEqual(len(merged), 1)
        # Base takes precedence (added first)
        self.assertEqual(merged[0].source, "base")

    def test_merge_preserves_sort(self):
        """Merged result is sorted by (check_type, domain, check_id)."""
        base = [
            PlannedCheck(check_id="rubric:z:z", check_type="RUBRIC",
                         domain="z", source="s", critical=True),
        ]
        theatre = [
            PlannedCheck(check_id="theatre:calibration_validity:a",
                         check_type="CALIBRATION_VALIDITY", domain="calibration:a",
                         source="s", critical=False, anchor_class="DETERMINISTIC_CHECK"),
        ]
        merged = merge_theatre_checks(base, theatre)
        keys = [(c.check_type, c.domain, c.check_id) for c in merged]
        self.assertEqual(keys, sorted(keys))


# ── Test: THEATRE_CHECK_TYPES constant ──────────────────────────────────

class TestTheatreCheckTypes(unittest.TestCase):

    def test_four_check_types(self):
        """THEATRE_CHECK_TYPES has exactly 4 entries."""
        self.assertEqual(len(THEATRE_CHECK_TYPES), 4)

    def test_anchor_class_mappings(self):
        """Correct anchor class for each check type."""
        self.assertEqual(THEATRE_CHECK_TYPES["SETTLEMENT_ACCURACY"], "LIVE_EXTERNAL_EVIDENCE")
        self.assertEqual(THEATRE_CHECK_TYPES["ORACLE_CONSISTENCY"], "LIVE_EXTERNAL_EVIDENCE")
        self.assertEqual(THEATRE_CHECK_TYPES["CALIBRATION_VALIDITY"], "DETERMINISTIC_CHECK")
        self.assertEqual(THEATRE_CHECK_TYPES["FUNCTIONAL_CORRECTNESS"], "DETERMINISTIC_CHECK")


if __name__ == "__main__":
    unittest.main()
