"""Unit tests for the Storage layer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from echelon_verify.models import (
    CalibrationCertificate,
    GroundTruthRecord,
    ReplayScore,
)
from echelon_verify.storage import Storage


@pytest.fixture
def storage(tmp_storage_dir: Path) -> Storage:
    return Storage(str(tmp_storage_dir))


class TestRepoDir:
    def test_creates_directory(self, storage: Storage) -> None:
        path = storage.repo_dir("echelon/app")
        assert path.exists()
        assert path.name == "echelon_app"

    def test_idempotent(self, storage: Storage) -> None:
        p1 = storage.repo_dir("echelon/app")
        p2 = storage.repo_dir("echelon/app")
        assert p1 == p2

    def test_rejects_path_traversal(self, storage: Storage) -> None:
        with pytest.raises(ValueError, match="Invalid repo name"):
            storage.repo_dir("../../etc/passwd")


class TestJsonl:
    def test_append_and_read_round_trip(
        self,
        storage: Storage,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        repo_dir = storage.repo_dir("echelon/app")
        path = repo_dir / "ground_truth.jsonl"

        storage.append_jsonl(path, sample_ground_truth)
        storage.append_jsonl(path, sample_ground_truth)

        records = storage.read_jsonl(path, GroundTruthRecord)
        assert len(records) == 2
        assert records[0] == sample_ground_truth
        assert records[1] == sample_ground_truth

    def test_read_empty_file(self, storage: Storage) -> None:
        path = storage.base_dir / "empty.jsonl"
        records = storage.read_jsonl(path, GroundTruthRecord)
        assert records == []

    def test_read_replay_scores(
        self,
        storage: Storage,
        sample_scores: list[ReplayScore],
    ) -> None:
        path = storage.base_dir / "scores.jsonl"
        for score in sample_scores:
            storage.append_jsonl(path, score)

        restored = storage.read_jsonl(path, ReplayScore)
        assert len(restored) == 5
        assert restored[0].precision == sample_scores[0].precision


class TestCertificates:
    def _make_cert(self, **overrides) -> CalibrationCertificate:
        defaults = dict(
            construct_id="oracle-v1",
            replay_count=3,
            precision=0.8,
            recall=0.7,
            reply_accuracy=0.9,
            composite_score=0.8,
            brier=0.1,
            sample_size=3,
            timestamp=datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc),
            ground_truth_source="https://github.com/o/r",
            commit_range="abc..def",
            methodology_version="v1",
            scoring_model="test",
        )
        defaults.update(overrides)
        return CalibrationCertificate(**defaults)

    def test_write_and_read_certificate(self, storage: Storage) -> None:
        cert = self._make_cert()
        path = storage.write_certificate(cert)

        assert path.exists()
        assert cert.certificate_id in path.name

        restored = storage.read_certificate(cert.certificate_id)
        assert restored.construct_id == cert.construct_id
        assert restored.precision == cert.precision

    def test_certificate_not_found(self, storage: Storage) -> None:
        with pytest.raises(FileNotFoundError, match="Certificate not found"):
            storage.read_certificate("nonexistent-id")

    def test_list_certificates(self, storage: Storage) -> None:
        cert1 = self._make_cert(construct_id="oracle-a")
        cert2 = self._make_cert(construct_id="oracle-b")

        storage.write_certificate(cert1)
        storage.write_certificate(cert2)

        entries = storage.list_certificates()
        assert len(entries) == 2
        ids = {e["construct_id"] for e in entries}
        assert ids == {"oracle-a", "oracle-b"}

    def test_list_empty(self, storage: Storage) -> None:
        entries = storage.list_certificates()
        assert entries == []
