"""Theatre lifecycle state machine.

Six irreversible states: DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED.
"""

from __future__ import annotations

import enum


class TheatreState(str, enum.Enum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    ACTIVE = "ACTIVE"
    SETTLING = "SETTLING"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"


VALID_TRANSITIONS: dict[TheatreState, list[TheatreState]] = {
    TheatreState.DRAFT: [TheatreState.COMMITTED],
    TheatreState.COMMITTED: [TheatreState.ACTIVE],
    TheatreState.ACTIVE: [TheatreState.SETTLING],
    TheatreState.SETTLING: [TheatreState.RESOLVED],
    TheatreState.RESOLVED: [TheatreState.ARCHIVED],
    TheatreState.ARCHIVED: [],
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class TheatreStateMachine:
    """Enforces irreversible Theatre lifecycle transitions."""

    def __init__(self, theatre_id: str, state: TheatreState = TheatreState.DRAFT):
        self._theatre_id = theatre_id
        self._state = state

    @property
    def theatre_id(self) -> str:
        return self._theatre_id

    @property
    def state(self) -> TheatreState:
        return self._state

    def transition(self, target: TheatreState) -> TheatreState:
        """Advance to target state. Raises InvalidTransitionError if not allowed."""
        if target not in VALID_TRANSITIONS[self._state]:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state.value} to {target.value} "
                f"for theatre {self._theatre_id}"
            )
        self._state = target
        return self._state

    def can_transition(self, target: TheatreState) -> bool:
        """Check if transition to target is valid from current state."""
        return target in VALID_TRANSITIONS[self._state]
