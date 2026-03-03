"""Counter-Signal Evaluator — Stage 2b of the evidence pipeline.

Scaffolding-only in Cycle-011. Full interface and discount rule engine
implemented, but all 11 counter-signal classes return UNAVAILABLE with
allow_gap=True (no independent sources connected).

UNAVAILABLE is classified as INTELLIGENCE_GAP (not ABSENT) per AC-1
GapKind semantics. The criterion passes honestly under gap tolerance.

Three classes documented as first targets for future sources:
    infrastructure_outage, weather, financial_distress
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.osint.models.evidence import CollectionResult


class CounterSignalOutcome(str, Enum):
    """Outcome of a single counter-signal evaluation.

    ABSENT: checked and definitively not present.
    PRESENT_DISCOUNTED: present but explained/discounted.
    PRESENT_UNEXPLAINED: present and unexplained -- causes criterion FAIL.
    UNAVAILABLE: cannot be checked (INTELLIGENCE_GAP, not ABSENT).
    """

    ABSENT = "absent"
    PRESENT_DISCOUNTED = "present_discounted"
    PRESENT_UNEXPLAINED = "present_unexplained"
    UNAVAILABLE = "unavailable"


@dataclass
class CounterSignalResult:
    """Result of evaluating one counter-signal class.

    Attributes:
        signal_class: Name of the counter-signal class evaluated.
        outcome: One of the four CounterSignalOutcome values.
        source_id: Source that provided the signal (None if UNAVAILABLE).
        detail: Human-readable explanation.
        allow_gap: If True, UNAVAILABLE does not cause criterion FAIL.
            When False, UNAVAILABLE is treated as a hard requirement
            failure. Default True for 011 scaffolding.
    """

    signal_class: str
    outcome: CounterSignalOutcome
    source_id: str | None
    detail: str
    allow_gap: bool = True


# ── All 11 counter-signal classes ──────────────────────────────────
#
# Three marked as future targets (first sources to connect):
#   - infrastructure_outage
#   - weather
#   - financial_distress

COUNTER_SIGNAL_CLASSES: list[str] = [
    "infrastructure_outage",         # Future target #1
    "weather",                       # Future target #2
    "financial_distress",            # Future target #3
    "political_transition",
    "sanctions_change",
    "military_mobilisation",
    "cyber_attack",
    "pandemic_outbreak",
    "natural_disaster",
    "social_unrest",
    "regulatory_change",
]


class CounterSignalEvaluator:
    """Stage 2b: evaluate counter-signal classes against evidence.

    In Cycle-011 all 11 classes return UNAVAILABLE (INTELLIGENCE_GAP)
    because no independent counter-signal sources are connected.
    The criterion passes honestly under gap tolerance (allow_gap=True).
    """

    def evaluate(
        self,
        collection_results: list[CollectionResult],
        oracle_config: dict,
    ) -> list[CounterSignalResult]:
        """Evaluate all counter-signal classes.

        In 011, all classes return UNAVAILABLE with allow_gap=True.
        Future cycles will implement class-specific detection logic.

        Args:
            collection_results: CollectionResult list from Stage 1.
            oracle_config: Theatre oracle config dict (unused in 011).

        Returns:
            List of 11 CounterSignalResult, one per class.
        """
        results: list[CounterSignalResult] = []
        for signal_class in COUNTER_SIGNAL_CLASSES:
            results.append(
                CounterSignalResult(
                    signal_class=signal_class,
                    outcome=CounterSignalOutcome.UNAVAILABLE,
                    source_id=None,
                    detail=(
                        f"INTELLIGENCE_GAP: no independent source connected "
                        f"for counter-signal class '{signal_class}'"
                    ),
                    allow_gap=True,
                )
            )
        return results

    @staticmethod
    def check_criterion(
        results: list[CounterSignalResult],
    ) -> tuple[bool, str]:
        """Evaluate pass/fail criterion across all counter-signal results.

        Rules:
            - ABSENT: pass (signal checked, not present)
            - PRESENT_DISCOUNTED: pass (signal present but explained)
            - PRESENT_UNEXPLAINED: FAIL (signal present, unexplained)
            - UNAVAILABLE with allow_gap=True: pass (intelligence gap tolerated)
            - UNAVAILABLE with allow_gap=False: FAIL (hard requirement)

        Returns:
            Tuple of (passed: bool, detail: str).
        """
        failures: list[str] = []
        for result in results:
            if result.outcome == CounterSignalOutcome.PRESENT_UNEXPLAINED:
                failures.append(
                    f"{result.signal_class}: PRESENT_UNEXPLAINED — {result.detail}"
                )
            elif (
                result.outcome == CounterSignalOutcome.UNAVAILABLE
                and not result.allow_gap
            ):
                failures.append(
                    f"{result.signal_class}: UNAVAILABLE with allow_gap=False"
                )

        if failures:
            return False, f"Counter-signal criterion FAIL: {'; '.join(failures)}"
        return True, "Counter-signal criterion PASS"
