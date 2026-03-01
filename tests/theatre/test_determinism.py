"""Determinism tests for the unified Two-Rail certificate pipeline.

Runs the same template twice and asserts manifest hash, commitment hash,
and all file SHA-256s are identical across runs.
"""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

import pytest

project_root = str(Path(__file__).resolve().parents[2])
osint_root = str(Path(__file__).resolve().parents[2] / "osint")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if osint_root not in sys.path:
    sys.path.insert(0, osint_root)

from theatre.scoring.escrow_scorer import EscrowScorer  # noqa: E402 — must precede echelon_verify

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_pipeline(output_dir: Path, template: str = "escrow_milestone_release_v1"):
    from run_two_rail_certificates import run_template
    return asyncio.run(run_template(template, output_dir, verbose=False))


@pytest.fixture
def dual_runs(tmp_path):
    """Run escrow pipeline twice to separate directories."""
    dir_a = tmp_path / "run_a"
    dir_b = tmp_path / "run_b"
    _run_pipeline(dir_a)
    _run_pipeline(dir_b)
    evidence_a = dir_a / "evidence_escrow_milestone_release_v1"
    evidence_b = dir_b / "evidence_escrow_milestone_release_v1"
    return evidence_a, evidence_b


def test_deterministic_manifest_hash(dual_runs):
    """Dual-run produces identical manifest hash."""
    evidence_a, evidence_b = dual_runs
    manifest_a = json.loads((evidence_a / "manifest.json").read_text())
    manifest_b = json.loads((evidence_b / "manifest.json").read_text())
    assert manifest_a == manifest_b


def test_deterministic_commitment_hash(dual_runs):
    """Dual-run produces identical commitment hash in certificates."""
    evidence_a, evidence_b = dual_runs
    cert_a = json.loads((evidence_a / "certificate.json").read_text())
    cert_b = json.loads((evidence_b / "certificate.json").read_text())
    assert cert_a["commitment_hash"] == cert_b["commitment_hash"]


def test_deterministic_file_contents(dual_runs):
    """Every evidence file has identical SHA-256 across runs."""
    evidence_a, evidence_b = dual_runs
    excludes = {"certificate.json"}  # certificate_id is a UUID

    files_a = sorted(
        p.relative_to(evidence_a) for p in evidence_a.rglob("*")
        if p.is_file() and p.name not in excludes
    )
    files_b = sorted(
        p.relative_to(evidence_b) for p in evidence_b.rglob("*")
        if p.is_file() and p.name not in excludes
    )
    assert files_a == files_b, "File sets differ between runs"

    for rel in files_a:
        hash_a = _sha256(evidence_a / rel)
        hash_b = _sha256(evidence_b / rel)
        assert hash_a == hash_b, f"Hash mismatch for {rel}"
