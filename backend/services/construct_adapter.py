"""Construct Adapter — evaluation harness mapping construct verification onto investigation infrastructure.

Thin layer that creates investigations for construct evaluation runs, captures
episode outputs as evidence items, and validates completeness on run completion.
Does NOT execute prompts — defines the evaluation contract.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    ConstructRegistration,
    Investigation,
    InvestigationEvidenceItem,
)
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.models import ProvenanceClass
from backend.services.test_prompt_registry import TestPromptRegistry

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    """Summary of a completed evaluation run."""
    episode_count: int
    domain_coverage: dict[str, int]  # domain -> episode count
    skill_coverage: dict[str, int]   # skill -> episode count
    skill_coverage_ratio: float
    missing_prompts: list[int]


class ConstructAdapter:
    """Evaluation harness for construct verification.

    Maps construct evaluation operations onto existing
    investigation + evidence infrastructure.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        test_prompt_registry: TestPromptRegistry,
    ):
        self._db = db_session
        self._prompts = test_prompt_registry

    async def create_run(self, registration: ConstructRegistration) -> Investigation:
        """Create a new evaluation run (investigation) for a registered construct.

        Assigns sequential run_number per construct. Creates Investigation row
        with CONSTRUCT_VERIFICATION_V1 template and CONSTRUCT_EVALUATION stop condition.
        """
        construct_id = f"{registration.slug}:{registration.version}"

        # Assign sequential run_number
        result = await self._db.execute(
            select(func.max(Investigation.run_number)).where(
                Investigation.construct_id == construct_id
            )
        )
        max_run = result.scalar()
        run_number = (max_run or 0) + 1

        prompt_set = self._prompts.get_prompts(registration.slug, registration.version)
        committed_prompt_count = prompt_set.count if prompt_set else 0

        investigation = Investigation(
            id=str(uuid4()),
            theatre_id="",
            construct_id=construct_id,
            inquiry_class="INSPECTION",
            status="ACTIVE",
            template_id="CONSTRUCT_VERIFICATION_V1",
            stop_condition="CONSTRUCT_EVALUATION",
            stop_config_json={
                "construct_registration_id": registration.id,
                "construct_slug": registration.slug,
                "construct_version": registration.version,
                "run_number": run_number,
                "committed_prompt_count": committed_prompt_count,
                "commitment_hash": registration.commitment_hash,
            },
            committed_sources_json=["construct_test_prompts"],
            domain_filters_json=registration.domain_claims,
            run_number=run_number,
        )

        self._db.add(investigation)

        # Update registration status
        registration.status = "IN_PROGRESS"

        await self._db.flush()
        logger.info(
            "Created evaluation run %d for %s (investigation=%s)",
            run_number, construct_id, investigation.id,
        )
        return investigation

    async def capture_episode(
        self,
        investigation_id: str,
        skill_command: str,
        domain: str,
        prompt_index: int,
        output_text: str,
        timing_ms: int,
    ) -> InvestigationEvidenceItem:
        """Capture an episode output as an evidence item.

        Validates:
        - Investigation exists and is ACTIVE
        - prompt_index matches committed prompt set
        - skill_command matches the committed prompt at that index
        """
        investigation = await self._db.get(Investigation, investigation_id)
        if investigation is None:
            raise ValueError(f"Investigation {investigation_id} not found")

        if investigation.status != "ACTIVE":
            raise ValueError(
                f"Cannot capture episode for investigation in status '{investigation.status}'. "
                f"Expected 'ACTIVE'."
            )

        # Extract construct identity from stop_config
        config = investigation.stop_config_json or {}
        slug = config.get("construct_slug", "")
        version = config.get("construct_version", "")

        # Validate against committed prompt set
        prompt = self._prompts.get_prompt_at_index(slug, version, prompt_index)
        if prompt is not None:
            if prompt.skill_command != skill_command:
                raise ValueError(
                    f"Skill command mismatch at prompt_index {prompt_index}: "
                    f"expected '{prompt.skill_command}', got '{skill_command}'"
                )

        # Compute content hash
        content_hash = hashlib.sha256(output_text.encode()).hexdigest()

        evidence_item = InvestigationEvidenceItem(
            id=str(uuid4()),
            investigation_id=investigation_id,
            content_hash=content_hash,
            provenance_class="construct_evaluation",
            content_type="text/plain",
            source_description=f"{skill_command} prompt {prompt_index} — {domain}",
            source_id=f"construct:{slug}:{version}",
            references_json=[
                {"type": "construct_registration", "id": config.get("construct_registration_id", "")},
                {"type": "prompt_index", "index": prompt_index},
            ],
            content_text=output_text,
            construct_meta_json={
                "skill_command": skill_command,
                "domain": domain,
                "prompt_index": prompt_index,
                "prompt_text": prompt.prompt_text if prompt else "",
                "output_hash": f"sha256:{content_hash}",
                "timing_ms": timing_ms,
                "scores": {},  # Populated by ConstructScorer
            },
        )

        self._db.add(evidence_item)
        await self._db.flush()
        logger.info(
            "Captured episode %d for investigation %s (%s %s)",
            prompt_index, investigation_id, skill_command, domain,
        )
        return evidence_item

    async def complete_run(self, investigation_id: str) -> RunSummary:
        """Validate that all committed prompts have evidence items.

        On success, sets stop_condition_status='READY' so the certificate
        endpoint can gate on it. Does NOT issue certificates — that's
        ConstructCertificateBuilder's job.
        """
        investigation = await self._db.get(Investigation, investigation_id)
        if investigation is None:
            raise ValueError(f"Investigation {investigation_id} not found")

        if investigation.status != "ACTIVE":
            raise ValueError(
                f"Cannot complete investigation in status '{investigation.status}'. "
                f"Expected 'ACTIVE'."
            )

        config = investigation.stop_config_json or {}
        committed_count = config.get("committed_prompt_count", 0)
        slug = config.get("construct_slug", "")
        version = config.get("construct_version", "")

        # Get all evidence items
        result = await self._db.execute(
            select(InvestigationEvidenceItem).where(
                InvestigationEvidenceItem.investigation_id == investigation_id
            ).order_by(InvestigationEvidenceItem.submitted_at)
        )
        evidence_items = list(result.scalars().all())

        # Compute coverage
        domain_coverage: dict[str, int] = {}
        skill_coverage: dict[str, int] = {}
        seen_indices: set[int] = set()

        for item in evidence_items:
            meta = item.construct_meta_json or {}
            domain = meta.get("domain", "unknown")
            skill = meta.get("skill_command", "unknown")
            idx = meta.get("prompt_index", -1)

            domain_coverage[domain] = domain_coverage.get(domain, 0) + 1
            skill_coverage[skill] = skill_coverage.get(skill, 0) + 1
            if idx >= 0:
                seen_indices.add(idx)

        # Find missing prompts
        prompt_set = self._prompts.get_prompts(slug, version)
        if prompt_set:
            all_indices = {p.index for p in prompt_set.prompts}
            missing = sorted(all_indices - seen_indices)
            declared_skills = len(set(e["command"] for e in (
                await self._db.get(ConstructRegistration, config.get("construct_registration_id", ""))
            ).skill_manifest)) if config.get("construct_registration_id") else 0
        else:
            missing = []
            declared_skills = 0

        tested_skills = len(skill_coverage)
        ratio = tested_skills / declared_skills if declared_skills > 0 else 0.0

        if missing:
            raise ValueError(
                f"Incomplete run: {len(missing)} committed prompts missing evidence items. "
                f"Missing indices: {missing}"
            )

        # Mark stop condition satisfied — certificate endpoint gates on this
        investigation.stop_condition_status = "READY"
        investigation.stop_condition_reason = (
            f"all {len(evidence_items)} committed prompts have evidence"
        )
        investigation.stop_condition_evaluated_at = datetime.utcnow()
        await self._db.flush()

        return RunSummary(
            episode_count=len(evidence_items),
            domain_coverage=domain_coverage,
            skill_coverage=skill_coverage,
            skill_coverage_ratio=ratio,
            missing_prompts=missing,
        )
