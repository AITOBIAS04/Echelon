# Frontend Development Server

## Quick Start

```bash
cd frontend
npm run dev
# or
bun run dev
```

The server will start on `http://localhost:3000`

## Configuration

- **API URL**: Configured in `.env.local` as `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Port**: Default Next.js port 3000
- **Hot Reload**: Enabled automatically

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Troubleshooting

### Port Already in Use
If port 3000 is busy:
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm run dev
```

### Module Not Found Errors
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
# or
bun install
```

### API Connection Issues
Ensure backend is running on `http://localhost:8000`:
```bash
cd ../backend
source venv/bin/activate
PYTHONPATH=$(pwd) python -m backend.main
```

## Key Pages

- `/` - Home page
- `/situation-room` - Situation Room (with new experience components)
- `/markets` - Markets page
- `/timelines` - Timelines page
- `/dashboard` - User dashboard

## New Experience Components

All new components are in `components/experience/`:
- `OperationCentre` - 3-phase operation interface
- `NetworkGraph` - Network visualization
- `SignalIntelligence` - Real-time data terminal
- `Handler` - AI assistant chat
- UI Primitives: `DataReveal`, `ConfidenceMeter`, `LiveFeed`, `StatusIndicator`, `DataCard`, `ProgressRing`


