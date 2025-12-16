# Mission System Migration Guide

## Overview

The old mission system has been **deprecated** in favor of the new `OperationCentre` component, which provides a professional trading terminal interface instead of spy movie aesthetics.

## What Changed

### Old System (Deprecated)
- `MissionCard` component in `app/situation-room/page.jsx`
- Simple card-based mission display
- Single "ACCEPT MISSION" button
- Basic mission details display

### New System (Recommended)
- `OperationCentre` component in `components/experience/OperationCentre.tsx`
- 3-phase professional trading interface:
  1. **Intelligence Briefing** - Purchase intel sources
  2. **Position Builder** - Build trading positions (LONG/SHORT/HEDGE/LIMIT)
  3. **Resolution & Debrief** - View results and impact analysis

## Migration Steps

### 1. Import the New Component

```tsx
import { OperationCentre } from "@/components/experience/OperationCentre";
```

### 2. Replace Mission Card Usage

**Before:**
```tsx
{missionList.map((mission) => (
  <MissionCard 
    key={mission.id} 
    mission={mission} 
    onAccept={handleAcceptMission}
  />
))}
```

**After:**
```tsx
<OperationCentre
  operationId={mission.id}
  operationTitle={mission.title}
  operationDescription={mission.briefing || mission.description}
  intelSources={transformToIntelSources(mission)}
  onIntelAccess={handleIntelAccess}
  onPositionBuild={handlePositionBuild}
  onOperationComplete={handleOperationComplete}
  result={mission.result}
/>
```

### 3. Transform Mission Data to Intel Sources

```tsx
function transformToIntelSources(mission) {
  return [
    {
      id: "cardinal",
      name: "CARDINAL",
      accuracy: Math.round(mission.success_probability * 100),
      cost: 25, // Calculate based on mission difficulty
      accessed: false,
      data: {
        keyFacts: [
          `Success probability: ${Math.round(mission.success_probability * 100)}%`,
          `Duration: ${mission.duration_minutes} minutes`,
          `Reward: $${mission.base_reward_usdc?.toFixed(2)}`,
        ],
        metrics: [
          { label: "Difficulty", value: mission.difficulty?.toString() || "N/A" },
          { label: "Type", value: mission.mission_type },
        ],
        confidence: Math.round(mission.success_probability * 100),
        timestamp: new Date().toISOString(),
      },
    },
    // Add more intel sources as needed
  ];
}
```

### 4. Implement API Handlers

```tsx
const handleIntelAccess = async (sourceId: string) => {
  // Call your API to purchase intel
  await fetch(`${API_BASE}/api/intel/${sourceId}/purchase`, {
    method: "POST",
  });
};

const handlePositionBuild = async (position: Position) => {
  // Call your API to build position
  await fetch(`${API_BASE}/api/positions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(position),
  });
};
```

## Component Features

### Phase 1: Intelligence Briefing
- Clean card layout with operation details
- Intel sources displayed as `DataCard` components
- `ConfidenceMeter` showing accuracy ratings
- `DataReveal` component for de-blurring purchased intel
- Structured data display (bullet points, metrics, key facts)

### Phase 2: Position Builder
- Four position types: LONG, SHORT, HEDGE, LIMIT
- Each position shows risk meter and potential returns
- Position builder with amount input and quick percentage buttons
- Projected outcomes (Win/Loss) display

### Phase 3: Resolution & Debrief
- Results dashboard with key metrics
- Impact analysis showing affected markets
- XP/Clearance progress indicators
- Next operations recommendations

## Benefits

1. **Professional Design**: Trading terminal aesthetic, not spy movie props
2. **Better UX**: Clear 3-phase flow with smooth transitions
3. **Reusable Components**: Uses experience component library
4. **Data-Driven**: Structured data display instead of prose
5. **Extensible**: Easy to add new features and intel sources

## Deprecation Timeline

- **Phase 1** (Current): Old system marked as deprecated, new system available
- **Phase 2** (Next Release): Old system removed from main codebase
- **Phase 3** (Future): Complete migration to OperationCentre

## Support

For questions or issues with migration, see:
- `components/experience/OperationCentre.tsx` - Main component
- `components/experience/OperationCentre.example.tsx` - Usage examples


