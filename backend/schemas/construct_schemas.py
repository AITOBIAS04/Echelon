"""Pydantic schemas for Construct Verification API.

Request/response models for registration, runs, episodes, and certificates.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Registration ──

class ConstructRegistrationRequest(BaseModel):
    """POST /api/constructs/register request body."""
    slug: str = Field(..., max_length=64, description="Construct slug (e.g., 'artisan')")
    version: str = Field(..., max_length=32, description="Semver version (e.g., '1.4.0')")
    content_hash: str = Field(..., description="SHA-256 hash with 'sha256:' prefix")
    skill_manifest: list[dict] = Field(..., description="List of {command, domain} entries")
    domain_claims: list[str] = Field(..., description="Declared domain coverage")
    test_prompts_hash: str = Field(..., description="SHA-256 hash of committed test prompts")
    rubric_hash: str = Field(..., description="SHA-256 hash of committed rubric definitions")


class ConstructRegistrationResponse(BaseModel):
    """Registration response."""
    id: str
    slug: str
    version: str
    status: str
    commitment_hash: str
    skill_count: int
    created_at: Optional[datetime] = None


class ConstructRegistrationListItem(BaseModel):
    """List item for GET /api/constructs."""
    slug: str
    version: str
    status: str
    skill_count: int
    commitment_hash: str


# ── Runs ──

class CreateRunResponse(BaseModel):
    """POST .../runs response."""
    investigation_id: str
    run_number: int
    status: str
    construct_id: str


class EpisodeCaptureRequest(BaseModel):
    """POST .../episodes request body."""
    skill_command: str
    domain: str
    prompt_index: int
    output_text: str
    timing_ms: int = Field(ge=0)


class EpisodeCaptureResponse(BaseModel):
    """POST .../episodes response."""
    evidence_id: str
    content_hash: str
    prompt_index: int


class EpisodeDetail(BaseModel):
    """Episode entry in run detail response."""
    prompt_index: int
    skill_command: str
    domain: str
    timing_ms: int
    content_hash: str
    scores: dict[str, float] = Field(default_factory=dict)
    submitted_at: Optional[datetime] = None


class RunDetailResponse(BaseModel):
    """GET .../runs/:runNumber response with per-episode activity."""
    run_number: int
    investigation_id: str
    status: str
    registration: dict
    commitment_hash: str
    episodes: list[EpisodeDetail]
    domain_coverage: dict[str, int]
    skill_coverage: dict[str, int]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ── Certificates ──

class CertificateResponse(BaseModel):
    """GET .../certificate response."""
    certificate_id: str
    construct_slug: str
    construct_version: str
    composite_score: float
    domain_scores: dict[str, float]
    skill_coverage: float
    verification_tier: str
    verdict: str
    routing_decision: str
    evidence_bundle_hash: str
    episode_count: int


class SojuPayloadResponse(BaseModel):
    """Certificate formatted for Soju's POST endpoint."""
    verification_tier: str
    certificate_json: dict
