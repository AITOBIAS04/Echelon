"""Unit tests for Pydantic models."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from echelon_verify.models import (
    CalibrationCertificate,
    GroundTruthRecord,
    OracleOutput,
    ReplayScore,
    VerificationRunStatus,
)


class TestGroundTruthRecord:
    def test_valid_construction(self, sample_ground_truth: GroundTruthRecord) -> None:
        assert sample_ground_truth.id == "142"
        assert sample_ground_truth.repo == "echelon/app"
        assert len(sample_ground_truth.files_changed) == 2

    def test_json_round_trip(self, sample_ground_truth: GroundTruthRecord) -> None:
        json_str = sample_ground_truth.model_dump_json()
        restored = GroundTruthRecord.model_validate_json(json_str)
        assert restored == sample_ground_truth

    def test_defaults(self) -> None:
        record = GroundTruthRecord(
            id="1",
            title="Test",
            diff_content="diff",
            files_changed=["a.py"],
            timestamp=datetime.now(tz=timezone.utc),
            author="bob",
            url="https://github.com/o/r/pull/1",
            repo="o/r",
        )
        assert record.description == ""
        assert record.labels == []


class TestOracleOutput:
    def test_valid_construction(self, sample_oracle_output: OracleOutput) -> None:
        assert sample_oracle_output.ground_truth_id == "142"
        assert len(sample_oracle_output.key_claims) == 3

    def test_json_round_trip(self, sample_oracle_output: OracleOutput) -> None:
        json_str = sample_oracle_output.model_dump_json()
        restored = OracleOutput.model_validate_json(json_str)
        assert restored == sample_oracle_output


class TestReplayScore:
    def test_valid_construction(self, sample_replay_score: ReplayScore) -> None:
        assert sample_replay_score.precision == 0.85
        assert sample_replay_score.claims_total == 3

    def test_precision_out_of_range(self) -> None:
        with pytest.raises(ValidationError, match="precision"):
            ReplayScore(
                ground_truth_id="1",
                precision=1.5,
                recall=0.5,
                reply_accuracy=0.5,
                claims_total=1,
                claims_supported=1,
                changes_total=1,
                changes_surfaced=1,
                scoring_model="test",
                scoring_latency_ms=100,
                scored_at=datetime.now(tz=timezone.utc),
            )

    def test_negative_recall_rejected(self) -> None:
        with pytest.raises(ValidationError, match="recall"):
            ReplayScore(
                ground_truth_id="1",
                precision=0.5,
                recall=-0.1,
                reply_accuracy=0.5,
                claims_total=1,
                claims_supported=1,
                changes_total=1,
                changes_surfaced=1,
                scoring_model="test",
                scoring_latency_ms=100,
                scored_at=datetime.now(tz=timezone.utc),
            )

    def test_negative_claims_rejected(self) -> None:
        with pytest.raises(ValidationError, match="claims_total"):
            ReplayScore(
                ground_truth_id="1",
                precision=0.5,
                recall=0.5,
                reply_accuracy=0.5,
                claims_total=-1,
                claims_supported=0,
                changes_total=1,
                changes_surfaced=1,
                scoring_model="test",
                scoring_latency_ms=100,
                scored_at=datetime.now(tz=timezone.utc),
            )

    def test_json_round_trip(self, sample_replay_score: ReplayScore) -> None:
        json_str = sample_replay_score.model_dump_json()
        restored = ReplayScore.model_validate_json(json_str)
        assert restored == sample_replay_score


class TestCalibrationCertificate:
    def test_valid_construction(self) -> None:
        cert = CalibrationCertificate(
            construct_id="oracle-v1",
            replay_count=50,
            precision=0.82,
            recall=0.78,
            reply_accuracy=0.85,
            composite_score=0.82,
            brier=0.09,
            sample_size=50,
            timestamp=datetime.now(tz=timezone.utc),
            ground_truth_source="https://github.com/o/r",
            commit_range="abc..def",
            methodology_version="v1",
            scoring_model="claude-sonnet-4-6",
        )
        assert cert.domain == "community_oracle"
        assert cert.schema_version == "1.0.0"
        assert cert.certificate_id  # auto-generated UUID

    def test_brier_out_of_range(self) -> None:
        with pytest.raises(ValidationError, match="brier"):
            CalibrationCertificate(
                construct_id="oracle-v1",
                replay_count=50,
                precision=0.5,
                recall=0.5,
                reply_accuracy=0.5,
                composite_score=0.5,
                brier=0.6,  # > 0.5
                sample_size=50,
                timestamp=datetime.now(tz=timezone.utc),
                ground_truth_source="https://github.com/o/r",
                commit_range="abc..def",
                methodology_version="v1",
                scoring_model="test",
            )

    def test_replay_count_must_be_positive(self) -> None:
        with pytest.raises(ValidationError, match="replay_count"):
            CalibrationCertificate(
                construct_id="oracle-v1",
                replay_count=0,
                precision=0.5,
                recall=0.5,
                reply_accuracy=0.5,
                composite_score=0.5,
                brier=0.25,
                sample_size=1,
                timestamp=datetime.now(tz=timezone.utc),
                ground_truth_source="https://github.com/o/r",
                commit_range="abc..def",
                methodology_version="v1",
                scoring_model="test",
            )

    def test_json_round_trip(self) -> None:
        cert = CalibrationCertificate(
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
        json_str = cert.model_dump_json()
        restored = CalibrationCertificate.model_validate_json(json_str)
        assert restored.precision == cert.precision
        assert restored.certificate_id == cert.certificate_id

    def test_fixture_file_valid(self, fixtures_dir) -> None:
        data = json.loads((fixtures_dir / "sample_certificate.json").read_text())
        cert = CalibrationCertificate.model_validate(data)
        assert cert.construct_id == "community-oracle-v1"
        assert cert.replay_count == 5


class TestVerificationRunStatus:
    def test_all_status_values(self) -> None:
        for status in [
            "pending", "ingesting", "invoking", "scoring",
            "certifying", "completed", "failed",
        ]:
            obj = VerificationRunStatus(
                job_id="test-job",
                status=status,
                started_at=datetime.now(tz=timezone.utc),
            )
            assert obj.status == status

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VerificationRunStatus(
                job_id="test-job",
                status="unknown_status",
                started_at=datetime.now(tz=timezone.utc),
            )
