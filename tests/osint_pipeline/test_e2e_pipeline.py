"""End-to-end integration tests for the full 3-stage pipeline.

Tests the complete flow: CollectionRunner -> CorroborationEngine ->
CounterSignalChecker -> Scorer -> OracleOutput.

All HTTP calls use httpx.MockTransport — no live API calls.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.engine.collection_runner import CollectionRunner
from osint_pipeline.engine.corroboration import CorroborationEngine
from osint_pipeline.engine.counter_signal import CounterSignalChecker
from osint_pipeline.engine.scorer import Scorer
from osint_pipeline.models.evidence import (
    CollectionStatus,
    EvidenceBundle,
    FreshnessState,
    OracleCollectionSummary,
)
from osint_pipeline.models.oracle_output import OracleOutput


# ---------------------------------------------------------------------------
# Stub collectors for integration testing
# ---------------------------------------------------------------------------

class _StubCollectorA(BaseCollector):
    """Stub collector A — official_gov, GB."""

    @property
    def source_id(self) -> str:
        return "stub_gov_a"

    @property
    def source_group(self) -> str:
        return "official_gov"

    @property
    def independence_upstream_id(self) -> str:
        return "stub_upstream_gov_a"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(self, query_context):
        return "GET", "https://stub-a.example.com/api", {"Accept": "application/json"}, {"q": "test"}

    def extract(self, raw_body, status_code, query_context):
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0
        data = json.loads(raw_body)
        return {"source": "stub_a", "data": data}, 1.0

    def assess_freshness(self, structured_extract, retrieved_at):
        return FreshnessState.FRESH


class _StubCollectorB(BaseCollector):
    """Stub collector B — market_data, US."""

    @property
    def source_id(self) -> str:
        return "stub_market_b"

    @property
    def source_group(self) -> str:
        return "market_data"

    @property
    def independence_upstream_id(self) -> str:
        return "stub_upstream_market_b"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "US"

    def build_request(self, query_context):
        return "GET", "https://stub-b.example.com/api", {"Accept": "application/json"}, {"q": "test"}

    def extract(self, raw_body, status_code, query_context):
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0
        data = json.loads(raw_body)
        return {"source": "stub_b", "data": data}, 0.9

    def assess_freshness(self, structured_extract, retrieved_at):
        return FreshnessState.FRESH


class _StubCollectorC(BaseCollector):
    """Stub collector C — academic, EU, secondary corroboration."""

    @property
    def source_id(self) -> str:
        return "stub_academic_c"

    @property
    def source_group(self) -> str:
        return "academic"

    @property
    def independence_upstream_id(self) -> str:
        return "stub_upstream_academic_c"

    @property
    def resolution_role(self) -> str:
        return "secondary_corroboration"

    @property
    def jurisdiction(self) -> str:
        return "EU"

    def build_request(self, query_context):
        return "GET", "https://stub-c.example.com/api", {"Accept": "application/json"}, {"q": "test"}

    def extract(self, raw_body, status_code, query_context):
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0
        data = json.loads(raw_body)
        return {"source": "stub_c", "data": data}, 0.8

    def assess_freshness(self, structured_extract, retrieved_at):
        return FreshnessState.FRESH


def _mock_transport() -> httpx.MockTransport:
    """Create a mock transport that returns success for all URLs."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=json.dumps({"status": "ok", "query": str(request.url)}).encode()
        )
    return httpx.MockTransport(handler)


def _build_collectors() -> list[BaseCollector]:
    """Build 3 stub collectors with mock HTTP."""
    collectors = [_StubCollectorA(), _StubCollectorB(), _StubCollectorC()]
    transport = _mock_transport()
    for c in collectors:
        c._client = httpx.Client(transport=transport)
    return collectors


# ---------------------------------------------------------------------------
# End-to-End Tests
# ---------------------------------------------------------------------------

class TestE2EPipeline:
    """Full pipeline end-to-end with 3 mock collectors."""

    def test_full_pipeline_produces_oracle_output(self):
        """3 collectors -> CollectionRunner -> Corroboration -> CS -> Scorer."""
        collectors = _build_collectors()

        # Stage 1: Collection
        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(
            query_context={"company_number": "12345678"},
            theatre_id="test_theatre_001",
        )

        assert summary.total_sources_attempted == 3
        assert summary.total_sources_succeeded == 3
        assert len(summary.bundles) == 3
        assert len(summary.gaps) == 0

        # Stage 2: Corroboration
        corr_engine = CorroborationEngine(corroboration_minimum=2)
        corr_results = corr_engine.evaluate_all(summary)

        # We have 2 primary_evidence bundles, each should be evaluated
        primary_count = sum(
            1 for b in summary.bundles if b.resolution_role == "primary_evidence"
        )
        assert len(corr_results) == primary_count

        # Stage 2b: Counter-signal (empty — no CS-specific bundles)
        cs_checker = CounterSignalChecker()
        cs_results = cs_checker.evaluate([], [])

        # Stage 3: Scoring
        scorer = Scorer()
        output = scorer.score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
            theatre_id="test_theatre_001",
        )

        assert isinstance(output, OracleOutput)
        assert output.theatre_id == "test_theatre_001"
        assert output.oracle_id  # UUID present
        assert output.evaluated_at is not None

        runner.close_all()

    def test_composite_score_in_range(self):
        """OracleOutput.composite_score in [0.0, 1.0]."""
        collectors = _build_collectors()
        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])

        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        assert 0.0 <= output.composite_score <= 1.0
        runner.close_all()

    def test_coverage_percentage_correct(self):
        """Coverage percentage = (succeeded/attempted) * 100."""
        collectors = _build_collectors()
        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])
        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        expected = (summary.total_sources_succeeded / summary.total_sources_attempted) * 100
        assert abs(output.coverage_percentage - expected) < 0.01
        runner.close_all()

    def test_bundle_hash_deterministic(self):
        """Same collection -> same bundle_hash (within single run).

        Note: bundle hashes differ between runs because receipts include
        timestamps. Determinism is verified within a single collection.
        """
        collectors = _build_collectors()
        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])

        # Score twice with same inputs
        output1 = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )
        output2 = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        # Same summary -> same hash
        assert output1.bundle_hash == output2.bundle_hash
        runner.close_all()

    def test_gap_report_populated_when_collector_fails(self):
        """Failed collector produces gap report in OracleOutput."""
        def failing_handler(request: httpx.Request) -> httpx.Response:
            if "stub-b" in str(request.url):
                return httpx.Response(500, content=b"server error")
            return httpx.Response(
                200, content=json.dumps({"status": "ok"}).encode()
            )

        collectors = [_StubCollectorA(), _StubCollectorB(), _StubCollectorC()]
        transport = httpx.MockTransport(failing_handler)
        for c in collectors:
            c._client = httpx.Client(transport=transport)

        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        assert summary.total_sources_succeeded == 2
        assert summary.total_sources_failed == 1
        assert len(summary.gaps) == 1
        assert summary.gaps[0].source_id == "stub_market_b"

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])
        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        assert len(output.gap_report) == 1
        runner.close_all()

    def test_oracle_output_serialises_to_json(self):
        """OracleOutput can be serialised to JSON without errors."""
        collectors = _build_collectors()
        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])
        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        # Should serialise without error
        data = output.model_dump(mode="json")
        json_str = json.dumps(data, default=str)
        assert len(json_str) > 100

        # Should deserialise back
        parsed = json.loads(json_str)
        assert "bundle_hash" in parsed
        assert "composite_score" in parsed
        runner.close_all()


class TestE2EPipelineWithPartialCollectors:
    """Test pipeline with only 1-2 collectors available."""

    def test_single_collector_pipeline(self):
        """Pipeline works with just 1 collector."""
        collector = _StubCollectorA()
        collector._client = httpx.Client(transport=_mock_transport())

        runner = CollectionRunner(collectors=[collector])
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        assert summary.total_sources_succeeded == 1
        assert len(summary.bundles) == 1

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])
        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        assert isinstance(output, OracleOutput)
        assert 0.0 <= output.composite_score <= 1.0
        runner.close_all()

    def test_all_collectors_fail(self):
        """Pipeline handles all collectors failing."""
        def fail_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, content=b"error")

        collectors = _build_collectors()
        transport = httpx.MockTransport(fail_handler)
        for c in collectors:
            c._client = httpx.Client(transport=transport)

        runner = CollectionRunner(collectors=collectors)
        summary = runner.run(query_context={"test": True}, theatre_id="t1")

        assert summary.total_sources_succeeded == 0
        assert summary.total_sources_failed == 3

        corr_results = CorroborationEngine().evaluate_all(summary)
        cs_results = CounterSignalChecker().evaluate([], [])
        output = Scorer().score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
        )

        assert output.composite_score == 0.0
        assert output.coverage_percentage == 0.0
        runner.close_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
