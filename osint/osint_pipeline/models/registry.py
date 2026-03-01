"""
OSINT Source Registry loader and query interface.

Reads the Echelon OSINT Source Registry (v1.0.0, 78+ sources) and
provides typed access to source metadata for the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RegistrySource(BaseModel):
    """Single source entry from the OSINT Source Registry."""

    source_id: str
    source_group: str
    resolution_role: str
    priority_bucket: str
    settlement_eligible: bool
    jurisdiction: str
    auth_methods: list[str] = Field(default_factory=list)
    api_url: str | None = None
    ui_url: str | None = None
    repo_url: str | None = None
    independence_upstream_id: str = ""
    access_surface: str = "public_api"
    access_surface_confirmed: bool = False
    access_proof: dict[str, Any] = Field(default_factory=dict)
    revision_policy: str = "latest_only"
    receipt_mode_minimum: str = "http_transcript"
    counter_signal_class: str | None = None
    world_monitor_domain: str | None = None
    world_monitor_upstream_domain: str | None = None

    # --- v1.0.0 fields ---
    consumption_surfaces: list[dict[str, Any]] = Field(default_factory=list)
    access_tier: str = "tier_a"
    api_endpoint: str | None = None
    collector_status: str = "planned"
    rate_limit_policy: str | None = None
    dashboard_permitted: bool = True
    settlement_latest_only_override: bool = False
    settlement_requires_corroboration: bool = False
    independence_notes: str | None = None


class RegistryLoader:
    """
    Load and query the OSINT Source Registry.

    Usage:
        registry = RegistryLoader.from_file("path/to/registry.json")
        source = registry.get("companies_house_api")
        settlement_sources = registry.settlement_eligible()
        gb_sources = registry.by_jurisdiction("GB")
    """

    def __init__(self, sources: list[RegistrySource], metadata: dict[str, Any]):
        self._sources: dict[str, RegistrySource] = {s.source_id: s for s in sources}
        self.metadata = metadata

    @classmethod
    def from_file(cls, path: str | Path) -> RegistryLoader:
        """Load registry from JSON file."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = []
        for entry in data.get("sources", []):
            sources.append(RegistrySource(**entry))

        metadata = {
            "version": data.get("version", "unknown"),
            "total_sources": data.get("summary", {}).get("total_sources", len(sources)),
            "registry_hash": data.get("registry_hash", ""),
        }
        return cls(sources=sources, metadata=metadata)

    def get(self, source_id: str) -> RegistrySource | None:
        """Get a source by ID."""
        return self._sources.get(source_id)

    def exists(self, source_id: str) -> bool:
        """Check if a source exists in the registry."""
        return source_id in self._sources

    def all_sources(self) -> list[RegistrySource]:
        """Return all sources."""
        return list(self._sources.values())

    def settlement_eligible(self) -> list[RegistrySource]:
        """Return only settlement-eligible sources."""
        return [s for s in self._sources.values() if s.settlement_eligible]

    def by_jurisdiction(self, jurisdiction: str) -> list[RegistrySource]:
        """Return sources for a given jurisdiction."""
        return [s for s in self._sources.values() if s.jurisdiction == jurisdiction]

    def by_source_group(self, group: str) -> list[RegistrySource]:
        """Return sources in a given independence group."""
        return [s for s in self._sources.values() if s.source_group == group]

    def by_resolution_role(self, role: str) -> list[RegistrySource]:
        """Return sources with a given resolution role."""
        return [s for s in self._sources.values() if s.resolution_role == role]

    def counter_signal_sources(self) -> list[RegistrySource]:
        """Return all counter-signal sources."""
        return [s for s in self._sources.values() if s.resolution_role == "counter_signal"]

    def free_public_sources(self) -> list[RegistrySource]:
        """Return sources accessible via free public API (no payment)."""
        return [
            s for s in self._sources.values()
            if s.access_surface in ("public_api",)
            and "none" in s.auth_methods or "api_key" in s.auth_methods or "user_agent_header" in s.auth_methods
        ]

    def upstream_groups(self) -> dict[str, list[str]]:
        """
        Map independence_upstream_id to source_ids.

        Used by the corroboration engine to deduplicate sources
        sharing the same system of record.
        """
        groups: dict[str, list[str]] = {}
        for s in self._sources.values():
            uid = s.independence_upstream_id
            if uid:
                groups.setdefault(uid, []).append(s.source_id)
        return groups

    # --- v1.0.0 query methods ---

    def by_access_tier(self, tier: str) -> list[RegistrySource]:
        """Return sources in a given access tier (tier_a, tier_b, tier_c)."""
        return [s for s in self._sources.values() if s.access_tier == tier]

    def by_collector_status(self, status: str) -> list[RegistrySource]:
        """Return sources with a given collector status (active, planned, enumerated, deprecated)."""
        return [s for s in self._sources.values() if s.collector_status == status]

    def by_consumption_surface(self, surface: str) -> list[RegistrySource]:
        """Return sources that include a given consumption surface."""
        return [
            s for s in self._sources.values()
            if any(cs.get("surface") == surface for cs in s.consumption_surfaces)
        ]

    def active_sources(self) -> list[RegistrySource]:
        """Return sources with collector_status == 'active'."""
        return [s for s in self._sources.values() if s.collector_status == "active"]

    def settlement_sources_requiring_corroboration(self) -> list[RegistrySource]:
        """Return settlement-eligible sources that require corroboration."""
        return [
            s for s in self._sources.values()
            if s.settlement_eligible and s.settlement_requires_corroboration
        ]

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")

    @property
    def total_sources(self) -> int:
        return len(self._sources)

    def __len__(self) -> int:
        return len(self._sources)

    def __contains__(self, source_id: str) -> bool:
        return source_id in self._sources
