"""FactAnchorService — real-world event registry with theatre linking.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import FactAnchor, FactAnchorLink

logger = logging.getLogger(__name__)


class FactAnchorService:
    """CRUD and linking for FactAnchors — real-world event registry."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def get_or_create(
        self,
        anchor_type: str,
        external_id: str,
        external_source: str,
        occurred_at: datetime,
        location_json: Optional[dict] = None,
        metadata_json: Optional[dict] = None,
    ) -> FactAnchor:
        """Upsert a FactAnchor by (external_source, external_id).

        Idempotent: returns existing anchor if already registered.
        """
        result = await self._db.execute(
            select(FactAnchor).where(
                FactAnchor.external_source == external_source,
                FactAnchor.external_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.debug(
                "FactAnchor already exists: %s/%s → %s",
                external_source, external_id, existing.id,
            )
            return existing

        anchor = FactAnchor(
            anchor_type=anchor_type,
            external_id=external_id,
            external_source=external_source,
            occurred_at=occurred_at,
            location_json=location_json,
            metadata_json=metadata_json,
        )
        self._db.add(anchor)
        await self._db.flush()
        logger.info(
            "Created FactAnchor %s: %s/%s",
            anchor.id, external_source, external_id,
        )
        return anchor

    async def link_theatre(
        self,
        anchor_id: str,
        theatre_id: str,
        link_type: str,
        linked_entity_id: str,
        linked_entity_type: str,
        link_confidence: float = 1.0,
    ) -> tuple[FactAnchorLink, bool]:
        """Link a theatre to a FactAnchor.

        Returns (link, should_scan) where should_scan is True when >= 2
        distinct theatres are now linked to this anchor.
        """
        link = FactAnchorLink(
            fact_anchor_id=anchor_id,
            theatre_id=theatre_id,
            link_type=link_type,
            linked_entity_id=linked_entity_id,
            linked_entity_type=linked_entity_type,
            link_confidence=link_confidence,
        )
        self._db.add(link)
        await self._db.flush()

        # Count distinct theatres linked to this anchor
        result = await self._db.execute(
            select(func.count(func.distinct(FactAnchorLink.theatre_id))).where(
                FactAnchorLink.fact_anchor_id == anchor_id,
            )
        )
        distinct_count = result.scalar_one()
        should_scan = distinct_count >= 2

        if should_scan:
            logger.info(
                "FactAnchor %s now has %d linked theatres — cross-theatre scan triggered",
                anchor_id, distinct_count,
            )

        return link, should_scan

    async def get_theatres_for_anchor(
        self,
        anchor_id: str,
    ) -> list[FactAnchorLink]:
        """Get all theatre links for a FactAnchor."""
        result = await self._db.execute(
            select(FactAnchorLink).where(
                FactAnchorLink.fact_anchor_id == anchor_id,
            )
        )
        return list(result.scalars().all())

    async def get_anchors_for_theatre(
        self,
        theatre_id: str,
        anchor_type: Optional[str] = None,
    ) -> list[FactAnchorLink]:
        """Get all FactAnchorLinks for a theatre, optionally filtered by anchor_type."""
        query = (
            select(FactAnchorLink)
            .join(FactAnchor, FactAnchorLink.fact_anchor_id == FactAnchor.id)
            .where(FactAnchorLink.theatre_id == theatre_id)
        )
        if anchor_type is not None:
            query = query.where(FactAnchor.anchor_type == anchor_type)
        result = await self._db.execute(query)
        return list(result.scalars().all())
