"""Theatre Evidence Collector -- OSINT evidence collection for Theatres.

Orchestrates evidence collection during the TRADING phase using
LiveOSINTRealityProvider with mock WM fixtures. Collects evidence
bundles per heartbeat cadence, stores evidence in-memory keyed by
collection timestamp.

Cycle-012, Sprint 2 -- Task 1.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from backend.osint.engine.scorer import OracleOutput


@dataclass
class EvidenceSnapshot:
    """Single evidence collection snapshot for a Theatre."""

    theatre_id: str
    collection_timestamp: str
    oracle_output: OracleOutput | None
    evidence_bundles: list[Any]
    collection_results: list[Any]
    source_coverage_pct: float


class TheatreEvidenceCollector:
    """Collects OSINT evidence for a Theatre during the TRADING phase.

    Uses LiveOSINTRealityProvider (or any RealitySignalProvider) to
    collect evidence. Stores snapshots in-memory as a time-ordered list.
    """

    def __init__(
        self,
        reality_provider: Any,
        committed_sources: list[str],
    ) -> None:
        self._reality_provider = reality_provider
        self._committed_sources = committed_sources
        self._snapshots: list[EvidenceSnapshot] = []

    def collect_heartbeat(self, theatre_id: str) -> EvidenceSnapshot:
        """Collect evidence for all committed sources.

        Delegates to the reality provider's get_signal() method,
        then extracts the cached OracleOutput if available.

        Returns an EvidenceSnapshot capturing the collection state.
        """
        signal = self._reality_provider.get_signal(theatre_id)

        # Extract OracleOutput from the provider's cache if available
        oracle_output: OracleOutput | None = None
        evidence_bundles: list[Any] = []
        collection_results: list[Any] = []

        cached = getattr(self._reality_provider, '_last_output', {})
        if isinstance(cached, dict):
            output = cached.get(theatre_id)
            if output is not None and isinstance(output, OracleOutput):
                oracle_output = output
                evidence_bundles = list(oracle_output.evidence_bundles)

        # Compute source coverage
        coverage = self.compute_coverage_pct(oracle_output)

        snapshot = EvidenceSnapshot(
            theatre_id=theatre_id,
            collection_timestamp=datetime.now(timezone.utc).isoformat(),
            oracle_output=oracle_output,
            evidence_bundles=evidence_bundles,
            collection_results=collection_results,
            source_coverage_pct=coverage,
        )

        self._snapshots.append(snapshot)
        return snapshot

    def get_evidence_history(self) -> list[EvidenceSnapshot]:
        """Return all collected evidence snapshots."""
        return list(self._snapshots)

    def get_latest_evidence(self) -> EvidenceSnapshot | None:
        """Return the most recent evidence snapshot, or None."""
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    def compute_coverage_pct(self, oracle_output: OracleOutput | None = None) -> float:
        """Compute source coverage percentage.

        coverage = successful_sources / total_committed_sources
        """
        total = len(self._committed_sources)
        if total == 0:
            return 0.0

        if oracle_output is None:
            return 0.0

        # Count unique source_ids in evidence bundles
        collected_sources = set()
        for bundle in oracle_output.evidence_bundles:
            collected_sources.add(bundle.source_id)

        successful = len(collected_sources.intersection(set(self._committed_sources)))
        return successful / total
