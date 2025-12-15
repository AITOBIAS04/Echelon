"""
Echelon Agent Skills Architecture
=================================

A modular, cost-optimised decision system for AI agents.

Key Components:
- SkillLoader: Dynamic skill loading with caching
- ContextCompiler: ADK-style context compilation
- SkillRouter: Tiered decision routing
- ProviderRegistry: Multi-provider LLM management

Usage:
    from skills import SkillRouter, ContextCompiler
    
    router = SkillRouter()
    compiler = ContextCompiler()
    
    context = compiler.compile_for_trade(agent, market)
    decision = await router.route(context)
"""

from .skill_loader import SkillLoader, Skill
from .context_compiler import ContextCompiler, CompiledContext
from .skill_router import SkillRouter, RoutingDecision
from .provider_registry import ProviderRegistry, ProviderConfig

__all__ = [
    "SkillLoader",
    "Skill",
    "ContextCompiler",
    "CompiledContext",
    "SkillRouter",
    "RoutingDecision",
    "ProviderRegistry",
    "ProviderConfig",
]

__version__ = "1.0.0"
