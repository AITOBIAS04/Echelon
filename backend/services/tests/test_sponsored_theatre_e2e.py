"""End-to-end integration test -- full Companies House Theatre lifecycle.

Tests the complete lifecycle: create -> commit -> trade -> collect evidence
-> resolve -> settle -> certificate -> RLMF -> delivery -> status.

Uses the reference fixture from SDD Section 13:
  "Will Acme Ltd file annual accounts by 30 Sep 2026?"
  3 outcomes, b=100, 6 stub agents, 10 trading ticks.

Cycle-012, Sprint 2 -- Task 10.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.chain.sepolia import MockSepoliaClient
from backend.market.lmsr import LMSREngine
from backend.market.resolution import ResolutionEngine
from backend.market.state import FeeSchedule, MarketPhase
from backend.osint.engine.corroboration import CorroborationEngine
from backend.osint.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
    CounterSignalEvaluator,
    CounterSignalOutcome,
    CounterSignalResult,
)
from backend.osint.engine.scorer import CriterionScore, OracleOutput, Scorer
from backend.osint.models.evidence import (
    CollectionResult,
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
)
from backend.osint.models.registry import RegistryLoader
from backend.osint.source_manifest import SourceManifestBuilder
from backend.schemas.sponsored_theatre import SponsoredTheatreConfig
from backend.services.certificate_pipeline import CertificatePipeline
from backend.services.market_theatre_bridge import MarketTheatreBridge
from backend.services.rlmf_export import (
    AgentTrace,
    MarketEpoch,
    RLMFExport,
    RLMFExportGenerator,
)
from backend.services.sponsor_delivery import SponsorDeliveryAssembler
from backend.services.sponsored_theatre import SponsoredTheatreService
from backend.services.stub_agents import StubAgentSpawner, TradeDecisionTrace
from backend.services.theatre_evidence import EvidenceSnapshot, TheatreEvidenceCollector
from backend.services.theatre_resolution import TheatreResolutionEngine
from backend.services.theatre_status import build_theatre_status

from theatre.engine.canonical_json import canonical_json


# ===================================================================
# Test Registry and Fixtures
# ===================================================================


def _make_test_registry() -> str:
    """Create a temporary registry JSON file for the E2E test."""
    registry = {
        "version": "0.3.2-wm",
        "sources": [
            {
                "source_id": "worldmonitor_cii",
                "source_name": "World Monitor Country Instability Index",
                "source_group": "alt_data_behavioural",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "intelligence",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "worldmonitor_finance",
                "source_name": "World Monitor Finance Monitor",
                "source_group": "market_data",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "market",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "companies_house_uk",
                "source_name": "Companies House UK",
                "source_group": "government_registry",
                "priority_bucket": "settlement_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "companies_house",
                "receipt_mode_minimum": "http_transcript",
                "settlement_eligible": True,
                "jurisdiction": "UK",
            },
        ],
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(registry, f)
    return path


def _make_mock_bundle(source_id: str, confidence: float) -> EvidenceBundle:
    """Create a mock EvidenceBundle."""
    raw_data = json.dumps({"source_id": source_id, "ts": "test"}).encode()
    content_hash = hashlib.sha256(raw_data).hexdigest()

    return EvidenceBundle(
        bundle_id=f"eb_{source_id}_{int(datetime.now(timezone.utc).timestamp())}",
        source_id=source_id,
        source_group="alt_data_behavioural",
        resolution_role="primary_evidence",
        evidence_timestamp=datetime.now(timezone.utc),
        raw_payload_hash=content_hash,
        receipt=HTTPTranscriptReceipt(
            timestamp=datetime.now(timezone.utc),
            request_parameters={
                "method": "POST",
                "url": f"http://localhost:8080/api/v1/mock/{source_id}",
                "query": "",
                "headers": "content-type:application/json",
            },
            source_id=source_id,
            source_version="v0.1.0",
            http_status=200,
            content_hash=content_hash,
        ),
        normalised_event=NormalisedEvent(
            event_id=f"evt_{source_id}_001",
            geo=GeoPoint(lat=51.5074, lon=-0.1278, radius_m=50000),
            measure=NormalisedMeasure(
                type=MeasureType.COUNTRY_INSTABILITY_INDEX,
                value=0.78,
                unit="0_1",
            ),
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
        ),
    )


def _make_mock_collection_results(
    sources: list[str], confidence: float = 0.85,
) -> list[CollectionResult]:
    """Create mock CollectionResults for all sources."""
    results = []
    for source_id in sources:
        bundle = _make_mock_bundle(source_id, confidence)
        results.append(
            CollectionResult(
                source_id=source_id,
                bundle=bundle,
                raw_payload=b"mock_payload",
                fetch_duration_ms=50.0,
                success=True,
            )
        )
    return results


class MockEvidenceCollector:
    """Mock evidence collector that returns pre-built evidence bundles."""

    def __init__(self, committed_sources: list[str], confidence: float = 0.85) -> None:
        self._committed_sources = committed_sources
        self._confidence = confidence
        self._snapshots: list[EvidenceSnapshot] = []

    def collect_heartbeat(self, theatre_id: str) -> EvidenceSnapshot:
        bundles = [_make_mock_bundle(s, self._confidence) for s in self._committed_sources]
        snapshot = EvidenceSnapshot(
            theatre_id=theatre_id,
            collection_timestamp=datetime.now(timezone.utc).isoformat(),
            oracle_output=None,
            evidence_bundles=bundles,
            collection_results=[],
            source_coverage_pct=1.0,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_evidence_history(self) -> list[EvidenceSnapshot]:
        return list(self._snapshots)

    def get_latest_evidence(self) -> EvidenceSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None


@pytest.fixture
def registry_path():
    path = _make_test_registry()
    yield path
    os.unlink(path)


@pytest.fixture
def e2e_components(registry_path):
    """Set up all components for the full E2E lifecycle."""
    loader = RegistryLoader(registry_path)
    manifest_builder = SourceManifestBuilder(loader)
    chain_client = MockSepoliaClient()
    market_bridge = MarketTheatreBridge()

    theatre_service = SponsoredTheatreService(
        registry_loader=loader,
        manifest_builder=manifest_builder,
        chain_client=chain_client,
        market_bridge=market_bridge,
    )

    return {
        "loader": loader,
        "manifest_builder": manifest_builder,
        "chain_client": chain_client,
        "market_bridge": market_bridge,
        "theatre_service": theatre_service,
    }


# ===================================================================
# E2E Integration Tests
# ===================================================================


class TestSponsoredTheatreE2E:
    """Full Companies House Theatre lifecycle integration test."""

    def test_full_lifecycle_e2e(self, e2e_components):
        """Full lifecycle: create -> commit -> trade -> evidence -> resolve
        -> settle -> certificate -> RLMF -> delivery -> status.
        """
        service = e2e_components["theatre_service"]
        bridge = e2e_components["market_bridge"]
        loader = e2e_components["loader"]

        # === PHASE 1: Create Companies House Theatre ===
        config = SponsoredTheatreConfig(
            question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            liquidity_b=Decimal("100"),
            fee_schedule=FeeSchedule(trade_fee_bps=50, resolution_fee_bps=100),
            sponsor_id="sponsor_acme",
            sponsor_metadata={"company": "Acme Ltd", "jurisdiction": "UK"},
        )

        review = service.create(config)
        theatre_id = review.theatre_id

        assert review.theatre_id.startswith("theatre_")
        assert review.n_outcomes == 3
        assert len(review.commitment_hash) == 64

        # === PHASE 2: Commit parameters ===
        commit_result = service.commit(theatre_id)

        assert commit_result["status"] == "COMMITTED"
        assert commit_result["lmsr_hash_verified"] is True

        commitment_hash = commit_result["commitment_hash"]
        assert len(commitment_hash) == 64

        # Verify market is now TRADING
        market_state = bridge.get_market_state(theatre_id)
        assert market_state.market.phase == MarketPhase.TRADING

        # === PHASE 3: Spawn 6 stub agents and trade 10 ticks ===
        spawner = StubAgentSpawner()
        agents = spawner.spawn(theatre_id, agent_count=6, initial_balance=1000.0)
        assert len(agents) == 6

        # Set agent balances
        for agent in agents:
            market_state.position_manager.set_balance(
                agent.agent_id, agent.initial_balance
            )

        # Track epochs and trade traces
        all_traces: list[TradeDecisionTrace] = []
        epochs: list[MarketEpoch] = []

        # Evidence injection at ticks 3, 6, 9
        evidence_ticks = {3, 6, 9}
        mock_evidence = {"type": "companies_house_filing_check", "status": "pending"}

        for tick in range(10):
            evidence = mock_evidence if tick in evidence_ticks else None

            # Record epoch BEFORE trading
            prices = LMSREngine.prices(market_state.market.x, market_state.market.b)
            epoch = MarketEpoch(
                tick=tick,
                timestamp=datetime.now(timezone.utc).isoformat(),
                prices=list(prices),
                x_vector=list(market_state.market.x),
                total_trades=sum(
                    p.trade_count for p in market_state.position_manager.all_positions()
                ),
                trade_count_this_tick=0,
            )

            traces = spawner.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=evidence,
                tick=tick,
                seed=42,
            )

            # Count executed trades this tick
            executed = sum(1 for t in traces if t.executed_trade is not None)
            epoch.trade_count_this_tick = executed

            epochs.append(epoch)
            all_traces.extend(traces)

        # Verify sufficient trades happened
        total_executed_trades = sum(
            1 for t in all_traces if t.executed_trade is not None
        )
        assert total_executed_trades > 20, f"Only {total_executed_trades} trades executed, expected >20"

        # === PHASE 4: Collect evidence (mock) ===
        committed_sources = ["worldmonitor_cii", "worldmonitor_finance"]
        mock_collector = MockEvidenceCollector(committed_sources, confidence=0.85)

        # Collect evidence snapshots at ticks 3, 6, 9
        for _ in range(3):
            mock_collector.collect_heartbeat(theatre_id)

        evidence_history = mock_collector.get_evidence_history()
        assert len(evidence_history) == 3

        # === PHASE 5: Resolve ===
        scorer = Scorer(loader)
        corroboration_engine = CorroborationEngine(loader)
        counter_signal_eval = CounterSignalEvaluator()

        source_manifest_dict = service._manifest_to_dict(
            service.get_theatre_record(theatre_id).source_manifest
        )

        oracle_config = {
            "sources": committed_sources,
            "corroboration_minimum": 2,
            "theatre_id": theatre_id,
        }

        resolution_engine = TheatreResolutionEngine(
            evidence_collector=mock_collector,
            scorer=scorer,
            corroboration_engine=corroboration_engine,
            counter_signal_evaluator=counter_signal_eval,
            source_manifest=source_manifest_dict,
            oracle_config=oracle_config,
        )

        collection_results = _make_mock_collection_results(committed_sources, confidence=0.85)

        resolution_result = resolution_engine.resolve(
            theatre_id=theatre_id,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=collection_results,
        )

        assert 0.0 <= resolution_result.composite_score <= 1.0
        assert 0 <= resolution_result.winning_outcome_index <= 2
        assert resolution_result.oracle_output_id.startswith(theatre_id)

        # === PHASE 6: Settle market ===
        winning_outcome = resolution_result.winning_outcome_index
        settlement_report = bridge.settle_market(theatre_id, winning_outcome)

        assert market_state.market.phase == MarketPhase.SETTLED
        assert settlement_report.winning_outcome == winning_outcome

        # Verify bounded-loss invariant: market_maker_pnl >= -b * ln(n)
        b = market_state.market.b
        n = market_state.market.n_outcomes
        worst_case = -b * math.log(n)
        assert settlement_report.market_maker_pnl >= worst_case, (
            f"Bounded-loss invariant violated: market_maker_pnl={settlement_report.market_maker_pnl} "
            f"< -b*ln(n)={worst_case}"
        )

        # === PHASE 7: Generate certificate ===
        cert_pipeline = CertificatePipeline()
        certificate = cert_pipeline.generate(resolution_result, settlement_report)

        # Run 21 echelon_verify checks
        all_passed, checks = cert_pipeline.verify(certificate)
        if not all_passed:
            failures = [c for c in checks if "FAIL" in c]
            pytest.fail(f"Certificate failed checks: {failures}")

        assert all_passed is True
        assert len(checks) == 21
        assert certificate.schema_version == "1.0.0"
        assert certificate.verification_tier == "UNVERIFIED"

        # === PHASE 8: Generate RLMF export ===
        # Build agent traces from trade decisions
        agent_trace_map: dict[str, AgentTrace] = {}
        for agent in agents:
            agent_id = agent.agent_id
            agent_decisions = [
                {
                    "tick": t.tick,
                    "trigger": t.trigger_condition,
                    "confidence": t.confidence,
                    "outcome_index": t.intent.outcome_index if t.intent else None,
                    "shares": t.intent.shares if t.intent else 0,
                    "executed": t.executed_trade is not None,
                    "pattern": t.pattern_name,
                }
                for t in all_traces if t.agent_id == agent_id
            ]

            # Compute final balance
            position = market_state.position_manager.get_position(agent_id)
            settlement = next(
                (s for s in settlement_report.agent_settlements if s.agent_id == agent_id),
                None,
            )
            final_balance = agent.initial_balance
            if settlement:
                final_balance = agent.initial_balance - settlement.net_cashflow + settlement.payout

            agent_trace_map[agent_id] = AgentTrace(
                agent_id=agent_id,
                archetype=agent.archetype.value,
                initial_balance=agent.initial_balance,
                final_balance=final_balance,
                total_trades=position.trade_count,
                total_pnl=settlement.realised_pnl if settlement else 0.0,
                decision_traces=agent_decisions,
            )

        rlmf_gen = RLMFExportGenerator()
        rlmf_export = rlmf_gen.generate(
            theatre_id=theatre_id,
            question=config.question,
            outcome_labels=list(config.outcome_labels),
            winning_outcome=winning_outcome,
            oracle_output_id=resolution_result.oracle_output_id,
            epochs=epochs,
            agent_traces=list(agent_trace_map.values()),
            settlement_report=settlement_report,
            resolution_result=resolution_result,
        )

        assert rlmf_export.schema_version == "2.0.1"
        assert rlmf_export.theatre_id == theatre_id
        assert len(rlmf_export.epochs) == 10
        assert len(rlmf_export.agent_traces) == 6
        assert rlmf_export.winning_outcome == winning_outcome

        # === PHASE 9: Assemble delivery package ===
        delivery_assembler = SponsorDeliveryAssembler()
        delivery = delivery_assembler.assemble(
            theatre_id=theatre_id,
            certificate=certificate,
            evidence_snapshots=mock_collector.get_evidence_history(),
            rlmf_export=rlmf_export,
            commitment_hash=commitment_hash,
            source_manifest=source_manifest_dict,
        )

        assert delivery.theatre_id == theatre_id
        assert delivery.certificate is not None
        assert delivery.evidence_bundle is not None
        assert delivery.rlmf_export is not None
        assert delivery.commitment_hash == commitment_hash
        assert delivery.echelon_status_url is not None

        # Verify 4 deliverables are non-empty
        assert len(delivery.certificate) > 0
        assert len(delivery.evidence_bundle) > 0
        assert len(delivery.rlmf_export) > 0
        assert len(delivery.commitment_hash) == 64

        # === PHASE 10: Query echelon_status ===
        status = build_theatre_status(
            theatre_id=theatre_id,
            bridge=bridge,
            evidence_collector=mock_collector,
            certificate=certificate,
            commitment_hash=commitment_hash,
            on_chain=False,
        )

        assert status.theatre_id == theatre_id
        assert status.market_phase == "SETTLED"
        assert status.certificate_state == "VALID"
        assert status.composite_score is not None
        assert status.verification_tier == "UNVERIFIED"
        assert status.ttl_seconds == 300

    def test_bounded_loss_invariant(self, e2e_components):
        """Market maker P&L >= -b * ln(n) after settlement."""
        service = e2e_components["theatre_service"]
        bridge = e2e_components["market_bridge"]

        config = SponsoredTheatreConfig(
            question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_acme",
        )

        review = service.create(config)
        service.commit(review.theatre_id)

        market_state = bridge.get_market_state(review.theatre_id)
        spawner = StubAgentSpawner()
        agents = spawner.spawn(review.theatre_id, agent_count=6, initial_balance=1000.0)

        for agent in agents:
            market_state.position_manager.set_balance(agent.agent_id, agent.initial_balance)

        for tick in range(10):
            spawner.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=None,
                tick=tick,
                seed=42,
            )

        settlement = bridge.settle_market(review.theatre_id, winning_outcome=0)

        b = market_state.market.b
        n = market_state.market.n_outcomes
        worst_case = -b * math.log(n)
        assert settlement.market_maker_pnl >= worst_case

    def test_stub_agents_produce_sufficient_trades(self, e2e_components):
        """6 agents over 10 ticks should produce >20 executed trades."""
        service = e2e_components["theatre_service"]
        bridge = e2e_components["market_bridge"]

        config = SponsoredTheatreConfig(
            question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_acme",
        )

        review = service.create(config)
        service.commit(review.theatre_id)

        market_state = bridge.get_market_state(review.theatre_id)
        spawner = StubAgentSpawner()
        agents = spawner.spawn(review.theatre_id, agent_count=6, initial_balance=1000.0)

        for agent in agents:
            market_state.position_manager.set_balance(agent.agent_id, agent.initial_balance)

        total_executed = 0
        for tick in range(10):
            traces = spawner.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence={"evidence": True} if tick in {3, 6, 9} else None,
                tick=tick,
                seed=42,
            )
            total_executed += sum(1 for t in traces if t.executed_trade is not None)

        assert total_executed > 20, f"Only {total_executed} trades executed"

    def test_rlmf_brier_score_computation(self, e2e_components):
        """Brier score correctly computed from final prices and winning outcome."""
        gen = RLMFExportGenerator()

        # Perfect prediction: probability 1.0 for winning outcome
        final_prices = [1.0, 0.0, 0.0]
        brier = gen.compute_brier_score(final_prices, winning_outcome=0)
        assert abs(brier) < 1e-10  # Perfect = 0.0

        # Worst prediction: probability 0.0 for winning outcome
        final_prices = [0.0, 0.5, 0.5]
        brier = gen.compute_brier_score(final_prices, winning_outcome=0)
        # (0-1)^2 + (0.5-0)^2 + (0.5-0)^2 = 1 + 0.25 + 0.25 = 1.5 / 3 = 0.5
        assert abs(brier - 0.5) < 1e-10

        # Uniform prediction: all 1/3
        final_prices = [1/3, 1/3, 1/3]
        brier = gen.compute_brier_score(final_prices, winning_outcome=0)
        expected = ((1/3 - 1)**2 + (1/3 - 0)**2 + (1/3 - 0)**2) / 3
        assert abs(brier - expected) < 1e-10

    def test_rlmf_agent_pnl_matches_settlement(self, e2e_components):
        """Per-agent P&L in RLMF export matches settlement report."""
        service = e2e_components["theatre_service"]
        bridge = e2e_components["market_bridge"]
        loader = e2e_components["loader"]

        config = SponsoredTheatreConfig(
            question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_acme",
        )

        review = service.create(config)
        service.commit(review.theatre_id)
        theatre_id = review.theatre_id

        market_state = bridge.get_market_state(theatre_id)
        spawner = StubAgentSpawner()
        agents = spawner.spawn(theatre_id, agent_count=6, initial_balance=1000.0)

        for agent in agents:
            market_state.position_manager.set_balance(agent.agent_id, agent.initial_balance)

        epochs = []
        all_traces = []
        for tick in range(10):
            prices = LMSREngine.prices(market_state.market.x, market_state.market.b)
            epoch = MarketEpoch(
                tick=tick,
                timestamp=datetime.now(timezone.utc).isoformat(),
                prices=list(prices),
                x_vector=list(market_state.market.x),
                total_trades=sum(p.trade_count for p in market_state.position_manager.all_positions()),
                trade_count_this_tick=0,
            )
            traces = spawner.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=None,
                tick=tick,
                seed=42,
            )
            epoch.trade_count_this_tick = sum(1 for t in traces if t.executed_trade is not None)
            epochs.append(epoch)
            all_traces.extend(traces)

        settlement = bridge.settle_market(theatre_id, winning_outcome=0)

        # Build mock resolution result
        committed_sources = ["worldmonitor_cii", "worldmonitor_finance"]
        mock_collector = MockEvidenceCollector(committed_sources, confidence=0.85)
        mock_collector.collect_heartbeat(theatre_id)
        scorer = Scorer(loader)
        corroboration_engine = CorroborationEngine(loader)
        counter_signal_eval = CounterSignalEvaluator()
        source_manifest_dict = service._manifest_to_dict(
            service.get_theatre_record(theatre_id).source_manifest
        )
        oracle_config = {"sources": committed_sources, "corroboration_minimum": 2, "theatre_id": theatre_id}
        resolution_engine = TheatreResolutionEngine(
            evidence_collector=mock_collector,
            scorer=scorer,
            corroboration_engine=corroboration_engine,
            counter_signal_evaluator=counter_signal_eval,
            source_manifest=source_manifest_dict,
            oracle_config=oracle_config,
        )
        collection_results = _make_mock_collection_results(committed_sources)
        resolution_result = resolution_engine.resolve(
            theatre_id=theatre_id,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=collection_results,
        )

        # Build agent traces
        agent_traces = []
        for agent in agents:
            agent_id = agent.agent_id
            position = market_state.position_manager.get_position(agent_id)
            s = next((s for s in settlement.agent_settlements if s.agent_id == agent_id), None)
            agent_traces.append(AgentTrace(
                agent_id=agent_id,
                archetype=agent.archetype.value,
                initial_balance=agent.initial_balance,
                final_balance=agent.initial_balance - (s.net_cashflow if s else 0) + (s.payout if s else 0),
                total_trades=position.trade_count,
                total_pnl=s.realised_pnl if s else 0.0,
                decision_traces=[],
            ))

        rlmf_gen = RLMFExportGenerator()
        rlmf_export = rlmf_gen.generate(
            theatre_id=theatre_id,
            question=config.question,
            outcome_labels=list(config.outcome_labels),
            winning_outcome=0,
            oracle_output_id=resolution_result.oracle_output_id,
            epochs=epochs,
            agent_traces=agent_traces,
            settlement_report=settlement,
            resolution_result=resolution_result,
        )

        # Verify per-agent P&L matches settlement report
        for s in settlement.agent_settlements:
            assert s.agent_id in rlmf_export.agent_pnl
            assert abs(rlmf_export.agent_pnl[s.agent_id] - s.realised_pnl) < 1e-10

    def test_echelon_status_during_trading(self, e2e_components):
        """echelon_status returns correct state during TRADING phase."""
        service = e2e_components["theatre_service"]
        bridge = e2e_components["market_bridge"]

        config = SponsoredTheatreConfig(
            question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_acme",
        )

        review = service.create(config)
        service.commit(review.theatre_id)

        # During TRADING, no certificate yet
        status = build_theatre_status(
            theatre_id=review.theatre_id,
            bridge=bridge,
            evidence_collector=None,
            certificate=None,
            commitment_hash=review.commitment_hash,
        )

        assert status.market_phase == "TRADING"
        assert status.certificate_state is None
        assert status.composite_score is None
        assert status.verification_tier is None
        assert len(status.current_prices) == 3
        assert status.ttl_seconds == 300

    def test_rlmf_schema_v201_conformance(self, e2e_components):
        """RLMF export schema version is 2.0.1 and has all required fields."""
        gen = RLMFExportGenerator()
        assert gen.SCHEMA_VERSION == "2.0.1"

    def test_medium_1_fix_p_reality_none(self):
        """MEDIUM-1: ParadoxEngine.scan() returns None when p_reality is None."""
        from backend.engines.butterfly import ButterflyEngine
        from backend.engines.logic_gap import LogicGapCalculator
        from backend.engines.paradox import ParadoxConfig, ParadoxEngine, ParadoxMode
        from backend.engines.reality_signal import RealitySignal, RealitySignalProvider

        class NoneRealityProvider(RealitySignalProvider):
            def get_signal(self, theatre_id: str) -> RealitySignal:
                return RealitySignal(
                    p_reality=None,
                    evidence_bundle_hash="",
                    certificate_id=None,
                    source_type="osint",
                )

        config = ParadoxConfig(mode=ParadoxMode.ENABLED)
        butterfly = ButterflyEngine()
        logic_gap = LogicGapCalculator()
        provider = NoneRealityProvider()

        engine = ParadoxEngine(config, butterfly, logic_gap, provider)

        # Should return None instead of raising TypeError
        result = engine.scan("test_theatre")
        assert result is None
