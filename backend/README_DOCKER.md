# Project Seed Backend - Docker Guide

## Overview

This guide covers running the Project Seed backend in Docker containers. The setup includes:

- **Backend API** - FastAPI server with all endpoints
- **Scheduler** (optional) - Runs simulation ticks automatically
- **Data Persistence** - Markets, economy, and timelines survive restarts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Host                               │
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   backend           │    │   scheduler         │            │
│  │   (FastAPI)         │    │   (Simulation)      │            │
│  │   Port: 8000        │◄───│   Depends on API    │            │
│  └──────────┬──────────┘    └──────────┬──────────┘            │
│             │                          │                        │
│             └──────────┬───────────────┘                        │
│                        │                                        │
│             ┌──────────▼──────────┐                            │
│             │   Shared Volumes    │                            │
│             │   - /app/data       │                            │
│             │   - /app/database.db│                            │
│             │   - /app/.env       │                            │
│             └─────────────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Docker Desktop** - [Install Docker](https://docs.docker.com/get-docker/)

2. **Environment file** - Create `backend/.env` with your API keys

### Minimum `.env` file:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Recommended (for news/markets)
GNEWS_API_KEY=your_key
NEWSAPI_API_KEY=your_key

# Optional (for full functionality)
NEWSDATA_API_KEY=your_key
THENEWSAPI_API_KEY=your_key
MARKETAUX_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
CRYPTOCOMPARE_API_KEY=your_key
FOOTBALL_DATA_API_KEY=your_key
API_SPORTS_API_KEY=your_key
THESPORTSDB_API_KEY=3
```

## Quick Start

```bash
cd backend

# Build and start
docker-compose up --build

# API available at http://localhost:8000
```

## Docker Compose Services

### Backend API (default)

The main FastAPI server with all endpoints.

```bash
# Start only the API
docker-compose up backend

# With rebuild
docker-compose up --build backend
```

**Endpoints:**

- `GET /health` - Health check
- `GET /markets` - List betting markets
- `POST /markets/refresh` - Fetch news & create markets
- `GET /timelines` - List simulation timelines
- See API docs at `http://localhost:8000/docs`

### Scheduler (optional)

Runs the three-tier simulation tick system:

- **MICRO** (10s) - Price updates, yield distribution
- **NARRATIVE** (60s) - News checks, virality detection
- **MACRO** (300s) - Season end, evolution

```bash
# Start with scheduler
docker-compose --profile scheduler up

# Or start scheduler separately
docker-compose up scheduler
```

## Volume Mounts

| Container Path | Host Path | Purpose |
|----------------|-----------|---------|
| `/app/data` | `../data` | Simulation state (markets, economy, timelines) |
| `/app/database.db` | `./database.db` | SQLite user database |
| `/app/.env` | `./.env` | API keys (read-only) |

### Data Directory Structure

```
data/
├── markets.json          # Betting markets (persisted)
├── economy_state.json    # Yield manager state
├── stats.json            # Orchestrator statistics
├── world_state.json      # Global simulation state
├── backups/              # Automatic backups (max 5)
└── snapshots/            # Timeline snapshots
```

## Environment Variables

### Runtime Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Set to `production` for gunicorn |
| `PORT` | `8000` | API port |
| `HOST` | `0.0.0.0` | Bind address |
| `WORKERS` | `2` | Gunicorn workers (production only) |

### API Keys

All API keys are loaded from the `.env` file. See the Prerequisites section for the full list.

## Common Operations

### Start/Stop

```bash
# Start in foreground
docker-compose up

# Start in background
docker-compose up -d

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Rebuild

```bash
# After code changes
docker-compose up --build

# Force full rebuild
docker-compose build --no-cache
docker-compose up
```

### Shell Access

```bash
# Enter running container
docker-compose exec backend bash

# Run one-off command
docker-compose exec backend python -c "print('hello')"
```

## Health Checks

The backend container includes a health check that:

- Runs every 30 seconds
- Hits `GET /health`
- Marks unhealthy after 3 failures

Check health status:

```bash
docker-compose ps

# or

docker inspect project-seed-backend | grep -A 10 Health
```

## Production Deployment

### Environment Setup

```bash
export ENVIRONMENT=production
export WORKERS=4
```

### Run Production

```bash
ENVIRONMENT=production docker-compose up -d
```

### With External Database (PostgreSQL)

1. Update `DATABASE_URL` in docker-compose.yml:

```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

2. Remove SQLite volume mount

### Scaling (Advanced)

For high availability, consider:

- Running multiple backend instances behind a load balancer
- Using Redis for session storage
- Moving to PostgreSQL for the database

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
PORT=8001 docker-compose up
```

### Permission Denied

```bash
# Fix data directory permissions
chmod -R 755 ../data
chmod 644 ./database.db
```

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing .env file
# 2. Invalid API keys
# 3. Port conflict
```

### Database Locked

If you see "database is locked":

```bash
# Stop all containers
docker-compose down

# Remove lock file if exists
rm -f database.db-journal

# Restart
docker-compose up
```

### Out of Memory

Increase Docker's memory limit in Docker Desktop settings, or adjust the compose file:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

## Development Tips

### Hot Reload

In development mode, code changes auto-reload:

```bash
# Default is development mode
docker-compose up
```

### Running Tests

```bash
docker-compose exec backend pytest
```

### Accessing the Database

```bash
docker-compose exec backend python -c "
from backend.core.database import SessionLocal
db = SessionLocal()
# Your queries here
"
```

## Security Notes

1. **Never commit `.env`** - It's in `.gitignore`
2. **Use read-only mount** for `.env` (`:ro` flag)
3. **Non-root user** - Container runs as `app` user
4. **No exposed ports** except 8000 (API)

## File Reference

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build definition |
| `docker-compose.yml` | Service orchestration |
| `.dockerignore` | Excludes files from build |
| `start.sh` | Container startup script |
| `requirements.txt` | Python dependencies |
