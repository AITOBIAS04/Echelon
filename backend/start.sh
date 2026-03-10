#!/bin/bash

# start.sh - Production startup script for Project Seed Backend
# For use with Render, Railway, or any containerized deployment

set -e

echo "🌱 Starting Project Seed Backend..."

# Ensure PYTHONPATH includes current directory for backend imports
export PYTHONPATH="${PYTHONPATH}:/app"

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p data/backups
mkdir -p data/snapshots
echo "📁 Data directories ready"

# Require DATABASE_URL — no SQLite fallback in production
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is required. Set it to a PostgreSQL connection string."
    exit 1
fi

# Run database migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migrations skipped (alembic not configured)"
fi

# Database tables are created via Alembic migrations (above) and
# init_db() on FastAPI startup event. No manual create_all needed.

# Start the server
echo "🚀 Starting Uvicorn..."

# Production settings
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-2}

# Use gunicorn with uvicorn workers in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Running in PRODUCTION mode"
    exec gunicorn backend.main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers $WORKERS \
        --bind $HOST:$PORT \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
else
    echo "🛠️  Running in DEVELOPMENT mode"
    exec python -m uvicorn backend.main:app \
        --host $HOST \
        --port $PORT \
        --reload
fi

