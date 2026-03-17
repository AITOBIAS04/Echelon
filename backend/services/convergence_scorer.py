"""
Convergence Scorer — Cycle 025
================================

Computes CROSS_DOMAIN_CONVERGENCE measures from multi-domain signal sets.
Clusters signals by (geo_region, time_window) and emits convergence cells
for clusters spanning 2+ domain source_groups.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from collections import defaultdict

from backend.database.models import OsintSignal
from backend.osint.models.evidence import WMDomain


@dataclass
class ConvergenceCell:
    """A cluster of signals from multiple domains that converge in geo/time."""
    signals: list[OsintSignal]
    domains: set[str]
    convergence_score: float
    geo_region: str | None


class ConvergenceScorer:
    """Computes CROSS_DOMAIN_CONVERGENCE measures from multi-domain signal sets."""

    def __init__(self, time_window_minutes: int = 60):
        self.time_window = timedelta(minutes=time_window_minutes)

    def score(self, signals: list[OsintSignal]) -> list[ConvergenceCell]:
        """Group signals by geo/time, emit convergence cells for 2+ domain groups."""
        clusters = self._cluster_signals(signals)
        cells = []
        total_domains = len(self._all_domains())
        for key, cluster in clusters.items():
            domains = {s.source_group for s in cluster}
            if len(domains) >= 2:
                score = len(domains) / total_domains
                cells.append(ConvergenceCell(
                    signals=cluster,
                    domains=domains,
                    convergence_score=score,
                    geo_region=key[0],
                ))
        return cells

    def _cluster_signals(
        self, signals: list[OsintSignal]
    ) -> dict[tuple[str | None, int], list[OsintSignal]]:
        """Cluster by (geo_region, time_bucket).

        Exact geo_region string match for v1. Time bucketed by
        time_window_minutes from epoch.
        """
        bucket_seconds = int(self.time_window.total_seconds())
        if bucket_seconds == 0:
            bucket_seconds = 3600

        clusters: dict[tuple[str | None, int], list[OsintSignal]] = defaultdict(list)
        for signal in signals:
            ts = signal.collected_at
            time_bucket = int(ts.timestamp()) // bucket_seconds
            key = (signal.geo_region, time_bucket)
            clusters[key].append(signal)
        return dict(clusters)

    @staticmethod
    def _all_domains() -> set[str]:
        return {d.value for d in WMDomain}
