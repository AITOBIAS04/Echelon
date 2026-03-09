from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.osint_registry import get_osint_registry
from backend.database.connection import get_db
from backend.database.models import (
    Agent,
    AgentDeployment,
    DeploymentAuditEvent,
    Investigation,
    InvestigationCertificateRecord,
    InvestigationDriftEvent,
    Paradox,
    Theatre,
    TheatreTemplate,
    TheatreCertificate,
    Timeline,
    UserPosition,
    WingFlap,
)
from backend.dependencies import get_current_user


router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

SUPPORTED_RANGES = {"7d": 7, "30d": 30, "90d": 90}


class AnalyticsPoint(BaseModel):
    timestamp: datetime
    value: float


class PlatformAnalyticsCurrent(BaseModel):
    active_theatres: int
    completed_theatres: int
    active_investigations: int
    ready_investigations: int
    issued_certificates: int
    active_paradoxes: int
    active_signals: int
    critical_signals: int
    convergence_cells: int


class AnalyticsExplanationItem(BaseModel):
    id: str
    kind: str
    timestamp: datetime
    title: str
    summary: str
    tone: str
    provenance: str
    theatre_id: str | None = None
    investigation_id: str | None = None
    certificate_id: str | None = None
    timeline_id: str | None = None


class PlatformAnalyticsResponse(BaseModel):
    updated_at: datetime
    range: str
    bucket_size: str
    current: PlatformAnalyticsCurrent
    timeseries: dict[str, list[AnalyticsPoint]]
    comparisons: dict[str, "AnalyticsComparison"]
    explanations: dict[str, list[AnalyticsExplanationItem]]


class AnalyticsBreakdownsResponse(BaseModel):
    updated_at: datetime
    applied_filters: dict[str, str]
    signal_categories: dict[str, int]
    signal_sources: dict[str, int]
    signal_severities: dict[str, int]
    theatre_states: dict[str, int]
    theatre_families: dict[str, int]
    theatre_inquiry_classes: dict[str, int]
    investigation_statuses: dict[str, int]
    investigation_classes: dict[str, int]
    investigation_routing_decisions: dict[str, int]
    theatre_routing_hints: dict[str, int]
    theatre_gate_statuses: dict[str, int]
    agent_archetypes: dict[str, int]


class RiskTrendResponse(BaseModel):
    updated_at: datetime
    range: str
    bucket_size: str
    timeseries: dict[str, list[AnalyticsPoint]]
    comparisons: dict[str, "AnalyticsComparison"]
    explanations: dict[str, list[AnalyticsExplanationItem]]


class PortfolioPositionSummary(BaseModel):
    timeline_id: str
    timeline_name: str
    side: str
    current_price: float
    average_entry_price: float
    shards_held: int
    notional: float
    unrealised_pnl: float
    has_active_paradox: bool
    logic_gap: float


class PortfolioAnalyticsCurrent(BaseModel):
    total_notional: float
    total_unrealised_pnl: float
    position_count: int
    winning_positions: int
    losing_positions: int
    at_risk_positions: int


class PortfolioAnalyticsResponse(BaseModel):
    updated_at: datetime
    range: str
    history_status: str
    current: PortfolioAnalyticsCurrent
    top_positions: list[PortfolioPositionSummary]
    timeseries: list[AnalyticsPoint]


class AnalyticsComparison(BaseModel):
    current_period: float
    previous_period: float
    delta: float
    change_pct: float | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_range(range_key: str) -> tuple[datetime, list[datetime]]:
    if range_key not in SUPPORTED_RANGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported range '{range_key}'. Use one of: {', '.join(SUPPORTED_RANGES)}",
        )

    now = _utc_now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = SUPPORTED_RANGES[range_key]
    first_bucket = today - timedelta(days=days - 1)
    buckets = [first_bucket + timedelta(days=index) for index in range(days)]
    return first_bucket, buckets


def _parse_bucket_date(bucket_date: str | None) -> datetime | None:
    if not bucket_date:
        return None
    try:
        parsed = datetime.fromisoformat(bucket_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="bucket_date must be ISO date or datetime.") from exc
    return _as_utc(parsed.replace(hour=0, minute=0, second=0, microsecond=0))


def _comparison_windows(range_key: str) -> tuple[datetime, datetime, datetime, datetime]:
    days = SUPPORTED_RANGES[range_key]
    now = _utc_now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    current_start = today - timedelta(days=days - 1)
    current_end = today + timedelta(days=1)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days)
    return current_start, current_end, previous_start, previous_end


def _zero_points(buckets: list[datetime]) -> list[AnalyticsPoint]:
    return [AnalyticsPoint(timestamp=bucket, value=0) for bucket in buckets]


def _count_by_day(
    values: list[datetime | None],
    buckets: list[datetime],
) -> list[AnalyticsPoint]:
    counts = {bucket.date(): 0 for bucket in buckets}
    for value in values:
        moment = _as_utc(value)
        if moment is None:
            continue
        bucket_day = moment.replace(hour=0, minute=0, second=0, microsecond=0).date()
        if bucket_day in counts:
            counts[bucket_day] += 1

    return [
        AnalyticsPoint(timestamp=bucket, value=counts[bucket.date()])
        for bucket in buckets
    ]


def _active_paradox_series(
    paradox_windows: list[tuple[datetime | None, datetime | None]],
    buckets: list[datetime],
) -> list[AnalyticsPoint]:
    points: list[AnalyticsPoint] = []
    for bucket in buckets:
        bucket_end = bucket + timedelta(days=1)
        count = 0
        for spawned_at, resolved_at in paradox_windows:
            spawned = _as_utc(spawned_at)
            resolved = _as_utc(resolved_at)
            if spawned is None:
                continue
            if spawned < bucket_end and (resolved is None or resolved >= bucket):
                count += 1
        points.append(AnalyticsPoint(timestamp=bucket, value=count))
    return points


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _clean_filter_map(**kwargs: str | None) -> dict[str, str]:
    return {key: value for key, value in kwargs.items() if value}


def _count_in_window(
    values: list[datetime | None],
    start: datetime,
    end: datetime,
) -> int:
    count = 0
    for value in values:
        moment = _as_utc(value)
        if moment is None:
            continue
        if start <= moment < end:
            count += 1
    return count


def _average_value(points: list[AnalyticsPoint]) -> float:
    if not points:
        return 0.0
    return sum(point.value for point in points) / len(points)


def _build_comparison(current_period: float, previous_period: float) -> AnalyticsComparison:
    delta = current_period - previous_period
    change_pct = None if previous_period == 0 else (delta / previous_period) * 100
    return AnalyticsComparison(
        current_period=round(current_period, 2),
        previous_period=round(previous_period, 2),
        delta=round(delta, 2),
        change_pct=None if change_pct is None else round(change_pct, 2),
    )


def _recent_items_in_window(
    rows: list,
    timestamp_getter,
    start: datetime,
    end: datetime,
    limit: int = 5,
) -> list:
    filtered: list[tuple[datetime, object]] = []
    for row in rows:
        moment = _as_utc(timestamp_getter(row))
        if moment is None:
            continue
        if start <= moment < end:
            filtered.append((moment, row))
    filtered.sort(key=lambda item: item[0], reverse=True)
    return [row for _moment, row in filtered[:limit]]


@router.get("/platform", response_model=PlatformAnalyticsResponse)
async def get_platform_analytics(
    range_key: str = Query("30d", alias="range"),
    bucket_date: str | None = Query(None),
    theatre_inquiry_class: str | None = Query(None),
    theatre_family: str | None = Query(None),
    investigation_class: str | None = Query(None),
    agent_archetype: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PlatformAnalyticsResponse:
    _start_bucket, buckets = _parse_range(range_key)
    current_start, current_end, previous_start, previous_end = _comparison_windows(range_key)
    explanation_bucket = _parse_bucket_date(bucket_date)
    explanation_start = explanation_bucket or current_start
    explanation_end = (explanation_bucket + timedelta(days=1)) if explanation_bucket else current_end
    registry = get_osint_registry()

    theatre_rows = await db.execute(select(Theatre.state, Theatre.created_at))
    theatre_explanation_rows = await db.execute(
        select(
            Theatre.id,
            Theatre.construct_id,
            Theatre.inquiry_class,
            Theatre.created_at,
            TheatreTemplate.template_family,
        ).join(TheatreTemplate, Theatre.template_id == TheatreTemplate.id)
    )
    investigation_rows = await db.execute(
        select(
            Investigation.status,
            Investigation.created_at,
            Investigation.stop_condition_status,
        )
    )
    investigation_explanation_rows = await db.execute(
        select(
            Investigation.id,
            Investigation.construct_id,
            Investigation.inquiry_class,
            Investigation.created_at,
        )
    )
    theatre_certificate_rows = await db.execute(select(TheatreCertificate.issued_at))
    theatre_certificate_explanation_rows = await db.execute(
        select(
            TheatreCertificate.id,
            TheatreCertificate.theatre_id,
            TheatreCertificate.construct_id,
            TheatreCertificate.issued_at,
        )
    )
    investigation_certificate_rows = await db.execute(
        select(InvestigationCertificateRecord.issued_at)
    )
    investigation_certificate_explanation_rows = await db.execute(
        select(
            InvestigationCertificateRecord.id,
            InvestigationCertificateRecord.investigation_id,
            InvestigationCertificateRecord.routing_decision,
            InvestigationCertificateRecord.issued_at,
        )
    )
    deployment_rows = await db.execute(select(AgentDeployment.deployed_at))
    deployment_explanation_rows = await db.execute(
        select(
            AgentDeployment.id,
            AgentDeployment.theatre_id,
            AgentDeployment.deployed_at,
            Agent.name,
            Theatre.construct_id,
            Agent.archetype,
        )
        .join(Agent, Agent.id == AgentDeployment.agent_id)
        .join(Theatre, Theatre.id == AgentDeployment.theatre_id)
    )
    deployment_audit_rows = await db.execute(
        select(
            DeploymentAuditEvent.id,
            DeploymentAuditEvent.event_type,
            DeploymentAuditEvent.created_at,
            AgentDeployment.theatre_id,
            Theatre.construct_id,
            Agent.name,
            Agent.archetype,
        )
        .join(AgentDeployment, AgentDeployment.id == DeploymentAuditEvent.deployment_id)
        .join(Agent, Agent.id == AgentDeployment.agent_id)
        .join(Theatre, Theatre.id == AgentDeployment.theatre_id)
    )
    certificate_ready_rows = await db.execute(
        select(
            InvestigationCertificateRecord.id,
            InvestigationCertificateRecord.investigation_id,
            InvestigationCertificateRecord.routing_decision,
            InvestigationCertificateRecord.ready_at,
            Investigation.inquiry_class,
        ).join(Investigation, Investigation.id == InvestigationCertificateRecord.investigation_id)
    )
    wing_flap_rows = await db.execute(
        select(
            WingFlap.id,
            WingFlap.timestamp,
            WingFlap.flap_type,
            WingFlap.action,
            WingFlap.timeline_id,
            Timeline.name,
        ).join(Timeline, Timeline.id == WingFlap.timeline_id)
    )
    paradox_rows = await db.execute(select(Paradox.spawned_at, Paradox.resolved_at, Paradox.status))

    theatre_state_counts = Counter()
    theatre_created_at: list[datetime | None] = []
    completed_theatres = 0
    active_theatres = 0
    for state, created_at in theatre_rows.all():
        theatre_state_counts[state or "UNKNOWN"] += 1
        theatre_created_at.append(created_at)
        if state == "COMPLETED":
            completed_theatres += 1
        else:
            active_theatres += 1

    investigation_created_at: list[datetime | None] = []
    active_investigations = 0
    ready_investigations = 0
    for status, created_at, stop_condition_status in investigation_rows.all():
        investigation_created_at.append(created_at)
        if status != "COMPLETED":
            active_investigations += 1
        if stop_condition_status == "READY":
            ready_investigations += 1

    certificate_issued_at = [
        issued_at
        for (issued_at,) in theatre_certificate_rows.all()
        if issued_at is not None
    ]
    certificate_issued_at.extend(
        issued_at
        for (issued_at,) in investigation_certificate_rows.all()
        if issued_at is not None
    )

    deployment_created_at = [deployed_at for (deployed_at,) in deployment_rows.all()]
    paradox_windows = [(spawned_at, resolved_at) for spawned_at, resolved_at, _status in paradox_rows.all()]
    active_paradoxes = sum(
        1
        for spawned_at, resolved_at in paradox_windows
        if _as_utc(spawned_at) is not None and _as_utc(resolved_at) is None
    )

    signals = registry.active_signals
    critical_signals = sum(1 for signal in signals if signal.severity in {"CRITICAL", "HIGH"})

    from backend.api.convergence_routes import get_heatmap

    heatmap = await get_heatmap()

    comparisons = {
        "theatres_created": _build_comparison(
            _count_in_window(theatre_created_at, current_start, current_end),
            _count_in_window(theatre_created_at, previous_start, previous_end),
        ),
        "investigations_created": _build_comparison(
            _count_in_window(investigation_created_at, current_start, current_end),
            _count_in_window(investigation_created_at, previous_start, previous_end),
        ),
        "certificates_issued": _build_comparison(
            _count_in_window(certificate_issued_at, current_start, current_end),
            _count_in_window(certificate_issued_at, previous_start, previous_end),
        ),
        "deployments_created": _build_comparison(
            _count_in_window(deployment_created_at, current_start, current_end),
            _count_in_window(deployment_created_at, previous_start, previous_end),
        ),
    }

    def _theatre_matches(inquiry_class: str | None, family: str | None) -> bool:
        if theatre_inquiry_class and inquiry_class != theatre_inquiry_class:
            return False
        if theatre_family and family != theatre_family:
            return False
        return True

    def _investigation_matches(inquiry_class: str | None) -> bool:
        if investigation_class and inquiry_class != investigation_class:
            return False
        return True

    def _agent_matches(archetype) -> bool:
        archetype_value = archetype.value if hasattr(archetype, "value") else str(archetype)
        if agent_archetype and archetype_value != agent_archetype.upper():
            return False
        return True

    explanations = {
        "theatres_created": [
            AnalyticsExplanationItem(
                id=theatre_id,
                kind="theatre",
                timestamp=created_at,
                title=construct_id or theatre_id,
                summary=f"{(inquiry_class or 'UNKNOWN').replace('_', ' ').title()} theatre created.",
                tone="info",
                provenance="persisted_lifecycle",
                theatre_id=theatre_id,
            )
            for theatre_id, construct_id, inquiry_class, created_at, template_family in _recent_items_in_window(
                theatre_explanation_rows.all(),
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _theatre_matches(inquiry_class, template_family)
        ],
        "investigations_created": [
            AnalyticsExplanationItem(
                id=investigation_id,
                kind="investigation",
                timestamp=created_at,
                title=construct_id or investigation_id,
                summary=f"{(inquiry_class or 'UNKNOWN').replace('_', ' ').title()} investigation opened.",
                tone="info",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
            )
            for investigation_id, construct_id, inquiry_class, created_at in _recent_items_in_window(
                investigation_explanation_rows.all(),
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
        "certificates_issued": [
            *[
                AnalyticsExplanationItem(
                    id=certificate_id,
                    kind="theatre_certificate",
                    timestamp=issued_at,
                    title=construct_id or certificate_id,
                    summary="Theatre certificate issued from resolved theatre lifecycle.",
                    tone="success",
                    provenance="persisted_lifecycle",
                    theatre_id=theatre_id,
                    certificate_id=certificate_id,
                )
                for certificate_id, theatre_id, construct_id, issued_at in _recent_items_in_window(
                    theatre_certificate_explanation_rows.all(),
                    lambda row: row[3],
                    explanation_start,
                    explanation_end,
                    limit=3,
                )
            ],
            *[
                AnalyticsExplanationItem(
                    id=certificate_id,
                    kind="investigation_certificate",
                    timestamp=issued_at,
                    title=certificate_id,
                    summary=f"Investigation certificate issued with routing {routing_decision or 'UNKNOWN'}.",
                    tone="success",
                    provenance="persisted_lifecycle",
                    investigation_id=investigation_id,
                    certificate_id=certificate_id,
                )
                for certificate_id, investigation_id, routing_decision, issued_at in _recent_items_in_window(
                    investigation_certificate_explanation_rows.all(),
                    lambda row: row[3],
                    explanation_start,
                    explanation_end,
                    limit=3,
                )
            ],
        ][:5],
        "deployments_created": [
            AnalyticsExplanationItem(
                id=deployment_id,
                kind="deployment",
                timestamp=deployed_at,
                title=agent_name or deployment_id,
                summary=f"Agent deployed into {construct_id or theatre_id}.",
                tone="warning",
                provenance="persisted_lifecycle",
                theatre_id=theatre_id,
            )
            for deployment_id, theatre_id, deployed_at, agent_name, construct_id, archetype in _recent_items_in_window(
                deployment_explanation_rows.all(),
                lambda row: row[2],
                explanation_start,
                explanation_end,
            )
            if _agent_matches(archetype)
        ],
        "deployment_lifecycle": [
            AnalyticsExplanationItem(
                id=audit_id,
                kind="deployment_audit",
                timestamp=created_at,
                title=agent_name or audit_id,
                summary=f"{event_type.replace('_', ' ').title()} on {construct_id or theatre_id}.",
                tone="warning",
                provenance="persisted_lifecycle",
                theatre_id=theatre_id,
            )
            for audit_id, event_type, created_at, theatre_id, construct_id, agent_name, archetype in _recent_items_in_window(
                [
                    row for row in deployment_audit_rows.all()
                    if row[1] in {"PAUSED", "RESUMED", "WITHDRAWN"}
                ],
                lambda row: row[2],
                explanation_start,
                explanation_end,
            )
            if _agent_matches(archetype)
        ],
        "certificate_ready": [
            AnalyticsExplanationItem(
                id=certificate_id,
                kind="certificate_ready",
                timestamp=ready_at,
                title=certificate_id,
                summary=f"Certificate ready with routing {routing_decision or 'UNKNOWN'}.",
                tone="info" if routing_decision == "ALLOWED" else "warning",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
                certificate_id=certificate_id,
            )
            for certificate_id, investigation_id, routing_decision, ready_at, inquiry_class in _recent_items_in_window(
                [row for row in certificate_ready_rows.all() if row[3] is not None],
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
        "wing_flaps": [
            AnalyticsExplanationItem(
                id=flap_id,
                kind="wing_flap",
                timestamp=flap_timestamp,
                title=timeline_name or flap_id,
                summary=(action or flap_type.value if hasattr(flap_type, "value") else str(flap_type))[:180],
                tone="warning",
                provenance="persisted_operational_context",
                timeline_id=timeline_id,
            )
            for flap_id, flap_timestamp, flap_type, action, timeline_id, timeline_name in _recent_items_in_window(
                wing_flap_rows.all(),
                lambda row: row[1],
                explanation_start,
                explanation_end,
            )
        ],
    }

    return PlatformAnalyticsResponse(
        updated_at=_utc_now(),
        range=range_key,
        bucket_size="day",
        current=PlatformAnalyticsCurrent(
            active_theatres=active_theatres,
            completed_theatres=completed_theatres,
            active_investigations=active_investigations,
            ready_investigations=ready_investigations,
            issued_certificates=len(certificate_issued_at),
            active_paradoxes=active_paradoxes,
            active_signals=len(signals),
            critical_signals=critical_signals,
            convergence_cells=len(heatmap.cells),
        ),
        timeseries={
            "theatres_created": _count_by_day(theatre_created_at, buckets),
            "investigations_created": _count_by_day(investigation_created_at, buckets),
            "certificates_issued": _count_by_day(certificate_issued_at, buckets),
            "deployments_created": _count_by_day(deployment_created_at, buckets),
            "active_paradoxes": _active_paradox_series(paradox_windows, buckets),
        },
        comparisons=comparisons,
        explanations=explanations,
    )


@router.get("/breakdowns", response_model=AnalyticsBreakdownsResponse)
async def get_analytics_breakdowns(
    signal_category: str | None = Query(None),
    signal_source: str | None = Query(None),
    theatre_inquiry_class: str | None = Query(None),
    theatre_family: str | None = Query(None),
    investigation_class: str | None = Query(None),
    agent_archetype: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsBreakdownsResponse:
    registry = get_osint_registry()

    theatre_query = (
        select(Theatre.state, Theatre.inquiry_class, TheatreTemplate.template_family)
        .join(TheatreTemplate, Theatre.template_id == TheatreTemplate.id)
    )
    if theatre_inquiry_class:
        theatre_query = theatre_query.where(Theatre.inquiry_class == theatre_inquiry_class)
    if theatre_family:
        theatre_query = theatre_query.where(TheatreTemplate.template_family == theatre_family)
    theatre_rows = await db.execute(theatre_query)

    investigation_query = select(Investigation.status, Investigation.inquiry_class, Investigation.id)
    if investigation_class:
        investigation_query = investigation_query.where(Investigation.inquiry_class == investigation_class)
    investigation_rows = await db.execute(investigation_query)
    filtered_investigations = investigation_rows.all()
    filtered_investigation_ids = [investigation_id for _status, _inquiry_class, investigation_id in filtered_investigations]

    investigation_certificate_query = select(InvestigationCertificateRecord.routing_decision)
    if investigation_class:
        investigation_certificate_query = investigation_certificate_query.where(
            InvestigationCertificateRecord.investigation_id.in_(filtered_investigation_ids or ["__none__"])
        )
    investigation_certificate_rows = await db.execute(
        investigation_certificate_query
    )

    theatre_certificate_query = (
        select(TheatreCertificate.routing_hint, TheatreCertificate.coherence_gate_status)
        .join(Theatre, TheatreCertificate.theatre_id == Theatre.id)
        .join(TheatreTemplate, Theatre.template_id == TheatreTemplate.id)
    )
    if theatre_inquiry_class:
        theatre_certificate_query = theatre_certificate_query.where(
            Theatre.inquiry_class == theatre_inquiry_class
        )
    if theatre_family:
        theatre_certificate_query = theatre_certificate_query.where(
            TheatreTemplate.template_family == theatre_family
        )
    theatre_certificate_rows = await db.execute(theatre_certificate_query)

    agent_query = select(Agent.archetype)
    if agent_archetype:
        agent_query = agent_query.where(Agent.archetype == agent_archetype.upper())
    agent_rows = await db.execute(agent_query)

    theatre_states = Counter()
    theatre_families = Counter()
    theatre_classes = Counter()
    for state, inquiry_class, template_family in theatre_rows.all():
        theatre_states[state or "UNKNOWN"] += 1
        theatre_families[template_family or "UNKNOWN"] += 1
        theatre_classes[inquiry_class or "UNKNOWN"] += 1

    investigation_statuses = Counter()
    investigation_classes = Counter()
    for status, inquiry_class, _investigation_id in filtered_investigations:
        investigation_statuses[status or "UNKNOWN"] += 1
        investigation_classes[inquiry_class or "UNKNOWN"] += 1

    investigation_routing = Counter(
        routing_decision or "UNKNOWN"
        for (routing_decision,) in investigation_certificate_rows.all()
    )

    theatre_routing = Counter()
    theatre_gate_statuses = Counter()
    for routing_hint, gate_status in theatre_certificate_rows.all():
        theatre_routing[routing_hint or "UNKNOWN"] += 1
        theatre_gate_statuses[gate_status or "UNKNOWN"] += 1

    agent_archetypes = Counter(archetype.value if hasattr(archetype, "value") else str(archetype) for (archetype,) in agent_rows.all())

    categorized = registry.get_signals_by_category()
    filtered_signals = list(registry.active_signals)
    if signal_category:
        filtered_signals = list(categorized.get(signal_category, []))
    if signal_source:
        filtered_signals = [
            signal
            for signal in filtered_signals
            if (
                signal.source.value if hasattr(signal.source, "value") else str(signal.source)
            ) == signal_source
        ]

    filtered_categorized = Counter()
    for category, signals in categorized.items():
        filtered_categorized[category] = len(
            [
                signal for signal in signals
                if signal in filtered_signals
            ]
        )

    signal_categories = Counter(filtered_categorized)
    signal_sources = Counter(
        signal.source.value if hasattr(signal.source, "value") else str(signal.source)
        for signal in filtered_signals
    )
    signal_severities = Counter(signal.severity.lower() for signal in filtered_signals)

    return AnalyticsBreakdownsResponse(
        updated_at=_utc_now(),
        applied_filters=_clean_filter_map(
            signal_category=signal_category,
            signal_source=signal_source,
            theatre_inquiry_class=theatre_inquiry_class,
            theatre_family=theatre_family,
            investigation_class=investigation_class,
            agent_archetype=agent_archetype,
        ),
        signal_categories=_counter_to_dict(signal_categories),
        signal_sources=_counter_to_dict(signal_sources),
        signal_severities=_counter_to_dict(signal_severities),
        theatre_states=_counter_to_dict(theatre_states),
        theatre_families=_counter_to_dict(theatre_families),
        theatre_inquiry_classes=_counter_to_dict(theatre_classes),
        investigation_statuses=_counter_to_dict(investigation_statuses),
        investigation_classes=_counter_to_dict(investigation_classes),
        investigation_routing_decisions=_counter_to_dict(investigation_routing),
        theatre_routing_hints=_counter_to_dict(theatre_routing),
        theatre_gate_statuses=_counter_to_dict(theatre_gate_statuses),
        agent_archetypes=_counter_to_dict(agent_archetypes),
    )


@router.get("/risk-trend", response_model=RiskTrendResponse)
async def get_risk_trend(
    range_key: str = Query("30d", alias="range"),
    bucket_date: str | None = Query(None),
    investigation_class: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> RiskTrendResponse:
    _start_bucket, buckets = _parse_range(range_key)
    current_start, current_end, previous_start, previous_end = _comparison_windows(range_key)
    explanation_bucket = _parse_bucket_date(bucket_date)
    explanation_start = explanation_bucket or current_start
    explanation_end = (explanation_bucket + timedelta(days=1)) if explanation_bucket else current_end

    paradox_rows = await db.execute(select(Paradox.spawned_at, Paradox.resolved_at))
    paradox_explanation_rows = await db.execute(
        select(
            Paradox.id,
            Paradox.timeline_id,
            Timeline.name,
            Paradox.severity_class,
            Paradox.spawned_at,
            Paradox.detonation_time,
            Paradox.resolved_at,
        ).join(Timeline, Timeline.id == Paradox.timeline_id)
    )
    drift_rows = await db.execute(
        select(InvestigationDriftEvent.detected_at).where(
            InvestigationDriftEvent.impact_assessment == "material"
        )
    )
    drift_explanation_rows = await db.execute(
        select(
            InvestigationDriftEvent.id,
            InvestigationDriftEvent.investigation_id,
            InvestigationDriftEvent.drift_type,
            InvestigationDriftEvent.detected_at,
            Investigation.inquiry_class,
        )
        .join(Investigation, Investigation.id == InvestigationDriftEvent.investigation_id)
        .where(InvestigationDriftEvent.impact_assessment == "material")
    )
    readiness_rows = await db.execute(
        select(Investigation.stop_condition_evaluated_at).where(
            Investigation.stop_condition_status == "READY"
        )
    )
    readiness_explanation_rows = await db.execute(
        select(
            Investigation.id,
            Investigation.construct_id,
            Investigation.stop_condition_reason,
            Investigation.stop_condition_evaluated_at,
            Investigation.inquiry_class,
        ).where(Investigation.stop_condition_status == "READY")
    )
    review_required_rows = await db.execute(
        select(InvestigationCertificateRecord.ready_at).where(
            InvestigationCertificateRecord.routing_decision == "REVIEW_REQUIRED"
        )
    )
    review_required_explanation_rows = await db.execute(
        select(
            InvestigationCertificateRecord.id,
            InvestigationCertificateRecord.investigation_id,
            InvestigationCertificateRecord.routing_reason,
            InvestigationCertificateRecord.ready_at,
            Investigation.inquiry_class,
            InvestigationCertificateRecord.routing_decision,
        )
        .join(Investigation, Investigation.id == InvestigationCertificateRecord.investigation_id)
        .where(InvestigationCertificateRecord.routing_decision == "REVIEW_REQUIRED")
    )

    paradox_windows = paradox_rows.all()
    active_paradox_points = _active_paradox_series(paradox_windows, buckets)
    previous_bucket_days = SUPPORTED_RANGES[range_key]
    previous_buckets = [
        previous_start + timedelta(days=index)
        for index in range(previous_bucket_days)
    ]
    previous_active_paradox_points = _active_paradox_series(paradox_windows, previous_buckets)

    material_drift_values = [detected_at for (detected_at,) in drift_rows.all()]
    readiness_values = [evaluated_at for (evaluated_at,) in readiness_rows.all()]
    review_required_values = [ready_at for (ready_at,) in review_required_rows.all()]

    def _investigation_matches(inquiry_class: str | None) -> bool:
        if investigation_class and inquiry_class != investigation_class:
            return False
        return True

    explanations = {
        "active_paradoxes": [
            AnalyticsExplanationItem(
                id=paradox_id,
                kind="paradox",
                timestamp=spawned_at,
                title=timeline_name or paradox_id,
                summary=f"{severity_class.value if hasattr(severity_class, 'value') else severity_class} paradox active; detonation at {detonation_time.isoformat() if detonation_time else 'unknown'}.",
                tone="danger",
                provenance="persisted_operational_context",
                timeline_id=timeline_id,
            )
            for paradox_id, timeline_id, timeline_name, severity_class, spawned_at, detonation_time, resolved_at in sorted(
                [
                    row
                    for row in paradox_explanation_rows.all()
                    if _as_utc(row[4]) is not None and _as_utc(row[6]) is None and explanation_start <= _as_utc(row[4]) < explanation_end
                ],
                key=lambda row: _as_utc(row[5]) or _as_utc(row[4]),
            )[:5]
        ],
        "material_drift_events": [
            AnalyticsExplanationItem(
                id=drift_id,
                kind="drift",
                timestamp=detected_at,
                title=investigation_id,
                summary=f"{drift_type.replace('_', ' ').title()} flagged as material drift.",
                tone="warning",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
            )
            for drift_id, investigation_id, drift_type, detected_at, inquiry_class in _recent_items_in_window(
                drift_explanation_rows.all(),
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
        "readiness_met": [
            AnalyticsExplanationItem(
                id=investigation_id,
                kind="investigation_ready",
                timestamp=evaluated_at,
                title=construct_id or investigation_id,
                summary=(reason or "Stop condition met.").replace("_", " "),
                tone="info",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
            )
            for investigation_id, construct_id, reason, evaluated_at, inquiry_class in _recent_items_in_window(
                readiness_explanation_rows.all(),
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
        "review_required_certificates": [
            AnalyticsExplanationItem(
                id=certificate_id,
                kind="review_required_certificate",
                timestamp=ready_at,
                title=certificate_id,
                summary=f"Certificate queued with routing reason {routing_reason or 'unspecified'}.",
                tone="warning",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
                certificate_id=certificate_id,
            )
            for certificate_id, investigation_id, routing_reason, ready_at, inquiry_class, _routing_decision in _recent_items_in_window(
                review_required_explanation_rows.all(),
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
        "routing_transitions": [
            AnalyticsExplanationItem(
                id=certificate_id,
                kind="routing_transition",
                timestamp=ready_at,
                title=certificate_id,
                summary=f"Routing decision resolved to {routing_decision or 'UNKNOWN'}.",
                tone="info" if routing_decision == "ALLOWED" else "warning",
                provenance="persisted_lifecycle",
                investigation_id=investigation_id,
                certificate_id=certificate_id,
            )
            for certificate_id, investigation_id, routing_decision, ready_at, inquiry_class in _recent_items_in_window(
                [row for row in certificate_ready_rows.all() if row[3] is not None],
                lambda row: row[3],
                explanation_start,
                explanation_end,
            )
            if _investigation_matches(inquiry_class)
        ],
    }

    return RiskTrendResponse(
        updated_at=_utc_now(),
        range=range_key,
        bucket_size="day",
        timeseries={
            "active_paradoxes": active_paradox_points,
            "material_drift_events": _count_by_day(
                material_drift_values,
                buckets,
            ),
            "readiness_met": _count_by_day(
                readiness_values,
                buckets,
            ),
            "review_required_certificates": _count_by_day(
                review_required_values,
                buckets,
            ),
        },
        comparisons={
            "active_paradoxes": _build_comparison(
                _average_value(active_paradox_points),
                _average_value(previous_active_paradox_points),
            ),
            "material_drift_events": _build_comparison(
                _count_in_window(material_drift_values, current_start, current_end),
                _count_in_window(material_drift_values, previous_start, previous_end),
            ),
            "readiness_met": _build_comparison(
                _count_in_window(readiness_values, current_start, current_end),
                _count_in_window(readiness_values, previous_start, previous_end),
            ),
            "review_required_certificates": _build_comparison(
                _count_in_window(review_required_values, current_start, current_end),
                _count_in_window(review_required_values, previous_start, previous_end),
            ),
        },
        explanations=explanations,
    )


@router.get("/portfolio", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    range_key: str = Query("30d", alias="range"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> PortfolioAnalyticsResponse:
    if range_key not in SUPPORTED_RANGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported range '{range_key}'. Use one of: {', '.join(SUPPORTED_RANGES)}",
        )

    result = await db.execute(
        select(
            UserPosition.timeline_id,
            UserPosition.side,
            UserPosition.shards_held,
            UserPosition.average_entry_price,
            Timeline.name,
            Timeline.price_yes,
            Timeline.price_no,
            Timeline.has_active_paradox,
            Timeline.logic_gap,
        ).join(Timeline, Timeline.id == UserPosition.timeline_id)
        .where(UserPosition.user_id == user.user_id)
    )

    top_positions: list[PortfolioPositionSummary] = []
    total_notional = 0.0
    total_unrealised_pnl = 0.0
    winning_positions = 0
    losing_positions = 0
    at_risk_positions = 0

    for timeline_id, side, shards_held, average_entry_price, timeline_name, price_yes, price_no, has_active_paradox, logic_gap in result.all():
        current_price = price_yes if side == "YES" else price_no
        notional = float(shards_held) * float(current_price or 0.0)
        unrealised_pnl = float(shards_held) * (float(current_price or 0.0) - float(average_entry_price or 0.0))
        total_notional += notional
        total_unrealised_pnl += unrealised_pnl
        if unrealised_pnl > 0:
            winning_positions += 1
        elif unrealised_pnl < 0:
            losing_positions += 1
        if bool(has_active_paradox) or float(logic_gap or 0.0) >= 0.4:
            at_risk_positions += 1

        top_positions.append(
            PortfolioPositionSummary(
                timeline_id=timeline_id,
                timeline_name=timeline_name,
                side=side,
                current_price=float(current_price or 0.0),
                average_entry_price=float(average_entry_price or 0.0),
                shards_held=int(shards_held or 0),
                notional=notional,
                unrealised_pnl=unrealised_pnl,
                has_active_paradox=bool(has_active_paradox),
                logic_gap=float(logic_gap or 0.0),
            )
        )

    top_positions.sort(key=lambda position: abs(position.unrealised_pnl), reverse=True)

    return PortfolioAnalyticsResponse(
        updated_at=_utc_now(),
        range=range_key,
        history_status="current_snapshot_only",
        current=PortfolioAnalyticsCurrent(
            total_notional=round(total_notional, 2),
            total_unrealised_pnl=round(total_unrealised_pnl, 2),
            position_count=len(top_positions),
            winning_positions=winning_positions,
            losing_positions=losing_positions,
            at_risk_positions=at_risk_positions,
        ),
        top_positions=top_positions[:8],
        timeseries=[],
    )
