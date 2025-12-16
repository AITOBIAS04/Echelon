#!/bin/bash
# Fix Corrupted Virtual Environment
# This script will completely recreate the venv

set -e

echo "🔧 Fixing corrupted virtual environment..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Step 1: Deactivate and remove old venv
echo "📦 Removing old virtual environment..."
deactivate 2>/dev/null || true
rm -rf .venv

# Step 2: Clean Python cache
echo "🧹 Cleaning Python cache..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Step 3: Clean pip cache
echo "🧹 Cleaning pip cache..."
rm -rf ~/.cache/pip 2>/dev/null || true

# Step 4: Recreate venv with fresh Python
echo "📦 Creating new virtual environment..."
python3 -m venv .venv --clear

# Step 5: Activate and upgrade pip
echo "⬆️ Upgrading pip..."
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel --no-cache-dir

# Step 6: Install dependencies
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install --no-cache-dir -r requirements.txt

# Step 7: Verify
echo "✅ Verifying installation..."
python3 -c "import uvicorn; print('✅ uvicorn works!')" || echo "❌ uvicorn failed"
python3 -c "import fastapi; print('✅ fastapi works!')" || echo "❌ fastapi failed"

echo ""
echo "✅ Virtual environment recreated!"
echo "Activate with: source .venv/bin/activate"
echo "Start server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000"

