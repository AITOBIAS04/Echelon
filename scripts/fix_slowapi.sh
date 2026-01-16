#!/bin/bash
# Fix slowapi installation - installs in whatever Python is currently active

echo "🔍 Detecting Python environment..."
ACTIVE_PYTHON=$(which python)
echo "Active Python: $ACTIVE_PYTHON"
echo "Python version: $($ACTIVE_PYTHON --version)"
echo ""

echo "📦 Installing slowapi and dependencies..."
$ACTIVE_PYTHON -m pip install --quiet --upgrade pip
$ACTIVE_PYTHON -m pip install slowapi starlette eth-utils

echo ""
echo "✅ Verifying installation..."
if $ACTIVE_PYTHON -c "from slowapi import Limiter; print('✅ slowapi installed successfully')" 2>&1; then
    echo ""
    echo "🧪 Testing backend import..."
    export PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo
    if $ACTIVE_PYTHON -c "from backend.core.security import Limiter; print('✅ backend.core.security imports successfully')" 2>&1 | head -3; then
        echo ""
        echo "✅ SUCCESS! You can now run:"
        echo "  PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo $ACTIVE_PYTHON -m backend.main"
    else
        echo "❌ Backend import failed. Check the error above."
    fi
else
    echo "❌ slowapi installation failed. Check the error above."
    exit 1
fi
