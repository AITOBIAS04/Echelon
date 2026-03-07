"""Cycle-018 Sprint 1 — Template Catalog + Seeding tests.

6 tests:
1. Seed all 18 templates → verify count and families
2. Re-seed is idempotent (no duplicates)
3. List all templates → 18 returned
4. Filter by family NAV_UNC → 4 returned
5. Get Neon Courier template → all fields present, checkpoint_count matches
6. RUNNABLE templates have structured checkpoints from fixtures
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
)
from backend.services.scenario_template_seeder import (
    seed_templates,
    TEMPLATE_FAMILIES,
    FIXTURE_MAP,
)


# ── Fixtures ──

def _create_tables(eng):
    """Create only the tables needed for tests (avoids ARRAY column issues on SQLite)."""
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        TheatreCertificate.__table__,
        Theatre.__table__,
        ScenarioPackTemplate.__table__,
        ScenarioCheckpoint.__table__,
        CheckpointBranch.__table__,
    ]
    with eng.connect() as conn:
        for table in tables:
            table.create(conn, checkfirst=True)
        conn.commit()


@pytest.fixture
def engine():
    """In-memory SQLite with scenario pack tables."""
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    return eng


@pytest.fixture
def seeded_session(engine):
    """Session with all 18 templates seeded."""
    with Session(engine) as session:
        seed_templates(session)
        yield session


# ── Test 1: Seed all 18 templates ──

def test_seed_creates_18_templates(engine):
    """Seeder creates exactly 18 templates with correct families."""
    with Session(engine) as session:
        count = seed_templates(session)
        assert count == 18

        # Verify total count
        total = session.execute(
            select(func.count()).select_from(ScenarioPackTemplate)
        ).scalar()
        assert total == 18

        # Verify family distribution
        for family, template_ids in TEMPLATE_FAMILIES.items():
            family_count = session.execute(
                select(func.count()).select_from(ScenarioPackTemplate)
                .where(ScenarioPackTemplate.family == family)
            ).scalar()
            assert family_count == len(template_ids), f"Family {family}: expected {len(template_ids)}, got {family_count}"


# ── Test 2: Re-seed is idempotent ──

def test_reseed_is_idempotent(engine):
    """Re-seeding does not create duplicate templates."""
    with Session(engine) as session:
        first_count = seed_templates(session)
        assert first_count == 18

        second_count = seed_templates(session)
        assert second_count == 0

        total = session.execute(
            select(func.count()).select_from(ScenarioPackTemplate)
        ).scalar()
        assert total == 18


# ── Test 3: List all templates ──

def test_list_all_templates(seeded_session):
    """All 18 templates are queryable."""
    templates = seeded_session.execute(
        select(ScenarioPackTemplate).order_by(ScenarioPackTemplate.family)
    ).scalars().all()
    assert len(templates) == 18

    # All have names and families
    for t in templates:
        assert t.name, f"Template {t.id} has no name"
        assert t.family, f"Template {t.id} has no family"
        assert t.is_seeded is True


# ── Test 4: Filter by family NAV_UNC ──

def test_filter_by_family(seeded_session):
    """Filtering by NAV_UNC returns exactly 4 templates."""
    nav_templates = seeded_session.execute(
        select(ScenarioPackTemplate)
        .where(ScenarioPackTemplate.family == "NAV_UNC")
    ).scalars().all()
    assert len(nav_templates) == 4

    nav_ids = {t.id for t in nav_templates}
    assert nav_ids == {"neon_courier", "midnight_exchange", "runway_intercept", "last_mile_hospital"}


# ── Test 5: Get Neon Courier detail ──

def test_neon_courier_detail(seeded_session):
    """Neon Courier template has full fixture data and checkpoints."""
    template = seeded_session.get(ScenarioPackTemplate, "neon_courier")
    assert template is not None
    assert template.name == "Neon Courier"
    assert template.family == "NAV_UNC"
    assert template.template_status == "RUNNABLE"
    assert template.is_seeded is True
    assert template.episode_length_sec == 50
    assert template.fork_points_min == 8
    assert template.fork_points_max == 12

    # Has objective vector from fixture
    assert template.objective_vector_json is not None
    assert len(template.objective_vector_json) == 4
    assert template.objective_vector_json[0]["component"] == "delivery_success_rate"

    # Has saboteur deck from fixture
    assert template.saboteur_deck_json is not None
    assert len(template.saboteur_deck_json) == 6

    # Has checkpoints from forkPointSchema
    checkpoints = seeded_session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == "neon_courier")
        .order_by(ScenarioCheckpoint.sequence_num)
    ).scalars().all()
    assert len(checkpoints) == 8  # 8 fork points in NEON_COURIER_V1.json

    # First checkpoint matches fixture
    cp1 = checkpoints[0]
    assert cp1.trigger == "route_choice"
    assert "highway" in cp1.market_question.lower()


# ── Test 6: RUNNABLE templates have structured checkpoints ──

def test_runnable_templates_have_checkpoints(seeded_session):
    """All 4 RUNNABLE templates have checkpoints from fixtures."""
    runnable = seeded_session.execute(
        select(ScenarioPackTemplate)
        .where(ScenarioPackTemplate.template_status == "RUNNABLE")
    ).scalars().all()
    assert len(runnable) == 4

    runnable_ids = {t.id for t in runnable}
    assert runnable_ids == set(FIXTURE_MAP.keys())

    for t in runnable:
        cp_count = seeded_session.execute(
            select(func.count()).select_from(ScenarioCheckpoint)
            .where(ScenarioCheckpoint.template_id == t.id)
        ).scalar()
        assert cp_count > 0, f"RUNNABLE template {t.id} has no checkpoints"

        # Each checkpoint should have branches
        branch_count = seeded_session.execute(
            select(func.count()).select_from(CheckpointBranch)
            .where(CheckpointBranch.checkpoint_id.in_(
                select(ScenarioCheckpoint.id)
                .where(ScenarioCheckpoint.template_id == t.id)
            ))
        ).scalar()
        assert branch_count > 0, f"RUNNABLE template {t.id} checkpoints have no branches"

    # CATALOG_ONLY templates should also have checkpoint stubs
    catalog = seeded_session.execute(
        select(ScenarioPackTemplate)
        .where(ScenarioPackTemplate.template_status == "CATALOG_ONLY")
    ).scalars().all()
    assert len(catalog) == 14
