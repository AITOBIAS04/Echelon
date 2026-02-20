"""Tests for Tier Assigner — all boundary conditions and expiry computation."""

from datetime import datetime, timedelta

import pytest

from theatre.engine.tier_assigner import TierAssigner, TierHistory


class TestTierAssignment:
    def test_unverified_low_replay_count(self):
        tier = TierAssigner.assign(
            replay_count=10,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_unverified_at_boundary(self):
        tier = TierAssigner.assign(
            replay_count=49,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_backtested_at_boundary(self):
        tier = TierAssigner.assign(
            replay_count=50,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "BACKTESTED"

    def test_backtested_above_boundary(self):
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.05,
        )
        assert tier == "BACKTESTED"

    def test_unverified_high_failure_rate(self):
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.21,
        )
        assert tier == "UNVERIFIED"

    def test_unverified_at_failure_boundary(self):
        """Exactly 20% is still allowed."""
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.20,
        )
        assert tier == "BACKTESTED"

    def test_unverified_missing_pins(self):
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=False,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_unverified_missing_scores(self):
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=False,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_unverified_missing_hash(self):
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=False,
            has_disputes=False,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_unverified_has_disputes(self):
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=True,
            failure_rate=0.0,
        )
        assert tier == "UNVERIFIED"

    def test_proven_with_history(self):
        history = TierHistory(
            consecutive_months_backtested=3,
            has_production_telemetry=True,
            has_attestation=True,
        )
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
            history=history,
        )
        assert tier == "PROVEN"

    def test_proven_requires_3_months(self):
        history = TierHistory(
            consecutive_months_backtested=2,
            has_production_telemetry=True,
            has_attestation=True,
        )
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
            history=history,
        )
        assert tier == "BACKTESTED"

    def test_proven_requires_telemetry(self):
        history = TierHistory(
            consecutive_months_backtested=6,
            has_production_telemetry=False,
            has_attestation=True,
        )
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
            history=history,
        )
        assert tier == "BACKTESTED"

    def test_proven_requires_attestation(self):
        history = TierHistory(
            consecutive_months_backtested=6,
            has_production_telemetry=True,
            has_attestation=False,
        )
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
            history=history,
        )
        assert tier == "BACKTESTED"

    def test_no_history_stays_backtested(self):
        tier = TierAssigner.assign(
            replay_count=200,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.0,
            history=None,
        )
        assert tier == "BACKTESTED"


class TestExpiryComputation:
    def test_unverified_no_expiry(self):
        assert TierAssigner.compute_expiry("UNVERIFIED", datetime(2026, 1, 1)) is None

    def test_backtested_90_days(self):
        issued = datetime(2026, 1, 1)
        expiry = TierAssigner.compute_expiry("BACKTESTED", issued)
        assert expiry == issued + timedelta(days=90)

    def test_proven_180_days(self):
        issued = datetime(2026, 1, 1)
        expiry = TierAssigner.compute_expiry("PROVEN", issued)
        assert expiry == issued + timedelta(days=180)

    def test_unknown_tier_no_expiry(self):
        assert TierAssigner.compute_expiry("UNKNOWN", datetime(2026, 1, 1)) is None


class TestTierHistory:
    def test_meets_requirements(self):
        h = TierHistory(
            consecutive_months_backtested=3,
            has_production_telemetry=True,
            has_attestation=True,
        )
        assert h.meets_proven_requirements() is True

    def test_not_enough_months(self):
        h = TierHistory(
            consecutive_months_backtested=2,
            has_production_telemetry=True,
            has_attestation=True,
        )
        assert h.meets_proven_requirements() is False

    def test_default_empty_history(self):
        h = TierHistory()
        assert h.meets_proven_requirements() is False
