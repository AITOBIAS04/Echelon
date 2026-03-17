"""
Signal Persistence — Cycle 025
===============================

Shared helper for writing OSINT signals to the osint_signals table.
Used by the three POST endpoints (CII, Market, Maritime).
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import OsintSignal
from backend.osint.models.evidence import CollectionResult


async def persist_signal(
    session: AsyncSession,
    result: CollectionResult,
    source_id: str,
    source_group: str,
    investigation_id: str | None = None,
) -> OsintSignal | None:
    """Persist a collection result as an OsintSignal row.

    Deduplicates on content_hash — if a signal with the same hash
    already exists, returns None (skip).

    Uses the bundle's raw_payload_hash (collector-computed SHA-256)
    for both dedup and provenance, rather than recomputing from a
    reduced dict.
    """
    if not result.bundle:
        return None

    # Use the collector's canonical hash — single source of truth
    content_hash = result.bundle.raw_payload_hash

    # Build normalised data dict from bundle for storage
    event = result.bundle.normalised_event
    normalised = {
        "event_id": event.event_id,
        "measure_type": event.measure.type.value if hasattr(event.measure.type, "value") else str(event.measure.type),
        "measure_value": event.measure.value,
        "measure_unit": event.measure.unit,
        "confidence": event.confidence,
        "geo": {"lat": event.geo.lat, "lon": event.geo.lon},
    }
    if event.measure.metadata:
        normalised["metadata"] = event.measure.metadata

    # Dedup check
    existing = await session.execute(
        select(OsintSignal.id).where(OsintSignal.content_hash == content_hash).limit(1)
    )
    if existing.scalar_one_or_none():
        return None

    signal = OsintSignal(
        id=str(uuid4()),
        source_id=source_id,
        source_group=source_group,
        signal_type=normalised["measure_type"],
        geo_region=_extract_geo_region(event),
        entity_ref=None,
        content_hash=content_hash,
        normalised_data=normalised,
        investigation_id=investigation_id,
        collected_at=result.retrieved_at or datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    session.add(signal)
    return signal


def _extract_geo_region(event) -> str | None:
    """Extract a geo region string from event geo data."""
    if not event.geo:
        return None
    lat, lon = event.geo.lat, event.geo.lon
    if lat == 0.0 and lon == 0.0:
        return None
    # Simple region identifier from coordinates
    return f"{lat:.1f},{lon:.1f}"
