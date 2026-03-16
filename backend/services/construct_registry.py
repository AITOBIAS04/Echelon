"""Construct Registry — manages construct identity and lifecycle.

The only service that touches the construct_registrations table.
Handles registration, lookup, and status transitions.
"""

import hashlib
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ConstructRegistration

logger = logging.getLogger(__name__)

# Valid status transitions
_VALID_TRANSITIONS = {
    "REGISTERED": {"IN_PROGRESS"},
    "IN_PROGRESS": {"CERTIFIED", "FAILED"},
    "CERTIFIED": set(),
    "FAILED": {"REGISTERED"},  # Allow re-registration after failure
}


class ConstructRegistry:
    """Manages construct identity and lifecycle."""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def register(
        self,
        slug: str,
        version: str,
        content_hash: str,
        skill_manifest: list[dict],
        domain_claims: list[str],
        test_prompts_hash: str,
        rubric_hash: str,
    ) -> ConstructRegistration:
        """Register a construct for verification.

        Validates:
        - content_hash format (sha256: prefix)
        - skill_manifest non-empty, all entries have command + domain
        - (slug, version) not already registered

        Returns the persisted ConstructRegistration.
        """
        # Validate content_hash format
        if not content_hash.startswith("sha256:"):
            raise ValueError(f"content_hash must start with 'sha256:' prefix, got: {content_hash[:20]}")

        # Validate skill_manifest
        if not skill_manifest:
            raise ValueError("skill_manifest must be non-empty")

        for i, entry in enumerate(skill_manifest):
            if "command" not in entry:
                raise ValueError(f"skill_manifest[{i}] missing 'command' key")
            if "domain" not in entry:
                raise ValueError(f"skill_manifest[{i}] missing 'domain' key")

        # Check for duplicate (slug, version) before inserting
        existing = await self.get(slug, version)
        if existing is not None:
            raise ValueError(
                f"Construct {slug}:{version} is already registered "
                f"(status={existing.status}, id={existing.id})"
            )

        # Compute commitment_hash = sha256(content_hash + test_prompts_hash + rubric_hash)
        commitment_input = content_hash + test_prompts_hash + rubric_hash
        commitment_hash = f"sha256:{hashlib.sha256(commitment_input.encode()).hexdigest()}"

        registration = ConstructRegistration(
            id=str(uuid4()),
            slug=slug,
            version=version,
            content_hash=content_hash,
            skill_manifest=skill_manifest,
            skill_count=len(skill_manifest),
            domain_claims=domain_claims,
            test_prompts_hash=test_prompts_hash,
            rubric_hash=rubric_hash,
            commitment_hash=commitment_hash,
            status="REGISTERED",
        )

        self._db.add(registration)
        await self._db.flush()
        logger.info("Registered construct %s:%s (commitment=%s)", slug, version, commitment_hash[:24])
        return registration

    async def get(self, slug: str, version: str) -> Optional[ConstructRegistration]:
        """Lookup registration by composite key (slug, version)."""
        result = await self._db.execute(
            select(ConstructRegistration).where(
                ConstructRegistration.slug == slug,
                ConstructRegistration.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, registration_id: str) -> Optional[ConstructRegistration]:
        """Lookup registration by UUID."""
        return await self._db.get(ConstructRegistration, registration_id)

    async def update_status(self, registration_id: str, new_status: str) -> None:
        """Update registration status with enforced transitions.

        Valid transitions:
        - REGISTERED → IN_PROGRESS
        - IN_PROGRESS → CERTIFIED | FAILED
        - FAILED → REGISTERED (re-registration)
        """
        reg = await self._db.get(ConstructRegistration, registration_id)
        if reg is None:
            raise ValueError(f"Registration {registration_id} not found")

        allowed = _VALID_TRANSITIONS.get(reg.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition: {reg.status} → {new_status}. "
                f"Allowed: {allowed or 'none (terminal state)'}"
            )

        reg.status = new_status
        await self._db.flush()
        logger.info("Updated construct %s:%s status to %s", reg.slug, reg.version, new_status)

    async def list_registered(self) -> list[ConstructRegistration]:
        """List all registrations, ordered by created_at desc."""
        result = await self._db.execute(
            select(ConstructRegistration).order_by(ConstructRegistration.created_at.desc())
        )
        return list(result.scalars().all())
