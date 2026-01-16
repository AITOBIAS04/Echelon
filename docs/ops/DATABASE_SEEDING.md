# Database Seeding Guide

## Overview

The Echelon database uses **deterministic seeding** - the same fixtures produce the same database state every time, ensuring reproducibility across environments.

## Key Principles

1. **Fixtures, Not Databases**: We commit seed fixtures (SQL/JSON), never actual database files
2. **Deterministic**: Same input = same output, every time
3. **Environment Agnostic**: Works the same in dev, staging, CI, and production
4. **Migration First**: Always run migrations before seeding

## Quick Start

### Development (SQLite)

```bash
# Set SQLite database
export DATABASE_URL="sqlite:///./dev.db"

# Run migrations
cd backend
alembic upgrade head

# Seed database
cd ..
python -m backend.scripts.seed_database --force
```

### Production/Staging (PostgreSQL)

```bash
# Set PostgreSQL database URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migrations
cd backend
alembic upgrade head

# Seed database
cd ..
./scripts/seed_database.sh
```

## Seed Data Location

All seed fixtures are in `/data/seed/`:

- `seed_v2_fixed.sql` - PostgreSQL seed SQL (production-ready)
- `seed_v2.sql` - Original seed SQL
- `fixtures/` - Future: JSON/YAML fixtures for programmatic seeding

## Seeding Methods

### Method 1: Python Seeder (Recommended)

The Python seeder (`backend/scripts/seed_database.py`) is deterministic and creates:
- 5 test users
- 12 genesis agents (MEGALODON, THRESHER, CARDINAL, etc.)
- 10 timelines (Ghost Tanker, Tehran Blackout, etc.)
- 3 active paradoxes
- 75+ wing flaps (trading activity)

```bash
python -m backend.scripts.seed_database --force
```

### Method 2: SQL Seed

For PostgreSQL, you can use the SQL seed file directly:

```bash
psql $DATABASE_URL < data/seed/seed_v2_fixed.sql
```

### Method 3: Script Wrapper

Use the convenience script:

```bash
./scripts/seed_database.sh
```

## Migration Path

Always follow this order:

1. **Migrations**: `alembic upgrade head`
2. **Seed**: `python -m backend.scripts.seed_database --force`
3. **Verify**: Check API endpoints return expected data

## What Gets Seeded

- **Users**: 5 test users with different tiers
- **Agents**: 12 genesis agents across 4 archetypes (SHARK, SPY, DIPLOMAT, SABOTEUR)
- **Timelines**: 10 counterfactual timelines with market data
- **Paradoxes**: 3 active paradoxes requiring resolution
- **Wing Flaps**: 75+ historical trading events
- **Positions**: Sample user positions on timelines

## Deterministic Guarantees

- **Fixed IDs**: All IDs are hardcoded (e.g., `AGT_MEGALODON`, `USR_001`)
- **Fixed Names**: Agent names, timeline names are constant
- **Fixed Values**: Initial balances, stats are predetermined
- **Relative Times**: Timestamps use relative calculations (e.g., "2 hours ago")

## Troubleshooting

### "Database already has data"

Use `--force` flag to clear and reseed:

```bash
python -m backend.scripts.seed_database --force
```

### "Migration version mismatch"

Reset and re-run migrations:

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### "SQLite database locked"

Close any connections to the database file, then retry.

## CI/CD Integration

For automated testing:

```yaml
# Example GitHub Actions
- name: Setup database
  run: |
    export DATABASE_URL="sqlite:///./test.db"
    cd backend && alembic upgrade head
    cd .. && python -m backend.scripts.seed_database
```

## Never Commit

❌ **Never commit these:**
- `*.db` files
- `*.db.nosync` files
- `*.sqlite` files
- Any generated database files

✅ **Always commit:**
- `data/seed/*.sql` (fixture files)
- `data/seed/fixtures/*.json` (fixture files)
- Migration files in `backend/alembic/versions/`

## See Also

- `/data/seed/README.md` - Detailed fixture documentation
- `/docs/ops/DATABASE_SEED_INFO.md` - Database schema information
- `/backend/alembic/README` - Migration documentation
