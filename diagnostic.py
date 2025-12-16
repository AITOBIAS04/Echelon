#!/usr/bin/env python3
"""
Echelon Backend Diagnostic Script
==================================

Tests all backend endpoints and identifies what's working vs broken.

Usage:
    python diagnostic.py

Requirements:
    pip install httpx
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINTS = [
    # Core endpoints
    ("GET", "/", "Root/Health Check"),
    ("GET", "/health", "Health Endpoint"),
    ("GET", "/docs", "API Documentation"),
    
    # World State
    ("GET", "/world-state", "World State"),
    
    # Markets
    ("GET", "/markets", "All Markets"),
    ("GET", "/api/markets", "API Markets"),
    
    # Timelines
    ("GET", "/timelines", "All Timelines"),
    ("GET", "/api/timelines", "API Timelines"),
    
    # Situation Room
    ("GET", "/api/situation-room/state", "Situation Room State"),
    ("GET", "/api/situation-room/missions", "Active Missions"),
    ("GET", "/api/situation-room/intel", "Intel Market"),
    ("GET", "/api/situation-room/treaties", "Treaties"),
    ("GET", "/api/situation-room/narratives", "Storylines/Narratives"),
    ("GET", "/api/situation-room/tension", "Global Tension Index"),
    ("GET", "/api/situation-room/live-feed", "Live Feed"),
    
    # Agents
    ("GET", "/api/agents", "All Agents"),
    ("GET", "/api/agents/status", "Agent Status"),
    
    # Simulation
    ("GET", "/api/simulation/status", "Simulation Status"),
    
    # OSINT
    ("GET", "/api/osint/signals", "OSINT Signals"),
    ("GET", "/api/osint/tension", "Global Tension Index"),
]


async def test_endpoint(client: httpx.AsyncClient, method: str, path: str, name: str) -> dict:
    """Test a single endpoint."""
    url = f"{BASE_URL}{path}"
    result = {
        "name": name,
        "method": method,
        "path": path,
        "status": None,
        "response_type": None,
        "data_preview": None,
        "error": None,
    }
    
    try:
        if method == "GET":
            response = await client.get(url, timeout=5.0)
        elif method == "POST":
            response = await client.post(url, timeout=5.0)
        else:
            result["error"] = f"Unknown method: {method}"
            return result
        
        result["status"] = response.status_code
        
        # Try to parse JSON
        try:
            data = response.json()
            result["response_type"] = "json"
            
            # Preview the data
            if isinstance(data, dict):
                result["data_preview"] = {k: type(v).__name__ for k, v in list(data.items())[:5]}
                result["keys"] = list(data.keys())
                
                # Check if it's empty
                if all(v in [None, [], {}, "", 0] for v in data.values()):
                    result["warning"] = "All values are empty/null"
                    
            elif isinstance(data, list):
                result["data_preview"] = f"List with {len(data)} items"
                if len(data) == 0:
                    result["warning"] = "Empty list"
            else:
                result["data_preview"] = str(data)[:100]
                
        except json.JSONDecodeError:
            result["response_type"] = "text/html"
            result["data_preview"] = response.text[:100] if response.text else "(empty)"
            
    except httpx.ConnectError:
        result["error"] = "Connection refused - is the backend running?"
    except httpx.TimeoutException:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)
    
    return result


async def run_diagnostics():
    """Run all diagnostic tests."""
    print("=" * 70)
    print("ECHELON BACKEND DIAGNOSTIC")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        # First, check if backend is running at all
        print("\n🔌 Testing connection to backend...")
        try:
            response = await client.get(f"{BASE_URL}/", timeout=3.0)
            print(f"   ✅ Backend is responding (status: {response.status_code})")
        except httpx.ConnectError:
            print("   ❌ Backend is NOT running!")
            print(f"\n   Start it with: cd backend && uvicorn backend.main:app --reload")
            return
        except Exception as e:
            print(f"   ⚠️  Backend responded but with error: {e}")
        
        # Test all endpoints
        print("\n📡 Testing endpoints...\n")
        
        results = []
        for method, path, name in ENDPOINTS:
            result = await test_endpoint(client, method, path, name)
            results.append(result)
            
            # Print result
            if result["error"]:
                status_icon = "❌"
                status_text = f"ERROR: {result['error']}"
            elif result["status"] == 200:
                if result.get("warning"):
                    status_icon = "⚠️"
                    status_text = f"OK but {result['warning']}"
                else:
                    status_icon = "✅"
                    status_text = "OK"
            elif result["status"] == 404:
                status_icon = "🔍"
                status_text = "NOT FOUND"
            elif result["status"] == 500:
                status_icon = "💥"
                status_text = "SERVER ERROR"
            else:
                status_icon = "❓"
                status_text = f"Status {result['status']}"
            
            print(f"{status_icon} {name}")
            print(f"   {method} {path} → {status_text}")
            if result.get("data_preview"):
                print(f"   Data: {result['data_preview']}")
            print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        working = [r for r in results if r["status"] == 200 and not r.get("warning")]
        empty = [r for r in results if r.get("warning")]
        not_found = [r for r in results if r["status"] == 404]
        errors = [r for r in results if r["error"] or r["status"] in [500, 502, 503]]
        
        print(f"\n✅ Working: {len(working)}")
        for r in working:
            print(f"   - {r['name']}")
        
        print(f"\n⚠️  Empty/No Data: {len(empty)}")
        for r in empty:
            print(f"   - {r['name']}: {r['warning']}")
        
        print(f"\n🔍 Not Found (404): {len(not_found)}")
        for r in not_found:
            print(f"   - {r['name']} ({r['path']})")
        
        print(f"\n❌ Errors: {len(errors)}")
        for r in errors:
            print(f"   - {r['name']}: {r.get('error') or f'Status {r['status']}'}")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)
        
        if not_found:
            print("\n🔧 Missing endpoints need to be created in the FastAPI backend:")
            for r in not_found:
                print(f"   @app.get('{r['path']}')")
        
        if empty:
            print("\n🔧 Empty endpoints need data generators:")
            print("   - Run the simulation to populate data")
            print("   - Or seed with mock data on startup")
        
        print("\n")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())



