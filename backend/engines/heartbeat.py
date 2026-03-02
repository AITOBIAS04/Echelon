"""Heartbeat Scheduler — asyncio-based multi-cadence timer.

Drives periodic ticks at four cadences. Handlers registered per cadence,
shared across all theatres. One asyncio.Task per cadence per theatre.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Coroutine, Any


@dataclass
class HeartbeatConfig:
    """Interval configuration for the four heartbeat cadences."""

    agent_interval_s: float = 5.0
    market_interval_s: float = 10.0
    paradox_interval_s: float = 30.0
    entropy_interval_s: float = 60.0


CADENCES = ["agent", "market", "paradox", "entropy"]


class HeartbeatScheduler:
    """Drives the simulation game loop at four cadences."""

    def __init__(self, config: HeartbeatConfig) -> None:
        self._config = config
        self._handlers: dict[str, list[Callable[..., Coroutine[Any, Any, Any]]]] = {
            c: [] for c in CADENCES
        }
        self._tasks: dict[tuple[str, str], asyncio.Task] = {}
        self._tick_counts: dict[str, dict[str, int]] = {}

    def register_handler(
        self, cadence: str, handler: Callable[..., Coroutine[Any, Any, Any]]
    ) -> None:
        """Register an async handler for a cadence. Shared across all theatres."""
        if cadence not in CADENCES:
            raise ValueError(f"Unknown cadence: {cadence}. Must be one of {CADENCES}")
        self._handlers[cadence].append(handler)

    async def start(self, theatre_id: str) -> None:
        """Start heartbeat loop for a Theatre. Non-blocking."""
        if theatre_id not in self._tick_counts:
            self._tick_counts[theatre_id] = {c: 0 for c in CADENCES}

        intervals = {
            "agent": self._config.agent_interval_s,
            "market": self._config.market_interval_s,
            "paradox": self._config.paradox_interval_s,
            "entropy": self._config.entropy_interval_s,
        }

        for cadence in CADENCES:
            key = (theatre_id, cadence)
            if key not in self._tasks or self._tasks[key].done():
                self._tasks[key] = asyncio.create_task(
                    self._tick_loop(theatre_id, cadence, intervals[cadence])
                )

    async def stop(self, theatre_id: str) -> None:
        """Stop heartbeat for a Theatre. Cancel all tasks. Idempotent."""
        tasks_to_cancel = []
        for cadence in CADENCES:
            key = (theatre_id, cadence)
            task = self._tasks.pop(key, None)
            if task is not None and not task.done():
                task.cancel()
                tasks_to_cancel.append(task)

        for task in tasks_to_cancel:
            try:
                await task
            except asyncio.CancelledError:
                pass

    def tick_count(self, theatre_id: str) -> dict[str, int]:
        """Return tick counts per cadence for monitoring."""
        return dict(self._tick_counts.get(theatre_id, {c: 0 for c in CADENCES}))

    def is_running(self, theatre_id: str) -> bool:
        """Check if any heartbeat tasks are running for a Theatre."""
        for cadence in CADENCES:
            key = (theatre_id, cadence)
            task = self._tasks.get(key)
            if task is not None and not task.done():
                return True
        return False

    async def _tick_loop(
        self, theatre_id: str, cadence: str, interval: float
    ) -> None:
        """Internal tick loop. Runs until cancelled."""
        try:
            while True:
                await asyncio.sleep(interval)
                for handler in self._handlers[cadence]:
                    await handler(theatre_id)
                self._tick_counts[theatre_id][cadence] += 1
        except asyncio.CancelledError:
            raise
