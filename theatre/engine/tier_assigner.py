"""Verification Tier Assigner — deterministic tier assignment per v0 rules.

Three tiers:
- UNVERIFIED: insufficient evidence or quality failures
- BACKTESTED: meets minimum evidence threshold
- PROVEN: extended history with production attestation
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel


class TierHistory(BaseModel):
    """Historical evidence for PROVEN tier consideration."""

    consecutive_months_backtested: int = 0
    has_production_telemetry: bool = False
    has_attestation: bool = False

    def meets_proven_requirements(self) -> bool:
        return (
            self.consecutive_months_backtested >= 3
            and self.has_production_telemetry
            and self.has_attestation
        )


class TierAssigner:
    """Deterministic verification tier assignment per v0 rules."""

    BACKTESTED_MIN_REPLAYS = 50
    BACKTESTED_EXPIRY_DAYS = 90
    PROVEN_MIN_MONTHS = 3
    PROVEN_EXPIRY_DAYS = 180
    MAX_FAILURE_RATE = 0.20

    @staticmethod
    def assign(
        replay_count: int,
        has_full_pins: bool,
        has_published_scores: bool,
        has_verifiable_hash: bool,
        has_disputes: bool,
        failure_rate: float,
        history: TierHistory | None = None,
    ) -> Literal["UNVERIFIED", "BACKTESTED", "PROVEN"]:
        """Assign tier based on evidence.

        UNVERIFIED: <50 replays OR missing pins OR incomplete evidence OR >20% failure
        BACKTESTED: >=50 + full pins + published scores + verifiable hash + no disputes
        PROVEN: BACKTESTED + >=3 months consecutive + production telemetry + attestation
        """
        if failure_rate > TierAssigner.MAX_FAILURE_RATE:
            return "UNVERIFIED"
        if replay_count < TierAssigner.BACKTESTED_MIN_REPLAYS:
            return "UNVERIFIED"
        if not (has_full_pins and has_published_scores and has_verifiable_hash):
            return "UNVERIFIED"
        if has_disputes:
            return "UNVERIFIED"

        # PROVEN requires additional history evidence
        if history and history.meets_proven_requirements():
            return "PROVEN"

        return "BACKTESTED"

    @staticmethod
    def compute_expiry(
        tier: str, issued_at: datetime
    ) -> datetime | None:
        """Compute certificate expiry based on tier."""
        if tier == "UNVERIFIED":
            return None
        if tier == "BACKTESTED":
            return issued_at + timedelta(days=TierAssigner.BACKTESTED_EXPIRY_DAYS)
        if tier == "PROVEN":
            return issued_at + timedelta(days=TierAssigner.PROVEN_EXPIRY_DAYS)
        return None
