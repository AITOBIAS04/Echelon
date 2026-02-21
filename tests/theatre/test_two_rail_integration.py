"""Integration + determinism tests for Two-Rail deterministic Product Theatres.

Tests the full pipeline: fixtures → episodes → replay → certificates.
Verifies schema validity, score correctness, and deterministic hashing.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import jsonschema
import pytest

# Import runner functions
import sys

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.run_two_rail_theatres import (
    THEATRES,
    convert_records_to_episodes,
    run_all_theatres,
    run_single_theatre,
)

CERT_SCHEMA_PATH = _ROOT / "docs" / "schemas" / "echelon_certificate_schema.json"


@pytest.fixture
def cert_schema():
    return json.loads(CERT_SCHEMA_PATH.read_text())


@pytest.fixture
def output_dir():
    d = tempfile.mkdtemp(prefix="two_rail_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


# ---- Full pipeline: 3 theatres → 3 certificates → schema-valid ----


@pytest.mark.asyncio
async def test_full_pipeline_produces_three_certificates(output_dir, cert_schema):
    """Running all 3 theatres produces 3 schema-valid certificate files."""
    results = await run_all_theatres(output_dir)

    assert len(results) == 3

    for path, cert_dict in results:
        # File exists
        assert path.exists(), f"Certificate file not found: {path}"

        # Schema-valid
        jsonschema.validate(instance=cert_dict, schema=cert_schema)

        # Required fields present
        assert cert_dict["theatre_id"] == "product_replay_engine_v1"
        assert cert_dict["execution_path"] == "replay"
        assert "composite_score" in cert_dict
        assert "commitment_hash" in cert_dict
        assert "evidence_bundle_hash" in cert_dict


# ---- Score correctness: all 30 episodes score 1.0 composite ----


@pytest.mark.asyncio
async def test_all_scores_are_perfect(output_dir):
    """All 30 episodes (10 per theatre) should score 1.0 on happy-path fixtures."""
    results = await run_all_theatres(output_dir)

    for path, cert_dict in results:
        composite = cert_dict["composite_score"]
        assert composite == 1.0, (
            f"Theatre {cert_dict['template_id']} composite={composite}, expected 1.0"
        )

        # All individual criteria scores should be 1.0
        for criteria_id, score in cert_dict["scores"].items():
            assert score == 1.0, (
                f"Theatre {cert_dict['template_id']} criteria {criteria_id} "
                f"score={score}, expected 1.0"
            )


# ---- Determinism: two runs → identical hashes ----


@pytest.mark.asyncio
async def test_determinism_identical_hashes(output_dir):
    """Two consecutive runs produce identical commitment and dataset hashes."""
    # Run 1
    output_dir_1 = output_dir / "run1"
    results_1 = await run_all_theatres(output_dir_1)

    # Run 2
    output_dir_2 = output_dir / "run2"
    results_2 = await run_all_theatres(output_dir_2)

    assert len(results_1) == len(results_2) == 3

    for (_, cert1), (_, cert2) in zip(results_1, results_2):
        # Same template_id
        assert cert1["template_id"] == cert2["template_id"]

        # Identical commitment hashes
        assert cert1["commitment_hash"] == cert2["commitment_hash"], (
            f"Commitment hash mismatch for {cert1['template_id']}"
        )

        # Identical dataset hashes
        assert cert1["dataset_hash"] == cert2["dataset_hash"], (
            f"Dataset hash mismatch for {cert1['template_id']}"
        )

        # Evidence bundle hashes may differ due to committed_at timestamps
        # in the commitment receipt; the commitment_hash and dataset_hash
        # are the real determinism guarantees.

        # Identical composite scores
        assert cert1["composite_score"] == cert2["composite_score"]

        # Identical per-criteria scores
        assert cert1["scores"] == cert2["scores"]


# ---- Single theatre: run one → correct certificate ----


@pytest.mark.parametrize("theatre_key", list(THEATRES.keys()))
@pytest.mark.asyncio
async def test_single_theatre_produces_certificate(theatre_key, output_dir, cert_schema):
    """Running a single theatre produces one schema-valid certificate."""
    path, cert_dict = await run_single_theatre(theatre_key, output_dir)

    assert path.exists()
    jsonschema.validate(instance=cert_dict, schema=cert_schema)

    # Template ID matches expected
    expected_template_id = theatre_key
    assert cert_dict["template_id"] == expected_template_id

    # Replay count is 10 (10 fixture records per theatre)
    assert cert_dict["replay_count"] == 10

    # Tier is UNVERIFIED (10 replays < 50 minimum for BACKTESTED)
    assert cert_dict["verification_tier"] == "UNVERIFIED"


# ---- Evidence bundle completeness ----


@pytest.mark.asyncio
async def test_evidence_bundle_created(output_dir):
    """Each theatre produces an evidence bundle directory."""
    results = await run_all_theatres(output_dir)

    for _, cert_dict in results:
        template_id = cert_dict["template_id"]
        bundle_dir = output_dir / f"evidence_bundle_{template_id}"
        assert bundle_dir.exists(), f"Evidence bundle not found for {template_id}"

        # Key files should exist
        assert (bundle_dir / "manifest.json").exists()
        assert (bundle_dir / "template.json").exists()
        assert (bundle_dir / "commitment_receipt.json").exists()


# ---- Record conversion ----


def test_convert_records_to_episodes():
    """Fixture records convert to GroundTruthEpisode objects correctly."""
    records = [
        {
            "record_id": "test_001",
            "asset_id": "asset_x",
            "period_end": "2026-01-01",
            "inputs": {"key": "value"},
            "expected_outputs": {"result": True},
        }
    ]
    episodes = convert_records_to_episodes(records)
    assert len(episodes) == 1

    ep = episodes[0]
    assert ep.episode_id == "test_001"
    assert ep.input_data == {"key": "value"}
    assert ep.expected_output == {"result": True}
    assert ep.metadata["asset_id"] == "asset_x"
