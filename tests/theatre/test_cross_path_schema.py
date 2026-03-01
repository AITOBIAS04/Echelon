"""Cross-path schema tests — validate replay certificates against CalibrationCertificate.

Ensures replay-generated certificates are compatible with the OSINT pipeline's
Pydantic model and contain all required fields.
"""

import asyncio
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

from theatre.scoring.escrow_scorer import EscrowScorer  # noqa: E402

from osint_pipeline.models.certificate import CalibrationCertificate  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

REQUIRED_FIELDS = [
    "certificate_id",
    "theatre_id",
    "verification_tier",
    "composite_score",
    "evidence_bundle_hash",
    "commitment_hash",
    "criterion_scores",
    "issued_at",
    "pipeline_version",
    "execution_path",
    "target_entity",
]


@pytest.fixture(scope="module")
def replay_certificate(tmp_path_factory):
    """Generate a replay certificate for escrow template."""
    from run_two_rail_certificates import run_template

    output_dir = tmp_path_factory.mktemp("cross_path")
    asyncio.run(run_template("escrow_milestone_release_v1", output_dir, verbose=False))
    cert_path = output_dir / "evidence_escrow_milestone_release_v1" / "certificate.json"
    return json.loads(cert_path.read_text())


def test_replay_certificate_validates_as_calibration_certificate(replay_certificate):
    """Replay cert validates with CalibrationCertificate(**data)."""
    cert = CalibrationCertificate(**replay_certificate)
    assert cert.execution_path == "replay"
    assert cert.verification_tier == "UNVERIFIED"
    assert cert.composite_score > 0


def test_certificate_required_fields_present(replay_certificate):
    """All required CalibrationCertificate fields exist in the replay cert."""
    for field in REQUIRED_FIELDS:
        assert field in replay_certificate, f"Missing required field: {field}"
