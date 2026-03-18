"""ContractService — CRUD for EvaluationContracts with supersession logic.

Cycle 037: Contract-Backed Verification Infrastructure.

Orchestrates: SpecLoader → PolicyNormalizer → CheckPlanner → persist.
Enforces one ACTIVE contract per registration via supersession.
Idempotent: same spec_hash on ACTIVE contract returns existing (no duplicate).
"""

import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EvaluationContract
from backend.services.spec_loader import ConstructSpec, load as load_spec
from backend.services.policy_normalizer import normalize
from backend.services.check_planner import (
    plan_checks,
    checks_to_dicts,
    compute_contract_hash,
)

logger = logging.getLogger(__name__)


class ContractService:
    """Manages EvaluationContract lifecycle."""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create_contract(
        self,
        registration_id: str,
        yaml_content: str,
        available_assets: Optional[dict] = None,
    ) -> EvaluationContract:
        """Create or refresh an evaluation contract from YAML content.

        Pipeline: parse YAML → normalize claims → plan checks → persist.
        Idempotent: if ACTIVE contract has same spec_hash, returns existing.
        Supersedes: if ACTIVE contract has different spec_hash, supersedes it.

        Args:
            registration_id: FK to construct_registrations.id.
            yaml_content: Raw construct.yaml content.
            available_assets: Optional benchmark/anchor assets for CheckPlanner.

        Returns:
            The ACTIVE EvaluationContract (new or existing).
        """
        # 1. Parse and hash
        spec = load_spec(yaml_content)

        # 2. Check for existing ACTIVE contract
        existing = await self.get_active_contract(registration_id)
        if existing is not None:
            if existing.spec_hash == spec.spec_hash:
                logger.info(
                    "Idempotent: ACTIVE contract %s already has spec_hash %s",
                    existing.id, spec.spec_hash[:24],
                )
                return existing
            # Different spec_hash → supersede
            await self.supersede(existing.id)

        # 3. Normalize claims
        norm_result = normalize(spec)

        # 4. Plan checks
        planned = plan_checks(spec.slug, norm_result, available_assets)
        planned_dicts = checks_to_dicts(planned)

        # 5. Compute contract hash
        contract_hash = compute_contract_hash(spec.spec_hash, planned)

        # 6. Persist
        contract = EvaluationContract(
            id=str(uuid4()),
            construct_registration_id=registration_id,
            spec_hash=spec.spec_hash,
            contract_hash=contract_hash,
            normalized_claims=[
                {
                    "domain": c["domain"],
                    "original": c["original"],
                    "is_vague": c["is_vague"],
                    "matched_category": c.get("matched_category"),
                    "vagueness_reason": c.get("vagueness_reason"),
                }
                for c in norm_result.normalized_claims
            ],
            explicit_refusals=norm_result.explicit_refusals,
            planned_checks=planned_dicts,
            tier_cap=norm_result.tier_cap,
            status="ACTIVE",
        )

        self._db.add(contract)
        await self._db.flush()
        logger.info(
            "Created contract %s for registration %s (hash=%s)",
            contract.id, registration_id, contract_hash[:24],
        )
        return contract

    async def get_active_contract(
        self, registration_id: str
    ) -> Optional[EvaluationContract]:
        """Get the ACTIVE contract for a registration (at most one)."""
        result = await self._db.execute(
            select(EvaluationContract).where(
                EvaluationContract.construct_registration_id == registration_id,
                EvaluationContract.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, contract_hash: str) -> Optional[EvaluationContract]:
        """Lookup contract by contract_hash."""
        result = await self._db.execute(
            select(EvaluationContract).where(
                EvaluationContract.contract_hash == contract_hash
            )
        )
        return result.scalar_one_or_none()

    async def supersede(self, contract_id: str) -> None:
        """Transition contract from ACTIVE to SUPERSEDED."""
        contract = await self._db.get(EvaluationContract, contract_id)
        if contract is None:
            raise ValueError(f"Contract {contract_id} not found")
        if contract.status != "ACTIVE":
            raise ValueError(
                f"Cannot supersede contract in status '{contract.status}'. "
                f"Only ACTIVE contracts can be superseded."
            )
        contract.status = "SUPERSEDED"
        await self._db.flush()
        logger.info("Superseded contract %s", contract_id)

    async def validate_contract_active(self, contract_hash: str) -> bool:
        """Check if a contract_hash corresponds to an ACTIVE contract."""
        contract = await self.get_by_hash(contract_hash)
        if contract is None:
            return False
        return contract.status == "ACTIVE"

    async def list_contracts(
        self, registration_id: str
    ) -> list[EvaluationContract]:
        """List all contracts for a registration, ordered by created_at desc."""
        result = await self._db.execute(
            select(EvaluationContract)
            .where(EvaluationContract.construct_registration_id == registration_id)
            .order_by(EvaluationContract.created_at.desc())
        )
        return list(result.scalars().all())
