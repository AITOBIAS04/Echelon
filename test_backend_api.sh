#!/bin/bash
# Test Railway backend API endpoints
# Usage: ./test_backend_api.sh YOUR_RAILWAY_URL

RAILWAY_URL="${1:-https://your-backend-production.up.railway.app}"

echo "🧪 Testing Railway Backend API"
echo "URL: $RAILWAY_URL"
echo ""

echo "1. Testing /health endpoint..."
curl -s "$RAILWAY_URL/health" | head -20
echo ""
echo ""

echo "2. Testing /api/v1/butterfly/timelines/health..."
curl -s "$RAILWAY_URL/api/v1/butterfly/timelines/health?limit=8" | head -50
echo ""
echo ""

echo "3. Testing /api/v1/butterfly/wing-flaps..."
curl -s "$RAILWAY_URL/api/v1/butterfly/wing-flaps?limit=20" | head -50
echo ""
echo ""

echo "4. Testing /api/v1/paradox/active..."
curl -s "$RAILWAY_URL/api/v1/paradox/active" | head -50
echo ""
echo ""

echo "✅ Test complete!"
echo ""
echo "If you see JSON data above, your backend is working."
echo "If you see errors, check Railway logs."

