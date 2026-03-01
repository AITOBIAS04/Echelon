"""
Counter-signal checker — Stage 2b of the Composed Oracle pipeline.

Implements counter_signal_checked criterion from Composed Oracle Spec v2 §2.2.

Counter-signal classes (11 committed, expanded from 4 in v1):
1. calendar_holiday — Public holidays that could explain signal absence
2. calendar_trading_halt — Exchange/market closures
3. outage_reported — Known infrastructure outages
4. policy_rule_change — Regulatory or policy changes affecting the claim
5. regulatory_status_change — Entity regulatory status change
6. legal_dispute_active — Active legal proceedings
7. sanctions_designation — Sanctions list presence
8. corporate_event — M&A, restructuring, insolvency
9. force_majeure — Natural disaster, conflict, pandemic
10. data_revision_notice — Source has issued revision notice
11. seasonal_pattern — Known seasonal variation that could explain anomaly

Key principle: "We didn't just find a confirming signal; we proved
we looked for disconfirming signals."
"""

from __future__ import annotations

from typing import Any

from osint_pipeline.models.evidence import EvidenceBundle, FreshnessState, GapKind, GapReport
from osint_pipeline.models.oracle_output import CounterSignalResult


# All 11 committed counter-signal classes
COUNTER_SIGNAL_CLASSES = [
    "calendar_holiday",
    "calendar_trading_halt",
    "outage_reported",
    "policy_rule_change",
    "regulatory_status_change",
    "legal_dispute_active",
    "sanctions_designation",
    "corporate_event",
    "force_majeure",
    "data_revision_notice",
    "seasonal_pattern",
]


class CounterSignalChecker:
    """
    Evaluate counter-signal streams against collected evidence.

    For each required counter-signal class in the theatre config,
    the checker verifies that:
    1. A counter-signal source was queried (checked=True)
    2. The result is recorded (signal_found=True/False)
    3. If a signal IS found, the theatre config determines whether
       it's a blocking fail or an allowed gap
    """

    def __init__(self, allow_gaps: dict[str, bool] | None = None):
        """
        Args:
            allow_gaps: Map of counter_signal_class → allow_gap.
                        If a class is True, finding a signal doesn't fail.
        """
        self.allow_gaps = allow_gaps or {}

    def evaluate(
        self,
        counter_signal_bundles: list[EvidenceBundle],
        counter_signal_gaps: list[GapReport],
        required_classes: list[str] | None = None,
    ) -> list[CounterSignalResult]:
        """
        Evaluate counter-signal checking.

        Args:
            counter_signal_bundles: Bundles from counter_signal sources.
            counter_signal_gaps: Gap reports for counter_signal sources that failed.
            required_classes: Which classes must be checked. If None, checks all
                            classes that have available bundles or gaps.

        Returns:
            List of CounterSignalResult, one per evaluated class.
        """
        results: list[CounterSignalResult] = []

        # Index bundles by counter_signal_class
        bundles_by_class: dict[str, list[EvidenceBundle]] = {}
        for bundle in counter_signal_bundles:
            # The counter_signal_class comes from the registry
            cs_class = bundle.query_context.get(
                "counter_signal_class", "unknown"
            )
            bundles_by_class.setdefault(cs_class, []).append(bundle)

        # Index gaps by counter_signal_class
        gaps_by_class: dict[str, list[GapReport]] = {}
        for gap in counter_signal_gaps:
            cs_class = gap.source_group  # Best approximation
            gaps_by_class.setdefault(cs_class, []).append(gap)

        # Determine which classes to evaluate
        classes_to_check = required_classes or list(
            set(bundles_by_class.keys()) | set(gaps_by_class.keys())
        )

        for cs_class in classes_to_check:
            class_bundles = bundles_by_class.get(cs_class, [])
            class_gaps = gaps_by_class.get(cs_class, [])
            allow_gap = self.allow_gaps.get(cs_class, False)

            if class_bundles:
                # We have data — check if any signal was found
                signal_found = any(
                    b.structured_extract.get("counter_signal_detected", False)
                    for b in class_bundles
                )
                signal_detail = None
                if signal_found:
                    # Find the first bundle with a detected signal
                    for b in class_bundles:
                        if b.structured_extract.get("counter_signal_detected"):
                            signal_detail = b.structured_extract.get(
                                "counter_signal_detail", "Signal detected"
                            )
                            break

                results.append(
                    CounterSignalResult(
                        counter_signal_class=cs_class,
                        source_id=class_bundles[0].source_id,
                        checked=True,
                        signal_found=signal_found,
                        signal_detail=signal_detail,
                        allow_gap=allow_gap,
                    )
                )

            elif class_gaps:
                # Separate gaps by kind
                absence_gaps = [g for g in class_gaps if g.gap_kind == GapKind.SIGNAL_ABSENCE]
                intelligence_gaps = [g for g in class_gaps if g.gap_kind == GapKind.INTELLIGENCE_GAP]

                if absence_gaps:
                    # Signal absence IS evidence: the source confirmed nothing is there
                    results.append(
                        CounterSignalResult(
                            counter_signal_class=cs_class,
                            source_id=absence_gaps[0].source_id,
                            checked=True,
                            signal_found=False,
                            signal_detail="Source responded: signal absent (evidential absence)",
                            allow_gap=allow_gap,
                        )
                    )
                else:
                    # Intelligence gap: could not check
                    results.append(
                        CounterSignalResult(
                            counter_signal_class=cs_class,
                            source_id=intelligence_gaps[0].source_id,
                            checked=False,
                            signal_found=False,
                            signal_detail=f"Source unavailable: {intelligence_gaps[0].reason.value}",
                            allow_gap=allow_gap,
                        )
                    )

            else:
                # No bundle and no gap — class not evaluated
                results.append(
                    CounterSignalResult(
                        counter_signal_class=cs_class,
                        source_id="none",
                        checked=False,
                        signal_found=False,
                        signal_detail="No source configured for this class",
                        allow_gap=allow_gap,
                    )
                )

        return results
