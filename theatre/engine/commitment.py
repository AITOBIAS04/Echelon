"""Commitment Protocol — generates and verifies commitment hashes.

The commitment hash is SHA-256 over canonical JSON of a composite object
with exactly three keys: dataset_hashes, template, version_pins.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel

from theatre.engine.canonical_json import canonical_json


class CommitmentReceipt(BaseModel):
    """Immutable record of what was committed."""

    theatre_id: str
    commitment_hash: str
    committed_at: datetime
    template_snapshot: dict
    version_pins: dict
    dataset_hashes: dict


class CommitmentProtocol:
    """Generates and verifies commitment hashes."""

    @staticmethod
    def compute_hash(
        template: dict,
        version_pins: dict,
        dataset_hashes: dict,
    ) -> str:
        """Compute SHA-256 over canonical JSON of the composite object.

        The composite object has exactly three keys: dataset_hashes, template,
        version_pins — sorted lexicographically by canonical_json().
        """
        composite = {
            "dataset_hashes": dataset_hashes,
            "template": template,
            "version_pins": version_pins,
        }
        canonical = canonical_json(composite)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_hash(
        commitment_hash: str,
        template: dict,
        version_pins: dict,
        dataset_hashes: dict,
    ) -> bool:
        """Recompute and compare. Returns True if match."""
        recomputed = CommitmentProtocol.compute_hash(
            template, version_pins, dataset_hashes
        )
        return recomputed == commitment_hash

    @staticmethod
    def create_receipt(
        theatre_id: str,
        template: dict,
        version_pins: dict,
        dataset_hashes: dict,
    ) -> CommitmentReceipt:
        """Generate commitment hash and produce a receipt."""
        commitment_hash = CommitmentProtocol.compute_hash(
            template, version_pins, dataset_hashes
        )
        return CommitmentReceipt(
            theatre_id=theatre_id,
            commitment_hash=commitment_hash,
            committed_at=datetime.utcnow(),
            template_snapshot=template,
            version_pins=version_pins,
            dataset_hashes=dataset_hashes,
        )
