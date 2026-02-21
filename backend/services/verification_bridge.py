"""
Verification Bridge — echelon-verify → SQLAlchemy adapter.

Runs the echelon-verify pipeline as a background task and persists results
to the database. Each task gets its own session (no sharing with request).
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_session
from backend.database.models import (
    VerificationRun,
    VerificationRunStatus,
    VerificationCertificate,
    VerificationReplayScore,
)

logger = logging.getLogger(__name__)

# Graceful import of echelon-verify (may not be installed)
try:
    from echelon_verify.pipeline import VerificationPipeline
    from echelon_verify.config import PipelineConfig, IngestionConfig, OracleConfig, ScoringConfig
    from echelon_verify.models import CalibrationCertificate, ReplayScore
    from echelon_verify.oracle.base import OracleAdapter
    from echelon_verify.scoring.base import AnthropicScorer

    ECHELON_VERIFY_AVAILABLE = True
except ImportError:
    ECHELON_VERIFY_AVAILABLE = False
    logger.warning("echelon-verify package not installed — verification bridge disabled")


def certificate_to_db(cert: "CalibrationCertificate") -> VerificationCertificate:
    """Convert echelon-verify CalibrationCertificate to SQLAlchemy model."""
    return VerificationCertificate(
        id=str(uuid.uuid4()),
        construct_id=cert.construct_id,
        domain=getattr(cert, "domain", "community_oracle"),
        replay_count=cert.replay_count,
        precision=cert.precision,
        recall=cert.recall,
        reply_accuracy=cert.reply_accuracy,
        composite_score=cert.composite_score,
        brier=cert.brier,
        sample_size=cert.sample_size,
        ground_truth_source=cert.ground_truth_source,
        commit_range=getattr(cert, "commit_range", ""),
        methodology_version=getattr(cert, "methodology_version", "v1"),
        scoring_model=cert.scoring_model,
        raw_scores_json=getattr(cert, "raw_scores", None),
        created_at=datetime.utcnow(),
    )


def replay_score_to_db(
    score: "ReplayScore", certificate_id: str
) -> VerificationReplayScore:
    """Convert echelon-verify ReplayScore to SQLAlchemy model."""
    return VerificationReplayScore(
        id=str(uuid.uuid4()),
        certificate_id=certificate_id,
        ground_truth_id=score.ground_truth_id,
        precision=score.precision,
        recall=score.recall,
        reply_accuracy=score.reply_accuracy,
        claims_total=score.claims_total,
        claims_supported=score.claims_supported,
        changes_total=score.changes_total,
        changes_surfaced=score.changes_surfaced,
        scoring_model=score.scoring_model,
        scoring_latency_ms=score.scoring_latency_ms,
        scored_at=score.scored_at,
    )


async def _update_run_progress(
    run_id: str, progress: int, total: int, status: VerificationRunStatus
) -> None:
    """Update run progress in a fresh session (called from pipeline callback)."""
    async with get_session() as session:
        await session.execute(
            update(VerificationRun)
            .where(VerificationRun.id == run_id)
            .values(progress=progress, total=total, status=status)
        )


async def run_verification_task(run_id: str) -> None:
    """Background task — runs the full echelon-verify pipeline.

    Opens its own session (not shared with request).
    Guarantees run reaches a terminal status (COMPLETED or FAILED).
    """
    if not ECHELON_VERIFY_AVAILABLE:
        async with get_session() as session:
            await session.execute(
                update(VerificationRun)
                .where(VerificationRun.id == run_id)
                .values(
                    status=VerificationRunStatus.FAILED,
                    error="echelon-verify package not installed",
                )
            )
        return

    try:
        async with get_session() as session:
            run = await session.get(VerificationRun, run_id)
            if run is None:
                logger.error("Verification run %s not found", run_id)
                return

            config_data = run.config_json or {}

            # Build pipeline config from stored config
            # github_token is passed at runtime, never persisted
            github_token = config_data.pop("_github_token", None)

            ingestion_config = IngestionConfig(
                repo_url=run.repo_url,
                github_token=github_token,
                limit=config_data.get("limit", 100),
                min_replays=config_data.get("min_replays", 50),
            )

            oracle_config = OracleConfig(
                oracle_type=config_data.get("oracle_type", "http"),
                oracle_url=config_data.get("oracle_url"),
                oracle_headers=config_data.get("oracle_headers", {}),
                oracle_module=config_data.get("oracle_module"),
                oracle_callable=config_data.get("oracle_callable"),
            )

            scoring_config = ScoringConfig()

            pipeline_config = PipelineConfig(
                ingestion=ingestion_config,
                oracle=oracle_config,
                scoring=scoring_config,
            )

            # Update status
            run.status = VerificationRunStatus.INGESTING
            await session.commit()

        # Run pipeline outside the session to avoid long-lived transactions
        oracle = OracleAdapter.from_config(pipeline_config.oracle)
        scorer = AnthropicScorer(pipeline_config.scoring)
        pipeline = VerificationPipeline(pipeline_config, oracle, scorer)

        def progress_callback(completed: int, total: int) -> None:
            """Sync callback — schedules async DB update."""
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    _update_run_progress(run_id, completed, total, VerificationRunStatus.SCORING)
                )
            except RuntimeError:
                pass  # No running loop — skip progress update

        result = await pipeline.run(progress=progress_callback)

        # Persist results
        async with get_session() as session:
            db_cert = certificate_to_db(result.certificate)
            session.add(db_cert)
            await session.flush()  # Get cert ID

            for score in result.replay_scores:
                db_score = replay_score_to_db(score, db_cert.id)
                session.add(db_score)

            await session.execute(
                update(VerificationRun)
                .where(VerificationRun.id == run_id)
                .values(
                    status=VerificationRunStatus.COMPLETED,
                    certificate_id=db_cert.id,
                    progress=result.certificate.replay_count,
                    total=result.certificate.replay_count,
                )
            )

    except Exception as e:
        logger.error("Verification run %s failed: %s", run_id, e, exc_info=True)
        try:
            async with get_session() as session:
                await session.execute(
                    update(VerificationRun)
                    .where(VerificationRun.id == run_id)
                    .values(
                        status=VerificationRunStatus.FAILED,
                        error=str(e)[:2000],
                    )
                )
        except Exception as inner_e:
            logger.error(
                "Failed to update run %s to FAILED: %s", run_id, inner_e, exc_info=True
            )
