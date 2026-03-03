"""EchelonAgent -- ADK wrapper for the T0/T1/T2/T3 pipeline.

Wraps TheatreAgentInstance with ADK lifecycle:
initialise -> subscribe to heartbeat -> execute decision loop -> settle.

Tool bindings: echelon_status, echelon_verify, execute_trade.

Cycle-013, Sprint 3 -- Task 1.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.agents.agent_instance import TheatreAgentInstance
from backend.agents.decision_router import DecisionRouter
from backend.agents.decision_trace import DecisionTrace

# ADK import guarded -- no hard dependency
try:
    from google.adk import Agent, Tool  # type: ignore[import-not-found]

    HAS_ADK = True
except ImportError:
    HAS_ADK = False


class EchelonAgent:
    """ADK Agent wrapper for the T0/T1/T2/T3 pipeline.

    Wraps TheatreAgentInstance with optional ADK lifecycle.
    Tool bindings:
    - echelon_status: query market state
    - echelon_verify: check certificate
    - execute_trade: submit trade to LMSR

    State persists between ticks (T0Context, decision history).
    """

    def __init__(
        self,
        agent_instance: TheatreAgentInstance,
        decision_router: Optional[DecisionRouter] = None,
    ) -> None:
        self._instance = agent_instance
        self._router = decision_router
        self._adk_agent: Optional[object] = None
        self._tools: Dict[str, object] = {}
        self._decision_history: List[DecisionTrace] = []

    @property
    def agent_id(self) -> str:
        """Agent ID from wrapped instance."""
        return self._instance.agent_id

    @property
    def decision_history(self) -> List[DecisionTrace]:
        """All decision traces from this agent."""
        return list(self._decision_history)

    def initialise(self) -> None:
        """Create ADK agent with tool bindings.

        Raises RuntimeError if Google ADK is not installed.
        """
        if not HAS_ADK:
            raise RuntimeError(
                "Google ADK not available. Install with: pip install google-adk"
            )
        # ADK agent creation would happen here in production
        self._adk_agent = object()  # Placeholder

    def register_tools(
        self,
        echelon_status: Optional[object] = None,
        echelon_verify: Optional[object] = None,
        execute_trade: Optional[object] = None,
    ) -> None:
        """Register tool bindings for ADK agent.

        Args:
            echelon_status: Market state query tool.
            echelon_verify: Certificate verification tool.
            execute_trade: LMSR trade execution tool.
        """
        if echelon_status is not None:
            self._tools["echelon_status"] = echelon_status
        if echelon_verify is not None:
            self._tools["echelon_verify"] = echelon_verify
        if execute_trade is not None:
            self._tools["execute_trade"] = execute_trade

    def on_heartbeat(self, tick, market, position_manager, trading_engine,
                     evidence=None, seed=42):
        """Handle heartbeat tick synchronously.

        Delegates to the wrapped TheatreAgentInstance.tick().
        Decision traces accumulated for RLMF export.
        """
        trade, trace = self._instance.tick(
            market=market,
            position_manager=position_manager,
            trading_engine=trading_engine,
            evidence=evidence,
            tick=tick,
            seed=seed,
        )
        self._decision_history.append(trace)
        return trade, trace

    def settle(self, position_manager, resolved_outcome):
        """Handle settlement. Returns AgentSettlementResult."""
        return self._instance.settle(position_manager, resolved_outcome)
