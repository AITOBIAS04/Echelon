"""Tests for CheckPlanner — deterministic check plan generation + contract hash.

Cycle 037: Contract-Backed Verification Infrastructure.
"""

from backend.services.policy_normalizer import NormalizationResult
from backend.services.check_planner import (
    plan_checks,
    compute_contract_hash,
    checks_to_dicts,
)


def _make_norm_result(claims, refusals=None, tier_cap=None, has_vague=False):
    """Helper to build a NormalizationResult for testing."""
    return NormalizationResult(
        normalized_claims=claims,
        explicit_refusals=refusals or [],
        tier_cap=tier_cap,
        has_vague_claims=has_vague,
    )


class TestCheckPlanner:
    def test_artisan_rubric_checks(self):
        """Artisan construct with known rubric domains → RUBRIC checks for each."""
        claims = [
            {"domain": "Design Systems", "original": "Design Systems",
             "is_vague": False, "matched_category": "design_systems"},
            {"domain": "Motion Design", "original": "Motion Design",
             "is_vague": False, "matched_category": "motion_design"},
        ]
        norm = _make_norm_result(claims)
        checks = plan_checks("artisan", norm)

        rubric_checks = [c for c in checks if c.check_type == "RUBRIC"]
        assert len(rubric_checks) == 2
        assert rubric_checks[0].check_id == "rubric:artisan:design_systems"
        assert rubric_checks[1].check_id == "rubric:artisan:motion_design"
        assert all(c.critical for c in rubric_checks)

    def test_code_domain_benchmark_check(self):
        """Available benchmark asset → BENCHMARK check created."""
        claims = [
            {"domain": "Code Generation", "original": "Code Generation",
             "is_vague": False, "matched_category": "code_generation"},
        ]
        norm = _make_norm_result(claims)
        assets = {"benchmarks": [{"id": "humaneval", "domain": "Code Generation"}]}
        checks = plan_checks("test-construct", norm, available_assets=assets)

        benchmark_checks = [c for c in checks if c.check_type == "BENCHMARK"]
        assert len(benchmark_checks) == 1
        assert benchmark_checks[0].check_id == "benchmark:humaneval"
        assert benchmark_checks[0].domain == "Code Generation"
        assert benchmark_checks[0].asset_id == "humaneval"

    def test_anchor_checks_always_present(self):
        """Anchor checks (PUBLIC_STANDARD, DETERMINISTIC_CHECK) always included."""
        claims = [
            {"domain": "Accessibility", "original": "Accessibility",
             "is_vague": False, "matched_category": "accessibility"},
        ]
        norm = _make_norm_result(claims)
        checks = plan_checks("any-construct", norm)

        anchor_checks = [c for c in checks if c.check_type == "ANCHOR"]
        assert len(anchor_checks) == 2
        anchor_classes = {c.anchor_class for c in anchor_checks}
        assert "PUBLIC_STANDARD" in anchor_classes
        assert "DETERMINISTIC_CHECK" in anchor_classes

        # PUBLIC_STANDARD is critical, DETERMINISTIC_CHECK is not
        public = next(c for c in anchor_checks if c.anchor_class == "PUBLIC_STANDARD")
        determ = next(c for c in anchor_checks if c.anchor_class == "DETERMINISTIC_CHECK")
        assert public.critical is True
        assert determ.critical is False

    def test_deterministic_output(self):
        """Same input always produces same plan."""
        claims = [
            {"domain": "Design Systems", "original": "Design Systems",
             "is_vague": False, "matched_category": "design_systems"},
            {"domain": "Motion Design", "original": "Motion Design",
             "is_vague": False, "matched_category": "motion_design"},
        ]
        norm = _make_norm_result(claims)
        checks1 = plan_checks("artisan", norm)
        checks2 = plan_checks("artisan", norm)
        assert checks_to_dicts(checks1) == checks_to_dicts(checks2)

    def test_contract_hash_stability(self):
        """Same spec_hash + checks → same contract_hash."""
        claims = [
            {"domain": "Testing", "original": "Testing",
             "is_vague": False, "matched_category": "testing"},
        ]
        norm = _make_norm_result(claims)
        checks = plan_checks("test-construct", norm)

        hash1 = compute_contract_hash("sha256:abc123", checks)
        hash2 = compute_contract_hash("sha256:abc123", checks)
        assert hash1 == hash2
        assert hash1.startswith("sha256:")
        assert len(hash1) > 10

    def test_no_rubrics_still_plans(self):
        """Construct without registered rubrics → still gets anchor checks."""
        claims = [
            {"domain": "Testing", "original": "Testing",
             "is_vague": False, "matched_category": "testing"},
        ]
        norm = _make_norm_result(claims)
        checks = plan_checks("unknown-slug", norm)

        # RUBRIC check still planned (but asset_id will be None since no rubric)
        rubric_checks = [c for c in checks if c.check_type == "RUBRIC"]
        assert len(rubric_checks) == 1
        assert rubric_checks[0].asset_id is None  # No rubric available

        # Anchor checks still present
        anchor_checks = [c for c in checks if c.check_type == "ANCHOR"]
        assert len(anchor_checks) == 2

    def test_missing_benchmark_still_planned(self):
        """Benchmark in available_assets but not present → check still planned."""
        claims = [
            {"domain": "Code Review", "original": "Code Review",
             "is_vague": False, "matched_category": "code_review"},
        ]
        norm = _make_norm_result(claims)
        assets = {"benchmarks": [{"id": "nonexistent_dataset", "domain": "Code Review"}]}
        checks = plan_checks("test", norm, available_assets=assets)

        benchmark_checks = [c for c in checks if c.check_type == "BENCHMARK"]
        assert len(benchmark_checks) == 1
        assert benchmark_checks[0].asset_id == "nonexistent_dataset"

    def test_mixed_domains_sorted(self):
        """Mixed domains → output sorted by (check_type, domain, check_id)."""
        claims = [
            {"domain": "Motion Design", "original": "Motion Design",
             "is_vague": False, "matched_category": "motion_design"},
            {"domain": "Design Systems", "original": "Design Systems",
             "is_vague": False, "matched_category": "design_systems"},
        ]
        norm = _make_norm_result(claims)
        assets = {"benchmarks": [{"id": "bench1", "domain": "Design Systems"}]}
        checks = plan_checks("artisan", norm, available_assets=assets)

        # Verify sorted order
        keys = [(c.check_type, c.domain, c.check_id) for c in checks]
        assert keys == sorted(keys)
