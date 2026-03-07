"""
Agent Deployment Service (Cycle 019).

Manages agent-to-theatre deployments with strategy profiles,
deployment guards, and full audit trail.
"""

from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Agent,
    Theatre,
    TheatreCertificate,
    AgentDeployment,
    DeploymentAuditEvent,
)


class DeploymentGuardError(Exception):
    """Raised when a deployment guard rejects the operation."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class AgentDeploymentService:
    """Service for agent deployment lifecycle."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_deployment(
        self,
        agent_id: str,
        theatre_id: str,
        strategy_profile: str,
        deployed_by: str,
        config_json: Optional[dict] = None,
    ) -> AgentDeployment:
        """Create a new agent deployment with guards."""
        # Guard 1: Agent exists and is alive
        agent = await self._get_agent(agent_id)
        if not agent:
            raise DeploymentGuardError("AGENT_NOT_FOUND", f"Agent {agent_id} not found")
        if not agent.is_alive:
            raise DeploymentGuardError("AGENT_DEAD", f"Agent {agent_id} is not alive")

        # Guard 2: Agent sanity >= 15
        if getattr(agent, "sanity", 100) < 15:
            raise DeploymentGuardError(
                "AGENT_BREAKDOWN", f"Agent {agent_id} sanity too low ({agent.sanity})"
            )

        # Guard 3: Theatre exists
        theatre = await self._get_theatre(theatre_id)
        if not theatre:
            raise DeploymentGuardError("THEATRE_NOT_FOUND", f"Theatre {theatre_id} not found")

        # Guard 4: No active deployment of this agent to this theatre
        existing = await self._get_active_deployment(agent_id, theatre_id)
        if existing:
            raise DeploymentGuardError(
                "DUPLICATE_DEPLOYMENT",
                f"Agent {agent_id} already has active deployment to theatre {theatre_id}",
            )

        # Guard 5: Theatre deployability via certificate
        cert = await self._get_latest_certificate(theatre)
        if not cert:
            raise DeploymentGuardError(
                "NO_CERTIFICATE", f"Theatre {theatre_id} has no certificate — not deployable"
            )

        routing_hint = getattr(cert, "routing_hint", None)
        if routing_hint == "BLOCKED":
            raise DeploymentGuardError(
                "ROUTING_BLOCKED", f"Theatre {theatre_id} certificate has routing_hint=BLOCKED"
            )

        coherence_required = getattr(cert, "coherence_review_required", False)
        coherence_status = getattr(cert, "coherence_gate_status", None)
        if coherence_required and coherence_status != "PASSED":
            raise DeploymentGuardError(
                "COHERENCE_GATE_FAILED",
                f"Theatre {theatre_id} requires coherence review (status={coherence_status})",
            )

        # Create deployment
        now = datetime.utcnow()
        deployment = AgentDeployment(
            agent_id=agent_id,
            theatre_id=theatre_id,
            status="ACTIVE",
            strategy_profile=strategy_profile or "BALANCED",
            deployed_by=deployed_by,
            deployed_at=now,
            routing_hint_snapshot=routing_hint,
            coherence_gate_status_snapshot=coherence_status,
            config_json=config_json,
        )
        self.session.add(deployment)

        # Audit event
        audit = DeploymentAuditEvent(
            deployment_id=deployment.id,
            event_type="DEPLOYED",
            detail_json={
                "strategy_profile": strategy_profile,
                "routing_hint_snapshot": routing_hint,
                "coherence_gate_status_snapshot": coherence_status,
            },
        )
        self.session.add(audit)
        await self.session.flush()

        return deployment

    async def withdraw_deployment(
        self, deployment_id: str, withdrawn_by: str
    ) -> AgentDeployment:
        """Withdraw a deployment (ACTIVE|PAUSED → WITHDRAWN)."""
        deployment = await self._get_deployment(deployment_id)
        if not deployment:
            raise DeploymentGuardError("NOT_FOUND", f"Deployment {deployment_id} not found")
        if deployment.status == "WITHDRAWN":
            raise DeploymentGuardError("ALREADY_WITHDRAWN", "Deployment already withdrawn")

        now = datetime.utcnow()
        deployment.status = "WITHDRAWN"
        deployment.withdrawn_at = now
        deployment.updated_at = now

        audit = DeploymentAuditEvent(
            deployment_id=deployment_id,
            event_type="WITHDRAWN",
            detail_json={"withdrawn_by": withdrawn_by, "previous_status": deployment.status},
        )
        self.session.add(audit)
        await self.session.flush()

        return deployment

    async def pause_deployment(self, deployment_id: str) -> AgentDeployment:
        """Pause a deployment (ACTIVE → PAUSED)."""
        deployment = await self._get_deployment(deployment_id)
        if not deployment:
            raise DeploymentGuardError("NOT_FOUND", f"Deployment {deployment_id} not found")
        if deployment.status != "ACTIVE":
            raise DeploymentGuardError(
                "INVALID_STATE", f"Cannot pause deployment in {deployment.status} state"
            )

        now = datetime.utcnow()
        deployment.status = "PAUSED"
        deployment.paused_at = now
        deployment.updated_at = now

        audit = DeploymentAuditEvent(
            deployment_id=deployment_id,
            event_type="PAUSED",
        )
        self.session.add(audit)
        await self.session.flush()

        return deployment

    async def resume_deployment(self, deployment_id: str) -> AgentDeployment:
        """Resume a deployment (PAUSED → ACTIVE)."""
        deployment = await self._get_deployment(deployment_id)
        if not deployment:
            raise DeploymentGuardError("NOT_FOUND", f"Deployment {deployment_id} not found")
        if deployment.status != "PAUSED":
            raise DeploymentGuardError(
                "INVALID_STATE", f"Cannot resume deployment in {deployment.status} state"
            )

        now = datetime.utcnow()
        deployment.status = "ACTIVE"
        deployment.paused_at = None
        deployment.updated_at = now

        audit = DeploymentAuditEvent(
            deployment_id=deployment_id,
            event_type="RESUMED",
        )
        self.session.add(audit)
        await self.session.flush()

        return deployment

    async def change_strategy(
        self, deployment_id: str, new_strategy: str
    ) -> AgentDeployment:
        """Change strategy profile, creates audit event."""
        deployment = await self._get_deployment(deployment_id)
        if not deployment:
            raise DeploymentGuardError("NOT_FOUND", f"Deployment {deployment_id} not found")
        if deployment.status == "WITHDRAWN":
            raise DeploymentGuardError(
                "INVALID_STATE", "Cannot change strategy on withdrawn deployment"
            )

        old_strategy = deployment.strategy_profile
        deployment.strategy_profile = new_strategy
        deployment.updated_at = datetime.utcnow()

        audit = DeploymentAuditEvent(
            deployment_id=deployment_id,
            event_type="STRATEGY_CHANGED",
            detail_json={"old_strategy": old_strategy, "new_strategy": new_strategy},
        )
        self.session.add(audit)
        await self.session.flush()

        return deployment

    async def list_deployments(
        self,
        agent_id: Optional[str] = None,
        theatre_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AgentDeployment], int]:
        """List deployments with optional filters. Returns (deployments, total)."""
        query = select(AgentDeployment)
        count_query = select(func.count()).select_from(AgentDeployment)

        if agent_id:
            query = query.where(AgentDeployment.agent_id == agent_id)
            count_query = count_query.where(AgentDeployment.agent_id == agent_id)
        if theatre_id:
            query = query.where(AgentDeployment.theatre_id == theatre_id)
            count_query = count_query.where(AgentDeployment.theatre_id == theatre_id)
        if status:
            query = query.where(AgentDeployment.status == status)
            count_query = count_query.where(AgentDeployment.status == status)

        query = query.order_by(AgentDeployment.deployed_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        deployments = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return deployments, total

    async def get_deployment_detail(self, deployment_id: str) -> Optional[AgentDeployment]:
        """Get deployment with audit events eagerly loaded."""
        result = await self.session.execute(
            select(AgentDeployment)
            .where(AgentDeployment.id == deployment_id)
            .options(selectinload(AgentDeployment.audit_events))
        )
        return result.scalar_one_or_none()

    async def get_active_count_for_agent(self, agent_id: str) -> int:
        """Count active deployments for an agent."""
        result = await self.session.execute(
            select(func.count())
            .select_from(AgentDeployment)
            .where(AgentDeployment.agent_id == agent_id)
            .where(AgentDeployment.status == "ACTIVE")
        )
        return result.scalar() or 0

    # ── Private helpers ──

    async def _get_agent(self, agent_id: str) -> Optional[Agent]:
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def _get_theatre(self, theatre_id: str) -> Optional[Theatre]:
        result = await self.session.execute(
            select(Theatre).where(Theatre.id == theatre_id)
        )
        return result.scalar_one_or_none()

    async def _get_active_deployment(
        self, agent_id: str, theatre_id: str
    ) -> Optional[AgentDeployment]:
        result = await self.session.execute(
            select(AgentDeployment).where(
                AgentDeployment.agent_id == agent_id,
                AgentDeployment.theatre_id == theatre_id,
                AgentDeployment.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none()

    async def _get_deployment(self, deployment_id: str) -> Optional[AgentDeployment]:
        result = await self.session.execute(
            select(AgentDeployment).where(AgentDeployment.id == deployment_id)
        )
        return result.scalar_one_or_none()

    async def _get_latest_certificate(
        self, theatre: Theatre
    ) -> Optional[TheatreCertificate]:
        """Get latest certificate for theatre."""
        cert_id = getattr(theatre, "certificate_id", None)
        if not cert_id:
            return None
        result = await self.session.execute(
            select(TheatreCertificate).where(TheatreCertificate.id == cert_id)
        )
        return result.scalar_one_or_none()
