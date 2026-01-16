#!/bin/bash
# Install security dependencies in the active Python environment

echo "Installing security dependencies..."
python -m pip install slowapi starlette eth-utils

echo ""
echo "Verifying installation..."
python -c "from slowapi import Limiter; from eth_utils import is_address; print('✅ All security dependencies installed')" 2>&1

echo ""
echo "Testing backend import..."
PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo python -c "from backend.core.security import Limiter; print('✅ Security module imports successfully')" 2>&1 | head -5
