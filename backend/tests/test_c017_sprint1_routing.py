"""
Tests for Cycle-017 Sprint 1 — Deployability Routing.

8 tests:
1. Score below block threshold → BLOCKED + reason code
2. INVESTIGATIVE inquiry class + good score → REVIEW_REQUIRED
3. REJECTED tier → BLOCKED regardless of score
4. Good score + COUNTERFACTUAL → ALLOWED
5. Certificate issuance produces routing_hint (pipeline integration)
6. Audit event logged with correct detail_json
7. API filter: routing_hint query parameter works
8. DRAFT tier → REVIEW_REQUIRED (review tier rule)
"""

import pytest
import uuid
from datetime import datetime

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from services.routing_evaluator import (
    RoutingEvaluator,
    RoutingHint,
    RoutingPolicy,
    RoutingDecision,
)
from database.connection import Base
from database.models import (
    User,
    TheatreCertificate,
    TheatreAuditEvent,
    Theatre,
    TheatreTemplate,
)


# ── Fixtures ──

@pytest.fixture
def evaluator():
    return RoutingEvaluator()


@pytest.fixture
def engine():
    """In-memory SQLite for query tests."""
    eng = create_engine("sqlite:///:memory:")
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        Theatre.__table__,
        TheatreCertificate.__table__,
        TheatreAuditEvent.__table__,
    ]
    Base.metadata.create_all(eng, tables=tables)
    yield eng
    Base.metadata.drop_all(eng, tables=tables)
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as sess:
        yield sess


# ── Test 1: Score below block threshold → BLOCKED ──

def test_score_below_block_threshold(evaluator):
    """Score < 0.3 → BLOCKED with reason code."""
    decision = evaluator.evaluate(
        composite_score=0.2,
        verification_tier="VERIFIED",
        inquiry_class="COUNTERFACTUAL",
    )
    assert decision.hint == RoutingHint.BLOCKED
    assert "0.3" in decision.reason_code
    assert decision.rule_name == "block_threshold"


# ── Test 2: INVESTIGATIVE + good score → REVIEW_REQUIRED ──

def test_investigative_good_score_review_required(evaluator):
    """INVESTIGATIVE inquiry class triggers review regardless of good score."""
    decision = evaluator.evaluate(
        composite_score=0.85,
        verification_tier="VERIFIED",
        inquiry_class="INVESTIGATIVE",
    )
    assert decision.hint == RoutingHint.REVIEW_REQUIRED
    assert "investigative" in decision.reason_code
    assert decision.rule_name == "always_review_inquiry_class"


# ── Test 3: REJECTED tier → BLOCKED regardless of score ──

def test_rejected_tier_blocked(evaluator):
    """REJECTED tier → BLOCKED even with perfect score."""
    decision = evaluator.evaluate(
        composite_score=1.0,
        verification_tier="REJECTED",
        inquiry_class="COUNTERFACTUAL",
    )
    assert decision.hint == RoutingHint.BLOCKED
    assert "rejected" in decision.reason_code
    assert decision.rule_name == "blocked_tier"


# ── Test 4: Good score + COUNTERFACTUAL → ALLOWED ──

def test_good_score_counterfactual_allowed(evaluator):
    """Good score with default inquiry class → ALLOWED."""
    decision = evaluator.evaluate(
        composite_score=0.85,
        verification_tier="VERIFIED",
        inquiry_class="COUNTERFACTUAL",
    )
    assert decision.hint == RoutingHint.ALLOWED
    assert decision.reason_code == "default_pass"
    assert decision.rule_name == "default"


# ── Test 5: Certificate with routing_hint persisted ──

def test_certificate_routing_hint_persisted(session):
    """Certificate with routing_hint can be stored and read back."""
    cert_id = str(uuid.uuid4())
    now = datetime.utcnow()

    cert = TheatreCertificate(
        id=cert_id,
        theatre_id="t-test",
        template_id="tmpl-test",
        construct_id="c-test",
        inquiry_class="COUNTERFACTUAL",
        criteria_json={},
        scores_json={},
        composite_score=0.75,
        replay_count=10,
        evidence_bundle_hash="abc",
        ground_truth_hash="def",
        construct_version="v1",
        scorer_version="s1",
        methodology_version="m1",
        dataset_hash="dh1",
        verification_tier="VERIFIED",
        commitment_hash="ch1",
        issued_at=now,
        theatre_committed_at=now,
        theatre_resolved_at=now,
        ground_truth_source="test",
        execution_path="live",
        routing_hint="ALLOWED",
        review_reason_code="default_pass",
    )
    session.add(cert)
    session.flush()

    loaded = session.get(TheatreCertificate, cert_id)
    assert loaded.routing_hint == "ALLOWED"
    assert loaded.review_reason_code == "default_pass"


# ── Test 6: Audit event with ROUTING_DECISION ──

def test_routing_audit_event(session):
    """Audit event can be created with ROUTING_DECISION type."""
    event = TheatreAuditEvent(
        id=str(uuid.uuid4()),
        theatre_id="t-test",
        event_type="ROUTING_DECISION",
        detail_json={
            "certificate_id": "cert-1",
            "routing_hint": "REVIEW_REQUIRED",
            "reason_code": "score_below_0.6",
            "rule_name": "review_threshold",
        },
    )
    session.add(event)
    session.flush()

    loaded = session.get(TheatreAuditEvent, event.id)
    assert loaded.event_type == "ROUTING_DECISION"
    assert loaded.detail_json["routing_hint"] == "REVIEW_REQUIRED"
    assert loaded.detail_json["rule_name"] == "review_threshold"


# ── Test 7: API filter query (DB-level) ──

def test_routing_hint_filter_query(session):
    """Certificates can be filtered by routing_hint."""
    now = datetime.utcnow()
    base = dict(
        template_id="tmpl-test",
        construct_id="c-test",
        inquiry_class="COUNTERFACTUAL",
        criteria_json={},
        scores_json={},
        composite_score=0.75,
        replay_count=10,
        evidence_bundle_hash="abc",
        ground_truth_hash="def",
        construct_version="v1",
        scorer_version="s1",
        methodology_version="m1",
        dataset_hash="dh1",
        verification_tier="VERIFIED",
        commitment_hash="ch1",
        issued_at=now,
        theatre_committed_at=now,
        theatre_resolved_at=now,
        ground_truth_source="test",
        execution_path="live",
    )

    session.add(TheatreCertificate(id="c1", theatre_id="t1", routing_hint="ALLOWED", **base))
    session.add(TheatreCertificate(id="c2", theatre_id="t2", routing_hint="BLOCKED", **base))
    session.add(TheatreCertificate(id="c3", theatre_id="t3", routing_hint="REVIEW_REQUIRED", **base))
    session.flush()

    # Filter for BLOCKED
    result = session.execute(
        select(TheatreCertificate).where(TheatreCertificate.routing_hint == "BLOCKED")
    )
    blocked = result.scalars().all()
    assert len(blocked) == 1
    assert blocked[0].id == "c2"

    # Filter for REVIEW_REQUIRED
    result = session.execute(
        select(TheatreCertificate).where(TheatreCertificate.routing_hint == "REVIEW_REQUIRED")
    )
    review = result.scalars().all()
    assert len(review) == 1
    assert review[0].id == "c3"


# ── Test 8: DRAFT tier → REVIEW_REQUIRED ──

def test_draft_tier_review_required(evaluator):
    """DRAFT tier → REVIEW_REQUIRED via review_tier rule."""
    decision = evaluator.evaluate(
        composite_score=0.85,
        verification_tier="DRAFT",
        inquiry_class="COUNTERFACTUAL",
    )
    assert decision.hint == RoutingHint.REVIEW_REQUIRED
    assert "draft" in decision.reason_code
    assert decision.rule_name == "review_tier"
