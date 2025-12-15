#!/bin/bash

# start.sh - Production startup script for Project Seed Backend
# For use with Render, Railway, or any containerized deployment

set -e

echo "🌱 Starting Project Seed Backend..."

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p data/backups
mkdir -p data/snapshots
echo "📁 Data directories ready"

# Check for required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using SQLite"
    export DATABASE_URL="sqlite:///./seed_production.db"
fi

# Run database migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migrations skipped (alembic not configured)"
fi

# Initialize database tables
echo "🗄️  Initializing database..."
python -c "
from backend.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"

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

