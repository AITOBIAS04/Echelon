"""Evidence Envelope — append-only evidence container with Merkle-based integrity."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from pydantic import BaseModel

from backend.investigation.models import EvidenceItem, ProvenanceClass


class RedactionEvent(BaseModel):
    """Immutable record of an evidence redaction."""

    model_config = {"frozen": True}

    redaction_id: str
    evidence_id: str
    reason_class: str  # accidental_secret | defamatory | illegal | doxxing | copyright
    redacted_at: datetime


class EvidenceEnvelope:
    """Append-only evidence container with Merkle-based integrity.

    Immutability contract:
    - submit() is append-only. No delete() method exists.
    - redact() adds a redaction event but does NOT remove the hash from the chain.
    - compute_envelope_hash() includes all items including redacted ones.
    """

    def __init__(self) -> None:
        self._items: list[EvidenceItem] = []
        self._redactions: list[RedactionEvent] = []
        self._counter: int = 0
        self._redaction_counter: int = 0

    def submit(
        self,
        content: bytes,
        provenance_class: ProvenanceClass,
        content_type: str,
        source_description: str,
        references: list[str] | None = None,
        source_id: str = "",
        query_determinism: str = "",
    ) -> EvidenceItem:
        """Append an evidence item. Sequential ID, SHA-256 content hash."""
        self._counter += 1
        evidence_id = f"E{self._counter:03d}"
        content_hash = hashlib.sha256(content).hexdigest()

        item = EvidenceItem(
            evidence_id=evidence_id,
            content_hash=content_hash,
            provenance_class=provenance_class,
            submitted_at=datetime.now(timezone.utc),
            content_type=content_type,
            source_description=source_description,
            references=references or [],
            source_id=source_id,
            query_determinism=query_determinism,
        )
        self._items.append(item)
        return item

    def redact(self, evidence_id: str, reason_class: str) -> RedactionEvent:
        """Log a redaction event. Does NOT alter the envelope hash."""
        item = self.get_item(evidence_id)
        if item is None:
            raise ValueError(f"Evidence item {evidence_id} not found")

        self._redaction_counter += 1
        redaction_id = f"R{self._redaction_counter:03d}"

        event = RedactionEvent(
            redaction_id=redaction_id,
            evidence_id=evidence_id,
            reason_class=reason_class,
            redacted_at=datetime.now(timezone.utc),
        )
        self._redactions.append(event)
        return event

    def get_item(self, evidence_id: str) -> EvidenceItem | None:
        """Retrieve an evidence item by ID."""
        for item in self._items:
            if item.evidence_id == evidence_id:
                return item
        return None

    def get_manifest(self) -> dict:
        """Return the evidence manifest as a JSON-serialisable dict."""
        return {
            "item_count": len(self._items),
            "redaction_count": len(self._redactions),
            "envelope_hash": self.compute_envelope_hash(),
            "provenance_summary": self.provenance_summary,
            "items": [
                {
                    "evidence_id": item.evidence_id,
                    "content_hash": item.content_hash,
                    "provenance_class": item.provenance_class.value,
                    "content_type": item.content_type,
                    "source_description": item.source_description,
                    "submitted_at": item.submitted_at.isoformat(),
                    "redacted": any(
                        r.evidence_id == item.evidence_id for r in self._redactions
                    ),
                }
                for item in self._items
            ],
            "redactions": [
                {
                    "redaction_id": r.redaction_id,
                    "evidence_id": r.evidence_id,
                    "reason_class": r.reason_class,
                    "redacted_at": r.redacted_at.isoformat(),
                }
                for r in self._redactions
            ],
        }

    def compute_envelope_hash(self) -> str:
        """SHA-256 of pipe-separated content_hashes in submission order.

        Includes all items including redacted ones (immutability guarantee).
        """
        if not self._items:
            return hashlib.sha256(b"").hexdigest()
        payload = "|".join(item.content_hash for item in self._items)
        return hashlib.sha256(payload.encode()).hexdigest()

    def add_item_from_persisted(
        self,
        evidence_id: str,
        content_hash: str,
        provenance_class: ProvenanceClass,
        submitted_at: datetime,
        content_type: str,
        source_description: str,
        references: list[str] | None = None,
        source_id: str = "",
        query_determinism: str = "",
    ) -> EvidenceItem:
        """Replay a persisted evidence item into the envelope.

        Unlike submit(), this accepts pre-existing IDs and timestamps
        rather than generating new ones. Used for toolset rebuild from DB.
        """
        item = EvidenceItem(
            evidence_id=evidence_id,
            content_hash=content_hash,
            provenance_class=provenance_class,
            submitted_at=submitted_at,
            content_type=content_type,
            source_description=source_description,
            references=references or [],
            source_id=source_id,
            query_determinism=query_determinism,
        )
        self._items.append(item)
        # Keep counter in sync so any subsequent submit() continues correctly
        try:
            num = int(evidence_id.lstrip("E")) if evidence_id.startswith("E") and evidence_id[1:].isdigit() else None
        except (ValueError, IndexError):
            num = None
        if num is not None and num > self._counter:
            self._counter = num
        else:
            self._counter += 1
        return item

    @property
    def items(self) -> list[EvidenceItem]:
        return list(self._items)

    @property
    def redactions(self) -> list[RedactionEvent]:
        return list(self._redactions)

    @property
    def provenance_summary(self) -> dict[str, int]:
        """Count of items per provenance class."""
        summary: dict[str, int] = {}
        for item in self._items:
            key = item.provenance_class.value
            summary[key] = summary.get(key, 0) + 1
        return summary
