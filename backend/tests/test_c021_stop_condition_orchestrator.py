"""Tests for StopConditionOrchestrator — cycle-021 sprint-1.

Tests the orchestrator's evaluation logic, persistence, and WS event emission.
Uses sync Session with SQLite in-memory + async mocking for WS and session.flush.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
)
from backend.services.stop_condition_orchestrator import (
    StopConditionResult,
    evaluate_after_mutation,
    _compute_time_remaining,
)

_TABLES = [
    Investigation.__table__,
    InvestigationEvidenceItem.__table__,
    InvestigationClaimNode.__table__,
    InvestigationCounterSignal.__table__,
    InvestigationDriftEvent.__table__,
    InvestigationCertificateRecord.__table__,
]


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng, tables=_TABLES)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _make_investigation(session, inv_id=None, status="ACTIVE", stop_condition="EVIDENCE_THRESHOLD",
                        stop_config=None, stop_condition_status=None):
    now = datetime.now(timezone.utc)
    inv = Investigation(
        id=inv_id or f"inv-{uuid.uuid4().hex[:8]}",
        theatre_id="theatre-1",
        construct_id="construct-1",
        inquiry_class="INVESTIGATIVE",
        status=status,
        stop_condition=stop_condition,
        stop_config_json=stop_config or {"min_supported_claims": 1},
        domain_filters_json=[],
        created_at=now,
        updated_at=now,
    )
    if stop_condition_status:
        inv.stop_condition_status = stop_condition_status
    session.add(inv)
    session.flush()
    return inv


def _add_evidence(session, inv_id):
    item = InvestigationEvidenceItem(
        id=f"ev-{uuid.uuid4().hex[:8]}",
        investigation_id=inv_id,
        content_hash="a" * 64,
        provenance_class="public_primary",
        content_type="text/plain",
        source_description="test",
        source_id="market_data",
        submitted_at=datetime.now(timezone.utc),
    )
    session.add(item)
    session.flush()


def _add_supported_claim(session, inv_id, evidence_id="ev-1"):
    claim = InvestigationClaimNode(
        id=f"cl-{uuid.uuid4().hex[:8]}",
        investigation_id=inv_id,
        claim_text="Test claim",
        claim_type="fact",
        evidence_refs_json=[evidence_id],
        status="supported",
        confidence=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(claim)
    session.flush()


def _add_drift_event(session, inv_id, impact="material"):
    drift = InvestigationDriftEvent(
        id=f"dr-{uuid.uuid4().hex[:8]}",
        investigation_id=inv_id,
        drift_type="market_rule_change",
        detected_at=datetime.now(timezone.utc),
        original_value="old",
        new_value="new",
        impact_assessment=impact,
    )
    session.add(drift)
    session.flush()


@pytest.mark.asyncio
async def test_evaluate_persists_ready_status(session):
    """Evaluation result is written to investigation fields."""
    inv = _make_investigation(session, stop_config={"min_supported_claims": 1})
    _add_evidence(session, inv.id)
    _add_supported_claim(session, inv.id)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="evidence")

    assert result.ready is True
    assert inv.stop_condition_status == "READY"
    assert inv.stop_condition_reason == "evidence_threshold_met"
    assert inv.stop_condition_evaluated_at is not None
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_emits_ws_on_readiness_change(session):
    """WS event is fired when transitioning NOT_READY -> READY."""
    inv = _make_investigation(session, stop_condition_status=None,
                              stop_config={"min_supported_claims": 1})
    _add_evidence(session, inv.id)
    _add_supported_claim(session, inv.id)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="evidence")

    assert result.ready is True
    mock_ws.broadcast_global.assert_called_once_with(
        "INVESTIGATION_STOP_CONDITION_MET",
        {
            "investigation_id": inv.id,
            "reason": "evidence_threshold_met",
            "trigger": "evidence",
            "drift_material": False,
        },
    )


@pytest.mark.asyncio
async def test_evaluate_no_ws_when_already_ready(session):
    """No WS event when status is already READY."""
    inv = _make_investigation(session, stop_condition_status="READY",
                              stop_config={"min_supported_claims": 1})
    _add_evidence(session, inv.id)
    _add_supported_claim(session, inv.id)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="evidence")

    assert result.ready is True
    mock_ws.broadcast_global.assert_not_called()


@pytest.mark.asyncio
async def test_drift_trigger_includes_drift_in_reason(session):
    """Material drift trigger augments reason with drift_material; prefix."""
    inv = _make_investigation(session, stop_condition="OUTCOME_RESOLUTION")
    _add_drift_event(session, inv.id, impact="material")

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(
            mock_session, inv, trigger="drift", time_remaining=-1.0
        )

    assert result.drift_material is True
    assert result.reason.startswith("drift_material;")


@pytest.mark.asyncio
async def test_skips_completed_investigation(session):
    """Returns early for COMPLETED investigations."""
    inv = _make_investigation(session, status="COMPLETED")

    mock_session = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="evidence")

    assert result.ready is True
    assert result.reason == "already_ready_or_completed"
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_certificate_ready_rebuilds_routing_before_issuance(session):
    """CERTIFICATE_READY investigations still reevaluate and can force review."""
    inv = _make_investigation(
        session,
        status="CERTIFICATE_READY",
        stop_condition="EVIDENCE_THRESHOLD",
        stop_config={"min_supported_claims": 1},
        stop_condition_status="READY",
    )
    _add_evidence(session, inv.id)
    _add_supported_claim(session, inv.id)
    _add_drift_event(session, inv.id, impact="material")

    cert = InvestigationCertificateRecord(
        investigation_id=inv.id,
        certificate_hash="a" * 64,
        certificate_json={"certificate_id": "old"},
        routing_decision="ALLOWED",
        routing_reason="all_checks_passed",
        certificate_status="READY",
        ready_at=datetime.now(timezone.utc),
    )
    inv.certificate = cert
    session.add(cert)
    session.flush()

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="drift")

    assert result.drift_material is True
    assert cert.routing_decision == "REVIEW_REQUIRED"
    assert cert.routing_reason == "drift_event_material"
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_evidence_trigger_evaluates_stop(session):
    """Evidence trigger runs the evaluator and persists NOT_READY when threshold not met."""
    inv = _make_investigation(session, stop_config={"min_supported_claims": 5})
    _add_evidence(session, inv.id)
    _add_supported_claim(session, inv.id)  # only 1, need 5

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.stop_condition_orchestrator.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await evaluate_after_mutation(mock_session, inv, trigger="evidence")

    assert result.ready is False
    assert inv.stop_condition_status == "NOT_READY"
    assert "supported_claims:1/5" in inv.stop_condition_reason
    mock_ws.broadcast_global.assert_not_called()
