"""Tests for Evidence Bundle Builder — file creation, validation, hash."""

import json
from pathlib import Path

import pytest

from theatre.engine.commitment import CommitmentReceipt
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.engine.models import AuditEvent, BundleManifest


@pytest.fixture
def bundle_dir(tmp_path):
    return tmp_path


@pytest.fixture
def builder(bundle_dir):
    return EvidenceBundleBuilder("test-theatre", bundle_dir)


@pytest.fixture
def sample_manifest():
    return BundleManifest(
        theatre_id="test-theatre",
        template_id="product_observer_v1",
        construct_id="observer",
        execution_path="replay",
        commitment_hash="a" * 64,
        file_inventory={"manifest.json": "placeholder"},
    )


@pytest.fixture
def sample_receipt():
    from datetime import datetime
    return CommitmentReceipt(
        theatre_id="test-theatre",
        commitment_hash="a" * 64,
        committed_at=datetime(2026, 1, 1),
        template_snapshot={"schema_version": "2.0.1"},
        version_pins={"constructs": {"observer": "abc123"}},
        dataset_hashes={"provenance": "b" * 64},
    )


class TestEvidenceBundleCreation:
    def test_creates_directory_structure(self, builder, bundle_dir):
        base = bundle_dir / "evidence_bundle_test-theatre"
        assert base.exists()
        assert (base / "ground_truth").exists()
        assert (base / "invocations").exists()
        assert (base / "scores").exists()

    def test_write_manifest(self, builder, sample_manifest):
        builder.write_manifest(sample_manifest)
        path = builder.base_dir / "manifest.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["theatre_id"] == "test-theatre"

    def test_write_template(self, builder):
        template = {"schema_version": "2.0.1", "theatre_id": "test"}
        builder.write_template(template)
        path = builder.base_dir / "template.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["schema_version"] == "2.0.1"

    def test_write_commitment_receipt(self, builder, sample_receipt):
        builder.write_commitment_receipt(sample_receipt)
        path = builder.base_dir / "commitment_receipt.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["commitment_hash"] == "a" * 64

    def test_write_ground_truth(self, builder):
        dataset = [
            {"episode_id": "ep1", "input": "data1"},
            {"episode_id": "ep2", "input": "data2"},
        ]
        builder.write_ground_truth(dataset, "dataset.jsonl")
        path = builder.base_dir / "ground_truth" / "dataset.jsonl"
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_write_invocation(self, builder):
        builder.write_invocation(
            "ep_001",
            {"construct_id": "observer"},
            {"status": "SUCCESS", "output": {}},
        )
        path = builder.base_dir / "invocations" / "ep_001.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "request" in data
        assert "response" in data

    def test_write_episode_score_appends(self, builder):
        builder.write_episode_score({"episode_id": "ep1", "score": 0.8})
        builder.write_episode_score({"episode_id": "ep2", "score": 0.9})
        path = builder.base_dir / "scores" / "per_episode.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_write_aggregate_scores(self, builder):
        builder.write_aggregate_scores({"accuracy": 0.85, "composite": 0.85})
        path = builder.base_dir / "scores" / "aggregate.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["accuracy"] == 0.85

    def test_write_certificate(self, builder):
        builder.write_certificate({"certificate_id": "cert-1", "tier": "BACKTESTED"})
        path = builder.base_dir / "certificate.json"
        assert path.exists()

    def test_append_audit_event(self, builder):
        event = AuditEvent(event_type="state_transition", from_state="DRAFT", to_state="COMMITTED")
        builder.append_audit_event(event)
        builder.append_audit_event(event)
        path = builder.base_dir / "audit_trail.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2


class TestBundleHash:
    def test_compute_bundle_hash(self, builder, sample_manifest):
        builder.write_manifest(sample_manifest)
        h = builder.compute_bundle_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_deterministic(self, builder, sample_manifest):
        builder.write_manifest(sample_manifest)
        h1 = builder.compute_bundle_hash()
        h2 = builder.compute_bundle_hash()
        assert h1 == h2

    def test_hash_on_empty_bundle(self, builder):
        """Empty bundle produces valid hash from empty file inventory."""
        h = builder.compute_bundle_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestMinimumFileValidation:
    def test_empty_bundle_reports_all_missing(self, builder):
        missing = builder.validate_minimum_files()
        assert "manifest.json" in missing
        assert "template.json" in missing
        assert "commitment_receipt.json" in missing
        assert "scores/aggregate.json" in missing
        assert "certificate.json" in missing
        assert any("ground_truth" in m for m in missing)
        assert any("invocations" in m for m in missing)

    def test_complete_bundle_reports_nothing(
        self, builder, sample_manifest, sample_receipt
    ):
        builder.write_manifest(sample_manifest)
        builder.write_template({"schema_version": "2.0.1"})
        builder.write_commitment_receipt(sample_receipt)
        builder.write_ground_truth([{"ep": "1"}], "dataset.jsonl")
        builder.write_invocation("ep1", {}, {})
        builder.write_aggregate_scores({"accuracy": 0.8})
        builder.write_certificate({"cert": "data"})

        missing = builder.validate_minimum_files()
        assert missing == []

    def test_partial_bundle_reports_missing(self, builder, sample_manifest):
        builder.write_manifest(sample_manifest)
        # Missing template, commitment, scores, certificate, ground_truth, invocations
        missing = builder.validate_minimum_files()
        assert "template.json" in missing
        assert len(missing) > 0
