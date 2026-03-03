"""OSINT Source Registry — loader, query, and validation.

Loads the OSINT source registry JSON (v0.3.2+) and provides typed
access to source metadata. Used by the collection runner to derive
collection plans and by the corroboration engine for independence checks.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


# Controlled enums from the registry specification
_VALID_SOURCE_GROUPS = frozenset([
    "official_gov",
    "wire_service",
    "national_media",
    "local_media",
    "social_platform",
    "satellite_imagery",
    "maritime_ais",
    "aviation_adsb",
    "market_data",
    "prediction_market",
    "academic_research",
    "alt_data_behavioural",
    "cyber_threat_intel",
    "court_record",
    "financial_regulator",
    "government_registry",
    "judicial_record",
    "calendar_counter_signal",
    "intellectual_property",
    "entity_resolution",
    "geospatial_verification",
    "geophysical_hazard",
    "fire_emissions",
    "space_weather",
    "infrastructure_critical",
    "sanctions_compliance",
    "health_biosecurity",
    "election_governance",
    "energy_commodities",
    "climate_weather",
    "demographic_economic",
    "nuclear_wmd",
    "protest_unrest",
])

_VALID_RESOLUTION_ROLES = frozenset([
    "primary_evidence",
    "secondary_corroboration",
    "counter_signal",
    "triage_only",
])

_VALID_RECEIPT_MODES = frozenset([
    "http_transcript",
    "witness_quorum",
    "signed_receipt",
])

_VALID_PRIORITY_BUCKETS = frozenset([
    "settlement_grade",
    "scoring_grade",
    "triage_only",
    "avoid",
])


@dataclass
class RegistrySource:
    """Single source entry from the OSINT source registry."""

    source_id: str
    display_name: str
    source_group: str                           # Controlled enum
    resolution_role: str                        # "primary_evidence" | "secondary_corroboration" etc.
    independence_upstream_id: str               # Dedup key for corroboration
    receipt_mode_minimum: str                   # "http_transcript" | "witness_quorum" | "signed_receipt"
    world_monitor_domain: str | None = None    # WMDomain value if WM source
    priority_bucket: str = "scoring_grade"      # Priority bucket string
    settlement_eligible: bool = False
    jurisdiction: str | None = None


class RegistryLoader:
    """Loads and queries the OSINT source registry JSON.

    Stateless after init — loads from disk on construction.
    """

    def __init__(self, registry_path: str) -> None:
        self._path = registry_path
        self._sources: dict[str, RegistrySource] = {}
        self._load()

    def _load(self) -> None:
        """Parse registry JSON into RegistrySource instances."""
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources_list = data.get("sources", [])
        for entry in sources_list:
            source = RegistrySource(
                source_id=entry.get("source_id", ""),
                display_name=entry.get("source_name", entry.get("display_name", "")),
                source_group=entry.get("source_group", ""),
                resolution_role=entry.get("resolution_role", ""),
                independence_upstream_id=entry.get("independence_upstream_id", ""),
                receipt_mode_minimum=entry.get("receipt_mode_minimum", ""),
                world_monitor_domain=entry.get("world_monitor_domain"),
                priority_bucket=entry.get("priority_bucket", "scoring_grade"),
                settlement_eligible=entry.get("settlement_eligible", False),
                jurisdiction=entry.get("jurisdiction"),
            )
            self._sources[source.source_id] = source

    @property
    def sources(self) -> dict[str, RegistrySource]:
        """All loaded sources keyed by source_id."""
        return dict(self._sources)

    def get_source(self, source_id: str) -> RegistrySource | None:
        """Lookup by source_id. Returns None if not found."""
        return self._sources.get(source_id)

    def get_sources_by_group(self, source_group: str) -> list[RegistrySource]:
        """Filter sources by source_group enum value."""
        return [s for s in self._sources.values() if s.source_group == source_group]

    def get_sources_by_domain(self, wm_domain: str) -> list[RegistrySource]:
        """Filter sources by world_monitor_domain."""
        return [s for s in self._sources.values() if s.world_monitor_domain == wm_domain]

    def get_settlement_eligible(self) -> list[RegistrySource]:
        """Return all settlement-eligible sources."""
        return [s for s in self._sources.values() if s.settlement_eligible]

    def validate(self) -> list[str]:
        """Structural validation — enum membership, invariant checks.

        Returns list of validation errors. Empty list = valid.

        Checks:
        - source_group is one of the controlled enum values
        - resolution_role is valid
        - receipt_mode_minimum is valid
        - priority_bucket is valid
        - settlement_eligible sources have receipt_mode_minimum in valid set
        - independence_upstream_id is non-empty
        """
        errors: list[str] = []
        for sid, source in self._sources.items():
            if source.source_group not in _VALID_SOURCE_GROUPS:
                errors.append(
                    f"{sid}: invalid source_group '{source.source_group}'"
                )
            if source.resolution_role not in _VALID_RESOLUTION_ROLES:
                errors.append(
                    f"{sid}: invalid resolution_role '{source.resolution_role}'"
                )
            if source.receipt_mode_minimum not in _VALID_RECEIPT_MODES:
                errors.append(
                    f"{sid}: invalid receipt_mode_minimum '{source.receipt_mode_minimum}'"
                )
            if source.priority_bucket not in _VALID_PRIORITY_BUCKETS:
                errors.append(
                    f"{sid}: invalid priority_bucket '{source.priority_bucket}'"
                )
            if not source.independence_upstream_id:
                errors.append(
                    f"{sid}: independence_upstream_id is empty"
                )
            # Settlement invariant: eligible sources must have valid receipt mode
            if source.settlement_eligible:
                if source.receipt_mode_minimum not in _VALID_RECEIPT_MODES:
                    errors.append(
                        f"{sid}: settlement_eligible=True but invalid receipt_mode_minimum"
                    )
        return errors
