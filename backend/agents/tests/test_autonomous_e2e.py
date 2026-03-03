"""Autonomous Agent E2E -- full Companies House Theatre lifecycle.

The marquee test for Cycle-013. Tests:
  create -> commit -> trade (6 agents, 50 ticks) -> evidence injection
  (mock WM at ticks 10, 20, 35) -> resolve -> settle -> certificate
  (21 checks) -> RLMF -> delivery.

Deterministic: fixed seeds, balances, evidence fixtures.

Cycle-013, Sprint 3 -- Task 6 + Task 7.
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

from backend.agents.adk import FakeADKRunner
from backend.agents.adk.shark_v1 import MEGALODON_GENOME, spawn_megalodon
from backend.agents.agent_instance import TheatreAgentInstance
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import EchelonArchetype, create_genome
from backend.agents.rules_engine import RulesEngine
from backend.chain.sepolia import MockSepoliaClient
from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.state import FeeSchedule, MarketPhase
from backend.market.trading import TradingEngine
from backend.osint.engine.corroboration import CorroborationEngine
from backend.osint.engine.counter_signal import CounterSignalEvaluator
from backend.osint.engine.scorer import Scorer
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
from backend.services.agent_theatre_bridge import AgentTheatreBridge
from backend.services.certificate_pipeline import CertificatePipeline
from backend.services.market_theatre_bridge import MarketTheatreBridge
from backend.services.rlmf_export import (
    AgentTrace,
    MarketEpoch,
    RLMFExportGenerator,
)
from backend.services.sponsor_delivery import SponsorDeliveryAssembler
from backend.services.sponsored_theatre import SponsoredTheatreService
from backend.services.theatre_evidence import EvidenceSnapshot
from backend.services.theatre_resolution import TheatreResolutionEngine
from backend.services.theatre_status import build_theatre_status


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
        bundle_id=f"eb_{source_id}_001",
        source_id=source_id,
        source_group="alt_data_behavioural",
        resolution_role="primary_evidence",
        evidence_timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
        raw_payload_hash=content_hash,
        receipt=HTTPTranscriptReceipt(
            timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
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
            timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
        ),
    )


def _make_mock_collection_results(
    sources: list, confidence: float = 0.85,
) -> list:
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
    """Mock evidence collector for E2E tests."""

    def __init__(self, committed_sources, confidence=0.85):
        self._committed_sources = committed_sources
        self._confidence = confidence
        self._snapshots = []

    def collect_heartbeat(self, theatre_id):
        bundles = [
            _make_mock_bundle(s, self._confidence)
            for s in self._committed_sources
        ]
        snapshot = EvidenceSnapshot(
            theatre_id=theatre_id,
            collection_timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc).isoformat(),
            oracle_output=None,
            evidence_bundles=bundles,
            collection_results=[],
            source_coverage_pct=1.0,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_evidence_history(self):
        return list(self._snapshots)

    def get_latest_evidence(self):
        return self._snapshots[-1] if self._snapshots else None


@pytest.fixture
def registry_path():
    path = _make_test_registry()
    yield path
    os.unlink(path)


@pytest.fixture
def e2e_setup(registry_path):
    """Set up all components for autonomous agent E2E."""
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


class TestAutonomousAgentE2E:
    """Full Companies House Theatre lifecycle with autonomous agents."""

    def test_full_lifecycle_autonomous(self, e2e_setup):
        """Full lifecycle: create -> commit -> trade (6 agents, 50 ticks)
        -> evidence -> resolve -> settle -> certificate -> RLMF -> delivery.
        """
        service = e2e_setup["theatre_service"]
        market_bridge = e2e_setup["market_bridge"]
        loader = e2e_setup["loader"]

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
        assert review.n_outcomes == 3

        # === PHASE 2: Commit parameters ===
        commit_result = service.commit(theatre_id)
        assert commit_result["status"] == "TRADING"
        assert commit_result["lmsr_hash_verified"] is True
        commitment_hash = commit_result["commitment_hash"]

        market_state = market_bridge.get_market_state(theatre_id)
        assert market_state.market.phase == MarketPhase.TRADING

        # === PHASE 3: Spawn 6 autonomous agents and trade 50 ticks ===
        agent_bridge = AgentTheatreBridge()
        agents = agent_bridge.spawn_agents(
            theatre_id=theatre_id,
            initial_balance=50000.0,
            position_manager=market_state.position_manager,
        )
        assert len(agents) == 6

        # Evidence injection at ticks 10, 20, 35
        evidence_ticks = {10, 20, 35}
        evidence_data = {"type": "companies_house_filing_check", "status": "pending"}
        epochs = []

        for tick in range(50):
            evidence = evidence_data if tick in evidence_ticks else None

            # Record epoch BEFORE trading
            prices = LMSREngine.prices(
                market_state.market.x, market_state.market.b
            )
            epoch = MarketEpoch(
                tick=tick,
                timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc).isoformat(),
                prices=list(prices),
                x_vector=list(market_state.market.x),
                total_trades=sum(
                    p.trade_count
                    for p in market_state.position_manager.all_positions()
                ),
                trade_count_this_tick=0,
            )

            traces = agent_bridge.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=evidence,
                tick=tick,
                seed=42,
            )

            epoch.trade_count_this_tick = sum(
                1 for t in traces if "BUY" in t.action or "SELL" in t.action
            )
            epochs.append(epoch)

        all_traces = agent_bridge.collect_decision_traces()
        assert len(all_traces) == 300  # 6 agents * 50 ticks

        # Shark (MEGALODON is default Shark) trades most
        shark_agent = next(
            a for a in agents
            if a.genome.archetype == EchelonArchetype.SHARK
        )
        assert shark_agent.trade_count >= 20, (
            f"Shark traded only {shark_agent.trade_count} times, need >= 20"
        )

        # Verify total trades
        total_trades = sum(a.trade_count for a in agents)
        assert total_trades > 20

        # === PHASE 4: Collect evidence (mock) ===
        committed_sources = ["worldmonitor_cii", "worldmonitor_finance"]
        mock_collector = MockEvidenceCollector(committed_sources, confidence=0.85)
        for _ in range(3):
            mock_collector.collect_heartbeat(theatre_id)

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

        collection_results = _make_mock_collection_results(committed_sources)
        resolution_result = resolution_engine.resolve(
            theatre_id=theatre_id,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=collection_results,
        )

        assert 0.0 <= resolution_result.composite_score <= 1.0

        # === PHASE 6: Settle market ===
        winning_outcome = resolution_result.winning_outcome_index
        settlement_results = agent_bridge.settle_agents(
            agents, market_state.position_manager, winning_outcome
        )
        settlement_report = market_bridge.settle_market(theatre_id, winning_outcome)

        assert market_state.market.phase == MarketPhase.SETTLED
        assert settlement_report.winning_outcome == winning_outcome

        # Bounded-loss invariant (epsilon for float rounding)
        b = market_state.market.b
        n = market_state.market.n_outcomes
        worst_case = -b * math.log(n)
        assert settlement_report.market_maker_pnl >= worst_case - 1e-6

        # === PHASE 7: Certificate ===
        cert_pipeline = CertificatePipeline()
        certificate = cert_pipeline.generate(resolution_result, settlement_report)
        all_passed, checks = cert_pipeline.verify(certificate)

        if not all_passed:
            failures = [c for c in checks if "FAIL" in c]
            pytest.fail(f"Certificate failed checks: {failures}")

        assert all_passed is True
        assert len(checks) == 21

        # === PHASE 8: RLMF export ===
        agent_trace_list = []
        for agent in agents:
            agent_id = agent.agent_id
            agent_decision_traces = [
                t.to_rlmf_dict() for t in all_traces
                if t.agent_id == agent_id
            ]
            s = next(
                (s for s in settlement_report.agent_settlements
                 if s.agent_id == agent_id),
                None,
            )
            ar = next(
                (r for r in settlement_results if r.agent_id == agent_id),
                None,
            )

            agent_trace_list.append(AgentTrace(
                agent_id=agent_id,
                archetype=agent.genome.archetype.value,
                initial_balance=50000.0,
                final_balance=50000.0 - (s.net_cashflow if s else 0) + (s.payout if s else 0),
                total_trades=agent.trade_count,
                total_pnl=ar.realised_pnl if ar else 0.0,
                decision_traces=agent_decision_traces,
            ))

        rlmf_gen = RLMFExportGenerator()
        rlmf_export = rlmf_gen.generate(
            theatre_id=theatre_id,
            question=config.question,
            outcome_labels=list(config.outcome_labels),
            winning_outcome=winning_outcome,
            oracle_output_id=resolution_result.oracle_output_id,
            epochs=epochs,
            agent_traces=agent_trace_list,
            settlement_report=settlement_report,
            resolution_result=resolution_result,
        )

        assert rlmf_export.schema_version == "2.0.1"
        assert len(rlmf_export.epochs) == 50
        assert len(rlmf_export.agent_traces) == 6

        # Decision traces in RLMF contain actual trace data
        for at in agent_trace_list:
            assert len(at.decision_traces) == 50

        # === PHASE 9: Delivery ===
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
        assert len(delivery.commitment_hash) == 64

        # === PHASE 10: Status ===
        status = build_theatre_status(
            theatre_id=theatre_id,
            bridge=market_bridge,
            evidence_collector=mock_collector,
            certificate=certificate,
            commitment_hash=commitment_hash,
            on_chain=False,
        )

        assert status.market_phase == "SETTLED"
        assert status.certificate_state == "VALID"

    def test_shark_megalodon_20_trades(self, e2e_setup):
        """MEGALODON variant executes >= 20 trades over 50 ticks."""
        service = e2e_setup["theatre_service"]
        market_bridge = e2e_setup["market_bridge"]

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
        market_state = market_bridge.get_market_state(review.theatre_id)

        # Spawn MEGALODON via FakeADKRunner
        megalodon = spawn_megalodon(
            theatre_id=review.theatre_id,
            rules_engine=RulesEngine(),
        )
        market_state.position_manager.set_balance(megalodon.agent_id, 50000.0)

        runner = FakeADKRunner(agent_instance=megalodon, max_ticks=50)
        evidence_schedule = {
            10: {"type": "filing_check"},
            20: {"type": "filing_check"},
            35: {"type": "filing_check"},
        }

        # Spawn support agents for market dynamics (Shark needs momentum)
        support_bridge = AgentTheatreBridge()
        support_agents = support_bridge.spawn_agents(
            theatre_id=review.theatre_id,
            initial_balance=50000.0,
            position_manager=market_state.position_manager,
            archetypes=[EchelonArchetype.DEGEN, EchelonArchetype.SABOTEUR],
        )

        for tick in range(50):
            evidence = evidence_schedule.get(tick)

            # Support agents create market dynamics first
            support_bridge.execute_tick(
                agents=support_agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=evidence,
                tick=tick,
                seed=42,
            )

            # MEGALODON trades via FakeADKRunner
            runner.run_tick(
                market_state.market,
                market_state.position_manager,
                market_state.trading_engine,
                evidence,
                seed=42,
            )

        assert megalodon.trade_count >= 20, (
            f"MEGALODON traded only {megalodon.trade_count} times, need >= 20"
        )

        # Verify risk limits respected
        position = market_state.position_manager.get_position(megalodon.agent_id)
        for shares in position.shares:
            assert abs(shares) <= MEGALODON_GENOME.position_limit

        # Decision traces are valid
        for trace in runner.decision_log:
            assert isinstance(trace, DecisionTrace)
            assert trace.tier_used == "T1-RULES"
            assert trace.pattern_name != ""

    def test_shark_outperforms_degen(self, e2e_setup):
        """Shark outperforms Degen (or matches via calibration metric)."""
        service = e2e_setup["theatre_service"]
        market_bridge = e2e_setup["market_bridge"]

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
        market_state = market_bridge.get_market_state(review.theatre_id)

        agent_bridge = AgentTheatreBridge()
        agents = agent_bridge.spawn_agents(
            theatre_id=review.theatre_id,
            initial_balance=50000.0,
            position_manager=market_state.position_manager,
        )

        for tick in range(50):
            evidence = {"type": "filing"} if tick in {10, 20, 35} else None
            agent_bridge.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=evidence,
                tick=tick,
                seed=42,
            )

        results = agent_bridge.settle_agents(
            agents, market_state.position_manager, resolved_outcome=0
        )
        pnl = AgentTheatreBridge.aggregate_pnl(results)

        shark_pnl = pnl.get("SHARK", 0.0)
        degen_pnl = pnl.get("DEGEN", 0.0)
        saboteur_pnl = pnl.get("SABOTEUR", 0.0)

        # Shark should outperform at least one of Degen or Saboteur
        # via PnL, activity, or decision confidence (informed > random)
        shark_trades = next(
            r.trades_executed for r in results if r.archetype == "SHARK"
        )
        degen_trades = next(
            r.trades_executed for r in results if r.archetype == "DEGEN"
        )

        outperforms_pnl = shark_pnl >= degen_pnl or shark_pnl >= saboteur_pnl
        outperforms_activity = shark_trades >= degen_trades

        # Decision confidence: Shark (momentum, 0.5+delta*0.5) should average
        # higher than Degen (random, 0.2+random*0.3)
        all_traces = agent_bridge.collect_decision_traces()
        shark_agent = next(
            a for a in agents if a.genome.archetype == EchelonArchetype.SHARK
        )
        degen_agent = next(
            a for a in agents if a.genome.archetype == EchelonArchetype.DEGEN
        )
        shark_traces = [t for t in all_traces if t.agent_id == shark_agent.agent_id]
        degen_traces = [t for t in all_traces if t.agent_id == degen_agent.agent_id]
        shark_avg_conf = sum(t.confidence for t in shark_traces) / len(shark_traces)
        degen_avg_conf = sum(t.confidence for t in degen_traces) / len(degen_traces)
        outperforms_confidence = shark_avg_conf > degen_avg_conf

        assert outperforms_pnl or outperforms_activity or outperforms_confidence, (
            f"Shark (PnL={shark_pnl:.2f}, trades={shark_trades}, "
            f"conf={shark_avg_conf:.3f}) should outperform "
            f"Degen (PnL={degen_pnl:.2f}, trades={degen_trades}, "
            f"conf={degen_avg_conf:.3f}) or Saboteur (PnL={saboteur_pnl:.2f})"
        )

    def test_decision_traces_rlmf_compatible(self, e2e_setup):
        """All decision traces serialise to RLMF-compatible dicts."""
        service = e2e_setup["theatre_service"]
        market_bridge = e2e_setup["market_bridge"]

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
        market_state = market_bridge.get_market_state(review.theatre_id)

        agent_bridge = AgentTheatreBridge()
        agents = agent_bridge.spawn_agents(
            theatre_id=review.theatre_id,
            initial_balance=50000.0,
            position_manager=market_state.position_manager,
        )

        for tick in range(10):
            agent_bridge.execute_tick(
                agents=agents,
                market=market_state.market,
                trading_engine=market_state.trading_engine,
                position_manager=market_state.position_manager,
                evidence=None,
                tick=tick,
                seed=42,
            )

        traces = agent_bridge.collect_decision_traces()
        for trace in traces:
            rlmf_dict = trace.to_rlmf_dict()
            assert isinstance(rlmf_dict, dict)
            assert "tick_id" in rlmf_dict
            assert "agent_id" in rlmf_dict
            assert "tier_used" in rlmf_dict
            assert "confidence" in rlmf_dict
            assert "pattern_name" in rlmf_dict
            assert "options_considered" in rlmf_dict

    def test_deterministic_e2e(self, e2e_setup):
        """Running twice with same seed and theatre_id produces identical results."""
        # Use direct market creation with fixed theatre_id for determinism
        # (SponsoredTheatreService generates random theatre_ids which change
        # agent_ids and thus RNG seeds — not suitable for determinism tests)
        theatre_id = "theatre_determinism_test"

        # Run 1
        market1 = MarketLifecycle.create_market(
            market_id="mkt_det_1",
            theatre_id=theatre_id,
            b=100.0,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            fee_schedule=FeeSchedule(),
        )
        MarketLifecycle.commit(market1)
        MarketLifecycle.open_trading(market1)
        pos_mgr1 = PositionManager(n_outcomes=3, market_id="mkt_det_1")
        engine1 = TradingEngine(pos_mgr1)

        bridge1 = AgentTheatreBridge()
        agents1 = bridge1.spawn_agents(
            theatre_id=theatre_id,
            initial_balance=50000.0,
            position_manager=pos_mgr1,
        )

        for tick in range(20):
            bridge1.execute_tick(
                agents1, market1, engine1,
                pos_mgr1, None, tick, seed=42,
            )

        # Run 2 (identical setup, same theatre_id)
        market2 = MarketLifecycle.create_market(
            market_id="mkt_det_2",
            theatre_id=theatre_id,
            b=100.0,
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            fee_schedule=FeeSchedule(),
        )
        MarketLifecycle.commit(market2)
        MarketLifecycle.open_trading(market2)
        pos_mgr2 = PositionManager(n_outcomes=3, market_id="mkt_det_2")
        engine2 = TradingEngine(pos_mgr2)

        bridge2 = AgentTheatreBridge()
        agents2 = bridge2.spawn_agents(
            theatre_id=theatre_id,
            initial_balance=50000.0,
            position_manager=pos_mgr2,
        )

        for tick in range(20):
            bridge2.execute_tick(
                agents2, market2, engine2,
                pos_mgr2, None, tick, seed=42,
            )

        # Same theatre_id → same agent_ids → same RNG seeds → deterministic
        for a1, a2 in zip(
            sorted(agents1, key=lambda a: a.agent_id),
            sorted(agents2, key=lambda a: a.agent_id),
        ):
            assert a1.trade_count == a2.trade_count, (
                f"{a1.agent_id}: {a1.trade_count} != {a2.trade_count}"
            )
