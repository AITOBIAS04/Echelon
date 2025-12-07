#!/usr/bin/env python3
import hashlib

print("=" * 70)
print("🎮 SYSTEM VALIDATION - ALL COMPONENTS")
print("=" * 70)

print("\n[1/5] Situation Room Engine...")
from backend.core.situation_room_engine import SituationRoomEngine
from backend.agents.shark_strategies import SharkBrain, SharkGenome
engine = SituationRoomEngine()
genome = SharkGenome(agent_id="shark_001", tulip_weight=0.9)
shark = SharkBrain(genome)
print(f"      ✅ Engine (tick: {engine.tick_count})")
print(f"      ✅ Shark (tulip: {shark.genome.tulip_weight})")

print("\n[2/5] Football Simulation...")
from backend.simulation.sim_football_engine import run_simulation
result = run_simulation("a", "b", "1", verbose=False)
print(f"      ✅ Match: {result}")

print("\n[3/5] Market Simulation...")
from backend.simulation.sim_market_engine import MarketSimulation
market = MarketSimulation(hashlib.sha256(b"test").hexdigest())
print(f"      ✅ Market initialized")

print("\n[4/5] Agent Schemas...")
from backend.agents.schemas import FinancialAgent, FinancialArchetype, AthleticAgent
fin = FinancialAgent(
    id="f1", name="Whale", domain="financial",
    archetype=FinancialArchetype.WHALE, bankroll=10000.0
)
ath = AthleticAgent(
    id="a1", name="Striker", domain="athletic",
    archetype="STAR", position="FWD", skill=90
)
print(f"      ✅ Financial: {fin.name}")
print(f"      ✅ Athletic: {ath.name}")

print("\n[5/5] Database Models...")
from backend.core.models import AgentGenome, TulipStrategyConfig
print(f"      ✅ Models loaded")

print("\n" + "=" * 70)
print("🎉 SUCCESS - ALL SYSTEMS OPERATIONAL")
print("=" * 70)
print("\n✓ Situation Room with Shark strategies")
print("✓ Football & Market simulations")
print("✓ Universal agent schemas")
print("✓ Database models ready")
