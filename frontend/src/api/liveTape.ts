import type { TapeEvent, TapeEventType } from '../types/liveTape';

/**
 * Mock Live Tape API
 * 
 * Provides mock data for live tape events with realistic
 * event types, timelines, agents, and impacts.
 */

const now = new Date();

/**
 * Generate random number in range
 */
function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate random float in range
 */
function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

/**
 * Generate mock tape events
 */
function generateMockEvents(): TapeEvent[] {
  const events: TapeEvent[] = [];
  const timelineIds = [
    'tl_oil_hormuz_001',
    'tl_fed_rate_decision_001',
    'tl_contagion_zero_001',
    'tl_neon_courier_001',
    'tl_disaster_response_001',
  ];
  const timelineTitles = [
    'Strait of Hormuz Shipping',
    'Fed Rate Decision',
    'Contagion Zero',
    'Neon Courier Network',
    'Disaster Response',
  ];
  const agentIds = ['agent_001', 'agent_002', 'agent_003', 'agent_004', 'agent_005'];
  const agentNames = ['SHARK_ALPHA', 'SPY_BETA', 'DIPLOMAT_GAMMA', 'SABOTEUR_DELTA', 'WHALE_EPSILON'];
  const wallets = [
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    '0x8ba1f109551bD432803012645Hac136c22C177',
    '0x1234567890123456789012345678901234567890',
  ];

  // Generate 50 events with mix of types
  const eventTypeDistribution: Array<{ type: TapeEventType; weight: number }> = [
    { type: 'wing_flap', weight: 0.3 },
    { type: 'fork_live', weight: 0.2 },
    { type: 'sabotage_disclosed', weight: 0.15 },
    { type: 'paradox_spawn', weight: 0.1 },
    { type: 'evidence_flip', weight: 0.15 },
    { type: 'settlement', weight: 0.1 },
  ];

  for (let i = 0; i < 50; i++) {
    // Generate timestamp (most recent first, descending)
    const minutesAgo = i * randomInt(1, 5);
    const ts = new Date(now.getTime() - minutesAgo * 60 * 1000).toISOString();

    // Select event type based on distribution
    const rand = Math.random();
    let cumulative = 0;
    let selectedType: TapeEventType = 'wing_flap';
    for (const dist of eventTypeDistribution) {
      cumulative += dist.weight;
      if (rand <= cumulative) {
        selectedType = dist.type;
        break;
      }
    }

    const timelineIdx = randomInt(0, timelineIds.length - 1);
    const timelineId = timelineIds[timelineIdx];
    const timelineTitle = timelineTitles[timelineIdx];
    const agentIdx = randomInt(0, agentIds.length - 1);
    const agentId = agentIds[agentIdx];
    const agentName = agentNames[agentIdx];
    const wallet = wallets[randomInt(0, wallets.length - 1)];

    let event: TapeEvent;

    switch (selectedType) {
      case 'wing_flap':
        event = {
          id: `tape_wing_${i + 1}`,
          ts,
          type: 'wing_flap',
          timelineId,
          timelineTitle,
          agentId,
          agentName,
          wallet,
          summary: `${agentName} executed wing flap on ${timelineTitle}`,
          impact: {
            stabilityDelta: randomFloat(-5, 5),
            priceDelta: randomFloat(-0.05, 0.05),
          },
        };
        break;

      case 'fork_live':
        const forkId = `fork_${timelineId}_${Date.now()}_${i}`;
        event = {
          id: `tape_fork_${i + 1}`,
          ts,
          type: 'fork_live',
          timelineId,
          timelineTitle,
          summary: `Fork went live: ${timelineTitle}`,
          impact: {
            stabilityDelta: randomFloat(-10, 10),
            logicGapDelta: randomFloat(-5, 5),
          },
          replayPointer: {
            timelineId,
            forkId,
          },
        };
        break;

      case 'sabotage_disclosed':
        const sabotageForkId = `fork_${timelineId}_sabotage_${i}`;
        event = {
          id: `tape_sabotage_${i + 1}`,
          ts,
          type: 'sabotage_disclosed',
          timelineId,
          timelineTitle,
          agentId,
          agentName,
          summary: `Sabotage disclosed on ${timelineTitle} by ${agentName}`,
          impact: {
            stabilityDelta: randomFloat(-15, -5),
            logicGapDelta: randomFloat(5, 15),
          },
          replayPointer: {
            timelineId,
            forkId: sabotageForkId,
          },
        };
        break;

      case 'paradox_spawn':
        const paradoxForkId = `fork_${timelineId}_paradox_${i}`;
        event = {
          id: `tape_paradox_${i + 1}`,
          ts,
          type: 'paradox_spawn',
          timelineId,
          timelineTitle,
          summary: `Paradox spawned on ${timelineTitle}`,
          impact: {
            stabilityDelta: randomFloat(-20, -10),
            logicGapDelta: randomFloat(10, 20),
          },
          replayPointer: {
            timelineId,
            forkId: paradoxForkId,
          },
        };
        break;

      case 'evidence_flip':
        event = {
          id: `tape_evidence_${i + 1}`,
          ts,
          type: 'evidence_flip',
          timelineId,
          timelineTitle,
          summary: `Evidence flipped on ${timelineTitle}`,
          impact: {
            logicGapDelta: randomFloat(-10, 10),
            priceDelta: randomFloat(-0.1, 0.1),
          },
        };
        break;

      case 'settlement':
        event = {
          id: `tape_settlement_${i + 1}`,
          ts,
          type: 'settlement',
          timelineId,
          timelineTitle,
          summary: `${timelineTitle} settled`,
          impact: {
            stabilityDelta: randomFloat(5, 15),
            priceDelta: randomFloat(0, 0.2),
          },
        };
        break;
    }

    events.push(event);
  }

  return events;
}

/**
 * List tape events
 * 
 * Returns filtered tape events sorted by timestamp (most recent first).
 * 
 * @param params Optional filter parameters
 * @returns Promise resolving to array of TapeEvent
 */
export async function listTapeEvents(params?: {
  type?: TapeEventType;
  timelineId?: string;
  agentId?: string;
}): Promise<TapeEvent[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 200));

  let events = generateMockEvents();

  // Apply filters
  if (params?.type) {
    events = events.filter((e) => e.type === params.type);
  }
  if (params?.timelineId) {
    events = events.filter((e) => e.timelineId === params.timelineId);
  }
  if (params?.agentId) {
    events = events.filter((e) => e.agentId === params.agentId);
  }

  // Sort by timestamp descending (most recent first)
  events.sort((a, b) => {
    const tsA = new Date(a.ts).getTime();
    const tsB = new Date(b.ts).getTime();
    return tsB - tsA;
  });

  return events;
}
