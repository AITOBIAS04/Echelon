"""Tests for cycle-039: External Theatre Operations.

Covers registry schemas, run record schemas, in-memory store operations,
operations service, trigger/scheduling, reporting, and TREMOR+CORONA regression.
"""

import pytest
from datetime import datetime, timedelta

from backend.schemas.external_theatre_operations import (
    ExternalTheatreRegistryEntry,
    ExternalTheatreRunRecord,
    ExternalTheatreRunSummary,
    ExternalTheatreStatusReport,
    RegistryStatus,
    RunStatus,
)
from backend.services.external_theatre_registry_store import (
    ExternalTheatreRegistryStore,
)


# ===========================================================================
# Sprint 0 — Registry Models + Schemas
# ===========================================================================

class TestRegistrySchema:
    """Task 0.1: Registry entry schema validation."""

    def test_registry_entry_defaults(self):
        """Registry entry has correct defaults for status, is_active, timestamps."""
        entry = ExternalTheatreRegistryEntry(
            id="test-id",
            slug="tremor",
            version="0.1.0",
        )
        assert entry.status == RegistryStatus.ACTIVE
        assert entry.is_active is True
        assert entry.construct_class == "theatre"
        assert entry.latest_summary == {}
        assert isinstance(entry.created_at, datetime)

    def test_registry_entry_all_fields(self):
        """Registry entry accepts all SDD-specified fields."""
        now = datetime.utcnow()
        entry = ExternalTheatreRegistryEntry(
            id="full-id",
            slug="corona",
            version="0.2.0",
            construct_class="theatre",
            repo_path="/repos/corona",
            construct_json_path="/repos/corona/construct.json",
            status=RegistryStatus.INACTIVE,
            is_active=False,
            last_prepared_at=now,
            last_scanned_at=now,
            latest_summary={"total": 5},
            created_at=now,
            updated_at=now,
        )
        assert entry.slug == "corona"
        assert entry.repo_path == "/repos/corona"
        assert entry.last_prepared_at == now
        assert entry.latest_summary == {"total": 5}


class TestRunRecordSchema:
    """Task 0.2: Run record schema validation."""

    def test_run_record_defaults(self):
        """Run record has correct defaults for status, summaries."""
        run = ExternalTheatreRunRecord(
            id="run-1",
            theatre_slugs=["tremor", "corona"],
        )
        assert run.status == RunStatus.IN_PROGRESS
        assert run.completed_at is None
        assert run.preparation_summary == {}
        assert run.scan_summary == {}
        assert run.result_counts.total_theatres == 0
        assert run.feedback_snapshot == []

    def test_run_record_completed(self):
        """Run record can be populated with full results."""
        counts = ExternalTheatreRunSummary(
            total_theatres=2,
            total_successful=2,
            total_failed=0,
            candidate_count=1,
            total_scanned=1,
            total_with_findings=0,
            total_clean=1,
            has_paradox=False,
        )
        run = ExternalTheatreRunRecord(
            id="run-2",
            theatre_slugs=["tremor"],
            status=RunStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            spec_hash="abc123",
            contract_hash="def456",
            result_counts=counts,
        )
        assert run.status == RunStatus.COMPLETED
        assert run.result_counts.total_clean == 1
        assert run.result_counts.has_paradox is False
        assert run.spec_hash == "abc123"


class TestRunSummary:
    """Task 0.3: Run summary schema — no-paradox as positive state."""

    def test_no_paradox_explicit(self):
        """No-paradox is an explicit positive result, not absence of data."""
        summary = ExternalTheatreRunSummary(
            total_theatres=2,
            total_successful=2,
            total_failed=0,
            candidate_count=1,
            total_scanned=1,
            total_with_findings=0,
            total_clean=1,
            has_paradox=False,
        )
        assert summary.has_paradox is False
        assert summary.total_clean == 1
        assert summary.total_scanned == 1

    def test_paradox_detected(self):
        """Paradox detection is captured explicitly."""
        summary = ExternalTheatreRunSummary(
            total_theatres=2,
            total_successful=2,
            total_failed=0,
            candidate_count=1,
            total_scanned=1,
            total_with_findings=1,
            total_clean=0,
            has_paradox=True,
        )
        assert summary.has_paradox is True
        assert summary.total_with_findings == 1


class TestRegistryStore:
    """Task 0.4: In-memory store CRUD operations."""

    def test_register_and_get(self):
        """Register a theatre and retrieve by ID."""
        store = ExternalTheatreRegistryStore()
        entry = store.register(slug="tremor", version="0.1.0")
        assert entry.slug == "tremor"
        assert entry.is_active is True

        fetched = store.get(entry.id)
        assert fetched is not None
        assert fetched.slug == "tremor"

    def test_get_by_slug(self):
        """Retrieve a registry entry by slug."""
        store = ExternalTheatreRegistryStore()
        store.register(slug="tremor", version="0.1.0")
        store.register(slug="corona", version="0.2.0")

        found = store.get_by_slug("corona")
        assert found is not None
        assert found.slug == "corona"
        assert found.version == "0.2.0"

    def test_list_all_and_active(self):
        """List all vs active-only filtering."""
        store = ExternalTheatreRegistryStore()
        t = store.register(slug="tremor", version="0.1.0")
        c = store.register(slug="corona", version="0.2.0")
        store.deactivate(c.id)

        all_entries = store.list_all()
        active = store.list_active()
        assert len(all_entries) == 2
        assert len(active) == 1
        assert active[0].slug == "tremor"

    def test_deactivate_and_activate(self):
        """Deactivate and reactivate a theatre."""
        store = ExternalTheatreRegistryStore()
        entry = store.register(slug="tremor", version="0.1.0")

        deactivated = store.deactivate(entry.id)
        assert deactivated is not None
        assert deactivated.is_active is False
        assert deactivated.status == RegistryStatus.INACTIVE

        reactivated = store.activate(entry.id)
        assert reactivated is not None
        assert reactivated.is_active is True
        assert reactivated.status == RegistryStatus.ACTIVE

    def test_create_and_complete_run(self):
        """Create a run record and complete it with results."""
        store = ExternalTheatreRegistryStore()
        run = store.create_run(
            theatre_slugs=["tremor", "corona"],
            spec_hash="hash1",
        )
        assert run.status == RunStatus.IN_PROGRESS
        assert run.theatre_slugs == ["tremor", "corona"]

        counts = ExternalTheatreRunSummary(
            total_theatres=2, total_successful=2, total_failed=0,
            candidate_count=1, total_scanned=1,
            total_with_findings=0, total_clean=1, has_paradox=False,
        )
        completed = store.complete_run(
            run_id=run.id,
            preparation_summary={"ok": True},
            scan_summary={"clean": True},
            result_counts=counts,
        )
        assert completed is not None
        assert completed.status == RunStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.result_counts.total_clean == 1

    def test_fail_run(self):
        """Mark a run as failed."""
        store = ExternalTheatreRegistryStore()
        run = store.create_run(theatre_slugs=["tremor"])
        failed = store.fail_run(run.id, error_summary={"error": "parse failed"})
        assert failed is not None
        assert failed.status == RunStatus.FAILED

    def test_has_active_run_idempotence(self):
        """Idempotence check: detect active run for same theatre set."""
        store = ExternalTheatreRegistryStore()
        run = store.create_run(theatre_slugs=["tremor", "corona"])

        # Same set should be detected
        active_id = store.has_active_run(["corona", "tremor"])
        assert active_id == run.id

        # Different set should not match
        assert store.has_active_run(["tremor"]) is None

        # After completion, no active run
        store.complete_run(
            run.id,
            preparation_summary={},
            scan_summary={},
            result_counts=ExternalTheatreRunSummary(),
        )
        assert store.has_active_run(["tremor", "corona"]) is None

    def test_list_runs_with_filters(self):
        """List runs with slug and status filters."""
        store = ExternalTheatreRegistryStore()
        r1 = store.create_run(theatre_slugs=["tremor"])
        r2 = store.create_run(theatre_slugs=["corona"])
        store.complete_run(
            r1.id,
            preparation_summary={},
            scan_summary={},
            result_counts=ExternalTheatreRunSummary(),
        )

        # Filter by slug
        tremor_runs = store.list_runs(theatre_slug="tremor")
        assert len(tremor_runs) == 1
        assert tremor_runs[0].theatre_slugs == ["tremor"]

        # Filter by status
        in_progress = store.list_runs(status=RunStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].id == r2.id
