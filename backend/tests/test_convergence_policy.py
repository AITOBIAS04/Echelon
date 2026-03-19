"""Tests for Cycle 037b Sprint 2 — Convergence Policy + Persistence.

Validates:
- Per-dimension convergence: 3/3 pass, 3/3 fail, 2/3 pass, divergent, skipped
- Run-level convergence summary with escalation logic
- Persistence payload generation
"""

import pytest

from backend.schemas.evaluator_orchestration import (
    EvaluatorScoreRecord,
)
from backend.services.convergence_policy import (
    build_orchestration_persistence,
    compute_dimension_convergence,
    compute_run_convergence,
)


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════


def _record(evaluator_id: str, dimension: str, verdict: str, score=0.85):
    return EvaluatorScoreRecord(
        evaluator_id=evaluator_id,
        dimension=dimension,
        verdict=verdict,
        score=score,
    )


# ═══════════════════════════════════════════════════════════
# Per-Dimension Convergence Tests
# ═══════════════════════════════════════════════════════════


class TestDimensionConvergence:
    def test_three_three_pass(self):
        """3/3 PASS → CONVERGED_PASS, HIGH confidence."""
        records = [
            _record("a", "design", "PASS", 0.85),
            _record("b", "design", "PASS", 0.82),
            _record("c", "design", "PASS", 0.88),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "CONVERGED_PASS"
        assert dc.confidence == "HIGH"
        assert len(dc.evaluator_ids) == 3

    def test_three_three_fail(self):
        """3/3 FAIL → CONVERGED_FAIL, HIGH confidence."""
        records = [
            _record("a", "design", "FAIL", 0.20),
            _record("b", "design", "FAIL", 0.15),
            _record("c", "design", "FAIL", 0.25),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "CONVERGED_FAIL"
        assert dc.confidence == "HIGH"

    def test_two_three_pass(self):
        """2/3 PASS → CONVERGED_PASS, LOWER confidence."""
        records = [
            _record("a", "design", "PASS", 0.85),
            _record("b", "design", "FAIL", 0.30),
            _record("c", "design", "PASS", 0.80),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "CONVERGED_PASS"
        assert dc.confidence == "LOWER"

    def test_two_three_fail(self):
        """2/3 FAIL → CONVERGED_FAIL, LOWER confidence."""
        records = [
            _record("a", "design", "FAIL", 0.20),
            _record("b", "design", "PASS", 0.70),
            _record("c", "design", "FAIL", 0.25),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "CONVERGED_FAIL"
        assert dc.confidence == "LOWER"

    def test_fully_split_divergent(self):
        """1 PASS, 1 FAIL, 1 ABSTAIN (active: 1/1 each) → DIVERGENT."""
        records = [
            _record("a", "design", "PASS", 0.85),
            _record("b", "design", "FAIL", 0.30),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "DIVERGENT"
        assert dc.confidence is None

    def test_all_abstain_skipped(self):
        """All ABSTAIN → SKIPPED."""
        records = [
            _record("a", "design", "ABSTAIN"),
            _record("b", "design", "ABSTAIN"),
            _record("c", "design", "ABSTAIN"),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "SKIPPED"

    def test_two_pass_one_abstain(self):
        """2 PASS + 1 ABSTAIN → CONVERGED_PASS (abstains excluded from count)."""
        records = [
            _record("a", "design", "PASS", 0.85),
            _record("b", "design", "PASS", 0.82),
            _record("c", "design", "ABSTAIN"),
        ]
        dc = compute_dimension_convergence("design", records)
        assert dc.outcome == "CONVERGED_PASS"
        assert dc.confidence == "HIGH"  # 2/2 active agree


# ═══════════════════════════════════════════════════════════
# Run-Level Convergence Tests
# ═══════════════════════════════════════════════════════════


class TestRunConvergence:
    def test_all_converged_pass(self):
        """All dimensions CONVERGED_PASS → no escalation."""
        dims = [
            compute_dimension_convergence("design", [
                _record("a", "design", "PASS"), _record("b", "design", "PASS"), _record("c", "design", "PASS"),
            ]),
            compute_dimension_convergence("code", [
                _record("a", "code", "PASS"), _record("b", "code", "PASS"), _record("c", "code", "PASS"),
            ]),
        ]
        summary = compute_run_convergence(dims, ["a", "b", "c"], rubric_version="v1.0.0")
        assert summary.total_dimensions == 2
        assert summary.converged_pass == 2
        assert summary.divergent == 0
        assert summary.escalation_required is False
        assert summary.rubric_version == "v1.0.0"

    def test_one_divergent_triggers_escalation(self):
        """One DIVERGENT dimension → escalation required."""
        dims = [
            compute_dimension_convergence("design", [
                _record("a", "design", "PASS"), _record("b", "design", "PASS"), _record("c", "design", "PASS"),
            ]),
            compute_dimension_convergence("code", [
                _record("a", "code", "PASS"), _record("b", "code", "FAIL"),
            ]),
        ]
        summary = compute_run_convergence(dims, ["a", "b", "c"])
        assert summary.divergent == 1
        assert summary.escalation_required is True

    def test_empty_dimensions(self):
        """No dimensions → no escalation."""
        summary = compute_run_convergence([], ["a", "b", "c"])
        assert summary.total_dimensions == 0
        assert summary.escalation_required is False

    def test_mixed_outcomes(self):
        """Mix of CONVERGED_PASS, CONVERGED_FAIL, DIVERGENT, SKIPPED."""
        dims = [
            compute_dimension_convergence("d1", [
                _record("a", "d1", "PASS"), _record("b", "d1", "PASS"), _record("c", "d1", "PASS"),
            ]),
            compute_dimension_convergence("d2", [
                _record("a", "d2", "FAIL"), _record("b", "d2", "FAIL"), _record("c", "d2", "FAIL"),
            ]),
            compute_dimension_convergence("d3", [
                _record("a", "d3", "PASS"), _record("b", "d3", "FAIL"),
            ]),
            compute_dimension_convergence("d4", [
                _record("a", "d4", "ABSTAIN"), _record("b", "d4", "ABSTAIN"), _record("c", "d4", "ABSTAIN"),
            ]),
        ]
        summary = compute_run_convergence(dims, ["a", "b", "c"])
        assert summary.converged_pass == 1
        assert summary.converged_fail == 1
        assert summary.divergent == 1
        assert summary.skipped == 1
        assert summary.escalation_required is True


# ═══════════════════════════════════════════════════════════
# Persistence Payload Tests
# ═══════════════════════════════════════════════════════════


class TestPersistencePayload:
    def test_builds_complete_payload(self):
        """Persistence payload has all required keys."""
        records = [
            _record("a", "design", "PASS", 0.85),
            _record("b", "design", "PASS", 0.82),
        ]
        dim = compute_dimension_convergence("design", records)
        summary = compute_run_convergence([dim], ["a", "b"], rubric_version="v1.0.0")
        payload = build_orchestration_persistence(records, summary)

        assert "evaluator_scores" in payload
        assert "dimension_convergence" in payload
        assert "run_convergence_summary" in payload
        assert "rubric_version" in payload
        assert "escalation_required" in payload

        assert len(payload["evaluator_scores"]) == 2
        assert payload["rubric_version"] == "v1.0.0"
        assert payload["escalation_required"] is False

    def test_payload_score_fields(self):
        """Each evaluator score entry has expected fields."""
        records = [_record("a", "design", "PASS", 0.85)]
        dim = compute_dimension_convergence("design", records)
        summary = compute_run_convergence([dim], ["a"])
        payload = build_orchestration_persistence(records, summary)

        score_entry = payload["evaluator_scores"][0]
        assert score_entry["evaluator_id"] == "a"
        assert score_entry["dimension"] == "design"
        assert score_entry["verdict"] == "PASS"
        assert score_entry["score"] == 0.85
