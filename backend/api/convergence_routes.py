"""Convergence API routes — REST endpoint for heatmap data.

Exposes the ConvergenceDetector's accumulated cell data as a heatmap
endpoint consumed by the frontend ConvergenceMap component.

In-memory only (matching ConvergenceDetector's 011 scope). State
resets on restart. The OSINT pipeline feeds data via detect() calls;
this route simply reads current state.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/convergence", tags=["Convergence"])


class HeatmapCellResponse(BaseModel):
    lat: float
    lon: float
    density: float
    events: int
    sources: list[str]
    theatres: list[str]


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCellResponse]
    grid_size: int


# In-memory cell accumulator — fed by OSINT pipeline's ConvergenceDetector
_heatmap_cells: list[dict] = []


def update_heatmap_cells(cells: list[dict]) -> None:
    """Replace current heatmap state with fresh convergence data.

    Called by the OSINT pipeline after running ConvergenceDetector.detect().
    Each cell dict must contain: lat, lon, density, events, sources, theatres.
    """
    global _heatmap_cells
    _heatmap_cells = cells


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap():
    """Return current convergence heatmap data.

    Returns cell-level signal density for the frontend grid visualisation.
    Cells with zero activity are omitted — the frontend fills empty grid
    positions with zeroes.
    """
    return HeatmapResponse(
        cells=[
            HeatmapCellResponse(
                lat=c.get("lat", 0),
                lon=c.get("lon", 0),
                density=c.get("density", 0),
                events=c.get("events", 0),
                sources=c.get("sources", []),
                theatres=c.get("theatres", []),
            )
            for c in _heatmap_cells
        ],
        grid_size=1,
    )
