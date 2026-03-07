"""Tests for CertificateLifecycleService — cycle-021 sprint-2.

Tests the certificate lifecycle state machine (READY -> ANCHORED -> ISSUED),
batch anchor logic, and WS event emission.
Uses AsyncMock for session and WS manager.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.certificate_lifecycle_service import (
    CERT_STATUS_READY,
    CERT_STATUS_ANCHORED,
    CERT_STATUS_ISSUED,
    transition_to_ready,
    run_batch_anchor,
)


def _make_certificate(
    cert_id=None, investigation_id=None, cert_hash=None,
    status="READY", issued_at=None, ready_at=None,
):
    """Create a mock certificate record."""
    cert = MagicMock()
    cert.id = cert_id or f"cert-{uuid.uuid4().hex[:8]}"
    cert.investigation_id = investigation_id or f"inv-{uuid.uuid4().hex[:8]}"
    cert.certificate_hash = cert_hash or hashlib.sha256(cert.id.encode()).hexdigest()
    cert.certificate_status = status
    cert.issued_at = issued_at
    cert.ready_at = ready_at
    cert.anchored_at = None
    cert.batch_anchor_hash = None
    return cert


def _make_investigation(inv_id=None, status="ACTIVE"):
    """Create a mock investigation."""
    inv = MagicMock()
    inv.id = inv_id or f"inv-{uuid.uuid4().hex[:8]}"
    inv.status = status
    inv.completed_at = None
    return inv


@pytest.mark.asyncio
async def test_transition_to_ready_sets_fields():
    """Sets certificate_status=READY, ready_at, investigation=CERTIFICATE_READY."""
    cert = _make_certificate(status=None)
    cert.certificate_status = None
    inv = _make_investigation()

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await transition_to_ready(mock_session, cert, inv)

    assert result.certificate_status == CERT_STATUS_READY
    assert result.ready_at is not None
    assert inv.status == "CERTIFICATE_READY"
    mock_session.flush.assert_called_once()
    mock_ws.broadcast_global.assert_called_once()


@pytest.mark.asyncio
async def test_transition_to_ready_no_issued_at():
    """ready_at set, issued_at remains None."""
    cert = _make_certificate(status=None)
    cert.certificate_status = None
    cert.issued_at = None
    inv = _make_investigation()

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        result = await transition_to_ready(mock_session, cert, inv)

    assert result.ready_at is not None
    assert result.issued_at is None


@pytest.mark.asyncio
async def test_batch_anchor_transitions_ready_to_issued():
    """READY -> ANCHORED -> ISSUED with correct timestamps."""
    cert = _make_certificate(status=CERT_STATUS_READY)
    inv = _make_investigation()
    batch_ts = datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    # Mock the select query to return our cert
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [cert]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(return_value=inv)

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        issued_ids = await run_batch_anchor(mock_session, batch_timestamp=batch_ts)

    assert len(issued_ids) == 1
    assert cert.certificate_status == CERT_STATUS_ISSUED
    assert cert.anchored_at == batch_ts
    assert cert.issued_at == batch_ts


@pytest.mark.asyncio
async def test_batch_anchor_computes_hash():
    """Batch hash = SHA-256 of sorted cert hashes."""
    cert1 = _make_certificate(cert_hash="bbbb" + "0" * 60)
    cert2 = _make_certificate(cert_hash="aaaa" + "0" * 60)
    batch_ts = datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [cert1, cert2]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(return_value=_make_investigation())

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        await run_batch_anchor(mock_session, batch_timestamp=batch_ts)

    # Hash should be of sorted hashes
    sorted_hashes = sorted([cert1.certificate_hash, cert2.certificate_hash])
    expected_hash = hashlib.sha256(
        json.dumps(sorted_hashes, separators=(",", ":")).encode()
    ).hexdigest()

    assert cert1.batch_anchor_hash == expected_hash
    assert cert2.batch_anchor_hash == expected_hash


@pytest.mark.asyncio
async def test_batch_anchor_idempotent():
    """Second call returns empty list when no READY certs."""
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        issued_ids = await run_batch_anchor(mock_session)

    assert issued_ids == []
    mock_ws.broadcast_global.assert_not_called()


@pytest.mark.asyncio
async def test_batch_anchor_sets_completed():
    """Investigation status = COMPLETED after ISSUED."""
    cert = _make_certificate(status=CERT_STATUS_READY)
    inv = _make_investigation(inv_id=cert.investigation_id)
    batch_ts = datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [cert]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(return_value=inv)

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        await run_batch_anchor(mock_session, batch_timestamp=batch_ts)

    assert inv.status == "COMPLETED"
    assert inv.completed_at == batch_ts


@pytest.mark.asyncio
async def test_batch_anchor_emits_ws_per_cert():
    """One WS event per issued certificate."""
    cert1 = _make_certificate(status=CERT_STATUS_READY)
    cert2 = _make_certificate(status=CERT_STATUS_READY)
    batch_ts = datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc)

    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [cert1, cert2]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(return_value=_make_investigation())

    with patch("backend.services.certificate_lifecycle_service.ws_manager") as mock_ws:
        mock_ws.broadcast_global = AsyncMock()
        await run_batch_anchor(mock_session, batch_timestamp=batch_ts)

    assert mock_ws.broadcast_global.call_count == 2
    # Verify both calls are INVESTIGATION_CERTIFICATE_ISSUED
    for call in mock_ws.broadcast_global.call_args_list:
        assert call[0][0] == "INVESTIGATION_CERTIFICATE_ISSUED"


@pytest.mark.asyncio
async def test_cannot_skip_to_issued():
    """Cannot transition to READY if certificate is already ANCHORED."""
    cert = _make_certificate(status=CERT_STATUS_ANCHORED)
    inv = _make_investigation()

    mock_session = AsyncMock()

    with pytest.raises(ValueError, match="Cannot transition to READY"):
        with patch("backend.services.certificate_lifecycle_service.ws_manager"):
            await transition_to_ready(mock_session, cert, inv)
