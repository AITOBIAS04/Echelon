"""Tests for Genome Loader -- YAML genome loading and commitment hash.

Covers: single genome load, genome pack, commitment hash matching,
factory backward compat, spawn with YAML, spawn fallback, deterministic
variant selection.

Cycle-014b, Sprint 1 -- Task 6.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from backend.agents.genome import (
    AgentGenome,
    EchelonArchetype,
    create_genome,
)
from backend.agents.genome_loader import (
    compute_commitment_hash,
    load_genome,
    load_genome_pack,
)

GENOME_DIR = Path(__file__).resolve().parents[3] / "grimoires" / "loa" / "genomes"


# ===================================================================
# Load Single Genome
# ===================================================================


class TestLoadSingleGenome:
    """Test loading a single YAML genome file."""

    def test_load_single_genome(self):
        """Load shark_megalodon.yaml and assert all fields populated."""
        filepath = GENOME_DIR / "shark_megalodon.yaml"
        genome = load_genome(filepath)

        # Identity
        assert genome.archetype == EchelonArchetype.SHARK
        assert genome.variant == "MEGALODON"
        assert genome.name == "MEGALODON"
        assert genome.agent_id == "shark_megalodon_v1.0.0"
        assert genome.genome_version == "1.0.0"
        assert genome.lineage == "GENESIS"
        assert genome.description is not None

        # 8 economic parameters match YAML
        assert genome.risk_appetite == 0.90
        assert genome.evidence_sensitivity == 0.80
        assert genome.time_preference == 0.95
        assert genome.exploration_rate == 0.15
        assert genome.position_limit == 15000
        assert genome.sabotage_propensity == 0.30
        assert genome.shield_propensity == 0.10
        assert genome.patience == 30

        # Sub-models populated
        assert genome.tier_profile is not None
        assert genome.tier_profile.active_tiers == ["T1", "T2"]
        assert genome.tier_profile.default_tier == "T1"
        assert len(genome.tier_profile.escalation_rules) == 2
        assert genome.tier_profile.max_inference_budget_per_market == 0.12

        assert genome.decision_policy is not None
        assert genome.decision_policy.method == "SOFTMAX_Q_VALUE"
        assert genome.decision_policy.temperature == 0.3
        assert "buy" in genome.decision_policy.bias_vector
        assert len(genome.decision_policy.strategy_rules) >= 1

        assert genome.paradox_behaviour is not None
        assert genome.paradox_behaviour.logic_gap_threshold == 0.20
        assert genome.paradox_behaviour.response_action == "EXTRACT"

        assert genome.inquiry_class_affinity is not None
        assert genome.inquiry_class_affinity.counterfactual == 0.85

        assert genome.success_metrics is not None
        assert genome.success_metrics.brier_score_target == 0.18
        assert genome.success_metrics.pnl_expectation == "PROFITABLE"

        # Frozen
        with pytest.raises(Exception):
            genome.variant = "OTHER"


# ===================================================================
# Load Genome Pack
# ===================================================================


class TestLoadGenomePack:
    """Test loading all genomes from a directory."""

    def test_load_genome_pack(self):
        """Load all 4 genomes, assert 4 entries with unique agent_ids."""
        pack = load_genome_pack(GENOME_DIR)

        assert len(pack) == 4
        agent_ids = set(pack.keys())
        assert len(agent_ids) == 4

        # Each should be a valid AgentGenome
        for agent_id, genome in pack.items():
            assert isinstance(genome, AgentGenome)
            assert genome.archetype in EchelonArchetype


# ===================================================================
# Commitment Hash
# ===================================================================


class TestCommitmentHash:
    """Test commitment hash matches between runtime and validator."""

    def test_commitment_hash_matches_validator(self):
        """For each YAML genome, runtime hash must match validator hash."""
        # Import validator's compute_commitment_hash
        sys.path.insert(0, str(GENOME_DIR))
        try:
            from validate_genome import (
                compute_commitment_hash as val_hash,
                parse_yaml,
            )
        finally:
            sys.path.pop(0)

        for yaml_file in sorted(GENOME_DIR.glob("*.yaml")):
            # Runtime hash
            genome = load_genome(yaml_file)
            runtime_h = compute_commitment_hash(genome)

            # Validator hash
            with open(yaml_file) as f:
                data = parse_yaml(f.read())
            validator_h = val_hash(data)

            assert runtime_h == validator_h, (
                f"Hash mismatch for {yaml_file.name}: "
                f"runtime={runtime_h[:16]} validator={validator_h[:16]}"
            )


# ===================================================================
# Factory Backward Compat
# ===================================================================


class TestFactoryBackwardCompat:
    """Test that the factory path is unchanged."""

    def test_factory_still_works(self):
        """create_genome(SHARK) still returns valid genome unchanged."""
        genome = create_genome(EchelonArchetype.SHARK)

        assert genome.archetype == EchelonArchetype.SHARK
        assert genome.risk_appetite == 0.85
        assert genome.position_limit == 10_000
        assert genome.patience == 30
        assert genome.variant is None

        # New optional fields default to None
        assert genome.tier_profile is None
        assert genome.decision_policy is None
        assert genome.name is None
        assert genome.agent_id is None


# ===================================================================
# Spawn Integration
# ===================================================================


class TestSpawnIntegration:
    """Test spawn_agents with and without genome_dir."""

    def test_spawn_with_yaml_genomes(self):
        """spawn_agents() with genome_dir loads genomes from YAML."""
        from backend.services.agent_theatre_bridge import AgentTheatreBridge

        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_yaml_test",
            archetypes=[EchelonArchetype.SHARK],
            genome_dir=GENOME_DIR,
        )

        assert len(agents) == 1
        genome = agents[0].genome
        # YAML genome has variant populated
        assert genome.variant == "MEGALODON"
        assert genome.agent_id == "shark_megalodon_v1.0.0"
        assert genome.risk_appetite == 0.90

    def test_spawn_fallback_no_yaml(self):
        """spawn_agents() without genome_dir uses factory fallback."""
        from backend.services.agent_theatre_bridge import AgentTheatreBridge

        bridge = AgentTheatreBridge()
        agents = bridge.spawn_agents(
            theatre_id="theatre_factory_test",
            archetypes=[EchelonArchetype.SHARK],
        )

        assert len(agents) == 1
        genome = agents[0].genome
        # Factory genome has no variant
        assert genome.variant is None
        assert genome.risk_appetite == 0.85  # Factory default

    def test_spawn_fallback_missing_archetype(self):
        """Archetypes not in YAML pack fall back to factory."""
        from backend.services.agent_theatre_bridge import AgentTheatreBridge

        bridge = AgentTheatreBridge()
        # GENOME_DIR has SHARK, SPY, SABOTEUR, WHALE — no DIPLOMAT or DEGEN
        agents = bridge.spawn_agents(
            theatre_id="theatre_mixed_test",
            archetypes=[EchelonArchetype.DIPLOMAT, EchelonArchetype.SHARK],
            genome_dir=GENOME_DIR,
        )

        assert len(agents) == 2
        diplomat = next(a for a in agents if a.genome.archetype == EchelonArchetype.DIPLOMAT)
        shark = next(a for a in agents if a.genome.archetype == EchelonArchetype.SHARK)

        # Diplomat falls back to factory
        assert diplomat.genome.variant is None
        # Shark uses YAML
        assert shark.genome.variant == "MEGALODON"


# ===================================================================
# Deterministic Variant Selection
# ===================================================================


class TestDeterministicVariantSelection:
    """Test deterministic selection when multiple variants exist."""

    def _make_two_variant_dir(self, tmpdir: Path) -> None:
        """Create a temp dir with two SHARK variants.

        Filenames are intentionally reversed relative to agent_id lexical
        order to prove selection uses sorted agent_id, not filename order.
        - zzz_second.yaml  → agent_id "shark_hammerhead_v1.0.0" (sorts first)
        - aaa_first.yaml   → agent_id "shark_megalodon_v1.0.0" (sorts second)
        """
        with open(GENOME_DIR / "shark_megalodon.yaml") as f:
            base = f.read()

        hammerhead = base.replace("MEGALODON", "HAMMERHEAD").replace(
            "megalodon", "hammerhead"
        )
        # File named "zzz" but agent_id "shark_hammerhead" sorts first
        (tmpdir / "zzz_second.yaml").write_text(hammerhead)
        # File named "aaa" but agent_id "shark_megalodon" sorts second
        (tmpdir / "aaa_first.yaml").write_text(base)

    def test_deterministic_variant_selection_stable(self):
        """Selection among multiple variants is stable across repeated runs."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_two_variant_dir(tmpdir)

            from backend.services.agent_theatre_bridge import AgentTheatreBridge

            results = []
            for _ in range(5):
                bridge = AgentTheatreBridge()
                agents = bridge.spawn_agents(
                    theatre_id="theatre_det_test",
                    archetypes=[EchelonArchetype.SHARK],
                    genome_dir=tmpdir,
                )
                results.append(agents[0].genome.variant)

            assert len(set(results)) == 1, f"Non-deterministic selection: {results}"

    def test_variant_selection_uses_sorted_agent_id(self):
        """Selection is based on sorted agent_id order, not filename order.

        Creates files where filename order (aaa < zzz) is the reverse of
        agent_id order (hammerhead < megalodon). Verifies the chosen variant
        is consistent with indexing into agent_id-sorted candidates.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_two_variant_dir(tmpdir)

            from backend.services.agent_theatre_bridge import AgentTheatreBridge

            theatre_id = "theatre_order_test"
            bridge = AgentTheatreBridge()
            agents = bridge.spawn_agents(
                theatre_id=theatre_id,
                archetypes=[EchelonArchetype.SHARK],
                genome_dir=tmpdir,
            )

            chosen = agents[0].genome

            # Compute expected index from canonical sorted order
            canonical_ids = sorted(["shark_hammerhead_v1.0.0", "shark_megalodon_v1.0.0"])
            digest = hashlib.sha256(
                f"{theatre_id}:{EchelonArchetype.SHARK.value}".encode()
            ).digest()
            idx = int.from_bytes(digest[:4], "big") % len(canonical_ids)
            expected_id = canonical_ids[idx]

            assert chosen.agent_id == expected_id, (
                f"Expected agent_id={expected_id} (idx={idx} into {canonical_ids}), "
                f"got {chosen.agent_id}"
            )
