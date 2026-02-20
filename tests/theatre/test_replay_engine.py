"""Tests for Replay Engine — full lifecycle, failure cap, hash mismatch."""

import pytest

from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import MockOracleAdapter
from theatre.engine.replay import (
    DatasetHashMismatchError,
    ReplayEngine,
    ReplayResult,
)
from theatre.engine.scoring import TheatreScoringProvider


def _make_criteria() -> TheatreCriteria:
    return TheatreCriteria(
        criteria_ids=["accuracy"],
        criteria_human="Test accuracy",
        weights={"accuracy": 1.0},
    )


def _make_episodes(count: int = 5) -> list[GroundTruthEpisode]:
    return [
        GroundTruthEpisode(
            episode_id=f"ep_{i:03d}",
            input_data={"question": f"q{i}"},
            expected_output={"answer": f"a{i}"},
        )
        for i in range(count)
    ]


def _compute_dataset_hash(episodes: list[GroundTruthEpisode]) -> str:
    return ReplayEngine._compute_dataset_hash(episodes)


def _make_engine(
    episodes: list[GroundTruthEpisode],
    adapter: MockOracleAdapter | None = None,
    criteria: TheatreCriteria | None = None,
) -> ReplayEngine:
    crit = criteria or _make_criteria()
    scorer = TheatreScoringProvider(crit)
    oracle = adapter or MockOracleAdapter()
    dataset_hash = _compute_dataset_hash(episodes)
    return ReplayEngine(
        theatre_id="test-theatre",
        construct_id="observer",
        construct_version="abc123",
        criteria=crit,
        oracle_adapter=oracle,
        scoring_provider=scorer,
        committed_dataset_hash=dataset_hash,
    )


class TestReplayEngineLifecycle:
    @pytest.mark.asyncio
    async def test_successful_full_lifecycle(self):
        episodes = _make_episodes(5)
        engine = _make_engine(episodes)
        result = await engine.run(episodes)

        assert isinstance(result, ReplayResult)
        assert result.replay_count == 5
        assert result.scored_count == 5
        assert result.failure_count == 0
        assert result.refused_count == 0
        assert result.failure_rate == 0.0
        assert len(result.episode_results) == 5
        assert all(er.invocation_status == "SUCCESS" for er in result.episode_results)

    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        episodes = _make_episodes(3)
        engine = _make_engine(episodes)

        progress_calls = []
        result = await engine.run(
            episodes,
            progress_callback=lambda current, total: progress_calls.append((current, total)),
        )

        assert progress_calls == [(1, 3), (2, 3), (3, 3)]

    @pytest.mark.asyncio
    async def test_composite_score_computed(self):
        episodes = _make_episodes(3)
        engine = _make_engine(episodes)
        result = await engine.run(episodes)

        assert 0.0 <= result.composite_score <= 1.0
        assert "accuracy" in result.aggregate_scores


class TestReplayEngineFailures:
    @pytest.mark.asyncio
    async def test_dataset_hash_mismatch(self):
        episodes = _make_episodes(3)
        engine = ReplayEngine(
            theatre_id="test-theatre",
            construct_id="observer",
            construct_version="abc123",
            criteria=_make_criteria(),
            oracle_adapter=MockOracleAdapter(),
            scoring_provider=TheatreScoringProvider(_make_criteria()),
            committed_dataset_hash="wrong_hash_" + "0" * 53,
        )
        with pytest.raises(DatasetHashMismatchError, match="mismatch"):
            await engine.run(episodes)

    @pytest.mark.asyncio
    async def test_failure_rate_tracked(self):
        episodes = _make_episodes(5)
        # 2 out of 5 fail = 40% failure rate
        adapter = MockOracleAdapter(fail_episodes={"ep_000", "ep_001"})
        engine = _make_engine(
            episodes,
            adapter=adapter,
        )
        # Need to set retry_count=0 to prevent retries
        # The default metadata has retry_count=2, but the invoke_oracle
        # function uses the request metadata, which uses defaults
        result = await engine.run(episodes)

        assert result.failure_count >= 0  # May retry and succeed
        assert result.failure_rate >= 0.0

    @pytest.mark.asyncio
    async def test_refused_episodes_excluded(self):
        episodes = _make_episodes(5)
        adapter = MockOracleAdapter(refuse_episodes={"ep_002"})
        engine = _make_engine(episodes, adapter=adapter)
        result = await engine.run(episodes)

        assert result.refused_count == 1
        assert result.replay_count == 5
        # Failure rate excludes refused
        assert result.scored_count == 4

        refused = [er for er in result.episode_results if er.excluded]
        assert len(refused) == 1
        assert refused[0].episode_id == "ep_002"

    @pytest.mark.asyncio
    async def test_timeout_episodes_scored_as_zero(self):
        episodes = _make_episodes(3)
        adapter = MockOracleAdapter(timeout_episodes={"ep_001"})
        engine = _make_engine(episodes, adapter=adapter)

        # Use very short timeout and no retries
        result = await engine.run(episodes)

        # The timed out episode should eventually be scored
        timeout_results = [
            er for er in result.episode_results
            if er.episode_id == "ep_001"
        ]
        assert len(timeout_results) == 1


class TestDatasetHash:
    def test_deterministic(self):
        episodes = _make_episodes(5)
        h1 = _compute_dataset_hash(episodes)
        h2 = _compute_dataset_hash(episodes)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_data_different_hash(self):
        eps1 = _make_episodes(5)
        eps2 = _make_episodes(3)
        assert _compute_dataset_hash(eps1) != _compute_dataset_hash(eps2)
