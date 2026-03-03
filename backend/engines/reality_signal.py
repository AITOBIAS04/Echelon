"""Reality Signal providers — bridge between external truth and Paradox Engine.

Subclass per source type. Injected into ParadoxEngine via constructor.
Paradox never knows the concrete type — it only calls get_signal().

Cycle-011 Sprint 2 additions:
    - RealitySignal extended with optional provider_version and evidence_completeness
    - LiveOSINTRealityProvider: full OSINT pipeline orchestration
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RealitySignal:
    """External truth signal for a Theatre.

    Extended in Cycle-011 with optional provider_version and
    evidence_completeness fields (None defaults, backward compatible).
    """

    p_reality: float | None        # 0.0-1.0, or None if stale/unavailable
    evidence_bundle_hash: str      # SHA-256 of evidence bundle
    certificate_id: str | None     # calibration certificate ID (osint) or None
    source_type: str               # "osint" | "deterministic" | "survey" | "simulation"
    provider_version: str | None = None      # e.g. "011.1"
    evidence_completeness: float | None = None  # 0.0-1.0


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


class LiveOSINTRealityProvider(RealitySignalProvider):
    """Full OSINT pipeline orchestration — Cycle-011 Sprint 2.

    Pipeline: collect -> corroborate -> evaluate counter-signals -> score.
    Returns RealitySignal with p_reality = composite_score.

    Staleness protection: if last collection is older than max_staleness_s,
    returns p_reality=None so Paradox Engine skips the scan.

    Per-theatre cache stores the most recent OracleOutput, overwritten
    each run.
    """

    def __init__(
        self,
        collection_runner: object,     # CollectionRunner
        corroboration_engine: object,  # CorroborationEngine
        counter_signal_evaluator: object,  # CounterSignalEvaluator
        scorer: object,                # Scorer
        oracle_config: dict,
        max_staleness_s: float = 300.0,
        provider_version: str = "011.1",
    ) -> None:
        self._runner = collection_runner
        self._corroboration = corroboration_engine
        self._counter_signal = counter_signal_evaluator
        self._scorer = scorer
        self._oracle_config = oracle_config
        self._max_staleness_s = max_staleness_s
        self._provider_version = provider_version
        self._last_output: dict[str, object] = {}  # theatre_id -> OracleOutput
        self._last_output_time: dict[str, float] = {}  # theatre_id -> monotonic time

    def get_signal(self, theatre_id: str) -> RealitySignal:
        """Execute full OSINT pipeline and return RealitySignal.

        1. Check staleness — if cached output is fresh, reuse it.
        2. Otherwise run: collect -> corroborate -> counter-signal -> score.
        3. Cache the OracleOutput.
        4. Map to RealitySignal.

        Returns RealitySignal with p_reality=None if evidence is stale
        and collection fails.
        """
        import asyncio

        from backend.osint.engine.scorer import OracleOutput

        # Check if we have a fresh cached result
        if not self._check_staleness(theatre_id):
            cached = self._last_output.get(theatre_id)
            if cached is not None and isinstance(cached, OracleOutput):
                return self._oracle_output_to_signal(cached, theatre_id)

        # Run the full pipeline
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an async context — create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = pool.submit(
                        asyncio.run,
                        self._runner.collect(
                            self._runner.build_plan(self._oracle_config, theatre_id)
                        ),
                    ).result()
            else:
                results = loop.run_until_complete(
                    self._runner.collect(
                        self._runner.build_plan(self._oracle_config, theatre_id)
                    )
                )
        except Exception:
            # Collection failed — return stale signal
            return self._stale_signal(theatre_id)

        # Stage 2: Corroboration
        corroboration_config = dict(self._oracle_config)
        corroboration_config["theatre_id"] = theatre_id
        corroboration_result = self._corroboration.evaluate(
            results, corroboration_config
        )

        # Stage 2b: Counter-signals
        counter_signals = self._counter_signal.evaluate(results, self._oracle_config)

        # Stage 3: Scoring
        oracle_output = self._scorer.score(
            corroboration=corroboration_result,
            counter_signals=counter_signals,
            collection_results=results,
            oracle_config=self._oracle_config,
            theatre_id=theatre_id,
        )

        # Cache
        self._last_output[theatre_id] = oracle_output
        self._last_output_time[theatre_id] = time.monotonic()

        return self._oracle_output_to_signal(oracle_output, theatre_id)

    def _oracle_output_to_signal(
        self, output: object, theatre_id: str
    ) -> RealitySignal:
        """Map OracleOutput to RealitySignal."""
        from backend.osint.engine.scorer import OracleOutput

        if not isinstance(output, OracleOutput):
            return self._stale_signal(theatre_id)

        oracle_output_id = self._build_oracle_output_id(
            theatre_id, output.scored_at
        )
        return RealitySignal(
            p_reality=output.composite_score,
            evidence_bundle_hash=output.bundle_hash,
            certificate_id=oracle_output_id,
            source_type="osint",
            provider_version=self._provider_version,
            evidence_completeness=output.evidence_completeness,
        )

    def _check_staleness(self, theatre_id: str) -> bool:
        """Check if cached output is stale.

        Returns True if stale (needs refresh), False if fresh.
        """
        last_time = self._last_output_time.get(theatre_id)
        if last_time is None:
            return True  # No cached output — needs collection
        elapsed = time.monotonic() - last_time
        return elapsed >= self._max_staleness_s

    def _stale_signal(self, theatre_id: str) -> RealitySignal:
        """Return a signal indicating stale/unavailable evidence."""
        return RealitySignal(
            p_reality=None,
            evidence_bundle_hash="",
            certificate_id=None,
            source_type="osint",
            provider_version=self._provider_version,
            evidence_completeness=None,
        )

    @staticmethod
    def _build_oracle_output_id(theatre_id: str, scored_at: object) -> str:
        """Build oracle output ID: "{theatre_id}_{scored_at_ms}".

        Args:
            theatre_id: Theatre identifier.
            scored_at: datetime object from OracleOutput.

        Returns:
            String in format "{theatre_id}_{epoch_ms}".
        """
        from datetime import datetime

        if isinstance(scored_at, datetime):
            epoch_ms = int(scored_at.timestamp() * 1000)
        else:
            epoch_ms = 0
        return f"{theatre_id}_{epoch_ms}"
