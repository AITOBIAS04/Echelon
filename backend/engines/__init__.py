"""Echelon Engine Layer — Butterfly, Entropy, Heartbeat, Paradox, VRF, Status.

Public API for the engines package. Sprints 1-3 of Cycle-010b.
"""
from backend.engines.butterfly import ButterflyEngine, TimelineState, WingFlap, WingFlapType
from backend.engines.config import ButterflyConfig, EngineConfig, EntropyConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import CADENCES, HeartbeatConfig, HeartbeatScheduler
from backend.engines.integration import EngineOrchestrator
from backend.engines.logic_gap import LogicGapCalculator, LogicGapReading, LogicGapStatus
from backend.engines.paradox import (
    ParadoxAction,
    ParadoxConfig,
    ParadoxEngine,
    ParadoxMode,
    ParadoxRuntimeState,
)
from backend.engines.reality_signal import (
    DeterministicRealityProvider,
    LiveOSINTRealityProvider,
    OsintRealityProvider,
    RealitySignal,
    RealitySignalProvider,
    StubRealityProvider,
)
from backend.engines.status import MarketStatusSnapshot, market_status_snapshot
from backend.engines.vrf import VRFConfig, VRFProvider, VRFResult

__all__ = [
    # Butterfly Engine
    "WingFlapType",
    "WingFlap",
    "TimelineState",
    "ButterflyEngine",
    # Entropy Engine
    "EntropyEngine",
    # Heartbeat Scheduler
    "HeartbeatConfig",
    "HeartbeatScheduler",
    "CADENCES",
    # Configuration
    "ButterflyConfig",
    "EntropyConfig",
    "EngineConfig",
    # Logic Gap
    "LogicGapStatus",
    "LogicGapReading",
    "LogicGapCalculator",
    # Reality Signal
    "RealitySignal",
    "RealitySignalProvider",
    "OsintRealityProvider",
    "DeterministicRealityProvider",
    "StubRealityProvider",
    "LiveOSINTRealityProvider",
    # Paradox Engine
    "ParadoxMode",
    "ParadoxAction",
    "ParadoxConfig",
    "ParadoxRuntimeState",
    "ParadoxEngine",
    # VRF
    "VRFConfig",
    "VRFResult",
    "VRFProvider",
    # Status
    "MarketStatusSnapshot",
    "market_status_snapshot",
    # Integration
    "EngineOrchestrator",
]
