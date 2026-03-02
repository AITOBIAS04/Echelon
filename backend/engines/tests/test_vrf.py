"""VRF Provider tests — local determinism, purpose differentiation, scaling."""
from __future__ import annotations

import pytest

from backend.engines.vrf import VRFConfig, VRFProvider, VRFResult

TOLERANCE = 1e-9


class TestLocalDeterminism:
    """Same seed + theatre + purpose → same output."""

    def test_same_inputs_same_output(self) -> None:
        config = VRFConfig(mode="local", seed="test_seed")
        vrf = VRFProvider(config)
        r1 = vrf.request_randomness("t1", "sabotage_impact")
        vrf2 = VRFProvider(config)
        r2 = vrf2.request_randomness("t1", "sabotage_impact")
        assert r1.random_value == r2.random_value

    def test_different_seed_different_output(self) -> None:
        vrf1 = VRFProvider(VRFConfig(mode="local", seed="seed_A"))
        vrf2 = VRFProvider(VRFConfig(mode="local", seed="seed_B"))
        r1 = vrf1.request_randomness("t1", "sabotage_impact")
        r2 = vrf2.request_randomness("t1", "sabotage_impact")
        assert r1.random_value != r2.random_value

    def test_verified_true_in_local(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="seed"))
        result = vrf.request_randomness("t1", "test")
        assert result.verified is True
        assert result.proof is None

    def test_request_id_increments(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="seed"))
        r1 = vrf.request_randomness("t1", "a")
        r2 = vrf.request_randomness("t1", "b")
        assert r1.request_id == "vrf_1"
        assert r2.request_id == "vrf_2"


class TestPurposeDifferentiation:
    """Different purposes produce different values for the same theatre."""

    def test_different_purpose_different_value(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="test_seed"))
        r1 = vrf.request_randomness("t1", "sabotage_impact")
        r2 = vrf.request_randomness("t1", "threshold_offset")
        assert r1.random_value != r2.random_value

    def test_different_theatre_different_value(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="test_seed"))
        r1 = vrf.request_randomness("t1", "sabotage_impact")
        r2 = vrf.request_randomness("t2", "sabotage_impact")
        assert r1.random_value != r2.random_value


class TestScaleToRange:
    """scale_to_range converts uint256 to [min, max] range."""

    def test_zero_maps_to_min(self) -> None:
        assert VRFProvider.scale_to_range(0, -0.15, -0.05) == -0.15

    def test_max_maps_to_max(self) -> None:
        result = VRFProvider.scale_to_range(2**256 - 1, -0.15, -0.05)
        assert abs(result - (-0.05)) < TOLERANCE

    def test_midpoint(self) -> None:
        mid = (2**256 - 1) // 2
        result = VRFProvider.scale_to_range(mid, 0.0, 1.0)
        assert abs(result - 0.5) < 0.01  # approximate

    def test_equal_range_returns_min(self) -> None:
        assert VRFProvider.scale_to_range(12345, 0.5, 0.5) == 0.5

    def test_within_bounds(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="seed"))
        result = vrf.request_randomness("t1", "test")
        scaled = VRFProvider.scale_to_range(result.random_value, -0.15, -0.05)
        assert -0.15 <= scaled <= -0.05


class TestVerify:
    """Verification of VRF results."""

    def test_local_verify_always_true(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed="seed"))
        result = vrf.request_randomness("t1", "test")
        assert vrf.verify(result) is True


class TestTestnetMode:
    """Testnet mode raises NotImplementedError."""

    def test_testnet_raises(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="testnet"))
        with pytest.raises(NotImplementedError):
            vrf.request_randomness("t1", "test")

    def test_none_seed_raises(self) -> None:
        vrf = VRFProvider(VRFConfig(mode="local", seed=None))
        with pytest.raises(ValueError, match="non-None seed"):
            vrf.request_randomness("t1", "test")


class TestCommitmentDict:
    """VRF config in commitment hash."""

    def test_commitment_dict_keys(self) -> None:
        config = VRFConfig(mode="local", seed="my_seed")
        d = config.to_commitment_dict()
        assert d["provider"] == "chainlink_v2"
        assert d["mode"] == "local"
        assert d["seed"] == "my_seed"
