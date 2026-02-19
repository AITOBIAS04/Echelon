"""FastAPI router for the verification pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from echelon_verify.config import PipelineConfig
from echelon_verify.models import (
    CalibrationCertificate,
    VerificationRunRequest,
    VerificationRunResult,
    VerificationRunStatus,
)
from echelon_verify.oracle.base import OracleAdapter
from echelon_verify.pipeline import VerificationPipeline
from echelon_verify.scoring.anthropic_scorer import AnthropicScorer
from echelon_verify.storage import Storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verification", tags=["verification"])

# In-memory job tracking
_jobs: dict[str, VerificationRunStatus] = {}
_results: dict[str, CalibrationCertificate] = {}
_storage = Storage("data")


def _build_pipeline(request: VerificationRunRequest) -> VerificationPipeline:
    from echelon_verify.config import IngestionConfig

    config = PipelineConfig(
        ingestion=IngestionConfig(
            repo_url=request.repo_url,
            github_token=request.github_token,
            limit=request.limit,
        ),
        oracle=request.construct,
        scoring=request.scoring,
        min_replays=request.min_replays,
        construct_id=request.construct_id,
    )
    oracle = OracleAdapter.from_config(config.oracle)
    scorer = AnthropicScorer(config.scoring)
    return VerificationPipeline(config, oracle, scorer, _storage)


async def _run_verification(job_id: str, request: VerificationRunRequest) -> None:
    """Background task that runs the full verification pipeline."""
    try:
        _jobs[job_id].status = "ingesting"
        pipeline = _build_pipeline(request)

        def progress(completed: int, total: int) -> None:
            _jobs[job_id].progress = completed
            _jobs[job_id].total = total
            if _jobs[job_id].status == "ingesting":
                _jobs[job_id].status = "invoking"

        _jobs[job_id].status = "scoring"
        cert = await pipeline.run(progress=progress)

        _jobs[job_id].status = "completed"
        _results[job_id] = cert
    except Exception as exc:
        logger.error("Verification run %s failed: %s", job_id, exc, exc_info=True)
        _jobs[job_id].status = "failed"
        _jobs[job_id].error = str(exc)


@router.post("/run", response_model=VerificationRunStatus)
async def start_verification(request: VerificationRunRequest) -> VerificationRunStatus:
    """Start an async verification run."""
    job_id = str(uuid4())
    status = VerificationRunStatus(
        job_id=job_id,
        status="pending",
        started_at=datetime.now(timezone.utc),
    )
    _jobs[job_id] = status
    asyncio.create_task(_run_verification(job_id, request))
    return status


@router.get("/status/{job_id}", response_model=VerificationRunStatus)
async def get_status(job_id: str) -> VerificationRunStatus:
    """Get verification run status."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@router.get("/result/{job_id}", response_model=VerificationRunResult)
async def get_result(job_id: str) -> VerificationRunResult:
    """Get verification run result (certificate)."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    if _jobs[job_id].status != "completed":
        raise HTTPException(status_code=409, detail="Job not yet completed")
    return VerificationRunResult(
        job_id=job_id,
        certificate=_results[job_id],
        completed_at=datetime.now(timezone.utc),
    )


@router.get("/certificates", response_model=list[dict[str, Any]])
async def list_certificates() -> list[dict[str, Any]]:
    """List all stored certificates."""
    return _storage.list_certificates()
