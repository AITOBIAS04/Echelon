#!/bin/bash
# Start the Echelon Frontend Dev Server
# Usage: ./start_frontend.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../frontend"

echo "🚀 Starting Echelon Frontend (Vite) on http://localhost:5173"
echo ""

# Use npm/pnpm if available, fallback to bun
if command -v pnpm &> /dev/null; then
  pnpm dev
elif command -v npm &> /dev/null; then
  npm run dev
elif command -v bun &> /dev/null; then
  bun dev
else
  echo "❌ Error: No package manager found. Install pnpm, npm, or bun."
  exit 1
fi
