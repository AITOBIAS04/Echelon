"""Tests for the certificate generator."""

from __future__ import annotations

import pytest

from echelon_verify.certificate.generator import CertificateGenerator
from echelon_verify.models import CalibrationCertificate, ReplayScore


def _make_generator(**kwargs) -> CertificateGenerator:
    defaults = dict(
        construct_id="test-oracle",
        ground_truth_source="echelon/app",
        commit_range="abc123..def456",
        scoring_model="claude-sonnet-4-6",
        methodology_version="v1",
    )
    defaults.update(kwargs)
    return CertificateGenerator(**defaults)


class TestCertificateGenerator:
    def test_aggregate_means(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        # Expected means from conftest sample_scores (5 items, i=0..4):
        # precision:        [0.70, 0.75, 0.80, 0.85, 0.90] → mean = 0.80
        # recall:           [0.60, 0.68, 0.76, 0.84, 0.92] → mean = 0.76
        # reply_accuracy:   [0.80, 0.83, 0.86, 0.89, 0.92] → mean = 0.86
        assert abs(cert.precision - 0.80) < 1e-4
        assert abs(cert.recall - 0.76) < 1e-4
        assert abs(cert.reply_accuracy - 0.86) < 1e-4

    def test_composite_equal_weights(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        expected_composite = (0.80 + 0.76 + 0.86) / 3.0
        assert abs(cert.composite_score - expected_composite) < 1e-4

    def test_composite_custom_weights(self, sample_scores: list[ReplayScore]):
        gen = _make_generator(
            composite_weights={"precision": 2.0, "recall": 1.0, "reply_accuracy": 0.0}
        )
        cert = gen.generate(sample_scores)

        # (2.0 * 0.80 + 1.0 * 0.76 + 0.0 * 0.86) / 3.0
        expected = (2.0 * 0.80 + 1.0 * 0.76) / 3.0
        assert abs(cert.composite_score - expected) < 1e-4

    def test_brier_score(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        expected_composite = (0.80 + 0.76 + 0.86) / 3.0
        expected_brier = (1 - expected_composite) * 0.5
        assert abs(cert.brier - expected_brier) < 1e-4
        assert 0.0 <= cert.brier <= 0.5

    def test_sample_size_equals_count(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        assert cert.replay_count == 5
        assert cert.sample_size == 5

    def test_validates_against_model(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        assert isinstance(cert, CalibrationCertificate)
        assert cert.domain == "community_oracle"
        assert cert.construct_id == "test-oracle"
        assert cert.methodology_version == "v1"

    def test_individual_scores_included(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        assert len(cert.individual_scores) == 5
        assert cert.individual_scores[0].ground_truth_id == "pr-0"

    def test_empty_scores_raises(self):
        gen = _make_generator()
        with pytest.raises(ValueError, match="empty scores"):
            gen.generate([])

    def test_zero_weights_raises(self, sample_scores: list[ReplayScore]):
        gen = _make_generator(
            composite_weights={"precision": 0.0, "recall": 0.0, "reply_accuracy": 0.0}
        )
        with pytest.raises(ValueError, match="weights must not all be zero"):
            gen.generate(sample_scores)

    def test_certificate_json_roundtrip(self, sample_scores: list[ReplayScore]):
        gen = _make_generator()
        cert = gen.generate(sample_scores)

        json_str = cert.model_dump_json()
        restored = CalibrationCertificate.model_validate_json(json_str)
        assert restored.composite_score == cert.composite_score
        assert restored.brier == cert.brier
        assert len(restored.individual_scores) == 5
