"""Pydantic schemas for Multi-Evaluator Orchestration (Cycle 037b).

Data models for residual dimension scoring, evaluator score records,
per-dimension convergence, and run-level convergence summaries.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Evaluator Score Records ──

class EvaluatorScoreRecord(BaseModel):
    """Per-evaluator, per-dimension score from a residual scorer."""
    evaluator_id: str
    dimension: str
    verdict: Literal["PASS", "FAIL", "ABSTAIN"]
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    rationale: Optional[str] = None
    raw_output: Optional[dict] = None


# ── Per-Dimension Convergence ──

class DimensionConvergence(BaseModel):
    """Convergence outcome for a single residual dimension."""
    dimension: str
    outcome: Literal["CONVERGED_PASS", "CONVERGED_FAIL", "DIVERGENT", "SKIPPED"]
    evaluator_ids: list[str]
    verdicts: list[str]
    scores: list[Optional[float]] = Field(default_factory=list)
    confidence: Optional[Literal["HIGH", "LOWER"]] = None


# ── Run-Level Convergence Summary ──

class RunConvergenceSummary(BaseModel):
    """Run-level summary of multi-evaluator convergence."""
    evaluator_ids: list[str]
    total_dimensions: int
    converged_pass: int = 0
    converged_fail: int = 0
    divergent: int = 0
    skipped: int = 0
    escalation_required: bool = False
    dimension_results: list[DimensionConvergence] = Field(default_factory=list)
    rubric_version: Optional[str] = None


# ── Evaluator Outcome (for certificate integration) ──

class EvaluatorOutcome(BaseModel):
    """Aggregate evaluator orchestration outcome for a run.

    This is the top-level data structure persisted alongside certificates.
    """
    convergence_summary: RunConvergenceSummary
    evaluator_scores: list[EvaluatorScoreRecord] = Field(default_factory=list)
    issuance_eligible: bool = True
    block_reason: Optional[str] = None


# ── Response schemas for API surfaces ──

class EvaluatorOrchestrationResponse(BaseModel):
    """API response schema for evaluator orchestration results."""
    evaluator_ids: list[str]
    dimension_results: list[DimensionConvergence]
    escalation_required: bool
    issuance_eligible: bool
    block_reason: Optional[str] = None
