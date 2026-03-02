"""Engine configuration — committed parameters per Theatre.

Immutable after commitment. Included in commitment hash computation.
Reuses ParameterMutationAfterCommit from 010a exceptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ButterflyConfig:
    """Butterfly Engine committed parameters."""

    trade_impact_k: float = 0.1
    trade_impact_policy: str = "buy_negative_sell_positive"
    shield_tiers: dict[str, float] = field(
        default_factory=lambda: {"easy": 0.02, "medium": 0.05, "hard": 0.10}
    )
    sabotage_impact: float = -0.10  # deterministic midpoint (Sprint 1-2)


@dataclass
class EntropyConfig:
    """Entropy Engine committed parameters."""

    base_decay_rate: float = 0.01
    stressed_multiplier: float = 1.5
    danger_multiplier: float = 2.0
    critical_multiplier: float = 3.0


@dataclass
class EngineConfig:
    """Top-level committed engine configuration per Theatre."""

    butterfly: ButterflyConfig = field(default_factory=ButterflyConfig)
    entropy: EntropyConfig = field(default_factory=EntropyConfig)
    paradox: Any = None  # ParadoxConfig | None — avoids circular import
    vrf: Any = None  # VRFConfig | None — avoids circular import
    committed: bool = False

    def freeze(self) -> None:
        """Mark as committed. Raises if already committed."""
        from backend.market.exceptions import ParameterMutationAfterCommit

        if self.committed:
            raise ParameterMutationAfterCommit(
                "Engine configuration already committed"
            )
        self.committed = True

    def assert_not_committed(self) -> None:
        """Raise if configuration is already committed."""
        from backend.market.exceptions import ParameterMutationAfterCommit

        if self.committed:
            raise ParameterMutationAfterCommit(
                "Cannot modify committed engine configuration"
            )

    def to_commitment_dict(self) -> dict:
        """Serialisable dict for inclusion in commitment hash."""
        d: dict = {
            "butterfly": {
                "trade_impact_k": self.butterfly.trade_impact_k,
                "trade_impact_policy": self.butterfly.trade_impact_policy,
                "shield_tiers": self.butterfly.shield_tiers,
                "sabotage_impact": self.butterfly.sabotage_impact,
            },
            "entropy": {
                "base_decay_rate": self.entropy.base_decay_rate,
                "stressed_multiplier": self.entropy.stressed_multiplier,
                "danger_multiplier": self.entropy.danger_multiplier,
                "critical_multiplier": self.entropy.critical_multiplier,
            },
        }
        if self.paradox is not None:
            d["paradox"] = self.paradox.to_commitment_dict()
        if self.vrf is not None:
            d["vrf"] = self.vrf.to_commitment_dict()
        return d
