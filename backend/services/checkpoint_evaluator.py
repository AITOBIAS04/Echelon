"""
Checkpoint Evaluator v2 — Schema-driven checkpoint resolution.

Processes checkpoints in sequence_num order. At each checkpoint:
1. Dispatch to primitive evaluator based on evaluator_type
2. Evaluate branch_rule_json with agent action, seed, and state vector
3. Compute reward from reward_mapping_json + objective vector weights
4. Evaluate theatre_spawn_rule_json for derived theatre spawning
5. Create RunCheckpointResult with full state vector
6. Advance to next checkpoint via branch.next_checkpoint_id

v2 (Cycle 020): Schema-driven evaluation replaces hash-based branching.
All 5 evaluator primitives implemented. Environment RNG via seeded random.Random.
"""

import hashlib
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioCheckpoint,
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
    trigger_condition_json: dict | None,
    branch_rule_json: dict | None,
) -> list[str]:
    """Validate a checkpoint's config against its evaluator_type.

    Returns a list of error strings. Empty list = valid.
    """
    errors: list[str] = []

    if evaluator_type not in EVALUATOR_PRIMITIVES:
        errors.append(f"Unknown evaluator_type: {evaluator_type}")
        return errors

    contract = PRIMITIVE_CONTRACTS[evaluator_type]

    if trigger_condition_json is None:
        errors.append(f"{evaluator_type}: trigger_condition_json is required")
    else:
        missing = contract["trigger_fields"] - set(trigger_condition_json.keys())
        if missing:
            errors.append(f"{evaluator_type}: trigger_condition_json missing fields: {missing}")

    if branch_rule_json is None:
        errors.append(f"{evaluator_type}: branch_rule_json is required")
    else:
        missing = contract["branch_rule_fields"] - set(branch_rule_json.keys())
        if missing:
            errors.append(f"{evaluator_type}: branch_rule_json missing fields: {missing}")
        if branch_rule_json.get("type") != contract["branch_rule_type"]:
            errors.append(
                f"{evaluator_type}: branch_rule_json.type must be "
                f"'{contract['branch_rule_type']}', got '{branch_rule_json.get('type')}'"
            )

    return errors


def validate_spawn_rule(spawn_rule_json: dict | None) -> list[str]:
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

def _trigger_condition_met(
    trigger_condition_json: dict | None,
    agent_action: str,
    state_vector: dict,
) -> bool:
    """Evaluate whether a checkpoint's trigger condition is met.

    trigger_condition_json is evaluated against agent_action and state_vector.
    Returns True if the checkpoint should activate, False to skip.

    When trigger_condition_json is None, the checkpoint always activates (legacy).
    """
    if trigger_condition_json is None:
        return True

    tc_type = trigger_condition_json.get("type")

    if tc_type == "BINARY_RISK_GATE":
        # Activates when metric exceeds threshold
        threshold = trigger_condition_json.get("threshold", 0.0)
        metric = trigger_condition_json.get("metric", "")
        value = _parse_action_value(agent_action, metric)
        return value >= threshold

    if tc_type == "RESOURCE_DEPLETION":
        # Activates when resource level triggers depletion curve
        resource = trigger_condition_json.get("resource", "")
        value = state_vector.get(resource, _parse_action_value(agent_action, resource))
        return value > 0  # Active as long as resource exists

    if tc_type == "DETECTION_EVENT":
        # Activates when detection probability is non-trivial
        base_prob = trigger_condition_json.get("base_detection_probability", 0.0)
        return base_prob > 0

    if tc_type == "TIMING_BREACH":
        # Activates when within deadline range
        deadline = trigger_condition_json.get("deadline_sec", float("inf"))
        return deadline < float("inf")

    if tc_type == "MISSION_COMPLETION":
        # Activates when there are required objectives to check
        required = trigger_condition_json.get("required_objectives", [])
        return len(required) > 0

    # Unknown type: activate by default (safe fallback)
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

        # Validate checkpoint config
        # branch_rule_json is checkpoint-level evaluation logic. All branches of a
        # checkpoint share the same rule (the evaluator returns a branch index).
        # We validate using the first branch's rule and verify consistency.
        branch_rule = None
        if branches:
            branch_rule = branches[0].branch_rule_json
            # Verify all branches share the same rule type
            for br in branches[1:]:
                if br.branch_rule_json is not None and branch_rule is not None:
                    if br.branch_rule_json.get("type") != branch_rule.get("type"):
                        all_errors.append(
                            f"Checkpoint {cp.id} (seq {cp.sequence_num}): "
                            f"inconsistent branch_rule_json types across branches"
                        )

        errors = validate_checkpoint_config(
            cp.evaluator_type,
            cp.trigger_condition_json,
            branch_rule,
        )
        for e in errors:
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
) -> list[RunCheckpointResult]:
    """Evaluate all checkpoints for a run using schema-driven evaluation.

    Uses primitive evaluators when branch_rule_json is present,
    falls back to legacy hash-based selection otherwise.
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

        # Schema-driven evaluation if branch_rule_json present on checkpoint's branches
        # branch_rule_json is checkpoint-level logic stored on branches (shared across all)
        first_branch_rule = branches[0].branch_rule_json if branches else None

        if first_branch_rule is not None:
            try:
                selected_branch, eval_detail = select_branch(
                    evaluator_type=current_checkpoint.evaluator_type,
                    branches=branches,
                    branch_rule_json=first_branch_rule,
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

        # Spawn theatre via rule evaluation or legacy boolean
        from backend.services.theatre_spawner import should_spawn, spawn_theatre
        if should_spawn(
            current_checkpoint.theatre_spawn_rule_json,
            selected_branch,
            reward,
            run.run_mode,
            current_checkpoint,
        ):
            spawn_theatre(session, current_checkpoint, pack, run, result)

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


def compute_branch_probabilities(
    session: Session,
    template_id: str,
) -> dict[str, dict[str, float]]:
    """Compute branch selection probabilities from completed runs."""
    checkpoints = session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == template_id)
    ).scalars().all()

    if not checkpoints:
        return {}

    probabilities: dict[str, dict[str, float]] = {}

    for cp in checkpoints:
        results = session.execute(
            select(RunCheckpointResult)
            .where(RunCheckpointResult.checkpoint_id == cp.id)
        ).scalars().all()

        if not results:
            probabilities[cp.id] = None
            continue

        branch_counts: dict[str, int] = {}
        total = len(results)
        for r in results:
            branch_counts[r.selected_branch_id] = branch_counts.get(r.selected_branch_id, 0) + 1

        probabilities[cp.id] = {
            branch_id: round(count / total, 4)
            for branch_id, count in branch_counts.items()
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
