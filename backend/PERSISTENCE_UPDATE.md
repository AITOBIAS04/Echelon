# Persistence System Integration

## Overview

All simulation state now persists across server restarts. This fixes critical bugs:
- **"Infinite Wealth" Bug**: YieldManager now saves `last_payout` timestamp
- **Market Loss**: Markets survive restarts and are loaded on startup
- **State Corruption**: Atomic writes prevent data loss

## New Files

### `backend/core/persistence_manager.py`
Unified state persistence system with:
- Atomic writes (temp file → rename)
- Automatic backups
- Thread-safe operations
- Auto-save background thread
- JSON serialization for complex objects

### Updated Files

1. **`backend/simulation/yield_manager.py`**
   - Added persistence layer
   - Saves `last_payout`, `stakes`, `apy`, `total_distributed`
   - Loads state on initialization
   - Prevents "infinite wealth" on restart

2. **`backend/core/event_orchestrator.py`**
   - Added persistence integration
   - Saves markets and stats after creation
   - Loads markets on startup
   - Markets survive server restarts

3. **`backend/main.py`**
   - Added `/health` endpoint for container orchestration
   - Checks database connectivity
   - Returns health status and version

4. **`backend/start.sh`**
   - Production-ready startup script
   - Supports both development and production modes
   - Uses gunicorn with uvicorn workers in production
   - Creates data directories automatically
   - Database initialization

5. **`backend/requirements.txt`**
   - Added `gunicorn` for production
   - Added `alembic` for migrations
   - Updated `uvicorn` to include standard extras

6. **`backend/Dockerfile`**
   - Multi-stage build for smaller image
   - Non-root user for security
   - Updated health check to use `/health` endpoint
   - Production environment variables

## Usage

### Persistence Manager

```python
from backend.core.persistence_manager import get_persistence_manager

pm = get_persistence_manager()

# Save state
pm.save("markets", markets_dict)

# Load state
markets = pm.load("markets", default={})

# Auto-save (background thread)
def get_all_states():
    return {
        "markets": markets_dict,
        "economy": economy_dict,
    }

pm.start_auto_save(get_all_states, interval=60)
```

### Yield Manager

```python
from backend.simulation.yield_manager import YieldManager

# Persistence enabled by default
manager = YieldManager(apy=0.05, enable_persistence=True)

# State is automatically saved after:
# - distribute_yield() (after payout)
# - add_stake() (after stake change)

# State is automatically loaded on initialization
```

### Event Orchestrator

```python
from backend.core.event_orchestrator import EventOrchestrator

orchestrator = EventOrchestrator()

# Markets are automatically saved after creation
market = orchestrator.create_market(event)

# Markets are automatically loaded on initialization
```

## Data Storage

All state is stored in `data/` directory:

```
data/
├── markets.json          # All betting markets
├── economy_state.json    # Yield manager state
├── world_state.json      # World state (if used)
├── orchestrator_stats.json  # Event orchestrator stats
├── backups/              # Automatic backups
└── snapshots/            # Timeline snapshots
```

## Health Check

The `/health` endpoint is available for container orchestration:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-27T16:00:00Z",
  "database": "ok",
  "version": "1.0.0"
}
```

## Production Deployment

### Environment Variables

```bash
ENVIRONMENT=production
PORT=8000
WORKERS=2
DATABASE_URL=sqlite:///./seed_production.db
```

### Docker

```bash
# Build
docker build -t project-seed-backend .

# Run
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e ENVIRONMENT=production \
  project-seed-backend
```

### Docker Compose

```bash
docker-compose up --build
```

## Testing

Run the persistence manager test:

```bash
python -m backend.core.persistence_manager
```

Test yield manager:

```bash
python -m backend.simulation.yield_manager
```

## Migration Notes

- Existing markets will be lost on first restart (expected)
- New markets created after update will persist
- Yield state will be reset on first restart (expected)
- Future payouts will be correctly tracked

## Future Enhancements

- Full market object restoration (currently metadata only)
- Database-backed persistence option
- Compression for large state files
- State versioning and migration




