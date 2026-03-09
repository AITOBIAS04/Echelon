"""Cycle-022 Sprint 2 — Integration tests hitting the real POST /api/v1/investigations/ endpoint.

Tests exercise the actual FastAPI route with async SQLite via dependency override,
so bugs in the production create path (template resolution, model_fields_set, source
resolution) are caught by the test suite.

9 tests:
1. Template defaults applied via real POST — omitted fields get template values
2. Invalid template_id — 400 from real endpoint
3. Invalid domain filter — 400 from real endpoint
4. DRAFT template — 400 from real endpoint
5. Explicit user overrides preserved — even when values match Pydantic defaults
6. Explicit empty domain_filters=[] preserved — NOT overwritten by template defaults
7. Explicit empty stop_config={} preserved — NOT overwritten by template defaults
8. Certificate metadata includes provenance when present
9. Certificate hash payload includes provenance keys
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from backend.database.models import (
    InvestigationTemplate,
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
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
from backend.services.investigation_template_seeder import seed_investigation_templates

# Minimal FastAPI app with just the investigation router + dep override
from fastapi import FastAPI
from backend.api.investigation_routes import router as investigation_router
from backend.dependencies import get_db


# ── Async SQLite fixtures ──


def _enable_sqlite_fk(dbapi_conn, connection_record):
    """Enable foreign keys on SQLite (required for FK constraints)."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Enable FK support
    event.listen(engine.sync_engine, "connect", _enable_sqlite_fk)

    # Create only the tables needed (avoids ARRAY column issues on SQLite)
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        TheatreCertificate.__table__,
        Theatre.__table__,
        InvestigationTemplate.__table__,
        Investigation.__table__,
        InvestigationEvidenceItem.__table__,
        InvestigationClaimNode.__table__,
        InvestigationCounterSignal.__table__,
        InvestigationDriftEvent.__table__,
        InvestigationCertificateRecord.__table__,
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(table.create, checkfirst=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory(async_engine):
    return async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def seeded_app(async_session_factory):
    """FastAPI app with investigation router and seeded templates."""
    # Seed templates using a sync-compatible path through the async session
    async with async_session_factory() as session:
        # Seed templates — the seeder uses sync Session, so we do it manually
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as SyncSession

        sync_engine = create_engine("sqlite:///:memory:")
        tables = [
            User.__table__,
            TheatreTemplate.__table__,
            TheatreCertificate.__table__,
            Theatre.__table__,
            InvestigationTemplate.__table__,
            Investigation.__table__,
        ]
        with sync_engine.connect() as conn:
            for table in tables:
                table.create(conn, checkfirst=True)
            conn.commit()

        with SyncSession(sync_engine) as sync_session:
            seed_investigation_templates(sync_session)

            # Copy seeded templates into async session
            templates = sync_session.query(InvestigationTemplate).all()
            for t in templates:
                sync_session.expunge(t)
                session.add(InvestigationTemplate(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    inquiry_class=t.inquiry_class,
                    domain_filters_json=t.domain_filters_json,
                    default_sources_json=t.default_sources_json,
                    default_stop_condition=t.default_stop_condition,
                    default_time_window_days=t.default_time_window_days,
                    requires_legal_review=t.requires_legal_review,
                    min_corroboration_groups=t.min_corroboration_groups,
                    template_status=t.template_status,
                    is_seeded=t.is_seeded,
                ))

        # Add a DRAFT template for test 4
        session.add(InvestigationTemplate(
            id="draft_test",
            name="Draft Template",
            inquiry_class="INVESTIGATIVE",
            domain_filters_json=[],
            default_sources_json=[],
            default_stop_condition="OUTCOME_RESOLUTION",
            template_status="DRAFT",
            is_seeded=False,
        ))
        await session.commit()

    # Build the app with dep override
    app = FastAPI()
    app.include_router(investigation_router)

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(seeded_app):
    transport = ASGITransport(app=seeded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_read(async_session_factory):
    """Async session for reading back persisted records after POST."""
    async with async_session_factory() as session:
        yield session


# ── Test 1: Template defaults applied via real POST ──


@pytest.mark.asyncio
async def test_template_defaults_applied_via_real_post(client):
    """POST with only template_id — omitted fields get template defaults."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-001",
        "construct_id": "construct-001",
        "template_id": "corporate_due_diligence",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # Template defaults applied: corporate_due_diligence → INSPECTION
    assert data["inquiry_class"] == "INSPECTION"


# ── Test 2: Invalid template_id — 400 from real endpoint ──


@pytest.mark.asyncio
async def test_invalid_template_id_returns_400(client):
    """POST with nonexistent template_id returns 400."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-001",
        "construct_id": "construct-001",
        "template_id": "nonexistent",
    })
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


# ── Test 3: Invalid domain filter — 400 from real endpoint ──


@pytest.mark.asyncio
async def test_invalid_domain_filter_returns_400(client):
    """POST with invalid domain_filters returns 400."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-001",
        "construct_id": "construct-001",
        "domain_filters": ["totally_invented_filter"],
    })
    assert resp.status_code == 400
    assert "Invalid domain filter" in resp.json()["detail"]


# ── Test 4: DRAFT template — 400 from real endpoint ──


@pytest.mark.asyncio
async def test_draft_template_returns_400(client):
    """POST with DRAFT template_id returns 400."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-001",
        "construct_id": "construct-001",
        "template_id": "draft_test",
    })
    assert resp.status_code == 400
    assert "not ACTIVE" in resp.json()["detail"]


# ── Test 5: Explicit user overrides preserved ──


@pytest.mark.asyncio
async def test_explicit_overrides_preserved_via_real_post(client):
    """POST with explicit inquiry_class=INVESTIGATIVE alongside
    corporate_due_diligence template (which defaults to INSPECTION) —
    the explicit value MUST be preserved, not overwritten."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-002",
        "construct_id": "construct-002",
        "template_id": "corporate_due_diligence",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": ["finance_and_markets"],
        "stop_condition": "OUTCOME_RESOLUTION",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # User's explicit INVESTIGATIVE preserved — NOT overwritten to INSPECTION
    assert data["inquiry_class"] == "INVESTIGATIVE"


# ── Test 6: Explicit empty domain_filters=[] preserved ──


@pytest.mark.asyncio
async def test_explicit_empty_domain_filters_preserved(client, db_read):
    """POST with explicit domain_filters=[] alongside a template that has
    3 default filters — the explicit empty list MUST be preserved in the DB."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-003",
        "construct_id": "construct-003",
        "template_id": "corporate_due_diligence",
        "domain_filters": [],
    })
    assert resp.status_code == 201, resp.text
    inv_id = resp.json()["id"]

    # Read persisted record directly from DB
    from sqlalchemy import select as sa_select
    row = (await db_read.execute(
        sa_select(Investigation).where(Investigation.id == inv_id)
    )).scalar_one()

    # domain_filters MUST be empty — NOT overwritten to template's 3 filters
    assert row.domain_filters_json == [], (
        f"Expected empty domain_filters but got {row.domain_filters_json}"
    )
    # committed_sources should be None (no domain filters → no source resolution)
    assert row.committed_sources_json is None

    # stop_condition gets template default since not explicitly set
    assert row.stop_condition == "EVIDENCE_THRESHOLD"
    # stop_config gets template default since not explicitly set
    assert row.stop_config_json == {"time_window_days": 90}


# ── Test 7: Explicit empty stop_config={} preserved ──


@pytest.mark.asyncio
async def test_explicit_empty_stop_config_preserved(client, db_read):
    """POST with explicit stop_config={} alongside a template that has
    default_time_window_days=90 — the explicit empty dict MUST be preserved."""
    resp = await client.post("/api/v1/investigations/", json={
        "theatre_id": "theatre-004",
        "construct_id": "construct-004",
        "template_id": "corporate_due_diligence",
        "stop_config": {},
    })
    assert resp.status_code == 201, resp.text
    inv_id = resp.json()["id"]

    # Read persisted record directly from DB
    from sqlalchemy import select as sa_select
    row = (await db_read.execute(
        sa_select(Investigation).where(Investigation.id == inv_id)
    )).scalar_one()

    # stop_config MUST be empty — NOT overwritten to {"time_window_days": 90}
    assert row.stop_config_json == {}, (
        f"Expected empty stop_config but got {row.stop_config_json}"
    )
    # stop_condition gets template default since not explicitly set
    assert row.stop_condition == "EVIDENCE_THRESHOLD"
    # domain_filters get template defaults since not explicitly set
    assert row.domain_filters_json == ["corporate_and_entity", "court_and_legal", "property_and_land"]


# ── Test 8: Certificate metadata includes provenance ──


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


# ── Test 9: Certificate hash payload includes provenance keys ──


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
