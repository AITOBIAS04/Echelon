#!/bin/bash
# Minimal Installation - Install only essential packages

set -e

echo "🔧 Minimal installation approach..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Activate venv (assume it exists)
source .venv/bin/activate

echo "📦 Installing minimal dependencies..."

# Install pip upgrade first (smallest package)
echo "1. Upgrading pip..."
python3 -m pip install --upgrade pip --no-cache-dir --timeout 30 || {
    echo "❌ Pip upgrade failed. Check network connection."
    exit 1
}

# Install only what's needed to run the server
echo "2. Installing uvicorn..."
python3 -m pip install --no-cache-dir --timeout 60 uvicorn[standard] || {
    echo "❌ Uvicorn installation failed."
    exit 1
}

echo "3. Installing fastapi..."
python3 -m pip install --no-cache-dir --timeout 60 fastapi || {
    echo "❌ FastAPI installation failed."
    exit 1
}

echo "4. Installing core database packages..."
python3 -m pip install --no-cache-dir --timeout 60 sqlalchemy pydantic || {
    echo "❌ Database packages failed."
    exit 1
}

echo ""
echo "✅ Minimal installation complete!"
echo "Test with: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "If this works, you can install remaining packages later with:"
echo "pip install --no-cache-dir -r requirements.txt"

