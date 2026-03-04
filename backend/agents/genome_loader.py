"""Genome Loader -- YAML-driven genome loading for Echelon agents.

Loads archetype genome YAML files into AgentGenome instances,
replacing the in-code factory path with data-driven configuration.

Cycle-014b, Sprint 1 -- Task 2.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict

import yaml

from backend.agents.genome import (
    AgentGenome,
    DecisionPolicy,
    EchelonArchetype,
    InquiryClassAffinity,
    ParadoxBehaviour,
    SuccessMetrics,
    TierProfile,
)


def load_genome(filepath: Path) -> AgentGenome:
    """Load a single genome YAML file into an AgentGenome instance.

    Maps the 7 YAML sections to extended AgentGenome fields.
    Theatre context fields (committed_sources, outcome_labels) are NOT set;
    they are injected at spawn time.

    Args:
        filepath: Path to a genome YAML file.

    Returns:
        Frozen AgentGenome instance.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    ident = data.get("identity", {})
    econ = data.get("economic_parameters", {})

    # Map identity section
    archetype = EchelonArchetype(ident["archetype"])

    # Build sub-models from YAML sections
    tier_data = data.get("tier_profile", {})
    tier_profile = TierProfile(
        active_tiers=tier_data.get("active_tiers", []),
        default_tier=tier_data.get("default_tier", "T1"),
        escalation_rules=tier_data.get("escalation_rules", []),
        cost_profile=tier_data.get("cost_profile", ""),
        max_inference_budget_per_market=tier_data.get(
            "max_inference_budget_per_market", 0.10
        ),
    )

    dp_data = data.get("decision_policy", {})
    decision_policy = DecisionPolicy(
        method=dp_data.get("method", "SOFTMAX_Q_VALUE"),
        temperature=dp_data.get("temperature", 0.5),
        bias_vector=dp_data.get("bias_vector", {}),
        strategy_rules=dp_data.get("strategy_rules", []),
    )

    pb_data = data.get("paradox_behaviour", {})
    paradox_behaviour = ParadoxBehaviour(
        logic_gap_threshold=pb_data.get("logic_gap_threshold", 0.20),
        response_action=pb_data.get("response_action", "EXTRACT"),
        extraction_cost_ceiling=pb_data.get("extraction_cost_ceiling", 0.25),
        coalition_willingness=pb_data.get("coalition_willingness", 0.15),
        circuit_breaker_behaviour=pb_data.get("circuit_breaker_behaviour", "REDUCE"),
    )

    ica_data = data.get("inquiry_class_affinity", {})
    inquiry_class_affinity = InquiryClassAffinity(
        counterfactual=ica_data.get("counterfactual", 0.5),
        investigative=ica_data.get("investigative", 0.5),
        inspection=ica_data.get("inspection", 0.5),
        survey=ica_data.get("survey", 0.5),
        scrutiny=ica_data.get("scrutiny", 0.5),
    )

    sm_data = data.get("success_metrics", {})
    success_metrics = SuccessMetrics(
        brier_score_target=sm_data.get("brier_score_target", 0.20),
        ece_bound=sm_data.get("ece_bound", 0.10),
        pnl_expectation=sm_data.get("pnl_expectation", "PROFITABLE"),
        consistency_threshold=sm_data.get("consistency_threshold", 0.80),
        position_size_variance_max=sm_data.get("position_size_variance_max", 0.20),
        fork_choice_consistency_min=sm_data.get("fork_choice_consistency_min", 0.80),
    )

    return AgentGenome(
        # Identity
        archetype=archetype,
        variant=ident.get("variant"),
        genome_version=ident.get("version", "1.0.0"),
        name=ident.get("name"),
        agent_id=ident.get("agent_id"),
        lineage=ident.get("lineage", "GENESIS"),
        description=ident.get("description"),
        # 8 economic parameters
        risk_appetite=econ["risk_appetite"],
        evidence_sensitivity=econ["evidence_sensitivity"],
        time_preference=econ["time_preference"],
        exploration_rate=econ["exploration_rate"],
        position_limit=econ["position_limit"],
        sabotage_propensity=econ["sabotage_propensity"],
        shield_propensity=econ["shield_propensity"],
        patience=econ["patience"],
        # Extended sections
        tier_profile=tier_profile,
        decision_policy=decision_policy,
        paradox_behaviour=paradox_behaviour,
        inquiry_class_affinity=inquiry_class_affinity,
        success_metrics=success_metrics,
    )


def load_genome_pack(directory: Path) -> Dict[str, AgentGenome]:
    """Load all genome YAML files from a directory.

    Args:
        directory: Path to directory containing *.yaml genome files.

    Returns:
        Dict mapping agent_id to AgentGenome.
    """
    genomes: Dict[str, AgentGenome] = {}
    for yaml_file in sorted(directory.glob("*.yaml")):
        genome = load_genome(yaml_file)
        key = genome.agent_id or f"{genome.archetype.value}_{genome.variant}"
        genomes[key] = genome
    return genomes


def compute_commitment_hash(genome: AgentGenome) -> str:
    """Compute SHA-256 commitment hash from an AgentGenome instance.

    Must produce identical output to validate_genome.py:compute_commitment_hash()
    when given the same underlying genome data. Uses the same field set and
    pipe-separated serialisation.
    """
    parts = []

    # Identity
    parts.append(str(genome.agent_id or ""))
    parts.append(str(genome.genome_version))

    # 8 economic parameters — normalize integer-valued floats to match
    # the validator's str(int_value) output (position_limit is float in
    # Pydantic but int in YAML; str(15000.0) != str(15000))
    def _s(val: object) -> str:
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        return str(val)

    parts.append(_s(genome.risk_appetite))
    parts.append(_s(genome.evidence_sensitivity))
    parts.append(_s(genome.time_preference))
    parts.append(_s(genome.exploration_rate))
    parts.append(_s(genome.position_limit))
    parts.append(_s(genome.sabotage_propensity))
    parts.append(_s(genome.shield_propensity))
    parts.append(_s(genome.patience))

    # Active tiers (sorted CSV)
    if genome.tier_profile and genome.tier_profile.active_tiers:
        parts.append(",".join(sorted(str(t) for t in genome.tier_profile.active_tiers)))
    else:
        parts.append("")

    # Decision policy
    if genome.decision_policy:
        parts.append(str(genome.decision_policy.method))
        parts.append(str(genome.decision_policy.temperature))
    else:
        parts.append("")
        parts.append("")

    # Paradox behaviour
    if genome.paradox_behaviour:
        parts.append(str(genome.paradox_behaviour.logic_gap_threshold))
        parts.append(str(genome.paradox_behaviour.response_action))
    else:
        parts.append("")
        parts.append("")

    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
