#!/bin/bash

# Scheduler Startup Script
# This script runs the simulation scheduler with proper environment setup

cd "$(dirname "$0")/../.."

# Activate virtual environment
source backend/venv/bin/activate

# Set PYTHONPATH to root of monorepo
export PYTHONPATH="$(pwd)"

# Run the scheduler
echo "🚀 Starting Simulation Scheduler..."
echo "Press Ctrl+C to stop"
echo ""

python -m backend.simulation.scheduler


