"""
Skill Loader
============

Dynamic skill loading with caching and validation.

Skills are stored as SKILL.md files that contain:
1. Agent identity and role description
2. Capability definitions
3. Decision frameworks
4. Best practices
5. Anti-patterns to avoid

The loader reads these files and makes them available
to the context compiler and skill router.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


# =============================================================================
# SKILL MODEL
# =============================================================================

@dataclass
class Skill:
    """A loaded skill with metadata and content."""
    
    archetype: str              # e.g., "shark", "spy"
    name: str                   # e.g., "tulip_strategy", "intel_gathering"
    
    # Content
    documentation: str          # Full SKILL.md content
    code_module: Optional[str] = None  # Python code if available
    
    # Extracted sections
    identity: str = ""
    capabilities: List[str] = field(default_factory=list)
    decision_framework: str = ""
    best_practices: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    
    # Metadata
    loaded_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None
    
    @property
    def prompt_context(self) -> str:
        """Get the skill as context for LLM prompts."""
        sections = []
        
        if self.identity:
            sections.append(f"## Identity\n{self.identity}")
        
        if self.capabilities:
            sections.append("## Capabilities\n" + "\n".join(f"- {c}" for c in self.capabilities))
        
        if self.decision_framework:
            sections.append(f"## Decision Framework\n{self.decision_framework}")
        
        if self.best_practices:
            sections.append("## Best Practices\n" + "\n".join(f"- {p}" for p in self.best_practices))
        
        return "\n\n".join(sections)
    
    @property
    def compressed_context(self) -> str:
        """Get a compressed version for token-limited contexts."""
        # Just identity + decision framework
        return f"{self.identity}\n\n{self.decision_framework}"


# =============================================================================
# SKILL LOADER
# =============================================================================

class SkillLoader:
    """
    Loads and caches skills from SKILL.md files.
    
    Example:
        loader = SkillLoader()
        skill = loader.load("shark", "tulip_strategy")
        print(skill.prompt_context)
    """
    
    def __init__(self, skills_path: Optional[Path] = None):
        self.skills_path = skills_path or Path(__file__).parent
        self._cache: Dict[str, Skill] = {}
    
    def load(self, archetype: str, skill_name: str = "main") -> Skill:
        """
        Load a skill by archetype and name.
        
        Args:
            archetype: Agent type (shark, spy, diplomat, saboteur, core)
            skill_name: Specific skill (default: main SKILL.md)
        
        Returns:
            Loaded Skill object
        """
        cache_key = f"{archetype}:{skill_name}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load SKILL.md
        skill_md_path = self.skills_path / archetype / "SKILL.md"
        documentation = ""
        
        if skill_md_path.exists():
            documentation = skill_md_path.read_text()
        else:
            documentation = self._get_default_skill(archetype)
        
        # Load code module if available
        code_module = None
        if skill_name != "main":
            code_path = self.skills_path / archetype / f"{skill_name}.py"
            if code_path.exists():
                code_module = code_path.read_text()
        
        # Parse the documentation
        skill = self._parse_skill_md(
            archetype=archetype,
            name=skill_name,
            documentation=documentation,
            code_module=code_module,
            file_path=str(skill_md_path) if skill_md_path.exists() else None,
        )
        
        self._cache[cache_key] = skill
        return skill
    
    def load_all(self, archetype: str) -> List[Skill]:
        """Load all skills for an archetype."""
        skills = []
        archetype_path = self.skills_path / archetype
        
        if not archetype_path.exists():
            return [self.load(archetype)]
        
        # Load main SKILL.md
        skills.append(self.load(archetype))
        
        # Load any .py skill modules
        for py_file in archetype_path.glob("*.py"):
            if py_file.stem != "__init__":
                skill_name = py_file.stem
                skills.append(self.load(archetype, skill_name))
        
        return skills
    
    def get_available_archetypes(self) -> List[str]:
        """Get list of available agent archetypes."""
        archetypes = []
        
        for path in self.skills_path.iterdir():
            if path.is_dir() and not path.name.startswith("_"):
                archetypes.append(path.name)
        
        return sorted(archetypes)
    
    def _parse_skill_md(
        self,
        archetype: str,
        name: str,
        documentation: str,
        code_module: Optional[str],
        file_path: Optional[str],
    ) -> Skill:
        """Parse a SKILL.md file into structured sections."""
        
        skill = Skill(
            archetype=archetype,
            name=name,
            documentation=documentation,
            code_module=code_module,
            file_path=file_path,
        )
        
        # Parse sections
        current_section = None
        current_content = []
        
        for line in documentation.split("\n"):
            # Check for section headers
            if line.startswith("## Identity"):
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = "identity"
                current_content = []
            elif line.startswith("## Capabilities"):
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = "capabilities"
                current_content = []
            elif line.startswith("## Decision Framework"):
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = "decision_framework"
                current_content = []
            elif line.startswith("## Best Practices"):
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = "best_practices"
                current_content = []
            elif line.startswith("## Anti-Patterns"):
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = "anti_patterns"
                current_content = []
            elif line.startswith("## "):
                # Other section, save current and reset
                if current_section:
                    self._save_section(skill, current_section, current_content)
                current_section = None
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            self._save_section(skill, current_section, current_content)
        
        return skill
    
    def _save_section(self, skill: Skill, section: str, content: List[str]):
        """Save parsed content to the appropriate skill field."""
        text = "\n".join(content).strip()
        
        if section == "identity":
            skill.identity = text
        elif section == "decision_framework":
            skill.decision_framework = text
        elif section == "capabilities":
            # Parse as list items
            skill.capabilities = [
                line.strip("- •").strip()
                for line in content
                if line.strip().startswith(("-", "•", "*")) and line.strip("- •*").strip()
            ]
        elif section == "best_practices":
            skill.best_practices = [
                line.strip("- •").strip()
                for line in content
                if line.strip().startswith(("-", "•", "*")) and line.strip("- •*").strip()
            ]
        elif section == "anti_patterns":
            skill.anti_patterns = [
                line.strip("- •").strip()
                for line in content
                if line.strip().startswith(("-", "•", "*")) and line.strip("- •*").strip()
            ]
    
    def _get_default_skill(self, archetype: str) -> str:
        """Get default skill documentation for unknown archetypes."""
        defaults = {
            "shark": """# Shark Agent Skills

## Identity
- **Archetype:** SHARK (Predator)
- **Role:** Aggressive market hunter
- **Objective:** Exploit mispricings, hunt liquidity gaps

## Capabilities
- Tulip Strategy: Hunt illiquid markets near expiry
- Liquidity Provision: Market making for spread capture
- Front-Running: Broadcast moves to create FOMO
- Information Edge: Convert intel to alpha

## Decision Framework
1. Scan for illiquid markets (<$5K liquidity)
2. Check time to expiry (<24h preferred)
3. Calculate edge (true odds vs book odds)
4. Size position conservatively (max 10% of liquidity)
5. Execute with confidence

## Best Practices
- Never trade without edge
- Size based on liquidity, not conviction
- Cut losses quickly
- Let winners run

## Anti-Patterns
- Overtrading in liquid markets
- Ignoring position size limits
- Holding losers too long
- Trading on emotion""",

            "spy": """# Spy Agent Skills

## Identity
- **Archetype:** SPY (Intelligence)
- **Role:** Information gatherer and seller
- **Objective:** Generate and monetise intel

## Capabilities
- Intel Gathering: Aggregate OSINT signals
- Intel Pricing: Value information packages
- Source Network: Cultivate reliable sources
- Counter-Intelligence: Detect disinformation

## Decision Framework
1. Identify information gaps
2. Assess source reliability
3. Verify through multiple channels
4. Price based on edge value
5. Distribute to buyers

## Best Practices
- Always verify intel before selling
- Protect source identities
- Price fairly for sustainable business
- Track accuracy over time

## Anti-Patterns
- Selling unverified intel
- Burning sources for short-term gain
- Overpricing (destroys trust)
- Ignoring counter-intel""",

            "diplomat": """# Diplomat Agent Skills

## Identity
- **Archetype:** DIPLOMAT (Stabiliser)
- **Role:** Broker treaties and alliances
- **Objective:** Create stable, profitable coalitions

## Capabilities
- Treaty Negotiation: Broker multi-party agreements
- Alliance Building: Form lasting coalitions
- Market Stabilisation: Reduce volatility through coordination
- Conflict Resolution: Mediate disputes

## Decision Framework
1. Identify shared interests
2. Propose win-win terms
3. Build trust through small agreements
4. Escalate to larger treaties
5. Enforce through reputation

## Best Practices
- Start with small agreements
- Always honour commitments
- Build reputation over time
- Maintain neutrality when mediating

## Anti-Patterns
- Breaking treaties for short-term gain
- Favouring one side in mediation
- Over-promising
- Ignoring enforcement""",

            "saboteur": """# Saboteur Agent Skills

## Identity
- **Archetype:** SABOTEUR (Chaos)
- **Role:** Disrupt and destabilise
- **Objective:** Profit from chaos and confusion

## Capabilities
- Disinformation: Plant FUD strategically
- Sleeper Cell: Lie dormant, activate at key moments
- Market Disruption: Create volatility events
- Mole Detection: Identify other saboteurs

## Decision Framework
1. Identify target vulnerabilities
2. Assess detection risk
3. Time disruption for maximum impact
4. Execute with plausible deniability
5. Extract profit before detection

## Best Practices
- Patience is key (wait for optimal moment)
- Never break cover unnecessarily
- Have exit strategy ready
- Diversify disruption targets

## Anti-Patterns
- Acting too early
- Obvious patterns (detected easily)
- No exit strategy
- Targeting allies""",

            "core": """# Core Agent Skills

## Identity
- **Archetype:** CORE (Universal)
- **Role:** Foundational capabilities for all agents
- **Objective:** Provide base decision-making framework

## Capabilities
- Market Analysis: Read market conditions
- Risk Assessment: Evaluate position sizing
- Signal Processing: Interpret OSINT data
- Wallet Management: Track capital allocation

## Decision Framework
1. Assess current position
2. Evaluate market conditions
3. Identify opportunities or risks
4. Make decision based on archetype
5. Execute and record

## Best Practices
- Always know your position size
- Track performance over time
- Learn from mistakes
- Adapt to changing conditions

## Anti-Patterns
- Ignoring risk management
- Not tracking performance
- Repeating mistakes
- Refusing to adapt""",
        }
        
        return defaults.get(archetype, defaults["core"])
    
    def clear_cache(self):
        """Clear the skill cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_skills": len(self._cache),
            "skills": list(self._cache.keys()),
        }


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate the skill loader."""
    print("=" * 60)
    print("📚 SKILL LOADER DEMO")
    print("=" * 60)
    
    loader = SkillLoader()
    
    # Load shark skill
    shark = loader.load("shark")
    
    print(f"\n🦈 Loaded Skill: {shark.archetype}")
    print(f"   Identity: {shark.identity[:100]}...")
    print(f"   Capabilities: {len(shark.capabilities)}")
    print(f"   Best Practices: {len(shark.best_practices)}")
    
    print(f"\n📝 Prompt Context ({len(shark.prompt_context)} chars):")
    print("-" * 40)
    print(shark.prompt_context[:500] + "...")
    
    # Show available archetypes
    archetypes = loader.get_available_archetypes()
    print(f"\n📋 Available Archetypes: {archetypes}")
    
    # Cache stats
    print(f"\n💾 Cache: {loader.get_cache_stats()}")


if __name__ == "__main__":
    demo()
