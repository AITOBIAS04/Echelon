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


class RunListItem(BaseModel):
    """List item for GET .../runs."""
    run_number: int
    investigation_id: str
    status: str
    episode_count: int
    started_at: Optional[datetime] = None


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
    # Contract-backed fields (cycle-037, nullable for pre-037 runs)
    contract_hash: Optional[str] = None
    spec_hash: Optional[str] = None
    issuance_status: str = "READY"
    check_plan: Optional["CheckPlanSchema"] = None
    remediation: Optional["RemediationSchema"] = None


class SojuPayloadResponse(BaseModel):
    """Certificate formatted for Soju's POST endpoint."""
    verification_tier: str
    certificate_json: dict


# ── Contracts (Cycle 037) ──

class CreateContractRequest(BaseModel):
    """POST .../contract request body."""
    yaml_content: str = Field(..., description="Raw construct.yaml content")
    corpus_contents: Optional[list[str]] = Field(
        None,
        description="Raw corpus file contents (frontmatter + markdown). "
        "Parsed into CorpusSkills for security check planning.",
    )


class NormalizedClaimSchema(BaseModel):
    """Classified domain claim."""
    domain: str
    original: str
    is_vague: bool
    matched_category: Optional[str] = None
    vagueness_reason: Optional[str] = None


class RefusalSchema(BaseModel):
    """Explicit refusal declaration."""
    scope: str
    reason: str


class PlannedCheckSchema(BaseModel):
    """Planned evaluation check."""
    check_id: str
    check_type: str
    domain: str
    source: str
    critical: bool
    asset_id: Optional[str] = None
    anchor_class: Optional[str] = None


class ContractResponse(BaseModel):
    """Contract response."""
    id: str
    construct_registration_id: str
    spec_hash: str
    contract_hash: str
    normalized_claims: list[NormalizedClaimSchema]
    explicit_refusals: list[RefusalSchema]
    planned_checks: list[PlannedCheckSchema]
    tier_cap: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class ContractListResponse(BaseModel):
    """List of contracts."""
    contracts: list[ContractResponse]
    total: int


class CheckPlanEntrySchema(BaseModel):
    """Individual check in a check plan."""
    id: str
    type: str
    status: str
    score: Optional[float] = None
    reason: Optional[str] = None


class CheckPlanSchema(BaseModel):
    """Planned-vs-executed check plan in certificate."""
    total_planned: int
    total_executed: int
    checks: list[CheckPlanEntrySchema]


class RemediationSchema(BaseModel):
    """Machine-readable remediation payload for DEFERRED certificates."""
    status: str
    reason: str
    missing_checks: list[dict]
    executed_count: int
    planned_count: int
    recommendation: str
