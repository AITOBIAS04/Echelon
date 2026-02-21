"""Runner Script — deterministic Two-Rail Product Theatre execution.

Produces CalibrationCertificates for three financial verification domains:
distribution waterfall, escrow milestone release, and ledger reconciliation.

No LLM, no API calls, no network — pure arithmetic/policy binary checks.

Usage:
    python scripts/run_two_rail_theatres.py --all --verbose
    python scripts/run_two_rail_theatres.py --theatre distribution_waterfall_v1
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
from theatre.engine.commitment import CommitmentProtocol
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.engine.models import BundleManifest, GroundTruthEpisode, TheatreCriteria
from theatre.engine.replay import ReplayEngine
from theatre.engine.scoring import TheatreScoringProvider
from theatre.engine.template_validator import TemplateValidator
from theatre.engine.tier_assigner import TierAssigner
from theatre.scoring import (
    DeterministicOracleAdapter,
    EscrowScorer,
    ReconciliationScorer,
    WaterfallScorer,
)

logger = logging.getLogger(__name__)

# Stable engine type — identifies the Theatre engine kind.
THEATRE_ID = "product_replay_engine_v1"

# Fixture base path
FIXTURE_BASE = _ROOT / "theatre" / "fixtures" / "two_rail_theatres_v0_1"

# Theatre registry
THEATRES = {
    "distribution_waterfall_v1": {
        "template": "DISTRIBUTION_WATERFALL_V1.template.json",
        "dataset": "waterfall_fixtures_10.json",
        "scorer_class": WaterfallScorer,
    },
    "escrow_milestone_release_v1": {
        "template": "ESCROW_MILESTONE_RELEASE_V1.template.json",
        "dataset": "escrow_fixtures_10.json",
        "scorer_class": EscrowScorer,
    },
    "ledger_reconciliation_v1": {
        "template": "LEDGER_RECONCILIATION_V1.template.json",
        "dataset": "reconciliation_fixtures_10.json",
        "scorer_class": ReconciliationScorer,
    },
}


def _normalize_template_for_schema(template: dict) -> dict:
    """Transform v0.1 fixture template to conform to schema v2.0.1.

    v0.1 fixtures use a simpler format that pre-dates the formal schema.
    This normalizes them in-memory so they pass schema validation while
    preserving the original data semantics.
    """
    normalized = json.loads(json.dumps(template))  # deep copy

    # Remove non-schema root properties
    normalized.pop("template_id", None)
    normalized.pop("evidence_bundle", None)

    # Add required 'scoring' property (empty object — criteria.weights is the
    # actual scoring config for Product Theatres)
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
        new_entry: dict[str, Any] = {
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
    """Populate template version_pins and dataset_hashes with real values.

    Returns a new dict (does not mutate original).
    """
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


def convert_records_to_episodes(records: list[dict]) -> list[GroundTruthEpisode]:
    """Convert fixture dataset records to GroundTruthEpisode objects."""
    episodes = []
    for record in records:
        episodes.append(GroundTruthEpisode(
            episode_id=record["record_id"],
            input_data=record["inputs"],
            expected_output=record.get("expected_outputs", {}),
            metadata={
                "asset_id": record.get("asset_id", ""),
                "period_end": record.get("period_end", ""),
            },
        ))
    return episodes


async def run_single_theatre(
    theatre_key: str,
    output_dir: Path,
    verbose: bool = False,
) -> tuple[Path, dict]:
    """Execute a single deterministic theatre.

    Returns (certificate_path, certificate_dict).
    """
    config = THEATRES[theatre_key]
    theatre_id = THEATRE_ID

    # Step 0: Generate certificate_id
    certificate_id = str(uuid.uuid4())
    logger.info("[%s] Certificate ID: %s", theatre_key, certificate_id)

    # Step 1: Load template and dataset
    template_path = FIXTURE_BASE / "templates" / config["template"]
    dataset_path = FIXTURE_BASE / "datasets" / config["dataset"]

    raw_template = json.loads(template_path.read_text())
    dataset = json.loads(dataset_path.read_text())
    records = dataset["records"]
    logger.info("[%s] Loaded %d records", theatre_key, len(records))

    # Step 2: Convert records to episodes
    episodes = convert_records_to_episodes(records)

    # Step 3: Compute dataset hash
    dataset_hash = ReplayEngine._compute_dataset_hash(episodes)
    logger.info("[%s] Dataset hash: %s", theatre_key, dataset_hash)

    # Step 4: Extract fields from raw template, then normalize + populate
    template_id = raw_template.get("template_id", theatre_key)
    construct_info = raw_template["product_theatre_config"]["construct_under_test"]
    construct_version = construct_info["construct_version"]
    construct_id = construct_info["construct_id"]
    logger.info("[%s] Template ID: %s", theatre_key, template_id)

    # Normalize v0.1 fixtures to schema v2.0.1 format
    normalized = _normalize_template_for_schema(raw_template)

    # Populate runtime fields (version pins use hex hashes for schema compliance)
    construct_version_hex = hashlib.sha256(construct_version.encode()).hexdigest()
    populated_template = populate_template_runtime_fields(
        template=normalized,
        construct_version=construct_version_hex,
        dataset_hash=dataset_hash,
    )

    # Step 5: Validate template against schema
    schema_path = _ROOT / "docs" / "schemas" / "echelon_theatre_schema_v2.json"
    theatre_schema = json.loads(schema_path.read_text())
    validator = TemplateValidator(schema=theatre_schema)
    errors = validator.validate(populated_template, is_certificate_run=True)
    if errors:
        raise ValueError(f"[{theatre_key}] Template validation failed: {errors}")
    logger.info("[%s] Template validated", theatre_key)

    # Step 6: Create CommitmentReceipt
    version_pins = populated_template["version_pins"]
    dataset_hashes = populated_template["dataset_hashes"]

    receipt = CommitmentProtocol.create_receipt(
        theatre_id=theatre_id,
        template=populated_template,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes,
    )
    logger.info("[%s] Commitment hash: %s", theatre_key, receipt.commitment_hash)

    # Step 7: Build ReplayEngine
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

    # Step 8: Run replay
    def progress_callback(current: int, total: int) -> None:
        logger.info("[%s] Progress: %d/%d", theatre_key, current, total)

    replay_result = await engine.run(episodes, progress_callback=progress_callback)
    resolved_at = datetime.utcnow()
    logger.info(
        "[%s] Replay complete: %d scored, composite=%.3f",
        theatre_key,
        replay_result.scored_count,
        replay_result.composite_score,
    )

    # Step 9: Assign tier
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
    logger.info("[%s] Tier: %s", theatre_key, tier)

    # Step 9.5: Build evidence bundle
    bundle = EvidenceBundleBuilder(theatre_id=template_id, output_dir=output_dir)

    bundle.write_ground_truth(
        dataset=[ep.model_dump() for ep in episodes],
        filename=f"{theatre_key}_episodes.jsonl",
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
        replay_count=replay_result.replay_count,
        evidence_bundle_hash=evidence_bundle_hash,
        ground_truth_hash=dataset_hash,
        construct_version=construct_version_hex,
        scorer_version=version_pins.get("scorer_version", "deterministic-v0.1"),
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

    # Step 11: Validate certificate against schema
    cert_dict = certificate_to_schema_dict(certificate)

    cert_schema_path = _ROOT / "docs" / "schemas" / "echelon_certificate_schema.json"
    cert_schema = json.loads(cert_schema_path.read_text())

    import jsonschema
    jsonschema.validate(instance=cert_dict, schema=cert_schema)
    logger.info("[%s] Certificate validates against schema", theatre_key)

    bundle.write_certificate(cert_dict)

    missing = bundle.validate_minimum_files()
    if missing:
        logger.warning("[%s] Evidence bundle missing files: %s", theatre_key, missing)

    # Step 12: Write certificate to output
    cert_dir = output_dir / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / f"{template_id}.json"
    cert_path.write_text(json.dumps(cert_dict, indent=2))
    logger.info("[%s] Certificate written to %s", theatre_key, cert_path)

    return cert_path, cert_dict


async def run_all_theatres(
    output_dir: Path,
    verbose: bool = False,
) -> list[tuple[Path, dict]]:
    """Execute all three deterministic theatres."""
    results = []
    for theatre_key in THEATRES:
        path, cert_dict = await run_single_theatre(theatre_key, output_dir, verbose)
        results.append((path, cert_dict))
    return results


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Two-Rail deterministic Product Theatres",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Run all three theatres (default)",
    )
    parser.add_argument(
        "--theatre",
        choices=list(THEATRES.keys()),
        help="Run a single theatre by ID",
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

    if args.theatre:
        path, cert_dict = await run_single_theatre(
            args.theatre, output_dir, args.verbose
        )
        print(f"Certificate written to {path}")
        print(f"  Composite score: {cert_dict.get('composite_score', 'N/A')}")
        print(f"  Tier: {cert_dict.get('verification_tier', 'N/A')}")
    else:
        results = await run_all_theatres(output_dir, args.verbose)
        print(f"\n{'='*60}")
        print(f"Two-Rail Deterministic Theatres — {len(results)} certificates produced")
        print(f"{'='*60}")
        for path, cert_dict in results:
            print(f"  {cert_dict.get('template_id', '?'):40s} "
                  f"composite={cert_dict.get('composite_score', 0):.3f} "
                  f"tier={cert_dict.get('verification_tier', '?')}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
