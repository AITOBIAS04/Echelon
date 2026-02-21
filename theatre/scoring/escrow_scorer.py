"""Escrow Milestone Release Scorer — 5 binary checks for escrow verification.

Each check returns 1.0 (pass) or 0.0 (fail). Uses decimal.Decimal for
financial arithmetic with ROUND_HALF_UP rounding and £0.01 tolerance.
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

TOLERANCE = Decimal("0.01")


class EscrowScorer:
    """Deterministic scorer for escrow milestone release theatres."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        inputs = ground_truth.get("input_data", {})
        expected = ground_truth.get("expected_output", {})

        checks = {
            "required_evidence_present": self._check_required_evidence_present,
            "signature_policy_satisfied": self._check_signature_policy_satisfied,
            "validity_window_respected": self._check_validity_window_respected,
            "release_amount_correct": self._check_release_amount_correct,
            "idempotency": self._check_idempotency,
        }

        check_fn = checks.get(criteria_id)
        if check_fn is None:
            return 0.0

        return check_fn(inputs, expected)

    def _check_required_evidence_present(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify all required evidence types are present in the bundle."""
        schedule = inputs.get("milestone_schedule", {})
        bundle = inputs.get("evidence_bundle", {})

        milestones = schedule.get("milestones", [])
        if not milestones:
            return 0.0

        milestone = milestones[0]
        required_types = set(milestone.get("evidence_required", []))
        documents = bundle.get("documents", [])
        provided_types = {doc.get("doc_type") for doc in documents}

        if required_types <= provided_types:
            return 1.0
        return 0.0

    def _check_signature_policy_satisfied(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify all required signer roles have attestations."""
        schedule = inputs.get("milestone_schedule", {})
        bundle = inputs.get("evidence_bundle", {})

        milestones = schedule.get("milestones", [])
        if not milestones:
            return 0.0

        milestone = milestones[0]
        required_roles = set(milestone.get("required_signer_roles", []))
        attestations = bundle.get("attestations", [])
        attestation_roles = {att.get("role") for att in attestations}

        if required_roles <= attestation_roles:
            return 1.0
        return 0.0

    def _check_validity_window_respected(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify evidence timestamp is parseable ISO-8601 (v0.1: always passes if present)."""
        bundle = inputs.get("evidence_bundle", {})
        timestamp_str = bundle.get("evidence_timestamp")

        if not timestamp_str:
            return 0.0

        try:
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return 1.0
        except (ValueError, AttributeError):
            return 0.0

    def _check_release_amount_correct(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify release_pct * balance == expected release_amount."""
        escrow = inputs.get("escrow_state", {})
        schedule = inputs.get("milestone_schedule", {})
        release = expected.get("release_instruction", {})

        balance = Decimal(str(escrow.get("balance", 0)))

        milestones = schedule.get("milestones", [])
        if not milestones:
            return 0.0

        release_pct = Decimal(str(milestones[0].get("release_pct", 0)))
        expected_amount = Decimal(str(release.get("release_amount", 0)))

        computed = (release_pct * balance).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if abs(computed - expected_amount) > TOLERANCE:
            return 0.0
        return 1.0

    def _check_idempotency(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify milestone ID appears exactly once in the schedule."""
        schedule = inputs.get("milestone_schedule", {})
        release = expected.get("release_instruction", {})

        milestones = schedule.get("milestones", [])
        target_id = release.get("milestone_id")

        if not target_id:
            return 0.0

        count = sum(
            1 for m in milestones if m.get("milestone_id") == target_id
        )

        return 1.0 if count == 1 else 0.0
