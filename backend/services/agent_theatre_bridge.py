"""Agent-Theatre Bridge -- autonomous agents in the Sponsored Theatre lifecycle.

Drop-in replacement for StubAgentSpawner. Same execute_tick() semantics,
richer output (DecisionTrace instead of TradeDecisionTrace).

Spawns one agent per archetype, wires into heartbeat, collects P&L at
settlement, and accumulates decision traces for RLMF export.

Cycle-013, Sprint 3 -- Task 3.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from backend.agents.agent_instance import (
    AgentSettlementResult,
    TheatreAgentInstance,
)
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import (
    AgentGenome,
    EchelonArchetype,
    create_genome,
)
from backend.agents.genome_loader import load_genome_pack
from backend.agents.rules_engine import RulesEngine
from backend.market.positions import PositionManager
from backend.market.state import MarketState
from backend.market.trading import TradingEngine


class AgentTheatreBridge:
    """Bridge: autonomous agents <-> Theatre lifecycle.

    Drop-in replacement for StubAgentSpawner.
    Same execute_tick() semantics, richer output (DecisionTrace).
    """

    def __init__(self) -> None:
        self._rules_engine = RulesEngine()
        self._agents: List[TheatreAgentInstance] = []
        self._all_traces: List[DecisionTrace] = []

    def spawn_agents(
        self,
        theatre_id: str,
        initial_balance: float = 1000.0,
        position_manager: Optional[PositionManager] = None,
        archetypes: Optional[List[EchelonArchetype]] = None,
        inquiry_class: str = "COUNTERFACTUAL",
        genome_dir: Optional[Path] = None,
    ) -> List[TheatreAgentInstance]:
        """Spawn one agent per archetype for a Theatre.

        Args:
            theatre_id: Theatre to bind agents to.
            initial_balance: Starting cash for each agent.
            position_manager: If provided, sets initial balance for each agent.
            archetypes: List of archetypes to spawn. Default: all 6.
            inquiry_class: Inquiry class from the theatre record.
            genome_dir: Optional path to directory of YAML genome files.
                If provided and contains .yaml files, genomes are loaded
                from YAML instead of the in-code factory.

        Returns:
            List of spawned TheatreAgentInstance objects.
        """
        if archetypes is None:
            archetypes = list(EchelonArchetype)

        # Load YAML genome pack if available
        yaml_genomes: Dict[str, AgentGenome] = {}
        if genome_dir is not None and genome_dir.is_dir():
            yaml_files = list(genome_dir.glob("*.yaml"))
            if yaml_files:
                yaml_genomes = load_genome_pack(genome_dir)

        # Index YAML genomes by archetype for lookup
        genomes_by_archetype: Dict[EchelonArchetype, List[AgentGenome]] = {}
        for genome in yaml_genomes.values():
            genomes_by_archetype.setdefault(genome.archetype, []).append(genome)

        agents = []
        for arch in archetypes:
            candidates = genomes_by_archetype.get(arch)
            if candidates:
                if len(candidates) == 1:
                    genome = candidates[0]
                else:
                    # Deterministic selection: sort by agent_id for canonical order
                    ordered = sorted(candidates, key=lambda g: g.agent_id or "")
                    digest = hashlib.sha256(
                        f"{theatre_id}:{arch.value}".encode()
                    ).digest()
                    idx = int.from_bytes(digest[:4], "big") % len(ordered)
                    genome = ordered[idx]
            else:
                # Fallback to factory
                genome = create_genome(arch)

            instance = TheatreAgentInstance.spawn(
                genome=genome,
                theatre_id=theatre_id,
                rules_engine=self._rules_engine,
                inquiry_class=inquiry_class,
            )
            if position_manager is not None:
                position_manager.set_balance(instance.agent_id, initial_balance)
            agents.append(instance)

        self._agents = agents
        return agents

    def execute_tick(
        self,
        agents: List[TheatreAgentInstance],
        market: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        evidence: object,
        tick: int,
        seed: int = 42,
    ) -> List[DecisionTrace]:
        """Execute one tick for all agents.

        Interface-compatible with StubAgentSpawner.execute_tick().
        Returns DecisionTrace list instead of TradeDecisionTrace list.
        """
        traces = []
        for agent in agents:
            _trade, trace = agent.tick(
                market=market,
                position_manager=position_manager,
                trading_engine=trading_engine,
                evidence=evidence,
                tick=tick,
                seed=seed,
            )
            traces.append(trace)
        self._all_traces.extend(traces)
        return traces

    def settle_agents(
        self,
        agents: List[TheatreAgentInstance],
        position_manager: PositionManager,
        resolved_outcome: int,
    ) -> List[AgentSettlementResult]:
        """Settle all agents after Theatre resolution.

        Returns comprehensive settlement results with P&L per agent.
        """
        results = []
        for agent in agents:
            result = agent.settle(position_manager, resolved_outcome)
            results.append(result)
        return results

    def collect_decision_traces(self) -> List[DecisionTrace]:
        """Collect all decision traces accumulated across all ticks.

        Returns a copy of the internal trace list for RLMF export.
        """
        return list(self._all_traces)

    @staticmethod
    def aggregate_pnl(
        results: List[AgentSettlementResult],
    ) -> Dict[str, float]:
        """Aggregate P&L from settlement results by archetype.

        Returns:
            Dict mapping archetype name to total realised P&L.
        """
        pnl_by_archetype: Dict[str, float] = {}
        for r in results:
            pnl_by_archetype[r.archetype] = (
                pnl_by_archetype.get(r.archetype, 0.0) + r.realised_pnl
            )
        return pnl_by_archetype
