"""Tests for Cycle 037b — Evaluator Orchestration Schemas + Residual Dimension Filter.

Sprint 0: Validates schema construction, validation, and the deterministic-vs-rubric
dimension separation logic.
"""

import pytest

from backend.schemas.evaluator_orchestration import (
    DimensionConvergence,
    EvaluatorOutcome,
    EvaluatorScoreRecord,
    RunConvergenceSummary,
)
from backend.services.residual_dimension_filter import (
    ResidualDimension,
    filter_residual_dimensions,
)


# ═══════════════════════════════════════════════════════════
# Schema Tests
# ═══════════════════════════════════════════════════════════


class TestEvaluatorScoreRecord:
    def test_valid_pass_record(self):
        record = EvaluatorScoreRecord(
            evaluator_id="gpt-4o",
            dimension="design_systems",
            verdict="PASS",
            score=0.85,
            rationale="Strong adherence to design token conventions",
        )
        assert record.evaluator_id == "gpt-4o"
        assert record.verdict == "PASS"
        assert record.score == 0.85

    def test_abstain_verdict_with_no_score(self):
        record = EvaluatorScoreRecord(
            evaluator_id="opus-4",
            dimension="methodology",
            verdict="ABSTAIN",
        )
        assert record.verdict == "ABSTAIN"
        assert record.score is None
        assert record.rationale is None

    def test_invalid_verdict_rejected(self):
        with pytest.raises(Exception):
            EvaluatorScoreRecord(
                evaluator_id="test",
                dimension="test",
                verdict="MAYBE",
            )

    def test_score_bounds(self):
        with pytest.raises(Exception):
            EvaluatorScoreRecord(
                evaluator_id="test",
                dimension="test",
                verdict="PASS",
                score=1.5,
            )


class TestDimensionConvergence:
    def test_converged_pass(self):
        dc = DimensionConvergence(
            dimension="design_systems",
            outcome="CONVERGED_PASS",
            evaluator_ids=["gpt-4o", "opus-4", "sonnet-4"],
            verdicts=["PASS", "PASS", "PASS"],
            scores=[0.85, 0.82, 0.88],
            confidence="HIGH",
        )
        assert dc.outcome == "CONVERGED_PASS"
        assert len(dc.evaluator_ids) == 3
        assert dc.confidence == "HIGH"

    def test_divergent(self):
        dc = DimensionConvergence(
            dimension="methodology",
            outcome="DIVERGENT",
            evaluator_ids=["gpt-4o", "opus-4", "sonnet-4"],
            verdicts=["PASS", "FAIL", "PASS"],
        )
        assert dc.outcome == "DIVERGENT"


class TestRunConvergenceSummary:
    def test_full_summary(self):
        summary = RunConvergenceSummary(
            evaluator_ids=["gpt-4o", "opus-4", "sonnet-4"],
            total_dimensions=3,
            converged_pass=2,
            converged_fail=0,
            divergent=1,
            skipped=0,
            escalation_required=True,
            rubric_version="v1.0.0",
        )
        assert summary.total_dimensions == 3
        assert summary.escalation_required is True

    def test_empty_summary(self):
        summary = RunConvergenceSummary(
            evaluator_ids=[],
            total_dimensions=0,
        )
        assert summary.converged_pass == 0
        assert summary.escalation_required is False


class TestEvaluatorOutcome:
    def test_eligible_outcome(self):
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(
                evaluator_ids=["a", "b", "c"],
                total_dimensions=2,
                converged_pass=2,
            ),
            issuance_eligible=True,
        )
        assert outcome.issuance_eligible is True
        assert outcome.block_reason is None

    def test_blocked_outcome(self):
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(
                evaluator_ids=["a", "b", "c"],
                total_dimensions=2,
                divergent=2,
                escalation_required=True,
            ),
            issuance_eligible=False,
            block_reason="All required dimensions divergent",
        )
        assert outcome.issuance_eligible is False
        assert "divergent" in outcome.block_reason


# ═══════════════════════════════════════════════════════════
# Residual Dimension Filter Tests
# ═══════════════════════════════════════════════════════════

def _check(check_id, check_type, domain, critical=False, **kwargs):
    """Helper to build a planned check dict."""
    return {
        "check_id": check_id,
        "check_type": check_type,
        "domain": domain,
        "source": f"test:{check_id}",
        "critical": critical,
        **kwargs,
    }


class TestResidualDimensionFilter:
    def test_rubric_checks_are_residual(self):
        """RUBRIC checks should pass through as residual dimensions."""
        planned = [
            _check("rubric:artisan:design_systems", "RUBRIC", "design_systems", critical=True),
            _check("rubric:artisan:code_generation", "RUBRIC", "code_generation", critical=True),
        ]
        result = filter_residual_dimensions(planned, executed_results={})
        assert len(result) == 2
        dims = {r.dimension for r in result}
        assert dims == {"design_systems", "code_generation"}

    def test_anchor_checks_excluded(self):
        """ANCHOR checks are deterministic and should not appear in residuals."""
        planned = [
            _check("anchor:public_standard", "ANCHOR", "*", critical=True),
            _check("anchor:deterministic_check", "ANCHOR", "*"),
            _check("rubric:artisan:design_systems", "RUBRIC", "design_systems"),
        ]
        result = filter_residual_dimensions(planned, executed_results={})
        assert len(result) == 1
        assert result[0].dimension == "design_systems"

    def test_benchmark_checks_excluded(self):
        """BENCHMARK checks are deterministic and should not appear in residuals."""
        planned = [
            _check("benchmark:humaneval", "BENCHMARK", "code_generation"),
            _check("rubric:artisan:design_systems", "RUBRIC", "design_systems"),
        ]
        result = filter_residual_dimensions(planned, executed_results={})
        assert len(result) == 1
        assert result[0].dimension == "design_systems"

    def test_deterministically_covered_rubric_excluded(self):
        """A RUBRIC domain already covered by a deterministic BENCHMARK result is excluded."""
        planned = [
            _check("benchmark:humaneval", "BENCHMARK", "code_generation"),
            _check("rubric:artisan:code_generation", "RUBRIC", "code_generation"),
        ]
        # code_generation has a deterministic execution result from the benchmark
        result = filter_residual_dimensions(
            planned, executed_results={"code_generation": 0.92}
        )
        assert len(result) == 0

    def test_empty_plan_returns_empty(self):
        """No planned checks means no residuals."""
        result = filter_residual_dimensions([], executed_results={})
        assert result == []

    def test_all_deterministic_returns_empty(self):
        """If all checks are ANCHOR/BENCHMARK, there are no residual dimensions."""
        planned = [
            _check("anchor:public_standard", "ANCHOR", "*"),
            _check("benchmark:eval1", "BENCHMARK", "math"),
        ]
        result = filter_residual_dimensions(planned, executed_results={"math": 0.9})
        assert result == []

    def test_duplicate_rubric_domains_deduped(self):
        """Multiple RUBRIC checks for the same domain should deduplicate."""
        planned = [
            _check("rubric:artisan:design_systems", "RUBRIC", "design_systems"),
            _check("rubric:artisan2:design_systems", "RUBRIC", "design_systems"),
        ]
        result = filter_residual_dimensions(planned, executed_results={})
        assert len(result) == 1
        assert result[0].dimension == "design_systems"

    def test_mixed_plan_typical_cycle037(self):
        """Typical cycle-037 contract with anchors + rubrics."""
        planned = [
            _check("anchor:public_standard", "ANCHOR", "*", critical=True),
            _check("anchor:deterministic_check", "ANCHOR", "*"),
            _check("rubric:artisan:design_systems", "RUBRIC", "design_systems", critical=True),
            _check("rubric:artisan:code_generation", "RUBRIC", "code_generation", critical=True),
        ]
        result = filter_residual_dimensions(planned, executed_results={})
        assert len(result) == 2
        dims = {r.dimension for r in result}
        assert dims == {"design_systems", "code_generation"}
        # Both should preserve critical flag
        for r in result:
            assert r.critical is True
