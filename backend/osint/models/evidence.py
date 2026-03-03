"""Evidence models — CollectionResult dataclass + re-exports from API contract.

The API contract (worldmonitor_api_contract.py) is the single source of truth
for bundle shapes. This module re-exports those types and adds CollectionResult
for pipeline-internal use.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Re-exported from API contract — single source of truth.
# Consumers import these from here, not from the contract directly.
from backend.schemas.worldmonitor_api_contract import (
    EvidenceBundle,
    GeoPoint,
    HealthStatus,
    HTTPTranscriptReceipt,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
    WMDomain,
)

__all__ = [
    "EvidenceBundle",
    "GeoPoint",
    "HealthStatus",
    "HTTPTranscriptReceipt",
    "MeasureType",
    "NormalisedEvent",
    "NormalisedMeasure",
    "WMDomain",
    "CollectionResult",
]


@dataclass
class CollectionResult:
    """Output of a single collector fetch.

    Wraps the Pydantic EvidenceBundle in a stdlib dataclass for
    pipeline-internal use. The raw_payload field is bytes (not dict)
    so the content hash can be verified against exact wire bytes.
    """

    source_id: str                              # Registry source_id
    bundle: EvidenceBundle | None               # None on failure
    raw_payload: bytes                          # Exact response bytes (for hash verification)
    fetch_duration_ms: float                    # Wall-clock fetch time in ms
    success: bool                               # True if valid bundle produced
    error: str | None = None                    # Error description on failure
    retrieved_at: datetime | None = None        # UTC timestamp of fetch
