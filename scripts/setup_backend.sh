#!/bin/bash
# Setup script to ensure all backend dependencies are installed

set -e

echo "🔧 Backend Setup Script"
echo "======================"
echo ""

# Detect which Python to use
if [ -f "backend/venv/bin/python" ]; then
    PYTHON="backend/venv/bin/python"
    echo "✅ Using backend/venv Python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    echo "✅ Using .venv Python"
else
    PYTHON="python"
    echo "⚠️  Using system Python (consider creating a venv)"
fi

echo "Python: $($PYTHON --version)"
echo "Path: $($PYTHON -c 'import sys; print(sys.executable)')"
echo ""

# Install security dependencies
echo "📦 Installing security dependencies..."
$PYTHON -m pip install --quiet --upgrade pip
$PYTHON -m pip install slowapi starlette eth-utils 2>&1 | grep -E "(Requirement|Successfully|ERROR)" | tail -3

# Install other critical dependencies
echo "📦 Installing core dependencies..."
$PYTHON -m pip install fastapi uvicorn sqlalchemy pydantic python-jose passlib python-dotenv python-multipart 2>&1 | grep -E "(Requirement|Successfully|ERROR)" | tail -3

echo ""
echo "✅ Verifying installation..."

# Test imports
$PYTHON -c "from slowapi import Limiter; print('  ✅ slowapi')" 2>&1
$PYTHON -c "from eth_utils import is_address; print('  ✅ eth_utils')" 2>&1
$PYTHON -c "from fastapi import FastAPI; print('  ✅ fastapi')" 2>&1

echo ""
echo "🧪 Testing backend import..."
export PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo
$PYTHON -c "from backend.core.security import Limiter; print('  ✅ backend.core.security')" 2>&1 | head -3

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the backend:"
echo "  export PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo"
echo "  $PYTHON -m backend.main"
echo ""
echo "Or use uvicorn directly:"
echo "  $PYTHON -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

