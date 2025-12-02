# Docker Quickstart Guide

## Prerequisites

- Docker Desktop installed
- `.env` file in `backend/` with API keys

## Quick Start (30 seconds)

```bash
cd backend

# Build and run
docker-compose up --build

# That's it! API is at http://localhost:8000
```

## Verify It's Working

```bash
# Health check
curl http://localhost:8000/health

# List markets
curl http://localhost:8000/markets

# Fetch news and create markets
curl -X POST http://localhost:8000/markets/refresh
```

## Common Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Start with scheduler (runs simulation ticks)
docker-compose --profile scheduler up
```

## Data Persistence

Your data survives container restarts:

| Data | Location | Mount |
|------|----------|-------|
| Markets, Economy | `../data/` | `/app/data` |
| Database | `./database.db` | `/app/database.db` |
| API Keys | `./.env` | `/app/.env` |

## Troubleshooting

### "Port 8000 already in use"

```bash
# Find what's using it
lsof -i :8000

# Or change the port
PORT=8001 docker-compose up
```

### "Permission denied" on data directory

```bash
# Fix permissions
chmod -R 755 ../data
```

### Container keeps restarting

```bash
# Check logs
docker-compose logs backend

# Common issue: missing .env file
ls -la .env
```

## Environment Variables

Required in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Optional (for full functionality):

```
GNEWS_API_KEY=...
NEWSAPI_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
# ... etc
```

## Production Deployment

```bash
# Set production mode
ENVIRONMENT=production docker-compose up -d

# With more workers
WORKERS=4 ENVIRONMENT=production docker-compose up -d
```
