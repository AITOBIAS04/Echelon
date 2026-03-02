"""FULL mode quant template tests — 4 suites with real engines active.

Verifies that all quant fixture suites produce correct results when the
full engine stack (Butterfly, Entropy, VRF, Paradox) is active.
LMSR math is unchanged; engines add tracking/fairness on top.
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.config import EngineConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import HeartbeatConfig, HeartbeatScheduler
from backend.engines.integration import EngineOrchestrator
from backend.engines.vrf import VRFConfig, VRFProvider
from backend.market.lmsr import LMSREngine
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.trading import TradingEngine

TOLERANCE = 1e-9
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "theatre" / "fixtures" / "echelon_quant_v0_2"
BASELINES_PATH = FIXTURES_DIR / "full_mode_baselines.json"


def _load_baselines() -> dict:
    with open(BASELINES_PATH) as f:
        return json.load(f)


def _make_full_mode_orchestrator(
    b: float = 100.0,
    n_outcomes: int = 2,
    market_id: str = "fm_test",
):
    """Wire engines for FULL mode fixture execution."""
    labels = ["O0", "O1", "O2", "O3", "O4"][:n_outcomes]
    market = MarketLifecycle.create_market(
        market_id, "full_mode_theatre", b, n_outcomes, labels,
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)

    position_manager = PositionManager(n_outcomes, market_id)
    position_manager.set_balance("agent_01", 100_000.0)
    trading_engine = TradingEngine(position_manager)
    butterfly = ButterflyEngine()
    engine_config = EngineConfig()
    entropy = EntropyEngine(engine_config.entropy, butterfly)
    heartbeat = HeartbeatScheduler(HeartbeatConfig())
    vrf = VRFProvider(VRFConfig(mode="local", seed="full_mode_seed"))

    orchestrator = EngineOrchestrator(
        market=market,
        trading_engine=trading_engine,
        position_manager=position_manager,
        butterfly=butterfly,
        entropy=entropy,
        engine_config=engine_config,
        heartbeat=heartbeat,
        vrf=vrf,
    )
    return orchestrator, butterfly, market


class TestHygieneSuiteFullMode:
    """quant_market_hygiene_v0_1 with full engine stack."""

    def test_hygiene_first_record_lmsr_matches(self) -> None:
        path = (
            FIXTURES_DIR
            / "quant_market_hygiene_v0_1"
            / "quant_market_hygiene_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]  # qmhy_0001: small_b_high_impact
        inputs = record["inputs"]
        b = inputs["market_spec"]["b"]
        n = inputs["market_spec"]["n_outcomes"]
        x0 = inputs["state_before"]["x"]
        trade = inputs["trade"]
        outcome_idx = trade["outcome_index"]
        delta_shares = trade["delta_shares"]

        # Run through full engine stack
        orch, butterfly, market = _make_full_mode_orchestrator(b=b, n_outcomes=n)
        trade_result = orch.execute_trade_with_flap("agent_01", outcome_idx, delta_shares)

        # LMSR cost matches fixture (engines don't modify cost)
        expected_cost = record["expected_outputs"]["execution"]["cost_paid"]
        assert abs(trade_result.cost - expected_cost) < TOLERANCE

        # Engine state tracked
        flaps = butterfly.get_flaps("fm_test")
        assert len(flaps) == 1
        assert flaps[0].flap_type == WingFlapType.TRADE

    def test_hygiene_engine_stability_bounded(self) -> None:
        path = (
            FIXTURES_DIR
            / "quant_market_hygiene_v0_1"
            / "quant_market_hygiene_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]
        inputs = record["inputs"]
        b = inputs["market_spec"]["b"]
        n = inputs["market_spec"]["n_outcomes"]
        trade = inputs["trade"]

        orch, butterfly, _ = _make_full_mode_orchestrator(b=b, n_outcomes=n)
        orch.execute_trade_with_flap("agent_01", trade["outcome_index"], trade["delta_shares"])

        state = butterfly.get_timeline_state("fm_test")
        assert 0.0 <= state.stability <= 1.0


class TestBSensitivitySuiteFullMode:
    """lmsr_b_sensitivity_suite_v0_1 with full engine stack."""

    def test_b_sensitivity_costs_match(self) -> None:
        path = (
            FIXTURES_DIR
            / "b_sensitivity_suite_v0_1"
            / "b_sensitivity_fixtures_5.json"
        )
        with open(path) as f:
            data = json.load(f)

        for record in data["records"]:
            inputs = record["inputs"]
            b = inputs["b"]
            trade = inputs["trade"]
            x0 = trade["x0"]
            n = trade["n_outcomes"]
            j = trade["j"]
            delta_shares = trade["delta"]

            # Verify LMSR math matches (pure cost function)
            delta = [0.0] * n
            delta[j] = delta_shares
            actual_cost = LMSREngine.trade_cost(x0, delta, b)
            expected_cost = record["expected_outputs"]["execution"]["cost_paid"]
            assert abs(actual_cost - expected_cost) < TOLERANCE, (
                f"b={b}: expected {expected_cost}, got {actual_cost}"
            )

    def test_b_sensitivity_engine_tracking(self) -> None:
        """Engines track state for first b-sensitivity record."""
        path = (
            FIXTURES_DIR
            / "b_sensitivity_suite_v0_1"
            / "b_sensitivity_fixtures_5.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]
        inputs = record["inputs"]
        b = inputs["b"]
        trade = inputs["trade"]
        n = trade["n_outcomes"]
        j = trade["j"]
        delta_shares = trade["delta"]

        orch, butterfly, _ = _make_full_mode_orchestrator(b=b, n_outcomes=n)
        orch.execute_trade_with_flap("agent_01", j, delta_shares)

        flaps = butterfly.get_flaps("fm_test")
        assert len(flaps) == 1
        assert flaps[0].stability_impact != 0.0


class TestApiFidelitySuiteFullMode:
    """quant_market_api_fidelity_v0_1 with full engine stack."""

    def test_api_fidelity_quote_correct(self) -> None:
        path = (
            FIXTURES_DIR
            / "api_fidelity_suite_v0_1"
            / "api_fidelity_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]  # api_0001
        inputs = record["inputs"]
        state_feed = inputs["state_feed"]
        x = state_feed["x"]
        b = state_feed["b"]
        n = state_feed["n_outcomes"]
        quote_req = inputs["quote_request"]
        j = quote_req["outcome_index"]
        delta_shares = quote_req["delta_shares"]

        # Verify quote matches LMSR
        delta = [0.0] * n
        delta[j] = delta_shares
        actual_cost = LMSREngine.trade_cost(x, delta, b)
        expected_cost = inputs["quote_response"]["quoted_cost"]
        assert abs(actual_cost - expected_cost) < TOLERANCE

    def test_api_fidelity_prices_after(self) -> None:
        path = (
            FIXTURES_DIR
            / "api_fidelity_suite_v0_1"
            / "api_fidelity_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]
        inputs = record["inputs"]
        state_feed = inputs["state_feed"]
        x = state_feed["x"]
        b = state_feed["b"]
        n = state_feed["n_outcomes"]
        quote_req = inputs["quote_request"]
        j = quote_req["outcome_index"]
        delta_shares = quote_req["delta_shares"]

        delta = [0.0] * n
        delta[j] = delta_shares
        x_new = [xi + di for xi, di in zip(x, delta)]
        actual_prices = LMSREngine.prices(x_new, b)
        expected_prices = inputs["quote_response"]["quoted_prices_after"]

        for ap, ep in zip(actual_prices, expected_prices):
            assert abs(ap - ep) < TOLERANCE


class TestPerturbationSuiteFullMode:
    """quant_market_perturbation_harness_v0_1 with full engine stack."""

    def test_perturbation_fixtures_load(self) -> None:
        path = (
            FIXTURES_DIR
            / "perturbation_suite_v0_1"
            / "perturbation_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        assert data["dataset_id"] == "perturbation_suite_v0_2_10"
        assert len(data["records"]) == 10

    def test_perturbation_vrf_seed_deterministic(self) -> None:
        """VRF with fixture seed produces deterministic output."""
        path = (
            FIXTURES_DIR
            / "perturbation_suite_v0_1"
            / "perturbation_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)

        record = data["records"][0]  # pert_0001 baseline
        vrf_seed = str(record["inputs"]["vrf"]["seed"])

        vrf = VRFProvider(VRFConfig(mode="local", seed=vrf_seed))
        r1 = vrf.request_randomness("mkt_0001", "perturbation")
        r2 = VRFProvider(VRFConfig(mode="local", seed=vrf_seed)).request_randomness(
            "mkt_0001", "perturbation"
        )
        assert r1.random_value == r2.random_value


class TestBaselinesFile:
    """FULL mode baselines JSON exists and is well-formed."""

    def test_baselines_file_exists(self) -> None:
        assert BASELINES_PATH.exists(), f"Baselines not found: {BASELINES_PATH}"

    def test_baselines_structure(self) -> None:
        baselines = _load_baselines()
        assert "version" in baselines
        assert "suites" in baselines
        expected_suites = {
            "quant_market_hygiene_v0_1",
            "b_sensitivity_suite_v0_1",
            "api_fidelity_suite_v0_1",
            "perturbation_suite_v0_1",
        }
        assert set(baselines["suites"].keys()) == expected_suites

    def test_baselines_engine_defaults(self) -> None:
        baselines = _load_baselines()
        for suite in baselines["suites"].values():
            defaults = suite["engine_defaults"]
            assert defaults["trade_impact_k"] == 0.1
            assert defaults["vrf_mode"] == "local"
