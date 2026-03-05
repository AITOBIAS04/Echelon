"""Investigation Counter-Signal Feed — 11-class taxonomy separate from pipeline counter-signals."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class InvestigationCounterSignalClass(str, Enum):
    """11 investigation-specific counter-signal classes.

    Classes 1-9 are standard coverage classes.
    Classes 10-11 (MARKET_DIVERGENCE, WITNESS_SOURCE_RECANTATION) are event-driven only —
    they only count toward 'checked' when an instance is explicitly logged.
    """

    OFFICIAL_DENIAL = "official_denial"
    REGULATORY_CLEARANCE = "regulatory_clearance"
    FILING_CONTRADICTION = "filing_contradiction"
    COMPETING_ANALYSIS = "competing_analysis"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"
    SOURCE_RELIABILITY_DEGRADATION = "source_reliability_degradation"
    ENTITY_STATUS_CHANGE = "entity_status_change"
    JURISDICTIONAL_CONFLICT = "jurisdictional_conflict"
    RETRACTION_OR_CORRECTION = "retraction_or_correction"
    MARKET_DIVERGENCE = "market_divergence"
    WITNESS_SOURCE_RECANTATION = "witness_source_recantation"


# Classes that are event-driven only (not passive coverage)
_EVENT_DRIVEN_CLASSES = {
    InvestigationCounterSignalClass.MARKET_DIVERGENCE,
    InvestigationCounterSignalClass.WITNESS_SOURCE_RECANTATION,
}

# Standard coverage classes (1-9)
_STANDARD_CLASSES = {
    c for c in InvestigationCounterSignalClass if c not in _EVENT_DRIVEN_CLASSES
}


class InvestigationCounterSignal(BaseModel):
    """Immutable counter-signal record."""

    model_config = {"frozen": True}

    counter_signal_id: str
    signal_class: InvestigationCounterSignalClass
    detected_at: datetime
    evidence_ref: str | None = None
    material: bool
    resolution_impact: str
    detection_method: str  # "automated_osint" | "paradox_engine" | "human_submitted"


class InvestigationCounterSignalFeed:
    """Counter-signal feed for investigation-class inquiries.

    Classes 10+11 (MARKET_DIVERGENCE, WITNESS_SOURCE_RECANTATION) are event-driven:
    they only count toward 'checked' when an InvestigationCounterSignal instance
    for that class exists in the feed.
    """

    def __init__(self) -> None:
        self._signals: list[InvestigationCounterSignal] = []
        self._counter: int = 0

    def log_counter_signal(
        self,
        signal_class: InvestigationCounterSignalClass,
        material: bool,
        resolution_impact: str,
        detection_method: str,
        evidence_ref: str | None = None,
    ) -> InvestigationCounterSignal:
        """Log a counter-signal. Sequential IDs (CS001, CS002, ...)."""
        self._counter += 1
        cs_id = f"CS{self._counter:03d}"

        signal = InvestigationCounterSignal(
            counter_signal_id=cs_id,
            signal_class=signal_class,
            detected_at=datetime.now(timezone.utc),
            evidence_ref=evidence_ref,
            material=material,
            resolution_impact=resolution_impact,
            detection_method=detection_method,
        )
        self._signals.append(signal)
        return signal

    def get_summary(self) -> dict:
        """Returns {checked, gaps, material_contradictions}.

        'checked' = number of distinct classes that have at least one logged signal.
        Event-driven classes (10, 11) only count when explicitly logged.
        'gaps' = total classes (11) minus checked.
        'material_contradictions' = count of signals with material=True.
        """
        logged_classes = {s.signal_class for s in self._signals}
        checked = len(logged_classes)
        total_classes = len(InvestigationCounterSignalClass)
        material_count = sum(1 for s in self._signals if s.material)

        return {
            "checked": checked,
            "gaps": total_classes - checked,
            "material_contradictions": material_count,
        }

    def get_detail(self) -> list[dict]:
        """Per-signal detail for certificate inclusion."""
        return [
            {
                "counter_signal_id": s.counter_signal_id,
                "signal_class": s.signal_class.value,
                "detected_at": s.detected_at.isoformat(),
                "evidence_ref": s.evidence_ref,
                "material": s.material,
                "resolution_impact": s.resolution_impact,
                "detection_method": s.detection_method,
            }
            for s in self._signals
        ]

    @property
    def signals(self) -> list[InvestigationCounterSignal]:
        return list(self._signals)
