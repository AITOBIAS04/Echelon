# Seed Fixtures

This directory contains deterministic seed data fixtures for the Echelon database.

## Purpose

- **Deterministic**: Same fixtures produce the same database state every time
- **Reproducible**: Anyone can recreate the exact same development database
- **Version Controlled**: Fixtures are committed, not generated database files
- **CI/CD Ready**: Can be used in automated testing and deployment pipelines

## Structure

```
data/seed/
├── README.md              # This file
├── seed_v2.sql            # PostgreSQL seed SQL (production-ready)
├── seed_v2_fixed.sql      # Fixed version of seed SQL
└── fixtures/              # Future: JSON/YAML fixture files for programmatic seeding
```

## Usage

### Option 1: SQL Seed (PostgreSQL)

```bash
# Set your DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migrations first
cd backend
alembic upgrade head

# Then seed with SQL
psql $DATABASE_URL < data/seed/seed_v2_fixed.sql
```

### Option 2: Python Seeder (Recommended)

```bash
# Set your DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migrations
cd backend
alembic upgrade head

# Run deterministic seeder
python -m backend.scripts.seed_database --fixtures data/seed/fixtures/
```

### Option 3: Development (SQLite)

```bash
# Uses SQLite for local development
export DATABASE_URL="sqlite:///./dev.db"

# Run migrations
cd backend
alembic upgrade head

# Seed with Python seeder (deterministic)
python -m backend.scripts.seed_database
```

## Fixture Format

Fixtures should be deterministic JSON/YAML files that can be loaded programmatically:

```json
{
  "users": [
    {
      "id": "USR_001",
      "username": "DeepStateTrader",
      "email": "deep@echelon.io",
      "tier": "pro"
    }
  ],
  "agents": [
    {
      "id": "AGT_MEGALODON",
      "name": "MEGALODON",
      "archetype": "SHARK",
      "tier": 3
    }
  ]
}
```

## Principles

1. **No Random Data**: All IDs, names, and values are fixed
2. **No Timestamps**: Use relative times (e.g., "2 hours ago") that are calculated
3. **No Environment-Specific**: Works the same in dev, staging, and CI
4. **Version Controlled**: All fixtures are committed to git
5. **Idempotent**: Running seed multiple times produces the same result

## Adding New Fixtures

1. Create fixture file in `data/seed/fixtures/`
2. Update seeder script to load fixtures
3. Test that seeding is deterministic
4. Document in this README

## Migration Path

1. **Run migrations**: `alembic upgrade head`
2. **Load fixtures**: `python -m backend.scripts.seed_database`
3. **Verify**: Check that data matches expected state

Never commit actual database files (`.db`, `.sqlite`) - only commit fixtures!
