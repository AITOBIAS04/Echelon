"""
Scenario Telemetry Exporter — Convert ScenarioRun + CheckpointResults into RLMF export records.

Produces training-compatible data matching the RLMF export shape for downstream
reinforcement learning and agent evaluation pipelines.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioRun,
    ScenarioPack,
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
    RunCheckpointResult,
)

logger = logging.getLogger(__name__)


def export_run_telemetry(session: Session, run: ScenarioRun) -> dict:
    """Export a completed run as an RLMF-compatible record.

    Returns a dict matching the RLMF training data shape:
    - episode_id, scenario_pack_id, template_id, agent_id
    - actions: list of checkpoint decisions
    - rewards: list of per-checkpoint rewards
    - state_features: aggregated state vectors
    - fork_count: number of checkpoints resolved
    - episode_duration_sec
    - branch_path: ordered branch labels
    - spawned_theatre_ids: list of spawned theatre IDs
    """
    pack = run.pack
    template = session.get(ScenarioPackTemplate, pack.template_id)

    results = session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run.id)
        .order_by(RunCheckpointResult.resolved_at)
    ).scalars().all()

    actions = []
    rewards = []
    branch_path = []
    spawned_theatre_ids = []
    state_features = {}

    for result in results:
        checkpoint = session.get(ScenarioCheckpoint, result.checkpoint_id)
        branch = session.get(CheckpointBranch, result.selected_branch_id)

        if not checkpoint or not branch:
            continue

        actions.append({
            "checkpoint_id": checkpoint.id,
            "sequence_num": checkpoint.sequence_num,
            "trigger": checkpoint.trigger,
            "evaluator_type": checkpoint.evaluator_type,
            "agent_decision": result.agent_decision_json,
            "selected_branch_id": branch.id,
            "selected_branch_label": branch.label,
        })

        rewards.append(result.reward)
        branch_path.append(branch.label)

        if result.spawned_theatre_id:
            spawned_theatre_ids.append(result.spawned_theatre_id)

        if result.state_vector_json:
            for key, value in result.state_vector_json.items():
                state_features[f"cp_{checkpoint.sequence_num}_{key}"] = value

    return {
        "episode_id": run.id,
        "scenario_pack_id": run.pack_id,
        "template_id": pack.template_id,
        "template_name": template.name if template else None,
        "agent_id": run.agent_id,
        "run_mode": run.run_mode,
        "environment_seed": run.environment_seed,
        "actions": actions,
        "rewards": rewards,
        "total_reward": run.total_reward,
        "state_features": state_features,
        "fork_count": len(results),
        "episode_duration_sec": run.episode_duration_sec,
        "branch_path": branch_path,
        "spawned_theatre_ids": spawned_theatre_ids,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
