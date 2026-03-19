"""Tests for Cycle 038 Sprint 1 — Core Services.

Tests cover:
- FactAnchorService: get_or_create, link_theatre, queries (T1.1, T1.2)
- CoherenceGroupService: CRUD, membership (T1.3)
- OracleConsistencyMonitor: record, check, divergence history (T1.4)
- Pydantic schemas: import and validation (T1.5)
"""

import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

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

import asyncio

from backend.database.models import (
    FactAnchor,
    FactAnchorLink,
    CoherenceGroup,
    CoherenceGroupMember,
    OracleResponse,
)


def run_async(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Mock AsyncSession
# ---------------------------------------------------------------------------

class MockScalarResult:
    """Mock for result.scalar_one_or_none() and result.scalars().all()."""

    def __init__(self, items=None, scalar=None):
        self._items = items or []
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        if self._scalar is not None:
            return self._scalar
        return self._items[0] if self._items else 0

    def scalars(self):
        return self

    def all(self):
        return self._items


class MockAsyncSession:
    """Minimal mock of AsyncSession for service-level unit tests."""

    def __init__(self):
        self._added = []
        self._execute_responses = []
        self._execute_call_count = 0

    def add(self, obj):
        self._added.append(obj)

    async def flush(self):
        # Assign IDs to newly added objects that lack them
        for obj in self._added:
            if hasattr(obj, "id") and obj.id is None:
                obj.id = f"mock-{type(obj).__name__.lower()}-{id(obj)}"

    async def execute(self, stmt):
        if self._execute_call_count < len(self._execute_responses):
            resp = self._execute_responses[self._execute_call_count]
            self._execute_call_count += 1
            return resp
        return MockScalarResult()

    def queue_response(self, items=None, scalar=None):
        self._execute_responses.append(MockScalarResult(items=items, scalar=scalar))


# ===========================================================================
# T1.1: FactAnchorService — get_or_create + queries
# ===========================================================================

class TestFactAnchorServiceGetOrCreate(unittest.TestCase):
    """T1.1: FactAnchorService.get_or_create()."""

    def test_creates_new_anchor(self):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue_response(scalar=None)  # No existing anchor
        svc = FactAnchorService(session)

        anchor = run_async(svc.get_or_create(
            anchor_type="seismic_event",
            external_id="us6000test",
            external_source="usgs_neic",
            occurred_at=datetime(2026, 3, 19, 10, 0, 0),
            location_json={"lat": 35.7, "lon": -121.3},
            metadata_json={"magnitude": 6.2},
        ))

        self.assertEqual(anchor.anchor_type, "seismic_event")
        self.assertEqual(anchor.external_id, "us6000test")
        self.assertEqual(anchor.external_source, "usgs_neic")
        self.assertEqual(len(session._added), 1)

    def test_returns_existing_on_duplicate(self):
        from backend.services.fact_anchor_service import FactAnchorService

        existing = FactAnchor(
            id="fa-existing",
            anchor_type="seismic_event",
            external_id="us6000test",
            external_source="usgs_neic",
            occurred_at=datetime(2026, 3, 19),
        )
        session = MockAsyncSession()
        session.queue_response(scalar=existing)
        svc = FactAnchorService(session)

        anchor = run_async(svc.get_or_create(
            anchor_type="seismic_event",
            external_id="us6000test",
            external_source="usgs_neic",
            occurred_at=datetime(2026, 3, 19),
        ))

        self.assertEqual(anchor.id, "fa-existing")
        self.assertEqual(len(session._added), 0)  # No new objects added

    def test_get_theatres_for_anchor(self):
        from backend.services.fact_anchor_service import FactAnchorService

        link1 = FactAnchorLink(
            id="fal-1", fact_anchor_id="fa-1", theatre_id="t-1",
            link_type="settlement", linked_entity_id="e-1",
            linked_entity_type="outcome",
        )
        link2 = FactAnchorLink(
            id="fal-2", fact_anchor_id="fa-1", theatre_id="t-2",
            link_type="settlement", linked_entity_id="e-2",
            linked_entity_type="outcome",
        )
        session = MockAsyncSession()
        session.queue_response(items=[link1, link2])
        svc = FactAnchorService(session)

        links = run_async(svc.get_theatres_for_anchor("fa-1"))
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].theatre_id, "t-1")

    def test_get_anchors_for_theatre(self):
        from backend.services.fact_anchor_service import FactAnchorService

        link = FactAnchorLink(
            id="fal-3", fact_anchor_id="fa-1", theatre_id="t-1",
            link_type="evidence", linked_entity_id="e-3",
            linked_entity_type="signal",
        )
        session = MockAsyncSession()
        session.queue_response(items=[link])
        svc = FactAnchorService(session)

        links = run_async(svc.get_anchors_for_theatre("t-1"))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].link_type, "evidence")


# ===========================================================================
# T1.2: FactAnchorService — link_theatre
# ===========================================================================

class TestFactAnchorServiceLinkTheatre(unittest.TestCase):
    """T1.2: FactAnchorService.link_theatre() with scan trigger."""

    def test_link_creates_record(self):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue_response(scalar=1)  # 1 distinct theatre
        svc = FactAnchorService(session)

        link, should_scan = run_async(svc.link_theatre(
            anchor_id="fa-1",
            theatre_id="t-1",
            link_type="settlement",
            linked_entity_id="outcome-1",
            linked_entity_type="theatre_outcome",
        ))

        self.assertEqual(link.fact_anchor_id, "fa-1")
        self.assertEqual(link.theatre_id, "t-1")
        self.assertFalse(should_scan)

    def test_scan_trigger_at_two_theatres(self):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue_response(scalar=2)  # 2 distinct theatres
        svc = FactAnchorService(session)

        _, should_scan = run_async(svc.link_theatre(
            anchor_id="fa-1",
            theatre_id="t-2",
            link_type="settlement",
            linked_entity_id="outcome-2",
            linked_entity_type="theatre_outcome",
        ))

        self.assertTrue(should_scan)

    def test_no_scan_trigger_single_theatre(self):
        from backend.services.fact_anchor_service import FactAnchorService

        session = MockAsyncSession()
        session.queue_response(scalar=1)  # Still only 1 theatre
        svc = FactAnchorService(session)

        _, should_scan = run_async(svc.link_theatre(
            anchor_id="fa-1",
            theatre_id="t-1",
            link_type="evidence",
            linked_entity_id="signal-1",
            linked_entity_type="osint_signal",
        ))

        self.assertFalse(should_scan)


# ===========================================================================
# T1.3: CoherenceGroupService
# ===========================================================================

class TestCoherenceGroupService(unittest.TestCase):
    """T1.3: CoherenceGroupService CRUD."""

    def test_create_group(self):
        from backend.services.coherence_group_service import CoherenceGroupService

        session = MockAsyncSession()
        svc = CoherenceGroupService(session)

        group = run_async(svc.create_group(
            name="seismic-pacific-ring",
            group_type="domain_overlap",
            policy_json={
                "settlement_divergence_threshold": 0.0,
                "oracle_tolerance": 0.1,
                "temporal_drift_hours": 24,
            },
        ))

        self.assertEqual(group.name, "seismic-pacific-ring")
        self.assertEqual(group.group_type, "domain_overlap")
        self.assertEqual(group.policy_json["oracle_tolerance"], 0.1)

    def test_add_member(self):
        from backend.services.coherence_group_service import CoherenceGroupService

        session = MockAsyncSession()
        svc = CoherenceGroupService(session)

        member = run_async(svc.add_member(
            group_id="cg-1",
            theatre_id="t-1",
            role="primary",
        ))

        self.assertEqual(member.coherence_group_id, "cg-1")
        self.assertEqual(member.theatre_id, "t-1")
        self.assertEqual(member.role, "primary")

    def test_get_groups_for_theatre(self):
        from backend.services.coherence_group_service import CoherenceGroupService

        group = CoherenceGroup(
            id="cg-1", name="test-group", group_type="domain_overlap",
            policy_json={},
        )
        session = MockAsyncSession()
        session.queue_response(items=[group])
        svc = CoherenceGroupService(session)

        groups = run_async(svc.get_groups_for_theatre("t-1"))
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, "test-group")

    def test_get_group_members(self):
        from backend.services.coherence_group_service import CoherenceGroupService

        m1 = CoherenceGroupMember(
            id="cgm-1", coherence_group_id="cg-1",
            theatre_id="t-1", role="primary",
        )
        m2 = CoherenceGroupMember(
            id="cgm-2", coherence_group_id="cg-1",
            theatre_id="t-2", role="observer",
        )
        session = MockAsyncSession()
        session.queue_response(items=[m1, m2])
        svc = CoherenceGroupService(session)

        members = run_async(svc.get_group_members("cg-1"))
        self.assertEqual(len(members), 2)
        self.assertEqual(members[1].role, "observer")


# ===========================================================================
# T1.4: OracleConsistencyMonitor
# ===========================================================================

class TestOracleConsistencyMonitor(unittest.TestCase):
    """T1.4: OracleConsistencyMonitor record, check, divergence."""

    def test_record_response_new(self):
        from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

        session = MockAsyncSession()
        session.queue_response(scalar=None)  # No existing
        monitor = OracleConsistencyMonitor(session)

        resp = run_async(monitor.record_response(
            theatre_id="t-1",
            source="usgs_neic",
            event_id="us6000test",
            value_json={"magnitude": 6.2, "mag_type": "mww"},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
            is_provisional=True,
        ))

        self.assertEqual(resp.source, "usgs_neic")
        self.assertTrue(resp.is_provisional)
        self.assertEqual(len(session._added), 1)

    def test_record_response_idempotent_update(self):
        from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

        existing = OracleResponse(
            id="or-existing", theatre_id="t-1", source="usgs_neic",
            event_id="us6000test",
            value_json={"magnitude": 6.2},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
            is_provisional=True,
        )
        session = MockAsyncSession()
        session.queue_response(scalar=existing)
        monitor = OracleConsistencyMonitor(session)

        resp = run_async(monitor.record_response(
            theatre_id="t-1",
            source="usgs_neic",
            event_id="us6000test",
            value_json={"magnitude": 6.1, "status": "reviewed"},
            queried_at=datetime(2026, 3, 19, 12, 0, 0),
            is_provisional=False,
        ))

        # Should update existing, not create new
        self.assertEqual(resp.id, "or-existing")
        self.assertEqual(resp.value_json["magnitude"], 6.1)
        self.assertFalse(resp.is_provisional)
        self.assertEqual(len(session._added), 0)  # No new objects

    def test_check_consistency_identical(self):
        from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

        r1 = OracleResponse(
            id="or-1", theatre_id="t-1", source="usgs_neic",
            event_id="us6000test", value_json={"magnitude": 6.2},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
        )
        r2 = OracleResponse(
            id="or-2", theatre_id="t-2", source="usgs_neic",
            event_id="us6000test", value_json={"magnitude": 6.2},
            queried_at=datetime(2026, 3, 19, 10, 5, 0),
        )
        session = MockAsyncSession()
        session.queue_response(items=[r1, r2])
        monitor = OracleConsistencyMonitor(session)

        result = run_async(monitor.check_consistency("usgs_neic", "us6000test"))
        self.assertTrue(result.is_consistent)
        self.assertEqual(result.max_delta, 0.0)

    def test_check_consistency_divergent(self):
        from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

        r1 = OracleResponse(
            id="or-1", theatre_id="t-1", source="usgs_neic",
            event_id="us6000test", value_json={"magnitude": 6.2},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
        )
        r2 = OracleResponse(
            id="or-2", theatre_id="t-2", source="usgs_neic",
            event_id="us6000test", value_json={"magnitude": 5.8},
            queried_at=datetime(2026, 3, 19, 10, 5, 0),
        )
        session = MockAsyncSession()
        session.queue_response(items=[r1, r2])
        monitor = OracleConsistencyMonitor(session)

        result = run_async(monitor.check_consistency("usgs_neic", "us6000test"))
        self.assertFalse(result.is_consistent)
        self.assertAlmostEqual(result.max_delta, 0.4, places=1)

    def test_check_consistency_provisional_preserved(self):
        from backend.services.oracle_consistency_monitor import OracleConsistencyMonitor

        r1 = OracleResponse(
            id="or-1", theatre_id="t-1", source="usgs_neic",
            event_id="us6000test", value_json={"magnitude": 6.2},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
            is_provisional=True,
        )
        session = MockAsyncSession()
        session.queue_response(items=[r1])
        monitor = OracleConsistencyMonitor(session)

        result = run_async(monitor.check_consistency("usgs_neic", "us6000test"))
        self.assertTrue(result.is_consistent)
        self.assertTrue(result.responses[0]["is_provisional"])


# ===========================================================================
# T1.5: Pydantic Schemas
# ===========================================================================

class TestPydanticSchemas(unittest.TestCase):
    """T1.5: All schema files importable, validation works."""

    def test_fact_anchor_schemas_import_and_validate(self):
        from backend.schemas.fact_anchor_schemas import (
            CreateFactAnchorRequest,
            LinkTheatreRequest,
            FactAnchorResponse,
            FactAnchorLinkResponse,
            FactAnchorDetailResponse,
        )

        req = CreateFactAnchorRequest(
            anchor_type="seismic_event",
            external_id="us6000test",
            external_source="usgs_neic",
            occurred_at=datetime(2026, 3, 19, 10, 0, 0),
        )
        self.assertEqual(req.anchor_type, "seismic_event")

        link_req = LinkTheatreRequest(
            theatre_id="t-1",
            link_type="settlement",
            linked_entity_id="outcome-1",
            linked_entity_type="theatre_outcome",
        )
        self.assertEqual(link_req.link_confidence, 1.0)

    def test_all_schema_files_importable(self):
        from backend.schemas.fact_anchor_schemas import CreateFactAnchorRequest
        from backend.schemas.coherence_group_schemas import (
            CreateCoherenceGroupRequest,
            CoherenceGroupResponse,
        )
        from backend.schemas.cross_theatre_paradox_schemas import (
            CrossTheatreParadoxResponse,
            ParadoxTypeEnum,
            ParadoxSeverityEnum,
            ParadoxStatusEnum,
        )
        from backend.schemas.oracle_consistency_schemas import (
            RecordOracleResponseRequest,
            ConsistencyCheckResponse,
            DivergenceRecordResponse,
        )

        # Verify enum values accessible
        self.assertEqual(ParadoxTypeEnum.SETTLEMENT_DIVERGENCE, "SETTLEMENT_DIVERGENCE")
        self.assertEqual(ParadoxSeverityEnum.MATERIAL, "MATERIAL")
        self.assertEqual(ParadoxStatusEnum.OPEN, "OPEN")


if __name__ == "__main__":
    unittest.main()
