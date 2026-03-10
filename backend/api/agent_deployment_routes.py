"""
Agent Deployment API Routes (Cycle 019).

7 endpoints for managing agent-to-theatre deployments.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import TokenData
from backend.dependencies import get_current_user, get_db
from backend.schemas.agent_deployment_schemas import (
    AgentDeploymentCreate,
    AgentDeploymentResponse,
    AgentDeploymentSummaryResponse,
    DeploymentDetailResponse,
    DeploymentListResponse,
    StrategyUpdateRequest,
)
from backend.services.agent_deployment_service import (
    AgentDeploymentService,
    DeploymentGuardError,
)
from backend.websockets.realtime_manager import manager as ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-deployments", tags=["Agent Deployments"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AgentDeploymentResponse)
async def create_deployment(
    body: AgentDeploymentCreate,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent deployment."""
    svc = AgentDeploymentService(db)
    try:
        deployment = await svc.create_deployment(
            agent_id=body.agent_id,
            theatre_id=body.theatre_id,
            strategy_profile=body.strategy_profile,
            deployed_by=user.user_id,
            config_json=body.config_json,
        )
        await db.commit()
        await ws_manager.broadcast_agent_deployed(
            agent_id=body.agent_id,
            theatre_id=body.theatre_id,
            strategy_profile=body.strategy_profile,
            deployed_by=user.user_id,
        )
        return deployment
    except DeploymentGuardError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.get("/", response_model=DeploymentListResponse)
async def list_deployments(
    agent_id: Optional[str] = Query(None),
    theatre_id: Optional[str] = Query(None),
    deployment_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List deployments with optional filters."""
    svc = AgentDeploymentService(db)
    deployments, total = await svc.list_deployments(
        agent_id=agent_id,
        theatre_id=theatre_id,
        status=deployment_status,
        limit=limit,
        offset=offset,
    )
    return DeploymentListResponse(
        deployments=[
            AgentDeploymentSummaryResponse.model_validate(d) for d in deployments
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{deployment_id}", response_model=DeploymentDetailResponse)
async def get_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get deployment detail with audit trail."""
    svc = AgentDeploymentService(db)
    deployment = await svc.get_deployment_detail(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.post("/{deployment_id}/withdraw", response_model=AgentDeploymentResponse)
async def withdraw_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw a deployment."""
    svc = AgentDeploymentService(db)
    try:
        deployment = await svc.withdraw_deployment(deployment_id, user.user_id)
        await db.commit()
        await ws_manager.broadcast_agent_withdrawn(
            agent_id=deployment.agent_id,
            theatre_id=deployment.theatre_id,
            withdrawn_by=user.user_id,
        )
        return deployment
    except DeploymentGuardError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.post("/{deployment_id}/pause", response_model=AgentDeploymentResponse)
async def pause_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a deployment."""
    svc = AgentDeploymentService(db)
    try:
        deployment = await svc.pause_deployment(deployment_id)
        await db.commit()
        return deployment
    except DeploymentGuardError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.post("/{deployment_id}/resume", response_model=AgentDeploymentResponse)
async def resume_deployment(
    deployment_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused deployment."""
    svc = AgentDeploymentService(db)
    try:
        deployment = await svc.resume_deployment(deployment_id)
        await db.commit()
        return deployment
    except DeploymentGuardError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.post("/{deployment_id}/strategy", response_model=AgentDeploymentResponse)
async def change_strategy(
    deployment_id: str,
    body: StrategyUpdateRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change deployment strategy profile."""
    svc = AgentDeploymentService(db)
    try:
        deployment = await svc.change_strategy(deployment_id, body.strategy_profile)
        await db.commit()
        return deployment
    except DeploymentGuardError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
