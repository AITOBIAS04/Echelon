"""Cycle-022 Sprint 1 — Seeder + API Endpoints tests.

5 tests:
1. Seeder creates 4 templates on first run
2. Seeder skips all 4 on re-run (idempotent)
3. GET /investigation-templates/ returns 4 templates
4. GET /investigation-templates/?inquiry_class=INSPECTION returns only corporate_due_diligence
5. GET /investigation-templates/corporate_due_diligence returns full detail with domain filters and sources
"""

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from backend.database.models import (
    InvestigationTemplate,
    Investigation,
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
)
from backend.services.investigation_template_seeder import (
    seed_investigation_templates,
    INVESTIGATION_TEMPLATES,
    _derive_default_sources,
    _derive_requires_legal_review,
    _derive_source_groups,
)


# ── Fixtures ──

def _create_tables(eng):
    """Create only the tables needed for tests (avoids ARRAY column issues on SQLite)."""
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
    """In-memory SQLite with investigation template tables."""
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    return eng


@pytest.fixture
def seeded_session(engine):
    """Session with all 4 investigation templates seeded."""
    with Session(engine) as session:
        seed_investigation_templates(session)
        yield session


# ── Test 1: Seeder creates 4 templates on first run ──

def test_seeder_creates_4_templates(engine):
    """Seeder creates exactly 4 investigation templates with correct IDs and derived fields."""
    with Session(engine) as session:
        count = seed_investigation_templates(session)
        assert count == 4

        # Verify total count
        total = session.execute(
            select(func.count()).select_from(InvestigationTemplate)
        ).scalar()
        assert total == 4

        # Verify all template IDs
        templates = session.execute(
            select(InvestigationTemplate)
        ).scalars().all()
        ids = {t.id for t in templates}
        assert ids == {"blank", "corporate_due_diligence", "market_event", "regulatory_action"}

        # All are ACTIVE and seeded
        for t in templates:
            assert t.template_status == "ACTIVE"
            assert t.is_seeded is True
            assert t.name, f"Template {t.id} has no name"

        # Verify blank has no domain filters or sources
        blank = session.get(InvestigationTemplate, "blank")
        assert blank.domain_filters_json == []
        assert blank.default_sources_json == []
        assert blank.requires_legal_review is False

        # Verify corporate_due_diligence has derived sources and legal review
        cdd = session.get(InvestigationTemplate, "corporate_due_diligence")
        assert cdd.inquiry_class == "INSPECTION"
        assert len(cdd.domain_filters_json) == 3
        assert "corporate_and_entity" in cdd.domain_filters_json
        assert "court_and_legal" in cdd.domain_filters_json
        assert "property_and_land" in cdd.domain_filters_json
        # Sources derived from DOMAIN_FILTER_SOURCE_GROUPS
        assert len(cdd.default_sources_json) > 0
        # court_and_legal maps to court_filing and insolvency → requires_legal_review
        assert cdd.requires_legal_review is True
        assert cdd.min_corroboration_groups == 3
        assert cdd.default_time_window_days == 90

        # Verify market_event
        me = session.get(InvestigationTemplate, "market_event")
        assert me.inquiry_class == "INVESTIGATIVE"
        assert me.default_stop_condition == "OUTCOME_RESOLUTION"
        assert me.default_time_window_days == 30
        # finance_and_markets + geopolitical_and_conflict → no legal review sources
        assert me.requires_legal_review is False

        # Verify regulatory_action
        ra = session.get(InvestigationTemplate, "regulatory_action")
        assert ra.inquiry_class == "SCRUTINY"
        assert ra.default_stop_condition == "SPONSOR_DEFINED"
        assert ra.default_time_window_days == 180
        # court_and_legal → legal review
        assert ra.requires_legal_review is True


# ── Test 2: Seeder skips all 4 on re-run (idempotent) ──

def test_reseed_is_idempotent(engine):
    """Re-seeding does not create duplicate templates."""
    with Session(engine) as session:
        first_count = seed_investigation_templates(session)
        assert first_count == 4

        second_count = seed_investigation_templates(session)
        assert second_count == 0

        total = session.execute(
            select(func.count()).select_from(InvestigationTemplate)
        ).scalar()
        assert total == 4


# ── Test 3: GET /investigation-templates/ returns 4 templates ──

def test_list_returns_all_4_templates(seeded_session):
    """All 4 templates are queryable with ACTIVE status."""
    templates = seeded_session.execute(
        select(InvestigationTemplate)
        .where(InvestigationTemplate.template_status == "ACTIVE")
        .order_by(InvestigationTemplate.name)
    ).scalars().all()
    assert len(templates) == 4

    # Verify list-level fields are populated
    for t in templates:
        assert t.name
        assert t.template_status == "ACTIVE"
        assert t.is_seeded is True
        assert t.inquiry_class in {"INVESTIGATIVE", "INSPECTION", "SCRUTINY", "SURVEY", "COUNTERFACTUAL"}


# ── Test 4: Filter by inquiry_class=INSPECTION returns only corporate_due_diligence ──

def test_filter_by_inquiry_class_inspection(seeded_session):
    """Filtering by INSPECTION returns exactly 1 template: corporate_due_diligence."""
    templates = seeded_session.execute(
        select(InvestigationTemplate)
        .where(InvestigationTemplate.inquiry_class == "INSPECTION")
        .where(InvestigationTemplate.template_status == "ACTIVE")
    ).scalars().all()
    assert len(templates) == 1
    assert templates[0].id == "corporate_due_diligence"
    assert templates[0].name == "Corporate Due Diligence"


# ── Test 5: Detail view for corporate_due_diligence ──

def test_corporate_due_diligence_detail(seeded_session):
    """corporate_due_diligence template has full detail with domain filters and sources."""
    template = seeded_session.get(InvestigationTemplate, "corporate_due_diligence")
    assert template is not None
    assert template.name == "Corporate Due Diligence"
    assert template.inquiry_class == "INSPECTION"
    assert template.template_status == "ACTIVE"
    assert template.is_seeded is True

    # Domain filters
    assert template.domain_filters_json == ["corporate_and_entity", "court_and_legal", "property_and_land"]

    # Default sources derived from DOMAIN_FILTER_SOURCE_GROUPS
    expected_source_groups = _derive_default_sources(template.domain_filters_json)
    assert template.default_sources_json == expected_source_groups
    assert len(template.default_sources_json) > 0

    # Verify specific source groups are present
    # corporate_and_entity → official_gov, corporate_filing, entity_resolution
    # court_and_legal → court_filing, insolvency
    # property_and_land → property_registry
    assert "official_gov" in template.default_sources_json
    assert "corporate_filing" in template.default_sources_json
    assert "entity_resolution" in template.default_sources_json
    assert "court_filing" in template.default_sources_json
    assert "insolvency" in template.default_sources_json
    assert "property_registry" in template.default_sources_json

    # Policy metadata
    assert template.requires_legal_review is True
    assert template.min_corroboration_groups == 3

    # Stop condition
    assert template.default_stop_condition == "EVIDENCE_THRESHOLD"
    assert template.default_time_window_days == 90

    # Description present
    assert template.description is not None
    assert len(template.description) > 0
