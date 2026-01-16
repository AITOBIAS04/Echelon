# Experience Components

Professional trading terminal UI components for the prediction market platform.

## Components

### Core Primitives

- **DataReveal** - Blur-to-reveal animation for sensitive data
- **ConfidenceMeter** - Horizontal or circular confidence/risk gauge
- **LiveFeed** - Real-time terminal-style data feed
- **StatusIndicator** - Status dots with animations (LIVE, CRITICAL, PROCESSING, OFFLINE)
- **DataCard** - Glassmorphism card with priority borders
- **ProgressRing** - Circular progress indicator

### Composite Components

- **OperationCentre** - Complete 3-phase operation interface (replaces old mission system)

## Design System

### Colors
- Background: `#0a0a0f`, `#12121a`
- Primary: `#6366f1` (indigo)
- Success: `#22c55e` (green)
- Warning: `#f59e0b` (amber)
- Danger: `#ef4444` (red)
- Text: `#e2e8f0`, `#94a3b8`

### Fonts
- UI: `Inter` (sans-serif)
- Data/Numbers: `JetBrains Mono` (monospace)

### Aesthetic
Professional trading terminal (Bloomberg Terminal meets Palantir), NOT spy movie props.

## Usage

```tsx
import { 
  OperationCentre,
  DataCard,
  ConfidenceMeter 
} from "@/components/experience";

<OperationCentre
  operationId="op-001"
  operationTitle="Operation Nightfall"
  operationDescription="High-stakes intelligence operation"
  intelSources={intelSources}
  onIntelAccess={handleIntelAccess}
  onPositionBuild={handlePositionBuild}
/>
```

## Migration

See `MIGRATION_GUIDE.md` for migrating from the old mission system.

## Dependencies

- `lucide-react` - Icons
- `tailwindcss` - Styling

All animations use CSS/Tailwind utilities - no additional animation libraries required!

