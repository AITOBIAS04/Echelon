import type { OpsBoardData, OpsCard, LiveNowSummary } from '../types/opsBoard';

/**
 * Mock Operations Board API
 * 
 * Provides mock data for the operations board with realistic
 * timeline and launch cards organized by operational lanes.
 */

const now = new Date();
const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000);
const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

/**
 * Generate random number in range
 */
function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate mock live now summary
 */
function generateLiveNow(): LiveNowSummary {
  return {
    forksLive: randomInt(8, 20),
    paradoxActive: randomInt(1, 5),
    breaches: randomInt(0, 5),
  };
}

/**
 * Generate mock cards for new_creations lane
 */
function generateNewCreationsCards(): OpsCard[] {
  const count = randomInt(6, 10);
  const cards: OpsCard[] = [];

  for (let i = 0; i < count; i++) {
    const isLaunch = Math.random() > 0.5;
    const createdAt = new Date(now.getTime() - randomInt(0, 48) * 60 * 60 * 1000);

    if (isLaunch) {
      cards.push({
        id: `ops_new_launch_${i + 1}`,
        type: 'launch',
        title: `New Launch ${i + 1}`,
        subtitle: 'Recently created launch',
        lane: 'new_creations',
        tags: [],
        qualityScore: randomInt(30, 70),
        phase: Math.random() > 0.7 ? 'sandbox' : 'draft',
        exportEligible: Math.random() > 0.8,
        createdAt: createdAt.toISOString(),
        updatedAt: createdAt.toISOString(),
      });
    } else {
      cards.push({
        id: `ops_new_timeline_${i + 1}`,
        type: 'timeline',
        title: `New Timeline ${i + 1}`,
        subtitle: 'Recently created timeline',
        lane: 'new_creations',
        tags: [],
        stability: randomInt(60, 90),
        logicGap: randomInt(10, 30),
        createdAt: createdAt.toISOString(),
        updatedAt: createdAt.toISOString(),
      });
    }
  }

  return cards;
}

/**
 * Generate mock cards for about_to_happen lane
 * Must include fork_soon and disclosure_active tags
 */
function generateAboutToHappenCards(): OpsCard[] {
  const count = randomInt(6, 10);
  const cards: OpsCard[] = [];

  // Ensure at least one card has fork_soon
  cards.push({
    id: 'ops_fork_soon_1',
    type: 'timeline',
    title: 'Fork Imminent: Strait of Hormuz',
    subtitle: 'Next fork in 5 minutes',
    lane: 'about_to_happen',
    tags: ['fork_soon'],
    stability: randomInt(50, 80),
    logicGap: randomInt(20, 40),
    nextForkEtaSec: randomInt(60, 600), // 1-10 minutes
    createdAt: twoDaysAgo.toISOString(),
    updatedAt: oneHourAgo.toISOString(),
  });

  // Ensure at least one card has disclosure_active
  cards.push({
    id: 'ops_disclosure_active_1',
    type: 'timeline',
    title: 'Active Disclosure: Fed Rate Decision',
    subtitle: 'Disclosure window open',
    lane: 'about_to_happen',
    tags: ['disclosure_active'],
    stability: randomInt(60, 85),
    logicGap: randomInt(15, 35),
    entropyRate: randomInt(-2, 2),
    createdAt: oneDayAgo.toISOString(),
    updatedAt: threeHoursAgo.toISOString(),
  });

  // Generate remaining cards
  for (let i = cards.length; i < count; i++) {
    const tags: OpsCard['tags'] = [];
    if (Math.random() > 0.6) tags.push('fork_soon');
    if (Math.random() > 0.6) tags.push('disclosure_active');
    if (Math.random() > 0.7) tags.push('evidence_flip');

    cards.push({
      id: `ops_about_${i + 1}`,
      type: 'timeline',
      title: `Timeline ${i + 1}: About to Happen`,
      subtitle: 'Upcoming event or fork',
      lane: 'about_to_happen',
      tags,
      stability: randomInt(55, 85),
      logicGap: randomInt(20, 45),
      nextForkEtaSec: randomInt(300, 3600), // 5-60 minutes
      entropyRate: randomInt(-3, 1),
      createdAt: oneDayAgo.toISOString(),
      updatedAt: oneHourAgo.toISOString(),
    });
  }

  return cards;
}

/**
 * Generate mock cards for at_risk lane
 * Must include brittle and paradox_active tags
 */
function generateAtRiskCards(): OpsCard[] {
  const count = randomInt(6, 10);
  const cards: OpsCard[] = [];

  // Ensure at least one card has brittle tag
  cards.push({
    id: 'ops_brittle_1',
    type: 'timeline',
    title: 'Brittle Timeline: Oil Crisis',
    subtitle: 'Logic gap widening',
    lane: 'at_risk',
    tags: ['brittle'],
    stability: randomInt(30, 50),
    logicGap: randomInt(45, 65), // Brittle range
    paradoxProximity: randomInt(30, 60),
    entropyRate: randomInt(-5, -2),
    sabotageHeat24h: randomInt(2, 8),
    createdAt: oneWeekAgo.toISOString(),
    updatedAt: oneHourAgo.toISOString(),
  });

  // Ensure at least one card has paradox_active tag
  cards.push({
    id: 'ops_paradox_active_1',
    type: 'timeline',
    title: 'Paradox Active: Contagion Zero',
    subtitle: 'Active paradox detected',
    lane: 'at_risk',
    tags: ['paradox_active'],
    stability: randomInt(25, 45),
    logicGap: randomInt(60, 80),
    paradoxProximity: randomInt(80, 95),
    entropyRate: randomInt(-6, -3),
    createdAt: oneWeekAgo.toISOString(),
    updatedAt: threeHoursAgo.toISOString(),
  });

  // Generate remaining cards
  for (let i = cards.length; i < count; i++) {
    const tags: OpsCard['tags'] = [];
    if (Math.random() > 0.5) tags.push('brittle');
    if (Math.random() > 0.5) tags.push('paradox_active');
    if (Math.random() > 0.6) tags.push('high_entropy');
    if (Math.random() > 0.6) tags.push('sabotage_heat');

    cards.push({
      id: `ops_risk_${i + 1}`,
      type: 'timeline',
      title: `At Risk Timeline ${i + 1}`,
      subtitle: 'Requires attention',
      lane: 'at_risk',
      tags,
      stability: randomInt(20, 55),
      logicGap: randomInt(40, 70),
      paradoxProximity: randomInt(50, 90),
      entropyRate: randomInt(-6, -2),
      sabotageHeat24h: randomInt(1, 10),
      createdAt: oneWeekAgo.toISOString(),
      updatedAt: oneHourAgo.toISOString(),
    });
  }

  return cards;
}

/**
 * Generate mock cards for graduation lane
 * Mix of about-to-graduate and recently graduated
 */
function generateGraduationCards(): OpsCard[] {
  const count = randomInt(6, 10);
  const cards: OpsCard[] = [];

  // About to graduate launches
  const aboutToGraduateCount = Math.floor(count * 0.4);
  for (let i = 0; i < aboutToGraduateCount; i++) {
    cards.push({
      id: `ops_graduating_${i + 1}`,
      type: 'launch',
      title: `Graduating Launch ${i + 1}`,
      subtitle: 'Ready for production',
      lane: 'graduation',
      tags: ['graduating'],
      qualityScore: randomInt(80, 95),
      phase: 'pilot',
      exportEligible: true,
      createdAt: oneWeekAgo.toISOString(),
      updatedAt: oneDayAgo.toISOString(),
    });
  }

  // Recently graduated timelines/launches
  for (let i = aboutToGraduateCount; i < count; i++) {
    const isLaunch = Math.random() > 0.5;
    const graduatedAt = new Date(now.getTime() - randomInt(1, 7) * 24 * 60 * 60 * 1000);

    if (isLaunch) {
      cards.push({
        id: `ops_graduated_launch_${i + 1}`,
        type: 'launch',
        title: `Graduated Launch ${i + 1}`,
        subtitle: 'Recently graduated',
        lane: 'graduation',
        tags: [],
        qualityScore: randomInt(85, 98),
        phase: 'graduated',
        exportEligible: true,
        createdAt: twoDaysAgo.toISOString(),
        updatedAt: graduatedAt.toISOString(),
      });
    } else {
      cards.push({
        id: `ops_graduated_timeline_${i + 1}`,
        type: 'timeline',
        title: `Graduated Timeline ${i + 1}`,
        subtitle: 'Recently graduated',
        lane: 'graduation',
        tags: [],
        stability: randomInt(75, 95),
        logicGap: randomInt(5, 25),
        createdAt: twoDaysAgo.toISOString(),
        updatedAt: graduatedAt.toISOString(),
      });
    }
  }

  return cards;
}

/**
 * Get operations board data
 * 
 * Returns complete ops board data with live metrics and cards organized by lane.
 * 
 * @returns Promise resolving to OpsBoardData
 */
export async function getOpsBoard(): Promise<OpsBoardData> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  return {
    liveNow: generateLiveNow(),
    lanes: {
      new_creations: generateNewCreationsCards(),
      about_to_happen: generateAboutToHappenCards(),
      at_risk: generateAtRiskCards(),
      graduation: generateGraduationCards(),
    },
  };
}
