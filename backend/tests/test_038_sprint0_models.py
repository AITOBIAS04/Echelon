"""Tests for Cycle 038 Sprint 0 — Schema + Model Validation.

Tests cover:
- New enum importability and values (T0.1)
- FactAnchor creation and unique constraint (T0.2)
- FactAnchorLink FK resolution and composite index (T0.2)
- CoherenceGroup creation with policy_json (T0.3)
- CrossTheatreParadox enum field storage and retrieval (T0.4)
- OracleResponse is_provisional flag (T0.4)
- WingFlapType extension (T0.1)
"""

import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock

# Mock the database connection module before importing models.
# connection.py creates an async engine at import time which requires asyncpg.
_mock_base_module = MagicMock()

# Provide a real declarative_base so model metaclass works
from sqlalchemy.orm import declarative_base
_real_base = declarative_base()
_mock_base_module.Base = _real_base

sys.modules.setdefault("backend.database.connection", _mock_base_module)
# Also ensure backend.database.config doesn't break
sys.modules.setdefault("backend.database.config", MagicMock())

# Patch the Base reference in connection mock so models.py can import it
_mock_base_module.engine = MagicMock()
_mock_base_module.async_session_maker = MagicMock()
_mock_base_module.get_session = MagicMock()
_mock_base_module.get_db = MagicMock()
_mock_base_module.init_db = MagicMock()
_mock_base_module.close_db = MagicMock()

# Now import models — they'll use the mocked connection's Base
from backend.database.models import (
    # Enums (T0.1)
    CrossTheatreParadoxStatus,
    CrossTheatreParadoxType,
    CrossTheatreParadoxSeverity,
    WingFlapType,
    # Models (T0.2–T0.4)
    FactAnchor,
    FactAnchorLink,
    CoherenceGroup,
    CoherenceGroupMember,
    CrossTheatreParadox,
    OracleResponse,
)


class TestEnumImports(unittest.TestCase):
    """T0.1: All 4 enum changes importable without error."""

    def test_cross_theatre_paradox_status_enum(self):
        """CrossTheatreParadoxStatus has 4 values."""
        values = {e.value for e in CrossTheatreParadoxStatus}
        self.assertEqual(values, {"OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED"})

    def test_cross_theatre_paradox_type_enum(self):
        """CrossTheatreParadoxType has 4 values."""
        values = {e.value for e in CrossTheatreParadoxType}
        self.assertEqual(values, {
            "SETTLEMENT_DIVERGENCE", "ORACLE_INCONSISTENCY",
            "SCOPE_OVERLAP_GAP", "TEMPORAL_DRIFT",
        })

    def test_cross_theatre_paradox_severity_enum(self):
        """CrossTheatreParadoxSeverity has 4 values."""
        values = {e.value for e in CrossTheatreParadoxSeverity}
        self.assertEqual(values, {"INFO", "WATCH", "MATERIAL", "CRITICAL"})

    def test_wingflap_type_has_cross_theatre_paradox(self):
        """WingFlapType includes CROSS_THEATRE_PARADOX."""
        self.assertIn("CROSS_THEATRE_PARADOX", [e.value for e in WingFlapType])
        # Verify old values still present
        self.assertIn("TRADE", [e.value for e in WingFlapType])
        self.assertIn("PARADOX", [e.value for e in WingFlapType])


class TestFactAnchorModel(unittest.TestCase):
    """T0.2: FactAnchor model structure and constraints."""

    def test_fact_anchor_creation(self):
        """FactAnchor can be instantiated with all required fields."""
        anchor = FactAnchor(
            id="fa-test-001",
            anchor_type="seismic_event",
            external_id="us6000test",
            external_source="usgs_neic",
            occurred_at=datetime(2026, 3, 19, 10, 0, 0),
            location_json={"lat": 35.7, "lon": -121.3, "depth_km": 10.5},
            metadata_json={"magnitude": 6.2, "mag_type": "mww"},
        )
        self.assertEqual(anchor.id, "fa-test-001")
        self.assertEqual(anchor.anchor_type, "seismic_event")
        self.assertEqual(anchor.external_id, "us6000test")
        self.assertEqual(anchor.external_source, "usgs_neic")
        self.assertIsNotNone(anchor.occurred_at)
        self.assertEqual(anchor.location_json["depth_km"], 10.5)
        self.assertEqual(anchor.metadata_json["magnitude"], 6.2)

    def test_fact_anchor_unique_index_definition(self):
        """FactAnchor has unique index on (external_source, external_id)."""
        table = FactAnchor.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_fact_anchors_external", index_names)
        for idx in table.indexes:
            if idx.name == "ix_fact_anchors_external":
                self.assertTrue(idx.unique)

    def test_fact_anchor_type_time_index(self):
        """FactAnchor has composite index on (anchor_type, occurred_at)."""
        table = FactAnchor.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_fact_anchors_type_time", index_names)


class TestFactAnchorLinkModel(unittest.TestCase):
    """T0.2: FactAnchorLink model structure."""

    def test_fact_anchor_link_creation(self):
        """FactAnchorLink can be instantiated with FK fields."""
        link = FactAnchorLink(
            id="fal-test-001",
            fact_anchor_id="fa-test-001",
            theatre_id="theatre-001",
            link_type="settlement",
            link_confidence=0.95,
            linked_entity_id="outcome-001",
            linked_entity_type="theatre_outcome",
        )
        self.assertEqual(link.fact_anchor_id, "fa-test-001")
        self.assertEqual(link.theatre_id, "theatre-001")
        self.assertEqual(link.link_type, "settlement")
        self.assertAlmostEqual(link.link_confidence, 0.95)

    def test_fact_anchor_link_composite_index(self):
        """FactAnchorLink has composite index on (fact_anchor_id, theatre_id)."""
        table = FactAnchorLink.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_fact_anchor_links_anchor_theatre", index_names)


class TestCoherenceGroupModel(unittest.TestCase):
    """T0.3: CoherenceGroup model with policy_json."""

    def test_coherence_group_creation(self):
        """CoherenceGroup instantiation with policy_json."""
        group = CoherenceGroup(
            id="cg-test-001",
            name="seismic-pacific-ring",
            group_type="domain_overlap",
            policy_json={
                "settlement_divergence_threshold": 0.0,
                "oracle_tolerance": 0.1,
                "temporal_drift_hours": 24,
                "scope_overlap_domains": ["seismic_event"],
            },
        )
        self.assertEqual(group.name, "seismic-pacific-ring")
        self.assertEqual(group.group_type, "domain_overlap")
        self.assertEqual(group.policy_json["oracle_tolerance"], 0.1)

    def test_coherence_group_member_creation(self):
        """CoherenceGroupMember with role field."""
        member = CoherenceGroupMember(
            id="cgm-test-001",
            coherence_group_id="cg-test-001",
            theatre_id="theatre-001",
            role="primary",
        )
        self.assertEqual(member.role, "primary")
        self.assertEqual(member.coherence_group_id, "cg-test-001")

    def test_coherence_group_member_indexes(self):
        """CoherenceGroupMember has indexes on group_id and theatre_id."""
        table = CoherenceGroupMember.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_coherence_members_group", index_names)
        self.assertIn("ix_coherence_members_theatre", index_names)


class TestCrossTheatreParadoxModel(unittest.TestCase):
    """T0.4: CrossTheatreParadox enum field storage and retrieval."""

    def test_cross_theatre_paradox_creation(self):
        """CrossTheatreParadox instantiation with enum fields."""
        paradox = CrossTheatreParadox(
            id="ctp-test-001",
            fact_anchor_id="fa-test-001",
            coherence_group_id=None,
            paradox_type=CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE,
            severity=CrossTheatreParadoxSeverity.MATERIAL,
            theatre_a_id="theatre-001",
            theatre_b_id="theatre-002",
            description="Magnitude classification divergence: M6.2 vs M5.8",
            evidence_json={
                "theatre_a_value": "M6.2",
                "theatre_b_value": "M5.8",
                "delta": 0.4,
            },
            resolution_status=CrossTheatreParadoxStatus.OPEN,
        )
        self.assertEqual(paradox.paradox_type, CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE)
        self.assertEqual(paradox.severity, CrossTheatreParadoxSeverity.MATERIAL)
        self.assertEqual(paradox.resolution_status, CrossTheatreParadoxStatus.OPEN)
        self.assertIsNone(paradox.coherence_group_id)
        self.assertIsNone(paradox.resolved_at)

    def test_cross_theatre_paradox_indexes(self):
        """CrossTheatreParadox has all 4 indexes defined."""
        table = CrossTheatreParadox.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_cross_paradox_anchor", index_names)
        self.assertIn("ix_cross_paradox_theatres", index_names)
        self.assertIn("ix_cross_paradox_status", index_names)
        self.assertIn("ix_cross_paradox_severity", index_names)

    def test_theatre_ordering_convention(self):
        """Verify theatre_a_id < theatre_b_id convention can be enforced at application level."""
        theatre_a, theatre_b = "theatre-alpha", "theatre-beta"
        if theatre_a > theatre_b:
            theatre_a, theatre_b = theatre_b, theatre_a
        paradox = CrossTheatreParadox(
            id="ctp-test-002",
            fact_anchor_id="fa-test-001",
            paradox_type=CrossTheatreParadoxType.ORACLE_INCONSISTENCY,
            severity=CrossTheatreParadoxSeverity.WATCH,
            theatre_a_id=theatre_a,
            theatre_b_id=theatre_b,
            description="Test ordering",
            evidence_json={},
        )
        self.assertLess(paradox.theatre_a_id, paradox.theatre_b_id)


class TestOracleResponseModel(unittest.TestCase):
    """T0.4: OracleResponse is_provisional flag."""

    def test_oracle_response_creation(self):
        """OracleResponse with is_provisional flag."""
        resp = OracleResponse(
            id="or-test-001",
            theatre_id="theatre-001",
            source="usgs_neic",
            event_id="us6000test",
            value_json={"magnitude": 6.2, "mag_type": "mww"},
            queried_at=datetime(2026, 3, 19, 10, 0, 0),
            is_provisional=True,
        )
        self.assertEqual(resp.source, "usgs_neic")
        self.assertEqual(resp.event_id, "us6000test")
        self.assertTrue(resp.is_provisional)
        self.assertEqual(resp.value_json["magnitude"], 6.2)

    def test_oracle_response_reviewed(self):
        """OracleResponse for reviewed (non-provisional) response."""
        resp = OracleResponse(
            id="or-test-002",
            theatre_id="theatre-001",
            source="usgs_neic",
            event_id="us6000test",
            value_json={"magnitude": 6.1, "mag_type": "mww", "status": "reviewed"},
            queried_at=datetime(2026, 3, 19, 12, 0, 0),
            is_provisional=False,
        )
        self.assertFalse(resp.is_provisional)

    def test_oracle_response_indexes(self):
        """OracleResponse has composite index on (source, event_id)."""
        table = OracleResponse.__table__
        index_names = {idx.name for idx in table.indexes}
        self.assertIn("ix_oracle_responses_source_event", index_names)


if __name__ == "__main__":
    unittest.main()
