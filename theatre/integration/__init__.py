"""Theatre Integration — bridges Cycle-027 verification to Cycle-031 Theatre engine."""

import json
from pathlib import Path
from typing import Any

from theatre.integration.ground_truth_adapter import (
    GroundTruthAdapter,
    convert_record_to_episode,
    convert_records_to_episodes,
)
from theatre.integration.models import GroundTruthRecord, OracleOutput
from theatre.integration.observer_oracle import ObserverOracleAdapter
from theatre.integration.observer_scorer import ObserverScoringFunction

_TEMPLATE_PATH = Path(__file__).parent / "observer_template.json"


def load_observer_template() -> dict[str, Any]:
    """Load and return the Observer Theatre template JSON."""
    return json.loads(_TEMPLATE_PATH.read_text())


__all__ = [
    "GroundTruthAdapter",
    "GroundTruthRecord",
    "OracleOutput",
    "ObserverOracleAdapter",
    "ObserverScoringFunction",
    "convert_record_to_episode",
    "convert_records_to_episodes",
    "load_observer_template",
]
