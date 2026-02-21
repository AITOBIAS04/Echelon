"""Unit tests for EscrowScorer — 5 binary checks for escrow milestone release."""

import asyncio
import copy
import json
from pathlib import Path

import pytest

from theatre.scoring.escrow_scorer import EscrowScorer

FIXTURE_PATH = Path(__file__).resolve().parents[2] / (
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/escrow_fixtures_10.json"
)


@pytest.fixture
def scorer():
    return EscrowScorer()


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
    "required_evidence_present",
    "signature_policy_satisfied",
    "validity_window_respected",
    "release_amount_correct",
    "idempotency",
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


# ---- Per-check failure: required_evidence_present ----


@pytest.mark.asyncio
async def test_required_evidence_missing_doc(scorer, fixture_data):
    """Removing a required document should fail the evidence check."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["evidence_bundle"]["documents"] = [
        {"doc_type": "qs_report", "doc_hash": "abc"}
    ]
    gt = _make_gt(record)
    score = await scorer.score("required_evidence_present", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_required_evidence_extra_doc_passes(scorer, fixture_data):
    """Extra documents beyond required should still pass."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["evidence_bundle"]["documents"].append(
        {"doc_type": "extra_doc", "doc_hash": "xyz"}
    )
    gt = _make_gt(record)
    score = await scorer.score("required_evidence_present", gt, gt["input_data"])
    assert score == 1.0


# ---- Per-check failure: signature_policy_satisfied ----


@pytest.mark.asyncio
async def test_signature_policy_missing_role(scorer, fixture_data):
    """Missing a required signer role should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["evidence_bundle"]["attestations"] = [
        {"role": "quantity_surveyor", "signer_id": "qs_001", "signature": "abc"},
    ]
    gt = _make_gt(record)
    score = await scorer.score("signature_policy_satisfied", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: validity_window_respected ----


@pytest.mark.asyncio
async def test_validity_window_no_timestamp(scorer, fixture_data):
    """Missing evidence_timestamp should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    del record["inputs"]["evidence_bundle"]["evidence_timestamp"]
    gt = _make_gt(record)
    score = await scorer.score("validity_window_respected", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_validity_window_bad_timestamp(scorer, fixture_data):
    """Unparseable timestamp should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["evidence_bundle"]["evidence_timestamp"] = "not-a-date"
    gt = _make_gt(record)
    score = await scorer.score("validity_window_respected", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: release_amount_correct ----


@pytest.mark.asyncio
async def test_release_amount_wrong_balance(scorer, fixture_data):
    """Wrong escrow balance should make release amount incorrect."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["escrow_state"]["balance"] = 50000.0
    gt = _make_gt(record)
    score = await scorer.score("release_amount_correct", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_release_amount_wrong_pct(scorer, fixture_data):
    """Wrong release percentage should fail."""
    record = copy.deepcopy(fixture_data["records"][0])
    record["inputs"]["milestone_schedule"]["milestones"][0]["release_pct"] = 0.5
    gt = _make_gt(record)
    score = await scorer.score("release_amount_correct", gt, gt["input_data"])
    assert score == 0.0


# ---- Per-check failure: idempotency ----


@pytest.mark.asyncio
async def test_idempotency_duplicate_milestone(scorer, fixture_data):
    """Duplicate milestone_id in schedule should fail idempotency."""
    record = copy.deepcopy(fixture_data["records"][0])
    milestone = record["inputs"]["milestone_schedule"]["milestones"][0]
    record["inputs"]["milestone_schedule"]["milestones"].append(
        copy.deepcopy(milestone)
    )
    gt = _make_gt(record)
    score = await scorer.score("idempotency", gt, gt["input_data"])
    assert score == 0.0


@pytest.mark.asyncio
async def test_idempotency_no_matching_milestone(scorer):
    """Milestone ID not found in schedule should fail."""
    gt = {
        "input_data": {
            "milestone_schedule": {
                "milestones": [{"milestone_id": "ms_other"}]
            },
            "evidence_bundle": {},
            "escrow_state": {},
        },
        "expected_output": {
            "release_instruction": {"milestone_id": "ms_unknown"}
        },
    }
    score = await EscrowScorer().score("idempotency", gt, gt["input_data"])
    assert score == 0.0


# ---- Rounding boundary tests ----


@pytest.mark.asyncio
async def test_release_amount_at_tolerance_boundary(scorer):
    """Release amount at exactly £0.01 tolerance should pass."""
    gt = {
        "input_data": {
            "escrow_state": {"balance": 99999.0},
            "milestone_schedule": {
                "milestones": [{"milestone_id": "ms_1", "release_pct": 0.1}],
            },
            "evidence_bundle": {},
        },
        "expected_output": {
            "release_instruction": {
                "release_amount": 9999.90,
                "milestone_id": "ms_1",
            }
        },
    }
    score = await scorer.score("release_amount_correct", gt, gt["input_data"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_release_amount_over_tolerance(scorer):
    """Release amount exceeding tolerance should fail."""
    gt = {
        "input_data": {
            "escrow_state": {"balance": 100000.0},
            "milestone_schedule": {
                "milestones": [{"milestone_id": "ms_1", "release_pct": 0.1}],
            },
            "evidence_bundle": {},
        },
        "expected_output": {
            "release_instruction": {
                "release_amount": 10001.0,
                "milestone_id": "ms_1",
            }
        },
    }
    score = await scorer.score("release_amount_correct", gt, gt["input_data"])
    assert score == 0.0
