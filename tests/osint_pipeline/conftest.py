"""Shared fixtures for OSINT pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from osint_pipeline.models.evidence import (
    CollectionStatus,
    EvidenceBundle,
    FreshnessState,
    GapReport,
    HTTPTranscriptReceipt,
    OracleCollectionSummary,
    ReceiptMode,
)
from osint_pipeline.models.registry import RegistryLoader


REGISTRY_PATH = Path(
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/"
    "echelon_osint_source_registry_v0_4_0.json"
)


@pytest.fixture
def registry_path() -> Path:
    """Path to the real registry fixture."""
    return REGISTRY_PATH


@pytest.fixture
def registry(registry_path: Path) -> RegistryLoader:
    """Loaded registry from the real fixture."""
    return RegistryLoader.from_file(registry_path)


def make_receipt(
    receipt_hash: str = "a" * 64,
    body_hash: str = "b" * 64,
) -> HTTPTranscriptReceipt:
    """Build a dummy receipt for testing."""
    return HTTPTranscriptReceipt(
        method="GET",
        url="http://localhost/test",
        response_status=200,
        response_body_hash=body_hash,
        timestamp_ms=1000,
        receipt_hash=receipt_hash,
    )


def make_bundle(
    source_id: str = "test_source",
    upstream_id: str = "test_upstream",
    source_group: str = "official_gov",
    confidence: float = 0.9,
    **kwargs,
) -> EvidenceBundle:
    """Build a dummy evidence bundle for testing."""
    defaults = dict(
        source_id=source_id,
        source_group=source_group,
        independence_upstream_id=upstream_id,
        resolution_role="primary_evidence",
        jurisdiction="GB",
        raw_payload_hash="c" * 64,
        raw_payload_size_bytes=100,
        receipt=make_receipt(),
        confidence_score=confidence,
    )
    defaults.update(kwargs)
    return EvidenceBundle(**defaults)


SAMPLE_COMPANY_PROFILE = {
    "company_number": "12345678",
    "company_name": "Test Company Ltd",
    "company_status": "active",
    "type": "ltd",
    "date_of_creation": "2020-01-01",
    "registered_office_address": {
        "address_line_1": "1 Test Street",
        "postal_code": "SW1A 1AA",
    },
    "sic_codes": ["62020"],
    "has_insolvency_history": False,
    "has_charges": False,
}


SAMPLE_QUERY_CONTEXT = {
    "company_number": "12345678",
}
