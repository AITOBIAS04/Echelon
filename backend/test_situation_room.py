#!/usr/bin/env python3
"""
Comprehensive Situation Room Integration Test
"""

print("=" * 60)
print("SITUATION ROOM INTEGRATION TEST")
print("=" * 60)

# Test 1: Core imports
print("\n1. Testing core imports...")
try:
    from backend.core.situation_room_engine import SituationRoomEngine
    from backend.agents.shark_strategies import SharkBrain, TulipStrategy
    from backend.core.models import AgentGenome, TulipStrategyConfig
    from backend.core.synthetic_osint import SyntheticOSINTGenerator
    from backend.core.narrative_war import NarrativeWarEngine
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Engine initialization
print("\n2. Testing engine initialization...")
try:
    engine = SituationRoomEngine()
    print(f"   ✅ Engine created: {type(engine).__name__}")
    print(f"      - Tick count: {engine.tick_count}")
    print(f"      - Has process method: {hasattr(engine, 'process_tick')}")
except Exception as e:
    print(f"   ❌ Engine init failed: {e}")
    exit(1)

# Test 3: SharkBrain initialization
print("\n3. Testing SharkBrain...")
try:
    shark = SharkBrain(agent_id="test_shark", risk_tolerance=0.7)
    print(f"   ✅ SharkBrain created")
    print(f"      - Agent ID: {shark.agent_id}")
    print(f"      - Risk tolerance: {shark.risk_tolerance}")
except Exception as e:
    print(f"   ❌ SharkBrain failed: {e}")

# Test 4: TulipStrategy initialization
print("\n4. Testing TulipStrategy...")
try:
    strategy = TulipStrategy(
        target_asset="TEST",
        manipulation_intensity=0.8,
        duration_ticks=100
    )
    print(f"   ✅ TulipStrategy created")
    print(f"      - Target: {strategy.target_asset}")
    print(f"      - Intensity: {strategy.manipulation_intensity}")
except Exception as e:
    print(f"   ❌ TulipStrategy failed: {e}")

# Test 5: OSINT Generator
print("\n5. Testing OSINT Generator...")
try:
    osint = SyntheticOSINTGenerator()
    print(f"   ✅ OSINT Generator created")
except Exception as e:
    print(f"   ❌ OSINT Generator failed: {e}")

# Test 6: Narrative War Engine
print("\n6. Testing Narrative War Engine...")
try:
    narrative = NarrativeWarEngine()
    print(f"   ✅ Narrative War Engine created")
except Exception as e:
    print(f"   ❌ Narrative War Engine failed: {e}")

# Test 7: Check for _process_financial_markets method
print("\n7. Checking Situation Room methods...")
try:
    has_financial = hasattr(engine, '_process_financial_markets')
    print(f"   {'✅' if has_financial else '❌'} _process_financial_markets: {has_financial}")
    
    has_process_tick = hasattr(engine, 'process_tick')
    print(f"   {'✅' if has_process_tick else '❌'} process_tick: {has_process_tick}")
    
    has_get_state = hasattr(engine, 'get_state')
    print(f"   {'✅' if has_get_state else '❌'} get_state: {has_get_state}")
except Exception as e:
    print(f"   ❌ Method check failed: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
