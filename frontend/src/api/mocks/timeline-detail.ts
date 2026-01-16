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
export async function getMockTimelineDetail(
  timelineId: string
): Promise<TimelineDetail | null> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 200));

  const now = new Date();
  const expiresIn48h = new Date(now.getTime() + 48 * 60 * 60 * 1000);
  const createdAt = new Date(now.getTime() - 24 * 60 * 60 * 1000); // Created 24h ago

  // Special handling for Oil Crisis timeline
  if (timelineId === 'tl_oil_hormuz_001') {
    // Generate 24 health history data points (one per hour for last 24h)
    // Stability trending down: 85% → 54.7%
    // Logic Gap trending up: 15% → 42%
    // Entropy rate accelerating: -0.8% → -2.1%
    const healthHistory = Array.from({ length: 24 }, (_, i) => {
      const hoursAgo = 23 - i;
      const timestamp = new Date(now.getTime() - hoursAgo * 60 * 60 * 1000);
      
      // Linear interpolation for trends
      const progress = i / 23; // 0 to 1
      
      // Stability: 85% → 54.7% (downward trend)
      const stability = 85 - (85 - 54.7) * progress + (Math.random() - 0.5) * 2;
      
      // Logic Gap: 15% → 42% (upward trend)
      const logicGap = 15 + (42 - 15) * progress + (Math.random() - 0.5) * 2;
      
      // Entropy rate: -0.8% → -2.1% (accelerating downward)
      const entropyRate = -0.8 - (2.1 - 0.8) * progress + (Math.random() - 0.5) * 0.2;
      
      return {
        timestamp: timestamp.toISOString(),
        stability: Math.max(0, Math.min(100, stability)),
        logicGap: Math.max(0, Math.min(100, logicGap)),
        entropyRate: Math.max(-10, Math.min(0, entropyRate)),
      };
    });

    // Fork tape: 5 forks (2 settled, 1 locked, 1 repricing, 1 open)
    const forkTape = [
      // Fork 1: Settled
      {
        id: 'fork_001',
        timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        status: 'settled' as const,
        question: 'Will Iran issue an official statement within 24 hours?',
        options: [
          {
            id: 'opt_001_yes',
            label: 'Yes',
            price: 0.75,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(), price: 0.65 },
              { timestamp: new Date(now.getTime() - 3.5 * 60 * 60 * 1000).toISOString(), price: 0.68 },
              { timestamp: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(), price: 0.72 },
              { timestamp: new Date(now.getTime() - 2.5 * 60 * 60 * 1000).toISOString(), price: 0.74 },
              { timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(), price: 0.75 },
            ],
          },
          {
            id: 'opt_001_no',
            label: 'No',
            price: 0.25,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(), price: 0.35 },
              { timestamp: new Date(now.getTime() - 3.5 * 60 * 60 * 1000).toISOString(), price: 0.32 },
              { timestamp: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(), price: 0.28 },
              { timestamp: new Date(now.getTime() - 2.5 * 60 * 60 * 1000).toISOString(), price: 0.26 },
              { timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(), price: 0.25 },
            ],
          },
        ],
        settledAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        settledOutcome: 'Yes',
      },
      // Fork 2: Settled
      {
        id: 'fork_002',
        timestamp: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
        status: 'settled' as const,
        question: 'Will commercial shipping reroute around the Strait?',
        options: [
          {
            id: 'opt_002_yes',
            label: 'Yes',
            price: 0.45,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(), price: 0.50 },
              { timestamp: new Date(now.getTime() - 5.5 * 60 * 60 * 1000).toISOString(), price: 0.48 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(), price: 0.47 },
              { timestamp: new Date(now.getTime() - 4.5 * 60 * 60 * 1000).toISOString(), price: 0.46 },
              { timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(), price: 0.45 },
            ],
          },
          {
            id: 'opt_002_no',
            label: 'No',
            price: 0.55,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(), price: 0.50 },
              { timestamp: new Date(now.getTime() - 5.5 * 60 * 60 * 1000).toISOString(), price: 0.52 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(), price: 0.53 },
              { timestamp: new Date(now.getTime() - 4.5 * 60 * 60 * 1000).toISOString(), price: 0.54 },
              { timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(), price: 0.55 },
            ],
          },
        ],
        settledAt: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        settledOutcome: 'No',
      },
      // Fork 3: Locked
      {
        id: 'fork_003',
        timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(),
        status: 'locked' as const,
        question: 'Will US Navy deploy additional assets to the region?',
        options: [
          {
            id: 'opt_003_yes',
            label: 'Yes',
            price: 0.68,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(), price: 0.60 },
              { timestamp: new Date(now.getTime() - 45 * 60 * 1000).toISOString(), price: 0.63 },
              { timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), price: 0.65 },
              { timestamp: new Date(now.getTime() - 15 * 60 * 1000).toISOString(), price: 0.67 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.68 },
            ],
          },
          {
            id: 'opt_003_no',
            label: 'No',
            price: 0.32,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(), price: 0.40 },
              { timestamp: new Date(now.getTime() - 45 * 60 * 1000).toISOString(), price: 0.37 },
              { timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), price: 0.35 },
              { timestamp: new Date(now.getTime() - 15 * 60 * 1000).toISOString(), price: 0.33 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.32 },
            ],
          },
        ],
        lockedAt: new Date(now.getTime() + 10 * 60 * 1000).toISOString(), // Locks in 10 minutes
      },
      // Fork 4: Repricing
      {
        id: 'fork_004',
        timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(),
        status: 'repricing' as const,
        question: 'Will oil prices exceed $100/barrel by end of week?',
        options: [
          {
            id: 'opt_004_yes',
            label: 'Yes',
            price: 0.42,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), price: 0.38 },
              { timestamp: new Date(now.getTime() - 20 * 60 * 1000).toISOString(), price: 0.40 },
              { timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(), price: 0.41 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.42 },
            ],
          },
          {
            id: 'opt_004_no',
            label: 'No',
            price: 0.58,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), price: 0.62 },
              { timestamp: new Date(now.getTime() - 20 * 60 * 1000).toISOString(), price: 0.60 },
              { timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(), price: 0.59 },
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.58 },
            ],
          },
        ],
      },
      // Fork 5: Open
      {
        id: 'fork_005',
        timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
        status: 'open' as const,
        question: 'Will diplomatic talks resume within 48 hours?',
        options: [
          {
            id: 'opt_005_yes',
            label: 'Yes',
            price: 0.35,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.35 },
            ],
          },
          {
            id: 'opt_005_no',
            label: 'No',
            price: 0.65,
            priceHistory: [
              { timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), price: 0.65 },
            ],
          },
        ],
        lockedAt: new Date(now.getTime() + 15 * 60 * 1000).toISOString(), // Locks in 15 minutes
      },
    ];

    // Sabotage history: 4 events (mix of disclosed, executed, and slashed)
    const sabotageHistory = [
      {
        id: 'sab_001',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        phase: 'disclosed' as const,
        saboteurId: 'agent_shadow',
        saboteurName: 'Shadow Broker',
        sabotageType: 'Sensor Noise',
        stakeAmount: 1500,
        effectSize: -8,
        disclosedAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        slashed: false,
      },
      {
        id: 'sab_002',
        timestamp: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(),
        phase: 'executed' as const,
        saboteurId: 'agent_viper',
        saboteurName: 'Viper',
        sabotageType: 'Evidence Injection',
        stakeAmount: 2000,
        effectSize: -12,
        disclosedAt: new Date(now.getTime() - 3.5 * 60 * 60 * 1000).toISOString(),
        executedAt: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(),
        slashed: false,
      },
      {
        id: 'sab_003',
        timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
        phase: 'slashed' as const,
        saboteurId: 'agent_chaos',
        saboteurName: 'Chaos Agent',
        sabotageType: 'Stability Attack',
        stakeAmount: 1000,
        effectSize: -5,
        disclosedAt: new Date(now.getTime() - 5.5 * 60 * 60 * 1000).toISOString(),
        executedAt: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
        slashed: true,
      },
      {
        id: 'sab_004',
        timestamp: new Date(now.getTime() - 8 * 60 * 60 * 1000).toISOString(),
        phase: 'executed' as const,
        saboteurId: 'agent_phantom',
        saboteurName: 'Phantom',
        sabotageType: 'Logic Bomb',
        stakeAmount: 3000,
        effectSize: -15,
        disclosedAt: new Date(now.getTime() - 8.5 * 60 * 60 * 1000).toISOString(),
        executedAt: new Date(now.getTime() - 8 * 60 * 60 * 1000).toISOString(),
        slashed: false,
      },
    ];

    // Evidence ledger: 6 entries (mix of sources, one contradiction)
    const evidenceLedger = [
      {
        id: 'ev_001',
        timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(),
        source: 'RavenPack',
        headline: 'Satellite imagery shows increased naval activity in Hormuz Strait',
        sentiment: 'bearish' as const,
        confidence: 85,
        impactOnGap: 5,
      },
      {
        id: 'ev_002',
        timestamp: new Date(now.getTime() - 25 * 60 * 1000).toISOString(),
        source: 'Spire AIS',
        headline: 'Tanker traffic rerouting around Strait of Hormuz',
        sentiment: 'bearish' as const,
        confidence: 70,
        contradiction: {
          conflictsWith: 'ev_003',
          reason: 'Contradicts earlier reports of normal shipping lanes',
        },
        impactOnGap: 10,
      },
      {
        id: 'ev_003',
        timestamp: new Date(now.getTime() - 45 * 60 * 1000).toISOString(),
        source: 'X API',
        headline: 'Analyst dismisses Hormuz tensions as "overblown"',
        sentiment: 'bullish' as const,
        confidence: 40,
        impactOnGap: -3,
      },
      {
        id: 'ev_004',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        source: 'RavenPack',
        headline: 'Iranian officials signal willingness for diplomatic talks',
        sentiment: 'bullish' as const,
        confidence: 65,
        impactOnGap: -4,
      },
      {
        id: 'ev_005',
        timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        source: 'Spire AIS',
        headline: 'Commercial shipping delays reported in Persian Gulf',
        sentiment: 'neutral' as const,
        confidence: 55,
        impactOnGap: 2,
      },
      {
        id: 'ev_006',
        timestamp: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
        source: 'GDELT',
        headline: 'Global event database shows spike in Hormuz-related incidents',
        sentiment: 'bearish' as const,
        confidence: 75,
        impactOnGap: 7,
      },
    ];

    // Paradox status: Active, CLASS_2_SEVERE, countdown 7200 seconds (2 hours)
    const paradoxStatus = {
      active: true,
      spawnedAt: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
      severity: 'CLASS_2_SEVERE' as const,
      triggerReason: 'logic_gap' as const,
      triggerValue: 62,
      countdown: 7200, // 2 hours
      extractionCost: {
        usdc: 5000,
        echelon: 100,
        sanityCost: 50,
      },
      extractionHistory: [
        {
          timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
          agentId: 'agent_alpha',
          agentName: 'Alpha',
          success: false,
          cost: 5000,
          sanityCost: 50,
        },
      ],
    };

    // User position: YES, 500 shares at $0.52 avg, burn at collapse $260
    const userPosition = {
      side: 'YES' as const,
      shares: 500,
      avgPrice: 0.52,
      currentValue: 225, // 500 * 0.45 (current yesPrice)
      unrealisedPnl: -35, // (0.45 - 0.52) * 500
      burnAtCollapse: 260,
    };

    return {
      id: timelineId,
      name: 'Oil Crisis - Hormuz Strait',
      slug: 'oil-crisis-hormuz-strait',
      description:
        'Counterfactual: Iranian patrol boats block commercial shipping',
      createdAt: createdAt.toISOString(),
      expiresAt: expiresIn48h.toISOString(),
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

  // Fallback for other timeline IDs (simplified mock)
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
  ];

  // Mock paradox status (null for most timelines)
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
