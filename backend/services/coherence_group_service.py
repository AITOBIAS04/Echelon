"""CoherenceGroupService — management of theatre coherence groups.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import CoherenceGroup, CoherenceGroupMember

logger = logging.getLogger(__name__)


class CoherenceGroupService:
    """Management of CoherenceGroups and membership."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_group(
        self,
        name: str,
        group_type: str,
        policy_json: dict,
    ) -> CoherenceGroup:
        """Create a coherence group with policy thresholds."""
        group = CoherenceGroup(
            name=name,
            group_type=group_type,
            policy_json=policy_json,
        )
        self._db.add(group)
        await self._db.flush()
        logger.info("Created CoherenceGroup %s: %s", group.id, name)
        return group

    async def add_member(
        self,
        group_id: str,
        theatre_id: str,
        role: str = "primary",
    ) -> CoherenceGroupMember:
        """Add a theatre to a coherence group."""
        member = CoherenceGroupMember(
            coherence_group_id=group_id,
            theatre_id=theatre_id,
            role=role,
        )
        self._db.add(member)
        await self._db.flush()
        logger.info(
            "Added theatre %s to CoherenceGroup %s (role=%s)",
            theatre_id, group_id, role,
        )
        return member

    async def get_groups_for_theatre(
        self,
        theatre_id: str,
    ) -> list[CoherenceGroup]:
        """Get all coherence groups containing a theatre."""
        result = await self._db.execute(
            select(CoherenceGroup)
            .join(
                CoherenceGroupMember,
                CoherenceGroupMember.coherence_group_id == CoherenceGroup.id,
            )
            .where(CoherenceGroupMember.theatre_id == theatre_id)
        )
        return list(result.scalars().all())

    async def get_group_members(
        self,
        group_id: str,
    ) -> list[CoherenceGroupMember]:
        """Get all members of a coherence group."""
        result = await self._db.execute(
            select(CoherenceGroupMember).where(
                CoherenceGroupMember.coherence_group_id == group_id,
            )
        )
        return list(result.scalars().all())
