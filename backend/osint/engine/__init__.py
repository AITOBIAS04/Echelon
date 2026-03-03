"""OSINT engine — collection, corroboration, scoring pipeline stages."""
from __future__ import annotations

from backend.osint.engine.collection_runner import CollectionPlan, CollectionRunner
from backend.osint.engine.convergence import ConvergenceAlert, ConvergenceCell, ConvergenceDetector
from backend.osint.engine.corroboration import CorroborationEngine, CorroborationResult
from backend.osint.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
    CounterSignalEvaluator,
    CounterSignalOutcome,
    CounterSignalResult,
)
from backend.osint.engine.scorer import CriterionScore, OracleOutput, Scorer

__all__ = [
    # Collection
    "CollectionPlan",
    "CollectionRunner",
    # Corroboration
    "CorroborationEngine",
    "CorroborationResult",
    # Counter-signal
    "CounterSignalEvaluator",
    "CounterSignalOutcome",
    "CounterSignalResult",
    "COUNTER_SIGNAL_CLASSES",
    # Scorer
    "Scorer",
    "CriterionScore",
    "OracleOutput",
    # Convergence
    "ConvergenceDetector",
    "ConvergenceCell",
    "ConvergenceAlert",
]
