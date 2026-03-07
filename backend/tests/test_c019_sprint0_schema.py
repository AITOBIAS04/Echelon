"""Cycle-019 Sprint 0 — Schema Foundation tests.

4 tests:
1. All new models create tables without errors
2. Pydantic schemas validate with sample data
3. Theatre model has 3 new paradox risk columns
4. InvestigationCertificateRecord has unique constraint on investigation_id
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
    AgentDeployment,
    DeploymentAuditEvent,
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
)
from backend.schemas.agent_deployment_schemas import (
    AgentDeploymentCreate,
    AgentDeploymentResponse,
    AgentDeploymentSummaryResponse,
    DeploymentListResponse,
    StrategyUpdateRequest,
    DeploymentAuditEventResponse,
    DeploymentDetailResponse,
    ParadoxRiskResponse,
)


# ── Fixtures ──

# Tables needed for cycle-019 tests (excludes models with PG-only ARRAY columns)
_TABLES = [
    User.__table__,
    TheatreTemplate.__table__,
    TheatreCertificate.__table__,
    Theatre.__table__,
    AgentDeployment.__table__,
    DeploymentAuditEvent.__table__,
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


# ── Test 1: All new models create tables ──

def test_all_new_models_create_tables(engine):
    """All cycle-019 models create tables without errors."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    expected_tables = [
        "agent_deployments",
        "deployment_audit_events",
        "investigations",
        "investigation_evidence_items",
        "investigation_claim_nodes",
        "investigation_counter_signals",
        "investigation_drift_events",
        "investigation_certificates",
    ]

    for table in expected_tables:
        assert table in table_names, f"Table '{table}' not found"


# ── Test 2: Pydantic schemas validate ──

def test_pydantic_schemas_validate():
    """All Pydantic schemas pass validation with sample data."""
    now = datetime.now(timezone.utc)

    # Create request
    create = AgentDeploymentCreate(
        agent_id="agent-1",
        theatre_id="theatre-1",
        strategy_profile="AGGRESSIVE",
    )
    assert create.agent_id == "agent-1"
    assert create.strategy_profile == "AGGRESSIVE"

    # Strategy update
    update = StrategyUpdateRequest(strategy_profile="DEFENSIVE")
    assert update.strategy_profile == "DEFENSIVE"

    # Summary response (from_attributes)
    summary = AgentDeploymentSummaryResponse(
        id="dep-1",
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_at=now,
        created_at=now,
    )
    assert summary.status == "ACTIVE"

    # Full response
    response = AgentDeploymentResponse(
        id="dep-1",
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_by="user-1",
        deployed_at=now,
        routing_hint_snapshot="ALLOWED",
        coherence_gate_status_snapshot="PASSED",
        created_at=now,
        updated_at=now,
    )
    assert response.routing_hint_snapshot == "ALLOWED"

    # Audit event
    audit = DeploymentAuditEventResponse(
        id="evt-1",
        deployment_id="dep-1",
        event_type="DEPLOYED",
        detail_json={"strategy": "BALANCED"},
        created_at=now,
    )
    assert audit.event_type == "DEPLOYED"

    # Detail with audit trail
    detail = DeploymentDetailResponse(
        id="dep-1",
        agent_id="agent-1",
        theatre_id="theatre-1",
        status="ACTIVE",
        strategy_profile="BALANCED",
        deployed_by="user-1",
        deployed_at=now,
        created_at=now,
        updated_at=now,
        audit_events=[audit],
    )
    assert len(detail.audit_events) == 1

    # List response
    listing = DeploymentListResponse(
        deployments=[summary],
        total=1,
        limit=50,
        offset=0,
    )
    assert listing.total == 1

    # Paradox risk
    risk = ParadoxRiskResponse(
        level="WATCH",
        factors={"logic_gap": 0.4, "stability": 0.6},
        explanation="Logic gap widening",
        updated_at=now,
    )
    assert risk.level == "WATCH"


# ── Test 3: Theatre has paradox risk columns ──

def test_theatre_has_paradox_risk_columns(engine):
    """Theatre model has 3 new nullable paradox risk columns."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("theatres")}

    assert "paradox_risk_level" in columns
    assert "paradox_risk_factors_json" in columns
    assert "paradox_risk_updated_at" in columns


# ── Test 4: InvestigationCertificateRecord unique constraint ──

def test_investigation_certificate_unique_constraint(session):
    """InvestigationCertificateRecord.investigation_id has unique constraint."""
    now = datetime.now(timezone.utc)

    inv = Investigation(
        id="inv-1",
        theatre_id="theatre-1",
        construct_id="test_construct",
        created_at=now,
        updated_at=now,
    )
    session.add(inv)

    cert1 = InvestigationCertificateRecord(
        id="cert-1",
        investigation_id="inv-1",
        certificate_hash="abc123",
        certificate_json={"test": True},
        routing_decision="ALLOWED",
        issued_at=now,
    )
    session.add(cert1)
    session.flush()

    # Second certificate for same investigation should fail
    cert2 = InvestigationCertificateRecord(
        id="cert-2",
        investigation_id="inv-1",
        certificate_hash="def456",
        certificate_json={"test": True},
        routing_decision="ALLOWED",
        issued_at=now,
    )
    session.add(cert2)

    with pytest.raises(Exception):
        session.flush()
