"""Coherence Gate Evaluator — post-routing coherence review system.

Gate lifecycle: (none) → PENDING → PASSED | FAILED

Rules for requiring coherence review:
- routing_hint == REVIEW_REQUIRED → always
- inquiry_class == INVESTIGATIVE and composite_score < 0.8 → yes
- verification_tier == CONTESTED → yes
- Otherwise → no

Creates TheatreAuditEvent records on gate transitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import TheatreCertificate, TheatreAuditEvent
from backend.websockets.realtime_manager import manager as ws_manager


class CoherenceGateEvaluator:
    """Evaluates whether certificates require coherence review and manages gate lifecycle."""

    def should_require_review(
        self,
        routing_hint: Optional[str],
        inquiry_class: Optional[str],
        composite_score: float,
        verification_tier: str,
    ) -> bool:
        """Determine if a certificate requires coherence review."""
        if routing_hint == "REVIEW_REQUIRED":
            return True
        if (inquiry_class or "").upper() == "INVESTIGATIVE" and composite_score < 0.8:
            return True
        if verification_tier == "CONTESTED":
            return True
        return False

    async def open_gate(
        self,
        session: AsyncSession,
        certificate_id: str,
    ) -> TheatreCertificate:
        """Open a coherence gate on a certificate (set to PENDING).

        Creates a COHERENCE_GATE_OPENED audit event.
        """
        cert = await session.get(TheatreCertificate, certificate_id)
        if cert is None:
            raise ValueError(f"Certificate {certificate_id} not found")

        cert.coherence_review_required = True
        cert.coherence_gate_status = "PENDING"

        # Audit event
        audit = TheatreAuditEvent(
            id=str(uuid.uuid4()),
            theatre_id=cert.theatre_id,
            event_type="COHERENCE_GATE_OPENED",
            detail_json={
                "certificate_id": certificate_id,
                "from_status": None,
                "to_status": "PENDING",
            },
        )
        session.add(audit)

        # Broadcast gate transition via WebSocket (fire-and-forget)
        try:
            await ws_manager.broadcast_coherence_gate_transition(certificate_id, {
                "from_status": None,
                "to_status": "PENDING",
            })
        except Exception:
            pass

        return cert

    async def resolve_gate(
        self,
        session: AsyncSession,
        certificate_id: str,
        status: str,
        reviewer_id: str,
    ) -> TheatreCertificate:
        """Resolve a coherence gate (PASSED or FAILED).

        Creates a COHERENCE_GATE_RESOLVED audit event.

        Args:
            session: Database session
            certificate_id: Certificate to resolve
            status: "PASSED" or "FAILED"
            reviewer_id: User ID of the reviewer
        """
        if status not in ("PASSED", "FAILED"):
            raise ValueError(f"Invalid gate status: {status}. Must be PASSED or FAILED.")

        cert = await session.get(TheatreCertificate, certificate_id)
        if cert is None:
            raise ValueError(f"Certificate {certificate_id} not found")

        if cert.coherence_gate_status != "PENDING":
            raise ValueError(
                f"Cannot resolve gate in status '{cert.coherence_gate_status}'. Must be PENDING."
            )

        now = datetime.utcnow()
        from_status = cert.coherence_gate_status
        cert.coherence_gate_status = status
        cert.coherence_reviewed_at = now
        cert.coherence_reviewer_id = reviewer_id

        # Audit event
        audit = TheatreAuditEvent(
            id=str(uuid.uuid4()),
            theatre_id=cert.theatre_id,
            event_type="COHERENCE_GATE_RESOLVED",
            detail_json={
                "certificate_id": certificate_id,
                "from_status": from_status,
                "to_status": status,
                "reviewer_id": reviewer_id,
            },
        )
        session.add(audit)

        # Broadcast gate transition via WebSocket (fire-and-forget)
        try:
            await ws_manager.broadcast_coherence_gate_transition(certificate_id, {
                "from_status": from_status,
                "to_status": status,
                "reviewer_id": reviewer_id,
            })
        except Exception:
            pass

        return cert
