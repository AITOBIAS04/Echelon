"""Shared test fixtures for echelon-verify tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echelon_verify.models import (
    CalibrationCertificate,
    GroundTruthRecord,
    OracleOutput,
    ReplayScore,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def sample_ground_truth() -> GroundTruthRecord:
    return GroundTruthRecord(
        id="142",
        title="Add rate limiting to /api/users",
        description="Implements token bucket rate limiting for the users endpoint.",
        diff_content=(
            "--- a/src/routes/users.py\n"
            "+++ b/src/routes/users.py\n"
            "@@ -10,6 +10,15 @@\n"
            "+from utils.rate_limit import RateLimiter\n"
            "+\n"
            "+limiter = RateLimiter(max_requests=100, window_seconds=60)\n"
        ),
        files_changed=["src/routes/users.py", "src/utils/rate_limit.py"],
        timestamp=datetime(2026, 2, 15, 10, 30, 0, tzinfo=timezone.utc),
        labels=["enhancement", "api"],
        author="alice",
        url="https://github.com/echelon/app/pull/142",
        repo="echelon/app",
    )


@pytest.fixture
def sample_oracle_output() -> OracleOutput:
    return OracleOutput(
        ground_truth_id="142",
        summary="This PR adds rate limiting to the /api/users endpoint using a token bucket algorithm.",
        key_claims=[
            "Added rate limiting to /api/users",
            "Uses token bucket algorithm",
            "Max 100 requests per 60-second window",
        ],
        follow_up_question="What happens when the rate limit is exceeded?",
        follow_up_response="When the rate limit is exceeded, the endpoint returns a 429 status code.",
        metadata={"model": "gpt-4", "latency_ms": 320},
        invoked_at=datetime(2026, 2, 15, 11, 0, 0, tzinfo=timezone.utc),
        latency_ms=320,
    )


@pytest.fixture
def sample_replay_score() -> ReplayScore:
    return ReplayScore(
        ground_truth_id="142",
        precision=0.85,
        recall=0.90,
        reply_accuracy=0.75,
        claims_total=3,
        claims_supported=2,
        changes_total=2,
        changes_surfaced=2,
        scoring_model="claude-sonnet-4-6",
        scoring_latency_ms=1200,
        scored_at=datetime(2026, 2, 15, 11, 5, 0, tzinfo=timezone.utc),
        raw_scoring_output={"precision_detail": "2/3 claims supported"},
    )


@pytest.fixture
def sample_scores() -> list[ReplayScore]:
    """Multiple replay scores for certificate aggregation tests."""
    base = datetime(2026, 2, 15, 11, 0, 0, tzinfo=timezone.utc)
    return [
        ReplayScore(
            ground_truth_id=f"pr-{i}",
            precision=0.7 + i * 0.05,
            recall=0.6 + i * 0.08,
            reply_accuracy=0.8 + i * 0.03,
            claims_total=5,
            claims_supported=3 + i,
            changes_total=4,
            changes_surfaced=2 + i,
            scoring_model="claude-sonnet-4-6",
            scoring_latency_ms=1000 + i * 100,
            scored_at=base,
        )
        for i in range(5)
    ]


@pytest.fixture
def tmp_storage_dir(tmp_path: Path) -> Path:
    """Temporary directory for storage tests."""
    return tmp_path / "test_data"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    path = FIXTURES_DIR / name
    return json.loads(path.read_text())
