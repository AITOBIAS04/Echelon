"""
Collection runner — Stage 1 of the Composed Oracle pipeline.

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
    FailureMode,
    FreshnessState,
    GapKind,
    GapReport,
    OracleCollectionSummary,
    ReceiptMode,
    meets_receipt_minimum,
)
from osint_pipeline.models.registry import RegistrySource

logger = logging.getLogger(__name__)


class CollectionRunner:
    """
    Orchestrate OSINT collection across multiple sources.

    Usage:
        runner = CollectionRunner(collectors=[ch_collector, sec_collector, ...])
        summary = runner.run(
            query_context={"company_number": "12345678"},
            theatre_id="theatre_gb_realestate_001"
        )
    """

    def __init__(
        self,
        collectors: list[BaseCollector],
        max_workers: int = 5,
        timeout_budget_seconds: float = 60.0,
        registry_sources: dict[str, RegistrySource] | None = None,
    ):
        """
        Args:
            collectors: List of configured collector instances.
            max_workers: Max parallel collection threads.
            timeout_budget_seconds: Total budget for all collections.
            registry_sources: Optional map of source_id → RegistrySource
                for runner-level receipt mode enforcement.
        """
        self.collectors = {c.source_id: c for c in collectors}
        self.max_workers = max_workers
        self.timeout_budget_seconds = timeout_budget_seconds
        self.registry_sources: dict[str, RegistrySource] = registry_sources or {}

    def run(
        self,
        query_context: dict[str, Any],
        theatre_id: str | None = None,
        required_source_ids: list[str] | None = None,
        allow_gaps_for: list[str] | None = None,
    ) -> OracleCollectionSummary:
        """
        Execute collection across all configured collectors.

        Args:
            query_context: Shared query context (entity IDs, time windows).
            theatre_id: Theatre this collection serves.
            required_source_ids: If set, only collect from these sources.
                                If None, collect from all configured collectors.
            allow_gaps_for: source_ids where gaps are acceptable (downgraded path).

        Returns:
            OracleCollectionSummary with bundles and gap reports.
        """
        allow_gaps = set(allow_gaps_for or [])
        now = datetime.now(timezone.utc)

        # Determine which collectors to run
        if required_source_ids:
            active = {
                sid: c
                for sid, c in self.collectors.items()
                if sid in required_source_ids
            }
            # Report missing collectors
            for sid in required_source_ids:
                if sid not in self.collectors:
                    logger.warning(
                        f"Required source '{sid}' has no configured collector"
                    )
        else:
            active = self.collectors

        summary = OracleCollectionSummary(
            theatre_id=theatre_id,
            query_window_start=now,
            total_sources_attempted=len(active),
        )

        # Pre-check receipt mode enforcement at runner level.
        # Collectors that fail the minimum are skipped with a gap report.
        rejected_source_ids: set[str] = set()
        for sid, collector in list(active.items()):
            reg = self.registry_sources.get(sid)
            if reg is not None:
                minimum = ReceiptMode(reg.receipt_mode_minimum)
                if not meets_receipt_minimum(collector.RECEIPT_MODE, minimum):
                    summary.gaps.append(
                        GapReport(
                            source_id=sid,
                            source_group=collector.source_group,
                            jurisdiction=collector.jurisdiction,
                            reason=CollectionStatus.SOURCE_ERROR,
                            error_detail=(
                                f"Receipt mode {collector.RECEIPT_MODE.value} does not meet "
                                f"registry minimum {minimum.value}"
                            ),
                            gap_kind=GapKind.INTELLIGENCE_GAP,
                            freshness=FreshnessState.ERROR,
                            allow_gap=sid in allow_gaps,
                        )
                    )
                    summary.total_sources_failed += 1
                    rejected_source_ids.add(sid)
        active = {
            sid: c for sid, c in active.items() if sid not in rejected_source_ids
        }

        if not active:
            summary.query_window_end = datetime.now(timezone.utc)
            return summary

        # Execute collections (parallel where possible)
        results = {}
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(active))) as pool:
            futures = {
                pool.submit(collector.collect, query_context, theatre_id): source_id
                for source_id, collector in active.items()
            }
            try:
                for future in as_completed(futures, timeout=self.timeout_budget_seconds):
                    source_id = futures[future]
                    try:
                        result = future.result()
                        results[source_id] = result
                    except Exception as e:
                        logger.error(f"Collection failed for {source_id}: {e}")
                        results[source_id] = None
            except (TimeoutError, FuturesTimeoutError):
                logger.warning(
                    "Collection budget exhausted (%.1fs). "
                    "Producing gap reports for unfinished sources.",
                    self.timeout_budget_seconds,
                )

            # Produce gap reports for any sources that did not complete
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
                            failure_mode=FailureMode.READ_TIMEOUT,
                            retriable=True,
                        )
                    )
                    summary.total_sources_failed += 1

        # Process results
        for source_id, result in results.items():
            collector = active[source_id]

            if result is None:
                # Future failed entirely
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
        """
        Sequential collection (for debugging/testing).

        Same as run() but executes one source at a time with full logging.
        """
        now = datetime.now(timezone.utc)
        summary = OracleCollectionSummary(
            theatre_id=theatre_id,
            query_window_start=now,
            total_sources_attempted=len(self.collectors),
        )

        for source_id, collector in self.collectors.items():
            logger.info(f"Collecting from {source_id}...")
            try:
                result = collector.collect(query_context, theatre_id)
                if result.succeeded:
                    logger.info(
                        f"  OK: {source_id} — {result.duration_ms}ms, "
                        f"confidence={result.bundle.confidence_score:.2f}"
                    )
                    summary.bundles.append(result.bundle)
                    summary.total_sources_succeeded += 1
                else:
                    logger.warning(
                        f"  FAIL: {source_id} — {result.status.value}: {result.error_message}"
                    )
                    gap = collector.to_gap_report(result)
                    summary.gaps.append(gap)
                    summary.total_sources_failed += 1
            except Exception as e:
                logger.error(f"  ERROR: {source_id} — {e}")
                summary.gaps.append(
                    GapReport(
                        source_id=source_id,
                        source_group=collector.source_group,
                        jurisdiction=collector.jurisdiction,
                        reason=CollectionStatus.SOURCE_ERROR,
                        error_detail=str(e),
                    )
                )
                summary.total_sources_failed += 1

        summary.query_window_end = datetime.now(timezone.utc)
        return summary

    def close_all(self):
        """Close all collector HTTP clients."""
        for collector in self.collectors.values():
            collector.close()
