"""Signal Scanner — domain-filtered OSINT scanning with DeltaBrief output."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from backend.utils.canonical_json import canonical_json


class DomainFilter(str, Enum):
    """Domain filters for OSINT source group selection."""

    CORPORATE_AND_ENTITY = "corporate_and_entity"
    FINANCE_AND_MARKETS = "finance_and_markets"
    MARITIME = "maritime"
    AIRSPACE = "airspace"
    GEOPOLITICAL_AND_CONFLICT = "geopolitical_and_conflict"
    CYBER_THREAT = "cyber_threat"
    PROPERTY_AND_LAND = "property_and_land"
    COURT_AND_LEGAL = "court_and_legal"
    SATELLITE_AND_EARTH_OBSERVATION = "satellite_and_earth_observation"


# Maps domain filters to OSINT registry source groups
DOMAIN_FILTER_SOURCE_GROUPS: dict[DomainFilter, list[str]] = {
    DomainFilter.CORPORATE_AND_ENTITY: [
        "official_gov",
        "corporate_filing",
        "entity_resolution",
    ],
    DomainFilter.FINANCE_AND_MARKETS: [
        "market_data",
        "central_bank",
        "prediction_market",
    ],
    DomainFilter.MARITIME: ["maritime_ais", "geospatial_verification"],
    DomainFilter.AIRSPACE: ["flight_tracking"],
    DomainFilter.GEOPOLITICAL_AND_CONFLICT: [
        "conflict_event",
        "humanitarian_data",
        "disaster_alert",
    ],
    DomainFilter.CYBER_THREAT: ["cyber_threat"],
    DomainFilter.PROPERTY_AND_LAND: ["property_registry"],
    DomainFilter.COURT_AND_LEGAL: ["court_filing", "insolvency"],
    DomainFilter.SATELLITE_AND_EARTH_OBSERVATION: [
        "satellite_imagery",
        "seismology",
    ],
}

# Source groups requiring tier B/C access (not available by default)
_TIER_B_SOURCES = {"satellite_imagery", "flight_tracking"}
_TIER_C_SOURCES = {"cyber_threat"}


class SourceQuery(BaseModel):
    """Record of a single source query within a scan."""

    model_config = {"frozen": True}

    source_id: str
    source_group: str
    query: str
    result_count: int
    access_tier: str  # "A", "B", "C"
    skipped: bool = False
    skip_reason: str | None = None


class Anomaly(BaseModel):
    """Anomaly detected during a scan."""

    model_config = {"frozen": True}

    anomaly_id: str
    source_id: str
    description: str
    severity: float = Field(ge=0.0, le=1.0)
    detected_at: datetime


class DeltaBrief(BaseModel):
    """Immutable scan output with content hash."""

    model_config = {"frozen": True}

    brief_id: str
    domain_filters: list[DomainFilter]
    generated_at: datetime
    source_queries: list[SourceQuery]
    anomalies: list[Anomaly]
    content_hash: str  # SHA-256 of canonical JSON


class SignalScanner:
    """Domain-filtered OSINT signal scanner.

    Access-tier policy: only tier A sources are queried by default.
    Tier B/C sources are recorded as skipped with reason.
    """

    def __init__(self, domain_filters: list[DomainFilter]) -> None:
        self._domain_filters = domain_filters
        self._scan_counter: int = 0

    def scan(self, subject: str) -> DeltaBrief:
        """Mock scan. Returns stub DeltaBrief with source queries."""
        self._scan_counter += 1
        brief_id = f"DB{self._scan_counter:03d}"

        queries: list[SourceQuery] = []
        query_counter = 0

        for group in self.active_source_groups:
            query_counter += 1
            source_id = f"SRC{query_counter:03d}"

            if group in _TIER_B_SOURCES:
                queries.append(
                    SourceQuery(
                        source_id=source_id,
                        source_group=group,
                        query=subject,
                        result_count=0,
                        access_tier="B",
                        skipped=True,
                        skip_reason="access_tier_b_not_authorized",
                    )
                )
            elif group in _TIER_C_SOURCES:
                queries.append(
                    SourceQuery(
                        source_id=source_id,
                        source_group=group,
                        query=subject,
                        result_count=0,
                        access_tier="C",
                        skipped=True,
                        skip_reason="access_tier_c_not_authorized",
                    )
                )
            else:
                queries.append(
                    SourceQuery(
                        source_id=source_id,
                        source_group=group,
                        query=subject,
                        result_count=0,
                        access_tier="A",
                    )
                )

        # Compute content hash from canonical JSON of the brief data
        brief_data = {
            "brief_id": brief_id,
            "domain_filters": [f.value for f in self._domain_filters],
            "subject": subject,
            "source_queries": [q.model_dump(mode="json") for q in queries],
            "anomalies": [],
        }
        content_hash = hashlib.sha256(
            canonical_json(brief_data).encode()
        ).hexdigest()

        now = datetime.utcnow()

        return DeltaBrief(
            brief_id=brief_id,
            domain_filters=self._domain_filters,
            generated_at=now,
            source_queries=queries,
            anomalies=[],
            content_hash=content_hash,
        )

    @property
    def active_source_groups(self) -> list[str]:
        """Flatten domain filters to deduplicated source groups."""
        seen: set[str] = set()
        result: list[str] = []
        for df in self._domain_filters:
            for group in DOMAIN_FILTER_SOURCE_GROUPS.get(df, []):
                if group not in seen:
                    seen.add(group)
                    result.append(group)
        return result

    def _build_manifest(self, queries: list[SourceQuery]) -> dict:
        """Scanner manifest with requested/resolved/skipped groups and access_tier_policy."""
        requested = [f.value for f in self._domain_filters]
        resolved = list(
            {q.source_group for q in queries if not q.skipped}
        )
        skipped = [
            {
                "source_group": q.source_group,
                "reason": q.skip_reason,
                "access_tier": q.access_tier,
            }
            for q in queries
            if q.skipped
        ]

        return {
            "requested_domain_filters": requested,
            "resolved_source_groups": sorted(resolved),
            "skipped_source_groups": skipped,
            "access_tier_policy": "tier_a_only",
            "total_queries": len(queries),
            "total_skipped": len(skipped),
        }
