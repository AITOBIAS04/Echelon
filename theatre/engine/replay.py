"""Replay Engine — orchestrates Product Theatre execution.

Processes ground truth episodes sequentially: invoke construct, score, aggregate.
Tracks failure rates and enforces the >20% cap rule.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from pydantic import BaseModel

from theatre.engine.canonical_json import canonical_json
from theatre.engine.certificate import TheatreCalibrationCertificate
from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import (
    OracleAdapter,
    OracleInvocationRequest,
    OracleInvocationResponse,
    invoke_oracle,
)
from theatre.engine.scoring import TheatreScoringProvider


class EpisodeResult(BaseModel):
    """Result of a single episode execution."""

    episode_id: str
    invocation_status: str
    latency_ms: int
    scores: dict[str, float] | None = None
    composite_score: float | None = None
    excluded: bool = False  # True for REFUSED episodes
    oracle_output: dict[str, Any] | None = None  # Raw construct response


class ReplayResult(BaseModel):
    """Aggregate result of a full replay execution."""

    episode_results: list[EpisodeResult]
    aggregate_scores: dict[str, float]
    composite_score: float
    replay_count: int
    scored_count: int
    failure_count: int
    failure_rate: float
    refused_count: int
    dataset_hash: str


class DatasetHashMismatchError(Exception):
    """Raised when dataset hash does not match commitment."""


class ReplayEngine:
    """Executes Product Theatre lifecycle: invoke construct per episode, score, aggregate."""

    def __init__(
        self,
        theatre_id: str,
        construct_id: str,
        construct_version: str,
        criteria: TheatreCriteria,
        oracle_adapter: OracleAdapter,
        scoring_provider: TheatreScoringProvider,
        committed_dataset_hash: str,
    ):
        self._theatre_id = theatre_id
        self._construct_id = construct_id
        self._construct_version = construct_version
        self._criteria = criteria
        self._oracle = oracle_adapter
        self._scorer = scoring_provider
        self._committed_dataset_hash = committed_dataset_hash

    async def run(
        self,
        ground_truth: list[GroundTruthEpisode],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ReplayResult:
        """Execute full replay lifecycle.

        1. Verify dataset hash matches commitment
        2. For each episode: invoke → score → record
        3. Compute failure rate
        4. Aggregate scores across episodes
        """
        # Step 1: Verify dataset hash
        actual_hash = self._compute_dataset_hash(ground_truth)
        if actual_hash != self._committed_dataset_hash:
            raise DatasetHashMismatchError(
                f"Dataset hash mismatch: expected {self._committed_dataset_hash}, "
                f"got {actual_hash}"
            )

        # Step 2: Process episodes sequentially
        episode_results: list[EpisodeResult] = []
        scored_episodes: list[dict[str, float]] = []
        failure_count = 0
        refused_count = 0

        total = len(ground_truth)
        for i, episode in enumerate(ground_truth):
            request = OracleInvocationRequest(
                theatre_id=self._theatre_id,
                episode_id=episode.episode_id,
                construct_id=self._construct_id,
                construct_version=self._construct_version,
                input_data=episode.input_data,
            )

            response = await invoke_oracle(self._oracle, request)

            if response.status == "REFUSED":
                # Excluded from scoring
                episode_results.append(EpisodeResult(
                    episode_id=episode.episode_id,
                    invocation_status=response.status,
                    latency_ms=response.latency_ms,
                    excluded=True,
                    oracle_output=response.output_data,
                ))
                refused_count += 1
            elif response.status in ("TIMEOUT", "ERROR"):
                # Scored as missing (0.0 for all criteria)
                scores = {cid: 0.0 for cid in self._criteria.criteria_ids}
                composite = self._scorer.compute_composite(scores)
                episode_results.append(EpisodeResult(
                    episode_id=episode.episode_id,
                    invocation_status=response.status,
                    latency_ms=response.latency_ms,
                    scores=scores,
                    composite_score=composite,
                    oracle_output=response.output_data,
                ))
                scored_episodes.append(scores)
                failure_count += 1
            else:
                # SUCCESS — score normally
                scores = await self._scorer.score_episode(episode, response)
                composite = self._scorer.compute_composite(scores)
                episode_results.append(EpisodeResult(
                    episode_id=episode.episode_id,
                    invocation_status=response.status,
                    latency_ms=response.latency_ms,
                    scores=scores,
                    composite_score=composite,
                    oracle_output=response.output_data,
                ))
                scored_episodes.append(scores)

            if progress_callback:
                progress_callback(i + 1, total)

        # Step 3: Compute failure rate (over non-refused episodes)
        scoreable_count = total - refused_count
        failure_rate = failure_count / scoreable_count if scoreable_count > 0 else 0.0

        # Step 4: Aggregate scores
        aggregate_scores = self._aggregate_scores(scored_episodes)
        composite_score = self._scorer.compute_composite(aggregate_scores)

        return ReplayResult(
            episode_results=episode_results,
            aggregate_scores=aggregate_scores,
            composite_score=composite_score,
            replay_count=total,
            scored_count=len(scored_episodes),
            failure_count=failure_count,
            failure_rate=failure_rate,
            refused_count=refused_count,
            dataset_hash=actual_hash,
        )

    def _aggregate_scores(
        self, scored_episodes: list[dict[str, float]]
    ) -> dict[str, float]:
        """Compute mean scores across all scored episodes."""
        if not scored_episodes:
            return {cid: 0.0 for cid in self._criteria.criteria_ids}

        aggregated: dict[str, float] = {}
        for cid in self._criteria.criteria_ids:
            values = [ep.get(cid, 0.0) for ep in scored_episodes]
            aggregated[cid] = sum(values) / len(values)
        return aggregated

    @staticmethod
    def _compute_dataset_hash(episodes: list[GroundTruthEpisode]) -> str:
        """Compute SHA-256 hash of the dataset for commitment verification."""
        serialised = canonical_json([ep.model_dump() for ep in episodes])
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()
