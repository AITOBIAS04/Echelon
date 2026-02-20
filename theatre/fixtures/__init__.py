"""Theatre test fixtures — Product Theatre templates and sample data."""

import json
from pathlib import Path
from typing import Any

from theatre.engine.models import GroundTruthEpisode

_FIXTURES_DIR = Path(__file__).parent


def load_template(name: str) -> dict[str, Any]:
    """Load a template fixture by name (without .json extension)."""
    path = _FIXTURES_DIR / f"{name}.json"
    return json.loads(path.read_text())


def load_ground_truth(name: str) -> list[GroundTruthEpisode]:
    """Load a ground truth JSONL fixture by name (without .jsonl extension)."""
    path = _FIXTURES_DIR / f"{name}.jsonl"
    episodes: list[GroundTruthEpisode] = []
    for line in path.read_text().strip().splitlines():
        data = json.loads(line)
        episodes.append(GroundTruthEpisode(**data))
    return episodes


# Pre-defined fixture names for convenience
OBSERVER_TEMPLATE = "product_observer_v1"
EASEL_TEMPLATE = "product_easel_v1"
CARTOGRAPH_TEMPLATE = "product_cartograph_v1"

OBSERVER_GROUND_TRUTH = "observer_provenance"
EASEL_GROUND_TRUTH = "easel_tdr_records"
CARTOGRAPH_GROUND_TRUTH = "cartograph_grid_reference"
