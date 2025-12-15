#!/bin/bash
# Corrected Situation Room Integration Validation

echo "=== SITUATION ROOM INTEGRATION CHECK (CORRECTED) ==="
echo ""

# Check 1: Required files exist (CORRECT PATHS)
echo "📁 Checking required files..."
files=(
    "backend/core/situation_room_engine.py"
    "backend/agents/shark_strategies.py"
    "backend/simulation/situation-room/scheduler.py"
    "backend/core/synthetic_osint.py"
    "backend/core/narrative_war.py"
    "backend/core/models.py"
    "frontend/app/situation-room/page.jsx"
)

for f in "${files[@]}"; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ MISSING: $f"
    fi
done

echo ""
echo "🔍 Checking integrations..."

# Check 2: Shark imports in engine
if grep -q "SharkBrain\|shark_strategies" backend/core/situation_room_engine.py 2>/dev/null; then
    echo "  ✅ Shark imports in situation_room_engine.py"
else
    echo "  ❌ Missing shark imports in situation_room_engine.py"
fi

# Check 3: _process_financial_markets method
if grep -q "_process_financial_markets" backend/core/situation_room_engine.py 2>/dev/null; then
    echo "  ✅ _process_financial_markets method exists"
else
    echo "  ❌ Missing _process_financial_markets in engine"
fi

# Check 4: AgentGenome in models
if grep -q "AgentGenome" backend/core/models.py 2>/dev/null; then
    echo "  ✅ AgentGenome in models.py"
else
    echo "  ❌ Missing AgentGenome in models.py"
fi

# Check 5: TulipStrategy config
if grep -q "TulipStrategyConfig\|tulip" backend/core/models.py 2>/dev/null; then
    echo "  ✅ TulipStrategyConfig in models.py"
else
    echo "  ❌ Missing TulipStrategyConfig in models.py"
fi

# Check 6: Header link
if grep -q "situation-room" frontend/components/Header.jsx 2>/dev/null; then
    echo "  ✅ Situation Room link in Header"
else
    echo "  ❌ Missing Situation Room link in Header.jsx"
fi

# Check 7: Old war-room removed
if [ -f "frontend/app/war-room/page.jsx" ] || [ -f "frontend/components/war-room-page.jsx" ]; then
    echo "  ⚠️  Old war-room files still exist (should be deleted)"
else
    echo "  ✅ Old war-room files removed"
fi

# Additional checks
echo ""
echo "🔬 Additional checks..."

# Check 8: Football engine exists and has argparse
if [ -f "backend/simulation/sim_football_engine.py" ]; then
    if grep -q "argparse.*--mode.*--matchday" backend/simulation/sim_football_engine.py 2>/dev/null; then
        echo "  ✅ Football engine with full CLI support"
    else
        echo "  ⚠️  Football engine exists but may be missing CLI flags"
    fi
else
    echo "  ❌ Missing football simulation engine"
fi

# Check 9: API routes for Situation Room
if grep -q "situation.room\|situation_room" backend/api/situation_room_routes.py 2>/dev/null; then
    echo "  ✅ Situation Room API routes"
else
    echo "  ❌ Missing Situation Room API routes"
fi

echo ""
echo "=== CHECK COMPLETE ==="
