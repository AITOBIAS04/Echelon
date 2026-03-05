"""Convergence Tick — bridges OSINT evidence into the heatmap API.

Drains a process-level evidence buffer through ConvergenceDetector.detect(),
converts alerts to heatmap cells, and pushes to the convergence route.

Evidence bundles are pushed into the buffer by the OSINT Scorer
(see backend/osint/engine/scorer.py).  The game loop drains the buffer
every 120 seconds via the ``evidence`` task slot.

In-memory only (matching ConvergenceDetector's 011 scope).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.osint.engine.convergence import ConvergenceDetector
from backend.api.convergence_routes import update_heatmap_cells

if TYPE_CHECKING:
    from backend.osint.models.evidence import EvidenceBundle

logger = logging.getLogger("echelon.convergence_tick")

# ---------------------------------------------------------------------------
# Process-level evidence buffer
# ---------------------------------------------------------------------------

_evidence_buffer: list["EvidenceBundle"] = []


def push_evidence_bundles(bundles: list["EvidenceBundle"]) -> None:
    """Append new evidence bundles to the convergence buffer.

    Called by the OSINT Scorer after each theatre evaluation.
    Thread-safe for single-process async (game loop + OSINT in same process).
    """
    _evidence_buffer.extend(bundles)


# ---------------------------------------------------------------------------
# Game-loop callable
# ---------------------------------------------------------------------------

async def convergence_tick(session) -> str | None:
    """Drain evidence buffer, run convergence detection, update heatmap.

    Args:
        session: SQLAlchemy async session (accepted for game-loop interface
                 compatibility; unused — convergence is in-memory).

    Returns:
        Summary string for game loop logging, or None if no data.
    """
    global _evidence_buffer

    if not _evidence_buffer:
        return None

    # Drain buffer atomically
    bundles = _evidence_buffer
    _evidence_buffer = []

    detector = ConvergenceDetector(min_event_types=3, window_hours=24.0)
    alerts = detector.detect(bundles)

    if not alerts:
        return f"Processed {len(bundles)} evidence bundles, 0 convergence alerts"

    # Convert alerts to heatmap cells
    cells = []
    for alert in alerts:
        cell = alert.cell
        cells.append({
            "lat": float(cell.lat_bin) + 0.5,  # Center of 1-deg cell
            "lon": float(cell.lon_bin) + 0.5,
            "density": cell.convergence_score,
            "events": len(cell.events),
            "sources": sorted(cell.event_types),
            "theatres": [alert.theatre_id] if alert.theatre_id else [],
        })

    update_heatmap_cells(cells)

    return (
        f"Processed {len(bundles)} bundles → "
        f"{len(alerts)} convergence alerts → "
        f"{len(cells)} heatmap cells"
    )
