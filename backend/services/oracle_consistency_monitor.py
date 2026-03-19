"""OracleConsistencyMonitor — tracks oracle responses across theatres.

Cycle 038: Cross-Theatre Paradox Detection.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import OracleResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsistencyResult:
    """Result of a cross-theatre oracle consistency check."""

    is_consistent: bool
    source: str
    event_id: str
    responses: list[dict] = field(default_factory=list)
    max_delta: Optional[float] = None
    explanation: str = ""


@dataclass(frozen=True)
class DivergenceRecord:
    """A detected oracle divergence event."""

    source: str
    event_id: str
    theatre_ids: list[str] = field(default_factory=list)
    delta: float = 0.0
    detected_at: datetime = field(default_factory=datetime.utcnow)


class OracleConsistencyMonitor:
    """Tracks oracle responses across theatres for consistency.

    Records are created when theatres report oracle query results
    (typically at settlement time). Does not poll oracles directly.
    """

    def __init__(self, session: AsyncSession):
        self._db = session

    async def record_response(
        self,
        theatre_id: str,
        source: str,
        event_id: str,
        value_json: dict,
        queried_at: datetime,
        is_provisional: bool = False,
    ) -> OracleResponse:
        """Record an oracle response. Idempotent on (theatre_id, source, event_id).

        If a response already exists for the triple, updates value_json,
        queried_at, and is_provisional fields.
        """
        result = await self._db.execute(
            select(OracleResponse).where(
                OracleResponse.theatre_id == theatre_id,
                OracleResponse.source == source,
                OracleResponse.event_id == event_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.value_json = value_json
            existing.queried_at = queried_at
            existing.is_provisional = is_provisional
            await self._db.flush()
            logger.debug(
                "Updated OracleResponse for %s/%s (theatre=%s)",
                source, event_id, theatre_id,
            )
            return existing

        response = OracleResponse(
            theatre_id=theatre_id,
            source=source,
            event_id=event_id,
            value_json=value_json,
            queried_at=queried_at,
            is_provisional=is_provisional,
        )
        self._db.add(response)
        await self._db.flush()
        logger.info(
            "Recorded OracleResponse for %s/%s (theatre=%s, provisional=%s)",
            source, event_id, theatre_id, is_provisional,
        )
        return response

    async def check_consistency(
        self,
        source: str,
        event_id: str,
    ) -> ConsistencyResult:
        """Check if all theatres that queried (source, event_id) agree.

        Compares value_json across all responses for the same (source, event_id).
        If all value_json dicts are identical, returns consistent.
        Otherwise computes max delta from numeric fields if possible.
        """
        result = await self._db.execute(
            select(OracleResponse).where(
                OracleResponse.source == source,
                OracleResponse.event_id == event_id,
            )
        )
        responses = list(result.scalars().all())

        if len(responses) <= 1:
            return ConsistencyResult(
                is_consistent=True,
                source=source,
                event_id=event_id,
                responses=[self._response_to_dict(r) for r in responses],
                max_delta=None,
                explanation="Single or no responses — trivially consistent",
            )

        response_dicts = [self._response_to_dict(r) for r in responses]

        # Check if all value_json are identical
        first_value = responses[0].value_json
        all_identical = all(r.value_json == first_value for r in responses[1:])

        if all_identical:
            return ConsistencyResult(
                is_consistent=True,
                source=source,
                event_id=event_id,
                responses=response_dicts,
                max_delta=0.0,
                explanation="All responses identical",
            )

        # Compute max delta from numeric fields
        max_delta = self._compute_max_delta(responses)
        return ConsistencyResult(
            is_consistent=False,
            source=source,
            event_id=event_id,
            responses=response_dicts,
            max_delta=max_delta,
            explanation=f"Divergence detected across {len(responses)} responses (max_delta={max_delta})",
        )

    async def get_divergence_history(
        self,
        source: str,
        window_hours: int = 168,
    ) -> list[DivergenceRecord]:
        """Get recent divergence events for a source (default: 7 days).

        Groups responses by event_id and identifies those with differing values.
        """
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        result = await self._db.execute(
            select(OracleResponse).where(
                OracleResponse.source == source,
                OracleResponse.queried_at >= cutoff,
            ).order_by(OracleResponse.event_id, OracleResponse.queried_at)
        )
        all_responses = list(result.scalars().all())

        # Group by event_id
        by_event: dict[str, list[OracleResponse]] = {}
        for r in all_responses:
            by_event.setdefault(r.event_id, []).append(r)

        divergences: list[DivergenceRecord] = []
        for eid, group in by_event.items():
            if len(group) < 2:
                continue
            first_value = group[0].value_json
            if any(r.value_json != first_value for r in group[1:]):
                delta = self._compute_max_delta(group)
                divergences.append(
                    DivergenceRecord(
                        source=source,
                        event_id=eid,
                        theatre_ids=[r.theatre_id for r in group],
                        delta=delta or 0.0,
                        detected_at=max(r.queried_at for r in group),
                    )
                )

        return divergences

    @staticmethod
    def _response_to_dict(r: OracleResponse) -> dict:
        return {
            "theatre_id": r.theatre_id,
            "value": r.value_json,
            "queried_at": r.queried_at.isoformat() if r.queried_at else None,
            "is_provisional": r.is_provisional,
        }

    @staticmethod
    def _compute_max_delta(responses: list[OracleResponse]) -> Optional[float]:
        """Compute max delta from numeric fields in value_json."""
        numeric_keys: set[str] = set()
        for r in responses:
            if isinstance(r.value_json, dict):
                for k, v in r.value_json.items():
                    if isinstance(v, (int, float)):
                        numeric_keys.add(k)

        if not numeric_keys:
            return None

        max_delta = 0.0
        for key in numeric_keys:
            values = []
            for r in responses:
                if isinstance(r.value_json, dict) and key in r.value_json:
                    val = r.value_json[key]
                    if isinstance(val, (int, float)):
                        values.append(float(val))
            if len(values) >= 2:
                delta = max(values) - min(values)
                max_delta = max(max_delta, delta)

        return max_delta
