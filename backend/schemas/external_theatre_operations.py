"""Operational schemas for external theatre registry and run records.

Cycle 039: External Theatre Operations.

Defines the persistence shapes for:
- ExternalTheatreRegistryEntry: a registered external theatre
- ExternalTheatreRunRecord: a single orchestration + scan cycle
- ExternalTheatreRunSummary: aggregated result counts
- ExternalTheatreStatusReport: builder-facing latest-status view

These are Pydantic models backed by an in-memory store (V1).
Progressive tier: V2 can swap to SQLAlchemy/PostgreSQL without
changing the schema contracts.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RegistryStatus(str, Enum):
    """Lifecycle status for a registered external theatre."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class RunStatus(str, Enum):
    """Lifecycle status for an operational run."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Registry Entry
# ---------------------------------------------------------------------------

class ExternalTheatreRegistryEntry(BaseModel):
    """A registered external theatre in the operations network."""

    id: str
    slug: str
    version: str
    construct_class: str = "theatre"
    repo_path: str = ""
    construct_json_path: str = ""
    status: RegistryStatus = RegistryStatus.ACTIVE
    is_active: bool = True

    # Operational timestamps (set by the operations service)
    last_prepared_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None

    # Latest run summary (JSON-serializable dict)
    latest_summary: dict = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Run Summary (embedded in run records)
# ---------------------------------------------------------------------------

class ExternalTheatreRunSummary(BaseModel):
    """Aggregated result counts for a single operational run."""

    total_theatres: int = 0
    total_successful: int = 0
    total_failed: int = 0
    candidate_count: int = 0
    total_scanned: int = 0
    total_with_findings: int = 0
    total_clean: int = 0
    has_paradox: bool = False


# ---------------------------------------------------------------------------
# Run Record
# ---------------------------------------------------------------------------

class ExternalTheatreRunRecord(BaseModel):
    """An operational run record: one orchestration + scan cycle."""

    id: str
    theatre_slugs: list[str] = Field(default_factory=list)

    # Execution lifecycle
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: RunStatus = RunStatus.IN_PROGRESS

    # Content hashes for change detection
    spec_hash: Optional[str] = None
    contract_hash: Optional[str] = None

    # Persisted result summaries (JSON-serializable)
    preparation_summary: dict = Field(default_factory=dict)
    scan_summary: dict = Field(default_factory=dict)
    result_counts: ExternalTheatreRunSummary = Field(
        default_factory=ExternalTheatreRunSummary,
    )

    # Builder feedback snapshot from 038b
    feedback_snapshot: list[dict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Status Report (builder-facing view)
# ---------------------------------------------------------------------------

class ExternalTheatreStatusReport(BaseModel):
    """Builder-facing status report for a registered external theatre."""

    slug: str
    version: str
    status: RegistryStatus
    is_active: bool

    # Latest operational state
    last_prepared_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    latest_run_status: Optional[RunStatus] = None
    latest_result_counts: Optional[ExternalTheatreRunSummary] = None

    # Builder feedback (persisted 038b feedback items)
    readiness: Optional[str] = None  # "READY" | "DEGRADED" | "BLOCKED"
    feedback_items: list[dict] = Field(default_factory=list)

    # Recent run history (last N runs)
    recent_runs: list[ExternalTheatreRunRecord] = Field(default_factory=list)
