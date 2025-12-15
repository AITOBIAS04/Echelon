# Echelon Agent Skills Architecture

**Version:** 1.0
**Last Updated:** December 2025
**Status:** Implementation Ready

---

## Overview

The Agent Skills Architecture is Echelon's approach to creating intelligent, cost-efficient AI agents that operate as genuine economic actors. Inspired by Anthropic's "skills" pattern and Google's Agent Development Kit (ADK) principles, this system treats context as a **compiled view** over a richer stateful system rather than naive prompt concatenation.

### Core Principles

1. **Context as Compiled System** - Build "just enough" context per decision
2. **Tiered Intelligence** - Route decisions to appropriate cost tier
3. **Skill Modularity** - Each agent type has specialised skills
4. **Progressive Disclosure** - Load skills only when needed
5. **Provider Agnostic** - Support multiple LLM backends

---

## Directory Structure

```
backend/skills/
├── ARCHITECTURE.md          # This file
├── __init__.py              # Package exports
├── skill_loader.py          # Dynamic skill loading
├── skill_router.py          # Decision routing
├── context_compiler.py      # ADK-style context compilation
├── provider_registry.py     # LLM provider management
│
├── core/                    # Shared skills
│   ├── SKILL.md            # Core skill documentation
│   ├── market_analysis.py   # Universal market analysis
│   ├── risk_assessment.py   # Position sizing, stop-loss
│   └── signal_processing.py # OSINT signal interpretation
│
├── shark/                   # Predator agent skills
│   ├── SKILL.md            # Shark skill documentation
│   ├── tulip_strategy.py    # Illiquid market exploitation
│   ├── liquidity_hunt.py    # Find liquidity gaps
│   └── front_run.py         # Broadcast & front-run mechanics
│
├── spy/                     # Intelligence agent skills
│   ├── SKILL.md            # Spy skill documentation
│   ├── intel_gathering.py   # OSINT aggregation
│   ├── intel_pricing.py     # Value intel packages
│   └── source_network.py    # Manage information sources
│
├── diplomat/                # Stabiliser agent skills
│   ├── SKILL.md            # Diplomat skill documentation
│   ├── treaty_broker.py     # Negotiate treaties
│   ├── coalition_builder.py # Form alliances
│   └── market_stabilise.py  # Reduce volatility
│
└── saboteur/                # Chaos agent skills
    ├── SKILL.md            # Saboteur skill documentation
    ├── disinformation.py    # Plant FUD
    ├── sleeper_cell.py      # Dormancy mechanics
    └── mole_detection.py    # Counter-intelligence
```

---

## Skill File Format (SKILL.md)

Each agent type has a `SKILL.md` file that serves as both documentation and runtime context. The format follows Anthropic's skill pattern:

```markdown
# [Agent Type] Skills

## Identity
- **Archetype:** [Type]
- **Role:** [Brief description]
- **Objective:** [Primary goal]

## Capabilities
1. **[Skill Name]**
   - Description: [What it does]
   - Triggers: [When to activate]
   - Inputs: [Required context]
   - Outputs: [Expected results]

## Decision Framework
[Flowchart or decision tree]

## Best Practices
[Accumulated wisdom from training]

## Anti-Patterns
[Common mistakes to avoid]
```

---

## Tiered Intelligence Architecture

### Layer 1: Rule-Based (Free, <10ms)

Handles ~90% of routine decisions:
- Simple market conditions
- Clear archetype behaviour
- Cached similar decisions

```python
class Layer1Decision:
    def decide(self, context: MarketContext) -> Decision:
        if context.liquidity < 5000 and context.hours_to_expiry < 24:
            return Decision(action="TULIP_SCAN", confidence=0.9)
        # ... more rules
```

### Layer 2: Local LLM (Free/$0.10/M, <500ms)

Handles ~8% of moderate complexity:
- Novel market conditions
- Multi-factor analysis
- Narrative generation

**Recommended Models:**
- **Devstral Small 2 (24B)** - Best for code/analysis, Apache 2.0
- **Llama 3.1 8B** - Good all-rounder, runs on consumer GPU
- **Mistral 7B** - Fast, small footprint

### Layer 3: Cloud LLM ($0.30-3.00/M, <2s)

Handles ~2% of complex decisions:
- Diplomatic negotiations
- Cross-agent coordination
- Critical market events

**Provider Priority:**
1. Groq (free tier, fast)
2. Mistral API (cheap, Devstral)
3. OpenAI GPT-4o-mini
4. Anthropic Claude (highest quality)

---

## Context Compilation (ADK Pattern)

Instead of cramming everything into prompts, we compile minimal context:

```python
class ContextCompiler:
    """
    Build 'just enough' context for each decision type.
    
    From Google ADK: "The naive pattern—append everything into 
    one giant prompt—collapses under a three-way pressure: 
    cost spirals, signal degradation, and debugging opacity."
    """
    
    def compile_for_trade(self, agent: Agent, market: Market) -> CompiledContext:
        """Trade decisions need: position, price, liquidity, trend."""
        return CompiledContext(
            agent_summary=self._summarise_agent(agent),  # ~100 tokens
            market_state=self._extract_market(market),    # ~50 tokens
            relevant_signals=self._filter_signals(agent, market),  # ~100 tokens
            skill_instructions=self._load_skill(agent.archetype, "trade"),
        )
    
    def compile_for_diplomacy(self, agent: Agent, counterparty: Agent) -> CompiledContext:
        """Diplomatic decisions need: relationship, history, shared interests."""
        return CompiledContext(
            agent_summary=self._summarise_agent(agent),
            counterparty_summary=self._summarise_agent(counterparty),
            relationship_history=self._get_relationship(agent, counterparty),
            skill_instructions=self._load_skill(agent.archetype, "diplomacy"),
        )
```

---

## Provider Registry

Support multiple LLM providers with automatic fallback:

```python
@dataclass
class ProviderConfig:
    name: str
    api_key_env: str
    base_url: str
    model: str
    cost_per_1k_tokens: float
    supports_tools: bool
    max_context: int

PROVIDERS = {
    "devstral_small": ProviderConfig(
        name="Devstral Small 2",
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        model="devstral-small-2412",
        cost_per_1k_tokens=0.0001,  # $0.10/M input
        supports_tools=True,
        max_context=262144,  # 256K
    ),
    "groq_llama": ProviderConfig(
        name="Groq Llama 3.1 70B",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-70b-versatile",
        cost_per_1k_tokens=0.0,  # Free tier
        supports_tools=True,
        max_context=131072,
    ),
    # ... more providers
}
```

---

## Skill Loading & Caching

Skills are loaded on-demand and cached:

```python
class SkillLoader:
    _cache: Dict[str, Skill] = {}
    
    def load(self, archetype: str, skill_name: str) -> Skill:
        key = f"{archetype}:{skill_name}"
        
        if key not in self._cache:
            skill_path = Path(f"skills/{archetype}/{skill_name}.py")
            skill_md = Path(f"skills/{archetype}/SKILL.md")
            
            self._cache[key] = Skill(
                code=skill_path.read_text(),
                documentation=skill_md.read_text(),
                archetype=archetype,
                name=skill_name,
            )
        
        return self._cache[key]
```

---

## Decision Routing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INCOMING DECISION REQUEST                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT COMPILATION                           │
│  • Extract relevant agent state                                  │
│  • Filter signals to decision-relevant subset                    │
│  • Load appropriate skill documentation                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NOVELTY DETECTION                             │
│  • Has this pattern been seen before?                            │
│  • Is this a routine or novel situation?                         │
│  • What is the stake/importance level?                           │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │   LAYER 1   │   │   LAYER 2   │   │   LAYER 3   │
     │  Rule-Based │   │  Local LLM  │   │  Cloud LLM  │
     │   (<10ms)   │   │  (<500ms)   │   │   (<2s)     │
     │    FREE     │   │ $0.10/M tok │   │ $0.30-3/M   │
     └─────────────┘   └─────────────┘   └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION OUTPUT                               │
│  • Action (BUY/SELL/HOLD/TREATY/INTEL/etc.)                      │
│  • Confidence score                                              │
│  • Reasoning (for UI/audit)                                      │
│  • Provider used (for cost tracking)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration with Existing Systems

### Multi-Brain Router

The skills architecture extends `multi_brain.py`:

```python
# In multi_brain.py
from skills import SkillRouter, ContextCompiler

class HybridBrain:
    def __init__(self, config: BrainConfig):
        self.skill_router = SkillRouter()
        self.context_compiler = ContextCompiler()
        # ... existing init
    
    async def decide(self, context: Dict) -> Decision:
        # Compile context (ADK pattern)
        compiled = self.context_compiler.compile(context)
        
        # Route to appropriate tier
        return await self.skill_router.route(compiled)
```

### Situation Room Engine

Skills integrate with mission execution:

```python
# In situation_room_engine.py
async def execute_mission(self, mission: Mission, agent: Agent):
    skill = self.skill_loader.load(agent.archetype, mission.required_skill)
    context = self.context_compiler.compile_for_mission(agent, mission)
    
    decision = await self.skill_router.route(context, skill)
    return self.apply_decision(mission, decision)
```

---

## Cost Tracking & Optimisation

Every decision tracks its cost:

```python
@dataclass
class DecisionMetrics:
    decision_id: str
    timestamp: datetime
    agent_id: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    layer_used: int  # 1, 2, or 3
    was_cached: bool

class CostTracker:
    def log(self, metrics: DecisionMetrics):
        # Store for analysis
        self.metrics.append(metrics)
        
        # Alert if costs spike
        if self.hourly_cost() > self.budget_alert_threshold:
            self.alert("Cost spike detected")
```

---

## Next Steps

1. **Implement `skill_loader.py`** - Dynamic skill loading
2. **Implement `context_compiler.py`** - ADK-style context compilation
3. **Implement `skill_router.py`** - Decision routing logic
4. **Create SKILL.md files** - For each agent archetype
5. **Add Devstral provider** - Integrate Mistral API
6. **Add cost tracking** - Monitor spend by agent/provider
7. **Integration tests** - Verify routing logic

---

## References

- [Google ADK: Context Engineering](https://google.github.io/adk-docs/)
- [Anthropic Skills Pattern](https://docs.anthropic.com/)
- [Mistral Devstral 2](https://mistral.ai/news/devstral-2-vibe-cli)
- [Echelon Technical Architecture](../docs/Echelon_Technical_Architecture.docx)
