"""Cycle-019 Sprint 3 — Paradox Risk Evaluator tests.

6 tests:
1. Evaluator returns LOW for healthy theatre
2. Evaluator returns WATCH for moderate logic gap
3. Evaluator returns HIGH for active paradox
4. INVESTIGATIVE inquiry weighs evidence freshness higher
5. SCRUTINY inquiry weighs counter-signals higher
6. Theatre paradox_risk persistence roundtrip
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.services.paradox_risk_evaluator import (
    evaluate,
    persist_risk_to_theatre,
    ParadoxRiskAssessment,
    THRESHOLDS,
)
from backend.database.models import (
    Base,
    User,
    TheatreTemplate,
    Theatre,
)


# ── Fixtures ──

_TABLES = [
    User.__table__,
    TheatreTemplate.__table__,
    Theatre.__table__,
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


# ── Test 1: LOW for healthy theatre ──

def test_evaluator_returns_low_healthy():
    """Returns LOW for healthy theatre (no paradox, low logic gap, high stability)."""
    result = evaluate(
        logic_gap=0.1,
        stability=0.9,
        has_active_paradox=False,
        material_counter_signals=0,
        evidence_freshness_hours=2.0,
        inquiry_class="COUNTERFACTUAL",
    )

    assert result.level == "LOW"
    assert result.factors["logic_gap"] == 0.1
    assert result.factors["stability"] == 0.9
    assert "acceptable" in result.explanation.lower()


# ── Test 2: WATCH for moderate logic gap ──

def test_evaluator_returns_watch_moderate_logic_gap():
    """Returns WATCH for theatre with moderate logic gap."""
    result = evaluate(
        logic_gap=0.5,
        stability=0.7,
        has_active_paradox=False,
        material_counter_signals=0,
        evidence_freshness_hours=10.0,
        inquiry_class="COUNTERFACTUAL",
    )

    assert result.level == "WATCH"
    assert "Logic gap" in result.explanation


# ── Test 3: HIGH for active paradox ──

def test_evaluator_returns_high_active_paradox():
    """Returns HIGH for theatre with active paradox."""
    result = evaluate(
        logic_gap=0.2,
        stability=0.8,
        has_active_paradox=True,
        material_counter_signals=0,
        evidence_freshness_hours=5.0,
        inquiry_class="COUNTERFACTUAL",
    )

    assert result.level == "HIGH"
    assert "Paradox active" in result.explanation


# ── Test 4: INVESTIGATIVE weighs evidence freshness higher ──

def test_investigative_weighs_freshness_higher():
    """INVESTIGATIVE inquiry weighs evidence freshness more heavily."""
    # With COUNTERFACTUAL (low freshness weight = 0.3), 150 hours should be okay
    # threshold = 72 / 0.3 = 240 hours
    result_cf = evaluate(
        logic_gap=0.1,
        stability=0.9,
        has_active_paradox=False,
        material_counter_signals=0,
        evidence_freshness_hours=150.0,
        inquiry_class="COUNTERFACTUAL",
    )

    # With INVESTIGATIVE (high freshness weight = 0.7), same hours triggers WATCH
    # threshold = 72 / 0.7 = ~103 hours
    result_inv = evaluate(
        logic_gap=0.1,
        stability=0.9,
        has_active_paradox=False,
        material_counter_signals=0,
        evidence_freshness_hours=150.0,
        inquiry_class="INVESTIGATIVE",
    )

    assert result_cf.level == "LOW"
    assert result_inv.level == "WATCH"
    assert "Stale" in result_inv.explanation


# ── Test 5: SCRUTINY weighs counter-signals higher ──

def test_scrutiny_weighs_counter_signals_higher():
    """SCRUTINY inquiry weighs counter-signals more heavily."""
    # Both with 1 material counter-signal
    result_cf = evaluate(
        logic_gap=0.1,
        stability=0.9,
        has_active_paradox=False,
        material_counter_signals=1,
        evidence_freshness_hours=5.0,
        inquiry_class="COUNTERFACTUAL",
    )

    result_sc = evaluate(
        logic_gap=0.1,
        stability=0.9,
        has_active_paradox=False,
        material_counter_signals=1,
        evidence_freshness_hours=5.0,
        inquiry_class="SCRUTINY",
    )

    # Both should be WATCH with counter-signals > 0
    assert result_cf.level == "WATCH"
    assert result_sc.level == "WATCH"

    # SCRUTINY should use "rising" language (weight >= 0.7)
    assert "rising" in result_sc.explanation.lower()
    # COUNTERFACTUAL uses "detected" (weight < 0.7)
    assert "detected" in result_cf.explanation.lower()


# ── Test 6: Theatre paradox_risk persistence roundtrip ──

def test_theatre_paradox_risk_persistence(session):
    """Theatre paradox_risk fields persist correctly."""
    now = datetime.now(timezone.utc)

    tmpl = TheatreTemplate(
        id="tmpl-1", display_name="Test", template_family="binary",
        execution_path="TWO_RAIL", schema_version="1.0", template_json={},
        created_at=now, updated_at=now,
    )
    session.add(tmpl)

    theatre = Theatre(
        id="theatre-1", user_id="user-1", template_id="tmpl-1",
        state="RESOLVED", construct_id="test_construct",
        created_at=now, updated_at=now,
    )
    session.add(theatre)
    session.flush()

    # Compute and persist risk
    assessment = evaluate(
        logic_gap=0.5,
        stability=0.6,
        has_active_paradox=False,
        inquiry_class="INVESTIGATIVE",
    )
    persist_risk_to_theatre(theatre, assessment)
    session.flush()

    # Read back from DB
    from sqlalchemy import select
    result = session.execute(
        select(Theatre).where(Theatre.id == "theatre-1")
    )
    loaded = result.scalar_one()

    assert loaded.paradox_risk_level == "WATCH"
    assert loaded.paradox_risk_factors_json["logic_gap"] == 0.5
    assert loaded.paradox_risk_updated_at is not None
