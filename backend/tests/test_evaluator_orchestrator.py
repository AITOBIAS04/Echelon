"""Tests for Cycle 037b Sprint 1 — Evaluator Orchestrator + Scorer Adapter.

Validates:
- ResidualScorer protocol compliance
- Orchestrator concurrent execution of 3 scorers
- Output normalization (evaluator_id correction)
- Scorer failure → ABSTAIN fallback
- Grouping by dimension
- Empty dimension handling
"""

import asyncio

import pytest

from backend.schemas.evaluator_orchestration import EvaluatorScoreRecord
from backend.services.evaluator_orchestrator import (
    EvaluatorOrchestrator,
    ResidualScorer,
)
from backend.services.residual_dimension_filter import ResidualDimension


# ═══════════════════════════════════════════════════════════
# Test Scorer Implementations
# ═══════════════════════════════════════════════════════════


class MockScorer:
    """A mock scorer that returns deterministic results."""

    def __init__(self, evaluator_id: str, verdict: str = "PASS", score: float = 0.85):
        self._evaluator_id = evaluator_id
        self._verdict = verdict
        self._score = score

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(
        self,
        *,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        return [
            EvaluatorScoreRecord(
                evaluator_id=self._evaluator_id,
                dimension=dim.dimension,
                verdict=self._verdict,
                score=self._score,
                rationale=f"{self._evaluator_id} scored {dim.dimension}",
            )
            for dim in dimensions
        ]


class FailingScorer:
    """A scorer that raises an exception."""

    def __init__(self, evaluator_id: str):
        self._evaluator_id = evaluator_id

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(
        self,
        *,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        raise RuntimeError(f"{self._evaluator_id} connection timeout")


class MismatchedIdScorer:
    """A scorer that returns records with wrong evaluator_id."""

    def __init__(self, evaluator_id: str, wrong_id: str):
        self._evaluator_id = evaluator_id
        self._wrong_id = wrong_id

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(
        self,
        *,
        dimensions: list[ResidualDimension],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        return [
            EvaluatorScoreRecord(
                evaluator_id=self._wrong_id,
                dimension=dim.dimension,
                verdict="PASS",
                score=0.80,
            )
            for dim in dimensions
        ]


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════


def _dim(name: str, critical: bool = True) -> ResidualDimension:
    return ResidualDimension(
        dimension=name,
        source_check_id=f"rubric:test:{name}",
        source_check_type="RUBRIC",
        critical=critical,
    )


DESIGN_DIM = _dim("design_systems")
CODE_DIM = _dim("code_generation")
TWO_DIMS = [DESIGN_DIM, CODE_DIM]
EPISODE = {"construct_slug": "test-construct", "version": "1.0.0"}


# ═══════════════════════════════════════════════════════════
# Protocol Compliance
# ═══════════════════════════════════════════════════════════


class TestResidualScorerProtocol:
    def test_mock_scorer_satisfies_protocol(self):
        """MockScorer should be recognized as a ResidualScorer."""
        scorer = MockScorer("gpt-4o")
        assert isinstance(scorer, ResidualScorer)

    def test_failing_scorer_satisfies_protocol(self):
        scorer = FailingScorer("broken")
        assert isinstance(scorer, ResidualScorer)


# ═══════════════════════════════════════════════════════════
# Orchestrator Tests
# ═══════════════════════════════════════════════════════════


class TestEvaluatorOrchestrator:
    def test_requires_at_least_one_scorer(self):
        with pytest.raises(ValueError, match="At least one scorer"):
            EvaluatorOrchestrator(scorers=[])

    def test_evaluator_ids(self):
        orch = EvaluatorOrchestrator(scorers=[
            MockScorer("gpt-4o"),
            MockScorer("opus-4"),
            MockScorer("sonnet-4"),
        ])
        assert orch.evaluator_ids == ["gpt-4o", "opus-4", "sonnet-4"]

    @pytest.mark.asyncio
    async def test_three_scorers_two_dimensions(self):
        """3 scorers × 2 dimensions = 6 records."""
        scorers = [
            MockScorer("gpt-4o", "PASS", 0.85),
            MockScorer("opus-4", "PASS", 0.82),
            MockScorer("sonnet-4", "PASS", 0.88),
        ]
        orch = EvaluatorOrchestrator(scorers=scorers)
        records = await orch.execute(dimensions=TWO_DIMS, episode_payload=EPISODE)

        assert len(records) == 6
        # Each scorer should produce exactly 2 records
        for sid in ["gpt-4o", "opus-4", "sonnet-4"]:
            scorer_records = [r for r in records if r.evaluator_id == sid]
            assert len(scorer_records) == 2

    @pytest.mark.asyncio
    async def test_empty_dimensions_returns_empty(self):
        """No dimensions → no scoring, empty result."""
        orch = EvaluatorOrchestrator(scorers=[MockScorer("gpt-4o")])
        records = await orch.execute(dimensions=[], episode_payload=EPISODE)
        assert records == []

    @pytest.mark.asyncio
    async def test_scorer_failure_produces_abstain(self):
        """A failing scorer should produce ABSTAIN records, not crash orchestration."""
        scorers = [
            MockScorer("gpt-4o", "PASS", 0.85),
            FailingScorer("broken-scorer"),
            MockScorer("sonnet-4", "PASS", 0.88),
        ]
        orch = EvaluatorOrchestrator(scorers=scorers)
        records = await orch.execute(dimensions=TWO_DIMS, episode_payload=EPISODE)

        # 2 good scorers × 2 dims + 1 failed × 2 abstains = 6
        assert len(records) == 6

        abstains = [r for r in records if r.evaluator_id == "broken-scorer"]
        assert len(abstains) == 2
        for a in abstains:
            assert a.verdict == "ABSTAIN"
            assert "RuntimeError" in a.rationale

    @pytest.mark.asyncio
    async def test_evaluator_id_normalization(self):
        """Scorer returning wrong evaluator_id should be corrected."""
        scorers = [
            MismatchedIdScorer("correct-id", "wrong-id"),
        ]
        orch = EvaluatorOrchestrator(scorers=scorers)
        records = await orch.execute(dimensions=[DESIGN_DIM], episode_payload=EPISODE)

        assert len(records) == 1
        assert records[0].evaluator_id == "correct-id"

    @pytest.mark.asyncio
    async def test_mixed_verdicts(self):
        """Scorers can return different verdicts for the same dimension."""
        scorers = [
            MockScorer("gpt-4o", "PASS", 0.85),
            MockScorer("opus-4", "FAIL", 0.30),
            MockScorer("sonnet-4", "PASS", 0.80),
        ]
        orch = EvaluatorOrchestrator(scorers=scorers)
        records = await orch.execute(dimensions=[DESIGN_DIM], episode_payload=EPISODE)

        verdicts = {r.evaluator_id: r.verdict for r in records}
        assert verdicts == {"gpt-4o": "PASS", "opus-4": "FAIL", "sonnet-4": "PASS"}

    @pytest.mark.asyncio
    async def test_group_by_dimension(self):
        """group_by_dimension should partition records correctly."""
        scorers = [
            MockScorer("gpt-4o"),
            MockScorer("opus-4"),
        ]
        orch = EvaluatorOrchestrator(scorers=scorers)
        records = await orch.execute(dimensions=TWO_DIMS, episode_payload=EPISODE)
        grouped = orch.group_by_dimension(records)

        assert set(grouped.keys()) == {"design_systems", "code_generation"}
        assert len(grouped["design_systems"]) == 2
        assert len(grouped["code_generation"]) == 2

    @pytest.mark.asyncio
    async def test_single_scorer_single_dimension(self):
        """Minimum viable orchestration: 1 scorer, 1 dimension."""
        orch = EvaluatorOrchestrator(scorers=[MockScorer("solo", "PASS", 0.90)])
        records = await orch.execute(dimensions=[DESIGN_DIM], episode_payload=EPISODE)

        assert len(records) == 1
        assert records[0].evaluator_id == "solo"
        assert records[0].dimension == "design_systems"
        assert records[0].verdict == "PASS"
        assert records[0].score == 0.90
