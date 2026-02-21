"""Distribution Waterfall Scorer — 5 binary checks for waterfall arithmetic.

Each check returns 1.0 (pass) or 0.0 (fail). Uses decimal.Decimal for
financial arithmetic with ROUND_HALF_UP rounding and £0.01 tolerance.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

TOLERANCE = Decimal("0.01")


class WaterfallScorer:
    """Deterministic scorer for distribution waterfall theatres."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        inputs = ground_truth.get("input_data", {})
        expected = ground_truth.get("expected_output", {})

        checks = {
            "waterfall_arithmetic": self._check_waterfall_arithmetic,
            "noi_pool_conservation": self._check_noi_pool_conservation,
            "rounding_policy_compliance": self._check_rounding_policy_compliance,
            "cap_table_consistency": self._check_cap_table_consistency,
            "ledger_reconciliation": self._check_ledger_reconciliation,
        }

        check_fn = checks.get(criteria_id)
        if check_fn is None:
            return 0.0

        return check_fn(inputs, expected)

    def _check_waterfall_arithmetic(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify split amounts sum to gross and match expected values."""
        payment = inputs.get("payment", {})
        statement = expected.get("distribution_statement", {})

        gross = Decimal(str(payment.get("gross_amount", 0)))
        splits = payment.get("splits", [])
        splits_sum = sum(Decimal(str(s.get("amount", 0))) for s in splits)

        # Splits must sum to gross
        if abs(splits_sum - gross) > TOLERANCE:
            return 0.0

        # Each split must match expected
        expected_sum = Decimal(str(statement.get("splits_sum", 0)))
        if abs(splits_sum - expected_sum) > TOLERANCE:
            return 0.0

        for split in splits:
            bucket = split.get("bucket", "")
            amount = Decimal(str(split.get("amount", 0)))
            expected_amount = Decimal(str(statement.get(bucket, 0)))
            if abs(amount - expected_amount) > TOLERANCE:
                return 0.0

        return 1.0

    def _check_noi_pool_conservation(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify NOI allocations sum to the NOI pool amount."""
        noi_report = inputs.get("noi_report", {})
        noi_pool = Decimal(str(noi_report.get("noi_pool", 0)))
        allocations = noi_report.get("allocations", [])

        alloc_sum = sum(Decimal(str(a.get("amount", 0))) for a in allocations)

        if abs(alloc_sum - noi_pool) > TOLERANCE:
            return 0.0

        return 1.0

    # Fields that are rates (not monetary amounts) — exempt from 2dp rounding
    _RATE_FIELDS = {"distribution_per_token"}

    def _check_rounding_policy_compliance(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify all monetary amounts use consistent rounding (ROUND_HALF_UP, 2dp)."""
        statement = expected.get("distribution_statement", {})

        for key, value in statement.items():
            if not isinstance(value, (int, float)):
                continue
            if key in self._RATE_FIELDS:
                continue
            d = Decimal(str(value))
            rounded = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if d != rounded:
                return 0.0

        return 1.0

    def _check_cap_table_consistency(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify per_token * supply matches distributions within tolerance."""
        cap_table = inputs.get("cap_table_snapshot", {})
        statement = expected.get("distribution_statement", {})

        per_token = Decimal(str(cap_table.get("distribution_per_token", 0)))
        supply = Decimal(str(cap_table.get("token_supply", 0)))
        distributions = Decimal(str(statement.get("distributions", 0)))

        computed = per_token * supply
        if abs(computed - distributions) > TOLERANCE:
            return 0.0

        return 1.0

    def _check_ledger_reconciliation(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify sum of payment splits equals gross_amount."""
        payment = inputs.get("payment", {})
        gross = Decimal(str(payment.get("gross_amount", 0)))
        splits = payment.get("splits", [])

        splits_sum = sum(Decimal(str(s.get("amount", 0))) for s in splits)

        if abs(splits_sum - gross) > TOLERANCE:
            return 0.0

        return 1.0
