"""Theatre Status -- echelon_status integration for Sponsored Theatres.

Wraps Theatre live state for the echelon_status MCP tool. Provides
extended status during TRADING (prices, evidence coverage, source health)
and after SETTLEMENT (certificate state, composite score, counter-signal
status). Does not modify backend/engines/status.py.

Cycle-012, Sprint 2 -- Task 6.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from backend.market.lmsr import LMSREngine
from backend.services.certificate_pipeline import CalibrationCertificate
from backend.services.market_theatre_bridge import MarketTheatreBridge
from backend.services.theatre_evidence import TheatreEvidenceCollector


@dataclass
class TheatreStatusSnapshot:
    """Extended market status snapshot for Theatre-aware echelon_status.

    Base fields match MarketStatusSnapshot from backend/engines/status.py.
    Theatre extensions add evidence coverage, certificate state, etc.
    """

    # Base fields
    theatre_id: str
    market_phase: str
    current_prices: list[float]
    total_trades: int
    timeline_stability: float
    logic_gap_status: str | None
    logic_gap_value: float | None
    heartbeat_ticks: dict[str, int]
    commitment_hash: str
    on_chain: bool

    # Theatre extensions
    evidence_coverage_pct: float
    sources_online: int
    sources_total: int
    certificate_state: str | None
    composite_score: float | None
    counter_signal_status: str | None
    verification_tier: str | None

    # Cache
    cached_at: str
    ttl_seconds: int = 300


def build_theatre_status(
    theatre_id: str,
    bridge: MarketTheatreBridge,
    evidence_collector: TheatreEvidenceCollector | None = None,
    certificate: CalibrationCertificate | None = None,
    commitment_hash: str = "",
    on_chain: bool = False,
) -> TheatreStatusSnapshot:
    """Build a TheatreStatusSnapshot from Theatre components.

    During TRADING: returns current prices, evidence coverage, source status.
    After SETTLEMENT: returns certificate state, composite score, counter-signal status.
    """
    market_state = bridge.get_market_state(theatre_id)
    if market_state is None:
        raise ValueError(f"No market found for theatre '{theatre_id}'")

    market = market_state.market

    # Market prices from LMSR
    prices = list(LMSREngine.prices(market.x, market.b))

    # Trade count from position manager
    total_trades = sum(
        pos.trade_count
        for pos in market_state.position_manager.all_positions()
    )

    # Evidence state
    evidence_coverage = 0.0
    sources_online = 0
    sources_total = 0
    if evidence_collector is not None:
        latest = evidence_collector.get_latest_evidence()
        if latest is not None:
            evidence_coverage = latest.source_coverage_pct
        sources_total = len(evidence_collector._committed_sources)
        sources_online = int(evidence_coverage * sources_total)

    # Certificate state
    cert_state: str | None = None
    composite_score: float | None = None
    counter_signal_status: str | None = None
    verification_tier: str | None = None

    if certificate is not None:
        cert_state = "VALID"
        composite_score = certificate.composite_score
        verification_tier = certificate.verification_tier

        # Summarise counter-signal status
        if certificate.counter_signal_results:
            all_unavailable = all(
                r.get("outcome") == "unavailable"
                for r in certificate.counter_signal_results
            )
            counter_signal_status = (
                "ALL_UNAVAILABLE" if all_unavailable else "MIXED"
            )

    return TheatreStatusSnapshot(
        theatre_id=theatre_id,
        market_phase=market.phase.value,
        current_prices=prices,
        total_trades=total_trades,
        timeline_stability=1.0,  # Placeholder -- Butterfly not wired in Theatre flow
        logic_gap_status=None,
        logic_gap_value=None,
        heartbeat_ticks={},
        commitment_hash=commitment_hash or (market.commitment_hash or ""),
        on_chain=on_chain,
        evidence_coverage_pct=evidence_coverage,
        sources_online=sources_online,
        sources_total=sources_total,
        certificate_state=cert_state,
        composite_score=composite_score,
        counter_signal_status=counter_signal_status,
        verification_tier=verification_tier,
        cached_at=datetime.now(timezone.utc).isoformat(),
        ttl_seconds=300,
    )
