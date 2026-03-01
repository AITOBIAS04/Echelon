"""Arrears Resolution Scorer — 6 binary checks for tenant arrears state machine.

Each check returns 1.0 (pass) or 0.0 (fail). Uses decimal.Decimal for
financial arithmetic with ROUND_HALF_UP rounding and £0.01 tolerance.

Criteria:
  state_transition_validity — every transition follows the 12-state machine
  ladder_redirection_arithmetic — ladder contribution correctly redirected
  reserve_fund_impact — reserve fund draws calculated correctly
  distribution_adjustment — investor distributions adjusted correctly
  grace_period_enforcement — no premature escalation during grace period
  ladder_balance_protection — accrued ladder equity never forcibly reduced
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

TOLERANCE = Decimal("0.01")

# 24 valid (from, to) state transitions from the ARREARS_RESOLUTION_V1 template.
VALID_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
    ("CURRENT", "GRACE_PERIOD"),
    ("GRACE_PERIOD", "CURRENT"),
    ("GRACE_PERIOD", "LATE"),
    ("GRACE_PERIOD", "PARTIAL_RECEIVED"),
    ("LATE", "CURRENT"),
    ("LATE", "PARTIAL_RECEIVED"),
    ("LATE", "ARREARS"),
    ("PARTIAL_RECEIVED", "CURRENT"),
    ("PARTIAL_RECEIVED", "ARREARS"),
    ("ARREARS", "LADDER_REDIRECTED"),
    ("ARREARS", "DISPUTE_RAISED"),
    ("ARREARS", "PAYMENT_PLAN"),
    ("ARREARS", "RECOVERY"),
    ("ARREARS", "CURRENT"),
    ("LADDER_REDIRECTED", "ARREARS"),
    ("LADDER_REDIRECTED", "CURRENT"),
    ("DISPUTE_RAISED", "ARREARS"),
    ("DISPUTE_RAISED", "RESOLVED"),
    ("PAYMENT_PLAN", "CURRENT"),
    ("PAYMENT_PLAN", "RECOVERY"),
    ("RECOVERY", "EVICTION_PROCESS"),
    ("RECOVERY", "CURRENT"),
    ("EVICTION_PROCESS", "LEASE_TERMINATED"),
    ("EVICTION_PROCESS", "CURRENT"),
})


class ArrearsScorer:
    """Deterministic scorer for arrears resolution theatres."""

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        inputs = ground_truth.get("input_data", {})
        expected = ground_truth.get("expected_output", {})

        checks = {
            "state_transition_validity": self._check_state_transition_validity,
            "ladder_redirection_arithmetic": self._check_ladder_redirection_arithmetic,
            "reserve_fund_impact": self._check_reserve_fund_impact,
            "distribution_adjustment": self._check_distribution_adjustment,
            "grace_period_enforcement": self._check_grace_period_enforcement,
            "ladder_balance_protection": self._check_ladder_balance_protection,
        }

        check_fn = checks.get(criteria_id)
        if check_fn is None:
            return 0.0

        return check_fn(inputs, expected)

    def _check_state_transition_validity(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify every state transition is in the allowed set."""
        verdict = expected.get("criteria_verdicts", {}).get(
            "state_transition_validity"
        )

        transitions = expected.get("state_transitions", [])

        # Structural check: every transition pair must be valid.
        for t in transitions:
            pair = (t.get("from", ""), t.get("to", ""))
            if pair not in VALID_TRANSITIONS:
                # Structural check found invalid transition.
                if verdict is True:
                    # Verdict disagrees — fixture corruption.
                    return 0.0
                return 0.0

        # All transitions valid structurally.
        if verdict is False:
            # Verdict says fail despite valid transitions — trust verdict.
            return 0.0

        return 1.0

    def _check_ladder_redirection_arithmetic(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify ladder contribution redirection arithmetic."""
        verdict = expected.get("criteria_verdicts", {}).get(
            "ladder_redirection_arithmetic"
        )

        ladder_action = expected.get("ladder_action", "")
        lease = inputs.get("lease_state", {})
        contribution = Decimal(str(lease.get("ladder_contribution", 0)))

        detail = expected.get("ladder_redirection_detail")
        if detail is not None:
            # Verify: applied_to_arrears + remainder_to_equity == total_contribution
            total = Decimal(str(detail.get("total_contribution", 0)))
            applied = Decimal(str(detail.get("applied_to_arrears", 0)))
            remainder = Decimal(str(detail.get("remainder_to_equity", 0)))

            if abs((applied + remainder) - total) > TOLERANCE:
                if verdict is True:
                    return 0.0
                return 0.0

        elif ladder_action == "normal_equity_purchase":
            # Equity purchased should equal the contribution.
            equity = Decimal(str(expected.get("ladder_equity_purchased", 0)))
            if abs(equity - contribution) > TOLERANCE:
                if verdict is True:
                    return 0.0
                return 0.0

        elif ladder_action in ("no_action_yet", "frozen_pending_dispute"):
            equity = Decimal(str(expected.get("ladder_equity_purchased", 0)))
            if equity != Decimal("0"):
                if verdict is True:
                    return 0.0
                return 0.0

        # Cross-check verdict.
        if verdict is False:
            return 0.0

        return 1.0

    def _check_reserve_fund_impact(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify reserve fund draw/contribution arithmetic."""
        verdict = expected.get("criteria_verdicts", {}).get("reserve_fund_impact")

        rfi = expected.get("reserve_fund_impact", {})
        drawdown = Decimal(str(rfi.get("drawdown_amount", 0)))
        breached = rfi.get("minimum_coverage_breached", False)

        if drawdown > 0:
            after = rfi.get("reserve_after_drawdown")
            if after is None:
                # Non-zero drawdown but no post-drawdown balance — issue.
                if verdict is True:
                    return 0.0
                return 0.0

        # Cross-check verdict.
        if verdict is False:
            return 0.0

        return 1.0

    def _check_distribution_adjustment(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify investor distribution adjustments."""
        verdict = expected.get("criteria_verdicts", {}).get(
            "distribution_adjustment"
        )

        dist_adj = expected.get("distribution_adjustment", "none")
        detail = expected.get("distribution_adjustment_detail")

        if detail is not None:
            # Verify arithmetic if detail present.
            original = Decimal(str(detail.get("original_distribution", 0)))
            adjusted = Decimal(str(detail.get("adjusted_distribution", 0)))
            reduction = Decimal(str(detail.get("reduction_amount", 0)))

            if abs((original - reduction) - adjusted) > TOLERANCE:
                if verdict is True:
                    return 0.0
                return 0.0

        # Cross-check verdict.
        if verdict is False:
            return 0.0

        return 1.0

    def _check_grace_period_enforcement(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify no escalation occurs before grace period expires."""
        verdict = expected.get("criteria_verdicts", {}).get(
            "grace_period_enforcement"
        )

        # Check for external actions during grace period.
        external_actions = inputs.get("external_actions_taken", [])
        prior_state = inputs.get("prior_state", "")

        if prior_state == "GRACE_PERIOD" and external_actions:
            # Escalation during grace period — structural fail.
            if verdict is True:
                return 0.0
            return 0.0

        # Cross-check verdict.
        if verdict is False:
            return 0.0

        return 1.0

    def _check_ladder_balance_protection(
        self, inputs: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        """Verify accrued ladder balance is never forcibly reduced."""
        verdict = expected.get("criteria_verdicts", {}).get(
            "ladder_balance_protection"
        )

        protected = expected.get("ladder_balance_protected", True)

        input_balance = Decimal(
            str(inputs.get("lease_state", {}).get("accrued_ladder_balance", 0))
        )
        output_balance = Decimal(
            str(expected.get("accrued_ladder_balance", 0))
        )

        # Balance should never be *forcibly* reduced.  A legitimate
        # disposition (e.g. NAV redemption on lease termination) can take
        # the balance to 0 while `ladder_balance_protected` remains True.
        if output_balance < input_balance and not protected:
            if verdict is True:
                return 0.0
            return 0.0

        if not protected:
            if verdict is True:
                return 0.0
            return 0.0

        # Cross-check verdict.
        if verdict is False:
            return 0.0

        return 1.0
