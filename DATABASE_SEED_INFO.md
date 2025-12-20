# Database Seed Scripts & Initialization Guide

## Overview

The Echelon backend has **two seed scripts** for populating initial data:

1. **`backend/scripts/seed_database.py`** - Main database seeder (PostgreSQL/SQLAlchemy)
2. **`backend/seed_data.py`** - Legacy market seeder (Event Orchestrator)

## Primary Seed Script: `backend/scripts/seed_database.py`

This is the **main seeder** for PostgreSQL. It creates:
- **Users** (3 test users)
- **Agents** (5 agents: MEGALODON, CARDINAL, ENVOY, VIPER, ORACLE)
- **Timelines** (4 timelines: Ghost Tanker, Fed Rate, Contagion, Oil Crisis)
- **Paradoxes** (1 active paradox on Contagion timeline)
- **Wing Flaps** (50 causality events)
- **User Positions** (3 positions)

### How to Run:

```bash
# From project root
cd backend

# Run the seeder
python -m scripts.seed_database

# Or with force reseed (clears existing data)
python -m scripts.seed_database --force
```

### Prerequisites:

1. **Database must be initialized** (migrations run):
   ```bash
   alembic upgrade head
   ```

2. **Environment variables set**:
   - `DATABASE_URL` - PostgreSQL connection string
   - Or individual: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

3. **Database connection**:
   - The script uses `backend.database.connection.async_session_maker`
   - Calls `init_db()` to ensure connection

### What It Does:

1. Checks if database already has data
2. If data exists, prompts for confirmation (or use `--force`)
3. Clears existing data if reseeding
4. Creates all seed data in order:
   - Users → Agents → Timelines → Paradoxes → Wing Flaps → Positions
5. Commits transaction

### Sample Output:

```
============================================================
ECHELON DATABASE SEEDER
============================================================

🔌 Connecting to database...
🌱 Seeding database...

✅ Created 3 users
✅ Created 5 agents
✅ Created 4 timelines
✅ Created 1 paradoxes
✅ Created 50 wing flaps
✅ Created 3 user positions

============================================================
✅ DATABASE SEEDED SUCCESSFULLY!
============================================================
```

## Legacy Seed Script: `backend/seed_data.py`

This creates markets via the Event Orchestrator (older system):
- Creates 10 "Polymarket-style" events
- Uses `EventOrchestrator.create_market()`
- Dispatches agents to markets

### How to Run:

```bash
cd backend
python seed_data.py
```

**Note:** This is for the legacy market system, not the new Echelon database schema.

## Database Initialization Flow

### 1. Run Migrations (Creates Tables)

```bash
# From backend directory
alembic upgrade head
```

This creates all tables defined in `backend/alembic/versions/347c30465dba_initial_tables.py`:
- `users`
- `agents`
- `timelines`
- `wing_flaps`
- `paradoxes`
- `user_positions`

### 2. Seed Data

```bash
python -m scripts.seed_database
```

### 3. Verify

Check your database:
```bash
# Using psql
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM timelines;"
```

## Local PostgreSQL Setup

### Using Docker:

```bash
docker run --name echelon-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=echelon \
  -p 5432:5432 \
  -d postgres:15
```

### Environment Variables:

```bash
# .env file
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/echelon

# Or individual variables
DB_HOST=localhost
DB_PORT=5432
DB_NAME=echelon
DB_USER=postgres
DB_PASSWORD=your_password
```

### Initialize:

```bash
# 1. Run migrations
cd backend
alembic upgrade head

# 2. Seed data
python -m scripts.seed_database
```

## Railway/Production Setup

1. **Add PostgreSQL service** in Railway dashboard
2. **Link to backend service** - Railway auto-shares `DATABASE_URL`
3. **Migrations run automatically** - Updated `entrypoint.py` runs `alembic upgrade head` on startup
4. **Seed manually** (one-time):
   ```bash
   railway run python -m scripts.seed_database
   ```

## Important Notes

- **`USE_MOCKS=false`** must be set in `.env` to use real database
- The seed script uses **async SQLAlchemy** sessions
- All IDs are prefixed (e.g., `USR_001`, `AGT_MEGALODON`, `TL_GHOST_TANKER`)
- The script is **idempotent** - safe to run multiple times with `--force`

## Troubleshooting

### "No module named 'backend.database'"
- Ensure you're running from the correct directory
- Check `PYTHONPATH` includes the backend directory

### "Database connection failed"
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Verify credentials

### "Table already exists"
- Run migrations: `alembic upgrade head`
- Or drop and recreate: `alembic downgrade base && alembic upgrade head`

