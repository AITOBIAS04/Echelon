"""E2E pipeline test — WM (mock) + CH (mock) -> corroboration -> scoring.

Verifies the complete data path: collection -> corroboration -> scoring
with both WorldMonitor and Companies House sources producing
corroboration_minimum_met: true and scoring factor 1.0.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.osint.collectors.companies_house import CompaniesHouseCollector
from backend.osint.collectors.worldmonitor import WorldMonitorCollector, WorldMonitorConfig
from backend.osint.engine.collection_runner import CollectionRunner
from backend.osint.engine.corroboration import CorroborationEngine
from backend.osint.engine.counter_signal import CounterSignalEvaluator
from backend.osint.engine.scorer import Scorer
from backend.osint.models.evidence import WMDomain
from backend.osint.models.registry import RegistryLoader

SOURCES_PATH = str(Path(__file__).parent.parent / "sources.json")
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_bytes(name: str) -> bytes:
    with open(FIXTURES_DIR / name, "rb") as f:
        return f.read()


class TestE2ECorroboration:
    """Full pipeline E2E with WM + CH producing corroboration_met=true."""

    @pytest.mark.asyncio
    async def test_e2e_wm_ch_pipeline(self) -> None:
        """Complete pipeline: collection -> corroboration -> scoring.

        WM (mock) + CH (mock) -> 2 distinct upstream groups ->
        corroboration_met=true -> scoring factor 1.0 -> p_reality not penalised.
        """
        # Setup collectors
        wm_config = WorldMonitorConfig(
            base_url="http://mock:8080", timeout_s=5.0, retry_count=0,
        )
        wm_collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=wm_config)
        ch_collector = CompaniesHouseCollector(api_key="test-key")

        # Setup collection runner with both collectors
        collectors = {
            "worldmonitor_cii": wm_collector,
            "companies_house_api": ch_collector,
        }
        runner = CollectionRunner(collectors)

        # Build plan
        oracle_config = {
            "theatre_id": "e2e-test",
            "sources": ["worldmonitor_cii", "companies_house_api"],
            "corroboration_minimum": 2,
            "evaluation_window": {
                "start": datetime.now(timezone.utc).isoformat(),
                "end": datetime.now(timezone.utc).isoformat(),
            },
            "timeout_s": 5.0,
            "source_params": {
                "companies_house_api": {"company_number": "00000006"},
            },
        }
        plan = runner.build_plan(oracle_config, "e2e-test")

        # Mock both HTTP calls
        wm_fixture = _load_fixture_bytes("wm_cii_response.json")
        ch_fixture = _load_fixture_bytes("ch_company_profile.json")

        with patch.object(wm_collector, "_do_http_post", return_value=wm_fixture), \
             patch.object(ch_collector, "_do_http_get", return_value=ch_fixture):
            # Stage 1: Collection (source_params delivers company_number to CH)
            results = await runner.collect(plan)

        # Verify both collected successfully
        successful = [r for r in results if r.success]
        assert len(successful) == 2, (
            f"Expected 2 successful, got {len(successful)}. "
            f"Errors: {[r.error for r in results if not r.success]}"
        )

        # Stage 2: Corroboration
        registry = RegistryLoader(SOURCES_PATH)
        corr_engine = CorroborationEngine(registry)
        corr_result = corr_engine.evaluate(results, oracle_config)

        assert corr_result.corroboration_met is True, (
            f"Expected corroboration_met=True, got False. "
            f"distinct_source_groups={corr_result.distinct_source_groups}"
        )
        assert corr_result.distinct_source_groups >= 2

        # Stage 3: Counter-signals (all UNAVAILABLE with allow_gap=True)
        cs_evaluator = CounterSignalEvaluator()
        cs_results = cs_evaluator.evaluate(results, oracle_config)

        # Stage 4: Scoring
        scorer = Scorer(registry)
        output = scorer.score(
            corroboration=corr_result,
            counter_signals=cs_results,
            collection_results=results,
            oracle_config=oracle_config,
            theatre_id="e2e-test",
        )

        # Verify scoring uses 1.0 factor (not 0.7)
        corr_criterion = next(
            c for c in output.criterion_scores
            if c.criterion == "corroboration_minimum_met"
        )
        assert corr_criterion.passed is True
        assert corr_criterion.score == 1.0

        # Composite score should not be penalised by corroboration
        assert output.composite_score > 0.0
        # With both sources at high confidence and factor 1.0,
        # score should be higher than the 0.7 penalty threshold
        assert output.composite_score > 0.5
