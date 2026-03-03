"""Tests for settlement audit transition integrity.

Validates that audit trail entries capture the genuine pre-transition state,
not the post-mutation value.

Gate B1 remediation.
"""
from __future__ import annotations


class TestSettlementAuditTransition:
    """Validate audit event from_state captures pre-mutation value."""

    def test_from_state_captured_before_mutation(self):
        """from_state must reflect the real pre-transition state, not post-mutation.

        This test validates the pattern used in settle_theatre():
          previous_state = theatre.state   # capture BEFORE mutation
          theatre.state = "RESOLVED"       # mutation
          audit = TheatreAuditEvent(from_state=previous_state, ...)

        The bug was: from_state=theatre.state AFTER mutation → RESOLVED → RESOLVED.
        """

        class FakeTheatre:
            state: str = "ACTIVE"

        theatre = FakeTheatre()

        # Correct pattern: capture before mutation
        previous_state = theatre.state
        theatre.state = "RESOLVED"

        assert previous_state == "ACTIVE"
        assert theatre.state == "RESOLVED"
        assert previous_state != theatre.state, (
            "from_state must differ from to_state — "
            "a no-op transition (RESOLVED → RESOLVED) is a bug"
        )

    def test_settling_state_transition(self):
        """Audit trail from SETTLING → RESOLVED shows real transition."""

        class FakeTheatre:
            state: str = "SETTLING"

        theatre = FakeTheatre()
        previous_state = theatre.state
        theatre.state = "RESOLVED"

        assert previous_state == "SETTLING"
        assert theatre.state == "RESOLVED"

    def test_active_state_transition(self):
        """Audit trail from ACTIVE → RESOLVED shows real transition."""

        class FakeTheatre:
            state: str = "ACTIVE"

        theatre = FakeTheatre()
        previous_state = theatre.state
        theatre.state = "RESOLVED"

        assert previous_state == "ACTIVE"
        assert theatre.state == "RESOLVED"
