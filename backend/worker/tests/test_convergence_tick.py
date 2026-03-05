"""Tests for convergence_tick — evidence buffer → heatmap pipeline.

Validates:
- Empty buffer returns None (no-op)
- push_evidence_bundles fills the buffer
- convergence_tick drains buffer and updates heatmap cells
- Buffer drains atomically (not re-processed)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from backend.worker.tasks.convergence_tick import (
    convergence_tick,
    push_evidence_bundles,
    _evidence_buffer,
)


def _make_bundle(lat: float, lon: float, source_group: str, source_id: str = "src_1"):
    """Create a minimal EvidenceBundle-like object for testing."""
    from dataclasses import dataclass, field

    @dataclass
    class FakeGeo:
        lat: float
        lon: float

    @dataclass
    class FakeEvent:
        timestamp: datetime
        geo: FakeGeo

    @dataclass
    class FakeBundle:
        normalised_event: FakeEvent
        source_group: str
        source_id: str

    return FakeBundle(
        normalised_event=FakeEvent(
            timestamp=datetime.now(timezone.utc),
            geo=FakeGeo(lat=lat, lon=lon),
        ),
        source_group=source_group,
        source_id=source_id,
    )


@pytest.fixture(autouse=True)
def _reset_buffer():
    """Reset the evidence buffer between tests."""
    import backend.worker.tasks.convergence_tick as mod
    mod._evidence_buffer = []
    yield
    mod._evidence_buffer = []


class TestConvergenceTick:

    @pytest.mark.asyncio
    async def test_empty_buffer_returns_none(self):
        result = await convergence_tick(session=None)
        assert result is None

    def test_push_fills_buffer(self):
        bundles = [_make_bundle(10.0, 20.0, "WM")]
        push_evidence_bundles(bundles)
        import backend.worker.tasks.convergence_tick as mod
        assert len(mod._evidence_buffer) == 1

    @pytest.mark.asyncio
    async def test_tick_drains_buffer(self):
        """After tick, buffer should be empty."""
        bundles = [_make_bundle(10.0, 20.0, "WM")]
        push_evidence_bundles(bundles)

        await convergence_tick(session=None)

        import backend.worker.tasks.convergence_tick as mod
        assert len(mod._evidence_buffer) == 0

    @pytest.mark.asyncio
    async def test_tick_with_convergence_updates_heatmap(self):
        """When ≥3 source groups converge in one cell, heatmap is updated."""
        # Push 3 bundles in same 1-deg cell (floor(45.x)=45, floor(-90.x)=-91)
        push_evidence_bundles([
            _make_bundle(45.3, -90.7, "WM", "src_1"),
            _make_bundle(45.8, -90.2, "CH", "src_2"),
            _make_bundle(45.1, -90.9, "NEWS", "src_3"),
        ])

        with patch("backend.worker.tasks.convergence_tick.update_heatmap_cells") as mock_update:
            result = await convergence_tick(session=None)

            assert result is not None
            assert "3 bundles" in result
            assert "heatmap cells" in result

            # Verify update_heatmap_cells was called with cell data
            mock_update.assert_called_once()
            cells = mock_update.call_args[0][0]
            assert len(cells) >= 1
            cell = cells[0]
            assert "lat" in cell
            assert "lon" in cell
            assert "density" in cell
            assert "sources" in cell
            assert len(cell["sources"]) >= 3

    @pytest.mark.asyncio
    async def test_tick_below_threshold_no_heatmap_update(self):
        """When <3 source groups, no heatmap update."""
        push_evidence_bundles([
            _make_bundle(10.0, 20.0, "WM"),
            _make_bundle(10.5, 20.5, "CH"),  # Same cell, only 2 types
        ])

        with patch("backend.worker.tasks.convergence_tick.update_heatmap_cells") as mock_update:
            result = await convergence_tick(session=None)
            mock_update.assert_not_called()
            assert "0 convergence alerts" in result

    @pytest.mark.asyncio
    async def test_second_tick_after_drain_is_noop(self):
        """Buffer drains atomically — second tick is no-op."""
        push_evidence_bundles([_make_bundle(10.0, 20.0, "WM")])
        await convergence_tick(session=None)

        result = await convergence_tick(session=None)
        assert result is None
