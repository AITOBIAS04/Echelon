"""VRF Provider — verifiable random function for engine fairness.

Local mode: HMAC-SHA256 with fixed seed — deterministic, reproducible.
Testnet mode: placeholder for Chainlink VRF V2 on Base Sepolia.
Purpose-tagged: same seed + theatre + purpose → same output.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


@dataclass
class VRFConfig:
    """Committed VRF parameters."""

    provider: str = "chainlink_v2"
    mode: str = "local"  # "local" | "testnet"
    seed: str | None = "0xECHELON_VRF_010b"  # fixed for local mode

    def to_commitment_dict(self) -> dict:
        """Serialisable dict for inclusion in commitment hash."""
        return {
            "provider": self.provider,
            "mode": self.mode,
            "seed": self.seed,
        }


@dataclass
class VRFResult:
    """Output of a VRF request."""

    request_id: str
    random_value: int  # uint256 range
    proof: bytes | None  # None in local mode
    verified: bool
    purpose: str


class VRFProvider:
    """Verifiable Random Function provider."""

    def __init__(self, config: VRFConfig) -> None:
        self._config = config
        self._request_counter: int = 0

    def request_randomness(self, theatre_id: str, purpose: str) -> VRFResult:
        """Request a random value tagged by theatre and purpose.

        Local mode: HMAC-SHA256(seed, theatre_id:purpose) → deterministic uint256.
        Testnet mode: raises NotImplementedError (Chainlink VRF V2 not wired).
        """
        if self._config.mode == "testnet":
            raise NotImplementedError(
                "Testnet VRF requires Chainlink VRF V2 — not wired in Sprint 3"
            )

        if self._config.seed is None:
            raise ValueError("VRF local mode requires a non-None seed")

        self._request_counter += 1
        request_id = f"vrf_{self._request_counter}"

        # HMAC-SHA256: deterministic, purpose-tagged
        key = self._config.seed.encode("utf-8")
        message = f"{theatre_id}:{purpose}".encode("utf-8")
        digest = hmac.new(key, message, hashlib.sha256).digest()
        random_value = int.from_bytes(digest, "big") % (2**256)

        return VRFResult(
            request_id=request_id,
            random_value=random_value,
            proof=None,  # local mode — no on-chain proof
            verified=True,  # local mode — always verified
            purpose=purpose,
        )

    def verify(self, result: VRFResult) -> bool:
        """Verify a VRF result. Local: always True. Testnet: on-chain proof."""
        if self._config.mode == "local":
            return True
        raise NotImplementedError("Testnet verification not wired")

    @staticmethod
    def scale_to_range(
        random_value: int, min_val: float, max_val: float
    ) -> float:
        """Scale uint256 to [min_val, max_val] range.

        Used by engines to convert VRF output to their committed impact ranges.
        """
        if min_val >= max_val:
            return min_val
        # Normalise to [0.0, 1.0] then scale
        normalised = random_value / (2**256 - 1)
        return min_val + normalised * (max_val - min_val)
