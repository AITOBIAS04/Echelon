"""Collection Runner — Stage 1 of the evidence pipeline.

Orchestrates concurrent collector execution per Theatre oracle_config.
Uses asyncio.gather() with per-collector timeout. Failed fetches return
CollectionResult with success=False. Does NOT raise on individual failure.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, GeoPoint


@dataclass
class CollectionPlan:
    """Describes what to collect for a specific Theatre evaluation."""

    theatre_id: str
    sources: list[str]                              # source_ids to collect
    evaluation_window: tuple[datetime, datetime]    # (start, end)
    geo: GeoPoint | None = None                     # Geographic focus (optional)
    timeout_s: float = 30.0                         # Per-collector timeout
    source_params: dict[str, dict] = field(default_factory=dict)  # per-source params


class CollectionRunner:
    """Stage 1: orchestrate evidence collection per Theatre config.

    Runs all collectors concurrently via asyncio.gather() with
    per-collector timeout. Failed fetches return CollectionResult
    with success=False. Does NOT raise on individual failure.
    """

    def __init__(self, collectors: dict[str, BaseCollector]) -> None:
        """Initialize with source_id -> BaseCollector mapping."""
        self._collectors = collectors

    def build_plan(
        self, oracle_config: dict, theatre_id: str
    ) -> CollectionPlan:
        """Derive CollectionPlan from Theatre oracle_config.

        Extracts:
        - source_ids from oracle_config["sources"]
        - evaluation_window from oracle_config["evaluation_window"]
        - geo from oracle_config["geo"] (optional)
        - timeout_s from oracle_config["timeout_s"] (default 30.0)

        Filters to registered collectors only — unknown source_ids are
        still included (they produce failure results at collect time).
        """
        sources = oracle_config.get("sources", list(self._collectors.keys()))
        window_raw = oracle_config.get("evaluation_window", {})
        now = datetime.now(timezone.utc)

        # Parse evaluation window
        start = window_raw.get("start", now)
        end = window_raw.get("end", now)
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        # Parse optional geo
        geo_raw = oracle_config.get("geo")
        geo: GeoPoint | None = None
        if geo_raw is not None:
            geo = GeoPoint(
                lat=geo_raw.get("lat", 0.0),
                lon=geo_raw.get("lon", 0.0),
                radius_m=geo_raw.get("radius_m", 50000),
            )

        timeout_s = oracle_config.get("timeout_s", 30.0)
        source_params = oracle_config.get("source_params", {})

        return CollectionPlan(
            theatre_id=theatre_id,
            sources=sources,
            evaluation_window=(start, end),
            geo=geo,
            timeout_s=timeout_s,
            source_params=source_params,
        )

    async def collect(self, plan: CollectionPlan) -> list[CollectionResult]:
        """Run all collectors concurrently. Returns list of CollectionResult.

        Uses asyncio.gather() with return_exceptions=False.
        Each collector call is wrapped in asyncio.wait_for(timeout_s).
        Timeout produces CollectionResult(success=False, error="timeout").
        No leaked asyncio tasks on collection failure.
        """
        tasks = []
        for source_id in plan.sources:
            collector = self._collectors.get(source_id)
            if collector is None:
                # Source not registered — produce failure result
                tasks.append(self._missing_collector_result(source_id))
            else:
                tasks.append(
                    self._collect_with_timeout(collector, plan)
                )
        results = await asyncio.gather(*tasks)
        return list(results)

    async def _collect_with_timeout(
        self, collector: BaseCollector, plan: CollectionPlan
    ) -> CollectionResult:
        """Wrap collector.fetch() with per-collector timeout."""
        request = self._build_request(plan)
        # Merge per-source params (source-specific keys override generic)
        extra = plan.source_params.get(collector.source_id(), {})
        if extra:
            request.update(extra)
        try:
            return await asyncio.wait_for(
                collector.fetch(
                    request=request,
                    theatre_id=plan.theatre_id,
                ),
                timeout=plan.timeout_s,
            )
        except asyncio.TimeoutError:
            return CollectionResult(
                source_id=collector.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=plan.timeout_s * 1000,
                success=False,
                error=f"Timeout after {plan.timeout_s}s",
                retrieved_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            return CollectionResult(
                source_id=collector.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error=f"Unexpected error: {exc}",
                retrieved_at=datetime.now(timezone.utc),
            )

    def _build_request(self, plan: CollectionPlan) -> dict:
        """Build request dict from CollectionPlan fields."""
        request: dict = {
            "theatre_id": plan.theatre_id,
            "evaluation_window_start": plan.evaluation_window[0].isoformat(),
            "evaluation_window_end": plan.evaluation_window[1].isoformat(),
        }
        if plan.geo is not None:
            request["geo"] = {
                "lat": plan.geo.lat,
                "lon": plan.geo.lon,
                "radius_m": plan.geo.radius_m,
            }
        return request

    async def _missing_collector_result(self, source_id: str) -> CollectionResult:
        """Produce failure result for unregistered source."""
        return CollectionResult(
            source_id=source_id,
            bundle=None,
            raw_payload=b"",
            fetch_duration_ms=0.0,
            success=False,
            error=f"No collector registered for source_id '{source_id}'",
            retrieved_at=datetime.now(timezone.utc),
        )
