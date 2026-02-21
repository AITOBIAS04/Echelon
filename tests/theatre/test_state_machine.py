"""Tests for Theatre state machine — all valid and invalid transitions."""

import pytest

from theatre.engine.state_machine import (
    TheatreState,
    TheatreStateMachine,
    InvalidTransitionError,
    VALID_TRANSITIONS,
)


class TestTheatreState:
    def test_enum_values(self):
        assert TheatreState.DRAFT.value == "DRAFT"
        assert TheatreState.COMMITTED.value == "COMMITTED"
        assert TheatreState.ACTIVE.value == "ACTIVE"
        assert TheatreState.SETTLING.value == "SETTLING"
        assert TheatreState.RESOLVED.value == "RESOLVED"
        assert TheatreState.ARCHIVED.value == "ARCHIVED"

    def test_six_states(self):
        assert len(TheatreState) == 6


class TestValidTransitions:
    def test_five_valid_forward_transitions(self):
        assert VALID_TRANSITIONS[TheatreState.DRAFT] == [TheatreState.COMMITTED]
        assert VALID_TRANSITIONS[TheatreState.COMMITTED] == [TheatreState.ACTIVE]
        assert VALID_TRANSITIONS[TheatreState.ACTIVE] == [TheatreState.SETTLING]
        assert VALID_TRANSITIONS[TheatreState.SETTLING] == [TheatreState.RESOLVED]
        assert VALID_TRANSITIONS[TheatreState.RESOLVED] == [TheatreState.ARCHIVED]

    def test_archived_is_terminal(self):
        assert VALID_TRANSITIONS[TheatreState.ARCHIVED] == []


class TestTheatreStateMachine:
    def test_initial_state(self):
        sm = TheatreStateMachine("test-1")
        assert sm.state == TheatreState.DRAFT
        assert sm.theatre_id == "test-1"

    def test_custom_initial_state(self):
        sm = TheatreStateMachine("test-1", TheatreState.COMMITTED)
        assert sm.state == TheatreState.COMMITTED

    def test_full_lifecycle(self):
        sm = TheatreStateMachine("test-1")
        assert sm.transition(TheatreState.COMMITTED) == TheatreState.COMMITTED
        assert sm.transition(TheatreState.ACTIVE) == TheatreState.ACTIVE
        assert sm.transition(TheatreState.SETTLING) == TheatreState.SETTLING
        assert sm.transition(TheatreState.RESOLVED) == TheatreState.RESOLVED
        assert sm.transition(TheatreState.ARCHIVED) == TheatreState.ARCHIVED

    def test_can_transition_valid(self):
        sm = TheatreStateMachine("test-1")
        assert sm.can_transition(TheatreState.COMMITTED) is True

    def test_can_transition_invalid(self):
        sm = TheatreStateMachine("test-1")
        assert sm.can_transition(TheatreState.ACTIVE) is False

    def test_archived_cannot_transition(self):
        sm = TheatreStateMachine("test-1", TheatreState.ARCHIVED)
        for state in TheatreState:
            assert sm.can_transition(state) is False

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Backward transitions (never allowed)
            (TheatreState.COMMITTED, TheatreState.DRAFT),
            (TheatreState.ACTIVE, TheatreState.DRAFT),
            (TheatreState.ACTIVE, TheatreState.COMMITTED),
            (TheatreState.SETTLING, TheatreState.DRAFT),
            (TheatreState.SETTLING, TheatreState.COMMITTED),
            (TheatreState.SETTLING, TheatreState.ACTIVE),
            (TheatreState.RESOLVED, TheatreState.DRAFT),
            (TheatreState.RESOLVED, TheatreState.COMMITTED),
            (TheatreState.RESOLVED, TheatreState.ACTIVE),
            (TheatreState.RESOLVED, TheatreState.SETTLING),
            (TheatreState.ARCHIVED, TheatreState.DRAFT),
            (TheatreState.ARCHIVED, TheatreState.COMMITTED),
            (TheatreState.ARCHIVED, TheatreState.ACTIVE),
            (TheatreState.ARCHIVED, TheatreState.SETTLING),
            (TheatreState.ARCHIVED, TheatreState.RESOLVED),
            # Skip-ahead transitions (never allowed)
            (TheatreState.DRAFT, TheatreState.ACTIVE),
            (TheatreState.DRAFT, TheatreState.SETTLING),
            (TheatreState.DRAFT, TheatreState.RESOLVED),
            (TheatreState.DRAFT, TheatreState.ARCHIVED),
            (TheatreState.COMMITTED, TheatreState.SETTLING),
            (TheatreState.COMMITTED, TheatreState.RESOLVED),
            (TheatreState.COMMITTED, TheatreState.ARCHIVED),
            (TheatreState.ACTIVE, TheatreState.RESOLVED),
            (TheatreState.ACTIVE, TheatreState.ARCHIVED),
            (TheatreState.SETTLING, TheatreState.ARCHIVED),
            # Self-transitions (never allowed)
            (TheatreState.DRAFT, TheatreState.DRAFT),
            (TheatreState.COMMITTED, TheatreState.COMMITTED),
            (TheatreState.ACTIVE, TheatreState.ACTIVE),
            (TheatreState.SETTLING, TheatreState.SETTLING),
            (TheatreState.RESOLVED, TheatreState.RESOLVED),
            (TheatreState.ARCHIVED, TheatreState.ARCHIVED),
        ],
    )
    def test_invalid_transition(self, from_state, to_state):
        sm = TheatreStateMachine("test-1", from_state)
        with pytest.raises(InvalidTransitionError):
            sm.transition(to_state)

    def test_error_message_includes_states(self):
        sm = TheatreStateMachine("test-1", TheatreState.DRAFT)
        with pytest.raises(InvalidTransitionError, match="DRAFT.*ACTIVE"):
            sm.transition(TheatreState.ACTIVE)

    def test_error_message_includes_theatre_id(self):
        sm = TheatreStateMachine("my-theatre", TheatreState.DRAFT)
        with pytest.raises(InvalidTransitionError, match="my-theatre"):
            sm.transition(TheatreState.ARCHIVED)
