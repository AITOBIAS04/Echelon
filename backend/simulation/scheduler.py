import asyncio
import json
import os
from datetime import datetime

# --- USE ABSOLUTE IMPORTS ---
from backend.simulation.world_state import WorldState
from backend.agents.autonomous_agent import GeopoliticalAgent
from backend.simulation.yield_manager import YieldManager
from backend.simulation.genome import AgentGenome

# Fixed file path using relative location
STATE_FILE = os.path.join(os.path.dirname(__file__), "world_state.json")


async def load_state() -> WorldState:
    """Loads state from JSON or creates default."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        
        # Handle migration from old format to new format
        if "global_tension" not in data:
            data["global_tension"] = data.get("global_tension_score", 0.5)
            data["recent_reasoning"] = "Migrated from old world state format."
            data["event_log"] = []
        
        # Handle legacy string dates if they exist
        if isinstance(data.get("last_updated"), str):
            # We let Pydantic handle the parsing or reset it
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        elif "last_updated" not in data:
            data["last_updated"] = datetime.now()
        
        # Ensure required fields exist
        if "recent_reasoning" not in data:
            data["recent_reasoning"] = "System initialized."
        if "event_log" not in data:
            data["event_log"] = []
        
        return WorldState(**data)
    return WorldState(global_tension=0.0)


async def save_state(state: WorldState):
    """Dumps Pydantic model to JSON."""
    with open(STATE_FILE, "w") as f:
        f.write(state.model_dump_json(indent=2))


async def game_loop():
    print("--- 🌍 THE LIVING ENGINE IS ONLINE ---")
    
    # 1. Initialize the Brain with a default genome
    default_genome = AgentGenome(
        aggression=0.5,
        deception=0.5,
        risk_tolerance=0.5,
        archetype="Director",
        speech_style="Formal",
        secret_objective="SURVIVE"
    )
    agent = GeopoliticalAgent(agent_id="Director_AI", genome=default_genome)
    
    # 2. Initialize the Economy (War Bonds)
    yield_manager = YieldManager()  # <--- NEW: Start the Yield Manager
    
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💓 Tick Started...")
        
        # 3. Load Reality
        current_state = await load_state()
        print(f"   Current Tension: {current_state.global_tension:.2f}")
        
        # 4. Calculate & Distribute Yield (The Economy Tick)
        # In a real app, we'd check the blockchain here. 
        # For now, we simulate time passing.
        yield_manager.distribute_yield()  # <--- NEW: Pay the agents
        
        # 5. The Brain Logic
        # Determine Brain Mode
        brain_mode = "routine"
        if current_state.global_tension > 0.7 or current_state.global_tension < 0.1:
            brain_mode = "critical"
            
        print(f"   🧠 Agent is thinking (Mode: {brain_mode})...")
        decision = await agent.think(current_state, mode=brain_mode)
        
        # 6. Update Reality
        new_tension = decision.get("new_tension", current_state.global_tension)
        reasoning = decision.get("reasoning", "No reason given.")
        
        current_state.global_tension = new_tension
        current_state.recent_reasoning = reasoning
        current_state.last_updated = datetime.now()
        
        # 7. Persist
        await save_state(current_state)
        
        print(f"   ⚡ Update: Tension -> {new_tension:.2f}")
        print(f"   📝 Logic: {reasoning}")
        
        # 8. Sleep
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(game_loop())
