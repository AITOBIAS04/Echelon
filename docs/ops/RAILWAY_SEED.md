# Seeding the Database on Railway

Your database tables are created, but they're empty. You need to seed them with initial data.

## Option 1: Using Railway CLI (Recommended)

1. **Install Railway CLI** (if not already installed):
   ```bash
   curl -fsSL https://railway.com/install.sh | sh
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link to your project**:
   ```bash
   railway link
   ```
   Select your project when prompted.

4. **Run the seed script**:
   ```bash
   railway run python -m scripts.seed_database
   ```

   Or if you're in the backend directory:
   ```bash
   cd backend
   railway run python -m scripts.seed_database
   ```

## Option 2: Using Railway Web Console

1. Go to your backend service in Railway
2. Click "Deployments" tab
3. Click on the latest deployment
4. Click "Shell" or "Terminal"
5. Run:
   ```bash
   python -m scripts.seed_database
   ```

## What Gets Seeded

The seed script creates:
- **Users**: Test users with different tiers
- **Agents**: 5 agents with different archetypes (SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE)
- **Timelines**: 3 initial timelines (Contagion, Treaty, Market)
- **Paradoxes**: 1 active paradox on the Contagion timeline
- **Wing Flaps**: Sample causality events
- **User Positions**: Initial user positions on timelines

## Verify Seeding

After seeding, check your database in Railway:
1. Go to your PostgreSQL service
2. Click "Data" or "Query" tab
3. Run: `SELECT COUNT(*) FROM users;`
4. Should return: `3` (or more if you've added users)

Or check via your backend API:
- `GET /api/v1/butterfly/timelines/health` - Should return timelines
- `GET /api/v1/paradox/active` - Should return active paradoxes

## Troubleshooting

**If seeding fails:**
- Make sure `DATABASE_URL` is set in your backend service
- Check that migrations completed successfully
- Verify `USE_MOCKS=false` is set

**If tables are still empty:**
- Check seed script logs for errors
- Verify database connection is working
- Make sure you're running the seed script in the correct directory

