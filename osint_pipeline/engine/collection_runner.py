"""Collection runner — Stage 1 of the Composed Oracle pipeline.

Orchestrates multiple collectors per theatre oracle configuration,
handles parallelism, timeout budgets, and gap reporting.

The runner is the entry point that ties together:
- Registry (which sources to query)
- Collectors (how to query each source)
- Evidence bundles (deterministic receipts)
- Gap reports (what we couldn't see)
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from datetime import datetime, timezone
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import (
    CollectionStatus,
    GapKind,
    GapReport,
    OracleCollectionSummary,
)

logger = logging.getLogger(__name__)


class CollectionRunner:
    """Orchestrate OSINT collection across multiple sources.

    Usage::

        runner = CollectionRunner(collectors=[ch_collector, sec_collector])
        summary = runner.run(
            query_context={"company_number": "12345678"},
            theatre_id="theatre_gb_realestate_001",
        )
    """

    def __init__(
        self,
        collectors: list[BaseCollector],
        max_workers: int = 5,
        timeout_budget_seconds: float = 60.0,
    ):
        self.collectors = {c.source_id: c for c in collectors}
        self.max_workers = max_workers
        self.timeout_budget_seconds = timeout_budget_seconds

    def run(
        self,
        query_context: dict[str, Any],
        theatre_id: str | None = None,
        required_source_ids: list[str] | None = None,
        allow_gaps_for: list[str] | None = None,
    ) -> OracleCollectionSummary:
        """Execute collection across all configured collectors.

        Args:
            query_context: Shared query context (entity IDs, time windows).
            theatre_id: Theatre this collection serves.
            required_source_ids: If set, only collect from these sources.
            allow_gaps_for: source_ids where gaps are acceptable.

        Returns:
            OracleCollectionSummary with bundles and gap reports.
        """
        allow_gaps = set(allow_gaps_for or [])
        now = datetime.now(timezone.utc)

        # Determine which collectors to run
        if required_source_ids is not None:
            active = {
                sid: c
                for sid, c in self.collectors.items()
                if sid in required_source_ids
            }
            # Report missing collectors as gaps
            for sid in required_source_ids:
                if sid not in self.collectors:
                    logger.warning(
                        "Required source '%s' has no configured collector", sid
                    )
        else:
            active = dict(self.collectors)

        if not active:
            return OracleCollectionSummary(
                theatre_id=theatre_id,
                query_window_start=now,
                query_window_end=now,
                total_sources_attempted=0,
            )

        summary = OracleCollectionSummary(
            theatre_id=theatre_id,
            query_window_start=now,
            total_sources_attempted=len(active),
        )

        # Add gap reports for missing required sources
        if required_source_ids is not None:
            for sid in required_source_ids:
                if sid not in self.collectors:
                    summary.gaps.append(
                        GapReport(
                            source_id=sid,
                            source_group="unknown",
                            jurisdiction="unknown",
                            reason=CollectionStatus.SOURCE_ERROR,
                            error_detail="No configured collector for this source",
                            allow_gap=sid in allow_gaps,
                        )
                    )
                    summary.total_sources_failed += 1
                    summary.total_sources_attempted += 1

        # Execute collections in parallel
        results: dict[str, Any] = {}
        worker_count = min(self.max_workers, len(active)) if active else 1
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {
                pool.submit(collector.collect, query_context, theatre_id): source_id
                for source_id, collector in active.items()
            }
            try:
                for future in as_completed(
                    futures, timeout=self.timeout_budget_seconds
                ):
                    source_id = futures[future]
                    try:
                        result = future.result()
                        results[source_id] = result
                    except Exception as exc:
                        logger.error("Collection failed for %s: %s", source_id, exc)
                        results[source_id] = None
            except (TimeoutError, FuturesTimeoutError):
                logger.warning(
                    "Collection budget exhausted (%.1fs). "
                    "Producing gap reports for unfinished sources.",
                    self.timeout_budget_seconds,
                )

            # Produce gap reports for sources that did not complete (Concern 6)
            unfinished_source_ids = set(futures.values()) - set(results.keys())
            for future, source_id in futures.items():
                if source_id in unfinished_source_ids:
                    future.cancel()
                    collector = active[source_id]
                    summary.gaps.append(
                        GapReport(
                            source_id=source_id,
                            source_group=collector.source_group,
                            jurisdiction=collector.jurisdiction,
                            reason=CollectionStatus.TIMEOUT,
                            error_detail=(
                                f"Collection budget exhausted after "
                                f"{self.timeout_budget_seconds}s"
                            ),
                            gap_kind=GapKind.INTELLIGENCE_GAP,
                            allow_gap=source_id in allow_gaps,
                        )
                    )
                    summary.total_sources_failed += 1

        # Process completed results
        for source_id, result in results.items():
            collector = active[source_id]

            if result is None:
                # Future raised an unhandled exception
                summary.gaps.append(
                    GapReport(
                        source_id=source_id,
                        source_group=collector.source_group,
                        jurisdiction=collector.jurisdiction,
                        reason=CollectionStatus.SOURCE_ERROR,
                        error_detail="Collection thread failed",
                        allow_gap=source_id in allow_gaps,
                    )
                )
                summary.total_sources_failed += 1

            elif result.succeeded:
                summary.bundles.append(result.bundle)
                summary.total_sources_succeeded += 1

            else:
                # Collection attempted but failed
                gap = collector.to_gap_report(
                    result, allow_gap=source_id in allow_gaps
                )
                summary.gaps.append(gap)
                summary.total_sources_failed += 1

        summary.query_window_end = datetime.now(timezone.utc)
        return summary

    def run_sequential(
        self,
        query_context: dict[str, Any],
        theatre_id: str | None = None,
    ) -> OracleCollectionSummary:
        """Sequential collection for debugging/testing.

        Same as run() but single-threaded with full logging.
        """
        now = datetime.now(timezone.utc)
        summary = OracleCollectionSummary(
            theatre_id=theatre_id,
            query_window_start=now,
            total_sources_attempted=len(self.collectors),
        )

        for source_id, collector in self.collectors.items():
            logger.info("Collecting from %s...", source_id)
            try:
                result = collector.collect(query_context, theatre_id)
                if result.succeeded:
                    logger.info(
                        "  OK: %s — %dms, confidence=%.2f",
                        source_id,
                        result.duration_ms,
                        result.bundle.confidence_score,
                    )
                    summary.bundles.append(result.bundle)
                    summary.total_sources_succeeded += 1
                else:
                    logger.warning(
                        "  FAIL: %s — %s: %s",
                        source_id,
                        result.status.value,
                        result.error_message,
                    )
                    gap = collector.to_gap_report(result)
                    summary.gaps.append(gap)
                    summary.total_sources_failed += 1
            except Exception as exc:
                logger.error("  ERROR: %s — %s", source_id, exc)
                summary.gaps.append(
                    GapReport(
                        source_id=source_id,
                        source_group=collector.source_group,
                        jurisdiction=collector.jurisdiction,
                        reason=CollectionStatus.SOURCE_ERROR,
                        error_detail=str(exc),
                    )
                )
                summary.total_sources_failed += 1

        summary.query_window_end = datetime.now(timezone.utc)
        return summary

    def close_all(self) -> None:
        """Close all collector HTTP clients."""
        for collector in self.collectors.values():
            collector.close()
