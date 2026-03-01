"""OSINT Source Registry loader and query interface.

Reads the Echelon OSINT Source Registry (v0.4.0, 57 sources) and
provides typed access to source metadata for the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RegistrySource(BaseModel):
    """Single source entry from the OSINT Source Registry.

    All 26 fields from the registry JSON are represented (K-8 fix).
    """

    source_id: str
    source_name: str = ""
    source_group: str
    resolution_role: str
    priority_bucket: str
    settlement_eligible: bool
    jurisdiction: str
    auth_methods: list[str] = Field(default_factory=list)
    api_url: str | None = None
    ui_url: str | None = None
    independence_upstream_id: str = ""
    access_surface: str = "public_api"
    access_surface_confirmed: bool = False
    access_proof: dict[str, Any] = Field(default_factory=dict)
    revision_policy: str = "latest_only"
    receipt_mode_minimum: str = "http_transcript"
    counter_signal_class: str | None = None
    # K-2 fix: cost_model field was missing from skeleton
    cost_model: str = "free"
    world_monitor_domain: str | None = None
    # K-8 fix: all remaining registry fields
    replayability: str = "none"
    legal_risk: str = "low"
    rate_limit_notes: str = ""
    gap_policy_default: bool = False
    evidence_capture: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    theatre_families: list[str] = Field(default_factory=list)


class RegistryLoader:
    """Load and query the OSINT Source Registry.

    Usage::

        registry = RegistryLoader.from_file("path/to/registry.json")
        source = registry.get("companies_house_api")
        settlement_sources = registry.settlement_eligible()
        gb_sources = registry.by_jurisdiction("GB")
    """

    SUPPORTED_VERSION = "0.4.0"

    def __init__(self, sources: list[RegistrySource], metadata: dict[str, Any]):
        self._sources: dict[str, RegistrySource] = {s.source_id: s for s in sources}
        self.metadata = metadata

    @classmethod
    def from_file(cls, path: str | Path) -> RegistryLoader:
        """Load registry from JSON file.

        K-7 fix: validates ``version == "0.4.0"``. Raises ValueError on mismatch.
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # K-7 fix: version validation
        version = data.get("version", "unknown")
        if version != cls.SUPPORTED_VERSION:
            raise ValueError(
                f"Registry version mismatch: expected {cls.SUPPORTED_VERSION}, "
                f"got {version!r}"
            )

        sources = []
        for entry in data.get("sources", []):
            sources.append(RegistrySource(**entry))

        metadata = {
            "version": version,
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
        """Return sources accessible via free public API (no payment).

        K-1 fix: corrected operator precedence. Now requires:
        - access_surface == "public_api"
        - cost_model == "free"
        - settlement_eligible == True
        - auth via none, api_key, or user_agent_header
        """
        return [
            s for s in self._sources.values()
            if (
                s.access_surface == "public_api"
                and s.cost_model == "free"
                and s.settlement_eligible
                and any(
                    m in ("none", "api_key", "user_agent_header")
                    for m in s.auth_methods
                )
            )
        ]

    def upstream_groups(self) -> dict[str, list[str]]:
        """Map independence_upstream_id to source_ids.

        Used by the corroboration engine to deduplicate sources
        sharing the same system of record.
        """
        groups: dict[str, list[str]] = {}
        for s in self._sources.values():
            uid = s.independence_upstream_id
            if uid:
                groups.setdefault(uid, []).append(s.source_id)
        return groups

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
