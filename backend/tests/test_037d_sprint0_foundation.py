"""Tests for Cycle 037d Sprint 0 — Foundation: Construct Class + Theatre Domains.

Tests cover:
- ConstructSpec.construct_class field parsing (4 tests)
- Theatre domain registration and normalization (4 tests)
"""

import json
import unittest

from backend.services.spec_loader import ConstructSpec, load
from backend.services.policy_normalizer import KNOWN_PRECISE_DOMAINS, normalize


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_yaml(construct_class=None, extra_fields=""):
    """Build minimal valid YAML for testing construct_class parsing."""
    cc_line = f"construct_class: {construct_class}\n" if construct_class is not None else ""
    return (
        f"slug: test-construct\n"
        f"version: '1.0'\n"
        f"domain_claims:\n  - testing\n"
        f"skill_manifest:\n  - name: test-skill\n"
        f"{cc_line}"
        f"{extra_fields}"
    )


# ── Test: ConstructSpec.construct_class ─────────────────────────────────

class TestConstructClassParsing(unittest.TestCase):
    """T0.1: construct_class field on ConstructSpec."""

    def test_theatre_class_parsed(self):
        """Explicit 'theatre' value is preserved."""
        spec = load(_make_yaml(construct_class="theatre"))
        self.assertEqual(spec.construct_class, "theatre")

    def test_skill_class_explicit(self):
        """Explicit 'skill' value is preserved."""
        spec = load(_make_yaml(construct_class="skill"))
        self.assertEqual(spec.construct_class, "skill")

    def test_absent_defaults_to_skill(self):
        """Absent construct_class defaults to 'skill'."""
        spec = load(_make_yaml())
        self.assertEqual(spec.construct_class, "skill")

    def test_unknown_class_defaults_to_skill(self):
        """Unrecognized construct_class defaults to 'skill'."""
        spec = load(_make_yaml(construct_class="spaceship"))
        self.assertEqual(spec.construct_class, "skill")


# ── Test: Theatre Domain Registration ───────────────────────────────────

class TestTheatreDomainRegistration(unittest.TestCase):
    """T0.2: Theatre precise domains registered at import time."""

    @classmethod
    def setUpClass(cls):
        # Import triggers registration
        import backend.services.theatre_policy_rules  # noqa: F401
        cls._snapshot = KNOWN_PRECISE_DOMAINS.copy()

    def test_registration_count(self):
        """At least 10 theatre domains are registered."""
        from backend.services.theatre_policy_rules import THEATRE_PRECISE_DOMAINS
        self.assertTrue(
            THEATRE_PRECISE_DOMAINS.issubset(KNOWN_PRECISE_DOMAINS),
            "Theatre domains should be a subset of KNOWN_PRECISE_DOMAINS",
        )
        self.assertGreaterEqual(len(THEATRE_PRECISE_DOMAINS), 10)

    def test_seismic_intelligence_is_precise(self):
        """normalize() classifies 'seismic_intelligence' as precise."""
        spec = load(_make_yaml())
        spec_with_seismic = ConstructSpec(
            slug=spec.slug,
            version=spec.version,
            domain_claims=["seismic_intelligence"],
            refusals=spec.refusals,
            skill_manifest=spec.skill_manifest,
            raw_yaml=spec.raw_yaml,
            spec_hash=spec.spec_hash,
            construct_class="theatre",
        )
        result = normalize(spec_with_seismic)
        self.assertFalse(result.has_vague_claims)
        self.assertFalse(result.normalized_claims[0]["is_vague"])

    def test_space_weather_is_precise(self):
        """normalize() classifies 'space_weather' as precise."""
        spec = load(_make_yaml())
        spec_with_sw = ConstructSpec(
            slug=spec.slug,
            version=spec.version,
            domain_claims=["space_weather"],
            refusals=spec.refusals,
            skill_manifest=spec.skill_manifest,
            raw_yaml=spec.raw_yaml,
            spec_hash=spec.spec_hash,
            construct_class="theatre",
        )
        result = normalize(spec_with_sw)
        self.assertFalse(result.has_vague_claims)

    def test_unregistered_domain_still_vague(self):
        """A domain not in any registration set remains vague."""
        spec = load(_make_yaml())
        spec_vague = ConstructSpec(
            slug=spec.slug,
            version=spec.version,
            domain_claims=["underwater_basket_weaving"],
            refusals=spec.refusals,
            skill_manifest=spec.skill_manifest,
            raw_yaml=spec.raw_yaml,
            spec_hash=spec.spec_hash,
        )
        result = normalize(spec_vague)
        self.assertTrue(result.has_vague_claims)


# ── Test: construct.json Parser ─────────────────────────────────────────

class TestParseConstructJson(unittest.TestCase):
    """T0.3: parse_construct_json() with TREMOR and CORONA layouts."""

    def setUp(self):
        from backend.services.theatre_policy_rules import parse_construct_json
        self.parse = parse_construct_json

    def test_tremor_style_parsing(self):
        """TREMOR-style echelon.* nested layout is parsed correctly."""
        tremor = json.dumps({
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
                "verification_checks": [
                    {"check": "brier_score_computation",
                     "ground_truth": "Theatre outcome vs closing position",
                     "description": "Brier scores are mathematically correct"},
                ],
                "settlement_tiers": [
                    {"tier": 1, "name": "oracle", "condition": "status=reviewed"},
                ],
            }
        })
        meta = self.parse(tremor)
        self.assertEqual(meta.name, "tremor")
        self.assertEqual(len(meta.theatre_templates), 2)
        self.assertEqual(meta.theatre_templates[0].id, "magnitude_gate")
        self.assertEqual(meta.theatre_templates[0].resolution, "binary")
        self.assertEqual(meta.theatre_templates[0].oracle, "USGS reviewed catalog")
        self.assertEqual(meta.theatre_templates[0].brier_type, "binary")
        self.assertEqual(len(meta.osint_sources), 2)
        self.assertEqual(meta.osint_sources[1].role, "cross_validation")
        self.assertEqual(len(meta.verification_checks), 1)
        self.assertEqual(len(meta.settlement_tiers), 1)
        self.assertTrue(meta.has_brier_scoring)
        self.assertTrue(meta.has_cross_validation)
        self.assertIn("USGS reviewed catalog", meta.oracle_names)

    def test_corona_style_parsing(self):
        """CORONA-style root-level layout with rlmf.exports is parsed correctly."""
        corona = json.dumps({
            "slug": "corona",
            "name": "CORONA",
            "theatre_templates": [
                {"id": "T1", "name": "flare_class_gate",
                 "type": "binary", "resolution": "GOES X-ray + DONKI FLR"},
                {"id": "T2", "name": "geomagnetic_storm_gate",
                 "type": "binary", "resolution": "Kp index + DONKI GST"},
            ],
            "data_sources": [
                {"name": "NOAA SWPC", "url": "https://services.swpc.noaa.gov",
                 "auth": "none", "feeds": ["GOES X-ray flux"]},
                {"name": "NASA DONKI", "url": "https://api.nasa.gov/DONKI",
                 "auth": "api_key", "feeds": ["Solar flares"]},
            ],
            "rlmf": {
                "exports": ["brier_score", "position_history", "calibration_bucket"],
            },
        })
        meta = self.parse(corona)
        self.assertEqual(meta.name, "CORONA")
        self.assertEqual(len(meta.theatre_templates), 2)
        # CORONA: type → resolution, resolution → oracle
        self.assertEqual(meta.theatre_templates[0].resolution, "binary")
        self.assertEqual(meta.theatre_templates[0].oracle, "GOES X-ray + DONKI FLR")
        self.assertIsNone(meta.theatre_templates[0].brier_type)
        # data_sources → osint_sources with derived IDs
        self.assertEqual(len(meta.osint_sources), 2)
        self.assertEqual(meta.osint_sources[0].id, "noaa_swpc")
        self.assertEqual(meta.osint_sources[0].role, "primary")
        # Brier inferred from rlmf.exports
        self.assertTrue(meta.has_brier_scoring)
        # No cross-validation (no role field in data_sources)
        self.assertFalse(meta.has_cross_validation)
        # No verification_checks or settlement_tiers
        self.assertEqual(len(meta.verification_checks), 0)
        self.assertEqual(len(meta.settlement_tiers), 0)

    def test_invalid_json_raises(self):
        """Invalid JSON raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.parse("not json {{{")
        self.assertIn("Invalid JSON", str(ctx.exception))

    def test_minimal_fixture_without_templates_raises(self):
        """construct.json without theatre_templates raises ValueError (037d-fix P2)."""
        minimal = json.dumps({"name": "minimal"})
        with self.assertRaises(ValueError) as ctx:
            self.parse(minimal)
        self.assertIn("theatre_templates", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
