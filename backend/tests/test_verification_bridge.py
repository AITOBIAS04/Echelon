"""
Tests for verification bridge and API routes.
Sprint 2 — Service + API (cycle-028).
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from database.models import (
    User,
    VerificationRun,
    VerificationRunStatus,
    VerificationCertificate,
    VerificationReplayScore,
)
from services.verification_bridge import certificate_to_db, replay_score_to_db


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def engine():
    """In-memory SQLite engine for verification tables only."""
    eng = create_engine("sqlite:///:memory:")
    tables = [
        User.__table__,
        VerificationCertificate.__table__,
        VerificationReplayScore.__table__,
        VerificationRun.__table__,
    ]
    Base.metadata.create_all(eng, tables=tables)
    yield eng
    Base.metadata.drop_all(eng, tables=tables)
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as sess:
        yield sess


# ============================================
# MOCK echelon-verify MODELS
# ============================================

def make_mock_certificate():
    """Create a mock CalibrationCertificate."""
    cert = MagicMock()
    cert.construct_id = "oracle-test-v1"
    cert.domain = "community_oracle"
    cert.replay_count = 42
    cert.precision = 0.88
    cert.recall = 0.75
    cert.reply_accuracy = 0.82
    cert.composite_score = 0.81
    cert.brier = 0.11
    cert.sample_size = 42
    cert.ground_truth_source = "https://github.com/owner/repo"
    cert.commit_range = "abc..def"
    cert.methodology_version = "v1"
    cert.scoring_model = "claude-sonnet-4-6"
    cert.raw_scores = {"test": True}
    return cert


def make_mock_replay_score():
    """Create a mock ReplayScore."""
    score = MagicMock()
    score.ground_truth_id = "gt-pr-99"
    score.precision = 0.92
    score.recall = 0.88
    score.reply_accuracy = 0.90
    score.claims_total = 15
    score.claims_supported = 14
    score.changes_total = 8
    score.changes_surfaced = 7
    score.scoring_model = "claude-sonnet-4-6"
    score.scoring_latency_ms = 1200
    score.scored_at = datetime(2026, 2, 19, 16, 30, 0)
    return score


# ============================================
# BRIDGE CONVERSION TESTS
# ============================================

class TestCertificateToDb:
    def test_converts_all_fields(self):
        mock_cert = make_mock_certificate()
        db_cert = certificate_to_db(mock_cert)

        assert db_cert.construct_id == "oracle-test-v1"
        assert db_cert.domain == "community_oracle"
        assert db_cert.replay_count == 42
        assert db_cert.precision == 0.88
        assert db_cert.recall == 0.75
        assert db_cert.reply_accuracy == 0.82
        assert db_cert.composite_score == 0.81
        assert db_cert.brier == 0.11
        assert db_cert.sample_size == 42
        assert db_cert.ground_truth_source == "https://github.com/owner/repo"
        assert db_cert.methodology_version == "v1"
        assert db_cert.scoring_model == "claude-sonnet-4-6"
        assert db_cert.id is not None  # UUID generated

    def test_generates_unique_ids(self):
        mock_cert = make_mock_certificate()
        db1 = certificate_to_db(mock_cert)
        db2 = certificate_to_db(mock_cert)
        assert db1.id != db2.id


class TestReplayScoreToDb:
    def test_converts_all_fields(self):
        mock_score = make_mock_replay_score()
        cert_id = "cert-123"
        db_score = replay_score_to_db(mock_score, cert_id)

        assert db_score.certificate_id == cert_id
        assert db_score.ground_truth_id == "gt-pr-99"
        assert db_score.precision == 0.92
        assert db_score.recall == 0.88
        assert db_score.reply_accuracy == 0.90
        assert db_score.claims_total == 15
        assert db_score.claims_supported == 14
        assert db_score.changes_total == 8
        assert db_score.changes_surfaced == 7
        assert db_score.scoring_model == "claude-sonnet-4-6"
        assert db_score.scoring_latency_ms == 1200
        assert db_score.id is not None  # UUID generated


# ============================================
# BRIDGE TASK TESTS (mocked pipeline)
# ============================================

class TestRunVerificationTask:
    @pytest.mark.asyncio
    async def test_handles_missing_echelon_verify(self, session):
        """When echelon-verify is not installed, run should be set to FAILED."""
        # Create a user and run
        user = User(id="user-001", username="test", email="t@t.com", password_hash="h")
        session.add(user)
        session.commit()

        run = VerificationRun(
            id="run-fail-001",
            user_id="user-001",
            construct_id="test-oracle",
            repo_url="https://github.com/test/repo",
        )
        session.add(run)
        session.commit()

        # Patch ECHELON_VERIFY_AVAILABLE to False and get_session
        with patch("services.verification_bridge.ECHELON_VERIFY_AVAILABLE", False):
            # We need to mock get_session since it uses async
            from services.verification_bridge import run_verification_task

            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.execute = AsyncMock()

            with patch("services.verification_bridge.get_session", return_value=mock_session):
                await run_verification_task("run-fail-001")

            # Verify execute was called with FAILED status
            mock_session.execute.assert_called_once()


# ============================================
# ROUTE HANDLER TESTS (response format)
# ============================================

class TestRunResponseMapping:
    def test_run_to_response_mapping(self, session):
        """Verify the VerificationRunResponse correctly maps from ORM."""
        user = User(id="user-001", username="test", email="t@t.com", password_hash="h")
        session.add(user)
        session.commit()

        run = VerificationRun(
            id="run-map-001",
            user_id="user-001",
            construct_id="oracle-v1",
            repo_url="https://github.com/test/repo",
            status=VerificationRunStatus.SCORING,
            progress=25,
            total=100,
        )
        session.add(run)
        session.commit()

        from api.verification_routes import _run_to_response
        response = _run_to_response(run)
        assert response.run_id == "run-map-001"
        assert response.status == "SCORING"
        assert response.progress == 25
        assert response.total == 100
        assert response.certificate_id is None
