"""Tests for Theatre Scoring Provider — weighted composite, fallback, edge cases."""

import pytest

from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import OracleInvocationResponse
from theatre.engine.scoring import SimpleScoringFunction, TheatreScoringProvider


def _make_criteria(**overrides) -> TheatreCriteria:
    defaults = {
        "criteria_ids": ["accuracy", "completeness"],
        "criteria_human": "Test criteria",
        "weights": {"accuracy": 0.6, "completeness": 0.4},
    }
    defaults.update(overrides)
    return TheatreCriteria(**defaults)


def _make_episode(episode_id: str = "ep1", **overrides) -> GroundTruthEpisode:
    defaults = {
        "episode_id": episode_id,
        "input_data": {"question": "What colour is the sky?"},
        "expected_output": {"answer": "blue"},
    }
    defaults.update(overrides)
    return GroundTruthEpisode(**defaults)


def _make_response(
    status: str = "SUCCESS", output_data: dict | None = None
) -> OracleInvocationResponse:
    return OracleInvocationResponse(
        invocation_id="inv1",
        construct_id="observer",
        construct_version="abc123",
        output_data=output_data if output_data is not None else {"answer": "blue"},
        latency_ms=50,
        status=status,
    )


class TestTheatreScoringProvider:
    @pytest.mark.asyncio
    async def test_score_episode_success(self):
        criteria = _make_criteria()
        scorer = TheatreScoringProvider(criteria)
        episode = _make_episode()
        response = _make_response(output_data={"answer": "blue"})

        scores = await scorer.score_episode(episode, response)
        assert set(scores.keys()) == {"accuracy", "completeness"}
        assert all(0.0 <= v <= 1.0 for v in scores.values())

    @pytest.mark.asyncio
    async def test_score_episode_no_output(self):
        criteria = _make_criteria()
        scorer = TheatreScoringProvider(criteria)
        episode = _make_episode()
        response = _make_response(status="TIMEOUT")
        response.output_data = None

        scores = await scorer.score_episode(episode, response)
        assert scores == {"accuracy": 0.0, "completeness": 0.0}

    def test_compute_composite_weighted(self):
        criteria = _make_criteria(
            weights={"accuracy": 0.7, "completeness": 0.3}
        )
        scorer = TheatreScoringProvider(criteria)

        scores = {"accuracy": 0.8, "completeness": 0.6}
        composite = scorer.compute_composite(scores)
        assert abs(composite - (0.7 * 0.8 + 0.3 * 0.6)) < 1e-9

    def test_compute_composite_equal_weight_fallback(self):
        criteria = _make_criteria(weights={})
        scorer = TheatreScoringProvider(criteria)

        scores = {"accuracy": 0.8, "completeness": 0.6}
        composite = scorer.compute_composite(scores)
        assert abs(composite - 0.7) < 1e-9  # (0.8 + 0.6) / 2

    def test_compute_composite_missing_criterion(self):
        criteria = _make_criteria()
        scorer = TheatreScoringProvider(criteria)

        # Only one score provided — missing gets 0.0
        scores = {"accuracy": 0.8}
        composite = scorer.compute_composite(scores)
        assert abs(composite - (0.6 * 0.8 + 0.4 * 0.0)) < 1e-9

    def test_compute_composite_empty_scores(self):
        criteria = _make_criteria(weights={})
        scorer = TheatreScoringProvider(criteria)
        assert scorer.compute_composite({}) == 0.0

    @pytest.mark.asyncio
    async def test_scores_clamped_to_01(self):
        """Scores are clamped to [0.0, 1.0] range."""

        class OverScorer:
            async def score(self, criteria_id, ground_truth, oracle_output):
                return 1.5  # Exceeds range

        criteria = _make_criteria()
        scorer = TheatreScoringProvider(criteria, scorer=OverScorer())
        episode = _make_episode()
        response = _make_response()

        scores = await scorer.score_episode(episode, response)
        assert all(v <= 1.0 for v in scores.values())


class TestSimpleScoringFunction:
    @pytest.mark.asyncio
    async def test_exact_match(self):
        scorer = SimpleScoringFunction()
        score = await scorer.score(
            "accuracy",
            {"expected_output": {"answer": "blue"}},
            {"answer": "blue"},
        )
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_no_match(self):
        scorer = SimpleScoringFunction()
        score = await scorer.score(
            "accuracy",
            {"expected_output": {"answer": "blue"}},
            {"answer": "red"},
        )
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_partial_match(self):
        scorer = SimpleScoringFunction()
        score = await scorer.score(
            "accuracy",
            {"expected_output": {"a": 1, "b": 2}},
            {"a": 1, "b": 99},
        )
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_no_expected_output(self):
        scorer = SimpleScoringFunction()
        score = await scorer.score(
            "accuracy",
            {"expected_output": {}},
            {"answer": "blue"},
        )
        assert score == 0.5  # Neutral when no expected output
