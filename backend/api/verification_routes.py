"""
Verification API Routes — echelon-verify backend integration.

5 endpoints for managing verification runs and viewing certificates.
Auth-protected runs, public certificates.
"""

import asyncio
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.connection import get_session
from backend.database.models import (
    VerificationRun,
    VerificationRunStatus,
    VerificationCertificate,
    VerificationReplayScore,
)
from backend.schemas.verification import (
    VerificationRunCreate,
    VerificationRunResponse,
    VerificationRunListResponse,
    CertificateResponse,
    CertificateSummaryResponse,
    CertificateListResponse,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData
from backend.services.verification_bridge import run_verification_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


def _run_to_response(run: VerificationRun) -> VerificationRunResponse:
    """Convert ORM model to response, mapping `id` → `run_id`."""
    return VerificationRunResponse(
        run_id=run.id,
        status=run.status.value if isinstance(run.status, VerificationRunStatus) else run.status,
        progress=run.progress,
        total=run.total,
        construct_id=run.construct_id,
        repo_url=run.repo_url,
        error=run.error,
        certificate_id=run.certificate_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


# ============================================
# RUN ENDPOINTS (auth required)
# ============================================

@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_verification_run(
    body: VerificationRunCreate,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new verification run. Launches pipeline as background task."""
    run_id = str(uuid.uuid4())

    # Build config_json — redact github_token for storage
    config = {
        "oracle_type": body.oracle_type,
        "oracle_url": body.oracle_url,
        "oracle_headers": body.oracle_headers,
        "oracle_module": body.oracle_module,
        "oracle_callable": body.oracle_callable,
        "limit": body.limit,
        "min_replays": body.min_replays,
    }
    # Pass token at runtime only (not persisted)
    if body.github_token:
        config["_github_token"] = body.github_token

    run = VerificationRun(
        id=run_id,
        user_id=user.user_id,
        construct_id=body.construct_id,
        repo_url=body.repo_url,
        config_json={k: v for k, v in config.items() if not k.startswith("_")},
    )

    # Store runtime-only token separately for the background task
    runtime_config = dict(config)

    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Launch background task
    asyncio.create_task(run_verification_task(run_id))
    logger.info("Started verification run %s for construct %s", run_id, body.construct_id)

    return {
        "run_id": run.id,
        "status": run.status.value,
        "created_at": run.created_at,
    }


@router.get("/runs/{run_id}", response_model=VerificationRunResponse)
async def get_verification_run(
    run_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get verification run status. Users can only see their own runs."""
    result = await db.execute(
        select(VerificationRun).where(
            VerificationRun.id == run_id,
            VerificationRun.user_id == user.user_id,
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Not found")
    return _run_to_response(run)


@router.get("/runs", response_model=VerificationRunListResponse)
async def list_verification_runs(
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    construct_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List verification runs for current user with optional filtering."""
    query = select(VerificationRun).where(
        VerificationRun.user_id == user.user_id,
    )
    count_query = select(func.count()).select_from(VerificationRun).where(
        VerificationRun.user_id == user.user_id,
    )

    if status_filter:
        query = query.where(VerificationRun.status == status_filter)
        count_query = count_query.where(VerificationRun.status == status_filter)
    if construct_id:
        query = query.where(VerificationRun.construct_id == construct_id)
        count_query = count_query.where(VerificationRun.construct_id == construct_id)

    query = query.order_by(VerificationRun.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    runs = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return VerificationRunListResponse(
        runs=[_run_to_response(r) for r in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================
# CERTIFICATE ENDPOINTS (public)
# ============================================

@router.get("/certificates/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a certificate with all replay scores. Public endpoint."""
    result = await db.execute(
        select(VerificationCertificate)
        .where(VerificationCertificate.id == cert_id)
        .options(selectinload(VerificationCertificate.replay_scores))
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(status_code=404, detail="Not found")
    return CertificateResponse.model_validate(cert)


@router.get("/certificates", response_model=CertificateListResponse)
async def list_certificates(
    db: AsyncSession = Depends(get_db),
    construct_id: Optional[str] = Query(None),
    sort: Optional[str] = Query("created_desc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List certificates with optional filtering and sorting. Public endpoint."""
    query = select(VerificationCertificate)
    count_query = select(func.count()).select_from(VerificationCertificate)

    if construct_id:
        query = query.where(VerificationCertificate.construct_id == construct_id)
        count_query = count_query.where(VerificationCertificate.construct_id == construct_id)

    if sort == "brier_asc":
        query = query.order_by(VerificationCertificate.brier.asc())
    else:
        query = query.order_by(VerificationCertificate.created_at.desc())

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    certs = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CertificateListResponse(
        certificates=[CertificateSummaryResponse.model_validate(c) for c in certs],
        total=total,
        limit=limit,
        offset=offset,
    )
