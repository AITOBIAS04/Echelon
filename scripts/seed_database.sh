#!/bin/bash
# Deterministic Database Seeding Script
# =====================================
# This script provides a reproducible way to seed the database with fixtures.
# It ensures the same seed data is created every time, regardless of environment.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "🌱 Echelon Database Seeding"
echo "=========================="
echo ""

# Check for DATABASE_URL
if [ -z "${DATABASE_URL}" ]; then
  echo "⚠️  DATABASE_URL not set."
  echo ""
  echo "For PostgreSQL (production/staging):"
  echo "  export DATABASE_URL='postgresql://user:pass@host:5432/dbname'"
  echo ""
  echo "For SQLite (local development):"
  echo "  export DATABASE_URL='sqlite:///./dev.db'"
  echo ""
  exit 1
fi

# Detect database type
if [[ "$DATABASE_URL" == *"sqlite"* ]]; then
  DB_TYPE="sqlite"
  echo "📦 Database: SQLite (development)"
else
  DB_TYPE="postgresql"
  echo "📦 Database: PostgreSQL"
fi

# Step 1: Run migrations
echo ""
echo "🔄 Step 1: Running database migrations..."
cd "$PROJECT_ROOT/backend"

if [ -f "alembic.ini" ]; then
  alembic upgrade head
  echo "✅ Migrations complete"
else
  echo "⚠️  No alembic.ini found, skipping migrations"
  echo "   (Tables will be created by SQLAlchemy if needed)"
fi

# Step 2: Seed database
echo ""
echo "🌱 Step 2: Seeding database with fixtures..."

cd "$PROJECT_ROOT"

# Use Python seeder (deterministic)
if [ -f "backend/scripts/seed_database.py" ]; then
  echo "   Using Python seeder (deterministic)..."
  
  # Activate venv if it exists
  if [ -f "backend/.venv/bin/activate" ]; then
    source backend/.venv/bin/activate
  fi
  
  # Run seeder with --force to clear existing data
  python3 -m backend.scripts.seed_database --force
  
  echo "✅ Database seeded successfully"
else
  echo "❌ Error: backend/scripts/seed_database.py not found"
  exit 1
fi

# Step 3: Verify
echo ""
echo "✅ Seeding complete!"
echo ""
echo "Next steps:"
echo "  - Start backend: cd backend && python -m uvicorn main:app --reload"
echo "  - Check API: curl http://localhost:8000/api/agents"
echo ""
