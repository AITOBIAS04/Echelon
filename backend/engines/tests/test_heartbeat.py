"""Heartbeat Scheduler tests — async cadence loops, handler dispatch, lifecycle."""
from __future__ import annotations

import asyncio

import pytest

from backend.engines.heartbeat import CADENCES, HeartbeatConfig, HeartbeatScheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fast_config() -> HeartbeatConfig:
    """Very short intervals so tests complete quickly."""
    return HeartbeatConfig(
        agent_interval_s=0.01,
        market_interval_s=0.02,
        paradox_interval_s=0.03,
        entropy_interval_s=0.04,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    """Handler registration."""

    def test_register_valid_cadence(self) -> None:
        scheduler = HeartbeatScheduler(HeartbeatConfig())
        called: list[str] = []

        async def handler(theatre_id: str) -> None:
            called.append(theatre_id)

        scheduler.register_handler("entropy", handler)
        # Should not raise
        assert True

    def test_register_invalid_cadence_raises(self) -> None:
        scheduler = HeartbeatScheduler(HeartbeatConfig())

        async def handler(theatre_id: str) -> None:
            pass

        with pytest.raises(ValueError, match="Unknown cadence"):
            scheduler.register_handler("bogus", handler)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestLifecycle:
    """Start, stop, is_running."""

    @pytest.mark.asyncio
    async def test_start_creates_tasks(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        await scheduler.start("t1")
        assert scheduler.is_running("t1") is True

    @pytest.mark.asyncio
    async def test_stop_cancels_tasks(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        await scheduler.start("t1")
        await scheduler.stop("t1")
        assert scheduler.is_running("t1") is False

    @pytest.mark.asyncio
    async def test_stop_idempotent(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        await scheduler.start("t1")
        await scheduler.stop("t1")
        await scheduler.stop("t1")  # second stop — no error
        assert scheduler.is_running("t1") is False

    @pytest.mark.asyncio
    async def test_is_running_false_before_start(self) -> None:
        scheduler = HeartbeatScheduler(HeartbeatConfig())
        assert scheduler.is_running("t1") is False


# ---------------------------------------------------------------------------
# Handler dispatch
# ---------------------------------------------------------------------------

class TestHandlerDispatch:
    """Handlers are invoked per cadence tick."""

    @pytest.mark.asyncio
    async def test_handler_called_with_theatre_id(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        invocations: list[str] = []

        async def handler(theatre_id: str) -> None:
            invocations.append(theatre_id)

        scheduler.register_handler("agent", handler)
        await scheduler.start("t1")

        # Wait for a few ticks
        await asyncio.sleep(0.05)
        await scheduler.stop("t1")

        assert len(invocations) > 0
        assert all(tid == "t1" for tid in invocations)

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_cadence(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        a_calls: list[str] = []
        b_calls: list[str] = []

        async def handler_a(theatre_id: str) -> None:
            a_calls.append(theatre_id)

        async def handler_b(theatre_id: str) -> None:
            b_calls.append(theatre_id)

        scheduler.register_handler("agent", handler_a)
        scheduler.register_handler("agent", handler_b)
        await scheduler.start("t1")
        await asyncio.sleep(0.05)
        await scheduler.stop("t1")

        assert len(a_calls) > 0
        assert len(b_calls) > 0


# ---------------------------------------------------------------------------
# Tick counts
# ---------------------------------------------------------------------------

class TestTickCounts:
    """Tick count tracking."""

    @pytest.mark.asyncio
    async def test_tick_counts_increment(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        await scheduler.start("t1")

        await asyncio.sleep(0.06)
        await scheduler.stop("t1")

        counts = scheduler.tick_count("t1")
        # Agent cadence (0.01s interval) should have fired multiple times in 0.06s
        assert counts["agent"] > 0

    def test_tick_count_unknown_theatre(self) -> None:
        scheduler = HeartbeatScheduler(HeartbeatConfig())
        counts = scheduler.tick_count("nonexistent")
        assert all(v == 0 for v in counts.values())


# ---------------------------------------------------------------------------
# Multi-theatre isolation
# ---------------------------------------------------------------------------

class TestMultiTheatre:
    """Separate task trees per theatre."""

    @pytest.mark.asyncio
    async def test_two_theatres_independent(self) -> None:
        scheduler = HeartbeatScheduler(_fast_config())
        await scheduler.start("t1")
        await scheduler.start("t2")

        assert scheduler.is_running("t1") is True
        assert scheduler.is_running("t2") is True

        await scheduler.stop("t1")
        assert scheduler.is_running("t1") is False
        assert scheduler.is_running("t2") is True  # still running

        await scheduler.stop("t2")
        assert scheduler.is_running("t2") is False
