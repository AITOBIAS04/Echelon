#!/bin/bash
# Remove .venv now that nothing is locking it

set -e

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

echo "🔧 Removing .venv directory..."

# Make sure we're deactivated
deactivate 2>/dev/null || true

# Try standard remove
if rm -rf .venv 2>/dev/null; then
    echo "✅ .venv removed successfully"
else
    echo "⚠️ Standard rm failed, trying with chmod..."
    chmod -R u+w .venv 2>/dev/null || true
    if rm -rf .venv 2>/dev/null; then
        echo "✅ .venv removed successfully"
    else
        echo "❌ Still failed. Trying rename instead..."
        mv .venv .venv.old && echo "✅ Renamed to .venv.old (you can delete it later)"
    fi
fi

# Create fresh venv
echo ""
echo "📦 Creating fresh virtual environment..."
python3 -m venv .venv

echo "✅ Fresh venv created!"
echo ""
echo "Next steps:"
echo "  source .venv/bin/activate"
echo "  python3 -m pip install --no-cache-dir --upgrade pip"
echo "  python3 -m pip install --no-cache-dir \"uvicorn[standard]\" fastapi sqlalchemy pydantic"

