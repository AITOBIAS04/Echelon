"""Commitment Monitor — drift detection with impact assessment."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel


class DriftType(str, Enum):
    """Types of commitment drift detected during an investigation."""

    ENTITY_RESTRUCTURE = "entity_restructure"
    CONTRACT_AMENDMENT = "contract_amendment"
    MARKET_RULE_CHANGE = "market_rule_change"
    REGULATORY_STATUS_CHANGE = "regulatory_status_change"
    JURISDICTION_CHANGE = "jurisdiction_change"


class DriftImpact(str, Enum):
    """Impact classification for a drift event."""

    MATERIAL = "material"
    NON_MATERIAL = "non_material"


class DriftEvent(BaseModel):
    """Immutable drift event record."""

    model_config = {"frozen": True}

    drift_id: str
    drift_type: DriftType
    detected_at: datetime
    original_value: str
    new_value: str
    evidence_ref: str | None = None
    impact_assessment: DriftImpact


class CommitmentMonitor:
    """Monitor for commitment drift during an investigation.

    Tracks changes to the investigation target that may affect
    resolution integrity. Material drift triggers REVIEW_REQUIRED
    routing in the investigation certificate.
    """

    def __init__(self) -> None:
        self._events: list[DriftEvent] = []
        self._counter: int = 0

    def log_drift(
        self,
        drift_type: DriftType,
        original_value: str,
        new_value: str,
        impact_assessment: DriftImpact,
        evidence_ref: str | None = None,
    ) -> DriftEvent:
        """Log a drift event. Sequential IDs (D001, D002, ...)."""
        self._counter += 1
        drift_id = f"D{self._counter:03d}"

        event = DriftEvent(
            drift_id=drift_id,
            drift_type=drift_type,
            detected_at=datetime.utcnow(),
            original_value=original_value,
            new_value=new_value,
            evidence_ref=evidence_ref,
            impact_assessment=impact_assessment,
        )
        self._events.append(event)
        return event

    def add_event_from_persisted(
        self,
        drift_id: str,
        drift_type: DriftType,
        detected_at: datetime,
        original_value: str,
        new_value: str,
        evidence_ref: str | None,
        impact_assessment: str,
    ) -> DriftEvent:
        """Replay a persisted drift event into the monitor.

        Unlike log_drift(), this accepts pre-existing IDs and timestamps.
        Used for toolset rebuild from DB.
        """
        event = DriftEvent(
            drift_id=drift_id,
            drift_type=drift_type,
            detected_at=detected_at,
            original_value=original_value,
            new_value=new_value,
            evidence_ref=evidence_ref,
            impact_assessment=DriftImpact(impact_assessment),
        )
        self._events.append(event)
        try:
            num = int(drift_id.lstrip("D")) if drift_id.startswith("D") and drift_id[1:].isdigit() else None
        except (ValueError, IndexError):
            num = None
        if num is not None and num > self._counter:
            self._counter = num
        else:
            self._counter += 1
        return event

    def has_material_drift(self) -> bool:
        """True if any drift event has MATERIAL impact."""
        return any(
            e.impact_assessment == DriftImpact.MATERIAL for e in self._events
        )

    @property
    def events(self) -> list[DriftEvent]:
        return list(self._events)
