"""Echelon OSINT Evidence Pipeline — Collection, Corroboration, Scoring.

Cycle-011: WorldMonitor Integration. Three-stage pipeline connecting
WorldMonitor's OSINT domain endpoints to the Paradox Engine's
RealitySignalProvider interface.

Sprint 1: Evidence Pipeline Core + WorldMonitor Collector
Sprint 2: Corroboration + Scoring + Paradox Wiring + Convergence
"""
from __future__ import annotations

from backend.osint.canonical import (
    canonical_json,
    compute_content_hash,
    compute_receipt_hash,
)
from backend.osint.collectors.base import BaseCollector, HashInvariantViolation
from backend.osint.collectors.companies_house import CompaniesHouseCollector
from backend.osint.collectors.worldmonitor import (
    WorldMonitorCollector,
    WorldMonitorConfig,
)
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
from backend.osint.models.evidence import CollectionResult
from backend.osint.models.registry import RegistryLoader, RegistrySource

__all__ = [
    # Canonical hashing
    "canonical_json",
    "compute_content_hash",
    "compute_receipt_hash",
    # Collectors
    "BaseCollector",
    "HashInvariantViolation",
    "CompaniesHouseCollector",
    "WorldMonitorCollector",
    "WorldMonitorConfig",
    # Engine — Collection
    "CollectionPlan",
    "CollectionRunner",
    # Engine — Corroboration
    "CorroborationEngine",
    "CorroborationResult",
    # Engine — Counter-signal
    "CounterSignalEvaluator",
    "CounterSignalOutcome",
    "CounterSignalResult",
    "COUNTER_SIGNAL_CLASSES",
    # Engine — Scorer
    "Scorer",
    "CriterionScore",
    "OracleOutput",
    # Engine — Convergence
    "ConvergenceDetector",
    "ConvergenceCell",
    "ConvergenceAlert",
    # Models
    "CollectionResult",
    "RegistryLoader",
    "RegistrySource",
]
