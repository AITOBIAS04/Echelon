# Starting the Backend Server

## Quick Start

**From the project root:**

```bash
./backend/start_server.sh
```

This script will:
- ✅ Activate the virtual environment (Python 3.12)
- ✅ Set up PostgreSQL paths
- ✅ Start uvicorn with auto-reload
- ✅ Run on `http://0.0.0.0:8000`

## Manual Start

If you prefer to start manually:

```bash
# 1. Activate virtual environment
source backend/.venv/bin/activate

# 2. Set PostgreSQL path (macOS Homebrew)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# 3. Start server
cd /Users/tobyharber/Developer/prediction-market-monorepo.nosync
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Common Issues

### ❌ `ModuleNotFoundError: No module named 'fastapi'`

**Problem:** Running `uvicorn` without activating the virtual environment.

**Solution:** Always activate the virtual environment first:
```bash
source backend/.venv/bin/activate
```

Or use the startup script:
```bash
./backend/start_server.sh
```

### ❌ Wrong Python Version

**Problem:** Using system Python 3.14 instead of venv Python 3.12.

**Solution:** The startup script ensures the correct Python is used. Verify:
```bash
source backend/.venv/bin/activate
which python  # Should show: .../backend/.venv/bin/python
python --version  # Should show: Python 3.12.12
```

## Health Check

Once the server is running, test it:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc


