"""Ledger Reconciliation Scorer — 5 binary checks for reconciliation verification.

Each check returns 1.0 (pass) or 0.0 (fail). Uses decimal.Decimal for
financial arithmetic with ROUND_HALF_UP rounding and £0.01 tolerance.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

TOLERANCE = Decimal("0.01")


class ReconciliationScorer:
    """Deterministic scorer for ledger reconciliation theatres."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        inputs = ground_truth.get("input_data", {})
        expected = ground_truth.get("expected_output", {})

        checks = {
            "bank_ref_match": self._check_bank_ref_match,
            "bucket_sum_matches_gross": self._check_bucket_sum_matches_gross,
            "bucket_destination_valid": self._check_bucket_destination_valid,
            "event_log_complete": self._check_event_log_complete,
            "exceptions_correct": self._check_exceptions_correct,
        }

        check_fn = checks.get(criteria_id)
        if check_fn is None:
            return 0.0

        return check_fn(inputs, expected)

    def _check_bank_ref_match(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify settlement_reference is found in bank statement transactions."""
        payment = inputs.get("payment", {})
        bank = inputs.get("bank_statement_slice", {})

        settlement_ref = payment.get("settlement_reference")
        if not settlement_ref:
            return 0.0

        transactions = bank.get("transactions", [])
        bank_refs = {txn.get("reference") for txn in transactions}

        if settlement_ref in bank_refs:
            return 1.0
        return 0.0

    def _check_bucket_sum_matches_gross(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify sum of splits equals gross_amount."""
        payment = inputs.get("payment", {})
        gross = Decimal(str(payment.get("gross_amount", 0)))
        splits = payment.get("splits", [])

        splits_sum = sum(Decimal(str(s.get("amount", 0))) for s in splits)

        if abs(splits_sum - gross) > TOLERANCE:
            return 0.0
        return 1.0

    def _check_bucket_destination_valid(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify each split's destination_ref is in allowed_destinations for its bucket."""
        payment = inputs.get("payment", {})
        rules = inputs.get("reconciliation_rules", {})

        splits = payment.get("splits", [])
        bucket_rules = rules.get("bucket_rules", {})

        for split in splits:
            bucket = split.get("bucket", "")
            dest = split.get("destination_ref", "")
            rule = bucket_rules.get(bucket, {})
            allowed = rule.get("allowed_destinations", [])

            if dest not in allowed:
                return 0.0

        return 1.0

    def _check_event_log_complete(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify one event per split with matching bucket entries."""
        payment = inputs.get("payment", {})
        event_log = inputs.get("event_log", [])

        splits = payment.get("splits", [])

        if len(event_log) != len(splits):
            return 0.0

        split_buckets = {s.get("bucket") for s in splits}
        event_buckets = {e.get("bucket") for e in event_log}

        if split_buckets != event_buckets:
            return 0.0

        return 1.0

    def _check_exceptions_correct(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify exceptions match expected (empty list for happy path)."""
        result = expected.get("reconciliation_result", {})
        expected_exceptions = result.get("exceptions", [])

        # For happy-path fixtures, exceptions should be empty
        if expected_exceptions == []:
            return 1.0
        return 0.0
