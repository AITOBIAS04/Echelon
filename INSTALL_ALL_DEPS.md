# Install All Dependencies

## Problem
Fresh venv doesn't have all packages installed yet.

## Solution: Install Requirements

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Install all dependencies from requirements.txt
python3 -m pip install --no-cache-dir -r requirements.txt
```

## Or Install Essential Packages Manually

If requirements.txt installation is slow, install essentials first:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Core packages
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi
python3 -m pip install --no-cache-dir pydantic sqlalchemy
python3 -m pip install --no-cache-dir python-jose passlib python-multipart
python3 -m pip install --no-cache-dir aiohttp httpx requests
python3 -m pip install --no-cache-dir anthropic
python3 -m pip install --no-cache-dir python-dotenv
```

## Verify Installation

```bash
# Check pydantic is installed
python3 -c "import pydantic; print('✅ pydantic works!')"

# Check other key packages
python3 -c "import fastapi, sqlalchemy, aiohttp; print('✅ All core packages work!')"
```

## Then Run Scheduler

After installing dependencies:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Run from backend directory
python3 simulation/situation-room/scheduler.py

# OR run as module from project root
cd /Users/tobyharber/Documents/prediction-market-monorepo
python3 -m backend.simulation.situation-room.scheduler
```

