"""Unit tests for WaterfallScorer — 5 binary checks for distribution waterfall."""

import asyncio
import copy
import json
from pathlib import Path

import pytest

from theatre.scoring.waterfall_scorer import WaterfallScorer

FIXTURE_PATH = Path(__file__).resolve().parents[2] / (
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/waterfall_fixtures_10.json"
)


@pytest.fixture
def scorer():
    return WaterfallScorer()


@pytest.fixture
def fixture_data():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def _make_gt(record):
    """Build ground_truth dict from a fixture record."""
    return {
        "input_data": record["inputs"],
        "expected_output": record["expected_outputs"],
    }


# ---- Happy-path: all 10 records pass all 5 criteria ----


@pytest.mark.parametrize("criteria_id", [
    "waterfall_arithmetic",
    "noi_pool_conservation",
    "rounding_policy_compliance",
    "cap_table_consistency",
    "ledger_reconciliation",
])
@pytest.mark.asyncio
async def test_all_records_pass_criteria(scorer, fixture_data, criteria_id):
    """All 10 fixture records should score 1.0 on each criteria."""
    for record in fixture_data["records"]:
        gt = _make_gt(record)
        score = await scorer.score(criteria_id, gt, gt["input_data"])
        assert score == 1.0, (
            f"Record {record['record_id']} failed {criteria_id}"
        )


# ---- Unknown criteria_id returns 0.0 ----


@pytest.mark.asyncio
async def test_unknown_criteria_returns_zero(scorer, fixture_data):
    record = fixture_data["records"][0]
    gt = _make_gt(record)
    score = await scorer.score("nonexistent_check", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: waterfall_arithmetic ----


@pytest.mark.asyncio
async def test_waterfall_arithmetic_wrong_split(scorer, fixture_data):
    """Changing a split amount should fail waterfall_arithmetic."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["payment"]["splits"][0]["amount"] = 999.0
    gt = _make_gt(record)
    score = await scorer.score("waterfall_arithmetic", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_waterfall_arithmetic_wrong_expected_sum(scorer, fixture_data):
    """Mismatch between splits_sum and actual sum fails."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["expected_outputs"]["distribution_statement"]["splits_sum"] = 999.0
    gt = _make_gt(record)
    score = await scorer.score("waterfall_arithmetic", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: noi_pool_conservation ----


@pytest.mark.asyncio
async def test_noi_pool_conservation_mismatch(scorer, fixture_data):
    """NOI allocations not summing to noi_pool should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["noi_report"]["allocations"][0]["amount"] = 999.0
    gt = _make_gt(record)
    score = await scorer.score("noi_pool_conservation", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: rounding_policy_compliance ----


@pytest.mark.asyncio
async def test_rounding_policy_compliance_bad_rounding(scorer, fixture_data):
    """Amount with >2dp should fail rounding check."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["expected_outputs"]["distribution_statement"]["distributions"] = 720.005
    gt = _make_gt(record)
    score = await scorer.score("rounding_policy_compliance", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: cap_table_consistency ----


@pytest.mark.asyncio
async def test_cap_table_consistency_mismatch(scorer, fixture_data):
    """Wrong per_token should fail cap_table check."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["cap_table_snapshot"]["distribution_per_token"] = 0.05
    gt = _make_gt(record)
    score = await scorer.score("cap_table_consistency", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: ledger_reconciliation ----


@pytest.mark.asyncio
async def test_ledger_reconciliation_mismatch(scorer, fixture_data):
    """Split amounts not matching gross should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["payment"]["splits"][0]["amount"] = 500.0
    gt = _make_gt(record)
    score = await scorer.score("ledger_reconciliation", gt, gt["input_data"])
    assert score == 0.0


# ---- Rounding boundary tests ----


@pytest.mark.asyncio
async def test_rounding_boundary_at_tolerance(scorer):
    """Amount at exactly £0.01 tolerance boundary should pass."""
    gt = {
        "input_data": {
            "payment": {
                "gross_amount": 100.01,
                "splits": [{"bucket": "a", "amount": 100.01}],
            },
            "noi_report": {"noi_pool": 0, "allocations": []},
            "cap_table_snapshot": {
                "distribution_per_token": 0,
                "token_supply": 0,
            },
        },
        "expected_output": {
            "distribution_statement": {
                "splits_sum": 100.01,
                "a": 100.01,
            }
        },
    }
    score = await scorer.score("waterfall_arithmetic", gt, gt["input_data"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_rounding_boundary_just_over_tolerance(scorer):
    """Amount exceeding £0.01 tolerance should fail."""
    gt = {
        "input_data": {
            "payment": {
                "gross_amount": 100.00,
                "splits": [{"bucket": "a", "amount": 100.02}],
            },
            "noi_report": {"noi_pool": 0, "allocations": []},
            "cap_table_snapshot": {
                "distribution_per_token": 0,
                "token_supply": 0,
            },
        },
        "expected_output": {
            "distribution_statement": {
                "splits_sum": 100.00,
                "a": 100.02,
            }
        },
    }
    score = await scorer.score("waterfall_arithmetic", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_rounding_policy_compliance_at_boundary(scorer):
    """£0.005 rounds to £0.01 with ROUND_HALF_UP — should pass if exactly 2dp."""
    gt = {
        "input_data": {},
        "expected_output": {
            "distribution_statement": {
                "amount": 100.01,
            }
        },
    }
    score = await scorer.score("rounding_policy_compliance", gt, gt["input_data"])
    assert score == 1.0
