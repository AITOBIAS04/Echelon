"""Echelon Canonical JSON v0 + SHA-256 hashing utilities.

NOT RFC 8785 (JCS). Echelon Canonical JSON v0 is defined as:
    json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)

Two functions are re-exported from the API contract (canonical_json,
compute_receipt_hash). One function is new (compute_content_hash) and
intentionally differs from the API contract version — it hashes raw bytes,
not re-serialised JSON.
"""
from __future__ import annotations

import hashlib

from backend.schemas.worldmonitor_api_contract import (
    canonical_json as _contract_canonical_json,
    compute_receipt_hash as _contract_compute_receipt_hash,
)

__all__ = [
    "canonical_json",
    "compute_content_hash",
    "compute_receipt_hash",
]


def canonical_json(obj: dict) -> str:
    """Echelon Canonical JSON v0 — sorted keys, compact separators, no ASCII escape.

    NOT RFC 8785 (JCS). Re-exported from worldmonitor_api_contract.py.

    Produces deterministic JSON:
        json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)
    """
    return _contract_canonical_json(obj)


def compute_content_hash(raw_payload: bytes) -> str:
    """SHA-256 of raw response bytes.

    IMPORTANT: Hashes exact bytes, NOT parsed/re-serialised JSON.
    This is intentionally different from the API contract's compute_content_hash()
    which takes a dict and re-serialises via canonical_json(). The Echelon
    pipeline hashes the wire bytes to prevent re-serialisation discrepancies
    from invalidating receipts.

    Args:
        raw_payload: Exact HTTP response body bytes.

    Returns:
        Lowercase hex SHA-256 digest (64 characters).
    """
    return hashlib.sha256(raw_payload).hexdigest()


def compute_receipt_hash(
    method: str,
    url: str,
    query: str,
    headers: str,
    body_hash: str,
) -> str:
    """SHA-256 of canonical HTTP transcript per spec v1.0.

    Re-exported from worldmonitor_api_contract.py.

    Transcript format:
        METHOD\\nURL\\nQUERY\\nHEADERS\\nBODY_HASH

    The method is uppercased. All other fields are used as-is.
    """
    return _contract_compute_receipt_hash(method, url, query, headers, body_hash)
