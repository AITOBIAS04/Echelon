#!/bin/bash
# Fix pip list hang - usually caused by corrupted site-packages

set -e

echo "🔧 Fixing pip list hang issue..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Activate venv
source .venv/bin/activate

echo "📦 Checking site-packages location..."
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Site-packages: $SITE_PACKAGES"

echo ""
echo "🧹 Cleaning potentially corrupted package metadata..."

# Remove .pth files that might be corrupted
find "$SITE_PACKAGES" -name "*.pth" -type f -delete 2>/dev/null || true

# Remove .dist-info directories that might be corrupted
find "$SITE_PACKAGES" -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove .egg-info directories
find "$SITE_PACKAGES" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Cleaned metadata files"
echo ""
echo "🧪 Testing pip list again..."
timeout 10 python3 -m pip list || {
    echo ""
    echo "❌ pip list still hangs. Recreating venv..."
    deactivate 2>/dev/null || true
    rm -rf .venv
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✅ Fresh venv created"
    echo "Now try: python3 -m pip install --no-cache-dir uvicorn fastapi"
}

