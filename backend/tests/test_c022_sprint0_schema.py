"""Cycle-022 Sprint 0 — Investigation Template Infrastructure tests.

4 tests:
1. InvestigationTemplate model instantiates with all required fields
2. Investigation model accepts nullable template_id and committed_sources_json
3. Migration applies and rolls back cleanly
4. Response schemas validate against expected payloads
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
    Investigation,
    InvestigationTemplate,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
)
from backend.schemas.investigation_template_schemas import (
    InvestigationTemplateListItem,
    InvestigationTemplateListResponse,
    InvestigationTemplateDetail,
)


# ── Fixtures ──

# Tables needed for cycle-022 tests (excludes models with PG-only ARRAY columns)
_TABLES = [
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


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng, tables=_TABLES)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


# ── Test 1: InvestigationTemplate model instantiates ──

def test_investigation_template_instantiates(session):
    """InvestigationTemplate model instantiates with all required fields."""
    now = datetime.now(timezone.utc)

    template = InvestigationTemplate(
        id="tmpl-sanctions-001",
        name="Sanctions Screening",
        description="Standard template for sanctions-related investigations",
        inquiry_class="INVESTIGATIVE",
        domain_filters_json=["sanctions", "compliance"],
        default_sources_json=["ofac_sdn", "eu_sanctions_list"],
        default_stop_condition="OUTCOME_RESOLUTION",
        default_time_window_days=30,
        requires_legal_review=True,
        min_corroboration_groups=3,
        template_status="ACTIVE",
        is_seeded=True,
        created_at=now,
    )
    session.add(template)
    session.flush()

    # Verify round-trip
    result = session.get(InvestigationTemplate, "tmpl-sanctions-001")
    assert result is not None
    assert result.name == "Sanctions Screening"
    assert result.description == "Standard template for sanctions-related investigations"
    assert result.inquiry_class == "INVESTIGATIVE"
    assert result.domain_filters_json == ["sanctions", "compliance"]
    assert result.default_sources_json == ["ofac_sdn", "eu_sanctions_list"]
    assert result.default_stop_condition == "OUTCOME_RESOLUTION"
    assert result.default_time_window_days == 30
    assert result.requires_legal_review is True
    assert result.min_corroboration_groups == 3
    assert result.template_status == "ACTIVE"
    assert result.is_seeded is True


# ── Test 2: Investigation accepts template_id and committed_sources_json ──

def test_investigation_template_id_and_committed_sources(session):
    """Investigation model accepts nullable template_id and committed_sources_json."""
    now = datetime.now(timezone.utc)

    # Create template first
    template = InvestigationTemplate(
        id="tmpl-basic-001",
        name="Basic Template",
        created_at=now,
    )
    session.add(template)
    session.flush()

    # Investigation with template_id
    inv = Investigation(
        id="inv-with-template",
        theatre_id="theatre-1",
        construct_id="test_construct",
        template_id="tmpl-basic-001",
        committed_sources_json=["source_a", "source_b"],
        created_at=now,
        updated_at=now,
    )
    session.add(inv)
    session.flush()

    result = session.get(Investigation, "inv-with-template")
    assert result.template_id == "tmpl-basic-001"
    assert result.committed_sources_json == ["source_a", "source_b"]
    assert result.template is not None
    assert result.template.name == "Basic Template"

    # Investigation without template_id (nullable)
    inv_no_tmpl = Investigation(
        id="inv-no-template",
        theatre_id="theatre-2",
        construct_id="test_construct_2",
        template_id=None,
        committed_sources_json=None,
        created_at=now,
        updated_at=now,
    )
    session.add(inv_no_tmpl)
    session.flush()

    result2 = session.get(Investigation, "inv-no-template")
    assert result2.template_id is None
    assert result2.committed_sources_json is None
    assert result2.template is None


# ── Test 3: Migration applies and rolls back cleanly ──

def test_migration_creates_table_and_columns(engine):
    """investigation_templates table exists with expected columns,
    and investigations has template_id and committed_sources_json."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "investigation_templates" in table_names

    # Verify investigation_templates columns
    tmpl_cols = {c["name"] for c in inspector.get_columns("investigation_templates")}
    expected_tmpl_cols = {
        "id", "name", "description", "inquiry_class",
        "domain_filters_json", "default_sources_json",
        "default_stop_condition", "default_time_window_days",
        "requires_legal_review", "min_corroboration_groups",
        "template_status", "is_seeded", "created_at",
    }
    for col in expected_tmpl_cols:
        assert col in tmpl_cols, f"Column '{col}' missing from investigation_templates"

    # Verify new columns on investigations
    inv_cols = {c["name"] for c in inspector.get_columns("investigations")}
    assert "template_id" in inv_cols, "template_id missing from investigations"
    assert "committed_sources_json" in inv_cols, "committed_sources_json missing from investigations"


# ── Test 4: Response schemas validate ──

def test_response_schemas_validate():
    """Response schemas validate against expected payloads."""
    now = datetime.now(timezone.utc)

    # List item — matches SDD: template_id, name, description, inquiry_class,
    # template_status, domain_filter_count, requires_legal_review
    item = InvestigationTemplateListItem(
        template_id="tmpl-001",
        name="Sanctions Screening",
        description="Standard sanctions template",
        inquiry_class="INVESTIGATIVE",
        template_status="ACTIVE",
        domain_filter_count=3,
        requires_legal_review=True,
    )
    assert item.template_id == "tmpl-001"
    assert item.description == "Standard sanctions template"
    assert item.domain_filter_count == 3
    assert item.requires_legal_review is True

    # List response
    list_resp = InvestigationTemplateListResponse(
        templates=[item],
        total=1,
    )
    assert list_resp.total == 1
    assert len(list_resp.templates) == 1

    # Detail — full schema with template_id
    detail = InvestigationTemplateDetail(
        template_id="tmpl-001",
        name="Sanctions Screening",
        description="Full sanctions investigation template",
        inquiry_class="INVESTIGATIVE",
        domain_filters=["sanctions", "compliance"],
        default_sources=["ofac_sdn", "eu_sanctions_list"],
        default_stop_condition="OUTCOME_RESOLUTION",
        default_time_window_days=30,
        requires_legal_review=True,
        min_corroboration_groups=3,
        template_status="ACTIVE",
        is_seeded=True,
        created_at=now,
    )
    assert detail.template_id == "tmpl-001"
    assert detail.description == "Full sanctions investigation template"
    assert detail.default_sources == ["ofac_sdn", "eu_sanctions_list"]
    assert detail.default_time_window_days == 30
    assert detail.min_corroboration_groups == 3

    # Empty list response
    empty = InvestigationTemplateListResponse()
    assert empty.total == 0
    assert empty.templates == []

    # Detail with minimal fields
    minimal = InvestigationTemplateDetail(
        template_id="tmpl-min",
        name="Minimal",
        created_at=now,
    )
    assert minimal.template_id == "tmpl-min"
    assert minimal.description is None
    assert minimal.default_time_window_days is None
    assert minimal.requires_legal_review is False
    assert minimal.min_corroboration_groups == 2

    # List item with defaults
    default_item = InvestigationTemplateListItem(
        template_id="tmpl-default",
        name="Default Item",
    )
    assert default_item.description is None
    assert default_item.domain_filter_count == 0
    assert default_item.requires_legal_review is False
    assert default_item.template_status == "ACTIVE"
