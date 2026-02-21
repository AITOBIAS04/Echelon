"""
Tests for verification SQLAlchemy models and Pydantic schemas.
Sprint 1 — Data Layer (cycle-028).
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from database.models import (
    User,
    VerificationRun,
    VerificationCertificate,
    VerificationReplayScore,
    VerificationRunStatus,
)
from schemas.verification import (
    VerificationRunCreate,
    VerificationRunResponse,
    CertificateResponse,
    ReplayScoreResponse,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def engine():
    """In-memory SQLite engine for verification tables only.

    We only create the subset of tables that don't use PostgreSQL-specific
    types (ARRAY). The users table is needed for FK, and the 3 verification
    tables are what we're testing.
    """
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
    """Sync session for testing model instantiation."""
    with Session(engine) as sess:
        yield sess


@pytest.fixture
def sample_user(session):
    """Create a test user."""
    user = User(
        id="user-001",
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def sample_certificate(session):
    """Create a test certificate."""
    cert = VerificationCertificate(
        id="cert-001",
        construct_id="oracle-v1",
        domain="community_oracle",
        replay_count=50,
        precision=0.85,
        recall=0.78,
        reply_accuracy=0.82,
        composite_score=0.80,
        brier=0.12,
        sample_size=50,
        ground_truth_source="https://github.com/owner/repo",
        commit_range="abc123..def456",
        methodology_version="v1",
        scoring_model="claude-sonnet-4-6",
    )
    session.add(cert)
    session.commit()
    return cert


# ============================================
# MODEL TESTS
# ============================================

class TestVerificationRunModel:
    def test_create_with_defaults(self, session, sample_user):
        run = VerificationRun(
            id="run-001",
            user_id="user-001",
            construct_id="oracle-v1",
            repo_url="https://github.com/owner/repo",
        )
        session.add(run)
        session.commit()

        fetched = session.get(VerificationRun, "run-001")
        assert fetched is not None
        assert fetched.status == VerificationRunStatus.PENDING
        assert fetched.progress == 0
        assert fetched.total == 0
        assert fetched.error is None
        assert fetched.certificate_id is None

    def test_all_status_values(self):
        assert len(VerificationRunStatus) == 7
        expected = {"PENDING", "INGESTING", "INVOKING", "SCORING", "CERTIFYING", "COMPLETED", "FAILED"}
        assert {s.value for s in VerificationRunStatus} == expected


class TestVerificationCertificateModel:
    def test_create(self, session, sample_certificate):
        fetched = session.get(VerificationCertificate, "cert-001")
        assert fetched is not None
        assert fetched.construct_id == "oracle-v1"
        assert fetched.brier == 0.12
        assert fetched.replay_count == 50
        assert fetched.domain == "community_oracle"


class TestVerificationReplayScoreModel:
    def test_create(self, session, sample_certificate):
        score = VerificationReplayScore(
            id="score-001",
            certificate_id="cert-001",
            ground_truth_id="gt-pr-42",
            precision=0.90,
            recall=0.85,
            reply_accuracy=0.88,
            claims_total=10,
            claims_supported=9,
            changes_total=5,
            changes_surfaced=4,
            scoring_model="claude-sonnet-4-6",
            scoring_latency_ms=1500,
            scored_at=datetime(2026, 2, 19, 16, 0, 0),
        )
        session.add(score)
        session.commit()

        fetched = session.get(VerificationReplayScore, "score-001")
        assert fetched is not None
        assert fetched.certificate_id == "cert-001"
        assert fetched.claims_supported == 9


class TestRelationships:
    def test_run_certificate_relationship(self, session, sample_user, sample_certificate):
        run = VerificationRun(
            id="run-002",
            user_id="user-001",
            construct_id="oracle-v1",
            repo_url="https://github.com/owner/repo",
            status=VerificationRunStatus.COMPLETED,
            certificate_id="cert-001",
        )
        session.add(run)
        session.commit()

        fetched = session.get(VerificationRun, "run-002")
        assert fetched.certificate is not None
        assert fetched.certificate.id == "cert-001"

    def test_certificate_replay_scores(self, session, sample_certificate):
        for i in range(3):
            score = VerificationReplayScore(
                id=f"score-{i}",
                certificate_id="cert-001",
                ground_truth_id=f"gt-{i}",
                precision=0.8,
                recall=0.7,
                reply_accuracy=0.75,
                claims_total=10,
                claims_supported=8,
                changes_total=5,
                changes_surfaced=4,
                scoring_model="claude-sonnet-4-6",
                scoring_latency_ms=1000,
                scored_at=datetime(2026, 2, 19, 16, 0, 0),
            )
            session.add(score)
        session.commit()

        cert = session.get(VerificationCertificate, "cert-001")
        assert len(cert.replay_scores) == 3


# ============================================
# SCHEMA TESTS
# ============================================

class TestVerificationRunCreateSchema:
    def test_valid_http_oracle(self):
        data = VerificationRunCreate(
            repo_url="https://github.com/owner/repo",
            construct_id="oracle-v1",
            oracle_type="http",
            oracle_url="https://oracle.example.com/predict",
        )
        assert data.repo_url == "https://github.com/owner/repo"
        assert data.limit == 100
        assert data.min_replays == 50

    def test_rejects_missing_repo_url(self):
        with pytest.raises(Exception):
            VerificationRunCreate(
                construct_id="oracle-v1",
                oracle_type="http",
                oracle_url="https://oracle.example.com/predict",
            )

    def test_rejects_http_without_oracle_url(self):
        with pytest.raises(ValueError, match="oracle_url is required"):
            VerificationRunCreate(
                repo_url="https://github.com/owner/repo",
                construct_id="oracle-v1",
                oracle_type="http",
            )

    def test_rejects_python_without_module(self):
        with pytest.raises(ValueError, match="oracle_module and oracle_callable"):
            VerificationRunCreate(
                repo_url="https://github.com/owner/repo",
                construct_id="oracle-v1",
                oracle_type="python",
            )

    def test_valid_python_oracle(self):
        data = VerificationRunCreate(
            repo_url="https://github.com/owner/repo",
            construct_id="oracle-v1",
            oracle_type="python",
            oracle_module="my_oracle",
            oracle_callable="predict",
        )
        assert data.oracle_module == "my_oracle"


class TestCertificateResponseSchema:
    def test_from_orm(self, session, sample_certificate):
        cert = session.get(VerificationCertificate, "cert-001")
        response = CertificateResponse.model_validate(cert)
        assert response.id == "cert-001"
        assert response.brier == 0.12
        assert response.construct_id == "oracle-v1"
        assert response.replay_scores == []
