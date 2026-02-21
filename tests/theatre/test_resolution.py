"""Tests for Resolution State Machine — linear execution, escalation, HITL."""

import pytest

from theatre.engine.oracle_contract import MockOracleAdapter
from theatre.engine.resolution import (
    ResolutionContext,
    ResolutionResult,
    ResolutionStateMachine,
    ResolutionStep,
    StepOutcome,
    VersionPinError,
)


def _make_context(**overrides) -> ResolutionContext:
    defaults = {
        "theatre_id": "test-theatre",
        "version_pins": {
            "constructs": {"observer": "abc123", "scorer": "def456"},
        },
    }
    defaults.update(overrides)
    return ResolutionContext(**defaults)


class TestLinearExecution:
    @pytest.mark.asyncio
    async def test_single_deterministic_step(self):
        steps = [
            ResolutionStep(step_id="s1", type="deterministic_computation"),
        ]
        sm = ResolutionStateMachine(steps, {"constructs": {}})
        result = await sm.execute(_make_context())

        assert result.final_status == "COMPLETED"
        assert len(result.outcomes) == 1
        assert result.outcomes[0].status == "SUCCESS"

    @pytest.mark.asyncio
    async def test_multiple_deterministic_steps(self):
        steps = [
            ResolutionStep(step_id="s1", type="deterministic_computation"),
            ResolutionStep(step_id="s2", type="deterministic_computation"),
            ResolutionStep(step_id="s3", type="aggregation"),
        ]
        sm = ResolutionStateMachine(steps, {"constructs": {}})
        result = await sm.execute(_make_context())

        assert result.final_status == "COMPLETED"
        assert len(result.outcomes) == 3

    @pytest.mark.asyncio
    async def test_construct_invocation_success(self):
        steps = [
            ResolutionStep(
                step_id="invoke_obs",
                type="construct_invocation",
                construct_id="observer",
            ),
        ]
        adapter = MockOracleAdapter(default_response={"prediction": 0.8})
        sm = ResolutionStateMachine(
            steps,
            {"constructs": {"observer": "abc123"}},
            oracle_adapter=adapter,
        )
        result = await sm.execute(_make_context())

        assert result.final_status == "COMPLETED"
        assert result.outcomes[0].status == "SUCCESS"
        assert result.outcomes[0].output == {"prediction": 0.8}


class TestConstructValidation:
    @pytest.mark.asyncio
    async def test_missing_version_pin_raises(self):
        steps = [
            ResolutionStep(
                step_id="invoke_missing",
                type="construct_invocation",
                construct_id="nonexistent",
            ),
        ]
        adapter = MockOracleAdapter()
        sm = ResolutionStateMachine(
            steps,
            {"constructs": {"observer": "abc123"}},
            oracle_adapter=adapter,
        )
        with pytest.raises(VersionPinError, match="nonexistent"):
            await sm.execute(_make_context())

    @pytest.mark.asyncio
    async def test_missing_construct_id_fails(self):
        steps = [
            ResolutionStep(
                step_id="invoke_no_id",
                type="construct_invocation",
                # construct_id intentionally omitted
            ),
        ]
        adapter = MockOracleAdapter()
        sm = ResolutionStateMachine(
            steps, {"constructs": {}}, oracle_adapter=adapter,
        )
        result = await sm.execute(_make_context())
        assert result.final_status == "FAILED"
        assert "missing construct_id" in result.outcomes[0].error

    @pytest.mark.asyncio
    async def test_no_oracle_adapter_fails(self):
        steps = [
            ResolutionStep(
                step_id="invoke_obs",
                type="construct_invocation",
                construct_id="observer",
            ),
        ]
        sm = ResolutionStateMachine(
            steps, {"constructs": {"observer": "abc123"}},
            # No oracle adapter
        )
        result = await sm.execute(_make_context())
        assert result.final_status == "FAILED"
        assert "No oracle adapter" in result.outcomes[0].error


class TestEscalation:
    @pytest.mark.asyncio
    async def test_escalation_on_failure(self):
        steps = [
            ResolutionStep(
                step_id="primary",
                type="construct_invocation",
                construct_id="observer",
                escalation_path="fallback",
            ),
            ResolutionStep(
                step_id="fallback",
                type="deterministic_computation",
            ),
        ]
        # Primary fails
        adapter = MockOracleAdapter(fail_episodes={"primary"})
        sm = ResolutionStateMachine(
            steps,
            {"constructs": {"observer": "abc123"}},
            oracle_adapter=adapter,
        )
        result = await sm.execute(_make_context())

        # Should escalate to fallback and complete
        statuses = [o.status for o in result.outcomes]
        assert "ESCALATED" in statuses
        assert result.final_status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_failure_without_escalation_terminates(self):
        steps = [
            ResolutionStep(
                step_id="only_step",
                type="construct_invocation",
                construct_id="observer",
                # No escalation_path
            ),
        ]
        adapter = MockOracleAdapter(fail_episodes={"only_step"})
        sm = ResolutionStateMachine(
            steps,
            {"constructs": {"observer": "abc123"}},
            oracle_adapter=adapter,
        )
        result = await sm.execute(_make_context())
        assert result.final_status == "FAILED"


class TestHitlSteps:
    @pytest.mark.asyncio
    async def test_hitl_produces_pending_status(self):
        steps = [
            ResolutionStep(step_id="hitl_taste", type="hitl_rubric"),
        ]
        sm = ResolutionStateMachine(steps, {"constructs": {}})
        result = await sm.execute(_make_context())

        assert result.final_status == "PENDING_HITL"
        assert result.outcomes[0].status == "PENDING_HITL"

    @pytest.mark.asyncio
    async def test_hitl_mixed_with_normal_steps(self):
        steps = [
            ResolutionStep(step_id="s1", type="deterministic_computation"),
            ResolutionStep(step_id="hitl_review", type="hitl_rubric"),
            ResolutionStep(step_id="s3", type="aggregation"),
        ]
        sm = ResolutionStateMachine(steps, {"constructs": {}})
        result = await sm.execute(_make_context())

        # Should still complete all steps, but with PENDING_HITL final status
        assert result.final_status == "PENDING_HITL"
        assert len(result.outcomes) == 3


class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_audit_events_generated(self):
        steps = [
            ResolutionStep(step_id="s1", type="deterministic_computation"),
            ResolutionStep(step_id="s2", type="aggregation"),
        ]
        sm = ResolutionStateMachine(steps, {"constructs": {}})
        result = await sm.execute(_make_context())

        assert len(result.audit_events) == 2
        assert all(
            e.event_type.startswith("resolution_step_")
            for e in result.audit_events
        )
