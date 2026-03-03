"""BaseCollector ABC — abstract collector with hash invariant enforcement.

Subclasses implement _fetch(). The base class wraps it with
integrity verification before returning results.

Two hash invariants are enforced on every successful collection:
  1. receipt.content_hash == SHA-256(raw_payload)
  2. receipt.receipt_hash verified against canonical HTTP transcript
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.osint.canonical import compute_content_hash, compute_receipt_hash
from backend.osint.models.evidence import CollectionResult, HealthStatus


class HashInvariantViolation(Exception):
    """Raised internally when a collector's evidence bundle fails hash verification.

    This exception is caught by the base class and converted to a
    CollectionResult with success=False. It never propagates to callers.
    """


class BaseCollector(ABC):
    """Abstract collector defining the fetch-to-receipt contract.

    Subclasses implement _fetch() with domain-specific HTTP logic.
    The base class calls _fetch() and then verifies hash integrity.
    If invariants fail, the result is converted to success=False
    with a descriptive error. The collector never raises.
    """

    @abstractmethod
    def source_id(self) -> str:
        """Registry source_id this collector is authoritative for."""
        ...

    @abstractmethod
    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """Internal fetch — subclass implements HTTP call + bundle construction.

        Must NOT raise — returns CollectionResult with success=False on failure.
        """
        ...

    async def fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """Public fetch with hash invariant enforcement.

        Calls _fetch() (subclass implementation) then verifies:
          Invariant 1: receipt.content_hash == SHA-256(raw_payload)
          Invariant 2: receipt.receipt_hash matches canonical transcript (if present)

        On invariant failure, converts result to success=False with error.
        """
        result = await self._fetch(request, theatre_id)
        if result.success and result.bundle is not None:
            self._enforce_hash_invariants(result)
        return result

    def _enforce_hash_invariants(self, result: CollectionResult) -> None:
        """Verify hash invariants on successful collection results.

        Modifies result in-place on failure: sets success=False and error.
        """
        bundle = result.bundle
        receipt = bundle.receipt

        # Invariant 1: content_hash == SHA-256(raw_payload)
        expected_content_hash = compute_content_hash(result.raw_payload)
        if receipt.content_hash != expected_content_hash:
            result.success = False
            result.error = (
                f"Content hash mismatch: receipt={receipt.content_hash}, "
                f"computed={expected_content_hash}"
            )
            return

        # Invariant 2: receipt_hash verification (if present)
        if receipt.receipt_hash is not None:
            params = receipt.request_parameters
            expected_receipt_hash = compute_receipt_hash(
                method=params.get("method", "POST"),
                url=params.get("url", ""),
                query=params.get("query", ""),
                headers=params.get("headers", ""),
                body_hash=receipt.content_hash,
            )
            if receipt.receipt_hash != expected_receipt_hash:
                result.success = False
                result.error = (
                    f"Receipt hash mismatch: receipt={receipt.receipt_hash}, "
                    f"computed={expected_receipt_hash}"
                )

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Returns HEALTHY, DEGRADED, or UNAVAILABLE."""
        ...
