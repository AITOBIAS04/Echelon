"""OSINT Source Manifest — build and validate source manifests for Theatres.

Given a list of committed source IDs, validates against the OSINT registry
and produces a structured manifest with settlement eligibility and
independence flags. Sources sharing an independence_upstream_id are
flagged PROVISIONAL per the corroboration penalty model.

Cycle-012, Sprint 1 — Theatre Creation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.osint.models.registry import RegistryLoader, RegistrySource


class SettlementStatus:
    """Settlement eligibility status constants."""

    ELIGIBLE = "ELIGIBLE"
    PROVISIONAL = "PROVISIONAL"
    INELIGIBLE = "INELIGIBLE"


@dataclass
class SourceManifestEntry:
    """Single source entry in a Theatre's committed source manifest."""

    source_id: str
    source_group: str
    independence_upstream_id: str
    jurisdiction: str | None
    access_surface: str  # world_monitor_domain or "registry"
    settlement_status: str  # SettlementStatus constant
    settlement_eligible: bool
    display_name: str


@dataclass
class SourceManifest:
    """Complete source manifest for a Theatre's committed sources.

    Included in the commitment hash and certificate.
    """

    entries: list[SourceManifestEntry] = field(default_factory=list)
    registry_version: str = ""
    validated: bool = False
    validation_errors: list[str] = field(default_factory=list)


class SourceManifestBuilder:
    """Builds and validates OSINT source manifests for Theatres.

    Validates source IDs against the registry, flags PROVISIONAL sources
    (those sharing an independence_upstream_id with another committed
    source), and produces a SourceManifest for the commitment hash.
    """

    def __init__(self, registry_loader: RegistryLoader) -> None:
        self._registry = registry_loader

    def validate_sources(self, source_ids: list[str]) -> tuple[bool, list[str]]:
        """Validate source IDs against the registry.

        Returns (is_valid, list_of_errors). Empty errors = valid.
        """
        errors: list[str] = []
        for sid in source_ids:
            source = self._registry.get_source(sid)
            if source is None:
                errors.append(f"Source '{sid}' not found in registry")
        return (len(errors) == 0, errors)

    def build(self, source_ids: list[str]) -> SourceManifest:
        """Build a source manifest from committed source IDs.

        Validates all sources exist, determines settlement status,
        and flags PROVISIONAL sources (shared independence_upstream_id).
        """
        is_valid, errors = self.validate_sources(source_ids)

        if not is_valid:
            return SourceManifest(
                entries=[],
                registry_version=self._get_registry_version(),
                validated=False,
                validation_errors=errors,
            )

        # Collect all sources
        sources: list[RegistrySource] = []
        for sid in source_ids:
            source = self._registry.get_source(sid)
            if source is not None:
                sources.append(source)

        # Count upstream_id occurrences to detect shared upstream
        upstream_counts: dict[str, int] = {}
        for source in sources:
            uid = source.independence_upstream_id
            upstream_counts[uid] = upstream_counts.get(uid, 0) + 1

        # Build entries
        entries: list[SourceManifestEntry] = []
        for source in sources:
            settlement_status = self._determine_settlement_status(
                source, upstream_counts
            )
            entries.append(
                SourceManifestEntry(
                    source_id=source.source_id,
                    source_group=source.source_group,
                    independence_upstream_id=source.independence_upstream_id,
                    jurisdiction=source.jurisdiction,
                    access_surface=source.world_monitor_domain or "registry",
                    settlement_status=settlement_status,
                    settlement_eligible=source.settlement_eligible,
                    display_name=source.display_name,
                )
            )

        return SourceManifest(
            entries=entries,
            registry_version=self._get_registry_version(),
            validated=True,
            validation_errors=[],
        )

    def _determine_settlement_status(
        self,
        source: RegistrySource,
        upstream_counts: dict[str, int],
    ) -> str:
        """Determine settlement status for a source.

        - ELIGIBLE: settlement_eligible=True and unique upstream_id
        - PROVISIONAL: multiple sources share the same upstream_id
          (corroboration penalty applies)
        - INELIGIBLE: settlement_eligible=False and unique upstream_id
        """
        uid = source.independence_upstream_id
        shared = upstream_counts.get(uid, 1) > 1

        if shared:
            return SettlementStatus.PROVISIONAL

        if source.settlement_eligible:
            return SettlementStatus.ELIGIBLE

        return SettlementStatus.INELIGIBLE

    def _get_registry_version(self) -> str:
        """Extract registry version from loaded sources metadata."""
        import json
        try:
            with open(self._registry._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("version", "unknown")
        except Exception:
            return "unknown"
