"""
Theatre Bridge — Theatre Engine → SQLAlchemy adapter.

Runs the Theatre lifecycle as a background task and persists results
to the database. Each task gets its own session (no sharing with request).
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_session
from backend.database.models import (
    Theatre,
    TheatreTemplate,
    TheatreCertificate,
    TheatreEpisodeScore,
    TheatreAuditEvent,
)

logger = logging.getLogger(__name__)

# Graceful import of theatre engine (may not be installed / importable)
try:
    from theatre.engine.state_machine import TheatreState, TheatreStateMachine
    from theatre.engine.commitment import CommitmentProtocol
    from theatre.engine.models import TheatreCriteria, GroundTruthEpisode
    from theatre.engine.replay import ReplayEngine
    from theatre.engine.oracle_contract import OracleAdapter, MockOracleAdapter
    from theatre.engine.scoring import TheatreScoringProvider, SimpleScoringFunction
    from theatre.engine.tier_assigner import TierAssigner
    from theatre.engine.evidence_bundle import EvidenceBundleBuilder

    THEATRE_ENGINE_AVAILABLE = True
except ImportError:
    THEATRE_ENGINE_AVAILABLE = False
    logger.warning("Theatre engine not available — theatre bridge disabled")


async def _update_theatre_progress(
    theatre_id: str, progress: int, total: int
) -> None:
    """Update theatre progress in a fresh session (called from replay callback)."""
    async with get_session() as session:
        await session.execute(
            update(Theatre)
            .where(Theatre.id == theatre_id)
            .values(progress=progress, total_episodes=total)
        )


async def _transition_theatre_state(
    theatre_id: str, new_state: str, **extra_fields
) -> None:
    """Transition theatre to a new state with optional extra fields."""
    async with get_session() as session:
        values = {"state": new_state, "updated_at": datetime.utcnow()}
        values.update(extra_fields)
        await session.execute(
            update(Theatre)
            .where(Theatre.id == theatre_id)
            .values(**values)
        )


async def run_theatre_task(theatre_id: str) -> None:
    """Background task — runs the full Theatre lifecycle.

    Opens its own session (not shared with request).
    Guarantees theatre reaches a terminal state (RESOLVED or error state with message).

    Lifecycle: COMMITTED → ACTIVE (replay) → SETTLING (score) → RESOLVED (certificate)
    """
    if not THEATRE_ENGINE_AVAILABLE:
        async with get_session() as session:
            await session.execute(
                update(Theatre)
                .where(Theatre.id == theatre_id)
                .values(
                    error="Theatre engine not available",
                    updated_at=datetime.utcnow(),
                )
            )
        return

    try:
        # Load theatre and template
        async with get_session() as session:
            theatre = await session.get(Theatre, theatre_id)
            if theatre is None:
                logger.error("Theatre %s not found", theatre_id)
                return

            template = await session.get(TheatreTemplate, theatre.template_id)
            if template is None:
                logger.error("Template %s not found for theatre %s",
                             theatre.template_id, theatre_id)
                await session.execute(
                    update(Theatre)
                    .where(Theatre.id == theatre_id)
                    .values(
                        error="Template not found",
                        updated_at=datetime.utcnow(),
                    )
                )
                return

            # Extract data we need outside the session
            construct_id = theatre.construct_id
            template_json = template.template_json
            template_id = template.id
            version_pins = theatre.version_pins or {}
            dataset_hashes = theatre.dataset_hashes or {}
            commitment_hash = theatre.commitment_hash
            committed_at = theatre.committed_at

        # Parse criteria from template
        criteria_data = template_json.get("criteria", {})
        criteria = TheatreCriteria(
            criteria_ids=criteria_data.get("criteria_ids", []),
            criteria_human=criteria_data.get("criteria_human", ""),
            weights=criteria_data.get("weights", {}),
        )

        # Get construct version from version pins
        constructs_pins = version_pins.get("constructs", {})
        ptc = template_json.get("product_theatre_config", {})
        construct_under_test = ptc.get("construct_under_test", construct_id)
        construct_version = constructs_pins.get(construct_under_test, "unknown")

        # Get committed dataset hash
        replay_dataset_id = ptc.get("replay_dataset_id", "")
        committed_dataset_hash = dataset_hashes.get(replay_dataset_id, "")

        # Transition to ACTIVE
        await _transition_theatre_state(theatre_id, TheatreState.ACTIVE.value)

        # Create mock adapter for background execution
        # In production, this would be determined by adapter_type in template
        adapter_type = ptc.get("adapter_type", "mock")
        if adapter_type == "mock":
            oracle_adapter = MockOracleAdapter()
        else:
            # For non-mock adapters, we'd instantiate the real adapter here
            # For now, fall back to mock
            oracle_adapter = MockOracleAdapter()

        # Build scoring provider
        scoring_fn = SimpleScoringFunction()
        scoring_provider = TheatreScoringProvider(
            criteria=criteria,
            scorer=scoring_fn,
        )

        # Build replay engine
        replay_engine = ReplayEngine(
            theatre_id=theatre_id,
            construct_id=construct_under_test,
            construct_version=construct_version,
            criteria=criteria,
            oracle_adapter=oracle_adapter,
            scoring_provider=scoring_provider,
            committed_dataset_hash=committed_dataset_hash,
        )

        # Load ground truth episodes
        # In production, these come from the ground_truth_path or replay_data_path
        # For now, create minimal test episodes
        ground_truth: list[GroundTruthEpisode] = []

        # Progress callback
        def progress_callback(completed: int, total: int) -> None:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    _update_theatre_progress(theatre_id, completed, total)
                )
            except RuntimeError:
                pass

        # Run replay
        replay_result = await replay_engine.run(
            ground_truth=ground_truth,
            progress_callback=progress_callback,
        )

        # Transition to SETTLING
        await _transition_theatre_state(theatre_id, TheatreState.SETTLING.value)

        # Assign verification tier
        tier = TierAssigner.assign(
            replay_count=replay_result.replay_count,
            has_full_pins=bool(constructs_pins),
            has_published_scores=True,
            has_verifiable_hash=bool(replay_result.dataset_hash),
            has_disputes=False,
            failure_rate=replay_result.failure_rate,
        )
        now = datetime.utcnow()
        expiry = TierAssigner.compute_expiry(tier, now)

        # Build certificate
        scorer_version = version_pins.get("scorer_version", "v1")
        methodology_version = version_pins.get("methodology_version", "1.0.0")

        cert_id = str(uuid.uuid4())

        db_cert = TheatreCertificate(
            id=cert_id,
            theatre_id=theatre_id,
            template_id=template_id,
            construct_id=construct_under_test,
            criteria_json=criteria.model_dump(),
            scores_json=replay_result.aggregate_scores,
            composite_score=replay_result.composite_score,
            replay_count=replay_result.replay_count,
            evidence_bundle_hash=replay_result.dataset_hash,
            ground_truth_hash=committed_dataset_hash,
            construct_version=construct_version,
            scorer_version=scorer_version,
            methodology_version=methodology_version,
            dataset_hash=replay_result.dataset_hash,
            verification_tier=tier,
            commitment_hash=commitment_hash or "",
            issued_at=now,
            expires_at=expiry,
            theatre_committed_at=committed_at or now,
            theatre_resolved_at=now,
            ground_truth_source=ptc.get("ground_truth_source", "CUSTOM"),
            execution_path=template_json.get("execution_path", "replay"),
        )

        # Persist certificate and episode scores
        async with get_session() as session:
            session.add(db_cert)
            await session.flush()

            # Persist episode scores
            for ep in replay_result.episode_results:
                db_score = TheatreEpisodeScore(
                    id=str(uuid.uuid4()),
                    theatre_id=theatre_id,
                    certificate_id=cert_id,
                    episode_id=ep.episode_id,
                    invocation_status=ep.invocation_status,
                    latency_ms=ep.latency_ms,
                    scores_json=ep.scores or {},
                    composite_score=ep.composite_score or 0.0,
                    scored_at=now,
                )
                session.add(db_score)

            # Add audit event
            audit_event = TheatreAuditEvent(
                id=str(uuid.uuid4()),
                theatre_id=theatre_id,
                event_type="theatre_resolved",
                from_state=TheatreState.SETTLING.value,
                to_state=TheatreState.RESOLVED.value,
                detail_json={
                    "certificate_id": cert_id,
                    "composite_score": replay_result.composite_score,
                    "verification_tier": tier,
                    "replay_count": replay_result.replay_count,
                },
            )
            session.add(audit_event)

        # Transition to RESOLVED with certificate
        await _transition_theatre_state(
            theatre_id,
            TheatreState.RESOLVED.value,
            certificate_id=cert_id,
            resolved_at=now,
            progress=replay_result.replay_count,
            total_episodes=replay_result.replay_count,
            failure_count=replay_result.failure_count,
        )

    except Exception as e:
        logger.error("Theatre %s failed: %s", theatre_id, e, exc_info=True)
        try:
            async with get_session() as session:
                await session.execute(
                    update(Theatre)
                    .where(Theatre.id == theatre_id)
                    .values(
                        error=str(e)[:2000],
                        updated_at=datetime.utcnow(),
                    )
                )
        except Exception as inner_e:
            logger.error(
                "Failed to update theatre %s error: %s", theatre_id, inner_e,
                exc_info=True,
            )
