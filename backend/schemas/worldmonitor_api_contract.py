"""
World Monitor API Contract — v0.1 (Cycle-035 Prep)

Defines the FastAPI route stubs and Pydantic schemas for the three
World Monitor domains: intelligence, market, maritime.

This file is the API contract between Echelon's OSINT ingestion pipeline
and the World Monitor fork. It does NOT implement business logic — only
the request/response shapes and receipt generation contract.

Usage:
  - Copy to backend/api/worldmonitor_routes.py (routes)
  - Copy schemas to backend/schemas/worldmonitor.py (models)
  - Wire into main.py via router include

Registry alignment:
  worldmonitor_cii       → POST /api/v1/intelligence/cii
  worldmonitor_finance   → POST /api/v1/market/snapshot
  worldmonitor_maritime  → POST /api/v1/maritime/anomaly

All endpoints return EvidenceBundle-shaped responses with embedded
HTTP transcript receipts per the canonical spec (registry v0.3.2,
http_transcript_canonical_spec v1.0).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────

class WMDomain(str, Enum):
    """World Monitor domain identifiers. Maps to registry world_monitor_domain."""
    INTELLIGENCE = "intelligence"
    MARKET = "market"
    MARITIME = "maritime"


class MeasureType(str, Enum):
    """Normalised measure types produced by World Monitor endpoints."""
    COUNTRY_INSTABILITY_INDEX = "country_instability_index"
    SECTOR_RISK_SCORE = "sector_risk_score"
    FX_VOLATILITY = "fx_volatility"
    COMMODITY_ANOMALY = "commodity_anomaly"
    VESSEL_DENSITY_ANOMALY = "vessel_density_anomaly"
    AIS_GAP_DETECTED = "ais_gap_detected"
    DARK_FLEET_PROBABILITY = "dark_fleet_probability"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


# ── Shared Models ────────────────────────────────────────────────────

class GeoPoint(BaseModel):
    """Geographic point with uncertainty radius."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude (WGS84)")
    lon: float = Field(..., ge=-180, le=180, description="Longitude (WGS84)")
    radius_m: int = Field(50000, ge=0, description="Uncertainty radius in metres")


class NormalisedMeasure(BaseModel):
    """Standardised measurement output from any WM domain."""
    type: MeasureType
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit descriptor (e.g. '0_1', 'z_score', 'count')")
    metadata: Optional[dict] = Field(None, description="Domain-specific additional fields")


class NormalisedEvent(BaseModel):
    """Normalised event structure embedded in evidence bundles."""
    event_id: str = Field(..., description="Unique event identifier (format: evt_{record}_{seq})")
    geo: GeoPoint
    measure: NormalisedMeasure
    confidence: float = Field(..., ge=0.0, le=1.0, description="Source confidence [0, 1]")
    timestamp: datetime = Field(..., description="Event observation timestamp (UTC)")


class HTTPTranscriptReceipt(BaseModel):
    """
    Receipt following the HTTP transcript canonical spec (v1.0).

    The receipt hash is computed as:
      SHA-256(canonical_method + '\\n' + canonical_url + '\\n' +
              canonical_query + '\\n' + canonical_headers + '\\n' + body_hash)

    See: echelon_osint_source_registry_v0_3_2.json → http_transcript_canonical_spec
    """
    timestamp: datetime = Field(..., description="Receipt generation timestamp (UTC)")
    request_parameters: dict = Field(..., description="Canonical request parameters used")
    source_id: str = Field(..., description="Registry source_id that produced this data")
    source_version: str = Field(..., description="World Monitor build version (semver)")
    http_status: int = Field(..., description="HTTP status code of the upstream fetch")
    content_hash: str = Field(
        ...,
        min_length=64, max_length=64,
        description="SHA-256 of canonical JSON payload"
    )
    receipt_hash: Optional[str] = Field(
        None,
        min_length=64, max_length=64,
        description="SHA-256 of the canonical HTTP transcript (method+url+query+headers+body)"
    )


class EvidenceBundle(BaseModel):
    """
    Evidence bundle as consumed by the OSINT Composed Oracle template.

    This is the core interchange format between World Monitor and Echelon's
    verification pipeline. Each bundle carries a normalised event, its raw
    payload hash, and an HTTP transcript receipt for provenance verification.
    """
    bundle_id: str = Field(..., description="Unique bundle ID (format: eb_{context})")
    source_id: str = Field(..., description="Registry source_id (e.g. worldmonitor_cii)")
    source_group: str = Field(..., description="Registry source_group enum value")
    resolution_role: str = Field(
        ...,
        description="Registry resolution_role (primary_evidence | secondary_corroboration)"
    )
    evidence_timestamp: datetime = Field(..., description="When the evidence was captured (UTC)")
    raw_payload_hash: str = Field(
        ...,
        min_length=64, max_length=64,
        description="SHA-256 of the canonical raw payload JSON"
    )
    receipt: HTTPTranscriptReceipt
    normalised_event: NormalisedEvent

    # Optional fields for corroboration context
    confirms_primary: Optional[bool] = Field(
        None,
        description="Set to true when this bundle corroborates a primary evidence signal"
    )


# ── Intelligence Domain (CII) ───────────────────────────────────────

class CIIRequest(BaseModel):
    """Request to the Country Instability Index endpoint."""
    country_code: str = Field(
        ...,
        min_length=3, max_length=3,
        description="ISO 3166-1 alpha-3 country code (e.g. 'IRN', 'SYR')"
    )
    geo: Optional[GeoPoint] = Field(None, description="Optional sub-national geographic focus")
    evaluation_window_start: datetime = Field(..., description="Window start (UTC)")
    evaluation_window_end: datetime = Field(..., description="Window end (UTC)")


class CIIResponse(BaseModel):
    """Response from /api/v1/intelligence/cii"""
    domain: Literal["intelligence"] = "intelligence"
    bundle: EvidenceBundle
    upstream_sources_consulted: list[str] = Field(
        default_factory=list,
        description="List of upstream source_ids consumed to produce this CII score"
    )


# ── Market Domain ────────────────────────────────────────────────────

class MarketSnapshotRequest(BaseModel):
    """Request to the Market Snapshot endpoint."""
    asset_class: str = Field(
        ...,
        description="Asset class identifier (e.g. 'fx', 'commodity', 'equity_index')"
    )
    symbol: str = Field(..., description="Instrument symbol (e.g. 'USDIRR', 'BRENT', 'VIX')")
    geo: Optional[GeoPoint] = Field(None, description="Optional geographic context")
    evaluation_window_start: datetime = Field(..., description="Window start (UTC)")
    evaluation_window_end: datetime = Field(..., description="Window end (UTC)")


class MarketSnapshotResponse(BaseModel):
    """Response from /api/v1/market/snapshot"""
    domain: Literal["market"] = "market"
    bundle: EvidenceBundle
    upstream_sources_consulted: list[str] = Field(
        default_factory=list,
        description="List of upstream source_ids consumed (e.g. polygon_io, commodities_api)"
    )


# ── Maritime Domain ──────────────────────────────────────────────────

class MaritimeAnomalyRequest(BaseModel):
    """Request to the Maritime Anomaly Detection endpoint."""
    geo: GeoPoint = Field(..., description="Centre point of the maritime zone of interest")
    radius_nm: float = Field(
        50.0, ge=1.0, le=500.0,
        description="Search radius in nautical miles"
    )
    anomaly_types: list[str] = Field(
        default_factory=lambda: ["vessel_density", "ais_gap", "dark_fleet"],
        description="Types of anomaly to detect"
    )
    evaluation_window_start: datetime = Field(..., description="Window start (UTC)")
    evaluation_window_end: datetime = Field(..., description="Window end (UTC)")


class MaritimeAnomalyResponse(BaseModel):
    """Response from /api/v1/maritime/anomaly"""
    domain: Literal["maritime"] = "maritime"
    bundle: EvidenceBundle
    anomaly_count: int = Field(0, ge=0, description="Number of anomalies detected in window")
    upstream_sources_consulted: list[str] = Field(
        default_factory=list,
        description="List of upstream source_ids consumed (e.g. spire_ais, marinetraffic)"
    )


# ── Health / Meta ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response for all WM domains."""
    status: HealthStatus
    version: str = Field(..., description="World Monitor build version (semver)")
    domains: dict[str, HealthStatus] = Field(
        ...,
        description="Per-domain health status"
    )
    uptime_seconds: int = Field(..., ge=0)
    last_evidence_timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp of most recent evidence bundle produced"
    )


class RegistryAlignmentResponse(BaseModel):
    """
    Returns the source_ids this WM instance serves, for the ingestion
    pipeline to verify alignment with the OSINT source registry.
    """
    source_ids: list[str] = Field(
        ...,
        description="Registry source_ids this instance is authoritative for"
    )
    registry_version_compatible: str = Field(
        ...,
        description="Minimum registry version this instance is compatible with"
    )
    domains: list[WMDomain]


# ── Utility: Canonical Hashing ───────────────────────────────────────

def canonical_json(obj: dict) -> str:
    """
    Produce canonical JSON per registry spec:
    json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_content_hash(payload: dict) -> str:
    """SHA-256 of canonical JSON payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def compute_receipt_hash(
    method: str,
    url: str,
    query: str,
    headers: str,
    body_hash: str,
) -> str:
    """
    SHA-256 of the canonical HTTP transcript per registry spec v1.0:
    canonical_method + '\\n' + canonical_url + '\\n' + canonical_query +
    '\\n' + canonical_headers + '\\n' + body_hash
    """
    transcript = f"{method.upper()}\n{url}\n{query}\n{headers}\n{body_hash}"
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


# ── FastAPI Route Stubs ──────────────────────────────────────────────
#
# These are stubs only. Implementation lives in Cycle-035.
# Wire into main.py:
#   from backend.api.worldmonitor_routes import router as wm_router
#   app.include_router(wm_router, prefix="/api/v1", tags=["worldmonitor"])

"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    '''Health check across all World Monitor domains.'''
    raise HTTPException(status_code=501, detail="Not implemented — Cycle-035")


@router.get("/registry-alignment", response_model=RegistryAlignmentResponse)
async def registry_alignment():
    '''Returns source_ids this WM instance serves.'''
    raise HTTPException(status_code=501, detail="Not implemented — Cycle-035")


@router.post("/intelligence/cii", response_model=CIIResponse)
async def intelligence_cii(request: CIIRequest):
    '''
    Country Instability Index.

    Produces an evidence bundle with a normalised CII score for the
    requested country/region within the evaluation window. Consults
    upstream intelligence sources (GDELT, ACLED, social feeds) and
    returns a composite instability measure.

    Registry source_id: worldmonitor_cii
    '''
    raise HTTPException(status_code=501, detail="Not implemented — Cycle-035")


@router.post("/market/snapshot", response_model=MarketSnapshotResponse)
async def market_snapshot(request: MarketSnapshotRequest):
    '''
    Market Snapshot.

    Produces an evidence bundle with a normalised market anomaly score
    for the requested asset within the evaluation window. Consults
    upstream market data sources (Polygon.io, commodities feeds) and
    returns anomaly detection results.

    Registry source_id: worldmonitor_finance
    '''
    raise HTTPException(status_code=501, detail="Not implemented — Cycle-035")


@router.post("/maritime/anomaly", response_model=MaritimeAnomalyResponse)
async def maritime_anomaly(request: MaritimeAnomalyRequest):
    '''
    Maritime Anomaly Detection.

    Produces an evidence bundle with normalised maritime anomaly data
    for the requested geographic zone within the evaluation window.
    Detects vessel density anomalies, AIS gaps, and dark fleet signals.
    Consults upstream AIS sources (Spire, MarineTraffic).

    Registry source_id: worldmonitor_maritime
    '''
    raise HTTPException(status_code=501, detail="Not implemented — Cycle-035")
"""


# ── Contract Tests (run with: python3 -m pytest worldmonitor_api_contract.py) ──

def test_schemas_instantiate():
    """Verify all schema models can be instantiated with valid data."""
    from datetime import timezone

    now = datetime.now(timezone.utc)

    geo = GeoPoint(lat=26.5667, lon=56.25, radius_m=50000)
    measure = NormalisedMeasure(type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.78, unit="0_1")
    event = NormalisedEvent(
        event_id="evt_test_001",
        geo=geo,
        measure=measure,
        confidence=0.85,
        timestamp=now,
    )
    receipt = HTTPTranscriptReceipt(
        timestamp=now,
        request_parameters={"country": "IRN", "endpoint": "/api/v1/intelligence/cii"},
        source_id="worldmonitor_cii",
        source_version="v0.1.0",
        http_status=200,
        content_hash="a" * 64,
    )
    bundle = EvidenceBundle(
        bundle_id="eb_test_001",
        source_id="worldmonitor_cii",
        source_group="alt_data_behavioural",
        resolution_role="primary_evidence",
        evidence_timestamp=now,
        raw_payload_hash="a" * 64,
        receipt=receipt,
        normalised_event=event,
    )
    assert bundle.source_id == "worldmonitor_cii"
    assert bundle.receipt.content_hash == "a" * 64

    # Request models
    cii_req = CIIRequest(
        country_code="IRN",
        evaluation_window_start=now,
        evaluation_window_end=now,
    )
    assert cii_req.country_code == "IRN"

    mkt_req = MarketSnapshotRequest(
        asset_class="fx",
        symbol="USDIRR",
        evaluation_window_start=now,
        evaluation_window_end=now,
    )
    assert mkt_req.symbol == "USDIRR"

    mar_req = MaritimeAnomalyRequest(
        geo=geo,
        evaluation_window_start=now,
        evaluation_window_end=now,
    )
    assert mar_req.radius_nm == 50.0


def test_canonical_hashing():
    """Verify canonical JSON and content hash are deterministic."""
    obj = {"b": 2, "a": 1, "c": {"z": 26, "a": 1}}
    canonical = canonical_json(obj)
    assert canonical == '{"a":1,"b":2,"c":{"a":1,"z":26}}'

    h = compute_content_hash(obj)
    assert len(h) == 64
    # Same input must produce same hash
    assert compute_content_hash(obj) == h


def test_receipt_hash():
    """Verify receipt hash computation follows the canonical spec."""
    h = compute_receipt_hash(
        method="GET",
        url="https://localhost/api/v1/intelligence/cii",
        query="country=IRN",
        headers="accept:application/json",
        body_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    assert len(h) == 64
    # Deterministic
    h2 = compute_receipt_hash(
        method="get",  # lowercase → uppercased inside function
        url="https://localhost/api/v1/intelligence/cii",
        query="country=IRN",
        headers="accept:application/json",
        body_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    assert h == h2


if __name__ == "__main__":
    test_schemas_instantiate()
    test_canonical_hashing()
    test_receipt_hash()
    print("ALL CONTRACT TESTS PASSED")
