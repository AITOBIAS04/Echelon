"""Convergence Detector — multi-domain signal co-location detection.

Bins NormalisedEvents into 1 deg x 1 deg geographic cells, counts
distinct WMDomain values per cell, fires alerts when threshold met
within a configurable time window.

011 scope: Alerts logged in-process only. No persistence, no MCP
surface. No automatic Theatre creation. State lost on restart.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from backend.osint.models.evidence import EvidenceBundle, NormalisedEvent


@dataclass
class ConvergenceCell:
    """Geographic cell accumulator for convergence detection.

    Attributes:
        lat_bin: Floor of latitude (integer degree).
        lon_bin: Floor of longitude (integer degree).
        event_types: Set of WMDomain-equivalent strings (source_group).
        events: NormalisedEvent list within this cell.
        convergence_score: Computed score rewarding diversity and density.
    """

    lat_bin: int
    lon_bin: int
    event_types: set[str] = field(default_factory=set)
    events: list[NormalisedEvent] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    convergence_score: float = 0.0


@dataclass
class ConvergenceAlert:
    """Alert fired when multiple domains converge in a geographic cell.

    Attributes:
        alert_id: Unique alert identifier.
        cell: The ConvergenceCell that triggered this alert.
        theatre_id: Matched Theatre ID (None until theatre matching).
        triggered_at: UTC timestamp of alert creation.
    """

    alert_id: str
    cell: ConvergenceCell
    theatre_id: str | None = None
    triggered_at: datetime = field(default_factory=lambda: datetime.utcnow())


class ConvergenceDetector:
    """Multi-domain signal co-location detection.

    Groups evidence by 1 deg x 1 deg geographic cells (floor(lat), floor(lon)).
    Fires alerts when distinct event types (by source_group) in a cell meet
    the threshold within the time window.
    """

    def __init__(
        self,
        min_event_types: int = 3,
        window_hours: float = 24.0,
    ) -> None:
        """Initialize convergence detector.

        Args:
            min_event_types: Minimum distinct source_groups to trigger alert.
            window_hours: Time window in hours for event co-location.
        """
        self._min_event_types = min_event_types
        self._window_hours = window_hours

    def detect(
        self,
        bundles: list[EvidenceBundle],
    ) -> list[ConvergenceAlert]:
        """Bin events by geographic cell, filter by window, fire alerts.

        Args:
            bundles: EvidenceBundle list from the collection/corroboration stage.

        Returns:
            List of ConvergenceAlert for cells meeting the threshold.
        """
        if not bundles:
            return []

        # Time window cutoff
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self._window_hours)

        # Bin events by geographic cell
        cells: dict[tuple[int, int], ConvergenceCell] = {}

        for bundle in bundles:
            event = bundle.normalised_event
            # Filter by time window
            event_ts = event.timestamp
            if hasattr(event_ts, 'tzinfo') and event_ts.tzinfo is None:
                # Assume UTC for naive datetimes
                event_ts = event_ts.replace(tzinfo=timezone.utc)
            if event_ts < cutoff:
                continue

            cell_key = self._cell_key(event.geo.lat, event.geo.lon)
            if cell_key not in cells:
                cells[cell_key] = ConvergenceCell(
                    lat_bin=cell_key[0],
                    lon_bin=cell_key[1],
                )
            cell = cells[cell_key]
            cell.events.append(event)
            cell.event_types.add(bundle.source_group)
            cell.source_ids.append(bundle.source_id)

        # Fire alerts for cells meeting threshold
        alerts: list[ConvergenceAlert] = []
        for cell in cells.values():
            if len(cell.event_types) >= self._min_event_types:
                cell.convergence_score = self._compute_convergence_score(cell)
                alerts.append(
                    ConvergenceAlert(
                        alert_id=f"conv_{cell.lat_bin}_{cell.lon_bin}_{uuid.uuid4().hex[:8]}",
                        cell=cell,
                    )
                )

        return alerts

    def match_theatres(
        self,
        alerts: list[ConvergenceAlert],
        active_theatres: list[dict],
    ) -> list[ConvergenceAlert]:
        """Match alerts to Theatres by geographic overlap.

        A Theatre matches if its geo center falls within the alert cell's
        1 deg x 1 deg bounds.

        Args:
            alerts: ConvergenceAlert list from detect().
            active_theatres: List of Theatre dicts with ``theatre_id``
                and ``geo`` (dict with ``lat``, ``lon``).

        Returns:
            Same alerts with theatre_id populated where matched.
        """
        for alert in alerts:
            cell = alert.cell
            for theatre in active_theatres:
                geo = theatre.get("geo", {})
                t_lat = geo.get("lat", 0.0)
                t_lon = geo.get("lon", 0.0)
                t_cell = self._cell_key(t_lat, t_lon)
                if t_cell == (cell.lat_bin, cell.lon_bin):
                    alert.theatre_id = theatre.get("theatre_id")
                    break  # First match wins

        return alerts

    @staticmethod
    def _cell_key(lat: float, lon: float) -> tuple[int, int]:
        """Compute 1 deg x 1 deg cell key from coordinates.

        Uses floor() for consistent binning across positive and negative
        coordinates.
        """
        return (math.floor(lat), math.floor(lon))

    @staticmethod
    def _compute_convergence_score(cell: ConvergenceCell) -> float:
        """Convergence score rewarding type diversity and event density.

        Formula:
            (distinct_types / 3) * (1 + log2(event_count))

        Returns:
            Float convergence score (unbounded above, minimum ~0.33).
        """
        distinct_types = len(cell.event_types)
        event_count = len(cell.events)
        if event_count <= 0:
            return 0.0
        return (distinct_types / 3.0) * (1.0 + math.log2(max(1, event_count)))
