"""
Checkpoint Evaluator — Schema-driven checkpoint automation.

Processes checkpoints in sequence_num order. At each checkpoint:
1. Evaluate trigger_condition_json against current run state
2. Execute evaluator_type primitive
3. Select branch via branch_rule_json, deterministically given (agent action, checkpoint state, seed, evaluator config)
4. Compute reward from reward_mapping_json + objective vector weights
5. Flag theatre_spawn_rule_json for Theatre Spawner (Sprint 4)
6. Create RunCheckpointResult
7. Advance to next checkpoint via branch.next_checkpoint_id
"""

import hashlib
import logging
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


def _deterministic_branch_index(
    checkpoint_id: str,
    agent_action: str,
    seed: int,
    evaluator_type: str,
) -> int:
    """Compute a deterministic branch index from inputs.

    Uses SHA-256 hash of concatenated inputs to produce a stable integer.
    """
    data = f"{checkpoint_id}|{agent_action}|{seed}|{evaluator_type}"
    h = hashlib.sha256(data.encode()).hexdigest()
    return int(h[:8], 16)


def _compute_reward(
    evaluator_type: str,
    branch_reward_mapping: Optional[dict],
    checkpoint_reward_mapping: Optional[dict],
    objective_vector: Optional[list],
) -> float:
    """Compute reward from mappings and objective vector weights.

    Priority: branch reward_mapping > checkpoint reward_mapping > default.
    Objective vector weights scale the base reward.
    """
    base_reward = 0.0

    # Get base reward from mappings
    mapping = branch_reward_mapping or checkpoint_reward_mapping
    if mapping:
        base_reward = mapping.get("base_reward", 0.0)

        # Evaluator-specific multipliers
        multipliers = mapping.get("evaluator_multipliers", {})
        if evaluator_type in multipliers:
            base_reward *= multipliers[evaluator_type]

    # Apply objective vector weight scaling if available
    if objective_vector:
        total_weight = sum(comp.get("weight", 0.0) for comp in objective_vector if isinstance(comp, dict))
        if total_weight > 0:
            base_reward *= total_weight

    return round(base_reward, 4)


def evaluate_checkpoints(
    session: Session,
    run: ScenarioRun,
    seed: int,
    agent_actions: Optional[dict[str, str]] = None,
) -> list[RunCheckpointResult]:
    """Evaluate all checkpoints for a run sequentially.

    Args:
        session: Database session.
        run: The ScenarioRun to evaluate.
        seed: Environment seed for deterministic branch selection.
        agent_actions: Map of checkpoint_id → agent action string.
                       If not provided, uses "default" for all.

    Returns:
        List of RunCheckpointResult records created.
    """
    if agent_actions is None:
        agent_actions = {}

    # Store seed on run
    run.environment_seed = seed
    run.status = "RUNNING"
    run.started_at = datetime.now(timezone.utc)

    # Get template for objective vector
    pack = run.pack
    template = session.get(ScenarioPackTemplate, pack.template_id)
    objective_vector = template.objective_vector_json if template else None

    # Get first checkpoint
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

    while current_checkpoint is not None:
        # Get branches for this checkpoint
        branches = session.execute(
            select(CheckpointBranch)
            .where(CheckpointBranch.checkpoint_id == current_checkpoint.id)
        ).scalars().all()

        if not branches:
            break

        # Select branch deterministically
        agent_action = agent_actions.get(current_checkpoint.id, "default")
        branch_idx = _deterministic_branch_index(
            current_checkpoint.id,
            agent_action,
            seed,
            current_checkpoint.evaluator_type,
        )
        selected_branch = branches[branch_idx % len(branches)]

        # Compute reward
        reward = _compute_reward(
            current_checkpoint.evaluator_type,
            selected_branch.reward_mapping_json,
            current_checkpoint.reward_mapping_json,
            objective_vector,
        )

        # Create result
        result = RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            checkpoint_id=current_checkpoint.id,
            selected_branch_id=selected_branch.id,
            agent_decision_json={"action": agent_action},
            reward=reward,
            state_vector_json={
                "seed": seed,
                "evaluator_type": current_checkpoint.evaluator_type,
                "sequence_num": current_checkpoint.sequence_num,
            },
            resolved_at=datetime.now(timezone.utc),
        )
        session.add(result)
        results.append(result)

        run.current_checkpoint_seq = current_checkpoint.sequence_num
        run.total_reward += reward

        # Advance to next checkpoint
        next_cp_id = selected_branch.next_checkpoint_id
        if next_cp_id and next_cp_id in checkpoint_map:
            current_checkpoint = checkpoint_map[next_cp_id]
        else:
            current_checkpoint = None

    # Run complete
    run.status = "COMPLETED"
    run.completed_at = datetime.now(timezone.utc)
    session.flush()

    return results


def compute_branch_probabilities(
    session: Session,
    template_id: str,
) -> dict[str, dict[str, float]]:
    """Compute branch selection probabilities from completed runs.

    Returns: {checkpoint_id: {branch_id: probability}}
    """
    # Get all checkpoints for this template
    checkpoints = session.execute(
        select(ScenarioCheckpoint)
        .where(ScenarioCheckpoint.template_id == template_id)
    ).scalars().all()

    if not checkpoints:
        return {}

    probabilities: dict[str, dict[str, float]] = {}

    for cp in checkpoints:
        # Get all results for this checkpoint
        results = session.execute(
            select(RunCheckpointResult)
            .where(RunCheckpointResult.checkpoint_id == cp.id)
        ).scalars().all()

        if not results:
            probabilities[cp.id] = None
            continue

        # Count branch selections
        branch_counts: dict[str, int] = {}
        total = len(results)
        for r in results:
            branch_counts[r.selected_branch_id] = branch_counts.get(r.selected_branch_id, 0) + 1

        # Convert to probabilities
        probabilities[cp.id] = {
            branch_id: round(count / total, 4)
            for branch_id, count in branch_counts.items()
        }

    return probabilities


def build_episode_tree(
    session: Session,
    run: ScenarioRun,
) -> list[dict]:
    """Build episode tree from run checkpoint results.

    Returns list of tree nodes with checkpoint info, selected branch, reward.
    """
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
    """Build ForkReplay-compatible output from run results.

    Maps checkpoint decisions to disclosure events for frontend replay.
    """
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

        # Map checkpoint decision to disclosure event
        disclosure_events.append({
            "tMs": time_offset,
            "type": "evidence_flip",
            "label": f"Checkpoint {checkpoint.sequence_num}: {branch.label}",
        })

        # Add option with simulated price path
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
