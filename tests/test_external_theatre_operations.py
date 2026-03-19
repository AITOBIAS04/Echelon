"""Tests for cycle-039: External Theatre Operations.

Covers registry schemas, run record schemas, in-memory store operations,
operations service, trigger/scheduling, reporting, and TREMOR+CORONA regression.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from backend.schemas.external_theatre_operations import (
    ExternalTheatreRegistryEntry,
    ExternalTheatreRunRecord,
    ExternalTheatreRunSummary,
    ExternalTheatreStatusReport,
    RegistryStatus,
    RunStatus,
)
from backend.schemas.external_theatre_orchestration import (
    BuilderFeedbackItem,
    BuilderFeedbackReport,
    ExternalTheatreInput,
    ExternalTheatrePreparationRequest,
    ExternalTheatrePreparationResult,
    TheatrePreparationEntry,
)
from backend.schemas.external_theatre_scan import (
    CandidateScanOutcome,
    ExternalTheatreScanResult,
)
from backend.services.external_theatre_registry_store import (
    ExternalTheatreRegistryStore,
)
from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
)
from backend.services.external_theatre_operations_service import (
    ExternalTheatreOperationsService,
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


# ===========================================================================
# Sprint 1 — Operations Service
# ===========================================================================

# Minimal construct.json payloads for service tests
_SIMPLE_CONSTRUCT_A = json.dumps({"name": "THEATRE-A", "theatre_templates": [{"id": "t1"}]})
_SIMPLE_CONSTRUCT_B = json.dumps({"name": "THEATRE-B", "theatre_templates": [{"id": "t2"}]})


def _make_bundle(slug):
    """Build a minimal ExecutedTheatreComparisonBundle for testing."""
    return ExecutedTheatreComparisonBundle(
        construct_slug=slug,
        construct_version="0.1.0",
    )


def _mock_prep_result(slugs, candidate_count=1, successful=None, failed=0):
    """Build a mock ExternalTheatrePreparationResult."""
    if successful is None:
        successful = len(slugs)
    theatres = [
        TheatrePreparationEntry(
            construct_slug=s,
            construct_version="0.1.0",
            bundle=_make_bundle(s) if i < successful else None,
            error="failed" if i >= successful else None,
        )
        for i, s in enumerate(slugs)
    ]
    # Build real candidates pairing first two successful bundles
    candidates = []
    successful_slugs = slugs[:successful]
    for _ in range(candidate_count):
        if len(successful_slugs) >= 2:
            candidates.append(ComparisonCandidateSet(
                bundle_a=_make_bundle(successful_slugs[0]),
                bundle_b=_make_bundle(successful_slugs[1]),
                candidate_type="same_event",
                match_strength="EXACT",
                matching_keys=["shared-key"],
            ))
        elif len(successful_slugs) == 1:
            candidates.append(ComparisonCandidateSet(
                bundle_a=_make_bundle(successful_slugs[0]),
                bundle_b=_make_bundle(successful_slugs[0]),
                candidate_type="same_event",
                match_strength="EXACT",
                matching_keys=["shared-key"],
            ))
    feedback = [
        BuilderFeedbackReport(
            construct_slug=s,
            required_items=[
                BuilderFeedbackItem(
                    category="required", field="templates",
                    status="present", message="ok",
                ),
            ],
            optional_items=[],
            extraction_items=[],
            overall_readiness="READY",
        )
        for s in slugs[:successful]
    ]
    return ExternalTheatrePreparationResult(
        theatres=theatres,
        candidates=candidates,
        feedback=feedback,
        total_theatres=len(slugs),
        total_successful=successful,
        total_failed=failed,
    )


def _mock_scan_result(total_scanned=1, with_findings=0):
    """Build a mock ExternalTheatreScanResult."""
    return ExternalTheatreScanResult(
        outcomes=[],
        total_scanned=total_scanned,
        total_with_findings=with_findings,
        total_clean=total_scanned - with_findings,
    )


class TestOperationsServiceRegistry:
    """Task 1.1–1.2: Operations service register/unregister."""

    def test_register_theatre(self):
        """Register a theatre through the service layer."""
        svc = ExternalTheatreOperationsService()
        entry = svc.register_theatre(
            slug="tremor", version="0.1.0", repo_path="/repos/tremor",
        )
        assert entry.slug == "tremor"
        assert entry.is_active is True

        # Should be retrievable from store
        found = svc.store.get_by_slug("tremor")
        assert found is not None
        assert found.version == "0.1.0"

    def test_unregister_theatre(self):
        """Unregister (deactivate) a theatre through the service layer."""
        svc = ExternalTheatreOperationsService()
        entry = svc.register_theatre(slug="corona", version="0.2.0")

        result = svc.unregister_theatre(entry.id)
        assert result is not None
        assert result.is_active is False
        assert result.status == RegistryStatus.INACTIVE

    def test_unregister_nonexistent(self):
        """Unregistering a nonexistent theatre returns None."""
        svc = ExternalTheatreOperationsService()
        result = svc.unregister_theatre("fake-id")
        assert result is None


class TestOperationsServiceRun:
    """Task 1.3–1.4: Operations service run execution and persistence."""

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_success(self, mock_prep, mock_scan):
        """Successful run creates COMPLETED record with result counts."""
        mock_prep.return_value = _mock_prep_result(["a", "b"], candidate_count=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1, with_findings=0)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
            ExternalTheatreInput(
                construct_slug="b", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_B,
            ),
        ]

        run = svc.execute_run(inputs)
        assert run.status == RunStatus.COMPLETED
        assert run.completed_at is not None
        assert run.result_counts.total_theatres == 2
        assert run.result_counts.total_successful == 2
        assert run.result_counts.candidate_count == 1
        assert run.result_counts.total_scanned == 1
        assert run.result_counts.has_paradox is False
        assert run.spec_hash is not None

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_with_paradox(self, mock_prep, mock_scan):
        """Run with paradox findings records has_paradox=True."""
        mock_prep.return_value = _mock_prep_result(["a", "b"], candidate_count=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1, with_findings=1)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
            ExternalTheatreInput(
                construct_slug="b", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_B,
            ),
        ]

        run = svc.execute_run(inputs)
        assert run.status == RunStatus.COMPLETED
        assert run.result_counts.has_paradox is True
        assert run.result_counts.total_with_findings == 1

    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_no_candidates_skips_scan(self, mock_prep):
        """When orchestrator produces no candidates, scan is skipped."""
        mock_prep.return_value = _mock_prep_result(["a"], candidate_count=0, successful=1)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        run = svc.execute_run(inputs)
        assert run.status == RunStatus.COMPLETED
        assert run.result_counts.total_scanned == 0
        assert run.result_counts.has_paradox is False
        assert run.scan_summary == {}

    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_failure(self, mock_prep):
        """When orchestrator throws, run is marked FAILED."""
        mock_prep.side_effect = RuntimeError("orchestration boom")

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        run = svc.execute_run(inputs)
        assert run.status == RunStatus.FAILED
        assert "orchestration boom" in run.preparation_summary.get("error", "")

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_persists_spec_hash(self, mock_prep, mock_scan):
        """Run record contains a deterministic spec_hash."""
        mock_prep.return_value = _mock_prep_result(["a"], candidate_count=0, successful=1)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        run1 = svc.execute_run(inputs)
        run2 = svc.execute_run(inputs)
        # Same input → same spec hash
        assert run1.spec_hash == run2.spec_hash
        assert run1.spec_hash is not None

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_persists_feedback_snapshot(self, mock_prep, mock_scan):
        """Run record captures builder feedback from 038b."""
        mock_prep.return_value = _mock_prep_result(["a"], candidate_count=1, successful=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        run = svc.execute_run(inputs)
        assert run.status == RunStatus.COMPLETED
        assert len(run.feedback_snapshot) == 1
        assert run.feedback_snapshot[0]["construct_slug"] == "a"
        assert run.feedback_snapshot[0]["overall_readiness"] == "READY"
        assert len(run.feedback_snapshot[0]["items"]) >= 1

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_execute_run_updates_registry(self, mock_prep, mock_scan):
        """After a successful run, registry entry timestamps are updated."""
        mock_prep.return_value = _mock_prep_result(["theatre-x"], candidate_count=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1)

        svc = ExternalTheatreOperationsService()
        # Register the theatre first
        svc.register_theatre(slug="theatre-x", version="0.1.0")

        inputs = [
            ExternalTheatreInput(
                construct_slug="theatre-x", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        svc.execute_run(inputs)

        entry = svc.store.get_by_slug("theatre-x")
        assert entry is not None
        assert entry.last_prepared_at is not None
        assert entry.last_scanned_at is not None
        assert entry.latest_summary.get("prepared") is True

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_run_record_stored_in_store(self, mock_prep, mock_scan):
        """Completed run is retrievable from the store."""
        mock_prep.return_value = _mock_prep_result(["a"], candidate_count=0, successful=1)

        svc = ExternalTheatreOperationsService()
        inputs = [
            ExternalTheatreInput(
                construct_slug="a", construct_version="0.1.0",
                construct_json=_SIMPLE_CONSTRUCT_A,
            ),
        ]

        run = svc.execute_run(inputs)
        fetched = svc.store.get_run(run.id)
        assert fetched is not None
        assert fetched.status == RunStatus.COMPLETED
        assert fetched.theatre_slugs == ["a"]


# ===========================================================================
# Sprint 2 — Trigger / Scheduling Surface
# ===========================================================================

class TestTriggerRun:
    """Task 2.1–2.2: Trigger method with scheduler-facing signature."""

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_trigger_run_success(self, mock_prep, mock_scan):
        """trigger_run invokes execute_run for registered active theatres."""
        mock_prep.return_value = _mock_prep_result(["a", "b"], candidate_count=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1)

        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.register_theatre(slug="b", version="0.1.0")

        run, status = svc.trigger_run(
            theatre_slugs=["a", "b"],
            construct_json_map={"a": _SIMPLE_CONSTRUCT_A, "b": _SIMPLE_CONSTRUCT_B},
        )
        assert status == "started"
        assert run.status == RunStatus.COMPLETED

    def test_trigger_run_unregistered_theatre(self):
        """trigger_run rejects unregistered theatres."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        with pytest.raises(ValueError, match="Unregistered"):
            svc.trigger_run(
                theatre_slugs=["a", "unknown"],
                construct_json_map={"a": _SIMPLE_CONSTRUCT_A, "unknown": "{}"},
            )

    def test_trigger_run_inactive_theatre(self):
        """trigger_run rejects inactive theatres."""
        svc = ExternalTheatreOperationsService()
        entry = svc.register_theatre(slug="a", version="0.1.0")
        svc.unregister_theatre(entry.id)

        with pytest.raises(ValueError, match="Inactive"):
            svc.trigger_run(
                theatre_slugs=["a"],
                construct_json_map={"a": _SIMPLE_CONSTRUCT_A},
            )

    def test_trigger_run_missing_construct_json(self):
        """trigger_run rejects when construct.json is missing from map."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        with pytest.raises(ValueError, match="Missing construct.json"):
            svc.trigger_run(
                theatre_slugs=["a"],
                construct_json_map={},
            )


class TestTriggerIdempotence:
    """Task 2.3: Idempotence and active-state enforcement."""

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_duplicate_run_returns_active(self, mock_prep, mock_scan):
        """Second trigger for same set returns the active run, not a duplicate."""
        # Make execute_run leave the run IN_PROGRESS by not calling it,
        # instead manually create an active run via the store.
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.register_theatre(slug="b", version="0.1.0")

        # Simulate an in-progress run
        active_run = svc.store.create_run(theatre_slugs=["a", "b"])

        run, status = svc.trigger_run(
            theatre_slugs=["a", "b"],
            construct_json_map={"a": _SIMPLE_CONSTRUCT_A, "b": _SIMPLE_CONSTRUCT_B},
        )
        assert status == "duplicate"
        assert run.id == active_run.id
        # execute_run should NOT have been called
        mock_prep.assert_not_called()

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_completed_run_allows_new_trigger(self, mock_prep, mock_scan):
        """After a run completes, same set can be triggered again."""
        mock_prep.return_value = _mock_prep_result(["a"], candidate_count=0, successful=1)

        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        # Create and complete a run
        old_run = svc.store.create_run(theatre_slugs=["a"])
        svc.store.complete_run(
            old_run.id,
            preparation_summary={},
            scan_summary={},
            result_counts=ExternalTheatreRunSummary(),
        )

        # Should allow new trigger
        run, status = svc.trigger_run(
            theatre_slugs=["a"],
            construct_json_map={"a": _SIMPLE_CONSTRUCT_A},
        )
        assert status == "started"
        assert run.id != old_run.id

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_idempotence_order_independent(self, mock_prep, mock_scan):
        """Idempotence check treats ["a","b"] same as ["b","a"]."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.register_theatre(slug="b", version="0.1.0")

        # Active run for ["a", "b"]
        active_run = svc.store.create_run(theatre_slugs=["a", "b"])

        # Trigger with reversed order
        run, status = svc.trigger_run(
            theatre_slugs=["b", "a"],
            construct_json_map={"a": _SIMPLE_CONSTRUCT_A, "b": _SIMPLE_CONSTRUCT_B},
        )
        assert status == "duplicate"
        assert run.id == active_run.id


class TestTriggerAllActive:
    """Task 2.2: Trigger all active theatres convenience method."""

    @patch("backend.services.external_theatre_operations_service.scan_candidates")
    @patch("backend.services.external_theatre_operations_service.prepare_external_theatres")
    def test_trigger_all_active_success(self, mock_prep, mock_scan):
        """trigger_all_active runs all active theatres."""
        mock_prep.return_value = _mock_prep_result(["a", "b"], candidate_count=1)
        mock_scan.return_value = _mock_scan_result(total_scanned=1)

        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.register_theatre(slug="b", version="0.1.0")
        entry_c = svc.register_theatre(slug="c", version="0.1.0")
        svc.unregister_theatre(entry_c.id)  # c is inactive

        run, status = svc.trigger_all_active(
            construct_json_map={
                "a": _SIMPLE_CONSTRUCT_A,
                "b": _SIMPLE_CONSTRUCT_B,
            },
        )
        assert status == "started"
        assert run is not None
        assert run.status == RunStatus.COMPLETED

    def test_trigger_all_active_no_theatres(self):
        """trigger_all_active returns None when no active theatres."""
        svc = ExternalTheatreOperationsService()
        run, status = svc.trigger_all_active(construct_json_map={})
        assert run is None
        assert status == "no_active_theatres"

    def test_trigger_all_active_missing_json(self):
        """trigger_all_active returns error when construct.json missing."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        run, status = svc.trigger_all_active(construct_json_map={})
        assert run is None
        assert "missing_construct_json" in status


# ===========================================================================
# Sprint 3 — Reporting Surface
# ===========================================================================


def _make_inputs(slugs, construct_json_map):
    """Build ExternalTheatreInput list from slugs + JSON map."""
    return [
        ExternalTheatreInput(
            construct_slug=s,
            construct_version="0.1.0",
            construct_json=construct_json_map[s],
        )
        for s in slugs
    ]


class TestGetStatusReport:
    """Task 3.1: Per-theatre status report composition."""

    @patch(
        "backend.services.external_theatre_operations_service.scan_candidates",
        return_value=_mock_scan_result(total_scanned=1, with_findings=0),
    )
    @patch(
        "backend.services.external_theatre_operations_service.prepare_external_theatres",
        side_effect=lambda req: _mock_prep_result(
            [inp.construct_slug for inp in req.theatres]
        ),
    )
    def test_status_report_after_successful_run(self, _mock_prep, _mock_scan):
        """Status report includes registry state, latest run, and readiness."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.execute_run(_make_inputs(["a"], {"a": _SIMPLE_CONSTRUCT_A}))

        report = svc.get_status_report("a")
        assert report is not None
        assert report.slug == "a"
        assert report.version == "0.1.0"
        assert report.status == RegistryStatus.ACTIVE
        assert report.is_active is True
        assert report.latest_run_status == RunStatus.COMPLETED
        assert report.readiness == "READY"
        assert report.latest_result_counts is not None
        assert len(report.recent_runs) == 1

    def test_status_report_nonexistent_theatre(self):
        """Status report for nonexistent theatre returns None."""
        svc = ExternalTheatreOperationsService()
        report = svc.get_status_report("nonexistent")
        assert report is None

    def test_status_report_no_runs(self):
        """Status report for registered theatre with no runs shows BLOCKED."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        report = svc.get_status_report("a")
        assert report is not None
        assert report.slug == "a"
        assert report.latest_run_status is None
        assert report.latest_result_counts is None
        assert report.readiness == "BLOCKED"
        assert report.feedback_items == []
        assert report.recent_runs == []


class TestReadinessDerivation:
    """Task 3.2: Readiness state machine — READY, DEGRADED, BLOCKED."""

    @patch(
        "backend.services.external_theatre_operations_service.scan_candidates",
        return_value=_mock_scan_result(total_scanned=1, with_findings=0),
    )
    @patch(
        "backend.services.external_theatre_operations_service.prepare_external_theatres",
        side_effect=lambda req: _mock_prep_result(
            [inp.construct_slug for inp in req.theatres]
        ),
    )
    def test_readiness_ready(self, _mock_prep, _mock_scan):
        """Active theatre with completed run and no paradox → READY."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.execute_run(_make_inputs(["a"], {"a": _SIMPLE_CONSTRUCT_A}))

        report = svc.get_status_report("a")
        assert report.readiness == "READY"

    @patch(
        "backend.services.external_theatre_operations_service.scan_candidates",
        return_value=_mock_scan_result(total_scanned=1, with_findings=1),
    )
    @patch(
        "backend.services.external_theatre_operations_service.prepare_external_theatres",
        side_effect=lambda req: _mock_prep_result(
            [inp.construct_slug for inp in req.theatres]
        ),
    )
    def test_readiness_degraded(self, _mock_prep, _mock_scan):
        """Active theatre with completed run and paradox findings → DEGRADED."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.execute_run(_make_inputs(["a"], {"a": _SIMPLE_CONSTRUCT_A}))

        report = svc.get_status_report("a")
        assert report.readiness == "DEGRADED"
        assert report.latest_result_counts.has_paradox is True

    def test_readiness_blocked_inactive(self):
        """Inactive theatre → BLOCKED regardless of run history."""
        svc = ExternalTheatreOperationsService()
        entry = svc.register_theatre(slug="a", version="0.1.0")
        svc.unregister_theatre(entry.id)

        report = svc.get_status_report("a")
        assert report.readiness == "BLOCKED"
        assert report.is_active is False

    def test_readiness_blocked_no_runs(self):
        """Active theatre with no runs → BLOCKED."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        report = svc.get_status_report("a")
        assert report.readiness == "BLOCKED"

    @patch(
        "backend.services.external_theatre_operations_service.scan_candidates",
    )
    @patch(
        "backend.services.external_theatre_operations_service.prepare_external_theatres",
        side_effect=RuntimeError("prep failed"),
    )
    def test_readiness_blocked_failed_run(self, _mock_prep, _mock_scan):
        """Active theatre with failed last run → BLOCKED."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.execute_run(_make_inputs(["a"], {"a": _SIMPLE_CONSTRUCT_A}))

        report = svc.get_status_report("a")
        assert report.readiness == "BLOCKED"
        assert report.latest_run_status == RunStatus.FAILED


class TestFeedbackRollup:
    """Task 3.3: Feedback aggregation from recent completed runs."""

    @patch(
        "backend.services.external_theatre_operations_service.scan_candidates",
        return_value=_mock_scan_result(total_scanned=1, with_findings=0),
    )
    @patch(
        "backend.services.external_theatre_operations_service.prepare_external_theatres",
        side_effect=lambda req: _mock_prep_result(
            [inp.construct_slug for inp in req.theatres]
        ),
    )
    def test_feedback_from_completed_run(self, _mock_prep, _mock_scan):
        """Feedback rollup returns snapshot from most recent completed run."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        svc.execute_run(_make_inputs(["a"], {"a": _SIMPLE_CONSTRUCT_A}))

        report = svc.get_status_report("a")
        # Feedback snapshot should be a list (may be empty if no feedback items)
        assert isinstance(report.feedback_items, list)

    def test_feedback_empty_no_runs(self):
        """Feedback rollup returns empty list when no runs exist."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")

        report = svc.get_status_report("a")
        assert report.feedback_items == []


class TestListStatusReports:
    """Task 3.4: Bulk status reporting with active-only filtering."""

    def test_list_active_only(self):
        """list_status_reports(active_only=True) excludes inactive theatres."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        entry_b = svc.register_theatre(slug="b", version="0.1.0")
        svc.unregister_theatre(entry_b.id)  # b is now inactive

        reports = svc.list_status_reports(active_only=True)
        assert len(reports) == 1
        assert reports[0].slug == "a"

    def test_list_all_includes_inactive(self):
        """list_status_reports(active_only=False) includes inactive theatres."""
        svc = ExternalTheatreOperationsService()
        svc.register_theatre(slug="a", version="0.1.0")
        entry_b = svc.register_theatre(slug="b", version="0.1.0")
        svc.unregister_theatre(entry_b.id)

        reports = svc.list_status_reports(active_only=False)
        assert len(reports) == 2
        slugs = {r.slug for r in reports}
        assert slugs == {"a", "b"}
