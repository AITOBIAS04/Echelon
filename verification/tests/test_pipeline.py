"""E2E and integration tests for the verification pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from echelon_verify.certificate.generator import CertificateGenerator
from echelon_verify.config import (
    IngestionConfig,
    OracleConfig,
    PipelineConfig,
    ScoringConfig,
)
from echelon_verify.models import (
    CalibrationCertificate,
    GroundTruthRecord,
    OracleOutput,
)
from echelon_verify.pipeline import VerificationPipeline
from echelon_verify.storage import Storage


def _make_ground_truth(pr_id: str) -> GroundTruthRecord:
    return GroundTruthRecord(
        id=pr_id,
        title=f"PR {pr_id}",
        description=f"Description for {pr_id}",
        diff_content=f"--- a/file.py\n+++ b/file.py\n+added line {pr_id}",
        files_changed=["file.py"],
        timestamp=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        labels=["test"],
        author="tester",
        url=f"https://github.com/test/repo/pull/{pr_id}",
        repo="test/repo",
    )


def _make_oracle_output(gt_id: str) -> OracleOutput:
    return OracleOutput(
        ground_truth_id=gt_id,
        summary=f"Summary of {gt_id}",
        key_claims=[f"Claim about {gt_id}"],
        follow_up_question="What changed?",
        follow_up_response="A line was added.",
        metadata={},
        invoked_at=datetime(2026, 2, 15, 11, 0, 0, tzinfo=timezone.utc),
        latency_ms=100,
    )


def _mock_scorer() -> AsyncMock:
    scorer = AsyncMock()
    scorer.generate_follow_up_question.return_value = "What changed in this PR?"
    scorer.score_precision.return_value = (0.9, 1, 1, {"precision": 0.9})
    scorer.score_recall.return_value = (0.8, 2, 2, {"recall": 0.8})
    scorer.score_reply_accuracy.return_value = (0.85, {"accuracy": 0.85})
    return scorer


def _mock_oracle() -> AsyncMock:
    oracle = AsyncMock()

    async def invoke(gt: GroundTruthRecord, question: str) -> OracleOutput:
        return _make_oracle_output(gt.id)

    oracle.invoke.side_effect = invoke
    return oracle


def _make_config(output_dir: str) -> PipelineConfig:
    return PipelineConfig(
        ingestion=IngestionConfig(repo_url="https://github.com/test/repo"),
        oracle=OracleConfig(type="http", url="http://oracle.test/api"),
        scoring=ScoringConfig(api_key="test-key"),
        min_replays=2,
        output_dir=output_dir,
        construct_id="test-oracle",
    )


@pytest.mark.asyncio
async def test_e2e_pipeline_generates_certificate(tmp_path):
    """Full E2E: 3 mock PRs → oracle → scoring → certificate."""
    config = _make_config(str(tmp_path))
    oracle = _mock_oracle()
    scorer = _mock_scorer()
    storage = Storage(str(tmp_path))

    # Pre-populate ground truth
    repo_key = "test/repo"
    gt_path = storage.repo_dir(repo_key) / "ground_truth.jsonl"
    records = [_make_ground_truth(f"pr-{i}") for i in range(3)]
    for r in records:
        storage.append_jsonl(gt_path, r)

    pipeline = VerificationPipeline(config, oracle, scorer, storage)
    cert = await pipeline.score_only()

    assert isinstance(cert, CalibrationCertificate)
    assert cert.replay_count == 3
    assert 0.0 <= cert.precision <= 1.0
    assert 0.0 <= cert.recall <= 1.0
    assert 0.0 <= cert.reply_accuracy <= 1.0
    assert 0.0 <= cert.brier <= 0.5


@pytest.mark.asyncio
async def test_e2e_certificate_scores(tmp_path):
    """Verify certificate computes correct aggregate scores from mock data."""
    config = _make_config(str(tmp_path))
    oracle = _mock_oracle()
    scorer = _mock_scorer()
    storage = Storage(str(tmp_path))

    repo_key = "test/repo"
    gt_path = storage.repo_dir(repo_key) / "ground_truth.jsonl"
    records = [_make_ground_truth(f"pr-{i}") for i in range(3)]
    for r in records:
        storage.append_jsonl(gt_path, r)

    pipeline = VerificationPipeline(config, oracle, scorer, storage)
    cert = await pipeline.score_only()

    # All scores should be the mock values since all replays succeed
    assert abs(cert.precision - 0.9) < 1e-4
    assert abs(cert.recall - 0.8) < 1e-4
    assert abs(cert.reply_accuracy - 0.85) < 1e-4

    expected_composite = (0.9 + 0.8 + 0.85) / 3.0
    assert abs(cert.composite_score - expected_composite) < 1e-4


@pytest.mark.asyncio
async def test_partial_failure_still_certifies(tmp_path):
    """When 1 of 3 PRs fails, certificate is generated with 2 replays."""
    config = _make_config(str(tmp_path))
    storage = Storage(str(tmp_path))

    # Oracle that fails on pr-1
    oracle = AsyncMock()
    call_count = 0

    async def failing_invoke(gt: GroundTruthRecord, question: str) -> OracleOutput:
        nonlocal call_count
        call_count += 1
        if gt.id == "pr-1":
            raise RuntimeError("Oracle timeout")
        return _make_oracle_output(gt.id)

    oracle.invoke.side_effect = failing_invoke

    # Scorer that fails if oracle failed (score_single will catch it)
    scorer = _mock_scorer()

    repo_key = "test/repo"
    gt_path = storage.repo_dir(repo_key) / "ground_truth.jsonl"
    records = [_make_ground_truth(f"pr-{i}") for i in range(3)]
    for r in records:
        storage.append_jsonl(gt_path, r)

    pipeline = VerificationPipeline(config, oracle, scorer, storage)
    cert = await pipeline.score_only()

    assert cert.replay_count == 2  # 1 of 3 failed


@pytest.mark.asyncio
async def test_progress_callback_called(tmp_path):
    """Progress callback receives (completed, total) updates."""
    config = _make_config(str(tmp_path))
    oracle = _mock_oracle()
    scorer = _mock_scorer()
    storage = Storage(str(tmp_path))

    repo_key = "test/repo"
    gt_path = storage.repo_dir(repo_key) / "ground_truth.jsonl"
    records = [_make_ground_truth(f"pr-{i}") for i in range(2)]
    for r in records:
        storage.append_jsonl(gt_path, r)

    progress_calls: list[tuple[int, int]] = []

    def track_progress(completed: int, total: int) -> None:
        progress_calls.append((completed, total))

    pipeline = VerificationPipeline(config, oracle, scorer, storage)
    await pipeline.score_only(progress=track_progress)

    assert progress_calls == [(1, 2), (2, 2)]


@pytest.mark.asyncio
async def test_no_cached_data_raises(tmp_path):
    """score_only() raises when no cached ground truth exists."""
    config = _make_config(str(tmp_path))
    oracle = _mock_oracle()
    scorer = _mock_scorer()
    storage = Storage(str(tmp_path))

    pipeline = VerificationPipeline(config, oracle, scorer, storage)

    with pytest.raises(ValueError, match="No cached ground truth"):
        await pipeline.score_only()
