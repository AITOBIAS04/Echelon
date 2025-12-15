# API Testing Guide

## Quick Test Commands

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-27T16:00:00.000000Z",
  "database": "ok",
  "version": "1.0.0"
}
```

### 2. Refresh Markets (Fetch News & Create Markets)

```bash
curl -X POST http://localhost:8000/markets/refresh
```

**Expected Response:**
```json
{
  "success": true,
  "events_ingested": 15,
  "high_virality_events": 3,
  "markets_created": 3,
  "total_active_markets": 3
}
```

**Note:** This may take 10-30 seconds as it:
- Fetches news from multiple APIs
- Calculates virality scores
- Creates betting markets
- Dispatches agents

### 3. List Markets

```bash
curl http://localhost:8000/markets
```

**Expected Response:**
```json
{
  "markets": [
    {
      "id": "MKT_news_123_narrative",
      "title": "Bitcoin Reaches New All-Time High",
      "description": "BTC breaks $100k barrier...",
      "domain": "crypto",
      "duration": "narrative",
      "status": "OPEN",
      "created_at": "2025-11-27T16:00:00Z",
      "expires_at": "2025-12-04T16:00:00Z",
      "outcomes": ["YES", "NO"],
      "outcome_odds": {"YES": 0.65, "NO": 0.35},
      "total_volume": 0.0,
      "virality_score": 85.5
    }
  ],
  "total": 3,
  "filtered": 3
}
```

### 4. Market Stats

```bash
curl http://localhost:8000/markets/stats
```

**Expected Response:**
```json
{
  "total_markets": 3,
  "total_volume": 0.0,
  "by_domain": {
    "crypto": 1,
    "finance": 1,
    "sports": 1
  },
  "by_duration": {
    "micro": 0,
    "narrative": 2,
    "macro": 1
  },
  "by_status": {
    "OPEN": 3,
    "CLOSED": 0,
    "SETTLED": 0
  },
  "orchestrator_stats": {
    "events_processed": 15,
    "markets_created": 3,
    "markets_auto_created": 3
  }
}
```

## Automated Testing Script

Run the automated test script:

```bash
cd backend
./test_endpoints.sh
```

This script will:
1. ✅ Test health check
2. ✅ List markets (before refresh)
3. ✅ Refresh markets (fetch news)
4. ✅ List markets (after refresh)
5. ✅ Get market stats

## Using jq for Pretty Output

If you have `jq` installed:

```bash
# Health check with formatting
curl -s http://localhost:8000/health | jq

# Markets with formatting
curl -s http://localhost:8000/markets | jq '.markets[] | {id, title, virality_score}'

# Stats summary
curl -s http://localhost:8000/markets/stats | jq '{total_markets, total_volume, by_domain}'
```

## Filtering Markets

### By Domain
```bash
curl "http://localhost:8000/markets?domain=crypto"
```

### By Duration
```bash
curl "http://localhost:8000/markets?duration=narrative"
```

### By Status
```bash
curl "http://localhost:8000/markets?status=OPEN"
```

### Combined Filters
```bash
curl "http://localhost:8000/markets?domain=finance&duration=narrative&status=OPEN&limit=10"
```

## Troubleshooting

### Health Check Fails

**Error:** `Connection refused` or `Failed to connect`

**Solution:**
1. Make sure the server is running:
   ```bash
   # Docker
   docker-compose ps
   
   # Local
   ps aux | grep uvicorn
   ```

2. Check if port 8000 is in use:
   ```bash
   lsof -i :8000
   ```

### Markets Refresh Returns 0 Events

**Possible Causes:**
1. Missing API keys in `.env`
2. API rate limits exceeded
3. Network issues

**Solution:**
1. Check `.env` file has required keys:
   ```bash
   cat backend/.env | grep API_KEY
   ```

2. Check server logs:
   ```bash
   docker-compose logs backend
   ```

### Database Error in Health Check

**Error:** `"database": "error: ..."`

**Solution:**
1. Check database file permissions:
   ```bash
   ls -la backend/database.db
   ```

2. Recreate database:
   ```bash
   rm backend/database.db
   docker-compose restart backend
   ```

## Interactive API Documentation

Visit the Swagger UI for interactive testing:

```
http://localhost:8000/docs
```

This provides:
- All available endpoints
- Request/response schemas
- Try-it-out functionality
- Authentication testing

## Example Workflow

```bash
# 1. Start the server
cd backend
docker-compose up -d

# 2. Wait for health check
sleep 5
curl http://localhost:8000/health

# 3. Refresh markets (fetch news)
curl -X POST http://localhost:8000/markets/refresh

# 4. List created markets
curl http://localhost:8000/markets | jq '.markets[] | {title, domain, virality_score}'

# 5. Get stats
curl http://localhost:8000/markets/stats | jq
```

## Performance Notes

- **Health check**: < 100ms
- **List markets**: < 200ms
- **Refresh markets**: 10-30 seconds (depends on API response times)
- **Market stats**: < 100ms

## Next Steps

After testing the endpoints:

1. **Create a user account:**
   ```bash
   curl -X POST http://localhost:8000/users/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass"}'
   ```

2. **Login and get token:**
   ```bash
   curl -X POST http://localhost:8000/token \
     -d "username=testuser&password=testpass"
   ```

3. **Place a bet:**
   ```bash
   TOKEN="your_token_here"
   curl -X POST http://localhost:8000/markets/MKT_xxx/bet \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"outcome": "YES", "amount": 50}'
   ```




