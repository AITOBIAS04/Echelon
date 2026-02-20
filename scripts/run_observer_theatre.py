"""Runner Script — end-to-end Observer Theatre execution.

Single entry point that wires Cycle-027 verification pipeline into
Cycle-031 Theatre engine to produce a real CalibrationCertificate.

Usage:
    python scripts/run_observer_theatre.py --repo AITOBIAS04/Echelon --limit 10
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on the path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from theatre.engine.canonical_json import canonical_json
from theatre.engine.certificate import TheatreCalibrationCertificate
from theatre.engine.commitment import CommitmentProtocol
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.engine.models import AuditEvent, BundleManifest, TheatreCriteria
from theatre.engine.replay import ReplayEngine
from theatre.engine.scoring import TheatreScoringProvider
from theatre.engine.template_validator import TemplateValidator
from theatre.engine.tier_assigner import TierAssigner
import httpx

from theatre.integration import (
    GitHubIngester,
    GroundTruthAdapter,
    GroundTruthRecord,
    ObserverOracleAdapter,
    ObserverScoringFunction,
    load_observer_template,
)

logger = logging.getLogger(__name__)

# Stable engine type — identifies the Theatre engine kind.
# Distinct from template_id (specific template) and certificate_id (per-run).
THEATRE_ID = "product_replay_engine_v1"

# Deterministic namespace for RLMF episode UUIDs (UUID5)
RLMF_NAMESPACE = uuid.UUID("b7e15162-7c8e-4e13-b3e1-83b1c3e75f21")


def populate_template_runtime_fields(
    template: dict,
    construct_version: str,
    dataset_hash: str,
) -> dict:
    """Populate template version_pins and dataset_hashes with real values.

    Replaces placeholder values in the template with actual runtime data.
    Returns a new dict (does not mutate original).
    """
    populated = json.loads(json.dumps(template))  # deep copy

    # Populate version_pins.constructs with real construct version
    if "version_pins" in populated:
        constructs = populated["version_pins"].get("constructs", {})
        for construct_id in constructs:
            constructs[construct_id] = construct_version
        populated["version_pins"]["constructs"] = constructs

    # Populate dataset_hashes with real dataset hash
    if "dataset_hashes" in populated:
        for dataset_key in populated["dataset_hashes"]:
            populated["dataset_hashes"][dataset_key] = dataset_hash

    return populated


def certificate_to_schema_dict(cert: TheatreCalibrationCertificate) -> dict:
    """Convert a TheatreCalibrationCertificate to a dict matching the JSON Schema.

    Handles datetime serialisation to ISO 8601 and optional fields.
    """
    data = cert.model_dump()

    # Serialise datetimes to ISO 8601 strings
    for key in ("issued_at", "expires_at", "theatre_committed_at", "theatre_resolved_at"):
        val = data.get(key)
        if isinstance(val, datetime):
            data[key] = val.isoformat()
        elif val is None and key == "expires_at":
            # Schema requires expires_at — use far-future for UNVERIFIED
            data[key] = datetime(2099, 12, 31, 23, 59, 59).isoformat()

    # Serialise criteria to plain dict
    if hasattr(data.get("criteria"), "model_dump"):
        data["criteria"] = data["criteria"].model_dump()

    # Remove optional fields that are None (not in schema required)
    for optional_key in ("brier_score", "ece", "construct_chain_versions", "ground_truth_hash", "methodology_version"):
        if data.get(optional_key) is None:
            data.pop(optional_key, None)

    return data


def build_rlmf_record(
    episode: Any,
    oracle_output: dict[str, Any] | None,
    scores: dict[str, float],
    criteria_ids: list[str],
    theatre_id: str,
    config_hash: str,
    construct_id: str,
    construct_version: str,
    certificate_id: str,
    invocation_status: str,
    composite_score: float,
    timestep: int,
) -> dict:
    """Build an RLMF v2.0.1 export record for a single replay episode."""
    # Deterministic UUID from episode_id
    rlmf_episode_id = str(uuid.uuid5(RLMF_NAMESPACE, episode.episode_id))

    # Ground truth hash for this specific episode
    gt_hash = hashlib.sha256(
        canonical_json(episode.model_dump()).encode("utf-8")
    ).hexdigest()

    # Classify outcome: "verified" if composite >= 0.5, else "unverified"
    outcome = "verified" if composite_score >= 0.5 else "unverified"

    return {
        "episode_id": rlmf_episode_id,
        "theatre_id": theatre_id,
        "execution_path": "replay",
        "config_hash": config_hash,
        "criteria_ids": criteria_ids,
        "timestep": timestep,
        "state_features": {
            "input_data": episode.input_data,
            "construct_output": oracle_output or {},
            "ground_truth": episode.model_dump(),
            "ground_truth_hash": gt_hash,
        },
        "action_taken": outcome,
        "replay_output_class": outcome,
        "settlement": {
            "resolved_option": outcome,
            "success": composite_score >= 0.5,
            "criteria_scores": scores,
            "resolution_mode": "replay",
        },
        "verification": {
            "construct_id": construct_id,
            "construct_version": construct_version,
            "invocation_status": invocation_status.lower(),
            "certificate_id": certificate_id,
        },
        "metadata": {
            "schema_version": "2.0.1",
        },
    }


async def run_observer_theatre(
    records: list[GroundTruthRecord],
    output_dir: Path,
    anthropic_api_key: str | None = None,
    construct_version: str = "0000000",
    verbose: bool = False,
) -> Path:
    """Execute the full Observer Theatre lifecycle.

    Args:
        records: Pre-ingested PR ground truth records.
        output_dir: Base output directory.
        anthropic_api_key: Anthropic API key (None = use env default).
        construct_version: Git commit hash of construct under test.
        verbose: Enable verbose logging.

    Returns:
        Path to the written certificate file.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # ── Identity layer ────────────────────────────────────────────────
    # theatre_id  = stable engine type (product_replay_engine_v1)
    # template_id = stable template name (product_observer_v1, from template)
    # certificate_id = per-run UUID
    theatre_id = THEATRE_ID

    # ── Step 0: Generate certificate_id at run start ─────────────────
    certificate_id = str(uuid.uuid4())
    logger.info("Certificate ID: %s", certificate_id)

    # ── Step 1: Ingestion (records already provided) ─────────────────
    logger.info("Processing %d ground truth records", len(records))

    # ── Step 2: Generate follow-up questions ─────────────────────────
    scorer = ObserverScoringFunction(api_key=anthropic_api_key)
    follow_up_questions: dict[str, str] = {}

    for record in records:
        try:
            question = await scorer.generate_follow_up_question(
                title=record.title,
                description=record.description,
                diff_content=record.diff_content,
            )
            follow_up_questions[record.id] = question
        except Exception:
            logger.exception("Failed to generate follow-up for %s", record.id)
            follow_up_questions[record.id] = ""

    # ── Step 3: Convert to GroundTruthEpisodes ───────────────────────
    adapter = GroundTruthAdapter()
    adapter.set_follow_up_questions(follow_up_questions)
    episodes = adapter.convert(records)
    logger.info("Converted %d episodes", len(episodes))

    # ── Step 4: Compute dataset hash via canonical_json + SHA-256 ────
    dataset_hash = ReplayEngine._compute_dataset_hash(episodes)
    logger.info("Dataset hash: %s", dataset_hash)

    # ── Step 4.5: Populate template with real version_pins and dataset_hashes
    raw_template = load_observer_template()
    populated_template = populate_template_runtime_fields(
        template=raw_template,
        construct_version=construct_version,
        dataset_hash=dataset_hash,
    )

    # ── Step 5: Load + validate template via TemplateValidator ───────
    schema_path = _ROOT / "docs" / "schemas" / "echelon_theatre_schema_v2.json"
    theatre_schema = json.loads(schema_path.read_text())
    validator = TemplateValidator(schema=theatre_schema)
    errors = validator.validate(populated_template, is_certificate_run=True)
    if errors:
        raise ValueError(f"Template validation failed: {errors}")
    logger.info("Template validated successfully")

    # ── Step 5.5: template_id = stable template name from template file
    template_id = populated_template["theatre_id"]  # "product_observer_v1"
    logger.info("Theatre ID: %s | Template ID: %s", theatre_id, template_id)

    # ── Step 6: Create CommitmentReceipt ─────────────────────────────
    version_pins = populated_template["version_pins"]
    dataset_hashes = populated_template["dataset_hashes"]

    receipt = CommitmentProtocol.create_receipt(
        theatre_id=theatre_id,
        template=populated_template,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes,
    )
    logger.info("Commitment hash: %s", receipt.commitment_hash)

    # ── Step 7: Build ReplayEngine with oracle + scoring bridges ─────
    construct_id = populated_template["product_theatre_config"]["construct_under_test"]
    criteria = TheatreCriteria(**populated_template["criteria"])

    oracle_adapter = ObserverOracleAdapter(api_key=anthropic_api_key)
    scoring_provider = TheatreScoringProvider(criteria=criteria, scorer=scorer)

    engine = ReplayEngine(
        theatre_id=theatre_id,
        construct_id=construct_id,
        construct_version=construct_version,
        criteria=criteria,
        oracle_adapter=oracle_adapter,
        scoring_provider=scoring_provider,
        committed_dataset_hash=dataset_hash,
    )

    # ── Step 8: Run replay ───────────────────────────────────────────
    def progress_callback(current: int, total: int) -> None:
        logger.info("Progress: %d/%d episodes", current, total)

    replay_result = await engine.run(episodes, progress_callback=progress_callback)
    resolved_at = datetime.utcnow()
    logger.info(
        "Replay complete: %d scored, %d failures, composite=%.3f",
        replay_result.scored_count,
        replay_result.failure_count,
        replay_result.composite_score,
    )

    # ── Step 9: Assign tier ──────────────────────────────────────────
    tier = TierAssigner.assign(
        replay_count=replay_result.replay_count,
        has_full_pins=bool(version_pins.get("constructs")),
        has_published_scores=True,
        has_verifiable_hash=True,
        has_disputes=False,
        failure_rate=replay_result.failure_rate,
    )
    issued_at = datetime.utcnow()
    expires_at = TierAssigner.compute_expiry(tier, issued_at)
    logger.info("Tier: %s", tier)

    # ── Step 9.5: Build evidence bundle ──────────────────────────────
    # Bundle directory uses template_id (the specific template being verified)
    bundle = EvidenceBundleBuilder(theatre_id=template_id, output_dir=output_dir)

    # Write ground truth
    bundle.write_ground_truth(
        dataset=[ep.model_dump() for ep in episodes],
        filename="observer_prs.jsonl",
    )

    # Write invocations and per-episode scores
    for ep_result in replay_result.episode_results:
        bundle.write_invocation(
            episode_id=ep_result.episode_id,
            request={"episode_id": ep_result.episode_id, "status": ep_result.invocation_status},
            response={
                "oracle_output": ep_result.oracle_output,
                "scores": ep_result.scores,
                "composite": ep_result.composite_score,
            },
        )
        if ep_result.scores:
            bundle.write_episode_score({
                "episode_id": ep_result.episode_id,
                "scores": ep_result.scores,
                "composite_score": ep_result.composite_score,
                "status": ep_result.invocation_status,
            })

    # Write aggregate scores
    bundle.write_aggregate_scores({
        "scores": replay_result.aggregate_scores,
        "composite_score": replay_result.composite_score,
        "replay_count": replay_result.replay_count,
        "scored_count": replay_result.scored_count,
        "failure_count": replay_result.failure_count,
        "failure_rate": replay_result.failure_rate,
    })

    # Write template and commitment receipt
    bundle.write_template(populated_template)
    bundle.write_commitment_receipt(receipt)

    # ── Step 9.6: Build RLMF export records ──────────────────────────
    episode_map = {ep.episode_id: ep for ep in episodes}
    rlmf_records: list[dict] = []

    for idx, ep_result in enumerate(replay_result.episode_results):
        episode = episode_map[ep_result.episode_id]
        rlmf_record = build_rlmf_record(
            episode=episode,
            oracle_output=ep_result.oracle_output,
            scores=ep_result.scores or {},
            criteria_ids=criteria.criteria_ids,
            theatre_id=theatre_id,
            config_hash=receipt.commitment_hash,
            construct_id=construct_id,
            construct_version=construct_version,
            certificate_id=certificate_id,
            invocation_status=ep_result.invocation_status,
            composite_score=ep_result.composite_score or 0.0,
            timestep=idx,
        )
        rlmf_records.append(rlmf_record)

    # ── Step 9.7: Validate RLMF records against schema ───────────────
    rlmf_schema_path = _ROOT / "docs" / "schemas" / "echelon_rlmf_schema_v2.json"
    rlmf_schema = json.loads(rlmf_schema_path.read_text())

    try:
        import jsonschema
        for record in rlmf_records:
            jsonschema.validate(instance=record, schema=rlmf_schema)
        logger.info("All %d RLMF records validate against schema", len(rlmf_records))
    except ImportError:
        logger.warning("jsonschema not installed — skipping RLMF validation")
    except jsonschema.ValidationError as e:
        raise ValueError(f"RLMF schema validation failed: {e.message}") from e

    # Write RLMF export to bundle
    bundle.write_rlmf_export(rlmf_records)

    # ── Step 9.8: Compute file inventory and bundle hash ─────────────
    file_inventory = bundle.compute_file_inventory()
    evidence_bundle_hash = bundle.compute_bundle_hash()

    # Write manifest (with file_inventory, after all evidence files written)
    manifest = BundleManifest(
        theatre_id=theatre_id,
        template_id=template_id,
        construct_id=construct_id,
        execution_path="replay",
        commitment_hash=receipt.commitment_hash,
        file_inventory=file_inventory,
    )
    bundle.write_manifest(manifest)

    # ── Step 10: Build certificate with certificate_id from Step 0 ───
    certificate = TheatreCalibrationCertificate(
        certificate_id=certificate_id,
        theatre_id=theatre_id,
        template_id=template_id,
        construct_id=construct_id,
        criteria=criteria,
        scores=replay_result.aggregate_scores,
        composite_score=replay_result.composite_score,
        precision=replay_result.aggregate_scores.get("precision"),
        recall=replay_result.aggregate_scores.get("recall"),
        reply_accuracy=replay_result.aggregate_scores.get("reply_accuracy"),
        replay_count=replay_result.replay_count,
        evidence_bundle_hash=evidence_bundle_hash,
        ground_truth_hash=dataset_hash,
        construct_version=construct_version,
        scorer_version=version_pins.get("scorer_version", "unknown"),
        methodology_version=version_pins.get("methodology_version", "1.0.0"),
        dataset_hash=replay_result.dataset_hash,
        verification_tier=tier,
        commitment_hash=receipt.commitment_hash,
        issued_at=issued_at,
        expires_at=expires_at,
        theatre_committed_at=receipt.committed_at,
        theatre_resolved_at=resolved_at,
        ground_truth_source="GITHUB_API",
        execution_path="replay",
    )

    # ── Step 11: Validate certificate against JSON Schema ────────────
    cert_dict = certificate_to_schema_dict(certificate)

    cert_schema_path = _ROOT / "docs" / "schemas" / "echelon_certificate_schema.json"
    cert_schema = json.loads(cert_schema_path.read_text())

    try:
        import jsonschema
        jsonschema.validate(instance=cert_dict, schema=cert_schema)
        logger.info("Certificate validates against schema")
    except ImportError:
        logger.warning("jsonschema not installed — skipping schema validation")
    except jsonschema.ValidationError as e:
        raise ValueError(f"Certificate schema validation failed: {e.message}") from e

    # Write certificate to evidence bundle
    bundle.write_certificate(cert_dict)

    # Validate bundle completeness
    missing = bundle.validate_minimum_files()
    if missing:
        logger.warning("Evidence bundle missing files: %s", missing)

    # ── Step 12: Write certificate to output ─────────────────────────
    cert_dir = output_dir / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / f"{template_id}.json"
    cert_path.write_text(json.dumps(cert_dict, indent=2))
    logger.info("Certificate written to %s", cert_path)

    return cert_path


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Observer Theatre end-to-end",
    )
    parser.add_argument(
        "--repo",
        default="AITOBIAS04/Echelon",
        help="GitHub repository (owner/repo)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of PRs to process",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for certificates and evidence bundles",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    github_token = os.environ.get("GITHUB_TOKEN")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not anthropic_api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable required")
        sys.exit(1)

    # Ingest PRs from GitHub
    if not github_token:
        print("WARNING: GITHUB_TOKEN not set — API rate limits will be very low (60 req/hr)")

    print(f"Ingesting up to {args.limit} merged PRs from {args.repo}...")

    ingester = GitHubIngester(token=github_token)
    try:
        records = await ingester.ingest(repo=args.repo, limit=args.limit)
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: GitHub API returned {exc.response.status_code}: {exc.response.text[:200]}")
        sys.exit(1)
    except httpx.ConnectError as exc:
        print(f"ERROR: Could not connect to GitHub API: {exc}")
        sys.exit(1)

    if not records:
        print(f"No merged PRs found in {args.repo}")
        sys.exit(0)

    print(f"Ingested {len(records)} merged PRs")

    output_dir = Path(args.output_dir)
    cert_path = await run_observer_theatre(
        records,
        output_dir=output_dir,
        anthropic_api_key=anthropic_api_key,
        verbose=args.verbose,
    )
    print(f"Certificate written to {cert_path}")


if __name__ == "__main__":
    asyncio.run(main())
