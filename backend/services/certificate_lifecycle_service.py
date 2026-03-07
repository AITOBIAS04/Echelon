"""Certificate Lifecycle Service — cycle-021 sprint-2.

State machine: READY -> ANCHORED -> ISSUED
Batch anchor processes all READY certificates atomically.
"""

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Investigation, InvestigationCertificateRecord
from backend.websockets.realtime_manager import manager as ws_manager

# Certificate Status Constants
CERT_STATUS_READY = "READY"
CERT_STATUS_ANCHORED = "ANCHORED"
CERT_STATUS_ISSUED = "ISSUED"

# Valid Transitions
_VALID_TRANSITIONS = {
    CERT_STATUS_READY: CERT_STATUS_ANCHORED,
    CERT_STATUS_ANCHORED: CERT_STATUS_ISSUED,
}


async def transition_to_ready(
    session: AsyncSession,
    certificate: InvestigationCertificateRecord,
    investigation: Investigation,
) -> InvestigationCertificateRecord:
    """Transition certificate to READY state.

    Called after certificate is built. Sets ready_at, does NOT set issued_at.
    Investigation status becomes CERTIFICATE_READY.

    Raises ValueError if certificate already has a status beyond READY.
    """
    if certificate.certificate_status and certificate.certificate_status != CERT_STATUS_READY:
        raise ValueError(
            f"Cannot transition to READY: certificate is already "
            f"'{certificate.certificate_status}'"
        )

    certificate.certificate_status = CERT_STATUS_READY
    certificate.ready_at = datetime.now(timezone.utc)

    investigation.status = "CERTIFICATE_READY"
    await session.flush()

    await ws_manager.broadcast_global(
        "INVESTIGATION_CERTIFICATE_READY",
        {
            "investigation_id": investigation.id,
            "certificate_id": certificate.id,
            "ready_at": certificate.ready_at.isoformat(),
        },
    )

    return certificate


async def run_batch_anchor(
    session: AsyncSession,
    batch_timestamp: datetime | None = None,
) -> list[str]:
    """Process READY certificates that reached the current batch boundary.

    1. Query all certificates with certificate_status = 'READY'
    2. Compute batch anchor hash (SHA-256 of sorted certificate hashes)
    3. Transition each to ANCHORED with batch_anchor_hash
    4. Transition each to ISSUED with issued_at = batch_timestamp
    5. Mark investigations as COMPLETED
    6. Emit WS events

    Returns list of issued certificate IDs.
    Idempotent: if no READY certificates exist, returns empty list.
    """
    if batch_timestamp is None:
        now = datetime.now(timezone.utc)
        batch_timestamp = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Query READY certificates
    result = await session.execute(
        select(InvestigationCertificateRecord)
        .where(InvestigationCertificateRecord.certificate_status == CERT_STATUS_READY)
    )
    ready_certs = [
        cert
        for cert in result.scalars().all()
        if not isinstance(getattr(cert, "ready_at", None), datetime)
        or cert.ready_at <= batch_timestamp
    ]

    if not ready_certs:
        return []

    # 2. Compute batch anchor hash
    sorted_hashes = sorted(cert.certificate_hash for cert in ready_certs)
    batch_hash_input = json.dumps(sorted_hashes, separators=(",", ":"))
    batch_anchor_hash = hashlib.sha256(batch_hash_input.encode()).hexdigest()

    issued_ids: list[str] = []

    for cert in ready_certs:
        # 3. READY -> ANCHORED
        cert.certificate_status = CERT_STATUS_ANCHORED
        cert.anchored_at = batch_timestamp
        cert.batch_anchor_hash = batch_anchor_hash

        # 4. ANCHORED -> ISSUED
        cert.certificate_status = CERT_STATUS_ISSUED
        cert.issued_at = batch_timestamp

        # 5. Mark investigation COMPLETED
        investigation = await session.get(Investigation, cert.investigation_id)
        if investigation:
            investigation.status = "COMPLETED"
            investigation.completed_at = batch_timestamp

        issued_ids.append(cert.id)

    await session.flush()

    # 6. Emit WS events (after flush to ensure persistence)
    for cert in ready_certs:
        await ws_manager.broadcast_global(
            "INVESTIGATION_CERTIFICATE_ISSUED",
            {
                "investigation_id": cert.investigation_id,
                "certificate_id": cert.id,
                "issued_at": batch_timestamp.isoformat(),
                "batch_anchor_hash": batch_anchor_hash,
            },
        )

    return issued_ids
