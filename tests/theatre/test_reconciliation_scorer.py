"""Unit tests for ReconciliationScorer — 5 binary checks for ledger reconciliation."""

import asyncio
import copy
import json
from pathlib import Path

import pytest

from theatre.scoring.reconciliation_scorer import ReconciliationScorer

FIXTURE_PATH = Path(__file__).resolve().parents[2] / (
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/reconciliation_fixtures_10.json"
)


@pytest.fixture
def scorer():
    return ReconciliationScorer()


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
    "bank_ref_match",
    "bucket_sum_matches_gross",
    "bucket_destination_valid",
    "event_log_complete",
    "exceptions_correct",
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


# ---- Per-check failure: bank_ref_match ----


@pytest.mark.asyncio
async def test_bank_ref_match_missing_ref(scorer, fixture_data):
    """Bank reference not found in transactions should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["bank_statement_slice"]["transactions"] = []
    gt = _make_gt(record)
    score = await scorer.score("bank_ref_match", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_bank_ref_match_wrong_ref(scorer, fixture_data):
    """Mismatched bank reference should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["bank_statement_slice"]["transactions"][0]["reference"] = "WRONG-REF"
    gt = _make_gt(record)
    score = await scorer.score("bank_ref_match", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: bucket_sum_matches_gross ----


@pytest.mark.asyncio
async def test_bucket_sum_mismatch(scorer, fixture_data):
    """Splits not summing to gross should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["payment"]["splits"][0]["amount"] = 999.0
    gt = _make_gt(record)
    score = await scorer.score("bucket_sum_matches_gross", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: bucket_destination_valid ----


@pytest.mark.asyncio
async def test_bucket_destination_invalid(scorer, fixture_data):
    """Destination not in allowed list should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["payment"]["splits"][0]["destination_ref"] = "hacker_wallet"
    gt = _make_gt(record)
    score = await scorer.score("bucket_destination_valid", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_bucket_destination_unknown_bucket(scorer, fixture_data):
    """Split with unknown bucket (no rule) should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["payment"]["splits"][0]["bucket"] = "unknown_bucket"
    gt = _make_gt(record)
    score = await scorer.score("bucket_destination_valid", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: event_log_complete ----


@pytest.mark.asyncio
async def test_event_log_missing_event(scorer, fixture_data):
    """Fewer events than splits should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["event_log"] = [record["inputs"]["event_log"][0]]
    gt = _make_gt(record)
    score = await scorer.score("event_log_complete", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_event_log_extra_event(scorer, fixture_data):
    """More events than splits should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["event_log"].append({
        "event_id": "extra",
        "type": "payment_split_posted",
        "bucket": "extra_bucket",
        "amount": 0,
        "ref": "REF",
    })
    gt = _make_gt(record)
    score = await scorer.score("event_log_complete", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_event_log_wrong_bucket(scorer, fixture_data):
    """Events with non-matching buckets should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["event_log"][0]["bucket"] = "wrong_bucket"
    gt = _make_gt(record)
    score = await scorer.score("event_log_complete", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: exceptions_correct ----


@pytest.mark.asyncio
async def test_exceptions_not_empty(scorer, fixture_data):
    """Non-empty exceptions list should fail (happy path expects empty)."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["expected_outputs"]["reconciliation_result"]["exceptions"] = [
        {"type": "amount_mismatch"}
    ]
    gt = _make_gt(record)
    score = await scorer.score("exceptions_correct", gt, gt["input_data"])
    assert score == 0.0


# ---- Rounding boundary tests ----


@pytest.mark.asyncio
async def test_bucket_sum_at_tolerance(scorer):
    """Sum within £0.01 tolerance should pass."""
    gt = {
        "input_data": {
            "payment": {
                "gross_amount": 100.00,
                "settlement_reference": "REF1",
                "splits": [
                    {"bucket": "a", "amount": 60.005, "destination_ref": "x"},
                    {"bucket": "b", "amount": 39.995, "destination_ref": "y"},
                ],
            },
            "bank_statement_slice": {"transactions": [{"reference": "REF1"}]},
            "event_log": [],
            "reconciliation_rules": {"bucket_rules": {}},
        },
        "expected_output": {"reconciliation_result": {"exceptions": []}},
    }
    score = await scorer.score("bucket_sum_matches_gross", gt, gt["input_data"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_bucket_sum_over_tolerance(scorer):
    """Sum exceeding £0.01 tolerance should fail."""
    gt = {
        "input_data": {
            "payment": {
                "gross_amount": 100.00,
                "settlement_reference": "REF1",
                "splits": [
                    {"bucket": "a", "amount": 60.02, "destination_ref": "x"},
                    {"bucket": "b", "amount": 40.00, "destination_ref": "y"},
                ],
            },
            "bank_statement_slice": {"transactions": [{"reference": "REF1"}]},
            "event_log": [],
            "reconciliation_rules": {"bucket_rules": {}},
        },
        "expected_output": {"reconciliation_result": {"exceptions": []}},
    }
    score = await scorer.score("bucket_sum_matches_gross", gt, gt["input_data"])
    assert score == 0.0
