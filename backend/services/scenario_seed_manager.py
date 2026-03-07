"""
Scenario Seed Manager — Allocate environment seeds based on run_mode policy.

Policies:
- TRAINING: random seed per run (stochastic, varying)
- EVALUATION: controlled stochasticity from a fixed seed set
- CALIBRATION: canonical seed set for cross-run comparability

REPLAY mode does NOT use this module. REPLAY uses replay_recorded_path() in
checkpoint_evaluator.py to copy persisted results from a source run verbatim.
The seed is preserved as metadata on the replay run but is not used for
branch selection.
"""

import random
from typing import Optional

# Canonical seeds for CALIBRATION mode — fixed across all runs
CALIBRATION_SEEDS = [42, 137, 256, 512, 1024]

# Evaluation pool — larger set for controlled stochasticity
EVALUATION_SEEDS = [7, 13, 23, 31, 47, 59, 67, 73, 89, 97]


def allocate_seed(
    run_mode: str,
    run_index: int = 0,
    replay_seed: Optional[int] = None,
) -> int:
    """Allocate an environment seed based on run_mode.

    Args:
        run_mode: One of TRAINING, EVALUATION, CALIBRATION, REPLAY.
        run_index: Index into seed sets for CALIBRATION/EVALUATION.
        replay_seed: Required for REPLAY mode — the seed from the original run.

    Returns:
        The allocated seed value.

    Raises:
        ValueError: If REPLAY mode is used without a replay_seed.
    """
    if run_mode == "TRAINING":
        return random.randint(0, 2**31 - 1)

    if run_mode == "EVALUATION":
        return EVALUATION_SEEDS[run_index % len(EVALUATION_SEEDS)]

    if run_mode == "CALIBRATION":
        return CALIBRATION_SEEDS[run_index % len(CALIBRATION_SEEDS)]

    if run_mode == "REPLAY":
        if replay_seed is None:
            raise ValueError("REPLAY mode requires a replay_seed from the original run.")
        return replay_seed

    raise ValueError(f"Unknown run_mode: {run_mode}")
