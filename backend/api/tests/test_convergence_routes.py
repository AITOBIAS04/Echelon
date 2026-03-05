"""Tests for convergence API route — heatmap data contract.

Uses httpx TestClient against the FastAPI router to validate:
- Empty heatmap returns empty cells list
- update_heatmap_cells populates the response
- Response schema matches frontend ConvergenceResponse contract
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.convergence_routes import router, update_heatmap_cells


@pytest.fixture()
def client():
    """Create test client with convergence router mounted."""
    app = FastAPI()
    app.include_router(router)
    # Reset heatmap state between tests
    update_heatmap_cells([])
    return TestClient(app)


class TestConvergenceHeatmap:
    """Tests for GET /api/v1/convergence/heatmap."""

    def test_empty_heatmap(self, client: TestClient) -> None:
        """Empty state returns empty cells list with grid_size=1."""
        resp = client.get("/api/v1/convergence/heatmap")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cells"] == []
        assert data["grid_size"] == 1

    def test_populated_heatmap(self, client: TestClient) -> None:
        """update_heatmap_cells populates the response."""
        update_heatmap_cells([
            {
                "lat": 45.0,
                "lon": -90.0,
                "density": 0.8,
                "events": 12,
                "sources": ["WM", "CH"],
                "theatres": ["FED_RATE"],
            },
            {
                "lat": 30.0,
                "lon": 0.0,
                "density": 0.3,
                "events": 5,
                "sources": ["WM"],
                "theatres": [],
            },
        ])

        resp = client.get("/api/v1/convergence/heatmap")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cells"]) == 2

        cell = data["cells"][0]
        assert cell["lat"] == 45.0
        assert cell["lon"] == -90.0
        assert cell["density"] == 0.8
        assert cell["events"] == 12
        assert cell["sources"] == ["WM", "CH"]
        assert cell["theatres"] == ["FED_RATE"]

    def test_response_matches_frontend_contract(self, client: TestClient) -> None:
        """Response shape matches frontend ConvergenceResponse interface."""
        update_heatmap_cells([{
            "lat": 10.0,
            "lon": 20.0,
            "density": 0.5,
            "events": 3,
            "sources": ["X"],
            "theatres": [],
        }])

        resp = client.get("/api/v1/convergence/heatmap")
        data = resp.json()

        # Top-level keys
        assert "cells" in data
        assert "grid_size" in data

        # Cell keys match frontend CellData
        cell = data["cells"][0]
        for key in ("lat", "lon", "density", "events", "sources", "theatres"):
            assert key in cell, f"Missing key: {key}"

    def test_update_replaces_previous_data(self, client: TestClient) -> None:
        """Calling update_heatmap_cells replaces, not appends."""
        update_heatmap_cells([{"lat": 1, "lon": 1, "density": 0.1, "events": 1, "sources": [], "theatres": []}])
        update_heatmap_cells([{"lat": 2, "lon": 2, "density": 0.2, "events": 2, "sources": [], "theatres": []}])

        resp = client.get("/api/v1/convergence/heatmap")
        data = resp.json()
        assert len(data["cells"]) == 1
        assert data["cells"][0]["lat"] == 2
