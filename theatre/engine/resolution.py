"""Resolution State Machine — executes pre-committed oracle programme sequence.

Processes resolution steps in committed order with support for:
- construct_invocation: invoke via oracle contract
- deterministic_computation: execute without oracle
- hitl_rubric: produce PENDING_HITL status
- aggregation: combine previous step outputs
- Escalation paths on step failure
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from theatre.engine.models import AuditEvent
from theatre.engine.oracle_contract import (
    OracleAdapter,
    OracleInvocationRequest,
    OracleInvocationResponse,
    invoke_oracle,
)


class ResolutionStep(BaseModel):
    """A single step in the resolution programme."""

    step_id: str
    type: Literal[
        "construct_invocation",
        "deterministic_computation",
        "hitl_rubric",
        "aggregation",
    ]
    construct_id: str | None = None
    input_spec: dict[str, Any] = {}
    output_spec: dict[str, Any] = {}
    escalation_path: str | None = None  # step_id to jump to on failure
    timeout_seconds: int = 30


class StepOutcome(BaseModel):
    """Result of executing a single resolution step."""

    step_id: str
    status: Literal["SUCCESS", "FAILED", "PENDING_HITL", "ESCALATED"]
    output: dict[str, Any] | None = None
    error: str | None = None
    latency_ms: int = 0


class ResolutionResult(BaseModel):
    """Result of executing the full resolution programme."""

    outcomes: list[StepOutcome]
    audit_events: list[AuditEvent] = []
    final_status: Literal["COMPLETED", "FAILED", "PENDING_HITL"]


class ResolutionContext(BaseModel):
    """Execution context passed through the resolution pipeline."""

    theatre_id: str
    version_pins: dict[str, Any]
    step_outputs: dict[str, dict[str, Any]] = {}


class VersionPinError(Exception):
    """Raised when a construct lacks a version pin."""


class ResolutionStateMachine:
    """Executes pre-committed oracle programme sequence."""

    def __init__(
        self,
        steps: list[ResolutionStep],
        version_pins: dict[str, Any],
        oracle_adapter: OracleAdapter | None = None,
    ):
        self._steps = {s.step_id: s for s in steps}
        self._execution_order = [s.step_id for s in steps]
        self._version_pins = version_pins
        self._oracle = oracle_adapter

    async def execute(self, context: ResolutionContext) -> ResolutionResult:
        """Run each step in committed order. On failure, follow escalation_path if defined."""
        outcomes: list[StepOutcome] = []
        audit_events: list[AuditEvent] = []
        pending_hitl = False

        current_order = list(self._execution_order)
        i = 0

        while i < len(current_order):
            step_id = current_order[i]
            step = self._steps[step_id]

            # Execute step
            outcome = await self._execute_step(step, context)
            outcomes.append(outcome)

            audit_events.append(AuditEvent(
                event_type=f"resolution_step_{outcome.status.lower()}",
                detail={
                    "step_id": step_id,
                    "step_type": step.type,
                    "status": outcome.status,
                },
            ))

            if outcome.status == "PENDING_HITL":
                pending_hitl = True
                i += 1
                continue

            if outcome.status == "FAILED" and step.escalation_path:
                # Follow escalation path
                if step.escalation_path in self._steps:
                    outcomes.append(StepOutcome(
                        step_id=step_id,
                        status="ESCALATED",
                        error=f"Escalating to {step.escalation_path}",
                    ))
                    audit_events.append(AuditEvent(
                        event_type="resolution_escalation",
                        detail={
                            "from_step": step_id,
                            "to_step": step.escalation_path,
                        },
                    ))
                    # Jump to escalation step
                    try:
                        esc_idx = current_order.index(step.escalation_path)
                        i = esc_idx
                        continue
                    except ValueError:
                        # Escalation step not in remaining order — append it
                        current_order.append(step.escalation_path)
                        i = len(current_order) - 1
                        continue

            if outcome.status == "FAILED":
                # No escalation path — resolution fails
                return ResolutionResult(
                    outcomes=outcomes,
                    audit_events=audit_events,
                    final_status="FAILED",
                )

            # Store output for downstream steps
            if outcome.output:
                context.step_outputs[step_id] = outcome.output

            i += 1

        final_status: Literal["COMPLETED", "FAILED", "PENDING_HITL"] = (
            "PENDING_HITL" if pending_hitl else "COMPLETED"
        )

        return ResolutionResult(
            outcomes=outcomes,
            audit_events=audit_events,
            final_status=final_status,
        )

    async def _execute_step(
        self, step: ResolutionStep, context: ResolutionContext
    ) -> StepOutcome:
        """Execute a single resolution step."""
        if step.type == "construct_invocation":
            return await self._execute_construct(step, context)
        elif step.type == "deterministic_computation":
            return self._execute_deterministic(step, context)
        elif step.type == "hitl_rubric":
            return StepOutcome(
                step_id=step.step_id,
                status="PENDING_HITL",
                output={"rubric": step.input_spec},
            )
        elif step.type == "aggregation":
            return self._execute_aggregation(step, context)
        else:
            return StepOutcome(
                step_id=step.step_id,
                status="FAILED",
                error=f"Unknown step type: {step.type}",
            )

    async def _execute_construct(
        self, step: ResolutionStep, context: ResolutionContext
    ) -> StepOutcome:
        """Execute a construct invocation step."""
        if not step.construct_id:
            return StepOutcome(
                step_id=step.step_id,
                status="FAILED",
                error="construct_invocation step missing construct_id",
            )

        # Validate version pin exists
        constructs = self._version_pins.get("constructs", {})
        if step.construct_id not in constructs:
            raise VersionPinError(
                f"Construct '{step.construct_id}' has no version pin"
            )

        if not self._oracle:
            return StepOutcome(
                step_id=step.step_id,
                status="FAILED",
                error="No oracle adapter configured",
            )

        request = OracleInvocationRequest(
            theatre_id=context.theatre_id,
            episode_id=step.step_id,
            construct_id=step.construct_id,
            construct_version=constructs[step.construct_id],
            input_data=step.input_spec,
        )
        request.metadata.timeout_seconds = step.timeout_seconds

        response = await invoke_oracle(self._oracle, request)

        if response.status == "SUCCESS":
            return StepOutcome(
                step_id=step.step_id,
                status="SUCCESS",
                output=response.output_data,
                latency_ms=response.latency_ms,
            )
        else:
            return StepOutcome(
                step_id=step.step_id,
                status="FAILED",
                error=response.error_detail or f"Oracle returned {response.status}",
                latency_ms=response.latency_ms,
            )

    def _execute_deterministic(
        self, step: ResolutionStep, context: ResolutionContext
    ) -> StepOutcome:
        """Execute a deterministic computation step (no oracle needed)."""
        return StepOutcome(
            step_id=step.step_id,
            status="SUCCESS",
            output={"computed": True, **step.output_spec},
        )

    def _execute_aggregation(
        self, step: ResolutionStep, context: ResolutionContext
    ) -> StepOutcome:
        """Aggregate outputs from previous steps."""
        aggregated = dict(context.step_outputs)
        return StepOutcome(
            step_id=step.step_id,
            status="SUCCESS",
            output={"aggregated_steps": list(aggregated.keys()), **aggregated},
        )
