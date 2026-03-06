"""
Tests for Cycle-017 Policy Surface — Sprint 0 (Schema Foundation).

4 tests:
1. TheatreCertificate model has all 6 new columns
2. Timeline model has all 3 TAO flow columns
3. Certificate schema serialises with/without 017 fields + is_deployable computed
4. Source registry accepts policy fields
"""

import pytest
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from database.connection import Base
from database.models import (
    User,
    TheatreCertificate,
    Timeline,
    Theatre,
    TheatreTemplate,
)
from schemas.theatre import (
    TheatreCertificateResponse,
    TheatreCertificateSummaryResponse,
)
from osint.models.registry import RegistrySource


# ── Fixtures ──

@pytest.fixture
def engine():
    """In-memory SQLite for schema verification.

    Only creates tables that don't use PostgreSQL-specific types (ARRAY).
    """
    eng = create_engine("sqlite:///:memory:")
    # Create subset of tables needed — skip those with ARRAY columns
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        Theatre.__table__,
        TheatreCertificate.__table__,
    ]
    Base.metadata.create_all(eng, tables=tables)
    yield eng
    Base.metadata.drop_all(eng, tables=tables)
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as sess:
        yield sess


# ── Test 1: TheatreCertificate has 6 new columns ──

def test_theatre_certificate_has_017_columns(engine):
    """Verify all 6 policy columns exist on theatre_certificates table."""
    insp = inspect(engine)
    columns = {c["name"] for c in insp.get_columns("theatre_certificates")}

    expected_017 = {
        "routing_hint",
        "review_reason_code",
        "coherence_review_required",
        "coherence_gate_status",
        "coherence_reviewed_at",
        "coherence_reviewer_id",
    }
    missing = expected_017 - columns
    assert not missing, f"Missing 017 columns on theatre_certificates: {missing}"


# ── Test 2: Timeline has 3 TAO flow columns ──

def test_timeline_has_tao_flow_columns():
    """Verify Timeline model declares TAO flow fields (model-level check).

    We can't create the timelines table in SQLite due to ARRAY columns,
    so we verify at the model/mapper level instead.
    """
    mapper_cols = {c.key for c in Timeline.__table__.columns}

    expected_flow = {"net_inflow_24h", "net_inflow_7d", "flow_updated_at"}
    missing = expected_flow - mapper_cols
    assert not missing, f"Missing TAO flow columns on Timeline model: {missing}"


# ── Test 3: Certificate schema with/without 017 fields + is_deployable ──

def test_certificate_schema_is_deployable():
    """Test is_deployable computed field across different routing/gate states."""
    base = dict(
        id="cert-1",
        theatre_id="t-1",
        template_id="tmpl-1",
        construct_id="c-1",
        criteria_json={},
        scores_json={},
        composite_score=0.75,
        precision=None,
        recall=None,
        brier_score=None,
        ece=None,
        replay_count=10,
        evidence_bundle_hash="abc",
        ground_truth_hash="def",
        construct_version="v1",
        construct_chain_versions=None,
        scorer_version="s1",
        methodology_version="m1",
        dataset_hash="dh1",
        verification_tier="VERIFIED",
        commitment_hash="ch1",
        issued_at=datetime.utcnow(),
        expires_at=None,
        theatre_committed_at=datetime.utcnow(),
        theatre_resolved_at=datetime.utcnow(),
        ground_truth_source="test",
        execution_path="live",
    )

    # No 017 fields → deployable
    resp_default = TheatreCertificateResponse(**base)
    assert resp_default.is_deployable is True
    assert resp_default.routing_hint is None

    # BLOCKED → not deployable
    resp_blocked = TheatreCertificateResponse(**{**base, "routing_hint": "BLOCKED"})
    assert resp_blocked.is_deployable is False

    # REVIEW_REQUIRED + coherence required + PENDING → not deployable
    resp_pending = TheatreCertificateResponse(**{
        **base,
        "routing_hint": "REVIEW_REQUIRED",
        "coherence_review_required": True,
        "coherence_gate_status": "PENDING",
    })
    assert resp_pending.is_deployable is False

    # REVIEW_REQUIRED + coherence required + PASSED → deployable
    resp_passed = TheatreCertificateResponse(**{
        **base,
        "routing_hint": "REVIEW_REQUIRED",
        "coherence_review_required": True,
        "coherence_gate_status": "PASSED",
    })
    assert resp_passed.is_deployable is True

    # Summary response also computes is_deployable
    summary_blocked = TheatreCertificateSummaryResponse(
        id="cert-1",
        theatre_id="t-1",
        construct_id="c-1",
        composite_score=0.75,
        verification_tier="VERIFIED",
        replay_count=10,
        execution_path="live",
        issued_at=datetime.utcnow(),
        routing_hint="BLOCKED",
    )
    assert summary_blocked.is_deployable is False


# ── Test 4: Source registry accepts policy fields ──

def test_source_registry_policy_fields():
    """Verify RegistrySource stores and returns policy fields."""
    source = RegistrySource(
        source_id="polymarket",
        display_name="Polymarket",
        source_group="prediction_market",
        resolution_role="primary_evidence",
        independence_upstream_id="polymarket",
        receipt_mode_minimum="http_transcript",
        query_determinism="pure_id_lookup",
        receipt_body_required=False,
        requires_legal_review=False,
    )
    assert source.query_determinism == "pure_id_lookup"
    assert source.receipt_body_required is False
    assert source.requires_legal_review is False

    # Source with legal review
    legal_source = RegistrySource(
        source_id="private_leak",
        display_name="Private Leak Source",
        source_group="cyber_threat_intel",
        resolution_role="primary_evidence",
        independence_upstream_id="private_leak",
        receipt_mode_minimum="signed_receipt",
        query_determinism="bulk_export",
        receipt_body_required=True,
        requires_legal_review=True,
    )
    assert legal_source.query_determinism == "bulk_export"
    assert legal_source.receipt_body_required is True
    assert legal_source.requires_legal_review is True

    # Default values
    default_source = RegistrySource(
        source_id="basic",
        display_name="Basic",
        source_group="wire_service",
        resolution_role="secondary_corroboration",
        independence_upstream_id="basic",
        receipt_mode_minimum="http_transcript",
    )
    assert default_source.query_determinism is None
    assert default_source.receipt_body_required is False
    assert default_source.requires_legal_review is False
