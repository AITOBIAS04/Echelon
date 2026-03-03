"""TheatreAgentInstance -- ephemeral agent bound to a Theatre.

Lifecycle: spawn() -> tick() [repeated] -> settle().
Each tick runs T0 compiler -> T1 rules engine -> executes trade ->
records DecisionTrace. Multiple instances per Identity (one per Theatre).

Cycle-013, Sprint 1 -- Tasks 5 + 6.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from backend.agents.context_compiler import ContextCompiler, T0Context
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import AgentGenome
from backend.agents.rules_engine import RulesEngine, T1Decision, TradeAction
from backend.market.positions import AgentPosition, PositionManager
from backend.market.state import MarketState
from backend.market.trading import Trade, TradingEngine


@dataclass
class TradeIntent:
    """Agent's intended trade before execution."""

    outcome_index: int
    shares: float
    trigger: str
    confidence: float


@dataclass
class AgentSettlementResult:
    """Settlement result for a single agent instance."""

    agent_id: str
    archetype: str
    trades_executed: int
    final_position: List[float]
    realised_pnl: float
    unrealised_pnl: float


class TheatreAgentInstance:
    """Ephemeral agent instance bound to a Theatre.

    Lifecycle: spawn() -> tick() [repeated] -> settle()
    Integrates with TradingEngine and PositionManager from backend/market/.
    """

    def __init__(
        self,
        agent_id: str,
        genome: AgentGenome,
        theatre_id: str,
        rules_engine: RulesEngine,
    ) -> None:
        self.agent_id = agent_id
        self.genome = genome
        self.theatre_id = theatre_id
        self._rules_engine = rules_engine
        self._decision_traces: List[DecisionTrace] = []
        self._trade_count: int = 0
        self._settled: bool = False

    @classmethod
    def spawn(
        cls,
        genome: AgentGenome,
        theatre_id: str,
        rules_engine: Optional[RulesEngine] = None,
    ) -> TheatreAgentInstance:
        """Factory: create an agent instance for a Theatre.

        Agent ID format: {theatre_id}_{archetype}[_{variant}]

        Args:
            genome: Agent genome with archetype parameters.
            theatre_id: Theatre this instance is bound to.
            rules_engine: Optional custom rules engine (default creates new).

        Returns:
            New TheatreAgentInstance ready for tick().
        """
        agent_id = f"{theatre_id}_{genome.archetype.value.lower()}"
        if genome.variant:
            agent_id = f"{agent_id}_{genome.variant.lower()}"
        return cls(
            agent_id=agent_id,
            genome=genome,
            theatre_id=theatre_id,
            rules_engine=rules_engine or RulesEngine(),
        )

    def tick(
        self,
        market: MarketState,
        position_manager: PositionManager,
        trading_engine: TradingEngine,
        evidence: object,
        tick: int,
        seed: int = 42,
    ) -> Tuple[Optional[Trade], DecisionTrace]:
        """Execute one decision tick.

        1. Get current position and balance from PositionManager.
        2. Compute evidence coverage.
        3. T0: compile context via ContextCompiler.
        4. T1: decide via RulesEngine.
        5. Execute trade via TradingEngine if BUY/SELL (catch failures silently).
        6. Build and store DecisionTrace.
        7. Return (executed_trade_or_None, trace).

        Args:
            market: Current market state.
            position_manager: Position tracker for balance/shares.
            trading_engine: LMSR trade execution engine.
            evidence: Evidence object (None if no evidence this tick).
            tick: Current tick number.
            seed: Base RNG seed for deterministic decisions.

        Returns:
            Tuple of (executed Trade or None, DecisionTrace).
        """
        # 1. Get current position and balance
        position = position_manager.get_position(self.agent_id)
        balance = position_manager.get_balance(self.agent_id)

        # 2. Compute evidence coverage (0.0 if None, 0.5 if present)
        evidence_coverage = 0.0 if evidence is None else 0.5

        # 3. T0: compile context
        t0_ctx = ContextCompiler.compile(
            genome=self.genome,
            market=market,
            position=position,
            available_balance=balance,
            evidence_coverage_pct=evidence_coverage,
        )

        # 4. T1: rules engine decision
        rng_seed = seed + tick + hash(self.agent_id) % 10000
        t1_decision = self._rules_engine.decide(t0_ctx, tick, rng_seed)

        # 5. Build trade intent and execute
        executed_trade: Optional[Trade] = None
        action_str = t1_decision.action.value

        if t1_decision.action in (TradeAction.BUY, TradeAction.SELL):
            if t1_decision.outcome_index is not None and t1_decision.shares > 0:
                # Cap shares by position limit from genome
                shares = min(t1_decision.shares, self.genome.position_limit)

                if t1_decision.action == TradeAction.SELL:
                    shares = -shares
                try:
                    executed_trade = trading_engine.execute_trade(
                        market=market,
                        agent_id=self.agent_id,
                        outcome_index=t1_decision.outcome_index,
                        shares=shares,
                    )
                    self._trade_count += 1
                    action_str = (
                        f"{t1_decision.action.value}"
                        f"(outcome={t1_decision.outcome_index},"
                        f" shares={abs(shares):.1f})"
                    )
                except Exception:
                    # Trade failed -- record attempt, continue
                    pass

        # 6. Build decision trace
        trace = DecisionTrace(
            tick_id=f"tick_{tick:04d}",
            agent_id=self.agent_id,
            theatre_id=self.theatre_id,
            tier_used="T1-RULES",
            market_state_snapshot={
                "prices": list(t0_ctx.prices),
                "phase": t0_ctx.phase,
                "evidence_coverage_pct": t0_ctx.evidence_coverage_pct,
            },
            evidence_state={
                "new_evidence_flag": evidence is not None,
                "source_ids_cited": [],
            },
            t0_context_hash=t0_ctx.context_hash,
            action=action_str,
            confidence=t1_decision.confidence,
            pattern_name=t1_decision.pattern_name,
            options_considered=[
                {
                    "action": opt.action,
                    "estimated_value": opt.estimated_value,
                    "rejection_reason": opt.rejection_reason,
                }
                for opt in t1_decision.options_considered
            ],
            reasoning_summary=t1_decision.reasoning_trace,
            escalated_to_t3=t1_decision.escalate_to_t3,
            evidence_refs=[],
        )

        self._decision_traces.append(trace)
        return executed_trade, trace

    def settle(
        self, position_manager: PositionManager, resolved_outcome: int
    ) -> AgentSettlementResult:
        """Finalise this instance. Compute settlement P&L.

        Args:
            position_manager: Position tracker with final positions.
            resolved_outcome: Index of the winning outcome.

        Returns:
            AgentSettlementResult with P&L and final position.
        """
        self._settled = True
        position = position_manager.get_position(self.agent_id)
        payout = position_manager.compute_settlement_payout(
            position, resolved_outcome
        )

        return AgentSettlementResult(
            agent_id=self.agent_id,
            archetype=self.genome.archetype.value,
            trades_executed=self._trade_count,
            final_position=list(position.shares),
            realised_pnl=payout - position.net_cashflow,
            unrealised_pnl=0.0,  # All positions settled
        )

    @property
    def decision_traces(self) -> List[DecisionTrace]:
        """All decision traces accumulated during this instance's lifetime."""
        return list(self._decision_traces)

    @property
    def trade_count(self) -> int:
        """Number of successfully executed trades."""
        return self._trade_count

    @property
    def is_settled(self) -> bool:
        """Whether this instance has been settled."""
        return self._settled
