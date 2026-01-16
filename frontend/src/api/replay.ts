import type { ForkReplay, ReplayPointer, ReplayForkOption } from '../types/replay';

/**
 * Mock Replay API
 * ===============
 * 
 * Provides mock data for fork replay functionality.
 * In production, this would call the actual API endpoint.
 */

/**
 * Generate a plausible price path for a fork option
 * 
 * @param startPrice - Starting price (0-1)
 * @param endPrice - Ending price (0-1)
 * @param durationMs - Duration in milliseconds
 * @param volatility - Price volatility factor (0-1)
 * @returns Array of price path points
 */
function generatePricePath(
  startPrice: number,
  endPrice: number,
  durationMs: number,
  volatility: number = 0.1
): { tMs: number; price: number }[] {
  const points: { tMs: number; price: number }[] = [];
  const numPoints = 20; // Generate 20 data points
  
  for (let i = 0; i <= numPoints; i++) {
    const progress = i / numPoints;
    const tMs = Math.floor(progress * durationMs);
    
    // Linear interpolation with some random volatility
    const basePrice = startPrice + (endPrice - startPrice) * progress;
    const randomOffset = (Math.random() - 0.5) * volatility;
    const price = Math.max(0, Math.min(1, basePrice + randomOffset));
    
    points.push({ tMs, price });
  }
  
  return points;
}

/**
 * Get Fork Replay
 * 
 * Returns replay data for a specific fork, including price paths,
 * disclosure events, and outcome information.
 * 
 * @param pointer - Replay pointer identifying the fork
 * @returns Promise resolving to ForkReplay
 */
export async function getForkReplay(pointer: ReplayPointer): Promise<ForkReplay> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));
  
  const now = new Date();
  const openedAt = new Date(now.getTime() - 2 * 60 * 60 * 1000); // 2 hours ago
  const lockedAt = new Date(now.getTime() - 1.5 * 60 * 60 * 1000); // 1.5 hours ago
  const executedAt = new Date(now.getTime() - 1 * 60 * 60 * 1000); // 1 hour ago
  const settledAt = executedAt;
  
  const durationMs = lockedAt.getTime() - openedAt.getTime();
  
  // Generate disclosure events
  const disclosureEvents = [
    {
      tMs: 5 * 60 * 1000, // 5 minutes after opening
      type: 'sabotage_disclosed' as const,
      label: 'Shadow Broker disclosed sabotage attack',
    },
    {
      tMs: 15 * 60 * 1000, // 15 minutes after opening
      type: 'evidence_flip' as const,
      label: 'RavenPack evidence contradicted earlier reports',
    },
    {
      tMs: 30 * 60 * 1000, // 30 minutes after opening
      type: 'paradox_spawn' as const,
      label: 'Paradox spawned in timeline',
    },
  ];
  
  // Generate price paths for options
  // Option 1: Starts at 0.4, ends at 0.75 (chosen option)
  const option1PricePath = generatePricePath(0.4, 0.75, durationMs, 0.08);
  
  // Option 2: Starts at 0.6, ends at 0.25 (not chosen)
  const option2PricePath = generatePricePath(0.6, 0.25, durationMs, 0.08);
  
  const replay: ForkReplay = {
    timelineId: pointer.timelineId,
    forkId: pointer.forkId,
    forkQuestion: 'Will Iran issue an official statement within 24 hours?',
    options: [
      {
        label: 'Yes',
        pricePath: option1PricePath,
      },
      {
        label: 'No',
        pricePath: option2PricePath,
      },
    ],
    openedAt: openedAt.toISOString(),
    lockedAt: lockedAt.toISOString(),
    executedAt: executedAt.toISOString(),
    settledAt: settledAt.toISOString(),
    chosenOption: 'Yes',
    outcomeLabel: 'Iran issued statement confirming willingness for talks',
    disclosureEvents,
    notes: 'This fork showed significant price movement following the paradox spawn event. The Yes option gained momentum after evidence flip contradicted earlier bearish signals.',
  };
  
  return replay;
}
