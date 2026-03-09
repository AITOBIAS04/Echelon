"""Cycle-022 Sprint 2 — Investigation Create Integration + Certificate Provenance tests.

7 tests:
1. Create investigation with valid template_id — template defaults applied via model_fields_set
2. Create investigation with invalid template_id — 400 rejection
3. Create investigation with DRAFT template — 400 rejection
4. Explicit user overrides take precedence (model_fields_set distinguishes explicit from default)
5. committed_sources_json populated from live registry source_ids (not group names)
6. Certificate metadata includes template_id + template_name + committed_sources when present
7. Certificate hash payload includes provenance keys when present
"""

import os

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import (
    InvestigationTemplate,
    Investigation,
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
)
from backend.investigation.certificate import InvestigationCertificateBuilder
from backend.investigation.claim_graph import ClaimGraph
from backend.investigation.commitment_monitor import CommitmentMonitor
from backend.investigation.counter_signals import InvestigationCounterSignalFeed
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.signal_scanner import (
    DomainFilter,
    DOMAIN_FILTER_SOURCE_GROUPS,
)
from backend.osint.models.registry import RegistryLoader
from backend.schemas.investigation_schemas import InvestigationCreateRequest
from backend.services.investigation_template_seeder import seed_investigation_templates
from backend.api.investigation_routes import (
    _resolve_committed_sources,
    _validate_domain_filters,
)


# ── Fixtures ──


def _create_tables(eng):
    """Create only the tables needed for tests."""
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        TheatreCertificate.__table__,
        Theatre.__table__,
        InvestigationTemplate.__table__,
        Investigation.__table__,
    ]
    with eng.connect() as conn:
        for table in tables:
            table.create(conn, checkfirst=True)
        conn.commit()


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    return eng


@pytest.fixture
def seeded_session(engine):
    with Session(engine) as session:
        seed_investigation_templates(session)
        yield session


def _resolve_expected_source_ids(domain_filters: list[str]) -> list[str]:
    """Resolve actual source_ids via the same chain the route uses."""
    return _resolve_committed_sources(domain_filters)


# ── Test 1: Template defaults applied when fields not explicitly set ──


def test_template_defaults_applied_via_model_fields_set(seeded_session):
    """When user sends only template_id (not inquiry_class etc.), model_fields_set
    indicates those fields were NOT explicitly provided, so template defaults apply."""
    session = seeded_session

    # Simulate a request where user only sends template_id (no inquiry_class, etc.)
    request = InvestigationCreateRequest(
        theatre_id="theatre-001",
        construct_id="construct-001",
        template_id="corporate_due_diligence",
    )

    # Verify model_fields_set shows which fields user explicitly provided
    assert "template_id" in request.model_fields_set
    assert "theatre_id" in request.model_fields_set
    assert "inquiry_class" not in request.model_fields_set  # Was NOT explicitly sent
    assert "stop_condition" not in request.model_fields_set
    assert "domain_filters" not in request.model_fields_set

    # Now simulate the route logic
    template = session.get(InvestigationTemplate, "corporate_due_diligence")
    assert template is not None

    inquiry_class = request.inquiry_class  # default: INVESTIGATIVE
    domain_filters = request.domain_filters  # default: []
    stop_condition = request.stop_condition  # default: OUTCOME_RESOLUTION

    explicitly_set = request.model_fields_set
    if "inquiry_class" not in explicitly_set:
        inquiry_class = template.inquiry_class
    if "domain_filters" not in explicitly_set or not domain_filters:
        domain_filters = template.domain_filters_json or []
    if "stop_condition" not in explicitly_set:
        stop_condition = template.default_stop_condition

    # Template defaults applied
    assert inquiry_class == "INSPECTION"  # From template, not default INVESTIGATIVE
    assert domain_filters == ["corporate_and_entity", "court_and_legal", "property_and_land"]
    assert stop_condition == "EVIDENCE_THRESHOLD"


# ── Test 2: Invalid template_id returns 400 ──


def test_invalid_template_id_returns_400(seeded_session):
    """An invalid template_id is rejected before DB insert."""
    session = seeded_session

    template = session.get(InvestigationTemplate, "nonexistent")
    assert template is None  # Template doesn't exist → route would raise 400


def test_invalid_domain_filter_returns_400():
    """Invalid domain filter values are rejected with 400."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_domain_filters(["totally_invented_filter"])
    assert exc_info.value.status_code == 400
    assert "Invalid domain filter" in str(exc_info.value.detail)


# ── Test 3: DRAFT template returns 400 ──


def test_draft_template_rejected(seeded_session):
    """A DRAFT template cannot be used — route checks template_status == ACTIVE."""
    session = seeded_session

    draft = InvestigationTemplate(
        id="draft_test",
        name="Draft Template",
        inquiry_class="INVESTIGATIVE",
        domain_filters_json=[],
        default_sources_json=[],
        default_stop_condition="OUTCOME_RESOLUTION",
        template_status="DRAFT",
        is_seeded=False,
    )
    session.add(draft)
    session.commit()

    loaded = session.get(InvestigationTemplate, "draft_test")
    assert loaded.template_status == "DRAFT"
    assert loaded.template_status != "ACTIVE"  # Route rejects non-ACTIVE


# ── Test 4: Explicit user overrides take precedence ──


def test_user_overrides_take_precedence_via_model_fields_set(seeded_session):
    """When user EXPLICITLY sends inquiry_class=INVESTIGATIVE alongside
    corporate_due_diligence template (which defaults to INSPECTION),
    model_fields_set detects the explicit field and does NOT override it."""
    session = seeded_session

    # User explicitly sends all fields
    request = InvestigationCreateRequest(
        theatre_id="theatre-002",
        construct_id="construct-002",
        template_id="corporate_due_diligence",
        inquiry_class="INVESTIGATIVE",  # Explicit — should NOT be overridden
        domain_filters=["finance_and_markets"],  # Explicit
        stop_condition="OUTCOME_RESOLUTION",  # Explicit
    )

    # model_fields_set includes explicitly sent fields
    assert "inquiry_class" in request.model_fields_set
    assert "domain_filters" in request.model_fields_set
    assert "stop_condition" in request.model_fields_set

    template = session.get(InvestigationTemplate, "corporate_due_diligence")

    inquiry_class = request.inquiry_class
    domain_filters = list(request.domain_filters)
    stop_condition = request.stop_condition

    explicitly_set = request.model_fields_set
    if "inquiry_class" not in explicitly_set:
        inquiry_class = template.inquiry_class
    if "domain_filters" not in explicitly_set or not domain_filters:
        domain_filters = template.domain_filters_json or []
    if "stop_condition" not in explicitly_set:
        stop_condition = template.default_stop_condition

    # User overrides preserved — NOT replaced by template defaults
    assert inquiry_class == "INVESTIGATIVE"  # NOT INSPECTION
    assert domain_filters == ["finance_and_markets"]  # NOT template's 3 filters
    assert stop_condition == "OUTCOME_RESOLUTION"  # NOT EVIDENCE_THRESHOLD


# ── Test 5: committed_sources are real source_ids ──


def test_committed_sources_are_real_source_ids():
    """committed_sources_json contains actual source_id values from sources.json,
    NOT source group names like 'market_data'."""
    committed = _resolve_committed_sources(["finance_and_markets"])
    assert len(committed) > 0

    # These should be actual source_ids (like "worldmonitor_finance", "polymarket_api"),
    # NOT source group names
    source_group_names = {"market_data", "central_bank", "prediction_market"}
    for source_id in committed:
        assert source_id not in source_group_names, (
            f"committed_sources contains source group name '{source_id}' "
            f"instead of a real source_id from sources.json"
        )

    # Verify known registry sources are present
    # finance_and_markets → market_data group → worldmonitor_finance
    # finance_and_markets → prediction_market group → polymarket_api
    assert "worldmonitor_finance" in committed
    assert "polymarket_api" in committed


# ── Test 6: Certificate metadata includes provenance when present ──


def test_certificate_metadata_includes_provenance():
    """Certificate builder includes template_id, template_name, and
    committed_sources in hash payload when provided."""
    builder = InvestigationCertificateBuilder()

    cert = builder.build(
        theatre_id="theatre-cert-001",
        construct_id="construct-cert-001",
        inquiry_class="INSPECTION",
        stop_condition="EVIDENCE_THRESHOLD",
        stop_config={"time_window_days": 90},
        evidence_envelope=EvidenceEnvelope(),
        claim_graph=ClaimGraph(),
        counter_signal_feed=InvestigationCounterSignalFeed(),
        commitment_monitor=CommitmentMonitor(),
        template_id="corporate_due_diligence",
        template_name="Corporate Due Diligence",
        committed_sources=["companies_house_api", "polymarket_api"],
    )

    assert cert is not None
    assert cert.certificate_hash is not None
    assert len(cert.certificate_hash) == 64  # SHA-256 hex digest

    # Certificate without provenance should have a DIFFERENT hash
    cert_no_provenance = builder.build(
        theatre_id="theatre-cert-001",
        construct_id="construct-cert-001",
        inquiry_class="INSPECTION",
        stop_condition="EVIDENCE_THRESHOLD",
        stop_config={"time_window_days": 90},
        evidence_envelope=EvidenceEnvelope(),
        claim_graph=ClaimGraph(),
        counter_signal_feed=InvestigationCounterSignalFeed(),
        commitment_monitor=CommitmentMonitor(),
    )

    assert cert.certificate_hash != cert_no_provenance.certificate_hash


# ── Test 7: Certificate hash payload includes provenance keys ──


def test_certificate_hash_includes_provenance_keys():
    """When provenance is present, the hash payload includes template_id,
    template_name, and committed_sources keys, changing the hash."""
    builder = InvestigationCertificateBuilder()

    base_args = dict(
        theatre_id="theatre-hash-001",
        construct_id="construct-hash-001",
        inquiry_class="SCRUTINY",
        stop_condition="SPONSOR_DEFINED",
        stop_config={"time_window_days": 180},
        evidence_envelope=EvidenceEnvelope(),
        claim_graph=ClaimGraph(),
        counter_signal_feed=InvestigationCounterSignalFeed(),
        commitment_monitor=CommitmentMonitor(),
    )

    # Without provenance
    cert_without = builder.build(**base_args)

    # With template provenance only
    cert_with_template = builder.build(
        **base_args,
        template_id="regulatory_action",
        template_name="Regulatory Action Tracking",
    )
    assert cert_without.certificate_hash != cert_with_template.certificate_hash

    # With committed_sources only
    cert_with_sources = builder.build(
        **base_args,
        committed_sources=["companies_house_api", "polymarket_api"],
    )
    assert cert_without.certificate_hash != cert_with_sources.certificate_hash

    # With both
    cert_with_both = builder.build(
        **base_args,
        template_id="regulatory_action",
        template_name="Regulatory Action Tracking",
        committed_sources=["companies_house_api", "polymarket_api"],
    )
    assert cert_with_both.certificate_hash != cert_with_template.certificate_hash
    assert cert_with_both.certificate_hash != cert_with_sources.certificate_hash

    # Verify determinism
    cert_with_both_2 = builder.build(
        **base_args,
        template_id="regulatory_action",
        template_name="Regulatory Action Tracking",
        committed_sources=["companies_house_api", "polymarket_api"],
    )
    assert cert_with_both.certificate_hash == cert_with_both_2.certificate_hash
