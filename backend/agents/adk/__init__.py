"""ADK integration layer -- FakeADKRunner and guarded ADK imports.

FakeADKRunner executes the agent's decision loop synchronously,
bypassing the ADK event system. Used in all default tests.

Cycle-013, Sprint 3 -- Task 1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from backend.agents.agent_instance import TheatreAgentInstance
from backend.agents.decision_trace import DecisionTrace
from backend.market.positions import PositionManager
from backend.market.state import MarketState
from backend.market.trading import Trade, TradingEngine


@dataclass
class FakeADKRunner:
    """Synchronous test runner that bypasses the ADK event system.

    Executes the agent's decision loop directly without ADK dependencies.
    Accumulates decision traces for RLMF export validation.
    """

    agent_instance: TheatreAgentInstance
    tick_count: int = 0
    max_ticks: int = 50
    decision_log: List[DecisionTrace] = field(default_factory=list)

    def run_tick(
        self,
        market: MarketState,
        position_manager: PositionManager,
        trading_engine: TradingEngine,
        evidence: object = None,
        seed: int = 42,
    ) -> Tuple[Optional[Trade], DecisionTrace]:
        """Execute a single tick synchronously.

        Returns:
            Tuple of (executed Trade or None, DecisionTrace).
        """
        trade, trace = self.agent_instance.tick(
            market=market,
            position_manager=position_manager,
            trading_engine=trading_engine,
            evidence=evidence,
            tick=self.tick_count,
            seed=seed,
        )
        self.decision_log.append(trace)
        self.tick_count += 1
        return trade, trace

    def run_all(
        self,
        market: MarketState,
        position_manager: PositionManager,
        trading_engine: TradingEngine,
        evidence_schedule: Optional[Dict[int, object]] = None,
        seed: int = 42,
    ) -> List[Tuple[Optional[Trade], DecisionTrace]]:
        """Run all ticks synchronously.

        Args:
            market: Market state (mutated by trades).
            position_manager: Position tracker.
            trading_engine: LMSR trade execution engine.
            evidence_schedule: {tick_number: evidence_object}.
            seed: Base RNG seed.

        Returns:
            List of (Trade or None, DecisionTrace) tuples.
        """
        results = []
        for tick in range(self.max_ticks):
            evidence = None
            if evidence_schedule and tick in evidence_schedule:
                evidence = evidence_schedule[tick]
            trade, trace = self.run_tick(
                market, position_manager, trading_engine, evidence, seed
            )
            results.append((trade, trace))
        return results
