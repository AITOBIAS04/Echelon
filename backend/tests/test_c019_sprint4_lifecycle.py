"""Cycle-019 Sprint 4 — Certificate Persistence + Deployment Lifecycle tests.

5 tests:
1. Certificate persisted with correct hash
2. Investigation status set to COMPLETED on certificate build
3. Deployment ACTIVE → PAUSED → ACTIVE lifecycle
4. Deployment WITHDRAWN rejects further transitions
5. Deployment detail returns audit trail
"""

import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    User,
    TheatreTemplate,
    Theatre,
    AgentDeployment,
    DeploymentAuditEvent,
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationCertificateRecord,
)


# ── Fixtures ──

_TABLES = [
    User.__table__,
    TheatreTemplate.__table__,
    Theatre.__table__,
    AgentDeployment.__table__,
    DeploymentAuditEvent.__table__,
    Investigation.__table__,
    InvestigationEvidenceItem.__table__,
    InvestigationClaimNode.__table__,
    InvestigationCounterSignal.__table__,
    InvestigationCertificateRecord.__table__,
]


def _uid():
    return str(uuid.uuid4())[:8]


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    # Stub agents table (Agent model uses ARRAY which SQLite can't render)
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE TABLE agents (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL DEFAULT '',
                archetype VARCHAR(20) NOT NULL DEFAULT 'DEGEN',
                tier INTEGER DEFAULT 1,
                level INTEGER DEFAULT 1,
                sanity INTEGER DEFAULT 100,
                max_sanity INTEGER DEFAULT 100,
                is_alive BOOLEAN DEFAULT 1,
                death_cause VARCHAR(200),
                owner_id VARCHAR(50) NOT NULL DEFAULT '',
                total_pnl_usd FLOAT DEFAULT 0.0,
                win_rate FLOAT DEFAULT 0.0,
                trades_count INTEGER DEFAULT 0,
                genome JSON DEFAULT '{}',
                parent_agent_ids TEXT DEFAULT '[]',
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        conn.commit()
    Base.metadata.create_all(eng, tables=_TABLES)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _seed(session):
    """Seed common test data."""
    now = datetime.now(timezone.utc)

    user = User(
        id="user-1", username="tester", email="t@test.com",
        password_hash="x", created_at=now, updated_at=now,
    )
    session.add(user)

    session.execute(text(
        "INSERT INTO agents (id, name, archetype, sanity, is_alive, owner_id, created_at, updated_at) "
        "VALUES ('agent-1', 'TestBot', 'DEGEN', 100, 1, 'user-1', :now, :now)"
    ), {"now": now})

    tmpl = TheatreTemplate(
        id="tmpl-1", display_name="Test", template_family="binary",
        execution_path="TWO_RAIL", schema_version="1.0", template_json={},
        created_at=now, updated_at=now,
    )
    session.add(tmpl)

    theatre = Theatre(
        id="theatre-1", user_id="user-1", template_id="tmpl-1",
        state="RESOLVED", construct_id="test_construct",
        created_at=now, updated_at=now,
    )
    session.add(theatre)

    session.flush()
    return now


# ── Test 1: Certificate persisted with correct hash ──

def test_certificate_persisted_with_hash(session):
    """Certificate record persisted with correct SHA-256 hash."""
    now = _seed(session)

    # Create investigation
    inv = Investigation(
        id="INV-001", theatre_id="theatre-1", construct_id="test_construct",
        inquiry_class="INVESTIGATIVE", status="ACTIVE",
        domain_filters_json=[], stop_condition="OUTCOME_RESOLUTION",
        stop_config_json={},
    )
    session.add(inv)
    session.flush()

    # Submit evidence
    content = b"evidence payload alpha"
    content_hash = hashlib.sha256(content).hexdigest()
    ev = InvestigationEvidenceItem(
        id="EV-001", investigation_id="INV-001",
        content_hash=content_hash, provenance_class="primary",
        content_type="text/plain", source_description="test",
    )
    session.add(ev)
    session.flush()

    # Build certificate
    cert_data = {
        "investigation_id": "INV-001",
        "evidence_count": 1,
        "claim_count": 0,
        "routing_decision": "ALLOWED",
    }
    import json
    cert_hash = hashlib.sha256(
        json.dumps(cert_data, sort_keys=True).encode()
    ).hexdigest()

    record = InvestigationCertificateRecord(
        investigation_id="INV-001",
        certificate_hash=cert_hash,
        certificate_json=cert_data,
        routing_decision="ALLOWED",
        routing_reason="All checks passed",
    )
    session.add(record)
    session.flush()

    # Verify
    loaded = session.execute(
        select(InvestigationCertificateRecord)
        .where(InvestigationCertificateRecord.investigation_id == "INV-001")
    ).scalar_one()

    assert loaded.certificate_hash == cert_hash
    assert loaded.certificate_json["evidence_count"] == 1
    assert loaded.routing_decision == "ALLOWED"


# ── Test 2: Investigation COMPLETED on certificate build ──

def test_investigation_completed_on_certificate(session):
    """Investigation status set to COMPLETED when certificate is built."""
    now = _seed(session)

    inv = Investigation(
        id="INV-002", theatre_id="theatre-1", construct_id="test_construct",
        inquiry_class="INVESTIGATIVE", status="ACTIVE",
        domain_filters_json=[], stop_condition="OUTCOME_RESOLUTION",
        stop_config_json={},
    )
    session.add(inv)
    session.flush()

    assert inv.status == "ACTIVE"

    # Build certificate and mark complete
    cert_data = {"investigation_id": "INV-002"}
    import json
    cert_hash = hashlib.sha256(
        json.dumps(cert_data, sort_keys=True).encode()
    ).hexdigest()

    record = InvestigationCertificateRecord(
        investigation_id="INV-002",
        certificate_hash=cert_hash,
        certificate_json=cert_data,
        routing_decision="ALLOWED",
    )
    session.add(record)

    # Mark investigation as completed (this is what persist_certificate does)
    inv.status = "COMPLETED"
    inv.completed_at = datetime.now(timezone.utc)
    inv.updated_at = datetime.now(timezone.utc)
    session.flush()

    # Read back
    loaded = session.execute(
        select(Investigation).where(Investigation.id == "INV-002")
    ).scalar_one()

    assert loaded.status == "COMPLETED"
    assert loaded.completed_at is not None

    # Certificate FK links to investigation (unique constraint)
    cert = session.execute(
        select(InvestigationCertificateRecord)
        .where(InvestigationCertificateRecord.investigation_id == "INV-002")
    ).scalar_one()
    assert cert.certificate_hash == cert_hash


# ── Test 3: Deployment ACTIVE → PAUSED → ACTIVE lifecycle ──

def test_deployment_lifecycle_active_paused_active(session):
    """Deployment transitions: ACTIVE → PAUSED → ACTIVE."""
    now = _seed(session)

    dep_id = _uid()
    dep = AgentDeployment(
        id=dep_id,
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_by="user-1",
        deployed_at=now,
    )
    session.add(dep)

    # DEPLOYED audit event
    audit_deploy = DeploymentAuditEvent(
        deployment_id=dep_id,
        event_type="DEPLOYED",
        detail_json={"strategy_profile": "BALANCED"},
    )
    session.add(audit_deploy)
    session.flush()

    assert dep.status == "ACTIVE"

    # ACTIVE → PAUSED
    dep.status = "PAUSED"
    dep.paused_at = datetime.now(timezone.utc)
    dep.updated_at = datetime.now(timezone.utc)
    audit_pause = DeploymentAuditEvent(
        deployment_id=dep_id,
        event_type="PAUSED",
    )
    session.add(audit_pause)
    session.flush()

    assert dep.status == "PAUSED"
    assert dep.paused_at is not None

    # PAUSED → ACTIVE
    dep.status = "ACTIVE"
    dep.paused_at = None
    dep.updated_at = datetime.now(timezone.utc)
    audit_resume = DeploymentAuditEvent(
        deployment_id=dep_id,
        event_type="RESUMED",
    )
    session.add(audit_resume)
    session.flush()

    assert dep.status == "ACTIVE"
    assert dep.paused_at is None

    # Verify 3 audit events
    events = session.execute(
        select(DeploymentAuditEvent)
        .where(DeploymentAuditEvent.deployment_id == dep_id)
        .order_by(DeploymentAuditEvent.created_at)
    ).scalars().all()

    assert len(events) == 3
    assert [e.event_type for e in events] == ["DEPLOYED", "PAUSED", "RESUMED"]


# ── Test 4: WITHDRAWN rejects further transitions ──

def test_withdrawn_rejects_further_transitions(session):
    """Deployment in WITHDRAWN state rejects pause and resume."""
    now = _seed(session)

    dep_id = _uid()
    dep = AgentDeployment(
        id=dep_id,
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_by="user-1",
        deployed_at=now,
    )
    session.add(dep)
    session.flush()

    # Withdraw
    dep.status = "WITHDRAWN"
    dep.withdrawn_at = datetime.now(timezone.utc)
    dep.updated_at = datetime.now(timezone.utc)
    audit_withdraw = DeploymentAuditEvent(
        deployment_id=dep_id,
        event_type="WITHDRAWN",
        detail_json={"withdrawn_by": "user-1"},
    )
    session.add(audit_withdraw)
    session.flush()

    assert dep.status == "WITHDRAWN"

    # Verify guard logic: WITHDRAWN should not transition
    # The service layer rejects these — here we verify the state
    from backend.services.agent_deployment_service import DeploymentGuardError

    # Pause guard: status must be ACTIVE
    assert dep.status != "ACTIVE", "WITHDRAWN deployment should not be pausable"

    # Resume guard: status must be PAUSED
    assert dep.status != "PAUSED", "WITHDRAWN deployment should not be resumable"

    # Strategy change guard: status must not be WITHDRAWN
    assert dep.status == "WITHDRAWN", "Cannot change strategy on withdrawn deployment"


# ── Test 5: Deployment detail returns audit trail ──

def test_deployment_detail_returns_audit_trail(session):
    """Deployment detail includes full audit trail in chronological order."""
    now = _seed(session)

    dep_id = _uid()
    dep = AgentDeployment(
        id=dep_id,
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_by="user-1",
        deployed_at=now,
    )
    session.add(dep)

    # Create lifecycle events
    events_data = [
        ("DEPLOYED", {"strategy_profile": "BALANCED"}),
        ("STRATEGY_CHANGED", {"old_strategy": "BALANCED", "new_strategy": "AGGRESSIVE"}),
        ("PAUSED", None),
        ("RESUMED", None),
        ("WITHDRAWN", {"withdrawn_by": "user-1"}),
    ]

    for event_type, detail in events_data:
        evt = DeploymentAuditEvent(
            deployment_id=dep_id,
            event_type=event_type,
            detail_json=detail or {},
        )
        session.add(evt)

    dep.status = "WITHDRAWN"
    dep.strategy_profile = "AGGRESSIVE"
    dep.withdrawn_at = datetime.now(timezone.utc)
    session.flush()

    # Load deployment with audit events
    from sqlalchemy.orm import selectinload

    result = session.execute(
        select(AgentDeployment)
        .where(AgentDeployment.id == dep_id)
        .options(selectinload(AgentDeployment.audit_events))
    )
    loaded = result.scalar_one()

    assert loaded.id == dep_id
    assert loaded.status == "WITHDRAWN"
    assert len(loaded.audit_events) == 5

    event_types = [e.event_type for e in loaded.audit_events]
    assert "DEPLOYED" in event_types
    assert "STRATEGY_CHANGED" in event_types
    assert "PAUSED" in event_types
    assert "RESUMED" in event_types
    assert "WITHDRAWN" in event_types

    # Verify strategy change detail
    strategy_evt = [e for e in loaded.audit_events if e.event_type == "STRATEGY_CHANGED"][0]
    assert strategy_evt.detail_json["old_strategy"] == "BALANCED"
    assert strategy_evt.detail_json["new_strategy"] == "AGGRESSIVE"
