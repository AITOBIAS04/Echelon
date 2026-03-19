"""ContractService — CRUD for EvaluationContracts with supersession logic.

Cycle 037: Contract-Backed Verification Infrastructure.
Cycle 037c-fix: Security domain registration + security check integration.
Cycle 037d-fix: Idempotence uses contract_hash (not spec_hash); invalid
    construct_json raises ValueError instead of silent downgrade.

Orchestrates: SpecLoader → PolicyNormalizer → CheckPlanner → persist.
Enforces one ACTIVE contract per registration via supersession.
Idempotent: same contract_hash on ACTIVE contract returns existing (no duplicate).
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
from backend.services.domain_pack_loader import CorpusSkill
from backend.services.security_policy_rules import extract_security_references
from backend.services.security_check_planner import (
    plan_security_checks,
    merge_security_checks,
)
# Side-effect: importing security_policy_rules registers 10 precise security
# domains into KNOWN_PRECISE_DOMAINS at import time (cycle 037c-fix P1).

from backend.services.theatre_policy_rules import parse_construct_json
from backend.services.theatre_check_planner import (
    plan_theatre_checks,
    merge_theatre_checks,
)
# Side-effect: importing theatre_policy_rules registers 10 precise theatre
# domains into KNOWN_PRECISE_DOMAINS at import time (cycle 037d).

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
        corpus_skills: Optional[list[CorpusSkill]] = None,
        construct_json: Optional[str] = None,
    ) -> EvaluationContract:
        """Create or refresh an evaluation contract from YAML content.

        Pipeline: parse YAML → normalize claims → plan checks → merge
        security checks → merge theatre checks → compute contract_hash →
        idempotence check → persist.

        Idempotent: if ACTIVE contract has same contract_hash, returns
        existing. This covers changes in YAML, construct_json, and corpus
        skills — any input that affects the planned checks.
        Supersedes: if ACTIVE contract has different contract_hash, supersedes
        it and creates a new one.

        Args:
            registration_id: FK to construct_registrations.id.
            yaml_content: Raw construct.yaml content.
            available_assets: Optional benchmark/anchor assets for CheckPlanner.
            corpus_skills: Optional security corpus skills for security check
                planning. When provided, security-specific checks (ATT&CK,
                CWE/OWASP, tool invocation, etc.) are merged into the contract.
            construct_json: Optional raw JSON string from theatre construct.json.
                When provided and construct_class is "theatre", theatre-specific
                checks (SETTLEMENT_ACCURACY, ORACLE_CONSISTENCY, etc.) are
                merged into the contract.

        Returns:
            The ACTIVE EvaluationContract (new or existing).

        Raises:
            ValueError: If construct_json is provided for a theatre construct
                but cannot be parsed. Callers should surface this as a client
                error rather than silently downgrading.
        """
        # 1. Parse and hash
        spec = load_spec(yaml_content)

        # 2. Normalize claims
        norm_result = normalize(spec)

        # 3. Plan checks
        planned = plan_checks(spec.slug, norm_result, available_assets)

        # 3b. Merge security-specific checks if corpus skills provided
        if corpus_skills:
            for skill in corpus_skills:
                refs = extract_security_references(skill)
                sec_checks = plan_security_checks(skill, refs)
                planned = merge_security_checks(planned, sec_checks)

        # 3c. Merge theatre-specific checks if construct_json provided
        #     and construct_class is "theatre".
        #     Invalid construct_json raises ValueError — callers must not
        #     silently downgrade a theatre contract to one without theatre
        #     checks.
        if construct_json and spec.construct_class == "theatre":
            theatre_meta = parse_construct_json(construct_json)
            theatre_checks = plan_theatre_checks(spec.slug, theatre_meta)
            planned = merge_theatre_checks(planned, theatre_checks)

        # 4. Compute contract hash (covers spec_hash + all planned checks)
        contract_hash = compute_contract_hash(spec.spec_hash, planned)

        # 5. Idempotence / supersession check against contract_hash
        existing = await self.get_active_contract(registration_id)
        if existing is not None:
            if existing.contract_hash == contract_hash:
                logger.info(
                    "Idempotent: ACTIVE contract %s already has contract_hash %s",
                    existing.id, contract_hash[:24],
                )
                return existing
            # Different contract_hash → supersede
            await self.supersede(existing.id)

        planned_dicts = checks_to_dicts(planned)

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
