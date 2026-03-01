"""Runner Script — Construct Calibration Pipeline.

Produces CalibrationCertificates for construct semantic accuracy verification.
Deterministic replay: pre-annotated fixtures, no LLM, no API calls.

Usage:
    python scripts/run_construct_calibration.py --construct community_oracle_v1
    python scripts/run_construct_calibration.py --construct community_oracle_v1 --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on the path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from theatre.engine.certificate import TheatreCalibrationCertificate
from theatre.engine.commitment import CommitmentProtocol, CommitmentReceipt
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.engine.models import BundleManifest, GroundTruthEpisode, TheatreCriteria
from theatre.engine.replay import ReplayEngine
from theatre.engine.scoring import TheatreScoringProvider
from theatre.engine.tier_assigner import TierAssigner
from theatre.scoring import DeterministicOracleAdapter
from theatre.scoring.construct_calibration_scorer import ConstructCalibrationScorer

logger = logging.getLogger(__name__)

# Stable engine type
THEATRE_ID = "product_replay_engine_v1"

# Fixed epoch for deterministic evidence bundle hashes in fixture mode.
# Commitment receipt timestamps must be stable for hash reproducibility.
_FIXTURE_EPOCH = datetime(2026, 3, 1, 0, 0, 0)

# Fixture base path
FIXTURE_BASE = _ROOT / "theatre" / "fixtures" / "construct_calibration"

# Construct registry
CONSTRUCTS = {
    "community_oracle_v1": {
        "template": "CONSTRUCT_CALIBRATION_V1.template.json",
        "dataset": "community_oracle_v1_fixtures.json",
        "scorer_class": ConstructCalibrationScorer,
        "construct_id": "community_oracle_v1",
        "construct_version": "v1.0.0-fixtures",
    },
}


def _normalize_template_for_schema(template: dict) -> dict:
    """Transform fixture template to conform to schema v2.0.1."""
    normalized = json.loads(json.dumps(template))  # deep copy

    # Remove non-schema root properties
    normalized.pop("template_id", None)
    normalized.pop("evidence_bundle", None)
    normalized.pop("inquiry_class", None)
    normalized.pop("domain", None)
    normalized.pop("version", None)

    # Add required 'scoring' property
    if "scoring" not in normalized:
        normalized["scoring"] = {}

    # Fix product_theatre_config
    ptc = normalized.get("product_theatre_config", {})
    if isinstance(ptc.get("construct_under_test"), dict):
        ptc["construct_under_test"] = ptc["construct_under_test"]["construct_id"]
    if ptc.get("ground_truth_source") not in (
        "GITHUB_API", "CI_CD", "PROVENANCE_JSONL",
        "DETERMINISTIC_COMPUTATION", "CUSTOM",
    ):
        ptc["ground_truth_source"] = "DETERMINISTIC_COMPUTATION"
    ptc.pop("mock_only", None)

    # Fix version_pins.constructs values to hex hashes
    constructs = normalized.get("version_pins", {}).get("constructs", {})
    for key in list(constructs.keys()):
        value = constructs[key]
        if not _is_hex_hash(value):
            constructs[key] = hashlib.sha256(value.encode()).hexdigest()

    # Fix resolution_programme entries
    _ACTION_TO_TYPE = {
        "load_dataset": "deterministic_computation",
        "deterministic_compute": "deterministic_computation",
        "binary_checks": "deterministic_computation",
        "issue_certificate": "aggregation",
    }
    new_programme = []
    for entry in normalized.get("resolution_programme", []):
        new_entry = {
            "step_id": entry.get("step", entry.get("step_id", "")),
            "type": _ACTION_TO_TYPE.get(
                entry.get("action", ""),
                entry.get("type", "deterministic_computation"),
            ),
        }
        new_programme.append(new_entry)
    normalized["resolution_programme"] = new_programme

    # Fix fork_definitions: schema requires minItems: 1
    if not normalized.get("fork_definitions"):
        normalized["fork_definitions"] = [{
            "fork_id": "f_01",
            "options": [
                {"option_id": "pass", "label": "Pass"},
                {"option_id": "fail", "label": "Fail"},
            ],
            "deadline_ms": 0,
        }]

    return normalized


def _is_hex_hash(value: str) -> bool:
    """Check if a string matches the schema hex hash pattern."""
    if not isinstance(value, str) or len(value) < 7 or len(value) > 64:
        return False
    return all(c in "0123456789abcdef" for c in value)


def populate_template_runtime_fields(
    template: dict,
    construct_version: str,
    dataset_hash: str,
) -> dict:
    """Populate template version_pins and dataset_hashes with real values."""
    populated = json.loads(json.dumps(template))  # deep copy

    if "version_pins" in populated:
        constructs = populated["version_pins"].get("constructs", {})
        for construct_id in constructs:
            constructs[construct_id] = construct_version
        populated["version_pins"]["constructs"] = constructs

    if "dataset_hashes" in populated:
        for dataset_key in populated["dataset_hashes"]:
            populated["dataset_hashes"][dataset_key] = dataset_hash

    return populated


def certificate_to_schema_dict(cert: TheatreCalibrationCertificate) -> dict:
    """Convert certificate to dict matching the JSON Schema."""
    data = cert.model_dump()

    for key in ("issued_at", "expires_at", "theatre_committed_at", "theatre_resolved_at"):
        val = data.get(key)
        if isinstance(val, datetime):
            data[key] = val.isoformat()
        elif val is None and key == "expires_at":
            data[key] = datetime(2099, 12, 31, 23, 59, 59).isoformat()

    if hasattr(data.get("criteria"), "model_dump"):
        data["criteria"] = data["criteria"].model_dump()

    for optional_key in ("brier_score", "ece", "construct_chain_versions",
                         "ground_truth_hash", "methodology_version",
                         "precision", "recall", "reply_accuracy"):
        if data.get(optional_key) is None:
            data.pop(optional_key, None)

    return data


def convert_records_to_episodes(records: list) -> list:
    """Convert fixture dataset records to GroundTruthEpisode objects."""
    episodes = []
    for record in records:
        episodes.append(GroundTruthEpisode(
            episode_id=record["record_id"],
            input_data=record["input_data"],
            expected_output=record.get("expected_output", {}),
            metadata={},
        ))
    return episodes


async def run_construct_calibration(
    construct_key: str,
    output_dir: Path,
    verbose: bool = False,
) -> tuple:
    """Execute construct calibration pipeline.

    Returns (certificate_path, certificate_dict).
    """
    config = CONSTRUCTS[construct_key]
    theatre_id = THEATRE_ID

    # Step 0: Generate deterministic certificate_id from construct key
    certificate_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"calibration.{construct_key}"))
    logger.info("[%s] Certificate ID: %s", construct_key, certificate_id)

    # Step 1: Load template and dataset
    template_path = FIXTURE_BASE / "templates" / config["template"]
    dataset_path = FIXTURE_BASE / "datasets" / config["dataset"]

    raw_template = json.loads(template_path.read_text())
    dataset = json.loads(dataset_path.read_text())
    records = dataset["records"]
    logger.info("[%s] Loaded %d records", construct_key, len(records))

    # Step 2: Convert records to episodes
    episodes = convert_records_to_episodes(records)

    # Step 3: Compute dataset hash
    dataset_hash = ReplayEngine._compute_dataset_hash(episodes)
    logger.info("[%s] Dataset hash: %s", construct_key, dataset_hash)

    # Step 4: Extract fields, normalize, populate
    template_id = raw_template.get("template_id", construct_key)
    construct_id = config["construct_id"]
    construct_version = config["construct_version"]
    logger.info("[%s] Template ID: %s", construct_key, template_id)

    # Normalize fixture template to schema v2.0.1
    normalized = _normalize_template_for_schema(raw_template)

    # Populate runtime fields
    construct_version_hex = hashlib.sha256(construct_version.encode()).hexdigest()
    populated_template = populate_template_runtime_fields(
        template=normalized,
        construct_version=construct_version_hex,
        dataset_hash=dataset_hash,
    )

    # Step 5: Create CommitmentReceipt (deterministic — fixed epoch for fixture mode)
    version_pins = populated_template["version_pins"]
    dataset_hashes = populated_template["dataset_hashes"]

    commitment_hash = CommitmentProtocol.compute_hash(
        populated_template, version_pins, dataset_hashes,
    )
    receipt = CommitmentReceipt(
        theatre_id=theatre_id,
        commitment_hash=commitment_hash,
        committed_at=_FIXTURE_EPOCH,
        template_snapshot=populated_template,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes,
    )
    logger.info("[%s] Commitment hash: %s", construct_key, receipt.commitment_hash)

    # Step 6: Build ReplayEngine
    criteria = TheatreCriteria(**populated_template["criteria"])
    scorer_instance = config["scorer_class"]()
    scoring_provider = TheatreScoringProvider(criteria=criteria, scorer=scorer_instance)
    oracle_adapter = DeterministicOracleAdapter()

    engine = ReplayEngine(
        theatre_id=theatre_id,
        construct_id=construct_id,
        construct_version=construct_version_hex,
        criteria=criteria,
        oracle_adapter=oracle_adapter,
        scoring_provider=scoring_provider,
        committed_dataset_hash=dataset_hash,
    )

    # Step 7: Run replay
    def progress_callback(current: int, total: int) -> None:
        logger.info("[%s] Progress: %d/%d", construct_key, current, total)

    replay_result = await engine.run(episodes, progress_callback=progress_callback)
    resolved_at = _FIXTURE_EPOCH
    logger.info(
        "[%s] Replay complete: %d scored, composite=%.4f",
        construct_key,
        replay_result.scored_count,
        replay_result.composite_score,
    )

    # Step 8: Assign tier
    tier = TierAssigner.assign(
        replay_count=replay_result.replay_count,
        has_full_pins=bool(version_pins.get("constructs")),
        has_published_scores=True,
        has_verifiable_hash=True,
        has_disputes=False,
        failure_rate=replay_result.failure_rate,
    )
    issued_at = _FIXTURE_EPOCH
    expires_at = TierAssigner.compute_expiry(tier, issued_at)
    logger.info("[%s] Tier: %s", construct_key, tier)

    # Step 9: Build evidence bundle (clean previous run for determinism)
    construct_output_dir = output_dir / "construct_calibration" / construct_key
    bundle_path = construct_output_dir / f"evidence_bundle_{template_id}"
    if bundle_path.exists():
        import shutil
        shutil.rmtree(bundle_path)

    bundle = EvidenceBundleBuilder(
        theatre_id=template_id,
        output_dir=construct_output_dir,
    )

    bundle.write_ground_truth(
        dataset=[ep.model_dump() for ep in episodes],
        filename=f"{construct_key}_episodes.jsonl",
    )

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

    bundle.write_aggregate_scores({
        "scores": replay_result.aggregate_scores,
        "composite_score": replay_result.composite_score,
        "replay_count": replay_result.replay_count,
        "scored_count": replay_result.scored_count,
        "failure_count": replay_result.failure_count,
        "failure_rate": replay_result.failure_rate,
    })

    bundle.write_template(populated_template)
    bundle.write_commitment_receipt(receipt)

    # Compute evidence bundle hash
    file_inventory = bundle.compute_file_inventory()
    evidence_bundle_hash = bundle.compute_bundle_hash()

    manifest = BundleManifest(
        theatre_id=theatre_id,
        template_id=template_id,
        construct_id=construct_id,
        execution_path="replay",
        commitment_hash=receipt.commitment_hash,
        file_inventory=file_inventory,
        created_at=_FIXTURE_EPOCH,
    )
    bundle.write_manifest(manifest)

    # Step 10: Build certificate
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
        construct_version=construct_version_hex,
        scorer_version=version_pins.get("scorer_version", "construct-calibration-v1.0"),
        methodology_version="1.0.0",
        dataset_hash=replay_result.dataset_hash,
        verification_tier=tier,
        commitment_hash=receipt.commitment_hash,
        issued_at=issued_at,
        expires_at=expires_at,
        theatre_committed_at=receipt.committed_at,
        theatre_resolved_at=resolved_at,
        ground_truth_source="DETERMINISTIC_COMPUTATION",
        execution_path="replay",
    )

    cert_dict = certificate_to_schema_dict(certificate)
    bundle.write_certificate(cert_dict)

    missing = bundle.validate_minimum_files()
    if missing:
        logger.warning("[%s] Evidence bundle missing files: %s", construct_key, missing)

    # Step 11: Write certificate to output
    cert_dir = construct_output_dir / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / f"{template_id}.json"
    cert_path.write_text(json.dumps(cert_dict, indent=2))
    logger.info("[%s] Certificate written to %s", construct_key, cert_path)

    # Step 12: Write index.json
    index_path = output_dir / "construct_calibration" / "index.json"
    index = {}
    if index_path.exists():
        index = json.loads(index_path.read_text())

    index[construct_key] = {
        "template_id": template_id,
        "construct_id": construct_id,
        "composite_score": replay_result.composite_score,
        "verification_tier": tier,
        "certificate_path": str(cert_path.relative_to(output_dir)),
        "evidence_bundle_hash": evidence_bundle_hash,
        "replay_count": replay_result.replay_count,
        "scores": replay_result.aggregate_scores,
        "generated_at": _FIXTURE_EPOCH.isoformat(),
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True))

    # Step 13: Verify via MCP echelon_verify
    try:
        from mcp.tools import verify as mcp_verify

        verify_result = mcp_verify.handle({
            "certificate": {"mode": "inline", "value": cert_dict},
        })
        overall = verify_result.get("overall_verdict", "UNKNOWN")
        logger.info("[%s] MCP verify: %s", construct_key, overall)

        if overall == "PASS":
            print(f"  MCP echelon_verify: PASS")
        else:
            checks = verify_result.get("checks", [])
            fails = [c for c in checks if c.get("verdict") == "FAIL"]
            print(f"  MCP echelon_verify: {overall} ({len(fails)} failures)")
            for f in fails:
                print(f"    - {f.get('check_id')}: {f.get('detail', '')[:80]}")
    except ImportError:
        logger.warning("[%s] MCP tools not available, skipping verification", construct_key)
        print("  MCP echelon_verify: SKIPPED (mcp package not found)")

    return cert_path, cert_dict


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Construct Calibration Pipeline",
    )
    parser.add_argument(
        "--construct",
        choices=list(CONSTRUCTS.keys()),
        required=True,
        help="Construct to calibrate",
    )
    parser.add_argument(
        "--construct-source",
        default=None,
        help="Override construct source path (not used in fixture mode)",
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

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    output_dir = Path(args.output_dir)

    path, cert_dict = await run_construct_calibration(
        args.construct, output_dir, args.verbose
    )

    scores = cert_dict.get("scores", {})
    print(f"\n{'='*60}")
    print(f"Construct Calibration — {args.construct}")
    print(f"{'='*60}")
    print(f"  Template:    {cert_dict.get('template_id', '?')}")
    print(f"  Composite:   {cert_dict.get('composite_score', 0):.4f}")
    print(f"  Precision:   {scores.get('precision', 0):.4f}")
    print(f"  Recall:      {scores.get('recall', 0):.4f}")
    print(f"  Reply Acc:   {scores.get('reply_accuracy', 0):.4f}")
    print(f"  Tier:        {cert_dict.get('verification_tier', '?')}")
    print(f"  Certificate: {path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
