"""Cycle-020 Sprint 4 — Paradox Risk Orchestration tests.

Tests:
1. trigger_recompute loads theatre and evaluates risk
2. Factor gathering returns correct values
3. Material delta detection (level change)
4. Non-material delta: same level, no boundary crossing
5. Orchestrator handles missing theatre gracefully
6. All 4 trigger paths verified via is_material_delta
7. Evidence freshness computed from real timestamps
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.paradox_risk_orchestrator import (
    compute_evidence_freshness_hours,
    is_material_delta,
    trigger_recompute,
)
from backend.services.paradox_risk_evaluator import ParadoxRiskAssessment


def _mock_freshness(hours: float = 5.0):
    """Patch compute_evidence_freshness_hours to return a fixed value."""
    return patch(
        "backend.services.paradox_risk_orchestrator.compute_evidence_freshness_hours",
        new=AsyncMock(return_value=hours),
    )


@pytest.mark.asyncio
async def test_trigger_recompute_evaluates_risk():
    """trigger_recompute evaluates and persists risk."""
    theatre = MagicMock()
    theatre.paradox_risk_level = "LOW"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.1, "stability": 0.9, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 5.0,
    }
    theatre.paradox_risk_updated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    with _mock_freshness(5.0):
        assessment = await trigger_recompute(
            db, "theatre-1", "paradox_state_change",
            logic_gap=0.8, stability=0.2, has_active_paradox=True,
            inquiry_class="COUNTERFACTUAL",
        )

    assert assessment is not None
    assert assessment.level == "HIGH"
    assert assessment._material is True  # Level changed LOW -> HIGH


@pytest.mark.asyncio
async def test_trigger_recompute_non_material():
    """Non-material delta: same level, no boundary crossing."""
    theatre = MagicMock()
    theatre.paradox_risk_level = "LOW"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.1, "stability": 0.9, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 5.0,
    }
    theatre.paradox_risk_updated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    with _mock_freshness(5.0):
        assessment = await trigger_recompute(
            db, "theatre-1", "evidence_freshness_threshold",
            logic_gap=0.15, stability=0.85, has_active_paradox=False,
            inquiry_class="COUNTERFACTUAL",
        )

    assert assessment is not None
    assert assessment.level == "LOW"
    assert assessment._material is False  # Same level, no boundary crossing


@pytest.mark.asyncio
async def test_trigger_recompute_missing_theatre():
    """Missing theatre returns None."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    result = await trigger_recompute(db, "nonexistent", "test")
    assert result is None


@pytest.mark.asyncio
async def test_trigger_recompute_reuses_persisted_factors_when_unset():
    """Unset overrides should inherit persisted factors instead of low-risk defaults."""
    theatre = MagicMock()
    theatre.paradox_risk_level = "WATCH"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.5,
        "stability": 0.8,
        "active_paradox": False,
        "material_counter_signals": 2,
        "evidence_freshness_hours": 4.0,
    }
    theatre.paradox_risk_updated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    with _mock_freshness(4.0):
        assessment = await trigger_recompute(
            db,
            "theatre-1",
            "material_counter_signal",
            inquiry_class="COUNTERFACTUAL",
        )

    assert assessment is not None
    assert assessment.level == "WATCH"
    assert assessment.factors["logic_gap"] == 0.5
    assert assessment.factors["material_counter_signals"] == 2


@pytest.mark.asyncio
async def test_trigger_recompute_emits_ws_with_reason_when_material():
    """Material recomputes should emit the live WS event from the orchestrator."""
    theatre = MagicMock()
    theatre.paradox_risk_level = "LOW"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.1,
        "stability": 0.9,
        "active_paradox": False,
        "material_counter_signals": 0,
        "evidence_freshness_hours": 1.0,
    }
    theatre.paradox_risk_updated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    with _mock_freshness(1.0), patch(
        "backend.websockets.realtime_manager.manager.broadcast_paradox_risk_changed",
        new=AsyncMock(),
    ) as broadcast:
        assessment = await trigger_recompute(
            db,
            "theatre-1",
            "material_counter_signal",
            logic_gap=0.9,
            inquiry_class="COUNTERFACTUAL",
            emit_ws=True,
        )

    assert assessment is not None
    broadcast.assert_awaited_once()
    assert broadcast.await_args.kwargs["reason"] == "material_counter_signal"


def test_materiality_all_four_trigger_paths():
    """Verify material delta detection for each trigger path scenario."""
    base = {
        "logic_gap": 0.3, "stability": 0.7, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 12.0,
    }

    # Path 1: Paradox state change (active_paradox flip)
    paradox_active = {**base, "active_paradox": True}
    assert is_material_delta("LOW", "LOW", base, paradox_active) is True

    # Path 2: Counter-signal ingestion (0 -> positive)
    with_cs = {**base, "material_counter_signals": 1}
    assert is_material_delta("LOW", "LOW", base, with_cs) is True

    # Path 3: Evidence freshness (factor change, same level = NOT material)
    stale = {**base, "evidence_freshness_hours": 100.0}
    assert is_material_delta("LOW", "LOW", base, stale) is False

    # Path 4: Level change from certificate/policy transition
    assert is_material_delta("LOW", "WATCH", base, base) is True
    assert is_material_delta("WATCH", "HIGH", base, base) is True


@pytest.mark.asyncio
async def test_evidence_freshness_from_persisted_timestamps():
    """Evidence freshness should derive from real DB timestamps, not cached factors."""
    from datetime import timedelta

    # Mock db.execute to return a latest_submitted timestamp
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

    mock_result = MagicMock()
    mock_result.scalar.return_value = two_hours_ago

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    hours = await compute_evidence_freshness_hours(db, "theatre-test")

    assert 1.9 < hours < 2.1  # ~2 hours


@pytest.mark.asyncio
async def test_evidence_freshness_no_evidence_returns_zero():
    """No evidence items means 0 freshness hours (no staleness)."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    hours = await compute_evidence_freshness_hours(db, "theatre-empty")
    assert hours == 0.0


@pytest.mark.asyncio
async def test_trigger_recompute_uses_real_freshness_when_no_override():
    """trigger_recompute should call compute_evidence_freshness_hours when
    evidence_freshness_hours is not explicitly overridden."""
    theatre = MagicMock()
    theatre.paradox_risk_level = "LOW"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.1, "stability": 0.9, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 5.0,
    }
    theatre.paradox_risk_updated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    with _mock_freshness(48.0) as mock_freshness_fn:
        assessment = await trigger_recompute(
            db, "theatre-1", "stale_read",
            logic_gap=0.1, stability=0.9,
            inquiry_class="COUNTERFACTUAL",
        )

    # Should have called compute_evidence_freshness_hours
    mock_freshness_fn.assert_awaited_once_with(db, "theatre-1")
    assert assessment.factors["evidence_freshness_hours"] == 48.0


def test_materiality_counter_signal_boundary():
    """Counter-signals crossing back to 0 is also material."""
    with_cs = {
        "logic_gap": 0.3, "stability": 0.7, "active_paradox": False,
        "material_counter_signals": 3, "evidence_freshness_hours": 12.0,
    }
    without_cs = {**with_cs, "material_counter_signals": 0}

    assert is_material_delta("WATCH", "WATCH", with_cs, without_cs) is True
