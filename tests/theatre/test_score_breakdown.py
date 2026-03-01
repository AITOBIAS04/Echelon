"""Regression tests for sprint-11 score breakdown artefacts.

Validates that breakdown JSONs have correct structure and that
composite scores equal the sum of weighted contributions under
Decimal arithmetic.
"""

import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = _ROOT / "reports"


def _load_breakdown(name: str) -> dict:
    path = REPORTS_DIR / name
    assert path.exists(), f"Missing breakdown file: {path}"
    return json.loads(path.read_text())


REQUIRED_KEYS = {
    "template",
    "composite_score",
    "target_score",
    "delta",
    "record_count",
    "criteria",
    "composite_check",
    "root_cause",
    "coupled_criterion",
    "coupling_detail",
}

REQUIRED_CRITERION_KEYS = {"weight", "pass", "total", "pass_rate", "contribution"}


# --- Structure tests ---


def test_escrow_breakdown_structure():
    """Escrow breakdown JSON has all required keys and criterion fields."""
    data = _load_breakdown("escrow_score_breakdown.json")
    missing = REQUIRED_KEYS - set(data.keys())
    assert not missing, f"Missing top-level keys: {missing}"

    assert len(data["criteria"]) > 0, "No criteria in breakdown"
    for cid, cdata in data["criteria"].items():
        cmissing = REQUIRED_CRITERION_KEYS - set(cdata.keys())
        assert not cmissing, f"Criterion {cid} missing keys: {cmissing}"


def test_reconciliation_breakdown_structure():
    """Reconciliation breakdown JSON has all required keys and criterion fields."""
    data = _load_breakdown("reconciliation_score_breakdown.json")
    missing = REQUIRED_KEYS - set(data.keys())
    assert not missing, f"Missing top-level keys: {missing}"

    assert len(data["criteria"]) > 0, "No criteria in breakdown"
    for cid, cdata in data["criteria"].items():
        cmissing = REQUIRED_CRITERION_KEYS - set(cdata.keys())
        assert not cmissing, f"Criterion {cid} missing keys: {cmissing}"


# --- Arithmetic invariant tests ---


TOLERANCE = Decimal("0.0001")


@pytest.mark.parametrize("filename", [
    "escrow_score_breakdown.json",
    "reconciliation_score_breakdown.json",
])
def test_composite_equals_sum_of_contributions(filename):
    """sum(criterion.contribution) == composite_score under Decimal arithmetic."""
    data = _load_breakdown(filename)
    composite = Decimal(str(data["composite_score"]))

    total = Decimal("0")
    for cdata in data["criteria"].values():
        total += Decimal(str(cdata["contribution"]))

    assert abs(total - composite) <= TOLERANCE, (
        f"Composite mismatch: sum={total} vs composite={composite} "
        f"(delta={abs(total - composite)})"
    )


@pytest.mark.parametrize("filename", [
    "escrow_score_breakdown.json",
    "reconciliation_score_breakdown.json",
])
def test_contribution_equals_weight_times_pass_rate(filename):
    """For each criterion: contribution == weight * (pass / total)."""
    data = _load_breakdown(filename)

    for cid, cdata in data["criteria"].items():
        weight = Decimal(str(cdata["weight"]))
        pass_count = Decimal(str(cdata["pass"]))
        total_count = Decimal(str(cdata["total"]))
        contribution = Decimal(str(cdata["contribution"]))

        expected = (weight * pass_count / total_count).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        actual = contribution.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        assert abs(expected - actual) <= TOLERANCE, (
            f"{cid}: expected contribution={expected}, got={actual}"
        )


@pytest.mark.parametrize("filename", [
    "escrow_score_breakdown.json",
    "reconciliation_score_breakdown.json",
])
def test_all_weights_sum_to_one(filename):
    """All criterion weights sum to 1.0."""
    data = _load_breakdown(filename)

    total_weight = Decimal("0")
    for cdata in data["criteria"].values():
        total_weight += Decimal(str(cdata["weight"]))

    assert abs(total_weight - Decimal("1.0")) <= TOLERANCE, (
        f"Weights sum to {total_weight}, expected 1.0"
    )
