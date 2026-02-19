"""Verification pipeline orchestrator — wires all 4 stages together."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TYPE_CHECKING

from echelon_verify.certificate.generator import CertificateGenerator
from echelon_verify.ingestion.github import GitHubIngester
from echelon_verify.models import (
    CalibrationCertificate,
    GroundTruthRecord,
    OracleOutput,
    ReplayScore,
)
from echelon_verify.oracle.base import OracleAdapter
from echelon_verify.scoring.base import ScoringProvider
from echelon_verify.storage import Storage

if TYPE_CHECKING:
    from echelon_verify.config import PipelineConfig

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class VerificationPipeline:
    """Coordinates ingest → invoke oracle → score → certify."""

    def __init__(
        self,
        config: PipelineConfig,
        oracle: OracleAdapter,
        scorer: ScoringProvider,
        storage: Storage | None = None,
    ) -> None:
        self._config = config
        self._oracle = oracle
        self._scorer = scorer
        self._storage = storage or Storage(config.output_dir)

    def _repo_key(self) -> str:
        """Extract 'owner/repo' from repo_url for Storage.repo_dir()."""
        parts = self._config.ingestion.repo_url.rstrip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        return "unknown"

    def _gt_path(self, repo_key: str) -> Path:
        return self._storage.repo_dir(repo_key) / "ground_truth.jsonl"

    async def ingest_only(self) -> list[GroundTruthRecord]:
        """Stage 1: Fetch ground truth from GitHub and cache to storage."""
        ingester = GitHubIngester(self._config.ingestion)
        repo_key = self._repo_key()
        gt_path = self._gt_path(repo_key)

        existing = self._storage.read_jsonl(gt_path, GroundTruthRecord)
        cached_ids = {r.id for r in existing} if existing else None

        records = await ingester.ingest(cached_ids=cached_ids)

        if records:
            for record in records:
                self._storage.append_jsonl(gt_path, record)
            logger.info("Ingested %d new ground truth records", len(records))

        return existing + records if existing else records

    async def score_only(
        self,
        progress: ProgressCallback | None = None,
    ) -> CalibrationCertificate:
        """Stages 2-4: Score cached data and generate certificate."""
        repo_key = self._repo_key()
        gt_path = self._gt_path(repo_key)

        records = self._storage.read_jsonl(gt_path, GroundTruthRecord)
        if not records:
            raise ValueError("No cached ground truth data. Run ingest first.")

        return await self._score_and_certify(records, repo_key, progress)

    async def run(
        self,
        progress: ProgressCallback | None = None,
    ) -> CalibrationCertificate:
        """Full pipeline: ingest → invoke → score → certify."""
        records = await self.ingest_only()
        if not records:
            raise ValueError("No ground truth records ingested.")

        return await self._score_and_certify(records, self._repo_key(), progress)

    async def _score_and_certify(
        self,
        records: list[GroundTruthRecord],
        repo_key: str,
        progress: ProgressCallback | None = None,
    ) -> CalibrationCertificate:
        """Score all records and generate certificate."""
        total = len(records)
        scores: list[ReplayScore] = []
        completed = 0

        for record in records:
            try:
                score = await self._score_single(record, repo_key)
                scores.append(score)
            except Exception:
                logger.warning(
                    "Replay failed for %s, skipping", record.id, exc_info=True
                )

            completed += 1
            if progress:
                progress(completed, total)

        if not scores:
            raise ValueError("All replays failed — no scores to certify.")

        if len(scores) < self._config.min_replays:
            logger.warning(
                "Only %d replays succeeded (minimum %d) — generating partial certificate",
                len(scores),
                self._config.min_replays,
            )

        gen = CertificateGenerator(
            construct_id=self._config.construct_id,
            ground_truth_source=self._config.ingestion.repo_url,
            commit_range=f"{records[0].id}..{records[-1].id}",
            scoring_model=self._config.scoring.model,
            methodology_version=self._config.scoring.prompt_version,
            composite_weights=self._config.composite_weights,
        )
        cert = gen.generate(scores)

        self._storage.write_certificate(cert)
        logger.info(
            "Certificate generated: %s (composite=%.3f, brier=%.3f, n=%d)",
            cert.certificate_id,
            cert.composite_score,
            cert.brier,
            cert.replay_count,
        )
        return cert

    async def _score_single(
        self, record: GroundTruthRecord, repo_key: str
    ) -> ReplayScore:
        """Score a single replay: generate question → invoke oracle → score."""
        # Generate follow-up question
        question = await self._scorer.generate_follow_up_question(record)

        # Invoke oracle
        oracle_output = await self._oracle.invoke(record, question)

        # Score all dimensions
        prec_score, claims_total, claims_supported, prec_raw = (
            await self._scorer.score_precision(record, oracle_output)
        )
        rec_score, changes_total, changes_surfaced, rec_raw = (
            await self._scorer.score_recall(record, oracle_output)
        )
        ra_score, ra_raw = await self._scorer.score_reply_accuracy(record, oracle_output)

        score = ReplayScore(
            ground_truth_id=record.id,
            precision=prec_score,
            recall=rec_score,
            reply_accuracy=ra_score,
            claims_total=claims_total,
            claims_supported=claims_supported,
            changes_total=changes_total,
            changes_surfaced=changes_surfaced,
            scoring_model=self._config.scoring.model,
            scoring_latency_ms=0,
            scored_at=datetime.now(timezone.utc),
            raw_scoring_output={
                "precision": prec_raw,
                "recall": rec_raw,
                "reply_accuracy": ra_raw,
            },
        )

        # Persist oracle output and score as they complete
        rdir = self._storage.repo_dir(repo_key)
        self._storage.append_jsonl(rdir / "oracle_outputs.jsonl", oracle_output)
        self._storage.append_jsonl(rdir / "replay_scores.jsonl", score)

        return score
