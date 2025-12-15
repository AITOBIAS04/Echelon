#!/bin/bash
# Fix Corrupted Python Dependencies
# Run this script to clean and reinstall dependencies

set -e

echo "🔧 Fixing corrupted Python dependencies..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Step 1: Deactivate and remove venv
echo "📦 Removing old virtual environment..."
deactivate 2>/dev/null || true
rm -rf .venv

# Step 2: Clean Python cache
echo "🧹 Cleaning Python cache..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Step 3: Clean pip cache
echo "🧹 Cleaning pip cache..."
rm -rf ~/.cache/pip 2>/dev/null || true

# Step 4: Recreate venv
echo "📦 Creating new virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Step 5: Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Step 6: Install problematic packages first
echo "📥 Installing core dependencies..."
pip install yarl==1.9.4
pip install multidict==6.0.5
pip install aiohttp==3.13.2

# Step 7: Install all requirements
echo "📥 Installing all requirements..."
pip install -r requirements.txt

# Step 8: Verify
echo "✅ Verifying installation..."
python3 -c "import aiohttp; print('✅ aiohttp works!')" || echo "❌ aiohttp failed"
python3 -c "import yarl; print('✅ yarl works!')" || echo "❌ yarl failed"
python3 -c "from backend.core.osint_registry import get_osint_registry; print('✅ Imports work!')" || echo "❌ Imports failed"

echo ""
echo "✅ Done! Activate with: source .venv/bin/activate"

