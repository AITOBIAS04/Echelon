"""SharkV1 -- First autonomous agent (MEGALODON variant).

Complete T0/T1/T2/T3 pipeline. Must execute >= 20 trades over 50 ticks,
respect all risk limits, and outperform at least one lower-skill archetype.

Acceptance criteria:
- >= 20 trades over 50 ticks
- Respects all risk limits (position, drawdown, stop-loss)
- Outperforms Degen or Saboteur

Cycle-013, Sprint 3 -- Task 2.
"""
from __future__ import annotations

from backend.agents.agent_instance import TheatreAgentInstance
from backend.agents.genome import EchelonArchetype, create_genome


# MEGALODON genome: enhanced Shark variant
# rho=0.90, epsilon=0.80, L=15000, novelty_threshold=0.6
MEGALODON_GENOME = create_genome(
    archetype=EchelonArchetype.SHARK,
    variant="MEGALODON",
)


def spawn_megalodon(
    theatre_id: str,
    rules_engine=None,
) -> TheatreAgentInstance:
    """Spawn a MEGALODON Shark agent for a Theatre.

    Returns a TheatreAgentInstance with MEGALODON genome parameters.
    The agent uses the standard T0/T1 pipeline via rules_engine.
    """
    return TheatreAgentInstance.spawn(
        genome=MEGALODON_GENOME,
        theatre_id=theatre_id,
        rules_engine=rules_engine,
    )
