"""Reality Signal providers — bridge between external truth and Paradox Engine.

Subclass per source type. Injected into ParadoxEngine via constructor.
Paradox never knows the concrete type — it only calls get_signal().
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RealitySignal:
    """External truth signal for a Theatre."""

    p_reality: float               # 0.0–1.0
    evidence_bundle_hash: str      # SHA-256 of evidence bundle
    certificate_id: str | None     # calibration certificate ID (osint) or None
    source_type: str               # "osint" | "deterministic" | "survey" | "simulation"


class RealitySignalProvider:
    """Abstract provider. Subclassed per source type."""

    def get_signal(self, theatre_id: str) -> RealitySignal:
        raise NotImplementedError


class OsintRealityProvider(RealitySignalProvider):
    """Reads composite_score from most recent calibration certificate."""

    def __init__(self, certificate_store: dict[str, dict] | None = None) -> None:
        self._store = certificate_store or {}

    def get_signal(self, theatre_id: str) -> RealitySignal:
        cert = self._store.get(theatre_id, {})
        return RealitySignal(
            p_reality=cert.get("composite_score", 0.5),
            evidence_bundle_hash=cert.get("evidence_hash", ""),
            certificate_id=cert.get("certificate_id"),
            source_type="osint",
        )


class DeterministicRealityProvider(RealitySignalProvider):
    """Reads scorer output (0.0 or 1.0) from deterministic computation."""

    def __init__(self, scorer_outputs: dict[str, float] | None = None) -> None:
        self._outputs = scorer_outputs or {}

    def get_signal(self, theatre_id: str) -> RealitySignal:
        p = self._outputs.get(theatre_id, 0.5)
        return RealitySignal(
            p_reality=p,
            evidence_bundle_hash="",
            certificate_id=None,
            source_type="deterministic",
        )


class StubRealityProvider(RealitySignalProvider):
    """For testing — returns configurable fixed p_reality."""

    def __init__(self, p_reality: float = 0.5) -> None:
        self._p_reality = p_reality

    def get_signal(self, theatre_id: str) -> RealitySignal:
        return RealitySignal(
            p_reality=self._p_reality,
            evidence_bundle_hash="stub_hash",
            certificate_id=None,
            source_type="simulation",
        )
