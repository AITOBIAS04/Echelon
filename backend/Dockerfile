# Project Seed Backend Dockerfile
# ================================
# Multi-stage build for optimized production image

# --- Stage 1: Builder ---
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# --- Stage 2: Production ---
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN addgroup --system app && adduser --system --group app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
# Install websockets first, then all other packages
# Use --no-upgrade to prevent pip from upgrading websockets when installing uvicorn
RUN pip install --no-cache websockets==11.0.3 && \
    pip install --no-cache --no-upgrade /wheels/* && \
    python -c "import websockets; v=websockets.__version__; assert v.startswith('11.'), f'Wrong version: {v}'; import websockets.legacy.handshake; print(f'✅ websockets {v} with legacy module verified')"

# Copy application code
COPY . .

# Create symlink so 'from backend.X' imports work
# (Railway copies backend/* to /app/*, but code expects backend/ prefix)
RUN ln -s /app /app/backend

# Create data directories
RUN mkdir -p data data/backups data/snapshots && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend \
    ENVIRONMENT=production \
    PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; import requests; requests.get(f'http://localhost:{os.environ.get(\"PORT\", 8000)}/health')" || exit 1

# Start command - use Python entrypoint to read PORT from env
CMD ["python", "entrypoint.py"]

