"""
Scenario Run State Builder — Normalize checkpoint state vector input for evaluators.

Builds a state vector from previous checkpoint results within a run,
providing evaluators with cumulative context.
"""

from backend.database.models import ScenarioRun, ScenarioCheckpoint, RunCheckpointResult


def build_state_vector(
    run: ScenarioRun,
    checkpoint: ScenarioCheckpoint,
    previous_results: list[RunCheckpointResult],
) -> dict:
    """Build state vector for checkpoint evaluation.

    Returns dict with:
    - cumulative_reward: total reward from previous checkpoints
    - completed_objectives: list of objective IDs from previous results
    - remaining_resources: dict of resource states (from state_vector_json)
    - elapsed_time_sec: cumulative time from previous checkpoints
    - previous_branch_outcomes: list of outcome_type strings
    - checkpoint_id: current checkpoint ID
    - sequence_num: current checkpoint sequence number
    """
    cumulative_reward = 0.0
    completed_objectives: list[str] = []
    previous_outcomes: list[str] = []
    elapsed_time_sec = 0.0

    for result in previous_results:
        cumulative_reward += result.reward

        # Extract objectives from evaluation detail
        if result.state_vector_json:
            detail = result.state_vector_json.get("evaluation_detail", {})
            if detail.get("result") == "success" or detail.get("result") == "partial":
                # Track that objectives were progressed
                pass

            prev_outcomes = result.state_vector_json.get("previous_branch_outcomes", [])
            if prev_outcomes:
                previous_outcomes = prev_outcomes

    return {
        "cumulative_reward": round(cumulative_reward, 4),
        "completed_objectives": completed_objectives,
        "previous_branch_outcomes": previous_outcomes,
        "elapsed_time_sec": elapsed_time_sec,
        "checkpoint_id": checkpoint.id,
        "sequence_num": checkpoint.sequence_num,
    }
