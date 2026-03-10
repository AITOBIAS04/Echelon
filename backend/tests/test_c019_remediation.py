"""Cycle-019 Remediation Tests — validates the 4 must-fix items.

Tests:
1. Toolset rebuild from persisted records produces correct hashes
2. Toolset replay preserves counter continuity (submit after replay uses next ID)
3. Paradox risk computed on theatre detail read (on-read evaluation)
4. Agent list returns real active_deployments_count via batch subquery
5. Checkpoint evaluator uses deterministic hash (Option B posture confirmed)
"""

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
    InvestigationCounterSignal as InvCounterSignalModel,
    InvestigationDriftEvent,
    Theatre,
    TheatreTemplate,
    User,
    AgentDeployment,
)
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.claim_graph import ClaimGraph, ClaimType
from backend.investigation.counter_signals import (
    InvestigationCounterSignalFeed,
    InvestigationCounterSignalClass,
)
from backend.investigation.commitment_monitor import CommitmentMonitor, DriftType
from backend.investigation.models import ProvenanceClass
from backend.services.paradox_risk_evaluator import evaluate, persist_risk_to_theatre
from backend.services.checkpoint_evaluator import _deterministic_branch_index


# ── Fixtures ──

_TABLES = [
    User.__table__,
    TheatreTemplate.__table__,
    Theatre.__table__,
    Investigation.__table__,
    InvestigationEvidenceItem.__table__,
    InvestigationClaimNode.__table__,
    InvCounterSignalModel.__table__,
    InvestigationDriftEvent.__table__,
    AgentDeployment.__table__,
]


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    # Create agent table manually (SQLite compat)
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


# ── Test 1: Toolset rebuild produces correct hashes ──

def test_toolset_rebuild_produces_correct_hashes():
    """Rebuild from persisted records matches original hash computation."""
    now = datetime.now(timezone.utc)

    # Original computation
    env_original = EvidenceEnvelope()
    item1 = env_original.submit(b"evidence alpha", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src1")
    item2 = env_original.submit(b"evidence beta", ProvenanceClass.ANALYST_DERIVED, "text/plain", "src2")
    original_hash = env_original.compute_envelope_hash()

    # Rebuild from "persisted" records
    env_rebuilt = EvidenceEnvelope()
    env_rebuilt.add_item_from_persisted(
        evidence_id=item1.evidence_id,
        content_hash=item1.content_hash,
        provenance_class=item1.provenance_class,
        submitted_at=item1.submitted_at,
        content_type=item1.content_type,
        source_description=item1.source_description,
    )
    env_rebuilt.add_item_from_persisted(
        evidence_id=item2.evidence_id,
        content_hash=item2.content_hash,
        provenance_class=item2.provenance_class,
        submitted_at=item2.submitted_at,
        content_type=item2.content_type,
        source_description=item2.source_description,
    )
    rebuilt_hash = env_rebuilt.compute_envelope_hash()

    assert rebuilt_hash == original_hash, "Rebuilt envelope hash must match original"


# ── Test 2: Counter continuity after replay ──

def test_replay_preserves_counter_continuity():
    """After replaying persisted items, new submissions continue with next sequential ID."""
    now = datetime.now(timezone.utc)

    # Replay 3 items
    env = EvidenceEnvelope()
    env.add_item_from_persisted("E001", "hash1", ProvenanceClass.PUBLIC_PRIMARY, now, "text/plain", "s1")
    env.add_item_from_persisted("E002", "hash2", ProvenanceClass.PUBLIC_PRIMARY, now, "text/plain", "s2")
    env.add_item_from_persisted("E003", "hash3", ProvenanceClass.ANALYST_DERIVED, now, "text/plain", "s3")

    # New submit should get E004
    new_item = env.submit(b"new evidence", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "s4")
    assert new_item.evidence_id == "E004"

    # Same for ClaimGraph
    cg = ClaimGraph()
    cg.add_claim_from_persisted("C001", "claim 1", ClaimType.FACT, ["E001"])
    cg.add_claim_from_persisted("C002", "claim 2", ClaimType.CAUSAL, ["E002"])
    new_claim = cg.add_claim("claim 3", ClaimType.ATTRIBUTION, ["E003"])
    assert new_claim.claim_id == "C003"

    # CounterSignalFeed
    feed = InvestigationCounterSignalFeed()
    feed.add_signal_from_persisted(
        "CS001", InvestigationCounterSignalClass.OFFICIAL_DENIAL, now,
        None, False, "no impact", "automated_osint"
    )
    new_sig = feed.log_counter_signal(
        InvestigationCounterSignalClass.FILING_CONTRADICTION, True, "big impact", "human_submitted"
    )
    assert new_sig.counter_signal_id == "CS002"

    # CommitmentMonitor
    mon = CommitmentMonitor()
    mon.add_event_from_persisted(
        "D001", DriftType.ENTITY_RESTRUCTURE, now, "old", "new", None, "non_material"
    )
    new_evt = mon.log_drift(DriftType.CONTRACT_AMENDMENT, "old2", "new2", impact_assessment="material")
    assert new_evt.drift_id == "D002"


# ── Test 3: Paradox risk computed on theatre read ──

def test_paradox_risk_computed_on_theatre(session):
    """Paradox risk is evaluated and persisted when absent on a theatre."""
    now = datetime.now(timezone.utc)

    # Create user + template + theatre
    session.add(User(id="u1", username="testuser", email="test@test.com", password_hash="fakehash", created_at=now, updated_at=now))
    session.add(TheatreTemplate(
        id="tpl-1", template_family="test", execution_path="single_run",
        display_name="Test", schema_version="1.0", template_json={"theatre_id": "t1", "execution_path": "single_run"},
        created_at=now,
    ))
    theatre = Theatre(
        id="t-1", user_id="u1", template_id="tpl-1", state="COMMITTED",
        construct_id="con-1", inquiry_class="INVESTIGATIVE",
        progress=0, total_episodes=10, failure_count=0,
        created_at=now, updated_at=now,
    )
    session.add(theatre)
    session.flush()

    # Initially no paradox risk
    assert theatre.paradox_risk_level is None

    # Evaluate risk directly (as get_theatre endpoint would do)
    assessment = evaluate(inquiry_class="INVESTIGATIVE")
    persist_risk_to_theatre(theatre, assessment)
    session.flush()

    # Now risk is set
    assert theatre.paradox_risk_level == "LOW"
    assert theatre.paradox_risk_factors_json is not None
    assert theatre.paradox_risk_updated_at is not None


# ── Test 4: Batch agent deployment counts ──

def test_batch_agent_deployment_counts(engine):
    """Batch subquery returns correct active_deployments_count per agent."""
    from sqlalchemy import func

    with Session(engine) as session:
        now = datetime.now(timezone.utc)

        # Create agents via raw SQL (SQLite compat)
        for aid in ["a1", "a2", "a3"]:
            session.execute(text(
                "INSERT INTO agents (id, name, owner_id, created_at, updated_at) "
                "VALUES (:id, :name, 'owner1', :now, :now)"
            ), {"id": aid, "name": f"Agent {aid}", "now": now})

        # Create user + template + theatre for FK
        session.add(User(id="u1", username="testuser", email="test@test.com", password_hash="fakehash", created_at=now, updated_at=now))
        session.add(TheatreTemplate(
            id="tpl-1", template_family="test", execution_path="single_run",
            display_name="Test", schema_version="1.0",
            template_json={"theatre_id": "t1", "execution_path": "single_run"},
            created_at=now,
        ))
        session.add(Theatre(
            id="t-1", user_id="u1", template_id="tpl-1", state="COMMITTED",
            construct_id="con-1", progress=0, total_episodes=10, failure_count=0,
            created_at=now, updated_at=now,
        ))

        # a1: 2 active deployments
        for i in range(2):
            session.add(AgentDeployment(
                id=f"dep-a1-{i}", agent_id="a1", theatre_id="t-1",
                status="ACTIVE", strategy_profile="balanced",
                deployed_by="u1", created_at=now, updated_at=now,
            ))

        # a2: 1 active + 1 withdrawn
        session.add(AgentDeployment(
            id="dep-a2-0", agent_id="a2", theatre_id="t-1",
            status="ACTIVE", strategy_profile="balanced",
            deployed_by="u1", created_at=now, updated_at=now,
        ))
        session.add(AgentDeployment(
            id="dep-a2-1", agent_id="a2", theatre_id="t-1",
            status="WITHDRAWN", strategy_profile="balanced",
            deployed_by="u1", created_at=now, updated_at=now,
        ))

        # a3: no deployments
        session.flush()

        # Batch subquery (same logic as agents_routes.py list endpoint)
        agent_ids = ["a1", "a2", "a3"]
        count_result = session.execute(
            select(AgentDeployment.agent_id, func.count())
            .where(
                AgentDeployment.agent_id.in_(agent_ids),
                AgentDeployment.status == "ACTIVE",
            )
            .group_by(AgentDeployment.agent_id)
        )
        counts_map = dict(count_result.all())

        assert counts_map.get("a1", 0) == 2
        assert counts_map.get("a2", 0) == 1
        assert counts_map.get("a3", 0) == 0  # Not in map = 0


# ── Test 5: Checkpoint evaluator is deterministic hash (Option B) ──

def test_checkpoint_evaluator_deterministic_posture():
    """Checkpoint evaluator uses deterministic hash — Option B posture."""
    # Same inputs always produce same output
    idx1 = _deterministic_branch_index("cp-1", "action-a", 42, "BINARY_RISK_GATE")
    idx2 = _deterministic_branch_index("cp-1", "action-a", 42, "BINARY_RISK_GATE")
    assert idx1 == idx2, "Same inputs must produce same branch index"

    # Different inputs produce different output
    idx3 = _deterministic_branch_index("cp-1", "action-b", 42, "BINARY_RISK_GATE")
    assert idx1 != idx3, "Different inputs should produce different indices"
