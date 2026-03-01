"""Unit tests for ArrearsScorer — 6 binary checks for arrears resolution state machine.

Covers all 16 fixture records (10 valid + 6 targeted single-criterion failures),
unknown criterion handling, and Decimal arithmetic precision.
"""

import asyncio
import json
from pathlib import Path

import pytest

from theatre.scoring.arrears_scorer import ArrearsScorer

FIXTURE_PATH = Path(__file__).resolve().parents[2] / (
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/arrears_fixtures_v02_18.json"
)

CRITERIA_IDS = [
    "state_transition_validity",
    "ladder_redirection_arithmetic",
    "reserve_fund_impact",
    "distribution_adjustment",
    "grace_period_enforcement",
    "ladder_balance_protection",
]

# Failure records: each targets exactly one criterion.
FAILURE_MAP = {
    "arrears_0011": "state_transition_validity",
    "arrears_0012": "ladder_redirection_arithmetic",
    "arrears_0013": "reserve_fund_impact",
    "arrears_0014": "distribution_adjustment",
    "arrears_0015": "grace_period_enforcement",
    "arrears_0016": "ladder_balance_protection",
}


@pytest.fixture
def scorer():
    return ArrearsScorer()


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


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---- Happy-path: records arrears_0001 through arrears_0010 pass all 6 criteria ----


@pytest.mark.parametrize("criteria_id", CRITERIA_IDS)
def test_all_valid_records_pass_all_criteria(scorer, fixture_data, criteria_id):
    """Records arrears_0001--arrears_0010 should score 1.0 for all 6 criteria."""
    for record in fixture_data["records"][:10]:
        gt = _make_gt(record)
        score = _run(scorer.score(criteria_id, gt, oracle_output={}))
        assert score == 1.0, (
            f"Record {record['record_id']} failed {criteria_id}"
        )


# ---- Targeted failure records: each fails exactly one criterion ----


def test_state_transition_failure(scorer, fixture_data):
    """arrears_0011 fails state_transition_validity, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0011")
    gt = _make_gt(record)
    assert _run(scorer.score("state_transition_validity", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "state_transition_validity":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0011 should pass {cid}"


def test_ladder_redirection_failure(scorer, fixture_data):
    """arrears_0012 fails ladder_redirection_arithmetic, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0012")
    gt = _make_gt(record)
    assert _run(scorer.score("ladder_redirection_arithmetic", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "ladder_redirection_arithmetic":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0012 should pass {cid}"


def test_reserve_fund_failure(scorer, fixture_data):
    """arrears_0013 fails reserve_fund_impact, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0013")
    gt = _make_gt(record)
    assert _run(scorer.score("reserve_fund_impact", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "reserve_fund_impact":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0013 should pass {cid}"


def test_distribution_adjustment_failure(scorer, fixture_data):
    """arrears_0014 fails distribution_adjustment, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0014")
    gt = _make_gt(record)
    assert _run(scorer.score("distribution_adjustment", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "distribution_adjustment":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0014 should pass {cid}"


def test_grace_period_failure(scorer, fixture_data):
    """arrears_0015 fails grace_period_enforcement, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0015")
    gt = _make_gt(record)
    assert _run(scorer.score("grace_period_enforcement", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "grace_period_enforcement":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0015 should pass {cid}"


def test_ladder_balance_protection_failure(scorer, fixture_data):
    """arrears_0016 fails ladder_balance_protection, passes other 5."""
    record = next(r for r in fixture_data["records"] if r["record_id"] == "arrears_0016")
    gt = _make_gt(record)
    assert _run(scorer.score("ladder_balance_protection", gt, {})) == 0.0
    for cid in CRITERIA_IDS:
        if cid != "ladder_balance_protection":
            assert _run(scorer.score(cid, gt, {})) == 1.0, f"arrears_0016 should pass {cid}"


# ---- Unknown criterion returns 0.0 ----


def test_unknown_criterion_returns_zero(scorer, fixture_data):
    record = fixture_data["records"][0]
    gt = _make_gt(record)
    score = _run(scorer.score("nonexistent_check", gt, oracle_output={}))
    assert score == 0.0


# ---- Decimal arithmetic precision ----


def test_decimal_arithmetic_precision(scorer, fixture_data):
    """Verify Decimal-based arithmetic matches expected fixture values exactly.

    Records with ladder_redirection_detail (arrears_0004, arrears_0005, arrears_0008)
    have explicit applied_to_arrears + remainder_to_equity sums that must pass.
    """
    detail_records = [
        r for r in fixture_data["records"]
        if r["expected_outputs"].get("ladder_redirection_detail") is not None
    ]
    assert len(detail_records) >= 2, "Expected at least 2 records with ladder_redirection_detail"

    for record in detail_records:
        gt = _make_gt(record)
        score = _run(scorer.score("ladder_redirection_arithmetic", gt, {}))
        assert score == 1.0, (
            f"Record {record['record_id']} failed Decimal precision check"
        )
