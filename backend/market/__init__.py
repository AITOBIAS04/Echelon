"""LMSR Market Engine — cost function, lifecycle, trading, settlement.

Public API for the market package.
"""
from backend.market.commitment import MarketCommitment
from backend.market.exceptions import (
    InsufficientBalance,
    InsufficientShares,
    InvalidMarketParameters,
    InvalidPhaseTransition,
    MarketError,
    ParameterMutationAfterCommit,
    TradingHalted,
)
from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import AgentPosition, PositionManager
from backend.market.resolution import AgentSettlement, ResolutionEngine, SettlementReport
from backend.market.state import FeeSchedule, MarketPhase, MarketState
from backend.market.trading import Trade, TradingEngine

__all__ = [
    # Sprint 1: LMSR core
    "LMSREngine",
    "MarketState",
    "MarketPhase",
    "FeeSchedule",
    "MarketLifecycle",
    "MarketCommitment",
    # Sprint 2: Trading + positions + settlement
    "Trade",
    "TradingEngine",
    "AgentPosition",
    "PositionManager",
    "AgentSettlement",
    "SettlementReport",
    "ResolutionEngine",
    # Exceptions
    "MarketError",
    "InvalidPhaseTransition",
    "InvalidMarketParameters",
    "ParameterMutationAfterCommit",
    "TradingHalted",
    "InsufficientBalance",
    "InsufficientShares",
]
