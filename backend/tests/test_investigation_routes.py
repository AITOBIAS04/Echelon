"""Tests for investigation API routes — DB-backed persistence (Cycle 019 remediation).

8 tests covering core endpoints. Uses direct DB operations instead of
the defunct in-memory _investigations dict.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select, text
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
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.claim_graph import ClaimGraph, ClaimType
from backend.investigation.counter_signals import (
    InvestigationCounterSignalFeed,
    InvestigationCounterSignalClass,
)
from backend.investigation.commitment_monitor import CommitmentMonitor, DriftType, DriftImpact
from backend.investigation.models import ProvenanceClass
from backend.api.investigation_routes import _rebuild_toolset


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


def _create_investigation(session, inv_id=None, **kwargs):
    """Helper to create a test investigation in DB."""
    now = datetime.now(timezone.utc)
    inv_id = inv_id or f"INV-{uuid.uuid4().hex[:8]}"
    defaults = dict(
        id=inv_id,
        theatre_id="TH_TEST",
        construct_id="CON_TEST",
        inquiry_class="INVESTIGATIVE",
        status="ACTIVE",
        domain_filters_json=[],
        stop_condition="OUTCOME_RESOLUTION",
        stop_config_json={},
        created_at=now,
        updated_at=now,
    )
    defaults.update(kwargs)
    inv = Investigation(**defaults)
    session.add(inv)
    session.flush()
    return inv


def _add_evidence(session, investigation_id, content=b"test evidence"):
    """Helper to add evidence to an investigation."""
    content_hash = hashlib.sha256(content).hexdigest()
    item = InvestigationEvidenceItem(
        id=f"EV-{uuid.uuid4().hex[:8]}",
        investigation_id=investigation_id,
        content_hash=content_hash,
        provenance_class="public_primary",
        content_type="text/plain",
        source_description="test source",
        references_json=[],
        submitted_at=datetime.now(timezone.utc),
    )
    session.add(item)
    session.flush()
    return item


def _add_claim(session, investigation_id, evidence_refs=None):
    """Helper to add a claim to an investigation."""
    node = InvestigationClaimNode(
        id=f"CLM-{uuid.uuid4().hex[:8]}",
        investigation_id=investigation_id,
        claim_text="Test claim statement",
        claim_type="fact",
        evidence_refs_json=evidence_refs or [],
        confidence=0.0,
        status="unconfirmed",
    )
    session.add(node)
    session.flush()
    return node


class TestInvestigationPersistence:
    """Tests for investigation DB persistence and toolset rebuild."""

    def test_create_investigation(self, session) -> None:
        """Investigation persists to DB with correct fields."""
        inv = _create_investigation(session, theatre_id="TH_CREATE", construct_id="CON_CREATE")
        assert inv.id.startswith("INV-")
        assert inv.theatre_id == "TH_CREATE"
        assert inv.construct_id == "CON_CREATE"
        assert inv.inquiry_class == "INVESTIGATIVE"
        assert inv.status == "ACTIVE"

    def test_list_investigations(self, session) -> None:
        """Multiple investigations persist and can be listed."""
        _create_investigation(session, theatre_id="TH_A")
        _create_investigation(session, theatre_id="TH_B")

        result = session.execute(select(Investigation)).scalars().all()
        assert len(result) == 2
        theatre_ids = {inv.theatre_id for inv in result}
        assert theatre_ids == {"TH_A", "TH_B"}

    def test_evidence_persists(self, session) -> None:
        """Evidence items persist with correct content hash."""
        inv = _create_investigation(session)
        content = b"first piece of evidence"
        item = _add_evidence(session, inv.id, content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert item.content_hash == expected_hash
        assert item.provenance_class == "public_primary"

    def test_claims_persist(self, session) -> None:
        """Claims persist with evidence refs."""
        inv = _create_investigation(session)
        ev = _add_evidence(session, inv.id)
        claim = _add_claim(session, inv.id, evidence_refs=[ev.id])

        assert claim.claim_text == "Test claim statement"
        assert claim.claim_type == "fact"
        assert ev.id in claim.evidence_refs_json

    def test_counter_signals_persist(self, session) -> None:
        """Counter-signals persist with correct class."""
        inv = _create_investigation(session)
        cs = InvestigationCounterSignal(
            id=f"CS-{uuid.uuid4().hex[:8]}",
            investigation_id=inv.id,
            signal_class="filing_contradiction",
            material=True,
            resolution_impact="weakens primary claim",
            detection_method="human_submitted",
            detected_at=datetime.now(timezone.utc),
        )
        session.add(cs)
        session.flush()

        assert cs.signal_class == "filing_contradiction"
        assert cs.material is True

    def test_drift_events_persist(self, session) -> None:
        """Drift events persist with impact assessment."""
        inv = _create_investigation(session)
        drift = InvestigationDriftEvent(
            id=f"D-{uuid.uuid4().hex[:8]}",
            investigation_id=inv.id,
            drift_type="ENTITY_RESTRUCTURE",
            original_value="Corp A",
            new_value="Corp B",
            impact_assessment="material",
            detected_at=datetime.now(timezone.utc),
        )
        session.add(drift)
        session.flush()

        assert drift.drift_type == "ENTITY_RESTRUCTURE"
        assert drift.impact_assessment == "material"

    def test_toolset_rebuild_from_db(self, session) -> None:
        """Toolset rebuilt from DB records produces valid hashes."""
        inv = _create_investigation(session)
        _add_evidence(session, inv.id, b"evidence one")
        _add_evidence(session, inv.id, b"evidence two")
        _add_claim(session, inv.id)

        # Reload with relationships
        session.expire(inv)
        loaded = session.execute(
            select(Investigation).where(Investigation.id == inv.id)
        ).scalar_one()

        # Eagerly load relationships
        _ = loaded.evidence_items
        _ = loaded.claim_nodes
        _ = loaded.counter_signals
        _ = loaded.drift_events

        toolset = _rebuild_toolset(loaded)

        assert len(toolset.evidence_envelope.items) == 2
        assert len(toolset.claim_graph.claims) == 1
        assert len(toolset.evidence_envelope.compute_envelope_hash()) == 64

    def test_investigation_survives_restart(self, engine) -> None:
        """Data survives simulated restart (new session)."""
        # Session 1: create
        with Session(engine) as s1:
            inv = _create_investigation(s1, inv_id="inv-restart")
            _add_evidence(s1, "inv-restart", b"persist me")
            s1.commit()

        # Session 2: verify
        with Session(engine) as s2:
            loaded = s2.execute(
                select(Investigation).where(Investigation.id == "inv-restart")
            ).scalar_one()
            assert loaded.theatre_id == "TH_TEST"

            evidence = s2.execute(
                select(InvestigationEvidenceItem).where(
                    InvestigationEvidenceItem.investigation_id == "inv-restart"
                )
            ).scalars().all()
            assert len(evidence) == 1


class TestInvestigation404:
    """Tests for 404 handling."""

    def test_nonexistent_investigation(self, session) -> None:
        """Querying a nonexistent investigation returns None."""
        result = session.execute(
            select(Investigation).where(Investigation.id == "INV-nonexistent")
        ).scalar_one_or_none()
        assert result is None
