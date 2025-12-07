# Testing Situation Room API Endpoints

## Commands to Run

### 1. Check Game State
```bash
curl http://localhost:8000/api/situation-room/state
```

**Expected Response:**
```json
{
  "global_tension": 0.5,
  "chaos_index": 0.1,
  "faction_power": {
    "eastern_bloc": 0.25,
    "western_alliance": 0.25,
    "corporate": 0.2,
    "underground": 0.15,
    "non_aligned": 0.15
  },
  "active_missions": 0,
  "recent_signals": [],
  "narrative_war": {...}
}
```

### 2. Check Missions
```bash
curl http://localhost:8000/api/situation-room/missions
```

**Expected Response:**
```json
{
  "missions": []
}
```

Or if missions exist:
```json
{
  "missions": [
    {
      "id": "mission_123",
      "codename": "Operation Shadow",
      "title": "Verify Intelligence",
      "mission_type": "intelligence",
      "difficulty": 3,
      "base_reward_usdc": 45.0,
      "status": "pending",
      ...
    }
  ]
}
```

### 3. Check System Status
```bash
curl http://localhost:8000/api/situation-room/status
```

**Expected Response:**
```json
{
  "status": "online",
  "tick_count": 0,
  "uploader_stats": {...},
  "missions_active": 0,
  "last_tick": null
}
```

## Troubleshooting

### If you get "Connection refused":
- Make sure the backend is running: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Check if port 8000 is in use: `lsof -i :8000`

### If you get 404:
- Verify the router is included in `main.py`
- Check that `backend/api/situation_room_routes.py` exists
- Ensure `backend/__init__.py` and `backend/api/__init__.py` exist

### If you get empty missions:
- The scheduler needs to be running to generate missions
- Run: `python3 simulation/situation-room/scheduler.py`
- Or inject a test signal: `curl -X POST http://localhost:8000/api/situation-room/test/inject-signal -H "Content-Type: application/json" -d '{"category": "geopolitical", "high_urgency": true}'`

### Pretty Print JSON Response:
```bash
curl http://localhost:8000/api/situation-room/state | python3 -m json.tool
curl http://localhost:8000/api/situation-room/missions | python3 -m json.tool
```

## Expected Behavior

1. **State Endpoint**: Should return game state even if no missions exist
2. **Missions Endpoint**: Will return empty array `[]` if no missions have been generated yet
3. **Status Endpoint**: Should always return system status

## Next Steps

If missions are empty:
1. Start the Situation Room scheduler
2. Wait for OSINT signals to be processed
3. Missions will be auto-generated from signals
4. Or inject a test signal to generate a mission immediately

