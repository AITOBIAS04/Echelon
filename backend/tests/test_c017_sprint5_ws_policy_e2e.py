"""Cycle-017 Sprint 5 — WebSocket Policy Events + E2E tests.

5 tests:
1. Certificate issuance triggers ROUTING_DECISION WS event
2. Gate resolution triggers COHERENCE_GATE_TRANSITION WS event
3. broadcast_tao_flow_alert sends to global + channel
4. ConnectionManager has all 3 new broadcast methods
5. E2E: certificate → routing → gate PENDING → resolve PASSED → is_deployable
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.database.models import (
    TheatreCertificate,
    TheatreAuditEvent,
    Theatre,
    TheatreTemplate,
    User,
)
from backend.services.coherence_gate_evaluator import CoherenceGateEvaluator
from backend.websockets.realtime_manager import ConnectionManager


# ── Fixtures ──

@pytest.fixture
def ws_manager():
    """Fresh ConnectionManager for each test."""
    return ConnectionManager()


@pytest.fixture
def engine():
    """In-memory SQLite for DB tests."""
    eng = create_engine("sqlite:///:memory:")
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        Theatre.__table__,
        TheatreCertificate.__table__,
        TheatreAuditEvent.__table__,
    ]
    for table in tables:
        table.create(eng, checkfirst=True)
    return eng


@pytest.fixture
def seed_certificate(engine):
    """Seed a certificate for E2E tests."""
    with Session(engine) as session:
        user = User(id="user-1", username="test", email="test@test.com", password_hash="x")
        session.add(user)
        session.flush()

        template = TheatreTemplate(
            id="tmpl-1",
            template_family="PRODUCT",
            execution_path="replay",
            display_name="Test",
            schema_version="2.0.1",
            template_json={"theatre_id": "t-1", "execution_path": "replay"},
        )
        session.add(template)
        session.flush()

        theatre = Theatre(
            id="theatre-1",
            user_id="user-1",
            template_id="tmpl-1",
            state="RESOLVED",
            construct_id="construct-1",
        )
        session.add(theatre)
        session.flush()

        now = datetime.now(timezone.utc)
        cert = TheatreCertificate(
            id="cert-e2e",
            theatre_id="theatre-1",
            template_id="tmpl-1",
            construct_id="construct-1",
            inquiry_class="INVESTIGATIVE",
            criteria_json={},
            scores_json={},
            composite_score=0.65,
            replay_count=1,
            evidence_bundle_hash="a" * 64,
            ground_truth_hash="b" * 64,
            construct_version="1.0.0",
            scorer_version="1.0.0",
            methodology_version="1.0.0",
            dataset_hash="c" * 64,
            verification_tier="CONTESTED",
            commitment_hash="d" * 64,
            theatre_committed_at=now,
            theatre_resolved_at=now,
            ground_truth_source="test",
            execution_path="replay",
            routing_hint="REVIEW_REQUIRED",
        )
        session.add(cert)
        session.commit()

    return engine


# ── Test 1: ROUTING_DECISION WS event ──

@pytest.mark.asyncio
async def test_routing_decision_broadcast(ws_manager):
    """broadcast_routing_decision sends ROUTING_DECISION event."""
    mock_ws = AsyncMock()
    await ws_manager.connect(mock_ws, "conn-1")

    await ws_manager.broadcast_routing_decision("cert-1", {
        "routing_hint": "REVIEW_REQUIRED",
        "reason_code": "INVESTIGATIVE_LOW_SCORE",
        "rule_name": "investigative_low_confidence",
    })

    mock_ws.send_text.assert_called_once()
    msg = json.loads(mock_ws.send_text.call_args[0][0])
    assert msg["type"] == "ROUTING_DECISION"
    assert msg["data"]["certificate_id"] == "cert-1"
    assert msg["data"]["routing_hint"] == "REVIEW_REQUIRED"


# ── Test 2: COHERENCE_GATE_TRANSITION WS event ──

@pytest.mark.asyncio
async def test_coherence_gate_transition_broadcast(ws_manager):
    """broadcast_coherence_gate_transition sends COHERENCE_GATE_TRANSITION event."""
    mock_ws = AsyncMock()
    await ws_manager.connect(mock_ws, "conn-1")

    await ws_manager.broadcast_coherence_gate_transition("cert-1", {
        "from_status": "PENDING",
        "to_status": "PASSED",
        "reviewer_id": "user-1",
    })

    mock_ws.send_text.assert_called_once()
    msg = json.loads(mock_ws.send_text.call_args[0][0])
    assert msg["type"] == "COHERENCE_GATE_TRANSITION"
    assert msg["data"]["certificate_id"] == "cert-1"
    assert msg["data"]["from_status"] == "PENDING"
    assert msg["data"]["to_status"] == "PASSED"


# ── Test 3: TAO_FLOW_ALERT to global + channel ──

@pytest.mark.asyncio
async def test_tao_flow_alert_broadcast(ws_manager):
    """broadcast_tao_flow_alert sends to global and timeline channel."""
    mock_ws = AsyncMock()
    await ws_manager.connect(mock_ws, "conn-1")
    ws_manager.subscribe("conn-1", "timeline:tl-1")

    await ws_manager.broadcast_tao_flow_alert("tl-1", {
        "net_inflow_24h": 1500.0,
        "net_inflow_7d": 5000.0,
        "threshold": 1000.0,
    })

    # Should receive 2 messages: global broadcast + channel broadcast
    assert mock_ws.send_text.call_count == 2
    msgs = [json.loads(call[0][0]) for call in mock_ws.send_text.call_args_list]
    assert msgs[0]["type"] == "TAO_FLOW_ALERT"
    assert msgs[0]["data"]["timeline_id"] == "tl-1"
    assert msgs[1]["type"] == "TAO_FLOW_ALERT"
    assert msgs[1]["data"]["net_inflow_24h"] == 1500.0


# ── Test 4: ConnectionManager has all 3 broadcast methods ──

def test_connection_manager_has_policy_methods():
    """ConnectionManager has all 3 policy broadcast methods."""
    mgr = ConnectionManager()
    assert hasattr(mgr, "broadcast_routing_decision")
    assert hasattr(mgr, "broadcast_coherence_gate_transition")
    assert hasattr(mgr, "broadcast_tao_flow_alert")
    assert callable(mgr.broadcast_routing_decision)
    assert callable(mgr.broadcast_coherence_gate_transition)
    assert callable(mgr.broadcast_tao_flow_alert)


# ── Test 5: E2E — Full policy lifecycle (exercises actual open_gate/resolve_gate) ──

@pytest.mark.asyncio
async def test_e2e_policy_lifecycle(seed_certificate):
    """Create → routing REVIEW_REQUIRED → open_gate() PENDING → resolve_gate() PASSED → is_deployable.

    Exercises the real CoherenceGateEvaluator.open_gate() and resolve_gate()
    methods to catch regressions in the production wiring. Uses a sync-to-async
    session adapter since aiosqlite may not be available.
    """
    from backend.schemas.theatre import TheatreCertificateResponse

    evaluator = CoherenceGateEvaluator()

    # Adapt sync session.get to async interface expected by open_gate/resolve_gate
    class _AsyncSessionAdapter:
        """Wraps a sync Session to satisfy the async API of CoherenceGateEvaluator."""
        def __init__(self, sync_session):
            self._s = sync_session

        async def get(self, model, pk):
            return self._s.get(model, pk)

        def add(self, obj):
            self._s.add(obj)

    # Patch WS manager to no-op (we're testing gate logic, not WS delivery)
    with patch("backend.services.coherence_gate_evaluator.ws_manager") as mock_ws:
        mock_ws.broadcast_coherence_gate_transition = AsyncMock()

        with Session(seed_certificate) as session:
            adapter = _AsyncSessionAdapter(session)

            # 1. Certificate exists with REVIEW_REQUIRED routing
            cert = session.get(TheatreCertificate, "cert-e2e")
            assert cert.routing_hint == "REVIEW_REQUIRED"

            # 2. Evaluator determines review is required
            needs_review = evaluator.should_require_review(
                routing_hint=cert.routing_hint,
                inquiry_class=cert.inquiry_class,
                composite_score=cert.composite_score,
                verification_tier=cert.verification_tier,
            )
            assert needs_review is True

            # 3. Actually call open_gate() — the production code path
            cert = await evaluator.open_gate(adapter, "cert-e2e")
            assert cert.coherence_review_required is True
            assert cert.coherence_gate_status == "PENDING"
            session.commit()

            # Verify PENDING persisted
            cert = session.get(TheatreCertificate, "cert-e2e")
            assert cert.coherence_gate_status == "PENDING"

            # 4. Actually call resolve_gate() — the production code path
            cert = await evaluator.resolve_gate(adapter, "cert-e2e", "PASSED", "user-1")
            assert cert.coherence_gate_status == "PASSED"
            assert cert.coherence_reviewed_at is not None
            assert cert.coherence_reviewer_id == "user-1"
            session.commit()

            # 5. Verify all states persisted
            cert = session.get(TheatreCertificate, "cert-e2e")
            assert cert.coherence_gate_status == "PASSED"
            assert cert.coherence_reviewed_at is not None
            assert cert.coherence_reviewer_id == "user-1"

            # 6. Verify audit trail created by actual open_gate/resolve_gate
            result = session.execute(
                select(TheatreAuditEvent)
                .where(TheatreAuditEvent.theatre_id == "theatre-1")
                .where(TheatreAuditEvent.event_type.in_([
                    "COHERENCE_GATE_OPENED",
                    "COHERENCE_GATE_RESOLVED",
                ]))
                .order_by(TheatreAuditEvent.created_at)
            )
            events = result.scalars().all()
            assert len(events) == 2
            assert events[0].event_type == "COHERENCE_GATE_OPENED"
            assert events[1].event_type == "COHERENCE_GATE_RESOLVED"

            # 7. Verify is_deployable via schema response
            now = datetime.now(timezone.utc)
            resp = TheatreCertificateResponse(
                id=cert.id,
                theatre_id=cert.theatre_id,
                template_id=cert.template_id,
                construct_id=cert.construct_id,
                criteria_json=cert.criteria_json or {},
                scores_json=cert.scores_json or {},
                composite_score=cert.composite_score,
                replay_count=cert.replay_count,
                evidence_bundle_hash=cert.evidence_bundle_hash,
                ground_truth_hash=cert.ground_truth_hash,
                construct_version=cert.construct_version,
                scorer_version=cert.scorer_version,
                methodology_version=cert.methodology_version,
                dataset_hash=cert.dataset_hash,
                verification_tier=cert.verification_tier,
                commitment_hash=cert.commitment_hash,
                issued_at=now,
                theatre_committed_at=cert.theatre_committed_at,
                theatre_resolved_at=cert.theatre_resolved_at,
                ground_truth_source=cert.ground_truth_source,
                execution_path=cert.execution_path,
                routing_hint=cert.routing_hint,
                coherence_review_required=cert.coherence_review_required,
                coherence_gate_status=cert.coherence_gate_status,
                precision=None,
                recall=None,
                brier_score=None,
                ece=None,
                construct_chain_versions=None,
                expires_at=None,
            )
            assert resp.is_deployable is True
