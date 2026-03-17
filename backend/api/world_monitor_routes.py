from __future__ import annotations

from collections import Counter
from datetime import datetime
from math import sqrt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.convergence_routes import get_heatmap
from backend.api.situation_room import state as situation_room_state
from backend.core.osint_registry import get_osint_registry
from backend.core.signal_detector import RegionOfInterest, Signal
from backend.database.connection import get_db
from backend.database.models import InvestigationCertificateRecord, InvestigationEvidenceItem
from backend.osint.collectors.worldmonitor import WorldMonitorCollector
from backend.osint.models.evidence import WMDomain
from backend.schemas.worldmonitor_api_contract import (
    CIIRequest, CIIResponse,
    MarketSnapshotRequest, MarketSnapshotResponse,
    MaritimeAnomalyRequest, MaritimeAnomalyResponse,
)
from backend.services.signal_persistence import persist_signal


router = APIRouter(prefix="/api/v1/world-monitor", tags=["World Monitor"])


class WorldMonitorGeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class WorldMonitorSignalResponse(BaseModel):
    id: str
    title: str
    description: str
    source: str
    category: str
    region: str
    level: float
    confidence: float
    severity: str
    timestamp: datetime
    expires_at: datetime
    geo: WorldMonitorGeoPoint
    correlated_signals: list[str]
    theatre_ids: list[str] | None = None
    investigation_id: str | None = None
    certificate_id: str | None = None
    link_confidence: str | None = None
    link_reason: str | None = None

    @model_validator(mode="after")
    def validate_link_metadata(self) -> "WorldMonitorSignalResponse":
        if self.theatre_ids or self.investigation_id or self.certificate_id:
            if not self.link_confidence or not self.link_reason:
                raise ValueError(
                    "World Monitor signal links require both link_confidence and link_reason"
                )
        return self


class WorldMonitorHeatmapCellResponse(BaseModel):
    lat: float
    lon: float
    density: float
    events: int
    sources: list[str]
    theatres: list[str]


class WorldMonitorSummaryResponse(BaseModel):
    updated_at: datetime
    tension_index: float
    tension_level: str
    chaos_index: float
    active_missions: int
    active_agents: int
    active_signals: int
    critical_signals: int
    convergence_cells: int


class WorldMonitorLiveResponse(BaseModel):
    updated_at: datetime
    summary: WorldMonitorSummaryResponse
    category_counts: dict[str, int]
    severity_counts: dict[str, int]
    source_counts: dict[str, int]
    signals: list[WorldMonitorSignalResponse]
    convergence_cells: list[WorldMonitorHeatmapCellResponse]
    missions: list[dict[str, Any]]
    intel: list[dict[str, Any]]
    live_feed: list[dict[str, Any]]


REGION_CENTERS: dict[RegionOfInterest, tuple[float, float]] = {
    RegionOfInterest.WASHINGTON_DC: (38.9072, -77.0369),
    RegionOfInterest.MOSCOW: (55.7558, 37.6173),
    RegionOfInterest.BEIJING: (39.9042, 116.4074),
    RegionOfInterest.TEHRAN: (35.6892, 51.3890),
    RegionOfInterest.PYONGYANG: (39.0392, 125.7625),
    RegionOfInterest.TAIPEI: (25.0330, 121.5654),
    RegionOfInterest.JERUSALEM: (31.7683, 35.2137),
    RegionOfInterest.KYIV: (50.4501, 30.5234),
    RegionOfInterest.BRUSSELS: (50.8503, 4.3517),
    RegionOfInterest.GENEVA: (46.2044, 6.1432),
    RegionOfInterest.STRAIT_HORMUZ: (26.5667, 56.2500),
    RegionOfInterest.SOUTH_CHINA_SEA: (15.0, 115.0),
    RegionOfInterest.BALTIC_SEA: (58.0, 20.0),
}


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def _extract_geo(signal: Signal) -> WorldMonitorGeoPoint:
    raw = getattr(signal, "raw_data", {}) or {}

    if isinstance(raw.get("geo"), dict):
        geo = raw["geo"]
        lat = geo.get("lat")
        lon = geo.get("lon", geo.get("lng"))
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return WorldMonitorGeoPoint(lat=lat, lon=lon)

    lat = raw.get("lat")
    lon = raw.get("lon", raw.get("lng"))
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return WorldMonitorGeoPoint(lat=lat, lon=lon)

    center = REGION_CENTERS.get(signal.region)
    if center:
        return WorldMonitorGeoPoint(lat=center[0], lon=center[1])

    return WorldMonitorGeoPoint(lat=0.0, lon=0.0)


def _infer_category_map() -> dict[str, str]:
    registry = get_osint_registry()
    grouped = registry.get_signals_by_category()
    category_map: dict[str, str] = {}
    for category, signals in grouped.items():
        for signal in signals:
            category_map[signal.id] = category
    return category_map


def _signal_title(signal: Signal) -> str:
    source = signal.source.value.replace("_", " ").title()
    region = signal.region.value.replace("_", " ").title()
    return f"{source} · {region}"


def _distance_between(
    left: WorldMonitorGeoPoint,
    *,
    lat: float,
    lon: float,
) -> float:
    lat_diff = left.lat - lat
    lon_diff = left.lon - lon
    return sqrt(lat_diff * lat_diff + lon_diff * lon_diff)


def _match_theatre_ids(
    geo: WorldMonitorGeoPoint,
    heatmap_cells: list[WorldMonitorHeatmapCellResponse],
) -> list[str]:
    nearby_cells = sorted(
        (
            cell
            for cell in heatmap_cells
            if cell.theatres
        ),
        key=lambda cell: _distance_between(geo, lat=cell.lat, lon=cell.lon),
    )

    theatre_ids: list[str] = []
    for cell in nearby_cells[:3]:
        distance = _distance_between(geo, lat=cell.lat, lon=cell.lon)
        # Convergence cells are coarse regional buckets, so keep the match broad but bounded.
        if distance > 18:
            continue
        for theatre_id in cell.theatres:
            if theatre_id not in theatre_ids:
                theatre_ids.append(theatre_id)

    return theatre_ids


def _extract_signal_reference_ids(references: Any) -> set[str]:
    if not isinstance(references, list):
        return set()

    signal_ids: set[str] = set()
    for reference in references:
        if not isinstance(reference, str) or not reference:
            continue
        if reference.startswith("signal:"):
            signal_ids.add(reference.split("signal:", 1)[1])
        elif reference.startswith("worldmonitor:"):
            signal_ids.add(reference.split("worldmonitor:", 1)[1])
        elif reference.startswith("world_monitor_signal:"):
            signal_ids.add(reference.split("world_monitor_signal:", 1)[1])
        elif len(reference) >= 8:
            # Backward-compatible path: plain signal IDs persisted directly in references.
            signal_ids.add(reference)
    return signal_ids


async def _load_investigation_links(
    db: AsyncSession,
    signal_ids: set[str],
) -> dict[str, str]:
    if not signal_ids:
        return {}

    result = await db.execute(
        select(
            InvestigationEvidenceItem.investigation_id,
            InvestigationEvidenceItem.references_json,
            InvestigationEvidenceItem.submitted_at,
        ).order_by(InvestigationEvidenceItem.submitted_at.desc())
    )

    links: dict[str, str] = {}
    for investigation_id, references_json, _submitted_at in result.all():
        for signal_id in _extract_signal_reference_ids(references_json):
            if signal_id in signal_ids and signal_id not in links:
                links[signal_id] = investigation_id

    return links


async def _load_certificate_links(
    db: AsyncSession,
    investigation_ids: set[str],
) -> dict[str, str]:
    if not investigation_ids:
        return {}

    result = await db.execute(
        select(
            InvestigationCertificateRecord.investigation_id,
            InvestigationCertificateRecord.id,
        ).where(InvestigationCertificateRecord.investigation_id.in_(investigation_ids))
    )

    return {
        investigation_id: certificate_id
        for investigation_id, certificate_id in result.all()
    }


@router.get("/live", response_model=WorldMonitorLiveResponse)
async def get_world_monitor_live(
    db: AsyncSession = Depends(get_db),
) -> WorldMonitorLiveResponse:
    registry = get_osint_registry()
    category_map = _infer_category_map()

    heatmap = await get_heatmap()
    heatmap_cells = [
        WorldMonitorHeatmapCellResponse(
            lat=cell.lat,
            lon=cell.lon,
            density=cell.density,
            events=cell.events,
            sources=cell.sources,
            theatres=cell.theatres,
        )
        for cell in heatmap.cells
    ]

    sorted_signals = sorted(
        registry.active_signals,
        key=lambda signal: (signal.level * signal.confidence, signal.timestamp),
        reverse=True,
    )
    visible_signal_ids = {signal.id for signal in sorted_signals[:120]}
    investigation_links = await _load_investigation_links(db, visible_signal_ids)
    certificate_links = await _load_certificate_links(
        db,
        set(investigation_links.values()),
    )

    signals: list[WorldMonitorSignalResponse] = []
    for signal in sorted_signals[:120]:
        geo = _extract_geo(signal)
        theatre_ids = _match_theatre_ids(geo, heatmap_cells)
        investigation_id = investigation_links.get(signal.id)
        certificate_id = (
            certificate_links.get(investigation_id)
            if investigation_id
            else None
        )
        signals.append(
            WorldMonitorSignalResponse(
                id=signal.id,
                title=_signal_title(signal),
                description=signal.description,
                source=signal.source.value,
                category=category_map.get(signal.id, "other"),
                region=signal.region.value,
                level=signal.level,
                confidence=signal.confidence,
                severity=signal.severity,
                timestamp=signal.timestamp,
                expires_at=signal.expires_at,
                geo=geo,
                correlated_signals=signal.correlated_signals,
                theatre_ids=theatre_ids or None,
                investigation_id=investigation_id,
                certificate_id=certificate_id,
                link_confidence=(
                    "persisted"
                    if investigation_id or certificate_id
                    else "inferred"
                    if theatre_ids
                    else None
                ),
                link_reason=(
                    "investigation_certificate"
                    if certificate_id
                    else "signal_ingested"
                    if investigation_id
                    else "convergence_cell_geo_match"
                    if theatre_ids
                    else None
                ),
            )
        )

    severity_counts = Counter(signal.severity.lower() for signal in signals)
    source_counts = Counter(signal.source for signal in signals)
    category_counts = Counter(signal.category for signal in signals)

    missions = [_dump_model(mission) for mission in situation_room_state.missions[:8]]

    now = datetime.utcnow()
    intel = [
        _dump_model(item)
        for item in situation_room_state.intel_items
        if not item.expires_at or item.expires_at > now
    ][:8]
    live_feed = [_dump_model(event) for event in situation_room_state.live_events[:16]]

    active_missions = len([mission for mission in situation_room_state.missions if mission.status == "active"])
    critical_signals = len([signal for signal in signals if signal.severity in {"CRITICAL", "HIGH"}])

    summary = WorldMonitorSummaryResponse(
        updated_at=now,
        tension_index=situation_room_state.tension_index,
        tension_level=situation_room_state.get_tension_level().value,
        chaos_index=situation_room_state.chaos_index,
        active_missions=active_missions,
        active_agents=88,
        active_signals=len(signals),
        critical_signals=critical_signals,
        convergence_cells=len(heatmap_cells),
    )

    return WorldMonitorLiveResponse(
        updated_at=now,
        summary=summary,
        category_counts=dict(category_counts),
        severity_counts=dict(severity_counts),
        source_counts=dict(source_counts),
        signals=signals,
        convergence_cells=heatmap_cells,
        missions=missions,
        intel=intel,
        live_feed=live_feed,
    )


# ── POST Endpoints (Cycle-025) ─────────────────────────────────────


@router.post("/intelligence/cii", response_model=CIIResponse)
async def post_cii(
    body: CIIRequest,
    theatre_id: str = Query(..., description="Theatre context ID"),
    db: AsyncSession = Depends(get_db),
) -> CIIResponse:
    """Country Instability Index — collect + persist + return evidence bundle."""
    collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE)
    request_dict = {
        "country_code": body.country_code,
        "geo": body.geo.model_dump() if body.geo else None,
        "evaluation_window_start": body.evaluation_window_start.isoformat(),
        "evaluation_window_end": body.evaluation_window_end.isoformat(),
    }
    result = await collector.fetch(request_dict, theatre_id=theatre_id)

    if not result.success or not result.bundle:
        raise HTTPException(status_code=502, detail=result.error or "Collector failed")

    await persist_signal(
        session=db,
        result=result,
        source_id=collector.source_id(),
        source_group=result.bundle.source_group,
    )
    await db.commit()

    metadata = {}
    if result.bundle.normalised_event.measure.metadata:
        metadata = result.bundle.normalised_event.measure.metadata

    return CIIResponse(
        bundle=result.bundle,
        upstream_sources_consulted=[collector.source_id()],
        forecast_score=metadata.get("forecast_score"),
        forecast_weight=metadata.get("forecast_weight"),
        sanctions_exposure=metadata.get("sanctions_exposure"),
    )


@router.post("/market/snapshot", response_model=MarketSnapshotResponse)
async def post_market_snapshot(
    body: MarketSnapshotRequest,
    theatre_id: str = Query(..., description="Theatre context ID"),
    db: AsyncSession = Depends(get_db),
) -> MarketSnapshotResponse:
    """Market Snapshot — collect + persist + return evidence bundle."""
    collector = WorldMonitorCollector(domain=WMDomain.MARKET)
    request_dict = {
        "asset_class": body.asset_class,
        "symbol": body.symbol,
        "geo": body.geo.model_dump() if body.geo else None,
        "evaluation_window_start": body.evaluation_window_start.isoformat(),
        "evaluation_window_end": body.evaluation_window_end.isoformat(),
    }
    result = await collector.fetch(request_dict, theatre_id=theatre_id)

    if not result.success or not result.bundle:
        raise HTTPException(status_code=502, detail=result.error or "Collector failed")

    await persist_signal(
        session=db,
        result=result,
        source_id=collector.source_id(),
        source_group=result.bundle.source_group,
    )
    await db.commit()

    metadata = {}
    if result.bundle.normalised_event.measure.metadata:
        metadata = result.bundle.normalised_event.measure.metadata

    return MarketSnapshotResponse(
        bundle=result.bundle,
        upstream_sources_consulted=[collector.source_id()],
        supply_chain_severity=metadata.get("supply_chain_severity"),
    )


@router.post("/maritime/anomaly", response_model=MaritimeAnomalyResponse)
async def post_maritime_anomaly(
    body: MaritimeAnomalyRequest,
    theatre_id: str = Query(..., description="Theatre context ID"),
    db: AsyncSession = Depends(get_db),
) -> MaritimeAnomalyResponse:
    """Maritime Anomaly Detection — collect + persist + return evidence bundle."""
    collector = WorldMonitorCollector(domain=WMDomain.MARITIME)
    request_dict = {
        "geo": body.geo.model_dump(),
        "radius_nm": body.radius_nm,
        "anomaly_types": body.anomaly_types,
        "evaluation_window_start": body.evaluation_window_start.isoformat(),
        "evaluation_window_end": body.evaluation_window_end.isoformat(),
    }
    result = await collector.fetch(request_dict, theatre_id=theatre_id)

    if not result.success or not result.bundle:
        raise HTTPException(status_code=502, detail=result.error or "Collector failed")

    await persist_signal(
        session=db,
        result=result,
        source_id=collector.source_id(),
        source_group=result.bundle.source_group,
    )
    await db.commit()

    metadata = {}
    if result.bundle.normalised_event.measure.metadata:
        metadata = result.bundle.normalised_event.measure.metadata

    return MaritimeAnomalyResponse(
        bundle=result.bundle,
        anomaly_count=int(result.bundle.normalised_event.measure.value),
        upstream_sources_consulted=[collector.source_id()],
        corridor=metadata.get("corridor"),
        corridor_risk=metadata.get("corridor_risk"),
        shipping_rate_index=metadata.get("shipping_rate_index"),
    )
