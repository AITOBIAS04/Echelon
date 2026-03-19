"""
Tests for Sprint 2 (Cycle 038): CrossTheatreParadoxScanner + Integration.

Tests cover:
- T2.1: Settlement divergence detection (5 tests)
- T2.2: Oracle inconsistency + provisional rule (4 tests)
- T2.3: Scope overlap + temporal drift (4 tests)
- T2.4: ParadoxRiskOrchestrator extension (3 tests)
- T2.5: WingFlap + WebSocket integration (3 tests)
- T2.6: FactAnchorService scanner wiring (2 tests)
"""

import asyncio
import sys
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the database connection module before importing anything.
_mock_base_module = MagicMock()
from sqlalchemy.orm import declarative_base
_real_base = declarative_base()
_mock_base_module.Base = _real_base
sys.modules.setdefault("backend.database.connection", _mock_base_module)
sys.modules.setdefault("backend.database.config", MagicMock())
_mock_base_module.engine = MagicMock()
_mock_base_module.async_session_maker = MagicMock()
_mock_base_module.get_session = MagicMock()
_mock_base_module.get_db = MagicMock()
_mock_base_module.init_db = MagicMock()
_mock_base_module.close_db = MagicMock()

# Mock fastapi for WebSocket-using modules (Python 3.9 compat)
if "fastapi" not in sys.modules:
    sys.modules.setdefault("fastapi", MagicMock())

from backend.database.models import (
    CrossTheatreParadoxSeverity,
    CrossTheatreParadoxStatus,
    CrossTheatreParadoxType,
    WingFlapType,
)


def run_async(coro):
    """Run async coroutine in sync test."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_anchor(**kwargs):
    """Create a fake FactAnchor-like object."""
    defaults = dict(
        id="anchor-1", anchor_type="seismic_event",
        external_source="usgs_neic", external_id="us6000test",
        occurred_at=datetime(2026, 3, 19), location_json=None,
        metadata_json=None, created_at=datetime(2026, 3, 19),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_link(**kwargs):
    """Create a fake FactAnchorLink-like object."""
    defaults = dict(
        id="link-1", fact_anchor_id="anchor-1", theatre_id="theatre-a",
        link_type="settlement", link_confidence=1.0,
        linked_entity_id="cert-1", linked_entity_type="YES",
        created_at=datetime(2026, 3, 19, 10, 0, 0),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_oracle_response(**kwargs):
    """Create a fake OracleResponse-like object."""
    defaults = dict(
        id="resp-1", theatre_id="theatre-a", source="usgs_neic",
        event_id="us6000test", value_json={"magnitude": 6.2},
        queried_at=datetime(2026, 3, 19), is_provisional=False,
        created_at=datetime(2026, 3, 19),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_group(**kwargs):
    """Create a fake CoherenceGroup-like object."""
    defaults = dict(
        id="group-1", name="Seismic Coherence", group_type="domain_overlap",
        policy_json={}, created_at=datetime(2026, 3, 19),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_member(**kwargs):
    """Create a fake CoherenceGroupMember-like object."""
    defaults = dict(
        id="member-1", coherence_group_id="group-1",
        theatre_id="theatre-a", role="primary",
        joined_at=datetime(2026, 3, 19),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class MockScalarResult:
    """Mock for SQLAlchemy result objects."""
    def __init__(self, items=None, scalar_value=None):
        self._items = items or []
        self._scalar_value = scalar_value

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def scalar_one(self):
        return self._scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value


class MockAsyncSession:
    """Mock AsyncSession with queued responses."""
    def __init__(self):
        self._responses = []
        self._added = []
        self._flushed = False

    def queue(self, response):
        self._responses.append(response)

    async def execute(self, stmt):
        if self._responses:
            return self._responses.pop(0)
        return MockScalarResult()

    def add(self, obj):
        self._added.append(obj)

    async def flush(self):
        self._flushed = True

    async def get(self, model_class, id_value):
        if self._responses:
            return self._responses.pop(0)
        return None


# ===========================
# T2.1: Settlement Divergence
# ===========================

class TestSettlementDivergence(unittest.TestCase):
    """T2.1: Detects opposite outcomes, skips same, respects dedup, ordering."""

    def test_detects_opposite_outcomes(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup check

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_settlement_divergence(
            make_anchor(),
            make_link(theatre_id="theatre-a", linked_entity_type="YES"),
            make_link(theatre_id="theatre-b", linked_entity_type="NO"),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.paradox_type, CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.MATERIAL)

    def test_skips_same_outcomes(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_settlement_divergence(
            make_anchor(),
            make_link(theatre_id="theatre-a", linked_entity_type="YES"),
            make_link(theatre_id="theatre-b", linked_entity_type="YES"),
        ))
        self.assertIsNone(result)

    def test_dedup_skips_existing(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        existing = SimpleNamespace(id="existing-1")
        session.queue(MockScalarResult(items=[existing]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_settlement_divergence(
            make_anchor(),
            make_link(theatre_id="theatre-a", linked_entity_type="YES"),
            make_link(theatre_id="theatre-b", linked_entity_type="NO"),
        ))
        self.assertIsNone(result)

    def test_theatre_ordering(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_settlement_divergence(
            make_anchor(),
            make_link(theatre_id="theatre-z", linked_entity_type="YES"),
            make_link(theatre_id="theatre-a", linked_entity_type="NO"),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.theatre_a_id, "theatre-a")
        self.assertEqual(result.theatre_b_id, "theatre-z")

    def test_non_settlement_links_ignored(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_settlement_divergence(
            make_anchor(),
            make_link(theatre_id="theatre-a", link_type="evidence"),
            make_link(theatre_id="theatre-b", link_type="evidence"),
        ))
        self.assertIsNone(result)


# =============================================
# T2.2: Oracle Inconsistency + Provisional Rule
# =============================================

class TestOracleInconsistency(unittest.TestCase):
    """T2.2: Oracle delta detection, tolerance, provisional downgrade, cross-source."""

    def test_same_source_divergence_material(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup
        session.queue(MockScalarResult(items=[  # theatre-a responses
            make_oracle_response(theatre_id="theatre-a", value_json={"magnitude": 6.2}),
        ]))
        session.queue(MockScalarResult(items=[  # theatre-b responses
            make_oracle_response(theatre_id="theatre-b", source="usgs_neic", value_json={"magnitude": 5.8}),
        ]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_oracle_inconsistency(
            make_anchor(),
            make_link(theatre_id="theatre-a"),
            make_link(theatre_id="theatre-b"),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.paradox_type, CrossTheatreParadoxType.ORACLE_INCONSISTENCY)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.MATERIAL)

    def test_cross_source_is_watch(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="usgs_neic", value_json={"magnitude": 6.2}),
        ]))
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="emsc", value_json={"magnitude": 5.8}),
        ]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_oracle_inconsistency(
            make_anchor(),
            make_link(theatre_id="theatre-a"),
            make_link(theatre_id="theatre-b"),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.WATCH)

    def test_provisional_revision_info(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="usgs_neic", is_provisional=True, value_json={"magnitude": 6.2}),
        ]))
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="usgs_neic", is_provisional=False, value_json={"magnitude": 6.0}),
        ]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_oracle_inconsistency(
            make_anchor(),
            make_link(theatre_id="theatre-a"),
            make_link(theatre_id="theatre-b"),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.INFO)

    def test_within_tolerance_no_paradox(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="usgs_neic", value_json={"magnitude": 6.20}),
        ]))
        session.queue(MockScalarResult(items=[
            make_oracle_response(source="usgs_neic", value_json={"magnitude": 6.15}),
        ]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_oracle_inconsistency(
            make_anchor(),
            make_link(theatre_id="theatre-a"),
            make_link(theatre_id="theatre-b"),
        ))
        self.assertIsNone(result)


# ===================================
# T2.3: Scope Overlap + Temporal Drift
# ===================================

class TestScopeOverlap(unittest.TestCase):
    """T2.3: Scope overlap gap detection."""

    def test_scope_gap_detected(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        # Queue: get primary members
        session.queue(MockScalarResult(items=[
            make_member(theatre_id="theatre-a", role="primary"),
            make_member(theatre_id="theatre-b", role="primary"),
        ]))
        # Queue: links for anchor — only theatre-a
        session.queue(MockScalarResult(items=[
            make_link(theatre_id="theatre-a", fact_anchor_id="anchor-1"),
        ]))
        # Queue: dedup check
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_scope_overlap(
            make_group(), make_anchor(),
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.paradox_type, CrossTheatreParadoxType.SCOPE_OVERLAP_GAP)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.WATCH)


class TestTemporalDrift(unittest.TestCase):
    """T2.3: Temporal drift detection."""

    def test_drift_above_window_is_info(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))  # dedup

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_temporal_drift(
            make_anchor(),
            make_link(theatre_id="theatre-a", created_at=datetime(2026, 3, 19, 10, 0, 0)),
            make_link(theatre_id="theatre-b", created_at=datetime(2026, 3, 20, 20, 0, 0)),  # 34h
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.paradox_type, CrossTheatreParadoxType.TEMPORAL_DRIFT)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.INFO)

    def test_drift_above_2x_window_is_watch(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_temporal_drift(
            make_anchor(),
            make_link(theatre_id="theatre-a", created_at=datetime(2026, 3, 19, 10, 0, 0)),
            make_link(theatre_id="theatre-b", created_at=datetime(2026, 3, 21, 14, 0, 0)),  # 52h > 48h
        ))

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, CrossTheatreParadoxSeverity.WATCH)

    def test_drift_within_window_no_paradox(self):
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)
        result = run_async(scanner.evaluate_temporal_drift(
            make_anchor(),
            make_link(theatre_id="theatre-a", created_at=datetime(2026, 3, 19, 10, 0, 0)),
            make_link(theatre_id="theatre-b", created_at=datetime(2026, 3, 19, 20, 0, 0)),  # 10h < 24h
        ))
        self.assertIsNone(result)


# ======================================
# T2.4: ParadoxRiskOrchestrator Extension
# ======================================

class TestOrchestratorExtension(unittest.TestCase):
    """T2.4: Cross-theatre exposure feeds into risk, floor logic, material delta."""

    def test_exposure_floor_watch(self):
        from backend.services.paradox_risk_orchestrator import is_material_delta
        old_factors = {"cross_theatre_exposure": 0}
        new_factors = {"cross_theatre_exposure": 1}
        self.assertTrue(is_material_delta("LOW", "WATCH", old_factors, new_factors))

    def test_exposure_floor_high(self):
        from backend.services.paradox_risk_orchestrator import is_material_delta
        old_factors = {"cross_theatre_exposure": 0}
        new_factors = {"cross_theatre_exposure": 3}
        self.assertTrue(is_material_delta("LOW", "HIGH", old_factors, new_factors))

    def test_exposure_change_is_material(self):
        from backend.services.paradox_risk_orchestrator import is_material_delta
        old_factors = {
            "logic_gap": 0.0, "stability": 1.0, "active_paradox": False,
            "material_counter_signals": 0, "evidence_freshness_hours": 0.0,
            "cross_theatre_exposure": 0,
        }
        new_factors = dict(old_factors)
        new_factors["cross_theatre_exposure"] = 2
        self.assertTrue(is_material_delta("WATCH", "WATCH", old_factors, new_factors))


# =========================================
# T2.5: WingFlap + WebSocket Integration
# =========================================

class TestWingFlapWebSocket(unittest.TestCase):
    """T2.5: WingFlap created for MATERIAL+ paradoxes, WebSocket emitted."""

    def test_wingflap_created_for_material(self):
        from backend.services.cross_theatre_paradox_scanner import _record_wingflap

        session = MockAsyncSession()
        paradox = SimpleNamespace(
            id="paradox-1",
            paradox_type=CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE,
            severity=CrossTheatreParadoxSeverity.MATERIAL,
            theatre_a_id="theatre-a",
            theatre_b_id="theatre-b",
            description="Settlement divergence test",
        )

        run_async(_record_wingflap(session, "theatre-a", paradox))
        run_async(_record_wingflap(session, "theatre-b", paradox))

        self.assertEqual(len(session._added), 2)
        flap_a = session._added[0]
        self.assertEqual(flap_a.timeline_id, "theatre-a")
        self.assertEqual(flap_a.flap_type, WingFlapType.CROSS_THEATRE_PARADOX)
        self.assertEqual(flap_a.direction, "DESTABILISE")

    def test_websocket_broadcast(self):
        from backend.services.cross_theatre_paradox_scanner import _broadcast_cross_theatre_paradox

        paradox = SimpleNamespace(
            id="paradox-1",
            paradox_type=CrossTheatreParadoxType.ORACLE_INCONSISTENCY,
            severity=CrossTheatreParadoxSeverity.MATERIAL,
            theatre_a_id="theatre-a",
            theatre_b_id="theatre-b",
            fact_anchor_id="anchor-1",
            description="Oracle inconsistency test",
        )

        # Mock the entire websockets module to avoid Python 3.9 syntax issues
        mock_mgr = MagicMock()
        mock_mgr.broadcast_cross_theatre_paradox = AsyncMock()
        mock_ws_module = MagicMock()
        mock_ws_module.manager = mock_mgr
        with patch.dict(sys.modules, {"backend.websockets.realtime_manager": mock_ws_module}):
            run_async(_broadcast_cross_theatre_paradox(paradox))
            mock_mgr.broadcast_cross_theatre_paradox.assert_called_once()

    def test_scan_creates_wingflaps_for_material(self):
        """scan_fact_anchor creates WingFlaps for MATERIAL paradoxes."""
        from backend.services.cross_theatre_paradox_scanner import CrossTheatreParadoxScanner

        session = MockAsyncSession()
        anchor = make_anchor()
        link_a = make_link(theatre_id="theatre-a", link_type="settlement", linked_entity_type="YES")
        link_b = make_link(theatre_id="theatre-b", link_type="settlement", linked_entity_type="NO",
                          created_at=datetime(2026, 3, 19, 11, 0, 0))

        # Queue: anchor lookup
        session.queue(MockScalarResult(items=[anchor]))
        # Queue: links lookup
        session.queue(MockScalarResult(items=[link_a, link_b]))
        # Queue: settlement divergence dedup
        session.queue(MockScalarResult(items=[]))
        # Queue: oracle inconsistency dedup
        session.queue(MockScalarResult(items=[]))
        # Queue: oracle responses theatre-a (empty)
        session.queue(MockScalarResult(items=[]))
        # Queue: oracle responses theatre-b (empty)
        session.queue(MockScalarResult(items=[]))
        # Queue: temporal drift dedup
        session.queue(MockScalarResult(items=[]))

        scanner = CrossTheatreParadoxScanner(session)

        with patch("backend.services.cross_theatre_paradox_scanner._broadcast_cross_theatre_paradox",
                   new_callable=AsyncMock):
            paradoxes = run_async(scanner.scan_fact_anchor("anchor-1"))

        material = [p for p in paradoxes
                    if p.severity in (CrossTheatreParadoxSeverity.MATERIAL, CrossTheatreParadoxSeverity.CRITICAL)]
        self.assertGreater(len(material), 0)

        # WingFlaps should be in session._added
        from backend.database.models import WingFlap
        wingflaps = [obj for obj in session._added if isinstance(obj, WingFlap)]
        self.assertEqual(len(wingflaps), 2)


# =========================================
# T2.6: FactAnchorService Scanner Wiring
# =========================================

class TestScannerWiring(unittest.TestCase):
    """T2.6: link_theatre triggers scan → detect → recompute."""

    @patch("backend.services.paradox_risk_orchestrator.trigger_recompute", new_callable=AsyncMock)
    @patch("backend.services.cross_theatre_paradox_scanner.CrossTheatreParadoxScanner")
    def test_link_triggers_scanner(self, MockScannerCls, mock_recompute):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue(MockScalarResult(scalar_value=2))  # distinct count

        paradox = SimpleNamespace(
            theatre_a_id="theatre-a", theatre_b_id="theatre-b",
            severity=CrossTheatreParadoxSeverity.MATERIAL,
        )
        mock_scanner_instance = AsyncMock()
        mock_scanner_instance.scan_fact_anchor = AsyncMock(return_value=[paradox])
        MockScannerCls.return_value = mock_scanner_instance

        svc = FactAnchorService(session)
        link, should_scan = run_async(svc.link_theatre(
            anchor_id="anchor-1", theatre_id="theatre-b",
            link_type="settlement", linked_entity_id="cert-1",
            linked_entity_type="YES",
        ))

        self.assertTrue(should_scan)
        mock_scanner_instance.scan_fact_anchor.assert_called_once_with("anchor-1")
        self.assertEqual(mock_recompute.call_count, 2)

    @patch("backend.services.fact_anchor_service.trigger_recompute", new_callable=AsyncMock, create=True)
    @patch("backend.services.fact_anchor_service.CrossTheatreParadoxScanner", create=True)
    def test_no_scan_single_theatre(self, MockScannerCls, mock_recompute):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue(MockScalarResult(scalar_value=1))

        svc = FactAnchorService(session)
        link, should_scan = run_async(svc.link_theatre(
            anchor_id="anchor-1", theatre_id="theatre-a",
            link_type="settlement", linked_entity_id="cert-1",
            linked_entity_type="YES",
        ))

        self.assertFalse(should_scan)
        MockScannerCls.assert_not_called()
        mock_recompute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
