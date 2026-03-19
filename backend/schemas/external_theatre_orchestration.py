"""Orchestration schemas for external theatre preparation pipeline.

Cycle 038b: External Theatre Orchestration.

Defines request/response/feedback Pydantic models for the orchestration
surface that composes 037d/037e/038a services into a single operational
path for external theatre repos.
"""

from typing import Optional

from pydantic import BaseModel, Field

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreScopeKey,
)


class ExternalTheatreInput(BaseModel):
    """Descriptor for a single external theatre to prepare."""

    construct_slug: str               # "tremor" | "corona"
    construct_version: str            # "0.1.0"
    construct_json: str               # Raw construct.json content (not path)
    construct_json_path: Optional[str] = None  # Optional: for feedback reporting


class ExternalTheatrePreparationRequest(BaseModel):
    """Full orchestration request."""

    theatres: list[ExternalTheatreInput]
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)
    certificate_id: Optional[str] = None


class ExtractionResult(BaseModel):
    """Result of fixture extraction for one theatre."""

    construct_slug: str
    success: bool
    settlement_fixture_count: int = 0
    oracle_fixture_count: int = 0
    has_calibration: bool = False
    functional_fixture_count: int = 0
    has_failure_scenarios: bool = False
    fallbacks_used: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class TheatrePreparationEntry(BaseModel):
    """Per-theatre preparation result within the orchestration."""

    construct_slug: str
    construct_version: str
    extraction: Optional[ExtractionResult] = None
    bundle: Optional[ExecutedTheatreComparisonBundle] = None
    execution_passed: bool = False
    execution_failed: bool = False
    error: Optional[str] = None


class BuilderFeedbackItem(BaseModel):
    """Single feedback item for external builder."""

    category: str          # "required" | "optional" | "extraction"
    field: str             # e.g. "verification_checks", "source_ids"
    status: str            # "present" | "missing" | "defaulted" | "enriched"
    message: str


class BuilderFeedbackReport(BaseModel):
    """Structured feedback for external theatre builder."""

    construct_slug: str
    required_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    optional_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    extraction_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    overall_readiness: str  # "READY" | "DEGRADED" | "BLOCKED"


class ExternalTheatrePreparationResult(BaseModel):
    """Complete orchestration result."""

    theatres: list[TheatrePreparationEntry] = Field(default_factory=list)
    candidates: list[ComparisonCandidateSet] = Field(default_factory=list)
    feedback: list[BuilderFeedbackReport] = Field(default_factory=list)
    event_keys_used: list[str] = Field(default_factory=list)
    scope_keys_used: list[TheatreScopeKey] = Field(default_factory=list)
    total_theatres: int = 0
    total_successful: int = 0
    total_failed: int = 0
