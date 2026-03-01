"""
Evidence models for the Echelon OSINT Pipeline.

Pydantic v2 models matching the Evidence Bundle Schema from
Echelon_OSINT_Reality_Oracle_Appendix_v3_1 §2.3 and the
HTTP Transcript Canonical Specification from
Echelon_OSINT_Composed_Oracle_Spec_v2 §5.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReceiptMode(str, Enum):
    """Receipt mode minimum levels (ordered by strength)."""

    NONE = "none"
    HTTP_TRANSCRIPT = "http_transcript"
    CRYPTOGRAPHIC_TRANSCRIPT = "cryptographic_transcript"
    SIGNED_RECEIPT = "signed_receipt"
    WITNESS_QUORUM = "witness_quorum"


class CollectionStatus(str, Enum):
    """Outcome of a single source collection attempt."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMITED = "rate_limited"
    SOURCE_ERROR = "source_error"
    NETWORK_ERROR = "network_error"
    NOT_FOUND = "not_found"
    STALE = "stale"


class FreshnessState(str, Enum):
    """Data freshness classification (World Monitor alignment)."""

    FRESH = "fresh"
    STALE = "stale"
    NO_DATA = "no_data"
    ERROR = "error"


# Ordered from weakest to strongest for enforcement comparisons.
RECEIPT_MODE_ORDER: list[ReceiptMode] = [
    ReceiptMode.NONE,
    ReceiptMode.HTTP_TRANSCRIPT,
    ReceiptMode.CRYPTOGRAPHIC_TRANSCRIPT,
    ReceiptMode.SIGNED_RECEIPT,
    ReceiptMode.WITNESS_QUORUM,
]


def meets_receipt_minimum(produced: ReceiptMode, minimum: ReceiptMode) -> bool:
    """Return True if *produced* receipt mode meets or exceeds *minimum*."""
    return RECEIPT_MODE_ORDER.index(produced) >= RECEIPT_MODE_ORDER.index(minimum)


class GapKind(str, Enum):
    """Distinguish evidential absence from intelligence failure.

    SIGNAL_ABSENCE means the source responded successfully but returned
    nothing -- this IS evidence (the thing does not exist).
    INTELLIGENCE_GAP means a failure prevented observation -- this is
    uncertainty, not evidence.
    """

    SIGNAL_ABSENCE = "signal_absence"
    INTELLIGENCE_GAP = "intelligence_gap"


class FailureMode(str, Enum):
    """Structured failure classification for gap reports."""

    CONNECTION_REFUSED = "connection_refused"
    DNS_FAILURE = "dns_failure"
    TLS_ERROR = "tls_error"
    READ_TIMEOUT = "read_timeout"
    RESPONSE_TOO_LARGE = "response_too_large"
    HTTP_ERROR_4XX = "http_error_4xx"
    HTTP_ERROR_5XX = "http_error_5xx"


RETRIABLE_FAILURES: frozenset[FailureMode] = frozenset({
    FailureMode.READ_TIMEOUT,
    FailureMode.HTTP_ERROR_5XX,
})


class HTTPTranscriptReceipt(BaseModel):
    """
    Deterministic receipt of an HTTP exchange.

    Two independent fetchers querying the same endpoint with identical
    parameters must produce identical receipt hashes.

    See Composed Oracle Spec v2 §5 for canonical form specification.
    """

    method: str = Field(description="HTTP method (uppercase)")
    url: str = Field(description="Request URL (canonical form)")
    request_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Request headers sent (for canonical form computation)",
    )
    response_status: int = Field(description="HTTP response status code")
    response_body_hash: str = Field(
        description="SHA-256 of raw response body (lowercase hex, 64 chars)"
    )
    timestamp_ms: int = Field(
        description="UTC timestamp of retrieval (milliseconds since epoch)"
    )
    receipt_hash: str = Field(
        description="SHA-256 of the HTTP Transcript Canonical Form"
    )

    @field_validator("response_body_hash", "receipt_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(f"Hash must be 64-char lowercase hex, got: {v[:20]}...")
        return v


class EvidenceBundle(BaseModel):
    """
    A single evidence artefact from the OSINT pipeline.

    Each bundle represents one fetch from one source, with full provenance
    chain from raw payload through to structured extract.

    See OSINT Reality Oracle Appendix v3.1 §2.3.
    """

    bundle_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier (UUID v4). Immutable once created.",
    )
    source_id: str = Field(
        description="Must match a source_id in the OSINT Source Registry"
    )
    source_group: str = Field(
        description="Source independence group (from registry)"
    )
    independence_upstream_id: str = Field(
        description="System-of-record identifier for corroboration dedup"
    )
    resolution_role: str = Field(
        description="primary_evidence | secondary_corroboration | counter_signal | triage_only"
    )
    jurisdiction: str = Field(
        description="ISO 3166-1 alpha-2 or GLOBAL"
    )

    # Raw data
    raw_payload_hash: str = Field(
        description="SHA-256 of the raw response body (content_hash)"
    )
    raw_payload_size_bytes: int = Field(
        description="Size of raw response in bytes"
    )

    # Receipt
    receipt: HTTPTranscriptReceipt = Field(
        description="HTTP Transcript Receipt for this fetch"
    )
    receipt_mode: ReceiptMode = Field(
        default=ReceiptMode.HTTP_TRANSCRIPT,
        description="Receipt mode used for this bundle"
    )

    # Structured extract
    structured_extract: dict[str, Any] = Field(
        default_factory=dict,
        description="Processed output consumed by downstream systems"
    )

    # Scoring
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Pipeline-assessed reliability [0.0, 1.0]"
    )
    freshness: FreshnessState = Field(
        default=FreshnessState.FRESH,
        description="Data freshness classification"
    )

    # Context
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC retrieval timestamp (ms precision)"
    )
    theatre_id: str | None = Field(
        default=None,
        description="Theatre this bundle serves (if theatre-specific)"
    )
    query_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Query parameters, entity identifiers, time windows"
    )

    @field_validator("raw_payload_hash")
    @classmethod
    def validate_content_hash(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(f"content_hash must be 64-char lowercase hex")
        return v


class CollectionResult(BaseModel):
    """
    Result of a collection attempt against a single source.

    Wraps either a successful EvidenceBundle or a failure record
    with diagnostic information.
    """

    source_id: str
    status: CollectionStatus
    bundle: EvidenceBundle | None = None
    error_message: str | None = None
    duration_ms: int = Field(
        default=0, description="Wall-clock time for this collection (ms)"
    )
    attempted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def succeeded(self) -> bool:
        return self.status == CollectionStatus.SUCCESS and self.bundle is not None


class GapReport(BaseModel):
    """
    Explicit record of sources that could not be queried.

    Gaps are credibility signals, not weaknesses. "Show what you
    cannot see" is the principle.
    """

    source_id: str
    source_group: str
    jurisdiction: str
    reason: CollectionStatus
    error_detail: str | None = None
    allow_gap: bool = Field(
        default=False,
        description="Whether this gap is acceptable per theatre config"
    )
    gap_kind: GapKind = Field(
        default=GapKind.INTELLIGENCE_GAP,
        description="Whether this gap represents evidential absence or collection failure",
    )
    freshness: FreshnessState = Field(default=FreshnessState.NO_DATA)
    failure_mode: FailureMode | None = Field(
        default=None, description="Structured failure classification"
    )
    retriable: bool = Field(
        default=False, description="Whether this failure is likely transient"
    )


class OracleCollectionSummary(BaseModel):
    """
    Summary of Stage 1 (Collection) output.

    Passed to Stage 2 (Corroboration) for cross-referencing.
    """

    theatre_id: str | None = None
    query_window_start: datetime | None = None
    query_window_end: datetime | None = None
    bundles: list[EvidenceBundle] = Field(default_factory=list)
    gaps: list[GapReport] = Field(default_factory=list)
    total_sources_attempted: int = 0
    total_sources_succeeded: int = 0
    total_sources_failed: int = 0

    @property
    def gap_count(self) -> int:
        """Number of gap reports in this summary."""
        return len(self.gaps)

    @property
    def gap_sources(self) -> list[str]:
        """Source IDs that produced gap reports."""
        return [g.source_id for g in self.gaps]

    @property
    def coverage_ratio(self) -> float:
        if self.total_sources_attempted == 0:
            return 0.0
        return self.total_sources_succeeded / self.total_sources_attempted

    @property
    def distinct_upstream_count(self) -> int:
        """Count distinct independence_upstream_id values across successful bundles.

        Two sources sharing the same upstream system of record count as one
        independent observation.
        """
        return len({b.independence_upstream_id for b in self.bundles})

    @property
    def distinct_upstream_succeeded_count(self) -> int:
        """Alias for distinct_upstream_count — clarifies that only succeeded bundles count."""
        return self.distinct_upstream_count

    @property
    def upstream_dedup_map(self) -> dict[str, list[str]]:
        """Map each independence_upstream_id to the source_ids that share it."""
        mapping: dict[str, list[str]] = {}
        for bundle in self.bundles:
            mapping.setdefault(bundle.independence_upstream_id, []).append(
                bundle.source_id
            )
        return mapping
