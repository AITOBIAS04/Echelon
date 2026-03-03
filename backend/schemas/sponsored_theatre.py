"""Pydantic v2 schemas for the Sponsored Theatre workflow.

Sponsor-facing configuration and review package models.
Cycle-012, Sprint 1 — Theatre Creation + Sponsor Onboarding.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.market.state import FeeSchedule


class SponsoredTheatreConfig(BaseModel):
    """Sponsor-provided configuration for a Sponsored Theatre.

    Validated at ingestion. All fields are frozen at commitment.
    """

    question: str = Field(
        ..., min_length=10, max_length=500,
        description="The Theatre question (e.g., 'Will Acme Ltd file annual accounts by 30 Sep 2026?')",
    )
    resolution_date: datetime = Field(
        ..., description="When the market resolves (UTC)",
    )
    committed_sources: list[str] = Field(
        ..., min_length=1,
        description="OSINT registry source IDs for settlement evidence",
    )
    outcome_labels: list[str] = Field(
        ..., min_length=2,
        description="Market outcome labels (e.g., ['Filed on time', 'Filed late', 'Not filed'])",
    )
    liquidity_b: Decimal = Field(
        ..., gt=Decimal("0"),
        description="LMSR b parameter — liquidity depth",
    )
    fee_schedule: FeeSchedule = Field(
        default_factory=FeeSchedule,
        description="Trade and resolution fee configuration",
    )
    sponsor_id: str = Field(
        ..., min_length=1,
        description="Sponsor identifier",
    )
    sponsor_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Freeform sponsor context (company name, jurisdiction, etc.)",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("outcome_labels")
    @classmethod
    def outcome_labels_must_be_unique(cls, v: list[str]) -> list[str]:
        """Reject duplicate outcome labels."""
        if len(v) != len(set(v)):
            raise ValueError("outcome_labels must be unique")
        return v

    @field_validator("outcome_labels")
    @classmethod
    def outcome_labels_max_10(cls, v: list[str]) -> list[str]:
        """Cap outcomes at 10."""
        if len(v) > 10:
            raise ValueError("outcome_labels must have at most 10 entries")
        return v


class SponsorReviewPackage(BaseModel):
    """Returned to sponsor for review before commitment approval.

    Contains everything the sponsor needs to verify the Theatre
    configuration, commitment hash, and worst-case financial exposure.
    """

    theatre_id: str
    template_json: dict[str, Any]
    commitment_hash: str
    worst_case_loss: float
    source_manifest: dict[str, Any]
    fee_schedule_breakdown: dict[str, Any]
    n_outcomes: int
    outcome_labels: list[str]
    liquidity_b: float
    resolution_date: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)
