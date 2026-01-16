import type { Breach, BreachStats } from '../../types/breach';

const now = new Date();
const fiveMinsAgo = new Date(now.getTime() - 5 * 60 * 1000);
const tenMinsAgo = new Date(now.getTime() - 10 * 60 * 1000);
const thirtyMinsAgo = new Date(now.getTime() - 30 * 60 * 1000);
const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);

const mockBreaches: Breach[] = [
  // 1. Critical breach - "Coordinated Sabotage Cluster"
  {
    id: 'breach_001',
    timestamp: fiveMinsAgo.toISOString(),
    severity: 'critical',
    category: 'sabotage_cluster',
    title: 'Coordinated Sabotage Cluster',
    description:
      'Multiple simultaneous sabotage attacks detected across 3 critical timelines. Shadow Broker and Viper agents coordinated a synchronized assault, deploying sensor noise, evidence injection, and logic bombs simultaneously to maximize system disruption.',
    affectedTimelines: [
      {
        id: 'tl_oil_hormuz_001',
        name: 'Oil Crisis - Hormuz Strait',
        stabilityBefore: 54.7,
        stabilityAfter: 42.3,
        logicGapBefore: 42,
        logicGapAfter: 58,
      },
      {
        id: 'tl_fed_rate_jan26',
        name: 'Fed Rate Decision - January 2026',
        stabilityBefore: 89.2,
        stabilityAfter: 78.5,
        logicGapBefore: 8,
        logicGapAfter: 18,
      },
      {
        id: 'tl_tech_reg_001',
        name: 'Tech Regulation - AI Oversight',
        stabilityBefore: 68.2,
        stabilityAfter: 55.8,
        logicGapBefore: 25,
        logicGapAfter: 42,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_alpha',
        name: 'Alpha',
        archetype: 'Analyst',
        pnlImpact: -3500,
        sanityImpact: 55,
      },
      {
        id: 'agent_beta',
        name: 'Beta',
        archetype: 'Trader',
        pnlImpact: -2800,
        sanityImpact: 42,
      },
      {
        id: 'agent_gamma',
        name: 'Gamma',
        archetype: 'Researcher',
        pnlImpact: -1500,
        sanityImpact: 28,
      },
    ],
    rootCause:
      'Coordinated attack by Shadow Broker and Viper agents. They synchronized their sabotage attempts across multiple timelines to overwhelm the system\'s defensive mechanisms. The attacks used a combination of sensor noise, evidence injection, and logic bombs deployed within a 5-minute window.',
    beneficiaries: [
      {
        type: 'agent',
        id: 'agent_shadow',
        name: 'Shadow Broker',
        estimatedGain: 8500,
      },
      {
        type: 'agent',
        id: 'agent_viper',
        name: 'Viper',
        estimatedGain: 7200,
      },
    ],
    evidenceChanges: [
      {
        timestamp: fiveMinsAgo.toISOString(),
        source: 'System',
        changeType: 'added',
        description: 'Detected coordinated sabotage pattern across multiple timelines.',
      },
      {
        timestamp: tenMinsAgo.toISOString(),
        source: 'RavenPack',
        changeType: 'contradicted',
        description: 'Sensor noise injection detected, contradicting earlier stable readings.',
      },
    ],
    status: 'active',
    recoverable: true,
    suggestedActions: [
      {
        id: 'action_001',
        action: 'Emergency freeze on all affected timelines',
        priority: 'immediate',
        estimatedImpact: 'Critical - Prevents further damage and allows recovery',
      },
      {
        id: 'action_002',
        action: 'Slash stakes from Shadow Broker and Viper immediately',
        priority: 'immediate',
        estimatedImpact: 'High - Deters future coordinated attacks and recovers funds',
      },
      {
        id: 'action_003',
        action: 'Investigate coordination mechanism used by attackers',
        priority: 'recommended',
        estimatedImpact: 'Medium - May reveal attack vector for future prevention',
      },
    ],
  },
  // 2. High breach - "Oracle Data Flip"
  {
    id: 'breach_002',
    timestamp: thirtyMinsAgo.toISOString(),
    severity: 'high',
    category: 'oracle_flip',
    title: 'Oracle Data Flip',
    description:
      'RavenPack oracle feed experienced a critical data flip, contradicting previous evidence and causing significant logic gap increase in the Oil Crisis timeline. The oracle reported a complete reversal of naval activity indicators within a 10-minute window.',
    affectedTimelines: [
      {
        id: 'tl_oil_hormuz_001',
        name: 'Oil Crisis - Hormuz Strait',
        stabilityBefore: 54.7,
        stabilityAfter: 48.2,
        logicGapBefore: 42,
        logicGapAfter: 52,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_delta',
        name: 'Delta',
        archetype: 'Defender',
        pnlImpact: -1800,
        sanityImpact: 25,
      },
      {
        id: 'agent_epsilon',
        name: 'Epsilon',
        archetype: 'Oracle',
        pnlImpact: -2200,
        sanityImpact: 35,
      },
    ],
    rootCause:
      'RavenPack oracle feed experienced a data corruption event, causing a complete flip in naval activity indicators. The oracle initially reported increased activity, then reversed to report decreased activity within 10 minutes, creating an unresolvable contradiction.',
    beneficiaries: [
      {
        type: 'wallet',
        id: 'wallet_0x7890',
        name: '0x7890...abcd',
        estimatedGain: 3200,
      },
    ],
    evidenceChanges: [
      {
        timestamp: thirtyMinsAgo.toISOString(),
        source: 'RavenPack',
        changeType: 'contradicted',
        description:
          'Oracle data flip: Initially reported increased naval activity, then reversed to decreased activity. Previous evidence contradicted.',
      },
      {
        timestamp: new Date(thirtyMinsAgo.getTime() - 10 * 60 * 1000).toISOString(),
        source: 'RavenPack',
        changeType: 'removed',
        description: 'Previous naval activity report removed due to data corruption.',
      },
    ],
    status: 'investigating',
    recoverable: true,
    suggestedActions: [
      {
        id: 'action_004',
        action: 'Audit RavenPack oracle feed integrity',
        priority: 'recommended',
        estimatedImpact: 'High - Identifies root cause and prevents future flips',
      },
      {
        id: 'action_005',
        action: 'Restore timeline from pre-flip snapshot',
        priority: 'recommended',
        estimatedImpact: 'Medium - May recover stability if done quickly',
      },
    ],
  },
  // 3. Medium breach - "Logic Gap Spike"
  {
    id: 'breach_003',
    timestamp: oneHourAgo.toISOString(),
    severity: 'medium',
    category: 'logic_gap_spike',
    title: 'Logic Gap Spike',
    description:
      'Two timelines experienced sudden logic gap spikes within minutes of each other, indicating potential sensor manipulation or coordinated attack. The spikes occurred independently but suggest a common attack vector.',
    affectedTimelines: [
      {
        id: 'tl_climate_001',
        name: 'Climate Policy - Carbon Tax',
        stabilityBefore: 72.5,
        stabilityAfter: 68.1,
        logicGapBefore: 20,
        logicGapAfter: 32,
      },
      {
        id: 'tl_election_001',
        name: 'Election Outcome - Senate',
        stabilityBefore: 58.3,
        stabilityAfter: 54.2,
        logicGapBefore: 30,
        logicGapAfter: 42,
      },
    ],
    affectedAgents: [
      {
        id: 'agent_zeta',
        name: 'Zeta',
        archetype: 'Analyst',
        pnlImpact: -800,
        sanityImpact: 15,
      },
    ],
    rootCause:
      'Sensor feeds from GDELT and Spire AIS were compromised, injecting false positive signals about policy changes and election outcomes. The attacks were not coordinated but exploited similar vulnerabilities in the sensor infrastructure.',
    beneficiaries: [],
    evidenceChanges: [
      {
        timestamp: oneHourAgo.toISOString(),
        source: 'GDELT',
        changeType: 'removed',
        description: 'False positive policy change signal removed.',
      },
      {
        timestamp: new Date(oneHourAgo.getTime() - 5 * 60 * 1000).toISOString(),
        source: 'Spire AIS',
        changeType: 'removed',
        description: 'False positive election outcome signal removed.',
      },
    ],
    status: 'mitigated',
    recoverable: true,
    suggestedActions: [
      {
        id: 'action_006',
        action: 'Strengthen sensor feed validation protocols',
        priority: 'recommended',
        estimatedImpact: 'Medium - Prevents future sensor manipulation',
      },
    ],
    resolvedAt: new Date(oneHourAgo.getTime() + 20 * 60 * 1000).toISOString(),
    resolutionNotes: 'False positive signals removed. Sensor feeds restored to normal operation.',
  },
  // 4. Low breach - "Sensor Contradiction"
  {
    id: 'breach_004',
    timestamp: twoHoursAgo.toISOString(),
    severity: 'low',
    category: 'sensor_contradiction',
    title: 'Sensor Contradiction',
    description:
      'Spire AIS sensor reported conflicting shipping data for the Oil Crisis timeline. Investigation revealed a false positive caused by scheduled maintenance on the AIS feed.',
    affectedTimelines: [
      {
        id: 'tl_oil_hormuz_001',
        name: 'Oil Crisis - Hormuz Strait',
        stabilityBefore: 54.7,
        stabilityAfter: 53.8,
        logicGapBefore: 42,
        logicGapAfter: 43,
      },
    ],
    affectedAgents: [],
    rootCause:
      'Spire AIS was undergoing scheduled maintenance, causing temporary sensor calibration issues. The feed reported conflicting shipping lane data during the maintenance window.',
    beneficiaries: [],
    evidenceChanges: [
      {
        timestamp: twoHoursAgo.toISOString(),
        source: 'Spire AIS',
        changeType: 'contradicted',
        description:
          'Sensor readings contradicted during maintenance window. Auto-corrected after maintenance completed.',
      },
    ],
    status: 'resolved',
    recoverable: true,
    suggestedActions: [],
    resolvedAt: new Date(twoHoursAgo.getTime() + 10 * 60 * 1000).toISOString(),
    resolutionNotes: 'False positive from Spire AIS maintenance',
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

/**
 * Get Mock Breach Stats
 * 
 * Returns aggregated breach statistics.
 * In production, this would call the actual API endpoint.
 */
export async function getMockBreachStats(): Promise<BreachStats> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  const breaches = await getMockBreaches();
  return calculateBreachStats(breaches);
}

