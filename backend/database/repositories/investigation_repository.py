"""
Investigation Repository (Cycle 019).

Provides DB persistence for investigation lifecycle, bridging
the in-memory InvestigationToolset with SQLAlchemy models.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
)


def _generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class InvestigationRepository:
    """Repository for investigation persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        theatre_id: str,
        construct_id: str,
        inquiry_class: str = "INVESTIGATIVE",
        domain_filters: Optional[list] = None,
        stop_condition: str = "OUTCOME_RESOLUTION",
        stop_config: Optional[dict] = None,
        created_by: Optional[str] = None,
    ) -> Investigation:
        """Create a new investigation record."""
        investigation = Investigation(
            id=_generate_id("INV-"),
            theatre_id=theatre_id,
            construct_id=construct_id,
            inquiry_class=inquiry_class,
            status="ACTIVE",
            domain_filters_json=domain_filters or [],
            stop_condition=stop_condition,
            stop_config_json=stop_config or {},
            created_by=created_by,
        )
        self.session.add(investigation)
        await self.session.flush()
        return investigation

    async def get(self, investigation_id: str) -> Optional[Investigation]:
        """Get investigation with all sub-entities eagerly loaded."""
        result = await self.session.execute(
            select(Investigation)
            .where(Investigation.id == investigation_id)
            .options(
                selectinload(Investigation.evidence_items),
                selectinload(Investigation.claim_nodes),
                selectinload(Investigation.counter_signals),
                selectinload(Investigation.drift_events),
                selectinload(Investigation.certificate),
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Investigation]:
        """List all investigations with counts."""
        result = await self.session.execute(
            select(Investigation).order_by(Investigation.created_at.desc())
        )
        return list(result.scalars().all())

    async def submit_evidence(
        self,
        investigation_id: str,
        content: bytes,
        provenance_class: str,
        content_type: str = "text/plain",
        source_description: str = "",
        source_id: str = "",
        query_determinism: str = "",
        references: Optional[list] = None,
    ) -> InvestigationEvidenceItem:
        """Persist an evidence item."""
        content_hash = hashlib.sha256(content).hexdigest()

        item = InvestigationEvidenceItem(
            id=_generate_id("EV-"),
            investigation_id=investigation_id,
            content_hash=content_hash,
            provenance_class=provenance_class,
            content_type=content_type,
            source_description=source_description,
            source_id=source_id,
            query_determinism=query_determinism,
            references_json=references or [],
        )
        self.session.add(item)

        # Update investigation timestamp
        inv = await self._get_investigation(investigation_id)
        if inv:
            inv.updated_at = datetime.utcnow()

        await self.session.flush()
        return item

    async def register_claim(
        self,
        investigation_id: str,
        claim_text: str,
        claim_type: str = "fact",
        evidence_refs: Optional[list] = None,
        confidence: float = 0.0,
    ) -> InvestigationClaimNode:
        """Persist a claim node."""
        node = InvestigationClaimNode(
            id=_generate_id("CLM-"),
            investigation_id=investigation_id,
            claim_text=claim_text,
            claim_type=claim_type,
            evidence_refs_json=evidence_refs or [],
            confidence=confidence,
        )
        self.session.add(node)

        inv = await self._get_investigation(investigation_id)
        if inv:
            inv.updated_at = datetime.utcnow()

        await self.session.flush()
        return node

    async def log_counter_signal(
        self,
        investigation_id: str,
        signal_class: str,
        material: bool = False,
        resolution_impact: str = "",
        detection_method: str = "human_submitted",
        evidence_ref: Optional[str] = None,
    ) -> InvestigationCounterSignal:
        """Persist a counter-signal."""
        signal = InvestigationCounterSignal(
            id=_generate_id("CS-"),
            investigation_id=investigation_id,
            signal_class=signal_class,
            material=material,
            resolution_impact=resolution_impact,
            detection_method=detection_method,
            evidence_ref=evidence_ref,
        )
        self.session.add(signal)

        inv = await self._get_investigation(investigation_id)
        if inv:
            inv.updated_at = datetime.utcnow()

        await self.session.flush()
        return signal

    async def log_drift(
        self,
        investigation_id: str,
        drift_type: str,
        original_value: str = "",
        new_value: str = "",
        impact_assessment: str = "non_material",
        evidence_ref: Optional[str] = None,
    ) -> InvestigationDriftEvent:
        """Persist a drift event."""
        event = InvestigationDriftEvent(
            id=_generate_id("DR-"),
            investigation_id=investigation_id,
            drift_type=drift_type,
            original_value=original_value,
            new_value=new_value,
            impact_assessment=impact_assessment,
            evidence_ref=evidence_ref,
        )
        self.session.add(event)

        inv = await self._get_investigation(investigation_id)
        if inv:
            inv.updated_at = datetime.utcnow()

        await self.session.flush()
        return event

    async def persist_certificate(
        self,
        investigation_id: str,
        certificate_hash: str,
        certificate_json: dict,
        routing_decision: str,
        routing_reason: str = "",
    ) -> InvestigationCertificateRecord:
        """Persist investigation certificate (1:1 with investigation)."""
        record = InvestigationCertificateRecord(
            investigation_id=investigation_id,
            certificate_hash=certificate_hash,
            certificate_json=certificate_json,
            routing_decision=routing_decision,
            routing_reason=routing_reason,
        )
        self.session.add(record)

        # Mark investigation as completed
        inv = await self._get_investigation(investigation_id)
        if inv:
            inv.status = "COMPLETED"
            inv.completed_at = datetime.utcnow()
            inv.updated_at = datetime.utcnow()

        await self.session.flush()
        return record

    async def _get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        result = await self.session.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        return result.scalar_one_or_none()
