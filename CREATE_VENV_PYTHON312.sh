#!/bin/bash
# Create venv with Python 3.12

set -e

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

echo "🔍 Checking Python versions..."

# Try to find Python 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
    echo "✅ Found python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "✅ Found python3.11"
elif [ -f "/opt/homebrew/bin/python3.12" ]; then
    PYTHON_CMD=/opt/homebrew/bin/python3.12
    echo "✅ Found Python 3.12 in Homebrew"
elif [ -f "/usr/local/bin/python3.12" ]; then
    PYTHON_CMD=/usr/local/bin/python3.12
    echo "✅ Found Python 3.12 in /usr/local"
else
    echo "❌ Python 3.12 or 3.11 not found"
    echo "Install with: brew install python@3.12"
    exit 1
fi

# Show version
$PYTHON_CMD --version

# Remove old venv
echo "🧹 Removing old venv..."
rm -rf .venv

# Create new venv
echo "📦 Creating venv with $PYTHON_CMD..."
$PYTHON_CMD -m venv .venv

# Activate
source .venv/bin/activate

# Verify version
echo "✅ Python version in venv:"
python3 --version

# Upgrade pip
echo "⬆️ Upgrading pip..."
python3 -m pip install --no-cache-dir --upgrade pip

# Install requirements (virtuals-acp is already commented out)
echo "📥 Installing requirements..."
python3 -m pip install --no-cache-dir -r requirements.txt

echo ""
echo "✅ Done! Activate with: source .venv/bin/activate"

