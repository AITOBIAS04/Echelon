"""Construct Verification API Routes.

Registration, evaluation runs, episodes, and certificate endpoints.
All routes version-addressable via /:slug/:version. No UUID in public API.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    ConstructRegistration,
    EvaluationContract,
    Investigation,
    InvestigationEvidenceItem,
    InvestigationCertificateRecord,
)
from backend.dependencies import get_db
from backend.schemas.construct_schemas import (
    ConstructRegistrationRequest,
    ConstructRegistrationResponse,
    ConstructRegistrationListItem,
    CreateRunResponse,
    RunListItem,
    EpisodeCaptureRequest,
    EpisodeCaptureResponse,
    EpisodeDetail,
    RunDetailResponse,
    CertificateResponse,
    CreateContractRequest,
    ContractResponse,
    ContractListResponse,
    NormalizedClaimSchema,
    RefusalSchema,
    PlannedCheckSchema,
    CheckPlanSchema,
    CheckPlanEntrySchema,
    RemediationSchema,
)
from backend.services.construct_registry import ConstructRegistry
from backend.services.construct_adapter import ConstructAdapter
from backend.services.contract_service import ContractService
from backend.services.test_prompt_registry import TestPromptRegistry
from backend.services.certificate_lifecycle_service import transition_to_ready

logger = logging.getLogger(__name__)

construct_router = APIRouter(
    prefix="/api/constructs",
    tags=["constructs"],
)

# Singleton prompt registry (loaded once)
_prompt_registry = TestPromptRegistry()


# ── Helper ──


async def _resolve_investigation(
    session: AsyncSession, slug: str, version: str, run_number: int
) -> Investigation:
    """Resolve a construct run to its Investigation row, or raise 404."""
    construct_id = f"{slug}:{version}"
    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
            Investigation.run_number == run_number,
        )
    )
    investigation = result.scalar_one_or_none()
    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_number} not found for {slug}:{version}",
        )
    return investigation


# ── Registration ──


@construct_router.post("/register", response_model=ConstructRegistrationResponse, status_code=201)
async def register_construct(
    body: ConstructRegistrationRequest,
    session: AsyncSession = Depends(get_db),
):
    """Register a construct for verification."""
    registry = ConstructRegistry(session)

    try:
        reg = await registry.register(
            slug=body.slug,
            version=body.version,
            content_hash=body.content_hash,
            skill_manifest=body.skill_manifest,
            domain_claims=body.domain_claims,
            test_prompts_hash=body.test_prompts_hash,
            rubric_hash=body.rubric_hash,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=409 if "already registered" in str(e) else 400, detail=str(e))
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Construct {body.slug}:{body.version} is already registered",
        )

    return ConstructRegistrationResponse(
        id=reg.id,
        slug=reg.slug,
        version=reg.version,
        status=reg.status,
        commitment_hash=reg.commitment_hash,
        skill_count=reg.skill_count,
        created_at=getattr(reg, "created_at", None),
    )


@construct_router.get("/", response_model=list[ConstructRegistrationListItem])
async def list_constructs(
    session: AsyncSession = Depends(get_db),
):
    """List all registered constructs."""
    registry = ConstructRegistry(session)
    registrations = await registry.list_registered()

    return [
        ConstructRegistrationListItem(
            slug=r.slug,
            version=r.version,
            status=r.status,
            skill_count=r.skill_count,
            commitment_hash=r.commitment_hash,
        )
        for r in registrations
    ]


@construct_router.get("/{slug}/{version}", response_model=ConstructRegistrationResponse)
async def get_construct(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Get registration details for a specific construct version."""
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    return ConstructRegistrationResponse(
        id=reg.id,
        slug=reg.slug,
        version=reg.version,
        status=reg.status,
        commitment_hash=reg.commitment_hash,
        skill_count=reg.skill_count,
        created_at=getattr(reg, "created_at", None),
    )


# ── Contracts (Cycle 037) ──


@construct_router.post("/{slug}/{version}/contract", response_model=ContractResponse, status_code=201)
async def create_contract(
    slug: str,
    version: str,
    body: CreateContractRequest,
    session: AsyncSession = Depends(get_db),
):
    """Create or refresh an evaluation contract from YAML content.

    Idempotent: same spec_hash returns existing ACTIVE contract.
    Different spec_hash supersedes existing ACTIVE and creates new.
    """
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    contract_svc = ContractService(session)

    try:
        contract = await contract_svc.create_contract(
            registration_id=reg.id,
            yaml_content=body.yaml_content,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _contract_to_response(contract)


@construct_router.get("/{slug}/{version}/contract", response_model=ContractResponse)
async def get_active_contract(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Get the ACTIVE evaluation contract for a construct version."""
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    contract_svc = ContractService(session)
    contract = await contract_svc.get_active_contract(reg.id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=f"No ACTIVE contract for {slug}:{version}. POST /{slug}/{version}/contract first.",
        )

    return _contract_to_response(contract)


@construct_router.get("/{slug}/{version}/contracts", response_model=ContractListResponse)
async def list_contracts(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """List all contracts for a construct version (ACTIVE + SUPERSEDED)."""
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    contract_svc = ContractService(session)
    contracts = await contract_svc.list_contracts(reg.id)

    return ContractListResponse(
        contracts=[_contract_to_response(c) for c in contracts],
        total=len(contracts),
    )


def _contract_to_response(contract: EvaluationContract) -> ContractResponse:
    """Convert EvaluationContract model to ContractResponse schema."""
    claims = contract.normalized_claims or []
    refusals = contract.explicit_refusals or []
    checks = contract.planned_checks or []

    return ContractResponse(
        id=contract.id,
        construct_registration_id=contract.construct_registration_id,
        spec_hash=contract.spec_hash,
        contract_hash=contract.contract_hash,
        normalized_claims=[
            NormalizedClaimSchema(
                domain=c.get("domain", ""),
                original=c.get("original", ""),
                is_vague=c.get("is_vague", False),
                matched_category=c.get("matched_category"),
                vagueness_reason=c.get("vagueness_reason"),
            )
            for c in claims
        ],
        explicit_refusals=[
            RefusalSchema(scope=r.get("scope", ""), reason=r.get("reason", ""))
            for r in refusals
        ],
        planned_checks=[
            PlannedCheckSchema(
                check_id=ch.get("check_id", ""),
                check_type=ch.get("check_type", ""),
                domain=ch.get("domain", ""),
                source=ch.get("source", ""),
                critical=ch.get("critical", False),
                asset_id=ch.get("asset_id"),
                anchor_class=ch.get("anchor_class"),
            )
            for ch in checks
        ],
        tier_cap=contract.tier_cap,
        status=contract.status if isinstance(contract.status, str) else contract.status.value,
        created_at=getattr(contract, "created_at", None),
    )


# ── Runs ──


@construct_router.post("/{slug}/{version}/runs", response_model=CreateRunResponse, status_code=201)
async def create_run(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Create a new evaluation run for a registered construct.

    Requires an ACTIVE contract (cycle-037+). Threads contract_hash
    into the investigation for certificate pinning.
    """
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    # Fetch ACTIVE contract — required for cycle-037+
    contract_svc = ContractService(session)
    contract = await contract_svc.get_active_contract(reg.id)

    if contract is None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"No ACTIVE contract for {slug}:{version}. "
                f"POST /{slug}/{version}/contract first."
            ),
        )

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        investigation = await adapter.create_run(reg, contract_hash=contract.contract_hash)
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CreateRunResponse(
        investigation_id=investigation.id,
        run_number=investigation.run_number,
        status=investigation.status,
        construct_id=investigation.construct_id,
    )


@construct_router.get("/{slug}/{version}/runs", response_model=list[RunListItem])
async def list_runs(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """List all evaluation runs for a registered construct."""
    construct_id = f"{slug}:{version}"

    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
        ).order_by(Investigation.run_number)
    )
    investigations = list(result.scalars().all())

    items = []
    for inv in investigations:
        # Count evidence items per investigation
        count_result = await session.execute(
            select(func.count()).select_from(InvestigationEvidenceItem).where(
                InvestigationEvidenceItem.investigation_id == inv.id,
            )
        )
        episode_count = count_result.scalar() or 0

        items.append(RunListItem(
            run_number=inv.run_number,
            investigation_id=inv.id,
            status=inv.status,
            episode_count=episode_count,
            started_at=getattr(inv, "created_at", None),
        ))

    return items


@construct_router.get("/{slug}/{version}/runs/{run_number}", response_model=RunDetailResponse)
async def get_run_detail(
    slug: str,
    version: str,
    run_number: int,
    session: AsyncSession = Depends(get_db),
):
    """Get run details with per-episode activity."""
    investigation = await _resolve_investigation(session, slug, version, run_number)

    # Get evidence items
    ev_result = await session.execute(
        select(InvestigationEvidenceItem).where(
            InvestigationEvidenceItem.investigation_id == investigation.id,
        ).order_by(InvestigationEvidenceItem.submitted_at)
    )
    evidence_items = list(ev_result.scalars().all())

    # Build episode list and coverage summaries
    episodes = []
    domain_coverage: dict[str, int] = {}
    skill_coverage: dict[str, int] = {}

    for item in evidence_items:
        meta = item.construct_meta_json or {}
        domain = meta.get("domain", "unknown")
        skill = meta.get("skill_command", "unknown")

        domain_coverage[domain] = domain_coverage.get(domain, 0) + 1
        skill_coverage[skill] = skill_coverage.get(skill, 0) + 1

        episodes.append(EpisodeDetail(
            prompt_index=meta.get("prompt_index", 0),
            skill_command=skill,
            domain=domain,
            timing_ms=meta.get("timing_ms", 0),
            content_hash=item.content_hash,
            scores=meta.get("scores", {}),
            submitted_at=getattr(item, "submitted_at", None),
        ))

    config = investigation.stop_config_json or {}

    return RunDetailResponse(
        run_number=investigation.run_number,
        investigation_id=investigation.id,
        status=investigation.status,
        registration={"slug": slug, "version": version},
        commitment_hash=config.get("commitment_hash", ""),
        episodes=sorted(episodes, key=lambda e: e.prompt_index),
        domain_coverage=domain_coverage,
        skill_coverage=skill_coverage,
        started_at=getattr(investigation, "created_at", None),
        completed_at=None,
    )


@construct_router.post("/{slug}/{version}/runs/{run_number}/episodes", response_model=EpisodeCaptureResponse, status_code=201)
async def capture_episode(
    slug: str,
    version: str,
    run_number: int,
    body: EpisodeCaptureRequest,
    session: AsyncSession = Depends(get_db),
):
    """Capture an episode output as evidence."""
    investigation = await _resolve_investigation(session, slug, version, run_number)

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        evidence = await adapter.capture_episode(
            investigation_id=investigation.id,
            skill_command=body.skill_command,
            domain=body.domain,
            prompt_index=body.prompt_index,
            output_text=body.output_text,
            timing_ms=body.timing_ms,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return EpisodeCaptureResponse(
        evidence_id=evidence.id,
        content_hash=evidence.content_hash,
        prompt_index=body.prompt_index,
    )


@construct_router.post("/{slug}/{version}/runs/{run_number}/complete", status_code=200)
async def complete_run(
    slug: str,
    version: str,
    run_number: int,
    session: AsyncSession = Depends(get_db),
):
    """Complete an evaluation run and trigger validation."""
    investigation = await _resolve_investigation(session, slug, version, run_number)

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        summary = await adapter.complete_run(investigation.id)
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "COMPLETE",
        "episode_count": summary.episode_count,
        "domain_coverage": summary.domain_coverage,
        "skill_coverage": summary.skill_coverage,
        "skill_coverage_ratio": summary.skill_coverage_ratio,
    }


# ── Certificates ──


@construct_router.get("/{slug}/{version}/certificate", response_model=CertificateResponse)
async def get_certificate(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Get the latest certificate for a construct version."""
    construct_id = f"{slug}:{version}"

    # Find the most recent investigation with a certificate
    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
        ).order_by(Investigation.run_number.desc())
    )
    investigations = list(result.scalars().all())

    for inv in investigations:
        cert_result = await session.execute(
            select(InvestigationCertificateRecord).where(
                InvestigationCertificateRecord.investigation_id == inv.id,
            )
        )
        cert_record = cert_result.scalar_one_or_none()
        if cert_record is not None:
            cert_json = cert_record.certificate_json or {}

            # Reconstruct check_plan schema if present
            check_plan_schema = None
            if "check_plan" in cert_json and cert_json["check_plan"] is not None:
                cp = cert_json["check_plan"]
                check_plan_schema = CheckPlanSchema(
                    total_planned=cp.get("total_planned", 0),
                    total_executed=cp.get("total_executed", 0),
                    checks=[
                        CheckPlanEntrySchema(
                            id=c["id"], type=c["type"], status=c["status"],
                            score=c.get("score"), reason=c.get("reason"),
                        )
                        for c in cp.get("checks", [])
                    ],
                )

            remediation_schema = None
            if "remediation" in cert_json and cert_json["remediation"] is not None:
                rem = cert_json["remediation"]
                remediation_schema = RemediationSchema(
                    status=rem.get("status", ""),
                    reason=rem.get("reason", ""),
                    missing_checks=rem.get("missing_checks", []),
                    executed_count=rem.get("executed_count", 0),
                    planned_count=rem.get("planned_count", 0),
                    recommendation=rem.get("recommendation", ""),
                )

            return CertificateResponse(
                certificate_id=cert_json.get("certificate_id", cert_record.id),
                construct_slug=cert_json.get("construct_slug", slug),
                construct_version=cert_json.get("construct_version", version),
                composite_score=cert_json.get("composite_score", 0.0),
                domain_scores=cert_json.get("domain_scores", {}),
                skill_coverage=cert_json.get("skill_coverage", 0.0),
                verification_tier=cert_json.get("verification_tier", "UNVERIFIED"),
                verdict=cert_json.get("verdict", "UNKNOWN"),
                routing_decision=cert_record.routing_decision,
                evidence_bundle_hash=cert_json.get("evidence_bundle_hash", ""),
                episode_count=cert_json.get("episode_count", 0),
                contract_hash=cert_json.get("contract_hash"),
                spec_hash=cert_json.get("spec_hash"),
                issuance_status=cert_json.get("issuance_status", "READY"),
                check_plan=check_plan_schema,
                remediation=remediation_schema,
            )

    raise HTTPException(
        status_code=404,
        detail=f"No certificate found for {slug}:{version}",
    )


@construct_router.post("/{slug}/{version}/certificate", response_model=CertificateResponse, status_code=201)
async def issue_certificate(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Issue a certificate from the most recent completed run.

    Enforces completion contract: run must have been completed via
    POST .../complete (stop_condition_status == READY) before certificate
    issuance. Uses the shared certificate lifecycle (transition_to_ready)
    so certificates participate in the batch anchor flow.
    """
    construct_id = f"{slug}:{version}"

    # Find the most recent investigation for this construct
    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
        ).order_by(Investigation.run_number.desc())
    )
    investigation = result.scalars().first()

    if investigation is None:
        raise HTTPException(status_code=404, detail=f"No runs found for {slug}:{version}")

    # ── Gate 1: Enforce completion contract ──
    # stop_condition_status is set by complete_run() after validating
    # that all committed prompts have evidence items.
    if investigation.stop_condition_status != "READY":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run {investigation.run_number} has not been completed. "
                f"Call POST /{slug}/{version}/runs/{investigation.run_number}/complete first. "
                f"(stop_condition_status={investigation.stop_condition_status!r})"
            ),
        )

    # ── Gate 2: No duplicate certificates ──
    existing_cert = await session.execute(
        select(InvestigationCertificateRecord).where(
            InvestigationCertificateRecord.investigation_id == investigation.id,
        )
    )
    if existing_cert.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Certificate already exists for run {investigation.run_number}",
        )

    # Get evidence items
    ev_result = await session.execute(
        select(InvestigationEvidenceItem).where(
            InvestigationEvidenceItem.investigation_id == investigation.id,
        )
    )
    evidence_items = list(ev_result.scalars().all())

    if not evidence_items:
        raise HTTPException(status_code=400, detail="No episodes captured for this run")

    # Build evidence bundle
    from backend.services.construct_evidence_bundle import ConstructEvidenceBundleBuilder
    bundle_builder = ConstructEvidenceBundleBuilder()
    manifest = bundle_builder.build_manifest(evidence_items)
    bundle_hash = bundle_builder.compute_bundle_hash(manifest)

    # Dispatch rubrics by construct slug
    config = investigation.stop_config_json or {}
    construct_slug = config.get("construct_slug", slug)

    from backend.data.construct_rubrics import get_rubrics
    from backend.services.construct_scorer import ConstructScorer
    rubrics = get_rubrics(construct_slug)
    if rubrics is None:
        raise HTTPException(
            status_code=400,
            detail=f"No rubrics registered for construct '{construct_slug}'",
        )
    scorer = ConstructScorer(rubrics=rubrics)

    domain_episode_scores: dict[str, list[dict]] = {}
    tested_skills: set[str] = set()

    for item in evidence_items:
        meta = item.construct_meta_json or {}
        domain = meta.get("domain", "")
        skill = meta.get("skill_command", "")
        prompt_text = meta.get("prompt_text", "")
        output_text = item.content_text or ""

        scores = scorer.score_episode(skill, domain, prompt_text, output_text)
        if domain not in domain_episode_scores:
            domain_episode_scores[domain] = []
        domain_episode_scores[domain].append(scores)
        tested_skills.add(skill)

        # Persist scores back to the evidence item so they're
        # available in run-detail and certificate responses.
        if scores and meta.get("scores") != scores:
            updated_meta = dict(meta)
            updated_meta["scores"] = scores
            item.construct_meta_json = updated_meta

    # Aggregate
    domain_scores = {
        domain: scorer.aggregate_domain(ep_scores, domain)
        for domain, ep_scores in domain_episode_scores.items()
    }
    composite = scorer.aggregate_composite(domain_scores)

    # Get registration for skill manifest
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Registration not found for {slug}:{version}")

    skill_coverage = scorer.compute_skill_coverage(reg.skill_manifest, tested_skills)

    # Get template config for thresholds — query the InvestigationTemplate
    # directly instead of traversing the lazy-loaded relationship (which
    # would raise MissingGreenlet in async context). template_config_json
    # lives on InvestigationTemplate, not Investigation.
    template_config = None
    if investigation.template_id:
        from backend.database.models import InvestigationTemplate
        tmpl_result = await session.get(InvestigationTemplate, investigation.template_id)
        if tmpl_result is not None:
            template_config = tmpl_result.template_config_json

    verdict = scorer.compute_verdict(composite, skill_coverage, template_config)
    tier = scorer.compute_tier(len(evidence_items))
    routing_hint = scorer.compute_routing_hint(verdict, tier)

    # Build certificate
    from backend.services.construct_certificate_builder import (
        ConstructCertificateBuilder,
        ScorerOutput,
    )
    cert_builder = ConstructCertificateBuilder()
    scorer_output = ScorerOutput(
        composite_score=composite,
        domain_scores=domain_scores,
        skill_coverage=skill_coverage,
        verdict=verdict,
        tier=tier,
        routing_hint=routing_hint,
        episode_count=len(evidence_items),
    )

    # Fetch contract for certificate enrichment (cycle-037+)
    contract = None
    if investigation.contract_hash is not None:
        contract_svc = ContractService(session)
        contract = await contract_svc.get_by_hash(investigation.contract_hash)

    cert = cert_builder.build(reg, investigation, scorer_output, bundle_hash, contract=contract)
    cert_json = cert_builder.to_certificate_json(cert)
    routing_decision, routing_reason = cert_builder.compute_routing_decision(scorer_output)

    # ── Persist via shared certificate lifecycle ──
    from uuid import uuid4
    cert_record = InvestigationCertificateRecord(
        id=str(uuid4()),
        investigation_id=investigation.id,
        certificate_hash=bundle_hash.replace("sha256:", ""),
        certificate_json=cert_json,
        routing_decision=routing_decision,
        routing_reason=routing_reason,
    )
    session.add(cert_record)
    await session.flush()

    # ── Gate lifecycle transition on issuance status ──
    # Only READY certificates enter the shared lifecycle (batch anchor flow).
    # DEFERRED certs are persisted but await remediation before transitioning.
    # REJECTED certs are persisted for audit trail but never transition.
    if cert.issuance_status == "READY":
        await transition_to_ready(session, cert_record, investigation)
        new_status = "CERTIFIED" if verdict == "PASS" else "FAILED"
        await registry.update_status(reg.id, new_status)
    elif cert.issuance_status == "REJECTED":
        await registry.update_status(reg.id, "FAILED")

    await session.commit()

    # Build check_plan and remediation schemas for response
    check_plan_schema = None
    remediation_schema = None
    if cert.check_plan is not None:
        check_plan_schema = CheckPlanSchema(
            total_planned=cert.check_plan["total_planned"],
            total_executed=cert.check_plan["total_executed"],
            checks=[
                CheckPlanEntrySchema(
                    id=c["id"], type=c["type"], status=c["status"],
                    score=c.get("score"), reason=c.get("reason"),
                )
                for c in cert.check_plan["checks"]
            ],
        )
    if cert.remediation is not None:
        remediation_schema = RemediationSchema(
            status=cert.remediation["status"],
            reason=cert.remediation["reason"],
            missing_checks=cert.remediation["missing_checks"],
            executed_count=cert.remediation["executed_count"],
            planned_count=cert.remediation["planned_count"],
            recommendation=cert.remediation["recommendation"],
        )

    return CertificateResponse(
        certificate_id=cert.certificate_id,
        construct_slug=slug,
        construct_version=version,
        composite_score=composite,
        domain_scores=domain_scores,
        skill_coverage=skill_coverage,
        verification_tier=tier,
        verdict=verdict,
        routing_decision=routing_decision,
        evidence_bundle_hash=bundle_hash,
        episode_count=len(evidence_items),
        contract_hash=cert.contract_hash,
        spec_hash=cert.spec_hash,
        issuance_status=cert.issuance_status,
        check_plan=check_plan_schema,
        remediation=remediation_schema,
    )
