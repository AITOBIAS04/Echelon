import type { Breach, BreachStats } from '../../types/breach';

const now = new Date();
const fiveMinsAgo = new Date(now.getTime() - 5 * 60 * 1000);
const tenMinsAgo = new Date(now.getTime() - 10 * 60 * 1000);
const thirtyMinsAgo = new Date(now.getTime() - 30 * 60 * 1000);
const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);

const mockBreaches: Breach[] = [
  {
    id: 'breach_001',
    timestamp: fiveMinsAgo.toISOString(),
    severity: 'critical',
    category: 'paradox_detonation',
    title: 'Paradox Detonation in Oil Crisis Timeline',
    description:
      'A critical paradox has detonated in the Oil Crisis - Hormuz Strait timeline, causing cascading failures across multiple agent positions. The timeline logic gap exceeded 60% threshold, triggering automatic paradox spawn.',
    affectedTimelines: [
      {
        id: 'tl_oil_hormuz_001',
        name: 'Oil Crisis - Hormuz Strait',
        stabilityBefore: 52.1,
        stabilityAfter: 28.5,
        logicGapBefore: 45,
        logicGapAfter: 78,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_alpha',
        name: 'Alpha',
        archetype: 'Analyst',
        pnlImpact: -2500,
        sanityImpact: 45,
      },
      {
        id: 'agent_beta',
        name: 'Beta',
        archetype: 'Trader',
        pnlImpact: -1800,
        sanityImpact: 30,
      },
    ],
    rootCause:
      'Multiple contradictory OSINT sources created an unresolvable logic gap. RavenPack reported increased naval activity while X API dismissed tensions as overblown. The system could not reconcile these signals.',
    beneficiaries: [
      {
        type: 'agent',
        id: 'agent_shadow',
        name: 'Shadow Broker',
        estimatedGain: 5000,
      },
      {
        type: 'wallet',
        id: 'wallet_0x1234',
        name: '0x1234...5678',
        estimatedGain: 3200,
      },
    ],
    evidenceChanges: [
      {
        timestamp: fiveMinsAgo.toISOString(),
        source: 'RavenPack',
        changeType: 'contradicted',
        description:
          'Satellite imagery contradicted earlier shipping lane reports from Spire AIS.',
      },
      {
        timestamp: tenMinsAgo.toISOString(),
        source: 'X API',
        changeType: 'added',
        description: 'Analyst dismissed Hormuz tensions as "overblown".',
      },
    ],
    status: 'active',
    recoverable: false,
    suggestedActions: [
      {
        id: 'action_001',
        action: 'Emergency timeline extraction',
        priority: 'immediate',
        estimatedImpact: 'High - May prevent total collapse',
      },
      {
        id: 'action_002',
        action: 'Freeze all trading on affected timeline',
        priority: 'immediate',
        estimatedImpact: 'High - Prevents further losses',
      },
      {
        id: 'action_003',
        action: 'Investigate Shadow Broker for potential manipulation',
        priority: 'recommended',
        estimatedImpact: 'Medium - May reveal attack vector',
      },
    ],
  },
  {
    id: 'breach_002',
    timestamp: thirtyMinsAgo.toISOString(),
    severity: 'high',
    category: 'logic_gap_spike',
    title: 'Sudden Logic Gap Spike in Tech Regulation Timeline',
    description:
      'The Tech Regulation timeline experienced an unexpected 35% logic gap increase within 5 minutes, indicating potential sensor manipulation or coordinated attack.',
    affectedTimelines: [
      {
        id: 'tl_tech_reg_001',
        name: 'Tech Regulation - AI Oversight',
        stabilityBefore: 68.2,
        stabilityAfter: 55.8,
        logicGapBefore: 25,
        logicGapAfter: 60,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_gamma',
        name: 'Gamma',
        archetype: 'Researcher',
        pnlImpact: -1200,
        sanityImpact: 20,
      },
    ],
    rootCause:
      'Sensor feed from GDELT was compromised, injecting false positive signals about regulatory changes.',
    beneficiaries: [
      {
        type: 'wallet',
        id: 'wallet_0xabcd',
        name: '0xabcd...ef01',
        estimatedGain: 1800,
      },
    ],
    evidenceChanges: [
      {
        timestamp: thirtyMinsAgo.toISOString(),
        source: 'GDELT',
        changeType: 'removed',
        description: 'False positive regulatory change signal removed.',
      },
    ],
    status: 'investigating',
    recoverable: true,
    suggestedActions: [
      {
        id: 'action_004',
        action: 'Audit GDELT sensor feed integrity',
        priority: 'recommended',
        estimatedImpact: 'Medium - Prevents future attacks',
      },
      {
        id: 'action_005',
        action: 'Restore timeline from last known good state',
        priority: 'recommended',
        estimatedImpact: 'High - May recover stability',
      },
    ],
  },
  {
    id: 'breach_003',
    timestamp: oneHourAgo.toISOString(),
    severity: 'medium',
    category: 'sabotage_cluster',
    title: 'Coordinated Sabotage Attack Cluster',
    description:
      'Multiple simultaneous sabotage attempts detected across 3 timelines, suggesting coordinated attack by malicious agents.',
    affectedTimelines: [
      {
        id: 'tl_climate_001',
        name: 'Climate Policy - Carbon Tax',
        stabilityBefore: 72.5,
        stabilityAfter: 65.1,
        logicGapBefore: 20,
        logicGapAfter: 28,
      },
      {
        id: 'tl_election_001',
        name: 'Election Outcome - Senate',
        stabilityBefore: 58.3,
        stabilityAfter: 52.0,
        logicGapBefore: 30,
        logicGapAfter: 38,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_delta',
        name: 'Delta',
        archetype: 'Defender',
        pnlImpact: 500,
        sanityImpact: 10,
      },
    ],
    rootCause:
      'Coordinated attack by Shadow Broker and Viper agents, targeting multiple timelines simultaneously to maximize chaos.',
    beneficiaries: [
      {
        type: 'agent',
        id: 'agent_viper',
        name: 'Viper',
        estimatedGain: 2500,
      },
      {
        type: 'agent',
        id: 'agent_shadow',
        name: 'Shadow Broker',
        estimatedGain: 2200,
      },
    ],
    evidenceChanges: [
      {
        timestamp: oneHourAgo.toISOString(),
        source: 'System',
        changeType: 'added',
        description: 'Detected coordinated sabotage pattern.',
      },
    ],
    status: 'mitigated',
    recoverable: true,
    suggestedActions: [
      {
        id: 'action_006',
        action: 'Slash stakes from Shadow Broker and Viper',
        priority: 'recommended',
        estimatedImpact: 'High - Deters future attacks',
      },
    ],
    resolvedAt: new Date(oneHourAgo.getTime() + 15 * 60 * 1000).toISOString(),
    resolutionNotes: 'Sabotage attempts were successfully mitigated. Stakes slashed.',
  },
  {
    id: 'breach_004',
    timestamp: twoHoursAgo.toISOString(),
    severity: 'low',
    category: 'sensor_contradiction',
    title: 'Minor Sensor Contradiction in Weather Timeline',
    description:
      'Weather sensors reported conflicting data, causing minor logic gap increase.',
    affectedTimelines: [
      {
        id: 'tl_weather_001',
        name: 'Weather - Hurricane Season',
        stabilityBefore: 75.0,
        stabilityAfter: 73.5,
        logicGapBefore: 15,
        logicGapAfter: 18,
      },
    ],
    affectedAgents: [],
    rootCause: 'Temporary sensor calibration issue, resolved automatically.',
    beneficiaries: [],
    evidenceChanges: [
      {
        timestamp: twoHoursAgo.toISOString(),
        source: 'Weather API',
        changeType: 'contradicted',
        description: 'Sensor readings contradicted, auto-corrected.',
      },
    ],
    status: 'resolved',
    recoverable: true,
    suggestedActions: [],
    resolvedAt: new Date(twoHoursAgo.getTime() + 10 * 60 * 1000).toISOString(),
    resolutionNotes: 'Sensor calibration issue resolved automatically.',
  },
];

/**
 * Mock API function to fetch breaches
 * In production, this would call the actual API endpoint
 */
export async function getMockBreaches(): Promise<Breach[]> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockBreaches;
}

/**
 * Calculate breach statistics
 */
export function calculateBreachStats(breaches: Breach[]): BreachStats {
  const stats: BreachStats = {
    totalActive: 0,
    bySeverity: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    },
    byCategory: {
      logic_gap_spike: 0,
      sensor_contradiction: 0,
      sabotage_cluster: 0,
      oracle_flip: 0,
      stability_collapse: 0,
      paradox_detonation: 0,
    },
  };

  breaches.forEach((breach) => {
    if (breach.status === 'active') {
      stats.totalActive++;
    }
    stats.bySeverity[breach.severity]++;
    stats.byCategory[breach.category]++;
  });

  return stats;
}
