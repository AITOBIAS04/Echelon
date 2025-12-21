#!/bin/bash
# Quick script to seed Railway database from local machine
# Usage: ./seed_railway.sh

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "backend/.venv/bin/activate" ]; then
    source backend/.venv/bin/activate
fi

# Set DATABASE_URL (use PUBLIC URL for local runs, not internal)
# Internal URL (postgres.railway.internal) only works inside Railway
# Public URL (hopper.proxy.rlwy.net) works from your local machine
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:<PASSWORD>@hopper.proxy.rlwy.net:15300/railway}"

# Run seed script from project root
python3 -m backend.scripts.seed_database --force

