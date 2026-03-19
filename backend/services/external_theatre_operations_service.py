"""Operations service for external theatre lifecycle management.

Cycle 039: External Theatre Operations — Sprints 1–2.

Composition layer over:
- 038b orchestrator (prepare_external_theatres)
- 038c scan adapter (scan_candidates)
- 039 registry store (ExternalTheatreRegistryStore)

Responsibilities:
- Register/unregister external theatres
- Trigger preparation + scan runs
- Persist run outcomes to the registry store
- Compose 038b feedback into persisted snapshots

This service does NOT duplicate orchestration, candidate generation,
or scan logic — it delegates to the existing 038b/038c implementations
and persists the operational record.
"""

import logging
from typing import Optional

from backend.schemas.external_theatre_operations import (
    ExternalTheatreRegistryEntry,
    ExternalTheatreRunRecord,
    ExternalTheatreRunSummary,
    RunStatus,
)
from backend.schemas.external_theatre_orchestration import (
    ExternalTheatreInput,
    ExternalTheatrePreparationRequest,
    ExternalTheatrePreparationResult,
)
from backend.schemas.external_theatre_scan import (
    ExternalTheatreScanRequest,
    ExternalTheatreScanResult,
)
from backend.services.external_theatre_orchestrator import prepare_external_theatres
from backend.services.external_theatre_registry_store import (
    ExternalTheatreRegistryStore,
)
from backend.services.external_theatre_scan_adapter import scan_candidates

logger = logging.getLogger(__name__)


class ExternalTheatreOperationsService:
    """Composition layer: registry + orchestration + scan + persistence.

    Owns the full lifecycle:
    1. Register theatres → store
    2. Trigger run → 038b orchestrator → 038c scanner → persist results
    3. Query run status/history → store
    """

    def __init__(self, store: Optional[ExternalTheatreRegistryStore] = None) -> None:
        self._store = store or ExternalTheatreRegistryStore()

    @property
    def store(self) -> ExternalTheatreRegistryStore:
        """Expose store for direct queries (status, history)."""
        return self._store

    # -------------------------------------------------------------------
    # Registry operations
    # -------------------------------------------------------------------

    def register_theatre(
        self,
        slug: str,
        version: str,
        construct_class: str = "theatre",
        repo_path: str = "",
        construct_json_path: str = "",
    ) -> ExternalTheatreRegistryEntry:
        """Register an external theatre for operational management."""
        return self._store.register(
            slug=slug,
            version=version,
            construct_class=construct_class,
            repo_path=repo_path,
            construct_json_path=construct_json_path,
        )

    def unregister_theatre(self, entry_id: str) -> Optional[ExternalTheatreRegistryEntry]:
        """Deactivate an external theatre (soft delete)."""
        return self._store.deactivate(entry_id)

    # -------------------------------------------------------------------
    # Trigger / Scheduling Surface (Sprint 2)
    # -------------------------------------------------------------------

    def trigger_run(
        self,
        theatre_slugs: list[str],
        construct_json_map: dict[str, str],
        event_keys: Optional[list[str]] = None,
        scope_keys: Optional[list] = None,
        certificate_id: Optional[str] = None,
    ) -> tuple[ExternalTheatreRunRecord, str]:
        """Stable scheduler-facing entry point for triggering a run.

        This is the canonical invocation surface for cron jobs, scheduler
        hooks, or manual operator triggers. It enforces:
        1. All theatre slugs must be registered and active
        2. No duplicate IN_PROGRESS run for the same theatre set (idempotence)

        Args:
            theatre_slugs: List of registered theatre slugs to scan.
            construct_json_map: Mapping of slug → raw construct.json content.
            event_keys: Optional shared event keys for candidate generation.
            scope_keys: Optional scope keys for candidate generation.
            certificate_id: Optional certificate context.

        Returns:
            Tuple of (run_record, status_message).
            Status is one of: "started", "duplicate", "rejected".
        """
        # Guard 1: Check all theatres are registered and active
        inactive_slugs = []
        missing_slugs = []
        for slug in theatre_slugs:
            entry = self._store.get_by_slug(slug)
            if entry is None:
                missing_slugs.append(slug)
            elif not entry.is_active:
                inactive_slugs.append(slug)

        if missing_slugs:
            raise ValueError(
                f"Unregistered theatre(s): {missing_slugs}. "
                "Register with register_theatre() first."
            )
        if inactive_slugs:
            raise ValueError(
                f"Inactive theatre(s): {inactive_slugs}. "
                "Activate with store.activate() first."
            )

        # Guard 2: Idempotence — check for active run with same theatre set
        active_run_id = self._store.has_active_run(theatre_slugs)
        if active_run_id is not None:
            active_run = self._store.get_run(active_run_id)
            logger.info(
                "Duplicate run rejected: active run %s for %s",
                active_run_id, theatre_slugs,
            )
            return (active_run, "duplicate")  # type: ignore[return-value]

        # Guard 3: All slugs must have construct.json content
        missing_json = [s for s in theatre_slugs if s not in construct_json_map]
        if missing_json:
            raise ValueError(
                f"Missing construct.json for theatre(s): {missing_json}"
            )

        # Build inputs and delegate to execute_run
        theatre_inputs = []
        for slug in theatre_slugs:
            entry = self._store.get_by_slug(slug)
            theatre_inputs.append(ExternalTheatreInput(
                construct_slug=slug,
                construct_version=entry.version,  # type: ignore[union-attr]
                construct_json=construct_json_map[slug],
            ))

        run = self.execute_run(
            theatre_inputs=theatre_inputs,
            event_keys=event_keys,
            scope_keys=scope_keys,
            certificate_id=certificate_id,
        )

        status = "started" if run.status == RunStatus.COMPLETED else "failed"
        return (run, status)

    def trigger_all_active(
        self,
        construct_json_map: dict[str, str],
        event_keys: Optional[list[str]] = None,
        scope_keys: Optional[list] = None,
        certificate_id: Optional[str] = None,
    ) -> tuple[Optional[ExternalTheatreRunRecord], str]:
        """Trigger a run for all currently active theatres.

        Convenience method for scheduled jobs that scan the full active set.
        Returns (None, "no_active_theatres") if no active theatres exist.
        """
        active = self._store.list_active()
        if not active:
            return (None, "no_active_theatres")

        slugs = [e.slug for e in active]

        # Filter construct_json_map to only active slugs with available content
        missing = [s for s in slugs if s not in construct_json_map]
        if missing:
            logger.warning(
                "Skipping trigger_all_active: missing construct.json for %s",
                missing,
            )
            return (None, f"missing_construct_json:{','.join(missing)}")

        return self.trigger_run(
            theatre_slugs=slugs,
            construct_json_map=construct_json_map,
            event_keys=event_keys,
            scope_keys=scope_keys,
            certificate_id=certificate_id,
        )

    # -------------------------------------------------------------------
    # Run execution
    # -------------------------------------------------------------------

    def execute_run(
        self,
        theatre_inputs: list[ExternalTheatreInput],
        event_keys: Optional[list[str]] = None,
        scope_keys: Optional[list] = None,
        certificate_id: Optional[str] = None,
    ) -> ExternalTheatreRunRecord:
        """Execute a full preparation + scan run and persist results.

        Steps:
        1. Extract theatre slugs from inputs
        2. Compute spec hashes from construct.json content
        3. Create run record (IN_PROGRESS)
        4. Call 038b orchestrator (prepare_external_theatres)
        5. Call 038c scan adapter (scan_candidates) on resulting candidates
        6. Build result summary and complete/fail the run record
        7. Update registry entries with latest summary timestamps

        Returns the completed (or failed) run record.
        """
        theatre_slugs = [t.construct_slug for t in theatre_inputs]

        # Compute spec hashes for change detection
        spec_hashes = [
            self._store.compute_spec_hash(t.construct_json)
            for t in theatre_inputs
        ]
        combined_spec_hash = self._store.compute_spec_hash(
            "|".join(sorted(spec_hashes))
        )

        # Create run record
        run = self._store.create_run(
            theatre_slugs=theatre_slugs,
            spec_hash=combined_spec_hash,
        )

        try:
            # Step 1: 038b orchestration
            prep_request = ExternalTheatrePreparationRequest(
                theatres=theatre_inputs,
                event_keys=event_keys or [],
                scope_keys=scope_keys or [],
                certificate_id=certificate_id,
            )
            prep_result = prepare_external_theatres(prep_request)

            # Step 2: 038c scan (only if candidates exist)
            scan_result: Optional[ExternalTheatreScanResult] = None
            if prep_result.candidates:
                scan_request = ExternalTheatreScanRequest(
                    candidates=prep_result.candidates,
                    event_keys=event_keys or [],
                    scope_keys=scope_keys or [],
                )
                scan_result = scan_candidates(scan_request)

            # Step 3: Build summary and complete run
            result_counts = self._build_run_summary(prep_result, scan_result)
            feedback_snapshot = self._extract_feedback_snapshot(prep_result)

            prep_summary = {
                "total_theatres": prep_result.total_theatres,
                "total_successful": prep_result.total_successful,
                "total_failed": prep_result.total_failed,
                "candidate_count": len(prep_result.candidates),
            }

            scan_summary = {}
            if scan_result is not None:
                scan_summary = {
                    "total_scanned": scan_result.total_scanned,
                    "total_with_findings": scan_result.total_with_findings,
                    "total_clean": scan_result.total_clean,
                }

            completed_run = self._store.complete_run(
                run_id=run.id,
                preparation_summary=prep_summary,
                scan_summary=scan_summary,
                result_counts=result_counts,
                feedback_snapshot=feedback_snapshot,
            )

            # Step 4: Update registry entries with latest timestamps
            self._update_registry_from_run(theatre_inputs, prep_result, scan_result)

            logger.info(
                "Run %s completed: %d theatres, %d candidates, paradox=%s",
                run.id,
                result_counts.total_theatres,
                result_counts.candidate_count,
                result_counts.has_paradox,
            )

            return completed_run  # type: ignore[return-value]

        except Exception as exc:
            logger.error("Run %s failed: %s", run.id, exc)
            failed_run = self._store.fail_run(
                run.id,
                error_summary={"error": str(exc)},
            )
            return failed_run  # type: ignore[return-value]

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _build_run_summary(
        self,
        prep_result: ExternalTheatrePreparationResult,
        scan_result: Optional[ExternalTheatreScanResult],
    ) -> ExternalTheatreRunSummary:
        """Build aggregated result counts from prep + scan results."""
        has_paradox = False
        total_scanned = 0
        total_with_findings = 0
        total_clean = 0
        candidate_count = len(prep_result.candidates)

        if scan_result is not None:
            total_scanned = scan_result.total_scanned
            total_with_findings = scan_result.total_with_findings
            total_clean = scan_result.total_clean
            has_paradox = scan_result.total_with_findings > 0

        return ExternalTheatreRunSummary(
            total_theatres=prep_result.total_theatres,
            total_successful=prep_result.total_successful,
            total_failed=prep_result.total_failed,
            candidate_count=candidate_count,
            total_scanned=total_scanned,
            total_with_findings=total_with_findings,
            total_clean=total_clean,
            has_paradox=has_paradox,
        )

    def _extract_feedback_snapshot(
        self,
        prep_result: ExternalTheatrePreparationResult,
    ) -> list[dict]:
        """Extract builder feedback items into a persistable snapshot."""
        snapshot: list[dict] = []
        for report in prep_result.feedback:
            items = []
            for item in report.required_items + report.optional_items + report.extraction_items:
                items.append({
                    "category": item.category,
                    "field": item.field,
                    "status": item.status,
                    "message": item.message,
                })
            snapshot.append({
                "construct_slug": report.construct_slug,
                "overall_readiness": report.overall_readiness,
                "items": items,
            })
        return snapshot

    def _update_registry_from_run(
        self,
        theatre_inputs: list[ExternalTheatreInput],
        prep_result: ExternalTheatrePreparationResult,
        scan_result: Optional[ExternalTheatreScanResult],
    ) -> None:
        """Update registry entries with latest run timestamps and summary."""
        from datetime import datetime

        now = datetime.utcnow()

        for theatre_input in theatre_inputs:
            entry = self._store.get_by_slug(theatre_input.construct_slug)
            if entry is None:
                continue

            # Check if this theatre was successfully prepared
            prepared = any(
                t.construct_slug == theatre_input.construct_slug
                and t.bundle is not None
                for t in prep_result.theatres
            )

            prepared_at = now if prepared else None
            scanned_at = now if scan_result is not None and prepared else None

            summary: dict = {
                "prepared": prepared,
                "candidate_count": len(prep_result.candidates),
            }
            if scan_result is not None:
                summary["total_scanned"] = scan_result.total_scanned
                summary["has_paradox"] = scan_result.total_with_findings > 0

            self._store.update_latest_summary(
                entry_id=entry.id,
                summary=summary,
                prepared_at=prepared_at,
                scanned_at=scanned_at,
            )
