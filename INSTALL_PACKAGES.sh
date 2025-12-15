#!/bin/bash
# Install packages with proper quoting for zsh

set -e

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

echo "📦 Installing packages..."

# Quote the package name to prevent zsh glob expansion
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic

echo "✅ Installation complete!"

