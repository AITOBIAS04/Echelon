"""Integration tests for the unified Two-Rail certificate pipeline.

Validates full pipeline output for escrow template: verifier PASS, FR-2 directory
layout, certificate fields, and CalibrationCertificate model compatibility.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

# Ensure correct import order (theatre before osint_pipeline.echelon_verify).
project_root = str(Path(__file__).resolve().parents[2])
osint_root = str(Path(__file__).resolve().parents[2] / "osint")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if osint_root not in sys.path:
    sys.path.insert(0, osint_root)

from theatre.scoring.escrow_scorer import EscrowScorer  # noqa: E402 — must precede echelon_verify

from osint_pipeline.echelon_verify import verify as echelon_verify  # noqa: E402
from osint_pipeline.models.certificate import CalibrationCertificate  # noqa: E402

# Import after path setup
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "integration_output"


@pytest.fixture
def escrow_evidence(output_dir):
    """Run escrow pipeline and return evidence directory path."""
    import asyncio
    # Re-import to get the module with correct sys.path
    from run_two_rail_certificates import run_template
    result = asyncio.run(run_template("escrow_milestone_release_v1", output_dir, verbose=False))
    passed, composite = result
    evidence_dir = output_dir / "evidence_escrow_milestone_release_v1"
    return evidence_dir, passed, composite


def test_escrow_pipeline_produces_pass(escrow_evidence):
    """Full pipeline for escrow produces Verifier CLI PASS."""
    _, passed, _ = escrow_evidence
    assert passed is True


def test_evidence_bundle_directory_layout(escrow_evidence):
    """All 6 FR-2 subdirectories exist."""
    evidence_dir, _, _ = escrow_evidence
    for subdir in ("inputs", "receipts", "gaps", "scores", "policy", "expected"):
        assert (evidence_dir / subdir).is_dir(), f"Missing subdirectory: {subdir}"


def test_manifest_contains_all_files(escrow_evidence):
    """Manifest has entries for every non-excluded file."""
    evidence_dir, _, _ = escrow_evidence
    manifest = json.loads((evidence_dir / "manifest.json").read_text())

    # Collect all files (excluding manifest.json and certificate.json)
    excludes = {"manifest.json", "certificate.json"}
    actual_files = set()
    for p in evidence_dir.rglob("*"):
        if p.is_file() and p.name not in excludes:
            rel = str(p.relative_to(evidence_dir))
            actual_files.add(rel)

    manifest_files = set(manifest.keys())
    assert manifest_files == actual_files


def test_certificate_has_replay_fields(escrow_evidence):
    """Certificate has execution_path='replay' and verification_tier='UNVERIFIED'."""
    evidence_dir, _, _ = escrow_evidence
    cert = json.loads((evidence_dir / "certificate.json").read_text())
    assert cert["execution_path"] == "replay"
    assert cert["verification_tier"] == "UNVERIFIED"


def test_certificate_model_matches_osint(escrow_evidence):
    """Certificate dict validates as CalibrationCertificate(**data)."""
    evidence_dir, _, _ = escrow_evidence
    cert_data = json.loads((evidence_dir / "certificate.json").read_text())
    cert = CalibrationCertificate(**cert_data)
    assert cert.execution_path == "replay"
    assert cert.composite_score > 0
