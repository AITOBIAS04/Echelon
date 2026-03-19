"""External Theatre Orchestrator — compose full external theatre preparation pipeline.

Cycle 038b: External Theatre Orchestration — Sprint 2.

Composes extraction, check execution, bundle building, and candidate generation
into one runtime flow with shared identity threading.

This is a pure synchronous service — no DB, no AsyncSession, no network calls.
"""

import logging
from typing import Optional

from backend.schemas.external_theatre_orchestration import (
    BuilderFeedbackItem,
    BuilderFeedbackReport,
    ExternalTheatreInput,
    ExternalTheatrePreparationRequest,
    ExternalTheatrePreparationResult,
    ExtractionResult,
    TheatrePreparationEntry,
)
from backend.schemas.theatre_comparison_bundle import TheatreScopeKey
from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture
from backend.services.theatre_check_planner import plan_theatre_checks
from backend.services.theatre_check_runner import execute_theatre_checks
from backend.services.theatre_comparison_bundle_builder import build_comparison_bundle
from backend.services.theatre_comparison_candidates import generate_candidates
from backend.services.theatre_policy_rules import (
    TheatreConstructMeta,
    parse_construct_json,
)

logger = logging.getLogger(__name__)


def prepare_external_theatres(
    request: ExternalTheatrePreparationRequest,
) -> ExternalTheatrePreparationResult:
    """Orchestrate full external theatre preparation.

    For each theatre in the request:
    1. Parse construct.json -> TheatreConstructMeta
    2. Extract enriched fixture -> TheatreFixtureInput
    3. Plan theatre checks -> list[PlannedCheck]
    4. Execute checks -> TheatreExecutionResult
    5. Build comparison bundle with shared event_keys/scope_keys

    Then:
    6. Generate cross-theatre candidates from all successful bundles
    7. Build builder feedback for each theatre

    Error handling: Per-theatre failures are captured in
    TheatrePreparationEntry.error and do not abort the remaining theatres.
    Candidate generation runs only on successful bundles.
    """
    entries: list[TheatrePreparationEntry] = []
    metas: list[Optional[TheatreConstructMeta]] = []

    for theatre_input in request.theatres:
        entry, meta = _prepare_single_theatre(
            theatre_input=theatre_input,
            event_keys=request.event_keys,
            scope_keys=request.scope_keys,
            certificate_id=request.certificate_id,
        )
        entries.append(entry)
        metas.append(meta)

    # Collect successful bundles for candidate generation
    successful_bundles = [e.bundle for e in entries if e.bundle is not None]
    candidates = generate_candidates(bundles=successful_bundles) if successful_bundles else []

    # Build feedback for each theatre with available meta + extraction
    feedback: list[BuilderFeedbackReport] = []
    for entry, meta in zip(entries, metas):
        if meta is not None and entry.extraction is not None:
            report = _build_builder_feedback(
                construct_slug=entry.construct_slug,
                meta=meta,
                extraction=entry.extraction,
            )
            feedback.append(report)

    total_successful = sum(1 for e in entries if e.bundle is not None)
    total_failed = sum(1 for e in entries if e.error is not None)

    result = ExternalTheatrePreparationResult(
        theatres=entries,
        candidates=candidates,
        feedback=feedback,
        event_keys_used=request.event_keys,
        scope_keys_used=request.scope_keys,
        total_theatres=len(request.theatres),
        total_successful=total_successful,
        total_failed=total_failed,
    )

    logger.info(
        "External theatre preparation: %d theatres, %d successful, %d failed, %d candidates",
        result.total_theatres,
        result.total_successful,
        result.total_failed,
        len(result.candidates),
    )

    return result


def _prepare_single_theatre(
    theatre_input: ExternalTheatreInput,
    event_keys: list[str],
    scope_keys: list[TheatreScopeKey],
    certificate_id: Optional[str],
) -> tuple[TheatrePreparationEntry, Optional[TheatreConstructMeta]]:
    """Prepare a single external theatre through the full pipeline.

    Calls:
    1. parse_construct_json(theatre_input.construct_json)
    2. extract_enriched_fixture(slug, version, meta)
    3. plan_theatre_checks(slug, meta)
    4. execute_theatre_checks(planned_checks_as_dicts, fixture)
    5. build_comparison_bundle(execution_result, fixture, certificate_id,
       event_keys, scope_keys)

    Returns (TheatrePreparationEntry, TheatreConstructMeta or None).
    The meta is returned separately for feedback generation.
    """
    slug = theatre_input.construct_slug
    version = theatre_input.construct_version

    # Step 1: Parse construct.json
    try:
        meta = parse_construct_json(theatre_input.construct_json)
    except (ValueError, Exception) as e:
        logger.warning("Parse failed for %s: %s", slug, e)
        entry = TheatrePreparationEntry(
            construct_slug=slug,
            construct_version=version,
            error=str(e),
        )
        return (entry, None)

    # Step 2: Extract enriched fixture
    extraction_result, fixture_input = extract_enriched_fixture(
        construct_slug=slug,
        construct_version=version,
        meta=meta,
    )

    if not extraction_result.success or fixture_input is None:
        entry = TheatrePreparationEntry(
            construct_slug=slug,
            construct_version=version,
            extraction=extraction_result,
            error=extraction_result.error or "Extraction failed",
        )
        return (entry, meta)

    # Step 3: Plan theatre checks
    try:
        planned = plan_theatre_checks(spec_slug=slug, meta=meta)
    except Exception as e:
        logger.warning("Check planning failed for %s: %s", slug, e)
        entry = TheatrePreparationEntry(
            construct_slug=slug,
            construct_version=version,
            extraction=extraction_result,
            error=f"Check planning failed: {e}",
        )
        return (entry, meta)

    # Step 4: Execute theatre checks
    planned_dicts = _planned_checks_to_dicts(planned)
    execution_result = execute_theatre_checks(
        planned_checks=planned_dicts,
        fixture=fixture_input,
    )

    # Step 5: Build comparison bundle
    # Critical None-vs-empty logic: pass None when caller's lists are empty
    # to trigger bundle builder's fallback behavior (SDD section 2.3, decision #4)
    try:
        bundle = build_comparison_bundle(
            execution_result=execution_result,
            fixture_input=fixture_input,
            certificate_id=certificate_id,
            event_keys=event_keys if event_keys else None,
            scope_keys=scope_keys if scope_keys else None,
        )
    except Exception as e:
        logger.warning("Bundle building failed for %s: %s", slug, e)
        entry = TheatrePreparationEntry(
            construct_slug=slug,
            construct_version=version,
            extraction=extraction_result,
            execution_passed=not execution_result.has_critical_failures,
            execution_failed=execution_result.has_critical_failures,
            error=f"Bundle building failed: {e}",
        )
        return (entry, meta)

    entry = TheatrePreparationEntry(
        construct_slug=slug,
        construct_version=version,
        extraction=extraction_result,
        bundle=bundle,
        execution_passed=not execution_result.has_critical_failures,
        execution_failed=execution_result.has_critical_failures,
    )

    return (entry, meta)


def _planned_checks_to_dicts(checks: list) -> list[dict]:
    """Convert PlannedCheck dataclass instances to dicts for the runner.

    The theatre_check_runner.execute_theatre_checks() expects list[dict]
    with "check_type" and "check_id" keys. PlannedCheck is a dataclass
    with those field names.
    """
    return [
        {"check_id": c.check_id, "check_type": c.check_type}
        for c in checks
    ]


def _build_builder_feedback(
    construct_slug: str,
    meta: TheatreConstructMeta,
    extraction: ExtractionResult,
) -> BuilderFeedbackReport:
    """Generate structured feedback for an external theatre builder.

    Required metadata (BLOCKED if missing):
    - theatre_templates (at least one)
    - construct name/slug

    Optional enrichment (DEGRADED if missing, recommendations):
    - verification_checks (TREMOR has, CORONA does not)
    - settlement_tiers (TREMOR has, CORONA does not)
    - explicit source IDs (TREMOR has, CORONA derives from name)
    - brier_type on templates

    Extraction feedback:
    - Each fallback from ExtractionResult.fallbacks_used
    - Success/failure per fixture category
    """
    required_items: list[BuilderFeedbackItem] = []
    optional_items: list[BuilderFeedbackItem] = []
    extraction_items: list[BuilderFeedbackItem] = []

    # --- Required items ---

    # Theatre templates
    if meta.theatre_templates:
        required_items.append(BuilderFeedbackItem(
            category="required",
            field="theatre_templates",
            status="present",
            message=f"{len(meta.theatre_templates)} theatre templates declared",
        ))
    else:
        required_items.append(BuilderFeedbackItem(
            category="required",
            field="theatre_templates",
            status="missing",
            message="No theatre templates found — construct cannot be verified",
        ))

    # Construct name
    if meta.name and meta.name != "unknown":
        required_items.append(BuilderFeedbackItem(
            category="required",
            field="construct_name",
            status="present",
            message=f"Construct name: {meta.name}",
        ))
    else:
        required_items.append(BuilderFeedbackItem(
            category="required",
            field="construct_name",
            status="missing",
            message="No construct name declared",
        ))

    # --- Optional items ---

    # Verification checks
    if meta.verification_checks:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="verification_checks",
            status="present",
            message=f"{len(meta.verification_checks)} verification checks declared",
        ))
    else:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="verification_checks",
            status="missing",
            message="No verification checks declared — oracle thresholds will use defaults",
        ))

    # Settlement tiers
    if meta.settlement_tiers:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="settlement_tiers",
            status="present",
            message=f"{len(meta.settlement_tiers)} settlement tiers declared",
        ))
    else:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="settlement_tiers",
            status="missing",
            message="No settlement tiers declared — all templates treated equally",
        ))

    # Explicit source IDs
    has_explicit_ids = all(
        s.id != s.name.lower().replace(" ", "_")
        for s in meta.osint_sources
        if s.name
    ) if meta.osint_sources else False
    if has_explicit_ids and meta.osint_sources:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="source_ids",
            status="present",
            message="All OSINT sources have explicit IDs",
        ))
    elif meta.osint_sources:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="source_ids",
            status="defaulted",
            message="Some source IDs derived from name — consider adding explicit 'id' fields",
        ))

    # Brier type on templates
    has_brier_type = any(t.brier_type is not None for t in meta.theatre_templates)
    if has_brier_type:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="brier_type",
            status="present",
            message="Templates declare explicit brier_type",
        ))
    else:
        optional_items.append(BuilderFeedbackItem(
            category="optional",
            field="brier_type",
            status="missing",
            message="No templates declare brier_type — defaulting to binary",
        ))

    # --- Extraction items ---

    # Fallbacks
    for fallback in extraction.fallbacks_used:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field=fallback,
            status="defaulted",
            message=f"Fallback applied: {fallback}",
        ))

    # Fixture category summaries
    if extraction.settlement_fixture_count > 0:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field="settlement_fixtures",
            status="enriched",
            message=f"{extraction.settlement_fixture_count} settlement fixtures generated",
        ))

    if extraction.oracle_fixture_count > 0:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field="oracle_fixtures",
            status="enriched",
            message=f"{extraction.oracle_fixture_count} oracle fixtures generated",
        ))

    if extraction.has_calibration:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field="calibration_fixture",
            status="enriched",
            message="Calibration fixture generated",
        ))

    if extraction.functional_fixture_count > 0:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field="functional_fixtures",
            status="enriched",
            message=f"{extraction.functional_fixture_count} functional fixtures generated",
        ))

    if extraction.has_failure_scenarios:
        extraction_items.append(BuilderFeedbackItem(
            category="extraction",
            field="failure_scenarios",
            status="enriched",
            message="Failure scenarios included (pass + fail)",
        ))

    # --- Readiness derivation ---
    # BLOCKED: extraction failed or no templates
    # DEGRADED: extraction succeeded but fallbacks were used
    # READY: extraction succeeded with no fallbacks
    if not extraction.success or not meta.theatre_templates:
        overall_readiness = "BLOCKED"
    elif extraction.fallbacks_used:
        overall_readiness = "DEGRADED"
    else:
        overall_readiness = "READY"

    return BuilderFeedbackReport(
        construct_slug=construct_slug,
        required_items=required_items,
        optional_items=optional_items,
        extraction_items=extraction_items,
        overall_readiness=overall_readiness,
    )
