# API Endpoint Testing Guide

## Market Endpoints

### 1. List Markets (Orchestrator - Dynamic)
```bash
curl http://localhost:8000/markets
```
Returns markets with IDs like: `MKT_mission_taipei_1764355935_micro`

### 2. List Markets (Static/Seeded)
```bash
curl http://localhost:8000/api/markets
```
Returns markets with IDs like: `trump_executive_order`, `ukraine_ceasefire`

### 3. Get Quote (Works with Orchestrator markets only)
```bash
# ✅ Works - Orchestrator market ID
curl "http://localhost:8000/markets/MKT_mission_taipei_1764355935_micro/quote?outcome=YES&amount=100"

# ❌ Doesn't work - Static market ID
curl "http://localhost:8000/markets/trump_executive_order/quote?outcome=YES&amount=100"
```

### 4. Trending Markets
```bash
curl "http://localhost:8000/markets/trending?limit=3"
```
Returns orchestrator markets sorted by volume.

## Summary

- **Quote endpoint** (`/markets/{id}/quote`) only works with **orchestrator markets**
- Use market IDs from `/markets` or `/markets/trending` for quotes
- Static markets from `/api/markets` are not supported by the quote endpoint yet
