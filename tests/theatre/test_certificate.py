"""Tests for Theatre Calibration Certificate model."""

from datetime import datetime

import pytest

from theatre.engine.certificate import TheatreCalibrationCertificate
from theatre.engine.models import TheatreCriteria


def _make_certificate(**overrides) -> TheatreCalibrationCertificate:
    defaults = {
        "certificate_id": "cert-001",
        "theatre_id": "theatre-001",
        "template_id": "product_observer_v1",
        "construct_id": "observer",
        "criteria": TheatreCriteria(
            criteria_ids=["accuracy"],
            criteria_human="Test",
            weights={"accuracy": 1.0},
        ),
        "scores": {"accuracy": 0.85},
        "composite_score": 0.85,
        "replay_count": 100,
        "evidence_bundle_hash": "a" * 64,
        "ground_truth_hash": "b" * 64,
        "construct_version": "abc123",
        "scorer_version": "v1.0",
        "methodology_version": "1.0",
        "dataset_hash": "c" * 64,
        "verification_tier": "BACKTESTED",
        "commitment_hash": "d" * 64,
        "theatre_committed_at": datetime(2026, 1, 1),
        "theatre_resolved_at": datetime(2026, 1, 2),
        "ground_truth_source": "PROVENANCE_JSONL",
        "execution_path": "replay",
    }
    defaults.update(overrides)
    return TheatreCalibrationCertificate(**defaults)


class TestTheatreCalibrationCertificate:
    def test_valid_certificate(self):
        cert = _make_certificate()
        assert cert.certificate_id == "cert-001"
        assert cert.verification_tier == "BACKTESTED"
        assert cert.composite_score == 0.85

    def test_certificate_with_calibration(self):
        cert = _make_certificate(
            precision=0.92,
            recall=0.88,
            brier_score=0.12,
            ece=0.03,
        )
        assert cert.precision == 0.92
        assert cert.recall == 0.88

    def test_certificate_with_chain_versions(self):
        cert = _make_certificate(
            construct_chain_versions={"observer": "abc", "scorer": "def"},
        )
        assert cert.construct_chain_versions["observer"] == "abc"

    def test_certificate_serialisation(self):
        cert = _make_certificate()
        data = cert.model_dump()
        assert "certificate_id" in data
        assert "verification_tier" in data
        assert "scores" in data
        assert data["execution_path"] == "replay"

    def test_certificate_json_round_trip(self):
        cert = _make_certificate()
        json_str = cert.model_dump_json()
        cert2 = TheatreCalibrationCertificate.model_validate_json(json_str)
        assert cert2.certificate_id == cert.certificate_id
        assert cert2.composite_score == cert.composite_score

    def test_market_execution_path(self):
        cert = _make_certificate(execution_path="market")
        assert cert.execution_path == "market"

    def test_proven_tier(self):
        cert = _make_certificate(verification_tier="PROVEN")
        assert cert.verification_tier == "PROVEN"

    def test_unverified_tier(self):
        cert = _make_certificate(verification_tier="UNVERIFIED")
        assert cert.verification_tier == "UNVERIFIED"

    def test_optional_expires_at(self):
        cert = _make_certificate(expires_at=datetime(2026, 4, 1))
        assert cert.expires_at is not None

    def test_default_no_expiry(self):
        cert = _make_certificate()
        assert cert.expires_at is None
