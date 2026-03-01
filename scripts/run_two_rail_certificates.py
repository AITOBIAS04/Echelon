#!/usr/bin/env python3
"""Unified Two-Rail Certificate Pipeline.

Produces CalibrationCertificates (OSINT pipeline model) from replay fixtures.
All four Two-Rail templates pass through the same infrastructure as OSINT:
  - RFC 8785 canonical JSON (osint_pipeline.engine.canonical)
  - Flat {path: sha256} manifests (osint_pipeline.engine.manifest_builder)
  - CalibrationCertificate model (osint_pipeline.models.certificate)
  - Verifier CLI (osint_pipeline.echelon_verify)

Usage:
    python scripts/run_two_rail_certificates.py --template escrow_milestone_release_v1
    python scripts/run_two_rail_certificates.py --all
    python scripts/run_two_rail_certificates.py --all --output-dir output/unified --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Path setup ---
# Order matters: insert _ROOT first, then _OSINT so _OSINT ends up at
# index 0.  This way `osint_pipeline` resolves from osint/ (has
# echelon_verify) and `theatre` falls through to root-level theatre/.
_ROOT = Path(__file__).resolve().parents[1]
_OSINT = _ROOT / "osint"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_OSINT) not in sys.path:
    sys.path.insert(0, str(_OSINT))

# Theatre imports MUST come before osint_pipeline.echelon_verify because
# echelon_verify adds osint/osint_pipeline/ to sys.path, which shadows
# root-level theatre/ with osint/osint_pipeline/theatre/ (no scoring).
from theatre.scoring.arrears_scorer import ArrearsScorer
from theatre.scoring.escrow_scorer import EscrowScorer
from theatre.scoring.reconciliation_scorer import ReconciliationScorer
from theatre.scoring.waterfall_scorer import WaterfallScorer

from osint_pipeline.echelon_verify import verify as echelon_verify
from osint_pipeline.engine.canonical import canonical_hash
from osint_pipeline.engine.certificate_generator import CertificateGenerator
from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash
from osint_pipeline.models.evidence import OracleCollectionSummary
from osint_pipeline.models.oracle_output import CriterionScore, OracleOutput

# --- Constants ---

FIXTURE_BASE = _ROOT / "theatre" / "fixtures" / "two_rail_theatres_v0_1"

# Fixed epoch for deterministic oracle_output.json (2026-01-01T00:00:00Z).
DETERMINISTIC_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)

TEMPLATE_REGISTRY: dict[str, dict[str, Any]] = {
    "escrow_milestone_release_v1": {
        "template_file": "ESCROW_MILESTONE_RELEASE_V1.template.json",
        "dataset_file": "escrow_fixtures_v02_11.json",
        "scorer_class": EscrowScorer,
        "policy_key": "escrow_policy",
    },
    "distribution_waterfall_v1": {
        "template_file": "DISTRIBUTION_WATERFALL_V1.template.json",
        "dataset_file": "waterfall_fixtures_v02_16.json",
        "scorer_class": WaterfallScorer,
        "policy_key": "waterfall_policy",
    },
    "ledger_reconciliation_v1": {
        "template_file": "LEDGER_RECONCILIATION_V1.template.json",
        "dataset_file": "reconciliation_fixtures_v02_16.json",
        "scorer_class": ReconciliationScorer,
        "policy_key": "reconciliation_policy",
    },
    "arrears_resolution_v1": {
        "template_file": "ARREARS_RESOLUTION_V1.template.json",
        "dataset_file": "arrears_fixtures_v02_18.json",
        "scorer_class": ArrearsScorer,
        "policy_key": "arrears_policy",
    },
}


# --- Pipeline ---


async def run_template(
    template_key: str,
    output_dir: Path,
    verbose: bool = False,
) -> tuple[bool, float]:
    """Run the unified pipeline for a single template.

    Returns (passed, composite_score).
    """
    config = TEMPLATE_REGISTRY[template_key]

    # Step 1: Load template and dataset.
    template_path = FIXTURE_BASE / "templates" / config["template_file"]
    dataset_path = FIXTURE_BASE / "datasets" / config["dataset_file"]

    raw_template = json.loads(template_path.read_text())
    dataset = json.loads(dataset_path.read_text())
    records = dataset["records"]

    criteria_ids: list[str] = raw_template["criteria"]["criteria_ids"]
    weights: dict[str, float] = raw_template["criteria"]["weights"]

    if verbose:
        print(f"  Loaded template: {config['template_file']}")
        print(f"  Loaded dataset: {config['dataset_file']} ({len(records)} records)")

    # Step 2: Score each record.
    scorer = config["scorer_class"]()
    all_record_scores: list[dict[str, Any]] = []

    for record in records:
        ground_truth = {
            "input_data": record["inputs"],
            "expected_output": record["expected_outputs"],
        }
        record_scores: dict[str, float] = {}
        for cid in criteria_ids:
            score = await scorer.score(cid, ground_truth, oracle_output={})
            record_scores[cid] = score
        all_record_scores.append({
            "record_id": record["record_id"],
            "scores": record_scores,
        })

    # Step 3: Compute per-criterion aggregates and composite.
    per_criterion_agg: dict[str, float] = {}
    for cid in criteria_ids:
        values = [rs["scores"][cid] for rs in all_record_scores]
        per_criterion_agg[cid] = sum(values) / len(values)

    composite = sum(
        per_criterion_agg[cid] * weights[cid]
        for cid in criteria_ids
    )

    if verbose:
        for cid in criteria_ids:
            print(f"  {cid}: {per_criterion_agg[cid]:.4f} (weight {weights[cid]})")
        print(f"  Composite: {composite:.4f}")

    # Step 4: Build OracleOutput.
    criterion_scores = []
    for cid in criteria_ids:
        agg = per_criterion_agg[cid]
        criterion_scores.append(CriterionScore(
            criterion_id=cid,
            score=agg,
            passed=agg >= 0.5,
            detail=f"{cid}: {agg:.4f} across {len(records)} records",
        ))

    oracle_output = OracleOutput(
        oracle_id=f"replay_{template_key}",
        theatre_id=raw_template.get("theatre_id", "product_replay_engine_v1"),
        evaluated_at=DETERMINISTIC_EPOCH,
        collection=OracleCollectionSummary(
            theatre_id=raw_template.get("theatre_id"),
            total_sources_attempted=len(records),
            total_sources_succeeded=len(records),
            total_sources_failed=0,
        ),
        criterion_scores=criterion_scores,
        composite_score=composite,
    )

    # Step 5: Build evidence bundle (FR-2 layout).
    evidence_dir = output_dir / f"evidence_{template_key}"
    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True)

    for subdir in ("inputs", "receipts", "gaps", "scores", "policy", "expected"):
        (evidence_dir / subdir).mkdir()

    # Write inputs and expected outputs.
    for record in records:
        rid = record["record_id"]
        (evidence_dir / "inputs" / f"{rid}.json").write_text(
            json.dumps(record["inputs"], sort_keys=True, indent=2)
        )
        (evidence_dir / "expected" / f"{rid}.json").write_text(
            json.dumps(record["expected_outputs"], sort_keys=True, indent=2)
        )

    # Write scores.
    (evidence_dir / "scores" / "per_record.json").write_text(
        json.dumps(all_record_scores, sort_keys=True, indent=2)
    )
    (evidence_dir / "scores" / "aggregate.json").write_text(
        json.dumps({
            "per_criterion": per_criterion_agg,
            "composite": composite,
        }, sort_keys=True, indent=2)
    )

    # Write policy.
    policy_key = config["policy_key"]
    policy_data = raw_template.get(policy_key, {})
    (evidence_dir / "policy" / f"{policy_key}.json").write_text(
        json.dumps(policy_data, sort_keys=True, indent=2)
    )

    # Write theatre template (original, unmutated — C-6).
    (evidence_dir / "theatre_template.json").write_text(
        json.dumps(raw_template, sort_keys=True, indent=2)
    )

    # Write oracle output (deterministic timestamps).
    oracle_dict = json.loads(oracle_output.model_dump_json())
    (evidence_dir / "oracle_output.json").write_text(
        json.dumps(oracle_dict, sort_keys=True, indent=2)
    )

    # Step 6: Build manifest and hash.
    manifest = build_manifest(evidence_dir)
    mhash = manifest_hash(manifest)

    (evidence_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2)
    )

    # Step 7: Compute commitment hash.
    commitment = canonical_hash(raw_template)

    # Step 8: Generate certificate.
    generator = CertificateGenerator()
    certificate = generator.generate(
        oracle_output=oracle_output,
        manifest_hash=mhash,
        commitment_hash=commitment,
        target_entity={
            "template_id": raw_template.get("template_id", template_key),
            "construct_id": raw_template.get("product_theatre_config", {})
                .get("construct_under_test", {})
                .get("construct_id", "unknown"),
            "dataset_id": dataset.get("dataset_id", "unknown"),
            "record_count": len(records),
        },
        theatre_id=raw_template.get("template_id", template_key),
        inquiry_class="INSPECTION",
        execution_path="replay",
        pipeline_version="0.7.0",
    )

    # Step 9: Write certificate.
    cert_dict = json.loads(certificate.model_dump_json())
    cert_path = evidence_dir / "certificate.json"
    cert_path.write_text(
        json.dumps(cert_dict, sort_keys=True, indent=2)
    )

    # Step 10: Verify.
    passed = echelon_verify(cert_path, evidence_dir)

    return passed, composite


async def run_all(
    template_keys: list[str],
    output_dir: Path,
    verbose: bool = False,
) -> int:
    """Run pipeline for multiple templates. Returns exit code."""
    results: dict[str, tuple[bool, float]] = {}

    for key in template_keys:
        print(f"\n{'='*60}")
        print(f"Template: {key}")
        print(f"{'='*60}")

        passed, composite = await run_template(key, output_dir, verbose=verbose)
        results[key] = (passed, composite)

        status = "PASS" if passed else "FAIL"
        print(f"\nResult: {status} (composite: {composite:.4f})")

    # Summary.
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    all_passed = True
    for key, (passed, composite) in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {key}: {composite:.4f}")
        if not passed:
            all_passed = False

    return 0 if all_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified Two-Rail Certificate Pipeline",
    )
    parser.add_argument(
        "--template",
        choices=list(TEMPLATE_REGISTRY.keys()),
        help="Run pipeline for a single template",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run pipeline for all four templates",
    )
    parser.add_argument(
        "--output-dir",
        default="output/unified_certificates",
        help="Output directory (default: output/unified_certificates)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging",
    )

    args = parser.parse_args()

    if not args.template and not args.all:
        parser.error("Specify --template <key> or --all")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        keys = list(TEMPLATE_REGISTRY.keys())
    else:
        keys = [args.template]

    return asyncio.run(run_all(keys, output_dir, verbose=args.verbose))


if __name__ == "__main__":
    sys.exit(main())
