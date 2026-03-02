"""Commitment hash tests — determinism, label sensitivity, round-trip."""
from __future__ import annotations

from backend.market.commitment import ORACLE_CONFIG_STUB, MarketCommitment
from backend.market.lifecycle import MarketLifecycle
from backend.market.state import FeeSchedule


def _make_market(labels: list[str] | None = None) -> "MarketState":
    """Helper — creates a test market."""
    return MarketLifecycle.create_market(
        market_id="mkt_test",
        theatre_id="theatre_test",
        b=10.0,
        n_outcomes=3,
        outcome_labels=labels or ["Yes", "No", "Maybe"],
    )


class TestHashDeterminism:
    """Commitment hash must be deterministic."""

    def test_same_params_same_hash(self) -> None:
        m1 = _make_market()
        m2 = _make_market()
        h1 = MarketCommitment.compute_hash(m1)
        h2 = MarketCommitment.compute_hash(m2)
        assert h1 == h2

    def test_repeated_calls_same_hash(self) -> None:
        m = _make_market()
        h1 = MarketCommitment.compute_hash(m)
        h2 = MarketCommitment.compute_hash(m)
        assert h1 == h2


class TestHashSensitivity:
    """Hash changes when committed parameters change."""

    def test_hash_differs_on_label_order(self) -> None:
        m1 = _make_market(["Yes", "No", "Maybe"])
        m2 = _make_market(["No", "Yes", "Maybe"])
        h1 = MarketCommitment.compute_hash(m1)
        h2 = MarketCommitment.compute_hash(m2)
        assert h1 != h2

    def test_hash_differs_on_b(self) -> None:
        m1 = MarketLifecycle.create_market("m", "t", 10.0, 2, ["A", "B"])
        m2 = MarketLifecycle.create_market("m", "t", 20.0, 2, ["A", "B"])
        assert MarketCommitment.compute_hash(m1) != MarketCommitment.compute_hash(m2)

    def test_hash_differs_on_fee_schedule(self) -> None:
        m1 = MarketLifecycle.create_market(
            "m", "t", 10.0, 2, ["A", "B"], fee_schedule=FeeSchedule(0, 0)
        )
        m2 = MarketLifecycle.create_market(
            "m", "t", 10.0, 2, ["A", "B"], fee_schedule=FeeSchedule(10, 0)
        )
        assert MarketCommitment.compute_hash(m1) != MarketCommitment.compute_hash(m2)


class TestVerifyHash:
    """verify_hash round-trip."""

    def test_verify_hash_roundtrip(self) -> None:
        m = _make_market()
        m.commitment_hash = MarketCommitment.compute_hash(m)
        assert MarketCommitment.verify_hash(m) is True

    def test_verify_hash_none_returns_false(self) -> None:
        m = _make_market()
        assert m.commitment_hash is None
        assert MarketCommitment.verify_hash(m) is False

    def test_verify_hash_tampered_returns_false(self) -> None:
        m = _make_market()
        m.commitment_hash = "0" * 64
        assert MarketCommitment.verify_hash(m) is False


class TestOracleConfigStub:
    """Oracle config stub constant."""

    def test_oracle_config_stub_value(self) -> None:
        assert ORACLE_CONFIG_STUB == {"type": "manual", "version": "v0"}

    def test_hash_is_64_hex_chars(self) -> None:
        m = _make_market()
        h = MarketCommitment.compute_hash(m)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
