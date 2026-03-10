"""
Checkpoint Evaluator v2 — Primitive-driven checkpoint resolution.

Processes checkpoints in sequence_num order. At each checkpoint:
1. Evaluate trigger_condition_json (field/operator/threshold) to gate activation
2. Dispatch to primitive evaluator based on evaluator_type + branch_rule_json
3. Compute reward from reward_mapping_json + objective vector weights
4. Evaluate theatre_spawn_rule_json for derived theatre spawning
5. Create RunCheckpointResult with full state vector
6. Advance to next checkpoint via branch.next_checkpoint_id

Trigger gating: trigger_condition_json supports field/operator/threshold evaluation
against run state_vector. Templates without field/operator/threshold activate
unconditionally (backward compatible). Unsupported operators fail at runtime.

REPLAY mode: replay_recorded_path() copies persisted RunCheckpointResults from a
source run verbatim. No evaluator dispatch or branch selection occurs.

Legacy: checkpoints without branch_rule_json fall back to hash-based branch
selection. This path exists for backward compatibility only.
"""

import hashlib
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioCheckpoint,
    ScenarioPack,
    ScenarioRun,
    CheckpointBranch,
    RunCheckpointResult,
    ScenarioPackTemplate,
)

logger = logging.getLogger(__name__)

# Evaluator primitives — each maps evaluator_type to a scoring function
EVALUATOR_PRIMITIVES = {
    "BINARY_RISK_GATE",
    "RESOURCE_DEPLETION",
    "DETECTION_EVENT",
    "TIMING_BREACH",
    "MISSION_COMPLETION",
}

# ── Primitive JSON Contracts ──

PRIMITIVE_CONTRACTS = {
    "BINARY_RISK_GATE": {
        "trigger_fields": {"type", "threshold", "metric"},
        "branch_rule_fields": {"type", "field", "threshold", "above_branch_index", "below_branch_index"},
        "branch_rule_type": "threshold_compare",
    },
    "RESOURCE_DEPLETION": {
        "trigger_fields": {"type", "resource", "depletion_curve"},
        "branch_rule_fields": {"type", "brackets", "field"},
        "branch_rule_type": "resource_bracket",
    },
    "DETECTION_EVENT": {
        "trigger_fields": {"type", "base_detection_probability"},
        "branch_rule_fields": {"type", "base_probability", "noise_amplitude", "detected_branch_index", "safe_branch_index"},
        "branch_rule_type": "probability_gate",
    },
    "TIMING_BREACH": {
        "trigger_fields": {"type", "deadline_sec", "drift_range"},
        "branch_rule_fields": {"type", "deadline_sec", "drift_range", "on_time_branch_index", "breach_branch_index"},
        "branch_rule_type": "deadline_compare",
    },
    "MISSION_COMPLETION": {
        "trigger_fields": {"type", "required_objectives", "min_completion"},
        "branch_rule_fields": {"type", "required", "min_completion", "success_branch_index", "partial_branch_index", "fail_branch_index"},
        "branch_rule_type": "objective_set",
    },
}

SPAWN_RULE_OPTIONAL_FIELDS = {"outcome_types", "min_reward", "checkpoint_classes", "run_modes"}


def validate_checkpoint_config(
    evaluator_type: str,
    trigger_condition_json: Optional[dict],
    branch_rule_json: Optional[dict],
) -> list[str]:
    """Validate a checkpoint's config against its evaluator_type.

    Returns a list of error strings. Empty list = valid.
    """
    errors: list[str] = []

    if evaluator_type not in EVALUATOR_PRIMITIVES:
        errors.append(f"Unknown evaluator_type: {evaluator_type}")
        return errors

    errors.extend(validate_trigger_condition_json(evaluator_type, trigger_condition_json))
    errors.extend(validate_branch_rule_json(evaluator_type, branch_rule_json))

    return errors


def validate_trigger_condition_json(
    evaluator_type: str,
    trigger_condition_json: Optional[dict],
) -> list[str]:
    """Validate trigger_condition_json for a primitive.

    Validates two layers:
    1. Primitive contract fields (type, metric/resource/etc.) for schema completeness
    2. Runtime trigger contract (field/operator/threshold) if present
    """
    if evaluator_type not in EVALUATOR_PRIMITIVES:
        return [f"Unknown evaluator_type: {evaluator_type}"]

    contract = PRIMITIVE_CONTRACTS[evaluator_type]
    if trigger_condition_json is None:
        return [f"{evaluator_type}: trigger_condition_json is required"]

    errors: list[str] = []

    # Validate primitive schema fields
    missing = contract["trigger_fields"] - set(trigger_condition_json.keys())
    if missing:
        errors.append(f"{evaluator_type}: trigger_condition_json missing fields: {missing}")

    # Validate runtime trigger contract if field/operator/threshold are present
    has_field = "field" in trigger_condition_json
    has_operator = "operator" in trigger_condition_json
    has_threshold = "threshold" in trigger_condition_json

    if has_field or has_operator:
        # field or operator signals runtime trigger contract intent;
        # threshold alone is a primitive contract field (e.g. BINARY_RISK_GATE)
        if not (has_field and has_operator and has_threshold):
            present = [k for k in ("field", "operator", "threshold") if k in trigger_condition_json]
            missing_trigger = [k for k in ("field", "operator", "threshold") if k not in trigger_condition_json]
            errors.append(
                f"{evaluator_type}: trigger contract has {present} but missing {missing_trigger}. "
                "All three (field, operator, threshold) are required for runtime gating."
            )
        elif trigger_condition_json["operator"] not in TRIGGER_OPERATORS:
            errors.append(
                f"{evaluator_type}: unsupported trigger operator '{trigger_condition_json['operator']}'. "
                f"Supported: {sorted(TRIGGER_OPERATORS.keys())}"
            )

    return errors


def validate_branch_rule_json(
    evaluator_type: str,
    branch_rule_json: Optional[dict],
) -> list[str]:
    """Validate branch_rule_json for a primitive."""
    if evaluator_type not in EVALUATOR_PRIMITIVES:
        return [f"Unknown evaluator_type: {evaluator_type}"]

    contract = PRIMITIVE_CONTRACTS[evaluator_type]
    if branch_rule_json is None:
        return [f"{evaluator_type}: branch_rule_json is required"]

    errors: list[str] = []
    missing = contract["branch_rule_fields"] - set(branch_rule_json.keys())
    if missing:
        errors.append(f"{evaluator_type}: branch_rule_json missing fields: {missing}")
    if branch_rule_json.get("type") != contract["branch_rule_type"]:
        errors.append(
            f"{evaluator_type}: branch_rule_json.type must be "
            f"'{contract['branch_rule_type']}', got '{branch_rule_json.get('type')}'"
        )

    return errors


def validate_branch_rule_set(
    evaluator_type: str,
    branches: list[CheckpointBranch],
) -> list[str]:
    """Validate every branch rule and require a shared evaluator contract."""
    errors: list[str] = []
    if not branches:
        return ["checkpoint must define at least one branch"]

    shared_rule = None
    for branch in branches:
        branch_errors = validate_branch_rule_json(evaluator_type, branch.branch_rule_json)
        for error in branch_errors:
            errors.append(f"Branch {branch.id}: {error}")

        if branch.branch_rule_json is None:
            continue

        if shared_rule is None:
            shared_rule = branch.branch_rule_json
        elif branch.branch_rule_json != shared_rule:
            errors.append(
                "branch_rule_json must match across branches for schema-driven evaluation"
            )

    return errors


def validate_spawn_rule(spawn_rule_json: Optional[dict]) -> list[str]:
    """Validate a theatre_spawn_rule_json config."""
    if spawn_rule_json is None:
        return []

    errors: list[str] = []

    if not isinstance(spawn_rule_json, dict):
        return ["theatre_spawn_rule_json must be a dict"]

    if "outcome_types" in spawn_rule_json:
        if not isinstance(spawn_rule_json["outcome_types"], list):
            errors.append("spawn_rule: outcome_types must be a list")

    if "min_reward" in spawn_rule_json:
        if not isinstance(spawn_rule_json["min_reward"], (int, float)):
            errors.append("spawn_rule: min_reward must be numeric")

    if "checkpoint_classes" in spawn_rule_json:
        if not isinstance(spawn_rule_json["checkpoint_classes"], list):
            errors.append("spawn_rule: checkpoint_classes must be a list")

    if "run_modes" in spawn_rule_json:
        if not isinstance(spawn_rule_json["run_modes"], list):
            errors.append("spawn_rule: run_modes must be a list")

    return errors


# ── Seeded RNG ──

def _seeded_rng(seed: int, checkpoint_id: str) -> random.Random:
    """Create checkpoint-scoped seeded RNG.

    Combines run seed with checkpoint_id for per-checkpoint determinism.
    """
    combined = hashlib.sha256(f"{seed}|{checkpoint_id}".encode()).hexdigest()
    return random.Random(int(combined[:8], 16))


# ── Trigger Condition Evaluation ──

# Supported trigger operators for field/operator/value evaluation
TRIGGER_OPERATORS = {
    "gte": lambda v, t: v >= t,
    "gt": lambda v, t: v > t,
    "lte": lambda v, t: v <= t,
    "lt": lambda v, t: v < t,
    "eq": lambda v, t: v == t,
    "ne": lambda v, t: v != t,
}


def _resolve_trigger_value(
    field: str,
    agent_action: str,
    state_vector: dict,
) -> float:
    """Resolve a trigger field value from state_vector first, then agent_action.

    state_vector is the authoritative source. agent_action is fallback for
    fields not yet accumulated in state.
    """
    if field in state_vector:
        try:
            return float(state_vector[field])
        except (TypeError, ValueError):
            pass
    return _parse_action_value(agent_action, field)


def _trigger_condition_met(
    trigger_condition_json: Optional[dict],
    agent_action: str,
    state_vector: dict,
) -> bool:
    """Evaluate whether a checkpoint's trigger condition is met.

    Supports two trigger contract forms:

    1. field/operator/threshold — general purpose:
       {"type": "...", "field": "risk", "operator": "gte", "threshold": 0.5, ...}
       Evaluates: state_vector[field] <operator> threshold

    2. "always" — unconditional activation:
       {"type": "always"} or trigger_condition_json is None

    The "type" field is retained for schema compatibility with evaluator primitives
    but does NOT select primitive-specific logic. Only the field/operator/threshold
    triple drives gating. Extra fields (metric, resource, etc.) are ignored at
    trigger evaluation time — they exist for template documentation only.

    Returns True if the checkpoint should activate, False to skip.
    Raises ValueError for unsupported operators (fail-fast at runtime).
    """
    if trigger_condition_json is None:
        return True

    tc_type = trigger_condition_json.get("type", "")

    # Explicit always-activate
    if tc_type == "always":
        return True

    # field/operator/threshold evaluation
    field = trigger_condition_json.get("field")
    operator = trigger_condition_json.get("operator")
    threshold = trigger_condition_json.get("threshold")

    if field is not None and operator is not None and threshold is not None:
        op_fn = TRIGGER_OPERATORS.get(operator)
        if op_fn is None:
            raise ValueError(
                f"Unsupported trigger operator '{operator}'. "
                f"Supported: {sorted(TRIGGER_OPERATORS.keys())}"
            )
        value = _resolve_trigger_value(field, agent_action, state_vector)
        return op_fn(value, float(threshold))

    # Legacy fallback: if trigger_condition_json has a recognized type but no
    # field/operator/threshold, activate unconditionally. This preserves backward
    # compatibility for templates that define trigger_condition_json with only
    # primitive-specific metadata fields (type, metric, resource, etc.) that were
    # never intended as runtime gates.
    return True


# ── Primitive Evaluator Functions ──

def _parse_action_value(agent_action: str, field: str) -> float:
    """Parse a numeric value from agent_action string.

    agent_action is either a plain number string or a JSON-like "field=value" format.
    """
    try:
        return float(agent_action)
    except (ValueError, TypeError):
        pass

    # Try key=value parsing
    for part in str(agent_action).split(","):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() == field:
                try:
                    return float(v.strip())
                except ValueError:
                    pass

    return 0.0


def evaluate_binary_risk_gate(
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[int, dict]:
    """BINARY_RISK_GATE: threshold comparison.

    action_value >= threshold -> above_branch_index, else below_branch_index.
    """
    field = branch_rule_json["field"]
    threshold = float(branch_rule_json["threshold"])
    above_idx = int(branch_rule_json["above_branch_index"])
    below_idx = int(branch_rule_json["below_branch_index"])

    action_value = _parse_action_value(agent_action, field)

    if action_value >= threshold:
        return above_idx, {"action_value": action_value, "threshold": threshold, "result": "above"}
    else:
        return below_idx, {"action_value": action_value, "threshold": threshold, "result": "below"}


def evaluate_resource_depletion(
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[int, dict]:
    """RESOURCE_DEPLETION: bracket mapping.

    remaining_fraction mapped to bracket -> corresponding branch_index.
    """
    field = branch_rule_json["field"]
    brackets = branch_rule_json["brackets"]

    value = _parse_action_value(agent_action, field)

    # Also check state_vector for resource tracking
    if field in state_vector:
        value = float(state_vector[field])

    for bracket in brackets:
        if float(bracket["min"]) <= value < float(bracket["max"]):
            return int(bracket["branch_index"]), {
                "value": value, "bracket_min": bracket["min"], "bracket_max": bracket["max"]
            }

    # Fallback: last bracket (inclusive of max)
    if brackets:
        last = brackets[-1]
        if value >= float(last["max"]):
            return int(last["branch_index"]), {"value": value, "fallback": "last_bracket"}

    return 0, {"value": value, "fallback": "default"}


def evaluate_detection_event(
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[int, dict]:
    """DETECTION_EVENT: probability gate with seeded noise.

    base_probability + noise(seed) > action_stealth_value -> detected, else safe.
    """
    base_prob = float(branch_rule_json["base_probability"])
    noise_amp = float(branch_rule_json["noise_amplitude"])
    detected_idx = int(branch_rule_json["detected_branch_index"])
    safe_idx = int(branch_rule_json["safe_branch_index"])

    # Get checkpoint_id from state_vector for RNG scoping
    checkpoint_id = state_vector.get("checkpoint_id", "default")
    rng = _seeded_rng(seed, checkpoint_id)
    noise = rng.uniform(-noise_amp, noise_amp)

    detection_threshold = base_prob + noise
    stealth_value = _parse_action_value(agent_action, "stealth")

    if detection_threshold > stealth_value:
        return detected_idx, {
            "detection_threshold": round(detection_threshold, 4),
            "stealth_value": stealth_value,
            "noise": round(noise, 4),
            "result": "detected",
        }
    else:
        return safe_idx, {
            "detection_threshold": round(detection_threshold, 4),
            "stealth_value": stealth_value,
            "noise": round(noise, 4),
            "result": "safe",
        }


def evaluate_timing_breach(
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[int, dict]:
    """TIMING_BREACH: deadline comparison with seeded drift.

    action_time + drift(seed) <= deadline -> on-time, else breach.
    """
    deadline = float(branch_rule_json["deadline_sec"])
    drift_range = float(branch_rule_json["drift_range"])
    on_time_idx = int(branch_rule_json["on_time_branch_index"])
    breach_idx = int(branch_rule_json["breach_branch_index"])

    checkpoint_id = state_vector.get("checkpoint_id", "default")
    rng = _seeded_rng(seed, checkpoint_id)
    drift = rng.uniform(-drift_range, drift_range)

    action_time = _parse_action_value(agent_action, "time")
    effective_time = action_time + drift

    if effective_time <= deadline:
        return on_time_idx, {
            "action_time": action_time,
            "drift": round(drift, 4),
            "effective_time": round(effective_time, 4),
            "deadline": deadline,
            "result": "on_time",
        }
    else:
        return breach_idx, {
            "action_time": action_time,
            "drift": round(drift, 4),
            "effective_time": round(effective_time, 4),
            "deadline": deadline,
            "result": "breach",
        }


def evaluate_mission_completion(
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[int, dict]:
    """MISSION_COMPLETION: objective set evaluation.

    Count completed objectives from action. >= min -> success, > 0 -> partial, 0 -> fail.
    """
    required = branch_rule_json["required"]
    min_completion = int(branch_rule_json["min_completion"])
    success_idx = int(branch_rule_json["success_branch_index"])
    partial_idx = int(branch_rule_json["partial_branch_index"])
    fail_idx = int(branch_rule_json["fail_branch_index"])

    # Parse completed objectives from agent_action
    # Format: "obj_a,obj_b" or "objectives=obj_a,obj_b"
    completed = set()
    action_str = str(agent_action)
    if "objectives=" in action_str:
        _, objs = action_str.split("objectives=", 1)
        completed = {o.strip() for o in objs.split(",") if o.strip()}
    else:
        completed = {o.strip() for o in action_str.split(",") if o.strip()}

    # Also check state_vector for previously completed objectives
    prev_completed = set(state_vector.get("completed_objectives", []))
    all_completed = completed | prev_completed

    matched = len(set(required) & all_completed)

    if matched >= min_completion:
        return success_idx, {"matched": matched, "required": len(required), "min": min_completion, "result": "success"}
    elif matched > 0:
        return partial_idx, {"matched": matched, "required": len(required), "min": min_completion, "result": "partial"}
    else:
        return fail_idx, {"matched": matched, "required": len(required), "min": min_completion, "result": "fail"}


# ── Evaluator Dispatch ──

PRIMITIVE_EVALUATORS = {
    "BINARY_RISK_GATE": evaluate_binary_risk_gate,
    "RESOURCE_DEPLETION": evaluate_resource_depletion,
    "DETECTION_EVENT": evaluate_detection_event,
    "TIMING_BREACH": evaluate_timing_breach,
    "MISSION_COMPLETION": evaluate_mission_completion,
}


def select_branch(
    evaluator_type: str,
    branches: list[CheckpointBranch],
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[CheckpointBranch, dict]:
    """Select branch via primitive evaluator.

    Returns (selected_branch, evaluation_detail).
    Raises ValueError for unknown evaluator_type or malformed config.
    """
    if not branches:
        raise ValueError("No branches available for checkpoint evaluation")

    evaluator = PRIMITIVE_EVALUATORS.get(evaluator_type)
    if evaluator is None:
        raise ValueError(f"Unknown evaluator primitive: {evaluator_type}")

    branch_index, detail = evaluator(
        branch_rule_json=branch_rule_json,
        agent_action=agent_action,
        seed=seed,
        state_vector=state_vector,
    )

    if branch_index < 0 or branch_index >= len(branches):
        raise ValueError(
            f"Evaluator {evaluator_type} returned branch_index {branch_index} "
            f"but only {len(branches)} branches exist"
        )

    return branches[branch_index], detail


# ── Legacy Hash Fallback ──

def _deterministic_branch_index(
    checkpoint_id: str,
    agent_action: str,
    seed: int,
    evaluator_type: str,
) -> int:
    """Legacy hash-based branch index. Used only when branch_rule_json is missing."""
    data = f"{checkpoint_id}|{agent_action}|{seed}|{evaluator_type}"
    h = hashlib.sha256(data.encode()).hexdigest()
    return int(h[:8], 16)


def _compute_reward(
    evaluator_type: str,
    branch_reward_mapping: Optional[dict],
    checkpoint_reward_mapping: Optional[dict],
    objective_vector: Optional[list],
) -> float:
    """Compute reward from mappings and objective vector weights."""
    base_reward = 0.0

    mapping = branch_reward_mapping or checkpoint_reward_mapping
    if mapping:
        base_reward = mapping.get("base_reward", 0.0)
        multipliers = mapping.get("evaluator_multipliers", {})
        if evaluator_type in multipliers:
            base_reward *= multipliers[evaluator_type]

    if objective_vector:
        total_weight = sum(comp.get("weight", 0.0) for comp in objective_vector if isinstance(comp, dict))
        if total_weight > 0:
            base_reward *= total_weight

    return round(base_reward, 4)


def validate_template_checkpoints(
    session: Session,
    template_id: str,
) -> list[str]:
    """Validate all checkpoints in a template have valid evaluator configs.

    Returns list of error strings. Empty = all valid.
    """
    checkpoints = session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == template_id)
    ).scalars().all()

    all_errors: list[str] = []
    for cp in checkpoints:
        # Get branches for this checkpoint
        branches = session.execute(
            select(CheckpointBranch)
            .where(CheckpointBranch.checkpoint_id == cp.id)
        ).scalars().all()

        errors = validate_trigger_condition_json(
            cp.evaluator_type,
            cp.trigger_condition_json,
        )
        for e in errors:
            all_errors.append(f"Checkpoint {cp.id} (seq {cp.sequence_num}): {e}")

        branch_errors = validate_branch_rule_set(cp.evaluator_type, branches)
        for e in branch_errors:
            all_errors.append(f"Checkpoint {cp.id} (seq {cp.sequence_num}): {e}")

        # Validate spawn rule if present
        spawn_errors = validate_spawn_rule(cp.theatre_spawn_rule_json)
        for e in spawn_errors:
            all_errors.append(f"Checkpoint {cp.id} (seq {cp.sequence_num}): {e}")

    return all_errors


def evaluate_checkpoints(
    session: Session,
    run: ScenarioRun,
    seed: int,
    agent_actions: Optional[dict[str, str]] = None,
    ws_events: Optional[list] = None,
) -> list[RunCheckpointResult]:
    """Evaluate all checkpoints for a run.

    Uses primitive evaluators when branch_rule_json is present,
    falls back to legacy hash-based selection otherwise.

    ws_events: if provided, checkpoint resolution and theatre spawn events are
    appended as dicts for the caller to emit asynchronously after run_sync returns.
    This avoids calling async WS broadcast from sync context.
    """
    if agent_actions is None:
        agent_actions = {}

    run.environment_seed = seed
    run.status = "RUNNING"
    run.started_at = datetime.now(timezone.utc)

    pack = run.pack
    template = session.get(ScenarioPackTemplate, pack.template_id)
    objective_vector = template.objective_vector_json if template else None

    checkpoints = session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == pack.template_id)
        .order_by(ScenarioCheckpoint.sequence_num)
    ).scalars().all()

    if not checkpoints:
        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        session.flush()
        return []

    results = []
    current_checkpoint = checkpoints[0]
    checkpoint_map = {cp.id: cp for cp in checkpoints}

    # Accumulate state vector across checkpoints
    state_vector = {
        "cumulative_reward": 0.0,
        "completed_objectives": [],
        "previous_branch_outcomes": [],
    }

    while current_checkpoint is not None:
        branches = session.execute(
            select(CheckpointBranch)
            .where(CheckpointBranch.checkpoint_id == current_checkpoint.id)
        ).scalars().all()

        if not branches:
            break

        agent_action = agent_actions.get(current_checkpoint.id, "default")

        # Add checkpoint context to state_vector
        state_vector["checkpoint_id"] = current_checkpoint.id
        state_vector["sequence_num"] = current_checkpoint.sequence_num

        # Evaluate trigger_condition_json to determine if checkpoint activates
        if not _trigger_condition_met(current_checkpoint.trigger_condition_json, agent_action, state_vector):
            # Skip this checkpoint — advance to next in sequence
            next_seq = current_checkpoint.sequence_num + 1
            current_checkpoint = next(
                (cp for cp in checkpoints if cp.sequence_num == next_seq), None
            )
            continue

        has_schema_rules = any(branch.branch_rule_json is not None for branch in branches)

        if has_schema_rules:
            branch_errors = validate_branch_rule_set(
                current_checkpoint.evaluator_type,
                branches,
            )
            if branch_errors:
                logger.error(
                    "Checkpoint %s has invalid schema branch config: %s",
                    current_checkpoint.id,
                    "; ".join(branch_errors),
                )
                run.status = "FAILED"
                run.completed_at = datetime.now(timezone.utc)
                session.flush()
                return results

            try:
                selected_branch, eval_detail = select_branch(
                    evaluator_type=current_checkpoint.evaluator_type,
                    branches=branches,
                    branch_rule_json=branches[0].branch_rule_json,
                    agent_action=agent_action,
                    seed=seed,
                    state_vector=state_vector,
                )
            except ValueError as e:
                logger.error("Checkpoint evaluation failed: %s", e)
                run.status = "FAILED"
                run.completed_at = datetime.now(timezone.utc)
                session.flush()
                return results
        else:
            # Legacy fallback: hash-based selection
            branch_idx = _deterministic_branch_index(
                current_checkpoint.id,
                agent_action,
                seed,
                current_checkpoint.evaluator_type,
            )
            selected_branch = branches[branch_idx % len(branches)]
            eval_detail = {"fallback": "hash_based"}

        reward = _compute_reward(
            current_checkpoint.evaluator_type,
            selected_branch.reward_mapping_json,
            current_checkpoint.reward_mapping_json,
            objective_vector,
        )

        # Build full state vector for persistence
        result_state_vector = {
            **state_vector,
            "seed": seed,
            "evaluator_type": current_checkpoint.evaluator_type,
            "evaluation_detail": eval_detail,
        }

        result = RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            checkpoint_id=current_checkpoint.id,
            selected_branch_id=selected_branch.id,
            agent_decision_json={"action": agent_action},
            reward=reward,
            state_vector_json=result_state_vector,
            resolved_at=datetime.now(timezone.utc),
        )
        session.add(result)
        results.append(result)

        # Collect WS event for checkpoint resolution
        if ws_events is not None:
            ws_events.append({
                "type": "CHECKPOINT_RESOLVED",
                "pack_id": pack.id,
                "run_id": run.id,
                "checkpoint_id": current_checkpoint.id,
                "selected_branch_id": selected_branch.id,
                "outcome_type": selected_branch.outcome_type,
                "reward": reward,
                "sequence_num": current_checkpoint.sequence_num,
            })

        # Spawn theatre via rule evaluation or legacy boolean
        from backend.services.theatre_spawner import should_spawn, spawn_theatre
        if should_spawn(
            current_checkpoint.theatre_spawn_rule_json,
            selected_branch,
            reward,
            run.run_mode,
            current_checkpoint,
        ):
            spawned = spawn_theatre(session, current_checkpoint, pack, run, result)
            if spawned and ws_events is not None:
                ws_events.append({
                    "type": "THEATRE_SPAWNED",
                    "pack_id": pack.id,
                    "run_id": run.id,
                    "theatre_id": spawned.id,
                    "checkpoint_id": current_checkpoint.id,
                })

        # Update state vector for next checkpoint
        state_vector["cumulative_reward"] = round(state_vector["cumulative_reward"] + reward, 4)
        state_vector["previous_branch_outcomes"].append(selected_branch.outcome_type)

        run.current_checkpoint_seq = current_checkpoint.sequence_num
        run.total_reward += reward

        # Advance to next checkpoint
        next_cp_id = selected_branch.next_checkpoint_id
        if next_cp_id and next_cp_id in checkpoint_map:
            current_checkpoint = checkpoint_map[next_cp_id]
        else:
            current_checkpoint = None

    run.status = "COMPLETED"
    run.completed_at = datetime.now(timezone.utc)
    session.flush()

    return results


def replay_recorded_path(
    session: Session,
    run: ScenarioRun,
    source_run_id: str,
) -> list[RunCheckpointResult]:
    """Replay a completed run by copying its recorded checkpoint results.

    Creates new RunCheckpointResult records on `run` that mirror the source run's
    branch selections, rewards, and state vectors exactly. No evaluator dispatch
    or branch selection occurs — the recorded path is restored verbatim.

    Integrity checks:
    - Source run must exist and be COMPLETED with persisted results
    - Source run must belong to the same user (via pack.user_id)
    - Source run must use the same template (via pack.template_id)

    Theatre provenance: replay does NOT copy spawned_theatre_id. Replayed results
    record the source theatre reference in state_vector_json metadata only. This
    prevents replay packs from claiming they spawned theatres that belong to the
    source run.

    Raises ValueError if any integrity condition fails.
    """
    source_run = session.get(ScenarioRun, source_run_id)
    if source_run is None:
        raise ValueError(f"Source run '{source_run_id}' not found for replay")
    if source_run.status != "COMPLETED":
        raise ValueError(
            f"Source run '{source_run_id}' is {source_run.status}, not COMPLETED. "
            "Only completed runs can be replayed."
        )

    # Integrity: same user, same template
    replay_pack = session.get(ScenarioPack, run.pack_id)
    source_pack = session.get(ScenarioPack, source_run.pack_id)
    if not replay_pack or not source_pack:
        raise ValueError("Could not resolve packs for replay integrity check")
    if replay_pack.user_id != source_pack.user_id:
        raise ValueError(
            f"Replay integrity: source run belongs to user '{source_pack.user_id}', "
            f"but replay pack belongs to user '{replay_pack.user_id}'. "
            "Replay source must be owned by the same user."
        )
    if replay_pack.template_id != source_pack.template_id:
        raise ValueError(
            f"Replay integrity: source run uses template '{source_pack.template_id}', "
            f"but replay pack uses template '{replay_pack.template_id}'. "
            "Replay source must use the same template."
        )

    source_results = session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == source_run_id)
        .order_by(RunCheckpointResult.resolved_at)
    ).scalars().all()

    if not source_results:
        raise ValueError(f"Source run '{source_run_id}' has no checkpoint results to replay")

    run.status = "RUNNING"
    run.started_at = datetime.now(timezone.utc)
    run.environment_seed = source_run.environment_seed

    results = []
    for src in source_results:
        # Build state vector with replay provenance metadata
        sv = {
            **(src.state_vector_json or {}),
            "replay_source_run_id": source_run_id,
            "replay_source_result_id": src.id,
        }
        # Record source theatre reference in metadata only — do NOT set
        # spawned_theatre_id on replay results (prevents provenance corruption)
        if src.spawned_theatre_id:
            sv["replay_source_spawned_theatre_id"] = src.spawned_theatre_id

        result = RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            checkpoint_id=src.checkpoint_id,
            selected_branch_id=src.selected_branch_id,
            agent_decision_json=src.agent_decision_json,
            reward=src.reward,
            state_vector_json=sv,
            resolved_at=datetime.now(timezone.utc),
        )
        session.add(result)
        results.append(result)

        run.current_checkpoint_seq = max(
            run.current_checkpoint_seq,
            (src.state_vector_json or {}).get("sequence_num", 0),
        )
        run.total_reward += src.reward

    run.status = "COMPLETED"
    run.completed_at = datetime.now(timezone.utc)
    run.total_reward = round(run.total_reward, 4)
    session.flush()

    logger.info(
        "Replayed run %s from source %s (%d results copied)",
        run.id, source_run_id, len(results),
    )
    return results


def compute_branch_probabilities(
    session: Session,
    template_id: str,
) -> dict[str, dict[str, float]]:
    """Compute branch selection probabilities from fresh completed runs only."""
    checkpoints = session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == template_id)
    ).scalars().all()

    if not checkpoints:
        return {}

    probabilities: dict[str, dict[str, float]] = {}

    for cp in checkpoints:
        branch_rows = session.execute(
            select(
                RunCheckpointResult.selected_branch_id,
                func.count(RunCheckpointResult.id),
            )
            .join(ScenarioRun, RunCheckpointResult.run_id == ScenarioRun.id)
            .where(
                RunCheckpointResult.checkpoint_id == cp.id,
                ScenarioRun.status == "COMPLETED",
                ScenarioRun.run_mode != "REPLAY",
            )
            .group_by(RunCheckpointResult.selected_branch_id)
        ).all()

        if not branch_rows:
            probabilities[cp.id] = None
            continue

        total = sum(count for _, count in branch_rows)

        probabilities[cp.id] = {
            branch_id: round(count / total, 4)
            for branch_id, count in branch_rows
        }

    return probabilities


def build_episode_tree(
    session: Session,
    run: ScenarioRun,
) -> list[dict]:
    """Build episode tree from run checkpoint results."""
    results = session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run.id)
        .order_by(RunCheckpointResult.resolved_at)
    ).scalars().all()

    nodes = []
    for result in results:
        checkpoint = session.get(ScenarioCheckpoint, result.checkpoint_id)
        branch = session.get(CheckpointBranch, result.selected_branch_id)

        if not checkpoint or not branch:
            continue

        nodes.append({
            "checkpoint_id": checkpoint.id,
            "sequence_num": checkpoint.sequence_num,
            "trigger": checkpoint.trigger,
            "market_question": checkpoint.market_question,
            "selected_branch": branch.label,
            "outcome_type": branch.outcome_type,
            "reward": result.reward,
            "spawned_theatre_id": result.spawned_theatre_id,
        })

    return nodes


def build_replay_output(
    session: Session,
    run: ScenarioRun,
) -> dict:
    """Build ForkReplay-compatible output from run results."""
    results = session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run.id)
        .order_by(RunCheckpointResult.resolved_at)
    ).scalars().all()

    pack = run.pack
    template = session.get(ScenarioPackTemplate, pack.template_id)

    disclosure_events = []
    options = []
    time_offset = 0

    for result in results:
        checkpoint = session.get(ScenarioCheckpoint, result.checkpoint_id)
        branch = session.get(CheckpointBranch, result.selected_branch_id)

        if not checkpoint or not branch:
            continue

        disclosure_events.append({
            "tMs": time_offset,
            "type": "evidence_flip",
            "label": f"Checkpoint {checkpoint.sequence_num}: {branch.label}",
        })

        options.append({
            "label": branch.label,
            "pricePath": [
                {"tMs": time_offset, "price": 0.5},
                {"tMs": time_offset + checkpoint.decision_window_sec * 1000, "price": 1.0 if result.reward > 0 else 0.0},
            ],
        })

        time_offset += checkpoint.decision_window_sec * 1000

    return {
        "timelineId": f"scenario_{pack.id}",
        "forkId": run.id,
        "forkQuestion": template.name if template else "Scenario Run",
        "options": options,
        "openedAt": run.started_at.isoformat() if run.started_at else run.created_at.isoformat(),
        "settledAt": run.completed_at.isoformat() if run.completed_at else None,
        "chosenOption": options[-1]["label"] if options else None,
        "outcomeLabel": f"Total reward: {run.total_reward}",
        "disclosureEvents": disclosure_events,
        "notes": f"Seed: {run.environment_seed}, Mode: {run.run_mode}",
    }
