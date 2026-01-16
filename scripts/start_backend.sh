#!/bin/bash
# Start the Echelon Backend Server
# Usage: ./start_backend.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/backend"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./setup_bun.sh first"
    exit 1
fi

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

echo "🚀 Starting Echelon Backend on http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Start uvicorn with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
