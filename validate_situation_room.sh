#!/bin/bash
# Save as: validate_situation_room.sh

echo "=== SITUATION ROOM INTEGRATION CHECK ==="
echo ""

# Check 1: Required files exist
echo "📁 Checking required files..."
files=(
    "backend/simulation/situation_room_engine.py"
    "backend/simulation/shark_strategies.py"
    "backend/simulation/scheduler.py"
    "backend/simulation/auto_uploader.py"
    "backend/simulation/synthetic_osint.py"
    "backend/simulation/narrative_war.py"
    "backend/models.py"
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
if grep -q "SharkBrain\|shark_strategies" backend/simulation/situation_room_engine.py 2>/dev/null; then
    echo "  ✅ Shark imports in engine"
else
    echo "  ❌ Missing shark imports in situation_room_engine.py"
fi

# Check 3: _process_financial_markets method
if grep -q "_process_financial_markets" backend/simulation/situation_room_engine.py 2>/dev/null; then
    echo "  ✅ _process_financial_markets method exists"
else
    echo "  ❌ Missing _process_financial_markets in engine"
fi

# Check 4: AgentGenome in models
if grep -q "AgentGenome" backend/models.py 2>/dev/null; then
    echo "  ✅ AgentGenome in models.py"
else
    echo "  ❌ Missing AgentGenome in models.py"
fi

# Check 5: TulipStrategy config
if grep -q "TulipStrategyConfig\|tulip" backend/models.py 2>/dev/null; then
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

echo ""
echo "=== CHECK COMPLETE ==="
