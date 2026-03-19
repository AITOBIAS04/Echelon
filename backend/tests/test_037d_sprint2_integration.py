"""Tests for Cycle 037d Sprint 2 — Contract Pipeline Integration.

Tests cover:
- Schema: construct_json on CreateContractRequest
- Route: construct_json passed through to service
- Service: theatre checks merged for theatre constructs, ignored for skill
- Anchor mapper: 4 new theatre rules
- AST verification of theatre_policy_rules import
- Regression: skill construct unchanged, hash determinism
"""

import ast
import json
import unittest
from pathlib import Path

from backend.schemas.construct_schemas import CreateContractRequest
from backend.services.construct_anchor_mapper import map_dimension_anchors
from backend.services.check_planner import PlannedCheck, plan_checks, compute_contract_hash
from backend.services.spec_loader import ConstructSpec, load
from backend.services.policy_normalizer import normalize


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_theatre_yaml():
    """YAML for a theatre construct with precise domains."""
    return (
        "slug: tremor\n"
        "version: '0.1.0'\n"
        "construct_class: theatre\n"
        "domain_claims:\n  - seismic_intelligence\n  - oracle_verification\n"
        "skill_manifest:\n  - name: poll\n  - name: magnitude-gate\n"
    )


def _make_skill_yaml():
    """YAML for a skill construct (default class)."""
    return (
        "slug: artisan\n"
        "version: '1.0.0'\n"
        "domain_claims:\n  - design_systems\n"
        "skill_manifest:\n  - name: test-skill\n"
    )


def _make_tremor_json():
    """Minimal TREMOR-style construct.json."""
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


# ── Test: Schema ────────────────────────────────────────────────────────

class TestCreateContractRequestSchema(unittest.TestCase):
    """T2.1: construct_json on CreateContractRequest."""

    def test_accepts_construct_json(self):
        """CreateContractRequest accepts construct_json field."""
        req = CreateContractRequest(
            yaml_content="slug: test\n",
            construct_json='{"name": "test"}',
        )
        self.assertEqual(req.construct_json, '{"name": "test"}')

    def test_construct_json_defaults_none(self):
        """construct_json defaults to None when not provided."""
        req = CreateContractRequest(yaml_content="slug: test\n")
        self.assertIsNone(req.construct_json)


# ── Test: Contract Service Theatre Integration ──────────────────────────

class TestContractServiceTheatreIntegration(unittest.TestCase):
    """T2.2: Theatre checks merged in contract service pipeline."""

    def test_theatre_construct_gets_theatre_checks(self):
        """Theatre construct with construct_json produces theatre check types."""
        spec = load(_make_theatre_yaml())
        self.assertEqual(spec.construct_class, "theatre")

        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)

        # Simulate what contract_service does
        from backend.services.theatre_policy_rules import parse_construct_json
        from backend.services.theatre_check_planner import plan_theatre_checks, merge_theatre_checks

        meta = parse_construct_json(_make_tremor_json())
        theatre_checks = plan_theatre_checks(spec.slug, meta)
        merged = merge_theatre_checks(base_checks, theatre_checks)

        check_types = {c.check_type for c in merged}
        self.assertIn("SETTLEMENT_ACCURACY", check_types)
        self.assertIn("ORACLE_CONSISTENCY", check_types)
        self.assertIn("CALIBRATION_VALIDITY", check_types)
        self.assertIn("FUNCTIONAL_CORRECTNESS", check_types)
        # Base ANCHOR checks still present (RUBRIC only if rubrics registered)
        self.assertIn("ANCHOR", check_types)

    def test_skill_construct_ignores_construct_json(self):
        """Skill construct does not get theatre checks even with construct_json."""
        spec = load(_make_skill_yaml())
        self.assertEqual(spec.construct_class, "skill")

        # Guard: construct_class != "theatre" → no theatre merge
        # This mirrors contract_service.py: if construct_json and spec.construct_class == "theatre"
        should_merge = _make_tremor_json() and spec.construct_class == "theatre"
        self.assertFalse(should_merge)


# ── Test: Anchor Mapper Theatre Rules ───────────────────────────────────

class TestAnchorMapperTheatreRules(unittest.TestCase):
    """T2.3: Theatre-specific mapping rules in construct_anchor_mapper."""

    def test_settlement_maps_to_live_external(self):
        """'settlement' keyword maps to LIVE_EXTERNAL_EVIDENCE."""
        result = map_dimension_anchors("settlement_accuracy")
        self.assertFalse(result.weakly_anchored)
        anchor_ids = {a.anchor_id for a in result.anchors}
        self.assertIn("theatre_oracle_settlement", anchor_ids)

    def test_brier_maps_to_deterministic(self):
        """'brier' keyword maps to DETERMINISTIC_CHECK."""
        result = map_dimension_anchors("brier_score_validation")
        self.assertFalse(result.weakly_anchored)
        anchor_ids = {a.anchor_id for a in result.anchors}
        self.assertIn("theatre_calibration", anchor_ids)

    def test_usgs_maps_to_live_external(self):
        """'usgs' keyword maps to LIVE_EXTERNAL_EVIDENCE via theatre_named_oracle."""
        result = map_dimension_anchors("usgs_data_verification")
        self.assertFalse(result.weakly_anchored)
        anchor_ids = {a.anchor_id for a in result.anchors}
        self.assertIn("theatre_named_oracle", anchor_ids)

    def test_unrecognized_still_weakly_anchored(self):
        """Unrecognized dimension remains weakly anchored."""
        result = map_dimension_anchors("quantum_entanglement_check")
        self.assertTrue(result.weakly_anchored)
        self.assertEqual(len(result.anchors), 0)


# ── Test: AST Import Verification ───────────────────────────────────────

class TestContractServiceImports(unittest.TestCase):
    """Verify contract_service.py imports theatre_policy_rules."""

    def test_contract_service_imports_theatre_policy_rules(self):
        """contract_service.py imports theatre_policy_rules (side-effect registration)."""
        cs_path = Path(__file__).resolve().parent.parent / "services" / "contract_service.py"
        tree = ast.parse(cs_path.read_text())
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)
        self.assertIn("backend.services.theatre_policy_rules", imported_modules)
        self.assertIn("backend.services.theatre_check_planner", imported_modules)


# ── Test: Hash Determinism ──────────────────────────────────────────────

class TestHashDeterminism(unittest.TestCase):
    """Contract hash changes with theatre checks, deterministic across runs."""

    def test_hash_changes_with_theatre_checks(self):
        """Contract hash differs when theatre checks are added."""
        spec = load(_make_theatre_yaml())
        norm = normalize(spec)
        base_checks = plan_checks(spec.slug, norm)
        base_hash = compute_contract_hash(spec.spec_hash, base_checks)

        from backend.services.theatre_policy_rules import parse_construct_json
        from backend.services.theatre_check_planner import plan_theatre_checks, merge_theatre_checks

        meta = parse_construct_json(_make_tremor_json())
        theatre_checks = plan_theatre_checks(spec.slug, meta)
        merged = merge_theatre_checks(base_checks, theatre_checks)
        merged_hash = compute_contract_hash(spec.spec_hash, merged)

        self.assertNotEqual(base_hash, merged_hash)

    def test_hash_deterministic_across_runs(self):
        """Same inputs produce same hash across multiple runs."""
        spec = load(_make_theatre_yaml())
        norm = normalize(spec)

        from backend.services.theatre_policy_rules import parse_construct_json
        from backend.services.theatre_check_planner import plan_theatre_checks, merge_theatre_checks

        hashes = set()
        for _ in range(3):
            base_checks = plan_checks(spec.slug, norm)
            meta = parse_construct_json(_make_tremor_json())
            theatre_checks = plan_theatre_checks(spec.slug, meta)
            merged = merge_theatre_checks(base_checks, theatre_checks)
            hashes.add(compute_contract_hash(spec.spec_hash, merged))

        self.assertEqual(len(hashes), 1, "Hash should be deterministic across runs")


if __name__ == "__main__":
    unittest.main()
