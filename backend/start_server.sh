#!/bin/bash
# Start/Restart the FastAPI server with proper virtual environment

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Kill existing server if running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping existing server on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Activate virtual environment
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "   Please run: ./setup_bun.sh"
    exit 1
fi

source "$SCRIPT_DIR/.venv/bin/activate"

# Set PostgreSQL path (for macOS Homebrew)
if [ -d "/opt/homebrew/opt/postgresql@15/bin" ]; then
    export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
fi

# Set USE_MOCKS from .env if it exists, otherwise default to false
if [ -f "$PROJECT_ROOT/.env" ]; then
    export USE_MOCKS=$(grep -E "^USE_MOCKS=" "$PROJECT_ROOT/.env" | cut -d'=' -f2 | tr -d '"' || echo "false")
else
    export USE_MOCKS=false
fi

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "🐍 Using Python $PYTHON_VERSION from virtual environment"
echo "📦 Starting FastAPI server..."
echo "   USE_MOCKS=$USE_MOCKS"
echo ""

# Start uvicorn
cd "$PROJECT_ROOT"
exec uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

