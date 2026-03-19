"""Tests for Cycle 037d Bugfix — Idempotence + Silent Downgrade.

P1: Contract idempotence now uses contract_hash (not spec_hash) so that
    changes to construct_json trigger supersession even when YAML is unchanged.

P2: Invalid construct_json for a theatre construct raises ValueError instead
    of silently creating a contract without theatre checks.
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

THEATRE_YAML = (
    "slug: tremor\n"
    "version: '0.1.0'\n"
    "construct_class: theatre\n"
    "domain_claims:\n  - seismic_intelligence\n  - oracle_verification\n"
    "skill_manifest:\n  - name: poll\n  - name: magnitude-gate\n"
)

SKILL_YAML = (
    "slug: artisan\n"
    "version: '1.0.0'\n"
    "domain_claims:\n  - design_systems\n"
    "skill_manifest:\n  - name: test-skill\n"
)


def _tremor_json_v1():
    """TREMOR construct.json with 2 templates + 1 cross-validation source."""
    return json.dumps({
        "name": "tremor",
        "echelon": {
            "theatre_templates": [
                {"id": "magnitude_gate", "name": "Magnitude Gate",
                 "resolution": "binary", "oracle": "USGS reviewed catalog",
                 "brier_type": "binary"},
                {"id": "aftershock_cascade", "name": "Aftershock Cascade",
                 "resolution": "multi_bucket", "oracle": "USGS reviewed catalog",
                 "brier_type": "multi_class"},
            ],
            "osint_sources": [
                {"id": "usgs_neic", "name": "USGS NEIC", "role": "primary"},
                {"id": "emsc", "name": "EMSC", "role": "cross_validation"},
            ],
            "verification_checks": [],
            "settlement_tiers": [],
        }
    })


def _tremor_json_v2():
    """TREMOR construct.json with 3 templates (added swarm_watch)."""
    return json.dumps({
        "name": "tremor",
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
            ],
            "osint_sources": [
                {"id": "usgs_neic", "name": "USGS NEIC", "role": "primary"},
                {"id": "emsc", "name": "EMSC", "role": "cross_validation"},
            ],
            "verification_checks": [],
            "settlement_tiers": [],
        }
    })


def _plan_full(yaml_content, construct_json=None):
    """Run the full planning pipeline and return (spec, planned, contract_hash)."""
    spec = load(yaml_content)
    norm = normalize(spec)
    planned = plan_checks(spec.slug, norm)

    if construct_json and spec.construct_class == "theatre":
        meta = parse_construct_json(construct_json)
        theatre = plan_theatre_checks(spec.slug, meta)
        planned = merge_theatre_checks(planned, theatre)

    contract_hash = compute_contract_hash(spec.spec_hash, planned)
    return spec, planned, contract_hash


# ── P1: Idempotence uses contract_hash ──────────────────────────────────

class TestIdempotenceUsesContractHash(unittest.TestCase):
    """P1: contract_hash changes when construct_json changes, even with same YAML."""

    def test_same_yaml_same_json_same_hash(self):
        """Identical YAML + identical construct_json → identical contract_hash."""
        _, _, hash1 = _plan_full(THEATRE_YAML, _tremor_json_v1())
        _, _, hash2 = _plan_full(THEATRE_YAML, _tremor_json_v1())
        self.assertEqual(hash1, hash2)

    def test_same_yaml_different_json_different_hash(self):
        """Same YAML + different construct_json → different contract_hash."""
        _, _, hash_v1 = _plan_full(THEATRE_YAML, _tremor_json_v1())
        _, _, hash_v2 = _plan_full(THEATRE_YAML, _tremor_json_v2())
        self.assertNotEqual(hash_v1, hash_v2)

    def test_same_yaml_with_vs_without_json_different_hash(self):
        """Same YAML with construct_json vs without → different contract_hash."""
        _, _, hash_with = _plan_full(THEATRE_YAML, _tremor_json_v1())
        _, _, hash_without = _plan_full(THEATRE_YAML, None)
        self.assertNotEqual(hash_with, hash_without)

    def test_spec_hash_identical_despite_json_change(self):
        """Confirm spec_hash is the same for both — proving the old bug existed."""
        spec_v1, _, _ = _plan_full(THEATRE_YAML, _tremor_json_v1())
        spec_v2, _, _ = _plan_full(THEATRE_YAML, _tremor_json_v2())
        # spec_hash is YAML-only, so it's the same for both
        self.assertEqual(spec_v1.spec_hash, spec_v2.spec_hash)
        # But contract_hash differs (tested above) — this is the fix

    def test_different_yaml_same_json_different_hash(self):
        """Different YAML + same construct_json → different contract_hash."""
        alt_yaml = (
            "slug: tremor\n"
            "version: '0.2.0'\n"  # Changed version
            "construct_class: theatre\n"
            "domain_claims:\n  - seismic_intelligence\n  - oracle_verification\n"
            "skill_manifest:\n  - name: poll\n  - name: magnitude-gate\n"
        )
        _, _, hash1 = _plan_full(THEATRE_YAML, _tremor_json_v1())
        _, _, hash2 = _plan_full(alt_yaml, _tremor_json_v1())
        self.assertNotEqual(hash1, hash2)

    def test_v2_has_more_checks_than_v1(self):
        """v2 construct.json (3 templates) produces more checks than v1 (2 templates)."""
        _, planned_v1, _ = _plan_full(THEATRE_YAML, _tremor_json_v1())
        _, planned_v2, _ = _plan_full(THEATRE_YAML, _tremor_json_v2())
        # v2 adds swarm_watch → 1 extra SETTLEMENT_ACCURACY +
        # 1 extra FUNCTIONAL_CORRECTNESS
        self.assertGreater(len(planned_v2), len(planned_v1))


# ── P2: Invalid construct_json raises ValueError ────────────────────────

class TestInvalidConstructJsonRaises(unittest.TestCase):
    """P2: parse_construct_json raises ValueError for malformed input."""

    def test_empty_json_raises(self):
        """Empty JSON object raises ValueError (no name or theatre_templates)."""
        with self.assertRaises(ValueError):
            parse_construct_json("{}")

    def test_invalid_json_syntax_raises(self):
        """Malformed JSON string raises ValueError."""
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            parse_construct_json("{not valid json")

    def test_missing_templates_raises(self):
        """JSON with name but no theatre_templates raises ValueError."""
        with self.assertRaises(ValueError):
            parse_construct_json(json.dumps({"name": "test"}))

    def test_valid_json_does_not_raise(self):
        """Valid construct.json parses without error."""
        meta = parse_construct_json(_tremor_json_v1())
        self.assertEqual(meta.name, "tremor")
        self.assertEqual(len(meta.theatre_templates), 2)


# ── Regression: skill construct unaffected ──────────────────────────────

class TestSkillConstructUnaffected(unittest.TestCase):
    """Skill constructs ignore construct_json — no theatre checks, no hash change."""

    def test_skill_ignores_construct_json_in_hash(self):
        """Skill construct with construct_json has same hash as without."""
        # Skill construct_class != "theatre" so construct_json is not processed
        _, _, hash_with = _plan_full(SKILL_YAML, _tremor_json_v1())
        _, _, hash_without = _plan_full(SKILL_YAML, None)
        self.assertEqual(hash_with, hash_without)

    def test_skill_has_no_theatre_checks(self):
        """Skill construct produces no theatre check types."""
        _, planned, _ = _plan_full(SKILL_YAML, _tremor_json_v1())
        check_types = {c.check_type for c in planned}
        theatre_types = {"SETTLEMENT_ACCURACY", "ORACLE_CONSISTENCY",
                         "CALIBRATION_VALIDITY", "FUNCTIONAL_CORRECTNESS"}
        self.assertEqual(check_types & theatre_types, set())


if __name__ == "__main__":
    unittest.main()
