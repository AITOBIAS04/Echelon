#!/bin/bash
# Check and unlock .venv directory

echo "🔍 Checking what's locking .venv..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

echo ""
echo "1. Checking for Python processes..."
ps aux | grep python | grep -v grep || echo "   No Python processes found"

echo ""
echo "2. Checking for processes using .venv..."
lsof +D .venv 2>/dev/null | head -10 || echo "   No processes found using .venv"

echo ""
echo "3. Checking for uvicorn processes..."
ps aux | grep uvicorn | grep -v grep || echo "   No uvicorn processes found"

echo ""
echo "✅ Check complete!"
echo ""
echo "Next steps:"
echo "1. Close any other IDEs/editors with backend files open"
echo "2. Kill any Python processes: pkill -f python"
echo "3. Wait a few seconds"
echo "4. Try: mv .venv .venv.old"
echo ""
echo "Or create a new venv:"
echo "   python3 -m venv .venv_new"
echo "   source .venv_new/bin/activate"

