"""
Agent Genealogy System
======================

Manages agent lineages, breeding mechanics, and trait inheritance.
Creates long-term attachment through evolving agent families.

Features:
- Genesis agents as founding members each season
- Performance tracking: accuracy, profitability, survival rate
- Breeding events at milestones (VRF-determined)
- Trait inheritance with mutation probability
- Sleeper genes that skip generations

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class AgentArchetype(str, Enum):
    """Core agent archetypes."""
    SHARK = "shark"
    SPY = "spy"
    DIPLOMAT = "diplomat"
    SABOTEUR = "saboteur"
    WHALE = "whale"
    DEGEN = "degen"
    MOMENTUM = "momentum"
    VALUE = "value"
    CONTRARIAN = "contrarian"
    RAT = "rat"


class TraitCategory(str, Enum):
    """Categories of inheritable traits."""
    TRADING = "trading"
    INTELLIGENCE = "intelligence"
    SOCIAL = "social"
    SPECIAL = "special"


class TraitRarity(str, Enum):
    """Trait rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""
    ACTIVE = "active"
    BREEDING = "breeding"
    RETIRED = "retired"
    EXTINCT = "extinct"
    ENDANGERED = "endangered"


# =============================================================================
# TRAIT DEFINITIONS
# =============================================================================

ARCHETYPE_TRAITS = {
    AgentArchetype.SHARK: {
        "base_traits": ["aggression", "speed", "market_sense"],
        "mutations": ["frenzy_mode", "blood_scent", "pack_hunter"],
        "inheritable": ["aggression", "speed", "risk_tolerance"],
    },
    AgentArchetype.SPY: {
        "base_traits": ["accuracy", "discretion", "source_network"],
        "mutations": ["deep_cover", "double_agent", "intel_synthesis"],
        "inheritable": ["accuracy", "discretion", "patience"],
    },
    AgentArchetype.DIPLOMAT: {
        "base_traits": ["charisma", "negotiation", "loyalty"],
        "mutations": ["silver_tongue", "alliance_builder", "treaty_breaker"],
        "inheritable": ["charisma", "negotiation", "trust_rating"],
    },
    AgentArchetype.SABOTEUR: {
        "base_traits": ["deception", "patience", "dormancy"],
        "mutations": ["sleeper", "mole", "chaos_agent"],
        "inheritable": ["deception", "patience", "infiltration"],
        "sleeper_gene": True,  # Can skip 2-3 generations
    },
}


class AgentTrait(BaseModel):
    """A single trait an agent possesses."""
    
    name: str = Field(..., description="Trait identifier")
    category: TraitCategory = Field(...)
    rarity: TraitRarity = Field(TraitRarity.COMMON)
    
    # Trait strength (0-100)
    base_value: int = Field(50, ge=0, le=100)
    current_value: int = Field(50, ge=0, le=100)
    
    # Inheritance
    is_inheritable: bool = Field(True)
    inheritance_chance: float = Field(0.7, ge=0, le=1)
    mutation_chance: float = Field(0.1, ge=0, le=1)
    
    # Special flags
    is_sleeper: bool = Field(False, description="Can skip generations")
    sleeper_countdown: int = Field(0, description="Generations until activation")
    
    # Metadata
    acquired_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field("genesis", description="genesis, inherited, mutated, acquired")


class AgentGenome(BaseModel):
    """Complete genetic profile of an agent."""
    
    genome_id: str = Field(..., description="Unique genome identifier")
    
    # Core identity
    archetype: AgentArchetype = Field(...)
    generation: int = Field(1, description="Generation number (1 = genesis)")
    
    # Traits
    traits: list[AgentTrait] = Field(default_factory=list)
    
    # Lineage
    parent_ids: list[str] = Field(default_factory=list, max_length=2)
    offspring_ids: list[str] = Field(default_factory=list)
    
    # Hidden traits (sleeper genes)
    dormant_traits: list[AgentTrait] = Field(default_factory=list)
    
    # Genome hash for verification
    genome_hash: str = Field("")
    
    def compute_hash(self) -> str:
        """Compute deterministic hash of genome."""
        data = {
            "archetype": self.archetype.value,
            "generation": self.generation,
            "traits": [(t.name, t.base_value) for t in self.traits],
            "parents": self.parent_ids,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def get_trait(self, name: str) -> Optional[AgentTrait]:
        """Get trait by name."""
        for trait in self.traits:
            if trait.name == name:
                return trait
        return None
    
    def get_trait_value(self, name: str, default: int = 50) -> int:
        """Get trait value by name."""
        trait = self.get_trait(name)
        return trait.current_value if trait else default


# =============================================================================
# AGENT IDENTITY
# =============================================================================

class AgentIdentity(BaseModel):
    """Full agent identity with genealogy."""
    
    agent_id: str = Field(..., description="Unique agent identifier")
    
    # Display info
    name: str = Field(..., description="Agent display name")
    codename: Optional[str] = Field(None, description="Secret codename")
    avatar_seed: str = Field("", description="Seed for avatar generation")
    
    # Genome
    genome: AgentGenome = Field(...)
    
    # Performance
    performance: "AgentPerformanceMetrics" = Field(default_factory=lambda: AgentPerformanceMetrics())
    
    # Status
    status: AgentStatus = Field(AgentStatus.ACTIVE)
    
    # Breeding
    breeding_points: int = Field(0, description="Points toward next breeding")
    breeding_threshold: int = Field(1000, description="Points needed to breed")
    last_bred_at: Optional[datetime] = Field(None)
    breeding_cooldown_hours: int = Field(168, description="Hours between breeding (1 week)")
    
    # Relationships
    allies: list[str] = Field(default_factory=list)
    rivals: list[str] = Field(default_factory=list)
    
    # Ownership
    owner_address: Optional[str] = Field(None, description="Current owner wallet")
    token_id: Optional[str] = Field(None, description="ERC-6551 token ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retired_at: Optional[datetime] = Field(None)


class AgentPerformanceMetrics(BaseModel):
    """Performance tracking for an agent."""
    
    # Trading metrics
    total_trades: int = Field(0)
    winning_trades: int = Field(0)
    total_volume: Decimal = Field(Decimal("0"))
    realized_pnl: Decimal = Field(Decimal("0"))
    
    # Accuracy (for Spies)
    intel_provided: int = Field(0)
    intel_accurate: int = Field(0)
    
    # Diplomacy (for Diplomats)
    treaties_brokered: int = Field(0)
    treaties_broken: int = Field(0)
    
    # Sabotage (for Saboteurs)
    fud_contributed: Decimal = Field(Decimal("0"))
    successful_sabotages: int = Field(0)
    
    # Survival
    timelines_survived: int = Field(0)
    times_eliminated: int = Field(0)
    
    # Calculated metrics
    @property
    def win_rate(self) -> Decimal:
        if self.total_trades == 0:
            return Decimal("0")
        return Decimal(self.winning_trades) / Decimal(self.total_trades)
    
    @property
    def accuracy(self) -> Decimal:
        if self.intel_provided == 0:
            return Decimal("0")
        return Decimal(self.intel_accurate) / Decimal(self.intel_provided)
    
    @property
    def survival_rate(self) -> Decimal:
        total = self.timelines_survived + self.times_eliminated
        if total == 0:
            return Decimal("1")
        return Decimal(self.timelines_survived) / Decimal(total)


# =============================================================================
# BREEDING MECHANICS
# =============================================================================

class BreedingRequest(BaseModel):
    """Request to breed two agents."""
    
    parent1_id: str
    parent2_id: str
    
    requester_address: str
    
    # VRF for randomness
    vrf_seed: Optional[str] = Field(None)
    vrf_request_id: Optional[str] = Field(None)
    
    # Status
    status: str = Field("pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    
    # Result
    offspring_id: Optional[str] = Field(None)


class BreedingResult(BaseModel):
    """Result of a breeding event."""
    
    offspring: AgentIdentity
    
    # Inheritance details
    inherited_from_parent1: list[str] = Field(default_factory=list)
    inherited_from_parent2: list[str] = Field(default_factory=list)
    mutations: list[str] = Field(default_factory=list)
    activated_sleepers: list[str] = Field(default_factory=list)
    
    # Breeding event metadata
    breeding_request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# GENEALOGY MANAGER
# =============================================================================

class GenealogyManager:
    """
    Manages agent genealogy, breeding, and trait inheritance.
    """
    
    def __init__(
        self,
        vrf_consumer: Optional[Any] = None,
        storage_backend: Optional[Any] = None
    ):
        self.vrf_consumer = vrf_consumer
        self.storage = storage_backend
        
        # In-memory storage
        self._agents: dict[str, AgentIdentity] = {}
        self._breeding_requests: dict[str, BreedingRequest] = {}
        self._family_trees: dict[str, list[str]] = {}  # root_id -> all descendants
    
    # =========================================================================
    # GENESIS AGENTS
    # =========================================================================
    
    async def create_genesis_agent(
        self,
        archetype: AgentArchetype,
        name: str,
        owner_address: Optional[str] = None,
        custom_traits: Optional[list[AgentTrait]] = None
    ) -> AgentIdentity:
        """
        Create a genesis (generation 1) agent.
        
        Genesis agents are the founding members of each season.
        """
        # Generate IDs
        agent_id = self._generate_agent_id(archetype, name)
        genome_id = f"genome_{agent_id}"
        
        # Create base traits from archetype
        traits = custom_traits or self._create_archetype_traits(archetype)
        
        # Create genome
        genome = AgentGenome(
            genome_id=genome_id,
            archetype=archetype,
            generation=1,
            traits=traits,
            parent_ids=[],
            dormant_traits=[]
        )
        genome.genome_hash = genome.compute_hash()
        
        # Create identity
        agent = AgentIdentity(
            agent_id=agent_id,
            name=name,
            avatar_seed=hashlib.sha256(agent_id.encode()).hexdigest()[:8],
            genome=genome,
            status=AgentStatus.ACTIVE,
            owner_address=owner_address
        )
        
        self._agents[agent_id] = agent
        self._family_trees[agent_id] = []  # Genesis agents are roots
        
        return agent
    
    def _create_archetype_traits(self, archetype: AgentArchetype) -> list[AgentTrait]:
        """Create default traits for an archetype."""
        config = ARCHETYPE_TRAITS.get(archetype, {})
        base_traits = config.get("base_traits", [])
        
        traits = []
        for trait_name in base_traits:
            # Randomize initial values slightly
            base_value = random.randint(40, 70)
            
            trait = AgentTrait(
                name=trait_name,
                category=TraitCategory.TRADING,
                rarity=TraitRarity.COMMON,
                base_value=base_value,
                current_value=base_value,
                is_inheritable=trait_name in config.get("inheritable", []),
                source="genesis"
            )
            traits.append(trait)
        
        return traits
    
    # =========================================================================
    # BREEDING
    # =========================================================================
    
    async def request_breeding(
        self,
        parent1_id: str,
        parent2_id: str,
        requester_address: str
    ) -> BreedingRequest:
        """
        Request breeding between two agents.
        
        Requirements:
        - Both parents must be active
        - Both parents must have sufficient breeding points
        - Breeding cooldown must have passed
        - Parents must be compatible (same or compatible archetypes)
        """
        parent1 = self._agents.get(parent1_id)
        parent2 = self._agents.get(parent2_id)
        
        if not parent1 or not parent2:
            raise ValueError("One or both parents not found")
        
        # Validate breeding eligibility
        self._validate_breeding_eligibility(parent1, parent2)
        
        # Create request
        request_id = f"breed_{parent1_id}_{parent2_id}_{int(datetime.utcnow().timestamp())}"
        
        request = BreedingRequest(
            parent1_id=parent1_id,
            parent2_id=parent2_id,
            requester_address=requester_address,
            status="pending"
        )
        
        # Request VRF seed
        if self.vrf_consumer:
            vrf_request = await self.vrf_consumer.request_breeding_seed(request_id)
            request.vrf_request_id = vrf_request
        else:
            # Use deterministic seed for testing
            request.vrf_seed = hashlib.sha256(request_id.encode()).hexdigest()
            request.status = "ready"
        
        self._breeding_requests[request_id] = request
        
        return request
    
    def _validate_breeding_eligibility(
        self,
        parent1: AgentIdentity,
        parent2: AgentIdentity
    ) -> None:
        """Validate that two agents can breed."""
        # Check status
        if parent1.status != AgentStatus.ACTIVE:
            raise ValueError(f"Parent 1 is not active: {parent1.status}")
        if parent2.status != AgentStatus.ACTIVE:
            raise ValueError(f"Parent 2 is not active: {parent2.status}")
        
        # Check breeding points
        if parent1.breeding_points < parent1.breeding_threshold:
            raise ValueError(f"Parent 1 needs more breeding points: {parent1.breeding_points}/{parent1.breeding_threshold}")
        if parent2.breeding_points < parent2.breeding_threshold:
            raise ValueError(f"Parent 2 needs more breeding points: {parent2.breeding_points}/{parent2.breeding_threshold}")
        
        # Check cooldown
        now = datetime.utcnow()
        if parent1.last_bred_at:
            cooldown_end = parent1.last_bred_at + timedelta(hours=parent1.breeding_cooldown_hours)
            if now < cooldown_end:
                raise ValueError(f"Parent 1 still on breeding cooldown until {cooldown_end}")
        
        if parent2.last_bred_at:
            cooldown_end = parent2.last_bred_at + timedelta(hours=parent2.breeding_cooldown_hours)
            if now < cooldown_end:
                raise ValueError(f"Parent 2 still on breeding cooldown until {cooldown_end}")
        
        # Check they're not the same agent
        if parent1.agent_id == parent2.agent_id:
            raise ValueError("Cannot breed agent with itself")
        
        # Check they're not direct parent/child
        if parent1.agent_id in parent2.genome.parent_ids:
            raise ValueError("Cannot breed with direct offspring")
        if parent2.agent_id in parent1.genome.parent_ids:
            raise ValueError("Cannot breed with direct parent")
    
    async def execute_breeding(
        self,
        request_id: str,
        vrf_seed: Optional[str] = None
    ) -> BreedingResult:
        """
        Execute breeding and create offspring.
        
        Uses VRF seed for:
        - Trait inheritance selection
        - Mutation determination
        - Sleeper gene activation
        """
        request = self._breeding_requests.get(request_id)
        if not request:
            raise ValueError("Breeding request not found")
        
        if vrf_seed:
            request.vrf_seed = vrf_seed
        
        if not request.vrf_seed:
            raise ValueError("VRF seed not available")
        
        parent1 = self._agents[request.parent1_id]
        parent2 = self._agents[request.parent2_id]
        
        # Use VRF seed for deterministic randomness
        rng = random.Random(request.vrf_seed)
        
        # Determine offspring archetype
        offspring_archetype = self._determine_offspring_archetype(parent1, parent2, rng)
        
        # Inherit traits
        inherited_traits, inheritance_details = self._inherit_traits(parent1, parent2, rng)
        
        # Check for mutations
        mutated_traits, mutation_names = self._apply_mutations(
            inherited_traits, offspring_archetype, rng
        )
        
        # Check for sleeper gene activation
        activated_sleepers = self._check_sleeper_activation(parent1, parent2, rng)
        
        # Combine all traits
        all_traits = mutated_traits + activated_sleepers
        
        # Generate offspring
        offspring_id = self._generate_agent_id(
            offspring_archetype,
            f"{parent1.name[:3]}_{parent2.name[:3]}_Gen{max(parent1.genome.generation, parent2.genome.generation) + 1}"
        )
        
        offspring_genome = AgentGenome(
            genome_id=f"genome_{offspring_id}",
            archetype=offspring_archetype,
            generation=max(parent1.genome.generation, parent2.genome.generation) + 1,
            traits=all_traits,
            parent_ids=[parent1.agent_id, parent2.agent_id],
            dormant_traits=self._extract_dormant_traits(parent1, parent2, rng)
        )
        offspring_genome.genome_hash = offspring_genome.compute_hash()
        
        offspring_name = self._generate_offspring_name(parent1.name, parent2.name, rng)
        
        offspring = AgentIdentity(
            agent_id=offspring_id,
            name=offspring_name,
            avatar_seed=hashlib.sha256(offspring_id.encode()).hexdigest()[:8],
            genome=offspring_genome,
            status=AgentStatus.ACTIVE
        )
        
        # Update parents
        parent1.genome.offspring_ids.append(offspring_id)
        parent2.genome.offspring_ids.append(offspring_id)
        parent1.last_bred_at = datetime.utcnow()
        parent2.last_bred_at = datetime.utcnow()
        parent1.breeding_points = 0  # Reset breeding points
        parent2.breeding_points = 0
        
        # Store offspring
        self._agents[offspring_id] = offspring
        
        # Update family trees
        for parent in [parent1, parent2]:
            for root_id, descendants in self._family_trees.items():
                if parent.agent_id == root_id or parent.agent_id in descendants:
                    descendants.append(offspring_id)
        
        # Complete request
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.offspring_id = offspring_id
        
        return BreedingResult(
            offspring=offspring,
            inherited_from_parent1=inheritance_details["parent1"],
            inherited_from_parent2=inheritance_details["parent2"],
            mutations=mutation_names,
            activated_sleepers=[t.name for t in activated_sleepers],
            breeding_request_id=request_id
        )
    
    def _determine_offspring_archetype(
        self,
        parent1: AgentIdentity,
        parent2: AgentIdentity,
        rng: random.Random
    ) -> AgentArchetype:
        """Determine offspring archetype from parents."""
        # 40% chance each parent's archetype, 20% mutation to related
        roll = rng.random()
        
        if roll < 0.4:
            return parent1.genome.archetype
        elif roll < 0.8:
            return parent2.genome.archetype
        else:
            # Rare mutation to different archetype
            all_archetypes = list(AgentArchetype)
            return rng.choice(all_archetypes)
    
    def _inherit_traits(
        self,
        parent1: AgentIdentity,
        parent2: AgentIdentity,
        rng: random.Random
    ) -> tuple[list[AgentTrait], dict]:
        """Inherit traits from parents."""
        inherited_traits = []
        details = {"parent1": [], "parent2": []}
        
        # Collect all inheritable traits
        p1_traits = {t.name: t for t in parent1.genome.traits if t.is_inheritable}
        p2_traits = {t.name: t for t in parent2.genome.traits if t.is_inheritable}
        
        all_trait_names = set(p1_traits.keys()) | set(p2_traits.keys())
        
        for trait_name in all_trait_names:
            p1_trait = p1_traits.get(trait_name)
            p2_trait = p2_traits.get(trait_name)
            
            # Determine inheritance
            if p1_trait and p2_trait:
                # Both parents have trait - blend values
                if rng.random() < 0.5:
                    source_trait = p1_trait
                    details["parent1"].append(trait_name)
                else:
                    source_trait = p2_trait
                    details["parent2"].append(trait_name)
                
                # Blend values with small variation
                blended_value = (p1_trait.current_value + p2_trait.current_value) // 2
                variation = rng.randint(-10, 10)
                new_value = max(0, min(100, blended_value + variation))
                
            elif p1_trait:
                source_trait = p1_trait
                details["parent1"].append(trait_name)
                new_value = p1_trait.current_value + rng.randint(-5, 5)
                
            else:
                source_trait = p2_trait
                details["parent2"].append(trait_name)
                new_value = p2_trait.current_value + rng.randint(-5, 5)
            
            # Check if trait is inherited (based on inheritance chance)
            if rng.random() < source_trait.inheritance_chance:
                new_trait = AgentTrait(
                    name=trait_name,
                    category=source_trait.category,
                    rarity=source_trait.rarity,
                    base_value=new_value,
                    current_value=new_value,
                    is_inheritable=source_trait.is_inheritable,
                    inheritance_chance=source_trait.inheritance_chance,
                    mutation_chance=source_trait.mutation_chance,
                    is_sleeper=source_trait.is_sleeper,
                    source="inherited"
                )
                inherited_traits.append(new_trait)
        
        return inherited_traits, details
    
    def _apply_mutations(
        self,
        traits: list[AgentTrait],
        archetype: AgentArchetype,
        rng: random.Random
    ) -> tuple[list[AgentTrait], list[str]]:
        """Apply mutations to inherited traits."""
        mutation_names = []
        config = ARCHETYPE_TRAITS.get(archetype, {})
        possible_mutations = config.get("mutations", [])
        
        # Check each trait for mutation
        for trait in traits:
            if rng.random() < trait.mutation_chance:
                # Mutate the trait value
                mutation_delta = rng.randint(-20, 30)  # Mutations can be positive
                trait.current_value = max(0, min(100, trait.current_value + mutation_delta))
                trait.source = "mutated"
                mutation_names.append(f"{trait.name}_mutated")
        
        # Chance for entirely new mutation trait
        if possible_mutations and rng.random() < 0.15:  # 15% chance
            mutation_name = rng.choice(possible_mutations)
            
            mutation_trait = AgentTrait(
                name=mutation_name,
                category=TraitCategory.SPECIAL,
                rarity=TraitRarity.RARE,
                base_value=rng.randint(60, 90),
                current_value=rng.randint(60, 90),
                is_inheritable=True,
                inheritance_chance=0.5,
                mutation_chance=0.05,
                source="mutated"
            )
            traits.append(mutation_trait)
            mutation_names.append(mutation_name)
        
        return traits, mutation_names
    
    def _check_sleeper_activation(
        self,
        parent1: AgentIdentity,
        parent2: AgentIdentity,
        rng: random.Random
    ) -> list[AgentTrait]:
        """Check for sleeper gene activation from grandparents."""
        activated = []
        
        # Check dormant traits from both parents
        for parent in [parent1, parent2]:
            for dormant in parent.genome.dormant_traits:
                if dormant.is_sleeper:
                    # Reduce countdown
                    dormant.sleeper_countdown -= 1
                    
                    if dormant.sleeper_countdown <= 0:
                        # Activate!
                        activated_trait = AgentTrait(
                            name=dormant.name,
                            category=dormant.category,
                            rarity=TraitRarity.EPIC,  # Activated sleepers are epic
                            base_value=dormant.base_value,
                            current_value=dormant.base_value,
                            is_inheritable=True,
                            is_sleeper=False,  # No longer sleeper
                            source="sleeper_activated"
                        )
                        activated.append(activated_trait)
        
        return activated
    
    def _extract_dormant_traits(
        self,
        parent1: AgentIdentity,
        parent2: AgentIdentity,
        rng: random.Random
    ) -> list[AgentTrait]:
        """Extract dormant traits to pass to offspring."""
        dormant = []
        
        # Check for saboteur lineage (sleeper genes)
        for parent in [parent1, parent2]:
            if parent.genome.archetype == AgentArchetype.SABOTEUR:
                config = ARCHETYPE_TRAITS.get(AgentArchetype.SABOTEUR, {})
                if config.get("sleeper_gene"):
                    # Create dormant saboteur trait
                    sleeper = AgentTrait(
                        name="hidden_saboteur",
                        category=TraitCategory.SPECIAL,
                        rarity=TraitRarity.LEGENDARY,
                        base_value=80,
                        current_value=80,
                        is_inheritable=True,
                        is_sleeper=True,
                        sleeper_countdown=rng.randint(2, 3),  # Skip 2-3 generations
                        source="sleeper_dormant"
                    )
                    dormant.append(sleeper)
        
        return dormant
    
    def _generate_offspring_name(
        self,
        parent1_name: str,
        parent2_name: str,
        rng: random.Random
    ) -> str:
        """Generate a name for offspring."""
        prefixes = ["Neo", "Alpha", "Prime", "Ultra", "Mega", "Omni"]
        suffixes = ["II", "III", "Jr", "Prime", "X", "Zero"]
        
        # Combine parts of parent names
        if rng.random() < 0.3:
            # Use parent name with suffix
            base = rng.choice([parent1_name, parent2_name])
            return f"{base} {rng.choice(suffixes)}"
        else:
            # Create new name
            prefix = rng.choice(prefixes)
            # Take syllables from parents
            p1_part = parent1_name[:3].upper()
            p2_part = parent2_name[:3].upper()
            return f"{prefix}-{p1_part}{p2_part}"
    
    def _generate_agent_id(self, archetype: AgentArchetype, name: str) -> str:
        """Generate unique agent ID."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        data = f"{archetype.value}:{name}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    async def get_family_tree(self, root_id: str) -> dict:
        """Get complete family tree for an agent."""
        agent = self._agents.get(root_id)
        if not agent:
            return {}
        
        tree = {
            "agent": agent,
            "parents": [],
            "offspring": [],
            "siblings": []
        }
        
        # Get parents
        for parent_id in agent.genome.parent_ids:
            parent = self._agents.get(parent_id)
            if parent:
                tree["parents"].append(parent)
        
        # Get offspring
        for offspring_id in agent.genome.offspring_ids:
            offspring = self._agents.get(offspring_id)
            if offspring:
                tree["offspring"].append(offspring)
        
        # Get siblings (share at least one parent)
        for parent_id in agent.genome.parent_ids:
            parent = self._agents.get(parent_id)
            if parent:
                for sibling_id in parent.genome.offspring_ids:
                    if sibling_id != root_id:
                        sibling = self._agents.get(sibling_id)
                        if sibling and sibling not in tree["siblings"]:
                            tree["siblings"].append(sibling)
        
        return tree
    
    async def get_lineage_depth(self, agent_id: str) -> int:
        """Get how many generations back this lineage goes."""
        agent = self._agents.get(agent_id)
        if not agent:
            return 0
        
        return agent.genome.generation
    
    async def get_endangered_agents(self) -> list[AgentIdentity]:
        """Get agents at risk of extinction."""
        endangered = []
        
        for agent in self._agents.values():
            if agent.status == AgentStatus.ACTIVE:
                # Check survival rate
                if agent.performance.survival_rate < Decimal("0.5"):
                    # Less than 50% survival over recent timelines
                    endangered.append(agent)
                    agent.status = AgentStatus.ENDANGERED
        
        return endangered
    
    async def add_breeding_points(
        self,
        agent_id: str,
        points: int,
        reason: str = "performance"
    ) -> AgentIdentity:
        """Add breeding points to an agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError("Agent not found")
        
        agent.breeding_points += points
        
        return agent


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of genealogy system."""
    
    manager = GenealogyManager()
    
    # Create genesis agents
    shark = await manager.create_genesis_agent(
        archetype=AgentArchetype.SHARK,
        name="MEGALODON",
        owner_address="0xOwner1"
    )
    print(f"Created genesis shark: {shark.name}")
    
    spy = await manager.create_genesis_agent(
        archetype=AgentArchetype.SPY,
        name="CARDINAL",
        owner_address="0xOwner2"
    )
    print(f"Created genesis spy: {spy.name}")
    
    # Simulate performance to earn breeding points
    shark.breeding_points = 1000
    spy.breeding_points = 1000
    
    # Request breeding
    request = await manager.request_breeding(
        parent1_id=shark.agent_id,
        parent2_id=spy.agent_id,
        requester_address="0xBreeder"
    )
    print(f"Breeding request: {request.status}")
    
    # Execute breeding
    result = await manager.execute_breeding(
        request_id=f"breed_{shark.agent_id}_{spy.agent_id}_{int(datetime.utcnow().timestamp())}",
        vrf_seed="test_seed_12345"
    )
    
    print(f"Offspring: {result.offspring.name}")
    print(f"Archetype: {result.offspring.genome.archetype}")
    print(f"Generation: {result.offspring.genome.generation}")
    print(f"Inherited from parent1: {result.inherited_from_parent1}")
    print(f"Inherited from parent2: {result.inherited_from_parent2}")
    print(f"Mutations: {result.mutations}")
    
    # Get family tree
    tree = await manager.get_family_tree(result.offspring.agent_id)
    print(f"Parents: {[p.name for p in tree['parents']]}")


if __name__ == "__main__":
    asyncio.run(example_usage())
