"""Cycle-018 Sprint 0 — Schema Foundation tests.

4 tests:
1. All 7 new tables exist after create_all
2. Theatre has spawned_from_checkpoint_id column
3. Pydantic ScenarioPackTemplateResponse serialises from dict with template_status
4. Pydantic ScenarioPackCreate validates template_id
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
    ScenarioPack,
    ScenarioRun,
    RunCheckpointResult,
    ScenarioPackAuditEvent,
    Theatre,
    TheatreTemplate,
    TheatreCertificate,
    User,
)
from backend.schemas.scenario_packs import (
    ScenarioPackTemplateResponse,
    ScenarioPackTemplateSummaryResponse,
    ScenarioPackCreate,
)


# ── Fixtures ──

def _create_tables(eng):
    """Create only the tables needed for scenario pack tests (avoids ARRAY column issues on SQLite)."""
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        TheatreCertificate.__table__,
        Theatre.__table__,
        ScenarioPackTemplate.__table__,
        ScenarioCheckpoint.__table__,
        CheckpointBranch.__table__,
        ScenarioPack.__table__,
        ScenarioRun.__table__,
        RunCheckpointResult.__table__,
        ScenarioPackAuditEvent.__table__,
    ]
    # Use DDL directly to handle index-if-exists for SQLite
    with eng.connect() as conn:
        for table in tables:
            table.create(conn, checkfirst=True)
        conn.commit()


@pytest.fixture
def engine():
    """In-memory SQLite with all scenario pack tables."""
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    return eng


# ── Test 1: All 7 new tables exist ──

def test_all_scenario_pack_tables_exist(engine):
    """All 7 new scenario pack tables are created."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    expected_tables = [
        "scenario_pack_templates",
        "scenario_checkpoints",
        "checkpoint_branches",
        "scenario_packs",
        "scenario_runs",
        "run_checkpoint_results",
        "scenario_pack_audit_events",
    ]

    for table in expected_tables:
        assert table in table_names, f"Missing table: {table}"


# ── Test 2: Theatre has spawned_from_checkpoint_id ──

def test_theatre_has_spawned_from_checkpoint_id(engine):
    """Theatre model has the spawned_from_checkpoint_id provenance column."""
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("theatres")]
    assert "spawned_from_checkpoint_id" in columns


# ── Test 3: Template response serialises with template_status ──

def test_template_response_has_template_status():
    """ScenarioPackTemplateResponse includes template_status field."""
    now = datetime.now(timezone.utc)
    resp = ScenarioPackTemplateResponse(
        id="neon_courier",
        name="Neon Courier",
        family="NAV_UNC",
        template_status="RUNNABLE",
        objective_vector=[],
        fork_points=[],
        saboteur_deck=[],
        fork_points_min=3,
        fork_points_max=5,
        is_seeded=True,
        checkpoint_count=4,
        created_at=now,
    )
    assert resp.template_status == "RUNNABLE"
    assert resp.id == "neon_courier"

    # Summary also has template_status
    summary = ScenarioPackTemplateSummaryResponse(
        id="neon_courier",
        name="Neon Courier",
        family="NAV_UNC",
        template_status="CATALOG_ONLY",
        checkpoint_count=0,
        fork_points_min=1,
        fork_points_max=10,
        is_seeded=False,
    )
    assert summary.template_status == "CATALOG_ONLY"


# ── Test 4: ScenarioPackCreate validates template_id ──

def test_scenario_pack_create_validates():
    """ScenarioPackCreate enforces template_id constraints and run_mode default."""
    pack = ScenarioPackCreate(template_id="neon_courier")
    assert pack.template_id == "neon_courier"
    assert pack.run_mode == "TRAINING"
    assert pack.agent_assignment == "auto_assign"

    # Empty template_id should fail
    with pytest.raises(Exception):
        ScenarioPackCreate(template_id="")
