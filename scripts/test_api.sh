#!/bin/bash
# Test script for Butler webhooks and Scheduler API

API_BASE="http://localhost:8000"

echo "=========================================="
echo "ECHELON API TEST SUITE"
echo "=========================================="

# Check if server is running
echo -e "\n1. Health Check..."
curl -s "$API_BASE/health" | head -c 100
echo ""

# Test Butler webhook test endpoint
echo -e "\n2. Butler Command Tests..."

echo -e "\n   Testing 'fork the fed market'..."
curl -s -X POST "$API_BASE/api/butler/test?raw_message=fork%20the%20fed%20market" | python3 -m json.tool 2>/dev/null | head -20

echo -e "\n   Testing 'hire CARDINAL to analyse tankers'..."
curl -s -X POST "$API_BASE/api/butler/test?raw_message=hire%20CARDINAL%20to%20analyse%20tankers" | python3 -m json.tool 2>/dev/null | head -20

echo -e "\n   Testing 'list agents'..."
curl -s -X POST "$API_BASE/api/butler/test?raw_message=list%20agents" | python3 -m json.tool 2>/dev/null | head -20

# Test Scheduler endpoints
echo -e "\n3. Scheduler Tests..."

echo -e "\n   Getting scheduler status..."
curl -s "$API_BASE/api/scheduler/status" | python3 -m json.tool 2>/dev/null

echo -e "\n   Starting scheduler..."
curl -s -X POST "$API_BASE/api/scheduler/start" | python3 -m json.tool 2>/dev/null

echo -e "\n   Listing agents..."
curl -s "$API_BASE/api/scheduler/agents" | python3 -m json.tool 2>/dev/null

echo -e "\n   Running manual cycle for HAMMERHEAD..."
curl -s -X POST "$API_BASE/api/scheduler/run-cycle/HAMMERHEAD" | python3 -m json.tool 2>/dev/null | head -30

echo -e "\n   Getting Layer 1 stats..."
curl -s "$API_BASE/api/scheduler/layer1-stats" | python3 -m json.tool 2>/dev/null

echo -e "\n   Stopping scheduler..."
curl -s -X POST "$API_BASE/api/scheduler/stop" | python3 -m json.tool 2>/dev/null

# Test Operations API
echo -e "\n4. Operations API Tests..."

echo -e "\n   Getting game state..."
curl -s "$API_BASE/api/game-state" | python3 -m json.tool 2>/dev/null | head -20

echo -e "\n   Listing operations..."
curl -s "$API_BASE/api/operations" | python3 -m json.tool 2>/dev/null | head -30

echo -e "\n   Listing agents..."
curl -s "$API_BASE/api/agents" | python3 -m json.tool 2>/dev/null | head -20

echo -e "\n   Getting signals..."
curl -s "$API_BASE/api/signals?limit=5" | python3 -m json.tool 2>/dev/null

echo -e "\n=========================================="
echo "TEST SUITE COMPLETE"
echo "=========================================="
