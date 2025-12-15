#!/bin/bash

# Test script for Project Seed API endpoints
# Run this after starting the backend server

API_BASE="http://localhost:8000"

echo "🧪 Testing Project Seed API Endpoints"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "1️⃣ Testing Health Check..."
echo "   Command: curl $API_BASE/health"
echo ""
response=$(curl -s -w "\n%{http_code}" "$API_BASE/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Health check failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 2: List Markets (before refresh)
echo "2️⃣ Testing List Markets (before refresh)..."
echo "   Command: curl $API_BASE/markets"
echo ""
response=$(curl -s -w "\n%{http_code}" "$API_BASE/markets")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Markets endpoint accessible${NC}"
    market_count=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null || echo "0")
    echo "   Current markets: $market_count"
    if [ "$market_count" = "0" ]; then
        echo -e "${YELLOW}   ℹ️  No markets yet - will create some in next step${NC}"
    fi
else
    echo -e "${RED}❌ Markets endpoint failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 3: Refresh Markets (fetch news and create markets)
echo "3️⃣ Testing Refresh Markets (this may take 10-30 seconds)..."
echo "   Command: curl -X POST $API_BASE/markets/refresh"
echo ""
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/markets/refresh")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Market refresh successful${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    # Extract stats
    events=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('events_ingested', 0))" 2>/dev/null || echo "0")
    markets=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('markets_created', 0))" 2>/dev/null || echo "0")
    echo ""
    echo "   📊 Summary:"
    echo "      - Events ingested: $events"
    echo "      - Markets created: $markets"
else
    echo -e "${RED}❌ Market refresh failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 4: List Markets (after refresh)
echo "4️⃣ Testing List Markets (after refresh)..."
echo "   Command: curl $API_BASE/markets"
echo ""
response=$(curl -s -w "\n%{http_code}" "$API_BASE/markets")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Markets endpoint accessible${NC}"
    market_count=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null || echo "0")
    filtered=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('filtered', 0))" 2>/dev/null || echo "0")
    echo "   Total markets: $market_count"
    echo "   Filtered (showing): $filtered"
    
    # Show first market if available
    if [ "$filtered" != "0" ]; then
        echo ""
        echo "   📋 First market preview:"
        echo "$body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
markets = data.get('markets', [])
if markets:
    m = markets[0]
    print(f\"      ID: {m.get('id', 'N/A')[:30]}...\")
    print(f\"      Title: {m.get('title', 'N/A')[:50]}\")
    print(f\"      Domain: {m.get('domain', 'N/A')}\")
    print(f\"      Virality: {m.get('virality_score', 0)}\")
" 2>/dev/null || echo "      (Could not parse market data)"
    fi
else
    echo -e "${RED}❌ Markets endpoint failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 5: Market Stats
echo "5️⃣ Testing Market Stats..."
echo "   Command: curl $API_BASE/markets/stats"
echo ""
response=$(curl -s -w "\n%{http_code}" "$API_BASE/markets/stats")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Stats endpoint accessible${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ Stats endpoint failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

echo "======================================"
echo "✅ Testing complete!"
echo ""
echo "💡 Tips:"
echo "   - If health check fails, make sure the server is running"
echo "   - If markets refresh fails, check your API keys in .env"
echo "   - View API docs at: http://localhost:8000/docs"
echo ""




