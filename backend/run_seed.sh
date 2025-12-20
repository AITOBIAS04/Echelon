#!/bin/bash
# Safe database seeding script
# Run this from the backend directory: bash run_seed.sh

set -e  # Exit on error

echo "🔍 Checking Python version..."
python3 --version

echo ""
echo "📦 Installing dependencies (this may take a minute)..."
# Try pip3 first, then pip, then python -m pip
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "🔄 Running database migrations..."
python3 -m alembic upgrade head

echo ""
echo "🌱 Seeding database..."
python3 -m scripts.seed_database

echo ""
echo "✅ Done! Database seeded successfully."

