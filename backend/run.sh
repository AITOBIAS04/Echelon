#!/bin/bash

# Backend Server Startup Script
# This script ensures the correct Python version and PYTHONPATH are set

cd "$(dirname "$0")/.."

# Activate virtual environment
source backend/venv/bin/activate

# Set PYTHONPATH to root of monorepo
export PYTHONPATH="$(pwd)"

# Run the backend server
python -m backend.main


