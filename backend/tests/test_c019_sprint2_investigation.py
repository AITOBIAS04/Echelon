"""Cycle-019 Sprint 2 — Investigation Persistence tests.

8 tests:
1. Create investigation persists to DB
2. Submit evidence persists InvestigationEvidenceItem with content_hash
3. Register claim persists InvestigationClaimNode
4. Log counter-signal persists InvestigationCounterSignal
5. Log drift event persists InvestigationDriftEvent
6. Persist certificate creates InvestigationCertificateRecord
7. Investigation survives simulated restart (new session)
8. Investigation API response shape check (contract stability)
"""

import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
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


# ── Fixtures ──

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


def _create_investigation(session, inv_id="inv-1"):
    """Helper to create a test investigation."""
    now = datetime.now(timezone.utc)
    inv = Investigation(
        id=inv_id,
        theatre_id="theatre-1",
        construct_id="test_construct",
        inquiry_class="INVESTIGATIVE",
        status="ACTIVE",
        domain_filters_json=["politics"],
        stop_condition="OUTCOME_RESOLUTION",
        stop_config_json={"timeout_hours": 72},
        created_at=now,
        updated_at=now,
    )
    session.add(inv)
    session.flush()
    return inv


# ── Test 1: Create investigation persists to DB ──

def test_create_investigation_persists(session):
    """Create investigation persists to DB."""
    inv = _create_investigation(session)

    result = session.execute(
        select(Investigation).where(Investigation.id == "inv-1")
    )
    loaded = result.scalar_one()

    assert loaded.id == "inv-1"
    assert loaded.theatre_id == "theatre-1"
    assert loaded.construct_id == "test_construct"
    assert loaded.inquiry_class == "INVESTIGATIVE"
    assert loaded.status == "ACTIVE"
    assert loaded.domain_filters_json == ["politics"]
    assert loaded.stop_condition == "OUTCOME_RESOLUTION"


# ── Test 2: Submit evidence persists with content_hash ──

def test_submit_evidence_persists(session):
    """Submit evidence persists InvestigationEvidenceItem with correct content_hash."""
    _create_investigation(session)

    content = b"Test evidence content"
    expected_hash = hashlib.sha256(content).hexdigest()

    item = InvestigationEvidenceItem(
        id="ev-1",
        investigation_id="inv-1",
        content_hash=expected_hash,
        provenance_class="public_primary",
        content_type="text/plain",
        source_description="Test source",
        source_id="src-1",
        query_determinism="deterministic",
        references_json=["ref-1", "ref-2"],
    )
    session.add(item)
    session.flush()

    result = session.execute(
        select(InvestigationEvidenceItem).where(
            InvestigationEvidenceItem.investigation_id == "inv-1"
        )
    )
    loaded = result.scalar_one()

    assert loaded.content_hash == expected_hash
    assert loaded.provenance_class == "public_primary"
    assert loaded.source_id == "src-1"
    assert loaded.references_json == ["ref-1", "ref-2"]


# ── Test 3: Register claim persists ──

def test_register_claim_persists(session):
    """Register claim persists InvestigationClaimNode."""
    _create_investigation(session)

    node = InvestigationClaimNode(
        id="clm-1",
        investigation_id="inv-1",
        claim_text="Company X filed for restructuring",
        claim_type="fact",
        evidence_refs_json=["ev-1"],
        confidence=0.85,
        status="SUPPORTED",
    )
    session.add(node)
    session.flush()

    result = session.execute(
        select(InvestigationClaimNode).where(
            InvestigationClaimNode.investigation_id == "inv-1"
        )
    )
    loaded = result.scalar_one()

    assert loaded.claim_text == "Company X filed for restructuring"
    assert loaded.claim_type == "fact"
    assert loaded.confidence == 0.85
    assert loaded.evidence_refs_json == ["ev-1"]


# ── Test 4: Log counter-signal persists ──

def test_log_counter_signal_persists(session):
    """Log counter-signal persists InvestigationCounterSignal."""
    _create_investigation(session)

    signal = InvestigationCounterSignal(
        id="cs-1",
        investigation_id="inv-1",
        signal_class="OFFICIAL_DENIAL",
        material=True,
        resolution_impact="May invalidate restructuring claim",
        detection_method="human_submitted",
        evidence_ref="ev-1",
    )
    session.add(signal)
    session.flush()

    result = session.execute(
        select(InvestigationCounterSignal).where(
            InvestigationCounterSignal.investigation_id == "inv-1"
        )
    )
    loaded = result.scalar_one()

    assert loaded.signal_class == "OFFICIAL_DENIAL"
    assert loaded.material is True
    assert loaded.evidence_ref == "ev-1"


# ── Test 5: Log drift event persists ──

def test_log_drift_event_persists(session):
    """Log drift event persists InvestigationDriftEvent."""
    _create_investigation(session)

    event = InvestigationDriftEvent(
        id="dr-1",
        investigation_id="inv-1",
        drift_type="ENTITY_RESTRUCTURE",
        original_value="Company X Inc.",
        new_value="Company X Holdings LLC",
        impact_assessment="material",
        evidence_ref="ev-1",
    )
    session.add(event)
    session.flush()

    result = session.execute(
        select(InvestigationDriftEvent).where(
            InvestigationDriftEvent.investigation_id == "inv-1"
        )
    )
    loaded = result.scalar_one()

    assert loaded.drift_type == "ENTITY_RESTRUCTURE"
    assert loaded.original_value == "Company X Inc."
    assert loaded.new_value == "Company X Holdings LLC"
    assert loaded.impact_assessment == "material"


# ── Test 6: Persist certificate ──

def test_persist_certificate(session):
    """Persist certificate creates InvestigationCertificateRecord."""
    _create_investigation(session)

    cert_data = {"routing_decision": "ALLOWED", "evidence_count": 5}
    cert_hash = hashlib.sha256(str(cert_data).encode()).hexdigest()

    record = InvestigationCertificateRecord(
        investigation_id="inv-1",
        certificate_hash=cert_hash,
        certificate_json=cert_data,
        routing_decision="ALLOWED",
        routing_reason="All evidence corroborated",
    )
    session.add(record)
    session.flush()

    result = session.execute(
        select(InvestigationCertificateRecord).where(
            InvestigationCertificateRecord.investigation_id == "inv-1"
        )
    )
    loaded = result.scalar_one()

    assert loaded.certificate_hash == cert_hash
    assert loaded.routing_decision == "ALLOWED"
    assert loaded.certificate_json == cert_data


# ── Test 7: Investigation survives simulated restart ──

def test_investigation_survives_restart(engine):
    """Investigation data survives simulated restart (new session)."""
    # Session 1: Create investigation + evidence + claim
    with Session(engine) as s1:
        _create_investigation(s1, "inv-restart")
        s1.add(InvestigationEvidenceItem(
            id="ev-r1", investigation_id="inv-restart",
            content_hash="abc123", provenance_class="public_primary",
        ))
        s1.add(InvestigationClaimNode(
            id="clm-r1", investigation_id="inv-restart",
            claim_text="Restart test claim", claim_type="fact",
        ))
        s1.commit()

    # Session 2 (simulated restart): Verify data persists
    with Session(engine) as s2:
        inv = s2.execute(
            select(Investigation).where(Investigation.id == "inv-restart")
        ).scalar_one()
        assert inv.theatre_id == "theatre-1"

        evidence = s2.execute(
            select(InvestigationEvidenceItem).where(
                InvestigationEvidenceItem.investigation_id == "inv-restart"
            )
        ).scalars().all()
        assert len(evidence) == 1
        assert evidence[0].content_hash == "abc123"

        claims = s2.execute(
            select(InvestigationClaimNode).where(
                InvestigationClaimNode.investigation_id == "inv-restart"
            )
        ).scalars().all()
        assert len(claims) == 1
        assert claims[0].claim_text == "Restart test claim"


# ── Test 8: Investigation API contract (response shape) ──

def test_investigation_response_shape():
    """Investigation API response shape matches contract."""
    from backend.schemas.investigation_schemas import (
        InvestigationSummaryResponse,
    )

    now = datetime.now(timezone.utc)
    summary = InvestigationSummaryResponse(
        id="inv-1",
        theatre_id="theatre-1",
        construct_id="test_construct",
        inquiry_class="INVESTIGATIVE",
        status="active",
        evidence_count=3,
        claim_count=2,
        counter_signal_count=1,
        drift_event_count=0,
        created_at=now,
        updated_at=now,
    )

    assert summary.id == "inv-1"
    assert summary.evidence_count == 3
    assert summary.claim_count == 2
    assert summary.counter_signal_count == 1
    assert summary.drift_event_count == 0
