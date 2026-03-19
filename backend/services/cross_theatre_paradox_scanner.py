"""
CrossTheatreParadoxScanner — Detects coherence failures across theatres sharing FactAnchors.

Cycle 038: Cross-Theatre Paradox Detection.

Four detection patterns:
1. Settlement divergence — opposite outcomes for same event
2. Oracle inconsistency — same source, different values
3. Scope overlap gap — expected correlated event absent
4. Temporal drift — settlement timing exceeds window
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    CrossTheatreParadox,
    CrossTheatreParadoxSeverity,
    CrossTheatreParadoxStatus,
    CrossTheatreParadoxType,
    FactAnchor,
    FactAnchorLink,
    CoherenceGroup,
    CoherenceGroupMember,
    OracleResponse,
    WingFlap,
    WingFlapType,
)

logger = logging.getLogger(__name__)


def _order_theatres(theatre_a_id: str, theatre_b_id: str) -> tuple[str, str]:
    """Enforce lexicographic ordering for dedup: theatre_a < theatre_b."""
    if theatre_a_id <= theatre_b_id:
        return theatre_a_id, theatre_b_id
    return theatre_b_id, theatre_a_id


def _link_provenance(link_a, link_b) -> dict:
    """Snapshot link-quality provenance for paradox evidence_json."""
    return {
        "link_a_confidence": getattr(link_a, "link_confidence", None),
        "link_a_type": getattr(link_a, "link_type", None),
        "link_b_confidence": getattr(link_b, "link_confidence", None),
        "link_b_type": getattr(link_b, "link_type", None),
    }


class CrossTheatreParadoxScanner:
    """Detects coherence failures across theatres sharing FactAnchors."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def scan_fact_anchor(
        self, anchor_id: str,
    ) -> list[CrossTheatreParadox]:
        """Scan a FactAnchor for cross-theatre paradoxes.

        Triggered when a new theatre link is added to an existing anchor.
        Evaluates all pairwise comparisons between linked theatres.
        """
        result = await self._db.execute(
            select(FactAnchor).where(FactAnchor.id == anchor_id)
        )
        anchor = result.scalars().first()
        if anchor is None:
            return []

        link_result = await self._db.execute(
            select(FactAnchorLink).where(FactAnchorLink.fact_anchor_id == anchor_id)
        )
        links = list(link_result.scalars().all())
        if len(links) < 2:
            return []

        paradoxes = []
        for i in range(len(links)):
            for j in range(i + 1, len(links)):
                link_a, link_b = links[i], links[j]

                # Settlement divergence
                p = await self.evaluate_settlement_divergence(anchor, link_a, link_b)
                if p is not None:
                    paradoxes.append(p)

                # Oracle inconsistency
                p = await self.evaluate_oracle_inconsistency(anchor, link_a, link_b)
                if p is not None:
                    paradoxes.append(p)

                # Temporal drift
                p = await self.evaluate_temporal_drift(anchor, link_a, link_b)
                if p is not None:
                    paradoxes.append(p)

        # WingFlap + WebSocket for MATERIAL+ paradoxes
        for paradox in paradoxes:
            if paradox.severity in (
                CrossTheatreParadoxSeverity.MATERIAL,
                CrossTheatreParadoxSeverity.CRITICAL,
            ):
                await _record_wingflap(self._db, paradox.theatre_a_id, paradox)
                await _record_wingflap(self._db, paradox.theatre_b_id, paradox)
                await _broadcast_cross_theatre_paradox(paradox)

        return paradoxes

    async def scan_coherence_group(
        self, group_id: str,
    ) -> list[CrossTheatreParadox]:
        """Scan a CoherenceGroup for scope overlap gaps."""
        result = await self._db.execute(
            select(CoherenceGroup).where(CoherenceGroup.id == group_id)
        )
        group = result.scalars().first()
        if group is None:
            return []

        member_result = await self._db.execute(
            select(CoherenceGroupMember).where(
                CoherenceGroupMember.coherence_group_id == group_id
            )
        )
        members = list(member_result.scalars().all())
        if len(members) < 2:
            return []

        # Get all anchors linked to any member theatre
        member_theatre_ids = [m.theatre_id for m in members]
        anchor_links_result = await self._db.execute(
            select(FactAnchorLink).where(
                FactAnchorLink.theatre_id.in_(member_theatre_ids)
            )
        )
        all_links = list(anchor_links_result.scalars().all())

        # Group links by anchor_id
        anchor_to_theatres: dict[str, set[str]] = {}
        anchor_to_link: dict[str, FactAnchorLink] = {}
        for link in all_links:
            anchor_to_theatres.setdefault(link.fact_anchor_id, set()).add(link.theatre_id)
            anchor_to_link[link.fact_anchor_id] = link

        paradoxes = []
        primary_theatre_ids = {m.theatre_id for m in members if m.role == "primary"}

        for anchor_id, linked_theatres in anchor_to_theatres.items():
            # Check if any primary member is missing a link
            missing = primary_theatre_ids - linked_theatres
            if missing:
                # Load anchor for scope overlap check
                anchor_result = await self._db.execute(
                    select(FactAnchor).where(FactAnchor.id == anchor_id)
                )
                anchor = anchor_result.scalars().first()
                if anchor is None:
                    continue

                p = await self.evaluate_scope_overlap(group, anchor)
                if p is not None:
                    paradoxes.append(p)

        return paradoxes

    async def evaluate_settlement_divergence(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Compare two theatres' settlements for the same anchor."""
        theatre_a_id, theatre_b_id = _order_theatres(
            link_a.theatre_id, link_b.theatre_id
        )

        # Dedup: check existing OPEN record
        existing = await self._check_existing(
            anchor.id, theatre_a_id, theatre_b_id,
            CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE,
        )
        if existing is not None:
            return None

        # Compare link metadata for outcome divergence
        # link_type "settlement" links carry outcome in linked_entity_type
        if link_a.link_type != "settlement" or link_b.link_type != "settlement":
            return None

        outcome_a = link_a.linked_entity_type
        outcome_b = link_b.linked_entity_type

        if outcome_a == outcome_b:
            return None  # Same outcome, no paradox

        severity = CrossTheatreParadoxSeverity.MATERIAL

        description = (
            f"Settlement divergence: theatre {theatre_a_id} resolved "
            f"'{outcome_a}' vs theatre {theatre_b_id} resolved '{outcome_b}' "
            f"for anchor {anchor.external_source}:{anchor.external_id}"
        )

        evidence = {
            "theatre_a_outcome": outcome_a,
            "theatre_b_outcome": outcome_b,
            "anchor_type": anchor.anchor_type,
            "external_source": anchor.external_source,
            "external_id": anchor.external_id,
            **_link_provenance(link_a, link_b),
        }

        return await self._create_paradox(
            anchor_id=anchor.id,
            paradox_type=CrossTheatreParadoxType.SETTLEMENT_DIVERGENCE,
            severity=severity,
            theatre_a_id=theatre_a_id,
            theatre_b_id=theatre_b_id,
            description=description,
            evidence_json=evidence,
        )

    async def evaluate_oracle_inconsistency(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Compare oracle responses for same event across theatres."""
        theatre_a_id, theatre_b_id = _order_theatres(
            link_a.theatre_id, link_b.theatre_id
        )

        existing = await self._check_existing(
            anchor.id, theatre_a_id, theatre_b_id,
            CrossTheatreParadoxType.ORACLE_INCONSISTENCY,
        )
        if existing is not None:
            return None

        # Get oracle responses for both theatres matching the anchor's event
        responses_a = await self._get_oracle_responses(theatre_a_id, anchor.external_id)
        responses_b = await self._get_oracle_responses(theatre_b_id, anchor.external_id)

        if not responses_a or not responses_b:
            return None

        resp_a = responses_a[0]
        resp_b = responses_b[0]

        # Check provisional revision rule
        if self._is_provisional_revision(resp_a, resp_b):
            severity = CrossTheatreParadoxSeverity.INFO
            description = (
                f"Oracle provisional revision: {resp_a.source} for event "
                f"{anchor.external_id} — provisional→reviewed lifecycle, not material"
            )
            evidence = {
                "source": resp_a.source,
                "event_id": anchor.external_id,
                "theatre_a_provisional": resp_a.is_provisional,
                "theatre_b_provisional": resp_b.is_provisional,
                "revision_lifecycle": True,
                **_link_provenance(link_a, link_b),
            }
            return await self._create_paradox(
                anchor_id=anchor.id,
                paradox_type=CrossTheatreParadoxType.ORACLE_INCONSISTENCY,
                severity=severity,
                theatre_a_id=theatre_a_id,
                theatre_b_id=theatre_b_id,
                description=description,
                evidence_json=evidence,
            )

        # Compute delta between oracle values
        delta = self._compute_oracle_delta(resp_a.value_json, resp_b.value_json)
        if delta is None or delta == 0.0:
            return None

        # Same source vs cross-source
        same_source = resp_a.source == resp_b.source
        tolerance = 0.1  # Default threshold

        if delta <= tolerance:
            return None

        severity = (
            CrossTheatreParadoxSeverity.MATERIAL if same_source
            else CrossTheatreParadoxSeverity.WATCH
        )

        description = (
            f"Oracle inconsistency: delta={delta:.3f} for event "
            f"{anchor.external_id} between theatres {theatre_a_id} and {theatre_b_id}"
            f" ({'same source' if same_source else 'cross-source'})"
        )

        evidence = {
            "source_a": resp_a.source,
            "source_b": resp_b.source,
            "event_id": anchor.external_id,
            "delta": delta,
            "tolerance": tolerance,
            "same_source": same_source,
            **_link_provenance(link_a, link_b),
        }

        return await self._create_paradox(
            anchor_id=anchor.id,
            paradox_type=CrossTheatreParadoxType.ORACLE_INCONSISTENCY,
            severity=severity,
            theatre_a_id=theatre_a_id,
            theatre_b_id=theatre_b_id,
            description=description,
            evidence_json=evidence,
        )

    async def evaluate_temporal_drift(
        self,
        anchor: FactAnchor,
        link_a: FactAnchorLink,
        link_b: FactAnchorLink,
    ) -> Optional[CrossTheatreParadox]:
        """Check if settlement timing diverges significantly."""
        theatre_a_id, theatre_b_id = _order_theatres(
            link_a.theatre_id, link_b.theatre_id
        )

        existing = await self._check_existing(
            anchor.id, theatre_a_id, theatre_b_id,
            CrossTheatreParadoxType.TEMPORAL_DRIFT,
        )
        if existing is not None:
            return None

        time_a = link_a.created_at
        time_b = link_b.created_at
        if time_a is None or time_b is None:
            return None

        delta_hours = abs((time_a - time_b).total_seconds()) / 3600.0
        window = 24.0  # Default temporal drift window in hours

        if delta_hours <= window:
            return None

        severity = (
            CrossTheatreParadoxSeverity.WATCH if delta_hours > 2 * window
            else CrossTheatreParadoxSeverity.INFO
        )

        description = (
            f"Temporal drift: {delta_hours:.1f}h between theatres "
            f"{theatre_a_id} and {theatre_b_id} (window={window}h)"
        )

        evidence = {
            "delta_hours": round(delta_hours, 2),
            "window_hours": window,
            "time_a": time_a.isoformat() if time_a else None,
            "time_b": time_b.isoformat() if time_b else None,
            **_link_provenance(link_a, link_b),
        }

        return await self._create_paradox(
            anchor_id=anchor.id,
            paradox_type=CrossTheatreParadoxType.TEMPORAL_DRIFT,
            severity=severity,
            theatre_a_id=theatre_a_id,
            theatre_b_id=theatre_b_id,
            description=description,
            evidence_json=evidence,
        )

    async def evaluate_scope_overlap(
        self,
        group: CoherenceGroup,
        anchor: FactAnchor,
    ) -> Optional[CrossTheatreParadox]:
        """Check if coherence group members all have links for an anchor."""
        # Get primary members
        member_result = await self._db.execute(
            select(CoherenceGroupMember).where(
                CoherenceGroupMember.coherence_group_id == group.id,
                CoherenceGroupMember.role == "primary",
            )
        )
        members = list(member_result.scalars().all())
        if len(members) < 2:
            return None

        # Check which members have links to this anchor
        member_theatre_ids = [m.theatre_id for m in members]
        link_result = await self._db.execute(
            select(FactAnchorLink).where(
                FactAnchorLink.fact_anchor_id == anchor.id,
                FactAnchorLink.theatre_id.in_(member_theatre_ids),
            )
        )
        links = list(link_result.scalars().all())
        linked_theatres = {link.theatre_id for link in links}
        missing = set(member_theatre_ids) - linked_theatres

        if not missing:
            return None

        # Use first linked and first missing for the pair
        present_list = sorted(linked_theatres)
        missing_list = sorted(missing)
        theatre_a_id, theatre_b_id = _order_theatres(
            present_list[0], missing_list[0]
        )

        existing = await self._check_existing(
            anchor.id, theatre_a_id, theatre_b_id,
            CrossTheatreParadoxType.SCOPE_OVERLAP_GAP,
        )
        if existing is not None:
            return None

        severity = CrossTheatreParadoxSeverity.WATCH

        description = (
            f"Scope overlap gap: theatre(s) {', '.join(missing_list)} in group "
            f"'{group.name}' missing link to anchor "
            f"{anchor.external_source}:{anchor.external_id}"
        )

        # Build link provenance from present links
        present_link_provenance = {
            link.theatre_id: {
                "confidence": getattr(link, "link_confidence", None),
                "link_type": getattr(link, "link_type", None),
            }
            for link in links
        }

        evidence = {
            "group_id": group.id,
            "group_name": group.name,
            "missing_theatres": missing_list,
            "present_theatres": present_list,
            "anchor_type": anchor.anchor_type,
            "present_link_provenance": present_link_provenance,
        }

        return await self._create_paradox(
            anchor_id=anchor.id,
            paradox_type=CrossTheatreParadoxType.SCOPE_OVERLAP_GAP,
            severity=severity,
            theatre_a_id=theatre_a_id,
            theatre_b_id=theatre_b_id,
            description=description,
            evidence_json=evidence,
            coherence_group_id=group.id,
        )

    def _is_provisional_revision(
        self,
        response_a: OracleResponse,
        response_b: OracleResponse,
    ) -> bool:
        """Context_038 rule: provisional oracle revision is INFO, not MATERIAL."""
        if response_a.source != response_b.source:
            return False
        return response_a.is_provisional != response_b.is_provisional

    @staticmethod
    def _compute_oracle_delta(value_a: dict, value_b: dict) -> Optional[float]:
        """Compute max delta between two oracle value_json dicts."""
        max_delta = 0.0
        found = False
        for key in set(value_a.keys()) | set(value_b.keys()):
            try:
                va = float(value_a.get(key, 0))
                vb = float(value_b.get(key, 0))
                delta = abs(va - vb)
                if delta > max_delta:
                    max_delta = delta
                found = True
            except (TypeError, ValueError):
                continue
        return max_delta if found else None

    async def _check_existing(
        self,
        anchor_id: str,
        theatre_a_id: str,
        theatre_b_id: str,
        paradox_type: CrossTheatreParadoxType,
    ) -> Optional[CrossTheatreParadox]:
        """Check for existing OPEN paradox with same key fields."""
        result = await self._db.execute(
            select(CrossTheatreParadox).where(
                CrossTheatreParadox.fact_anchor_id == anchor_id,
                CrossTheatreParadox.theatre_a_id == theatre_a_id,
                CrossTheatreParadox.theatre_b_id == theatre_b_id,
                CrossTheatreParadox.paradox_type == paradox_type,
                CrossTheatreParadox.resolution_status == CrossTheatreParadoxStatus.OPEN,
            )
        )
        return result.scalars().first()

    async def _create_paradox(
        self,
        anchor_id: str,
        paradox_type: CrossTheatreParadoxType,
        severity: CrossTheatreParadoxSeverity,
        theatre_a_id: str,
        theatre_b_id: str,
        description: str,
        evidence_json: dict,
        coherence_group_id: Optional[str] = None,
    ) -> CrossTheatreParadox:
        """Create and persist a CrossTheatreParadox record."""
        paradox = CrossTheatreParadox(
            id=str(uuid4()),
            fact_anchor_id=anchor_id,
            coherence_group_id=coherence_group_id,
            paradox_type=paradox_type,
            severity=severity,
            theatre_a_id=theatre_a_id,
            theatre_b_id=theatre_b_id,
            description=description,
            evidence_json=evidence_json,
            resolution_status=CrossTheatreParadoxStatus.OPEN,
        )
        self._db.add(paradox)
        await self._db.flush()

        logger.info(
            "Cross-theatre paradox detected: %s %s between %s and %s (severity=%s)",
            paradox_type.value, anchor_id, theatre_a_id, theatre_b_id, severity.value,
        )

        return paradox

    async def _get_oracle_responses(
        self, theatre_id: str, event_id: str,
    ) -> list[OracleResponse]:
        """Get oracle responses for a theatre and event."""
        result = await self._db.execute(
            select(OracleResponse).where(
                OracleResponse.theatre_id == theatre_id,
                OracleResponse.event_id == event_id,
            )
        )
        return list(result.scalars().all())


async def _record_wingflap(
    db: AsyncSession,
    theatre_id: str,
    paradox: CrossTheatreParadox,
) -> None:
    """Create a WingFlap for cross-theatre paradox."""
    flap = WingFlap(
        id=str(uuid4()),
        timeline_id=theatre_id,
        agent_id="SYSTEM",
        flap_type=WingFlapType.CROSS_THEATRE_PARADOX,
        action=f"Cross-theatre {paradox.paradox_type.value}: {paradox.description[:200]}",
        stability_delta=-0.15,
        direction="DESTABILISE",
        volume_usd=0.0,
        timeline_stability=0.0,
        timeline_price=0.0,
    )
    db.add(flap)


async def _broadcast_cross_theatre_paradox(paradox: CrossTheatreParadox) -> None:
    """Broadcast CROSS_THEATRE_PARADOX_DETECTED via WebSocket."""
    try:
        from backend.websockets.realtime_manager import manager as ws_manager

        await ws_manager.broadcast_cross_theatre_paradox(
            paradox_id=paradox.id,
            paradox_type=paradox.paradox_type.value,
            severity=paradox.severity.value,
            theatre_a_id=paradox.theatre_a_id,
            theatre_b_id=paradox.theatre_b_id,
            fact_anchor_id=paradox.fact_anchor_id,
            description=paradox.description[:200],
        )
    except Exception:
        logger.exception("Failed to broadcast cross-theatre paradox %s", paradox.id)
