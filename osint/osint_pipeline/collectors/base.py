"""
Base collector abstract class for Echelon OSINT Pipeline.

Every source collector implements this contract:
1. Accept a query context (entity ID, time window, etc.)
2. Fetch from the source API
3. Produce an EvidenceBundle with a valid HTTPTranscriptReceipt
4. Handle errors gracefully and return CollectionResult

The contract enforces deterministic receipt generation: identical
queries must produce identical receipt hashes regardless of which
collector instance runs them.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import httpx

from osint_pipeline.engine.canonical import http_transcript_hash, sha256_hex
from osint_pipeline.models.evidence import (
    CollectionResult,
    CollectionStatus,
    EvidenceBundle,
    FailureMode,
    FreshnessState,
    GapKind,
    GapReport,
    HTTPTranscriptReceipt,
    ReceiptMode,
    RETRIABLE_FAILURES,
    meets_receipt_minimum,
)
from osint_pipeline.models.registry import RegistrySource


class BaseCollector(ABC):
    """
    Abstract base class for OSINT source collectors.

    Subclasses must implement:
    - source_id: str property matching the registry
    - source_group: str property matching the registry
    - independence_upstream_id: str property
    - resolution_role: str property
    - jurisdiction: str property
    - build_request(): construct the HTTP request
    - extract(): parse raw response into structured data
    """

    # Subclass configuration
    DEFAULT_TIMEOUT: float = 30.0
    RECEIPT_MODE: ReceiptMode = ReceiptMode.HTTP_TRANSCRIPT

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._client: httpx.Client | None = None

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Registry source_id (e.g., 'companies_house_api')."""
        ...

    @property
    @abstractmethod
    def source_group(self) -> str:
        """Registry source_group enum value."""
        ...

    @property
    @abstractmethod
    def independence_upstream_id(self) -> str:
        """System-of-record identifier for dedup."""
        ...

    @property
    @abstractmethod
    def resolution_role(self) -> str:
        """primary_evidence | secondary_corroboration | counter_signal | triage_only."""
        ...

    @property
    @abstractmethod
    def jurisdiction(self) -> str:
        """ISO 3166-1 alpha-2 or GLOBAL."""
        ...

    @abstractmethod
    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """
        Build the HTTP request for this source.

        Args:
            query_context: Entity IDs, time windows, search params.

        Returns:
            Tuple of (method, url, headers, params).
            - method: "GET" or "POST"
            - url: Full URL (no query params appended)
            - headers: Request headers (will be canonicalised)
            - params: Query parameters (for GET) or body (for POST), or None
        """
        ...

    @abstractmethod
    def extract(
        self, raw_body: bytes, status_code: int, query_context: dict[str, Any]
    ) -> tuple[dict[str, Any], float]:
        """
        Parse raw response into structured extract + confidence score.

        Args:
            raw_body: Raw response bytes.
            status_code: HTTP status code.
            query_context: Original query context.

        Returns:
            Tuple of (structured_extract, confidence_score).
            confidence_score is [0.0, 1.0].
        """
        ...

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: datetime
    ) -> FreshnessState:
        """
        Assess data freshness. Override in subclass for source-specific logic.

        Default: FRESH if retrieval succeeded.
        """
        return FreshnessState.FRESH

    def validate_receipt_mode(
        self, registry_source: RegistrySource
    ) -> CollectionResult | None:
        """Check that this collector's receipt mode meets the registry minimum.

        Returns None if the mode is sufficient, or a failure CollectionResult
        if insufficient.
        """
        minimum = ReceiptMode(registry_source.receipt_mode_minimum)
        if not meets_receipt_minimum(self.RECEIPT_MODE, minimum):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SOURCE_ERROR,
                error_message=(
                    f"Receipt mode {self.RECEIPT_MODE.value} does not meet "
                    f"registry minimum {minimum.value} for {registry_source.source_id}"
                ),
                duration_ms=0,
            )
        return None

    def _get_client(self) -> httpx.Client:
        """Lazy-initialise HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.get("timeout", self.DEFAULT_TIMEOUT),
                follow_redirects=True,
            )
        return self._client

    def collect(
        self,
        query_context: dict[str, Any],
        theatre_id: str | None = None,
        registry_source: RegistrySource | None = None,
    ) -> CollectionResult:
        """
        Execute collection: fetch → receipt → bundle.

        This is the main entry point. It handles timing, error handling,
        and receipt generation uniformly. Subclasses only implement
        build_request() and extract().
        """
        start_ms = int(time.time() * 1000)
        now = datetime.now(timezone.utc)

        # Receipt mode enforcement
        if registry_source is not None:
            mode_failure = self.validate_receipt_mode(registry_source)
            if mode_failure is not None:
                return mode_failure

        try:
            method, url, headers, params = self.build_request(query_context)
            client = self._get_client()

            # Execute request
            if method.upper() == "POST":
                response = client.post(url, headers=headers, json=params)
            else:
                response = client.get(url, headers=headers, params=params)

            timestamp_ms = int(time.time() * 1000)
            raw_body = response.content
            status_code = response.status_code

            # Check for HTTP errors
            if status_code == 401 or status_code == 403:
                return self._failure(
                    CollectionStatus.AUTH_FAILURE,
                    f"HTTP {status_code}",
                    start_ms,
                )
            if status_code == 429:
                return self._failure(
                    CollectionStatus.RATE_LIMITED,
                    "Rate limited",
                    start_ms,
                )
            if status_code == 404:
                return self._failure(
                    CollectionStatus.NOT_FOUND,
                    "Resource not found",
                    start_ms,
                )
            if status_code >= 500:
                return self._failure(
                    CollectionStatus.SOURCE_ERROR,
                    f"HTTP {status_code}",
                    start_ms,
                )

            # Build deterministic receipt
            response_body_hash = sha256_hex(raw_body)
            receipt_hash_val = http_transcript_hash(
                method=method,
                url=url,
                headers=headers,
                response_status=status_code,
                response_body=raw_body,
                timestamp_ms=timestamp_ms,
            )

            receipt = HTTPTranscriptReceipt(
                method=method.upper(),
                url=url,
                request_headers=headers,
                response_status=status_code,
                response_body_hash=response_body_hash,
                timestamp_ms=timestamp_ms,
                receipt_hash=receipt_hash_val,
            )

            # Extract structured data
            structured_extract, confidence = self.extract(
                raw_body, status_code, query_context
            )

            # Assess freshness
            freshness = self.assess_freshness(structured_extract, now)

            # Build evidence bundle
            bundle = EvidenceBundle(
                source_id=self.source_id,
                source_group=self.source_group,
                independence_upstream_id=self.independence_upstream_id,
                resolution_role=self.resolution_role,
                jurisdiction=self.jurisdiction,
                raw_payload_hash=response_body_hash,
                raw_payload_size_bytes=len(raw_body),
                receipt=receipt,
                receipt_mode=self.RECEIPT_MODE,
                structured_extract=structured_extract,
                confidence_score=confidence,
                freshness=freshness,
                retrieved_at=now,
                theatre_id=theatre_id,
                query_context=query_context,
            )

            elapsed = int(time.time() * 1000) - start_ms
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=bundle,
                duration_ms=elapsed,
                attempted_at=now,
            )

        except httpx.TimeoutException:
            return self._failure(CollectionStatus.TIMEOUT, "Request timed out", start_ms)
        except httpx.ConnectError as e:
            return self._failure(
                CollectionStatus.NETWORK_ERROR, f"Connection error: {e}", start_ms
            )
        except Exception as e:
            return self._failure(
                CollectionStatus.SOURCE_ERROR, f"Unexpected error: {e}", start_ms
            )

    def _failure(
        self, status: CollectionStatus, message: str, start_ms: int
    ) -> CollectionResult:
        """Build a failure CollectionResult."""
        elapsed = int(time.time() * 1000) - start_ms
        return CollectionResult(
            source_id=self.source_id,
            status=status,
            error_message=message,
            duration_ms=elapsed,
            attempted_at=datetime.now(timezone.utc),
        )

    # Map CollectionStatus to GapKind semantics.
    # NOT_FOUND is evidential absence (the source confirmed nothing exists).
    # All other failures are intelligence gaps (we could not observe).
    STATUS_TO_GAP_KIND: dict[CollectionStatus, GapKind] = {
        CollectionStatus.NOT_FOUND: GapKind.SIGNAL_ABSENCE,
    }

    # Map CollectionStatus to structured FailureMode for gap reports.
    STATUS_TO_FAILURE_MODE: dict[CollectionStatus, FailureMode] = {
        CollectionStatus.TIMEOUT: FailureMode.READ_TIMEOUT,
        CollectionStatus.NETWORK_ERROR: FailureMode.CONNECTION_REFUSED,
        CollectionStatus.SOURCE_ERROR: FailureMode.HTTP_ERROR_5XX,
        CollectionStatus.AUTH_FAILURE: FailureMode.HTTP_ERROR_4XX,
        CollectionStatus.RATE_LIMITED: FailureMode.HTTP_ERROR_4XX,
    }

    def to_gap_report(
        self, result: CollectionResult, allow_gap: bool = False
    ) -> GapReport:
        """Convert a failed CollectionResult to a GapReport."""
        gap_kind = self.STATUS_TO_GAP_KIND.get(
            result.status, GapKind.INTELLIGENCE_GAP
        )
        freshness = (
            FreshnessState.NO_DATA
            if gap_kind == GapKind.SIGNAL_ABSENCE
            else FreshnessState.ERROR
        )
        failure_mode = self.STATUS_TO_FAILURE_MODE.get(result.status)
        retriable = failure_mode in RETRIABLE_FAILURES if failure_mode is not None else False
        return GapReport(
            source_id=self.source_id,
            source_group=self.source_group,
            jurisdiction=self.jurisdiction,
            reason=result.status,
            error_detail=result.error_message,
            allow_gap=allow_gap,
            gap_kind=gap_kind,
            freshness=freshness,
            failure_mode=failure_mode,
            retriable=retriable,
        )

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
