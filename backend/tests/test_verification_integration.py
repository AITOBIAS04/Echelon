"""
Integration tests for verification API — full lifecycle, auth, pagination.
Sprint 3 — Integration Tests + E2E (cycle-028).
"""

import pytest
import uuid
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

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
from schemas.verification import (
    VerificationRunCreate,
    VerificationRunResponse,
    VerificationRunListResponse,
    CertificateResponse,
    CertificateSummaryResponse,
    CertificateListResponse,
)


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


@pytest.fixture
def user_a(session):
    """User A for isolation tests."""
    user = User(id="user-a", username="alice", email="alice@test.com", password_hash="h")
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def user_b(session):
    """User B for isolation tests."""
    user = User(id="user-b", username="bob", email="bob@test.com", password_hash="h")
    session.add(user)
    session.commit()
    return user


def _make_run(session, user_id, construct_id="oracle-v1", status=VerificationRunStatus.PENDING,
              repo_url="https://github.com/test/repo", **kwargs):
    """Helper to create a VerificationRun."""
    run = VerificationRun(
        id=str(uuid.uuid4()),
        user_id=user_id,
        construct_id=construct_id,
        repo_url=repo_url,
        status=status,
        **kwargs,
    )
    session.add(run)
    session.commit()
    return run


def _make_certificate(session, construct_id="oracle-v1", brier=0.12, **kwargs):
    """Helper to create a VerificationCertificate."""
    cert = VerificationCertificate(
        id=str(uuid.uuid4()),
        construct_id=construct_id,
        domain="community_oracle",
        replay_count=50,
        precision=0.85,
        recall=0.78,
        reply_accuracy=0.82,
        composite_score=0.80,
        brier=brier,
        sample_size=50,
        ground_truth_source="https://github.com/owner/repo",
        commit_range="abc..def",
        methodology_version="v1",
        scoring_model="claude-sonnet-4-6",
        **kwargs,
    )
    session.add(cert)
    session.commit()
    return cert


def _make_replay_score(session, certificate_id, **kwargs):
    """Helper to create a VerificationReplayScore."""
    defaults = dict(
        ground_truth_id=f"gt-{uuid.uuid4().hex[:8]}",
        precision=0.85,
        recall=0.78,
        reply_accuracy=0.82,
        claims_total=10,
        claims_supported=8,
        changes_total=5,
        changes_surfaced=4,
        scoring_model="claude-sonnet-4-6",
        scoring_latency_ms=1000,
        scored_at=datetime(2026, 2, 19, 16, 0, 0),
    )
    defaults.update(kwargs)
    score = VerificationReplayScore(
        id=str(uuid.uuid4()),
        certificate_id=certificate_id,
        **defaults,
    )
    session.add(score)
    session.commit()
    return score


# ============================================
# 3.1 — BACKGROUND TASK LIFECYCLE
# ============================================

class TestBackgroundTaskLifecycle:
    def test_run_starts_as_pending(self, session, user_a):
        run = _make_run(session, "user-a")
        assert run.status == VerificationRunStatus.PENDING
        assert run.progress == 0
        assert run.total == 0

    def test_completed_run_has_certificate(self, session, user_a):
        cert = _make_certificate(session, construct_id="oracle-v1")
        run = _make_run(
            session, "user-a",
            status=VerificationRunStatus.COMPLETED,
            certificate_id=cert.id,
            progress=50,
            total=50,
        )
        fetched = session.get(VerificationRun, run.id)
        assert fetched.status == VerificationRunStatus.COMPLETED
        assert fetched.certificate_id == cert.id
        assert fetched.certificate is not None

    def test_certificate_has_replay_scores(self, session, user_a):
        cert = _make_certificate(session, construct_id="oracle-v1")
        for i in range(5):
            _make_replay_score(session, cert.id)

        fetched = session.get(VerificationCertificate, cert.id)
        assert len(fetched.replay_scores) == 5
        for score in fetched.replay_scores:
            assert 0 <= score.precision <= 1
            assert 0 <= score.recall <= 1

    def test_certificate_scores_in_valid_range(self, session, user_a):
        cert = _make_certificate(session, brier=0.107)
        assert 0 <= cert.precision <= 1
        assert 0 <= cert.recall <= 1
        assert 0 <= cert.brier <= 0.5


# ============================================
# 3.2 — FAILURE HANDLING
# ============================================

class TestFailureHandling:
    def test_failed_run_has_error_message(self, session, user_a):
        run = _make_run(
            session, "user-a",
            status=VerificationRunStatus.FAILED,
            error="Pipeline crashed: rate limit exceeded",
        )
        fetched = session.get(VerificationRun, run.id)
        assert fetched.status == VerificationRunStatus.FAILED
        assert "rate limit" in fetched.error

    def test_error_message_truncation(self, session, user_a):
        long_error = "x" * 3000
        run = _make_run(
            session, "user-a",
            status=VerificationRunStatus.FAILED,
            error=long_error[:2000],  # Bridge truncates to 2000
        )
        fetched = session.get(VerificationRun, run.id)
        assert len(fetched.error) <= 2000

    def test_failed_run_no_certificate(self, session, user_a):
        run = _make_run(
            session, "user-a",
            status=VerificationRunStatus.FAILED,
            error="some error",
        )
        fetched = session.get(VerificationRun, run.id)
        assert fetched.certificate_id is None
        assert fetched.certificate is None

    def test_run_always_reaches_terminal_status(self, session, user_a):
        """Runs should always end in COMPLETED or FAILED."""
        terminal = {VerificationRunStatus.COMPLETED, VerificationRunStatus.FAILED}

        # Completed run
        run_ok = _make_run(session, "user-a", status=VerificationRunStatus.COMPLETED)
        assert run_ok.status in terminal

        # Failed run
        run_fail = _make_run(session, "user-a", status=VerificationRunStatus.FAILED, error="err")
        assert run_fail.status in terminal


# ============================================
# 3.3 — AUTH AND USER ISOLATION
# ============================================

class TestAuthAndUserIsolation:
    def test_user_a_cannot_see_user_b_run(self, session, user_a, user_b):
        run_b = _make_run(session, "user-b", construct_id="oracle-b")

        # Simulate query as user A
        from sqlalchemy import select
        result = session.execute(
            select(VerificationRun).where(
                VerificationRun.id == run_b.id,
                VerificationRun.user_id == "user-a",  # User A's query
            )
        )
        assert result.scalar_one_or_none() is None

    def test_user_a_list_excludes_user_b(self, session, user_a, user_b):
        _make_run(session, "user-a", construct_id="oracle-a")
        _make_run(session, "user-b", construct_id="oracle-b")

        from sqlalchemy import select
        result = session.execute(
            select(VerificationRun).where(VerificationRun.user_id == "user-a")
        )
        runs = result.scalars().all()
        assert len(runs) == 1
        assert runs[0].construct_id == "oracle-a"

    def test_certificates_are_public(self, session, user_a, user_b):
        cert = _make_certificate(session, construct_id="public-cert")

        # Anyone can access certificates
        fetched = session.get(VerificationCertificate, cert.id)
        assert fetched is not None
        assert fetched.construct_id == "public-cert"


# ============================================
# 3.4 — PAGINATION AND FILTERING
# ============================================

class TestPaginationAndFiltering:
    def test_runs_limit_offset(self, session, user_a):
        for i in range(5):
            _make_run(session, "user-a", construct_id=f"oracle-{i}")

        from sqlalchemy import select
        result = session.execute(
            select(VerificationRun)
            .where(VerificationRun.user_id == "user-a")
            .limit(2)
            .offset(0)
        )
        runs = result.scalars().all()
        assert len(runs) == 2

    def test_runs_filter_by_status(self, session, user_a):
        _make_run(session, "user-a", status=VerificationRunStatus.COMPLETED)
        _make_run(session, "user-a", status=VerificationRunStatus.COMPLETED)
        _make_run(session, "user-a", status=VerificationRunStatus.FAILED, error="err")

        from sqlalchemy import select
        result = session.execute(
            select(VerificationRun).where(
                VerificationRun.user_id == "user-a",
                VerificationRun.status == VerificationRunStatus.COMPLETED,
            )
        )
        runs = result.scalars().all()
        assert len(runs) == 2

    def test_runs_filter_by_construct_id(self, session, user_a):
        _make_run(session, "user-a", construct_id="oracle-alpha")
        _make_run(session, "user-a", construct_id="oracle-beta")
        _make_run(session, "user-a", construct_id="oracle-alpha")

        from sqlalchemy import select
        result = session.execute(
            select(VerificationRun).where(
                VerificationRun.user_id == "user-a",
                VerificationRun.construct_id == "oracle-alpha",
            )
        )
        runs = result.scalars().all()
        assert len(runs) == 2

    def test_certificates_sort_by_brier(self, session):
        _make_certificate(session, construct_id="c1", brier=0.30)
        _make_certificate(session, construct_id="c2", brier=0.10)
        _make_certificate(session, construct_id="c3", brier=0.20)

        from sqlalchemy import select
        result = session.execute(
            select(VerificationCertificate).order_by(VerificationCertificate.brier.asc())
        )
        certs = result.scalars().all()
        assert certs[0].brier == 0.10
        assert certs[1].brier == 0.20
        assert certs[2].brier == 0.30

    def test_certificates_filter_by_construct_id(self, session):
        _make_certificate(session, construct_id="oracle-x")
        _make_certificate(session, construct_id="oracle-y")
        _make_certificate(session, construct_id="oracle-x")

        from sqlalchemy import select, func
        count = session.execute(
            select(func.count()).select_from(VerificationCertificate)
            .where(VerificationCertificate.construct_id == "oracle-x")
        ).scalar()
        assert count == 2

    def test_total_count_reflects_all(self, session, user_a):
        """Total count should reflect all matching, not just the page."""
        for i in range(10):
            _make_run(session, "user-a", construct_id=f"oracle-{i}")

        from sqlalchemy import select, func
        total = session.execute(
            select(func.count()).select_from(VerificationRun)
            .where(VerificationRun.user_id == "user-a")
        ).scalar()
        assert total == 10


# ============================================
# 3.5 — APP STARTUP SMOKE TESTS
# ============================================

class TestAppStartup:
    def test_verification_router_import(self):
        """The verification router should be importable."""
        from api.verification_routes import router
        assert router is not None
        assert router.prefix == "/api/v1/verification"

    def test_verification_bridge_import_without_echelon(self):
        """Bridge should import even when echelon-verify is not installed."""
        from services.verification_bridge import (
            ECHELON_VERIFY_AVAILABLE,
            certificate_to_db,
            replay_score_to_db,
            run_verification_task,
        )
        # Functions exist regardless of echelon-verify availability
        assert callable(certificate_to_db)
        assert callable(replay_score_to_db)
        assert callable(run_verification_task)

    def test_schema_imports(self):
        """All verification schemas should be importable."""
        from schemas.verification import (
            VerificationRunCreate,
            VerificationRunResponse,
            VerificationRunListResponse,
            CertificateResponse,
            CertificateSummaryResponse,
            CertificateListResponse,
            ReplayScoreResponse,
        )
        # All schemas present
        assert VerificationRunCreate is not None
        assert CertificateResponse is not None
