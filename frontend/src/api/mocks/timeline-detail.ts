import type { TimelineDetail } from '../../types/timeline-detail';

/**
 * Mock Timeline Detail Data
 * =========================
 * 
 * Provides sample timeline detail data for development and testing.
 */

/**
 * Get Mock Timeline Detail
 * 
 * Returns a mock TimelineDetail object for the given timeline ID.
 * 
 * @param timelineId - Timeline identifier
 * @returns Promise resolving to TimelineDetail
 */
export async function getMockTimelineDetail(timelineId: string): Promise<TimelineDetail> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));

  // Generate mock data based on timeline ID
  const now = new Date();
  const sixHoursAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000);

  // Generate health history (last 6 hours, every hour)
  const healthHistory = Array.from({ length: 6 }, (_, i) => {
    const timestamp = new Date(now.getTime() - (5 - i) * 60 * 60 * 1000);
    return {
      timestamp: timestamp.toISOString(),
      stability: 60 + Math.sin(i) * 10 + Math.random() * 5,
      logicGap: 35 + Math.cos(i) * 8 + Math.random() * 3,
      entropyRate: -2.0 - Math.random() * 0.5,
    };
  });

  // Mock fork events
  const forkTape = [
    {
      id: 'fork_001',
      timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      status: 'open' as const,
      question: 'Will the timeline reach 70% stability before expiration?',
      options: [
        {
          id: 'opt_yes',
          label: 'Yes',
          price: 0.65,
          priceHistory: Array.from({ length: 10 }, (_, i) => ({
            timestamp: new Date(now.getTime() - (10 - i) * 10 * 60 * 1000).toISOString(),
            price: 0.6 + Math.random() * 0.1,
          })),
        },
        {
          id: 'opt_no',
          label: 'No',
          price: 0.35,
          priceHistory: Array.from({ length: 10 }, (_, i) => ({
            timestamp: new Date(now.getTime() - (10 - i) * 10 * 60 * 1000).toISOString(),
            price: 0.3 + Math.random() * 0.1,
          })),
        },
      ],
      lockedAt: new Date(now.getTime() + 30 * 60 * 1000).toISOString(),
    },
  ];

  // Mock sabotage events
  const sabotageHistory = [
    {
      id: 'sab_001',
      timestamp: new Date(now.getTime() - 45 * 60 * 1000).toISOString(),
      phase: 'executed' as const,
      saboteurId: 'agent_123',
      saboteurName: 'Shadow Operative',
      sabotageType: 'Logic Bomb',
      stakeAmount: 5000,
      effectSize: -8.5,
      disclosedAt: new Date(now.getTime() - 50 * 60 * 1000).toISOString(),
      executedAt: new Date(now.getTime() - 45 * 60 * 1000).toISOString(),
      slashed: false,
    },
    {
      id: 'sab_002',
      timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      phase: 'slashed' as const,
      saboteurId: 'agent_456',
      saboteurName: 'Chaos Agent',
      sabotageType: 'Stability Attack',
      stakeAmount: 3000,
      effectSize: -5.2,
      disclosedAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      slashed: true,
    },
  ];

  // Mock evidence entries
  const evidenceLedger = [
    {
      id: 'ev_001',
      timestamp: new Date(now.getTime() - 15 * 60 * 1000).toISOString(),
      source: 'RavenPack',
      headline: 'Breaking: Key stakeholders express confidence in timeline resolution',
      sentiment: 'bullish' as const,
      confidence: 85,
      impactOnGap: -2.3,
    },
    {
      id: 'ev_002',
      timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(),
      source: 'Spire AIS',
      headline: 'Conflicting signals detected in market sentiment analysis',
      sentiment: 'bearish' as const,
      confidence: 72,
      contradiction: {
        conflictsWith: 'ev_001',
        reason: 'Opposing sentiment indicators',
      },
      impactOnGap: 3.1,
    },
    {
      id: 'ev_003',
      timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(),
      source: 'X API',
      headline: 'Public discussion trending with mixed opinions',
      sentiment: 'neutral' as const,
      confidence: 45,
      impactOnGap: 0.5,
    },
  ];

  // Mock paradox status (null for most timelines, active for some)
  const hasParadox = timelineId.includes('contagion') || timelineId.includes('mumbai');
  const paradoxStatus = hasParadox
    ? {
        active: true,
        spawnedAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        severity: 'CLASS_2_SEVERE' as const,
        triggerReason: 'logic_gap' as const,
        triggerValue: 62,
        countdown: 1800, // 30 minutes
        extractionCost: {
          usdc: 15000,
          echelon: 5000,
          sanityCost: 25,
        },
        extractionHistory: [
          {
            timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(),
            agentId: 'agent_789',
            agentName: 'Paradox Hunter',
            success: false,
            cost: 15000,
            sanityCost: 25,
          },
        ],
      }
    : null;

  // Mock user position (optional, only for some timelines)
  const hasPosition = timelineId.includes('oil') || timelineId.includes('hormuz');
  const userPosition = hasPosition
    ? {
        side: 'YES' as const,
        shares: 1500,
        avgPrice: 0.42,
        currentValue: 675,
        unrealisedPnl: 15.5,
        burnAtCollapse: 675,
      }
    : undefined;

  return {
    id: timelineId,
    name: timelineId.includes('oil')
      ? 'Oil Crisis - Hormuz Strait'
      : timelineId.includes('fed')
      ? 'Fed Rate Decision - January 2026'
      : timelineId.includes('contagion')
      ? 'Contagion Zero - Mumbai'
      : timelineId.includes('ghost')
      ? 'Ghost Tanker - Venezuela'
      : 'Timeline Example',
    slug: timelineId.replace('tl_', '').replace(/_/g, '-'),
    description: 'A detailed timeline tracking key events and market dynamics.',
    createdAt: sixHoursAgo.toISOString(),
    expiresAt: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    yesPrice: 0.45,
    noPrice: 0.55,
    stability: 54.7,
    logicGap: 42,
    entropyRate: -2.1,
    healthHistory,
    forkTape,
    sabotageHistory,
    evidenceLedger,
    paradoxStatus,
    userPosition,
  };
}
