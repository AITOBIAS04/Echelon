#!/bin/bash
# Start the Echelon Frontend Dev Server (Bun)
# Usage: ./start_frontend.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/frontend"

echo "🚀 Starting Echelon Frontend on http://localhost:3000"
echo ""

# Start with Bun
bun dev
