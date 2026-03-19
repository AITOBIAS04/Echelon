"""In-memory store for external theatre registry and run records.

Cycle 039: External Theatre Operations — Sprint 0.

V1 persistence layer: thread-safe in-memory dicts.
Progressive tier: V2 can swap to SQLAlchemy/PostgreSQL backend
without changing the operations service API.

This is a pure synchronous service — no DB, no AsyncSession.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from backend.schemas.external_theatre_operations import (
    ExternalTheatreRegistryEntry,
    ExternalTheatreRunRecord,
    ExternalTheatreRunSummary,
    RegistryStatus,
    RunStatus,
)

logger = logging.getLogger(__name__)


class ExternalTheatreRegistryStore:
    """In-memory store for external theatre registries and run records.

    All mutations return the affected object. Reads return copies
    to prevent accidental mutation of store state.
    """

    def __init__(self) -> None:
        self._registries: dict[str, ExternalTheatreRegistryEntry] = {}
        self._runs: dict[str, ExternalTheatreRunRecord] = {}

    # -------------------------------------------------------------------
    # Registry CRUD
    # -------------------------------------------------------------------

    def register(
        self,
        slug: str,
        version: str,
        construct_class: str = "theatre",
        repo_path: str = "",
        construct_json_path: str = "",
    ) -> ExternalTheatreRegistryEntry:
        """Register a new external theatre. Returns the created entry."""
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow()
        entry = ExternalTheatreRegistryEntry(
            id=entry_id,
            slug=slug,
            version=version,
            construct_class=construct_class,
            repo_path=repo_path,
            construct_json_path=construct_json_path,
            status=RegistryStatus.ACTIVE,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._registries[entry_id] = entry
        logger.info("Registered external theatre: %s v%s (id=%s)", slug, version, entry_id)
        return entry.model_copy()

    def get(self, entry_id: str) -> Optional[ExternalTheatreRegistryEntry]:
        """Get a registry entry by ID. Returns None if not found."""
        entry = self._registries.get(entry_id)
        return entry.model_copy() if entry else None

    def get_by_slug(self, slug: str) -> Optional[ExternalTheatreRegistryEntry]:
        """Get a registry entry by slug. Returns the first match."""
        for entry in self._registries.values():
            if entry.slug == slug:
                return entry.model_copy()
        return None

    def list_all(self) -> list[ExternalTheatreRegistryEntry]:
        """List all registry entries."""
        return [e.model_copy() for e in self._registries.values()]

    def list_active(self) -> list[ExternalTheatreRegistryEntry]:
        """List only active registry entries."""
        return [e.model_copy() for e in self._registries.values() if e.is_active]

    def deactivate(self, entry_id: str) -> Optional[ExternalTheatreRegistryEntry]:
        """Mark a registry entry as inactive. Returns updated entry or None."""
        entry = self._registries.get(entry_id)
        if entry is None:
            return None
        entry.is_active = False
        entry.status = RegistryStatus.INACTIVE
        entry.updated_at = datetime.utcnow()
        return entry.model_copy()

    def activate(self, entry_id: str) -> Optional[ExternalTheatreRegistryEntry]:
        """Mark a registry entry as active. Returns updated entry or None."""
        entry = self._registries.get(entry_id)
        if entry is None:
            return None
        entry.is_active = True
        entry.status = RegistryStatus.ACTIVE
        entry.updated_at = datetime.utcnow()
        return entry.model_copy()

    def update_latest_summary(
        self,
        entry_id: str,
        summary: dict,
        prepared_at: Optional[datetime] = None,
        scanned_at: Optional[datetime] = None,
    ) -> Optional[ExternalTheatreRegistryEntry]:
        """Update the latest run summary on a registry entry."""
        entry = self._registries.get(entry_id)
        if entry is None:
            return None
        entry.latest_summary = summary
        if prepared_at:
            entry.last_prepared_at = prepared_at
        if scanned_at:
            entry.last_scanned_at = scanned_at
        entry.updated_at = datetime.utcnow()
        return entry.model_copy()

    # -------------------------------------------------------------------
    # Run Record CRUD
    # -------------------------------------------------------------------

    def create_run(
        self,
        theatre_slugs: list[str],
        spec_hash: Optional[str] = None,
        contract_hash: Optional[str] = None,
    ) -> ExternalTheatreRunRecord:
        """Create a new run record in IN_PROGRESS state."""
        run_id = str(uuid.uuid4())
        run = ExternalTheatreRunRecord(
            id=run_id,
            theatre_slugs=theatre_slugs,
            started_at=datetime.utcnow(),
            status=RunStatus.IN_PROGRESS,
            spec_hash=spec_hash,
            contract_hash=contract_hash,
        )
        self._runs[run_id] = run
        logger.info("Created run %s for theatres: %s", run_id, theatre_slugs)
        return run.model_copy()

    def complete_run(
        self,
        run_id: str,
        preparation_summary: dict,
        scan_summary: dict,
        result_counts: ExternalTheatreRunSummary,
        feedback_snapshot: Optional[list[dict]] = None,
    ) -> Optional[ExternalTheatreRunRecord]:
        """Mark a run as COMPLETED with results."""
        run = self._runs.get(run_id)
        if run is None:
            return None
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        run.preparation_summary = preparation_summary
        run.scan_summary = scan_summary
        run.result_counts = result_counts
        if feedback_snapshot is not None:
            run.feedback_snapshot = feedback_snapshot
        return run.model_copy()

    def fail_run(
        self,
        run_id: str,
        error_summary: Optional[dict] = None,
    ) -> Optional[ExternalTheatreRunRecord]:
        """Mark a run as FAILED."""
        run = self._runs.get(run_id)
        if run is None:
            return None
        run.status = RunStatus.FAILED
        run.completed_at = datetime.utcnow()
        if error_summary:
            run.preparation_summary = error_summary
        return run.model_copy()

    def get_run(self, run_id: str) -> Optional[ExternalTheatreRunRecord]:
        """Get a run record by ID."""
        run = self._runs.get(run_id)
        return run.model_copy() if run else None

    def list_runs(
        self,
        theatre_slug: Optional[str] = None,
        status: Optional[RunStatus] = None,
        limit: int = 50,
    ) -> list[ExternalTheatreRunRecord]:
        """List run records with optional filters, newest first."""
        runs = list(self._runs.values())
        if theatre_slug:
            runs = [r for r in runs if theatre_slug in r.theatre_slugs]
        if status:
            runs = [r for r in runs if r.status == status]
        runs.sort(key=lambda r: r.started_at, reverse=True)
        return [r.model_copy() for r in runs[:limit]]

    def has_active_run(self, theatre_slugs: list[str]) -> Optional[str]:
        """Check if there's an IN_PROGRESS run for the given theatre set.

        Returns the run ID if found, None otherwise.
        Used for idempotence enforcement.
        """
        slug_set = set(theatre_slugs)
        for run in self._runs.values():
            if run.status == RunStatus.IN_PROGRESS and set(run.theatre_slugs) == slug_set:
                return run.id
        return None

    # -------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------

    @staticmethod
    def compute_spec_hash(construct_json: str) -> str:
        """Compute a stable hash of construct.json content."""
        return hashlib.sha256(construct_json.encode()).hexdigest()[:16]

    def clear(self) -> None:
        """Clear all data. For testing only."""
        self._registries.clear()
        self._runs.clear()
