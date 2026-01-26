import type { OpsBoardData, OpsCard, LiveNowSummary } from '../types/opsBoard';

/**
 * Mock Operations Board API
 *
 * Provides mock data for the operations board with realistic
 * timeline and launch cards organized by operational lanes.
 */

// Helper functions and variables for mock data generation
function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

const now = new Date();
const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

const MOCK_IMAGES = [
  'https://images.unsplash.com/photo-1518457683858-667fcf3a9a3c?w=80&h=80&fit=crop',  // Oil/Energy
  'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=80&h=80&fit=crop',  // Finance/Markets
  'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=80&h=80&fit=crop',  // Tech/AI
  'https://images.unsplash.com/photo-1591076482161-42ce6d7a4610?w=80&h=80&fit=crop',  // Shipping/Logistics
  'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=80&h=80&fit=crop',  // Cyber/Security
  'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=80&h=80&fit=crop',  // Geopolitics
  'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=80&h=80&fit=crop',  // Science
  'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=80&h=80&fit=crop',  // Space
];

/**
 * Get random image URL for mock data
 */
function getRandomImage(): string {
  return MOCK_IMAGES[Math.floor(Math.random() * MOCK_IMAGES.length)];
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
    const updatedAt = new Date(createdAt.getTime() + randomInt(0, 60) * 60 * 1000); // Updated shortly after creation

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
        image_url: getRandomImage(),
        createdAt: createdAt.toISOString(),
        updatedAt: updatedAt.toISOString(),
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
        sabotageHeat24h: Math.random() > 0.6 ? randomInt(0, 5) : undefined,
        image_url: getRandomImage(),
        createdAt: createdAt.toISOString(),
        updatedAt: updatedAt.toISOString(),
      });
    }
  }

  return cards;
}

/**
 * Generate mock cards for about_to_happen lane
 * Must include fork_soon, disclosure_active, and evidence_flip tags
 */
function generateAboutToHappenCards(): OpsCard[] {
  const cards: OpsCard[] = [];

  // 2-3 items with nextForkEtaSec between 60 and 900 (1m-15m) and tag fork_soon
  const forkSoonCount = randomInt(2, 3);
  for (let i = 0; i < forkSoonCount; i++) {
    const forkEta = randomInt(60, 900); // 1-15 minutes
    const createdAt = new Date(now.getTime() - randomInt(1, 24) * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 60) * 60 * 1000); // Updated within last hour
    
    cards.push({
      id: `ops_fork_soon_${i + 1}`,
      type: 'timeline',
      title: `Fork Imminent ${i + 1}: ${['Strait of Hormuz', 'Fed Rate Decision', 'Oil Crisis'][i] || 'Timeline'}`,
      subtitle: `Next fork in ${Math.floor(forkEta / 60)}m`,
      lane: 'about_to_happen',
      tags: ['fork_soon'],
      stability: randomInt(50, 80),
      logicGap: randomInt(20, 40),
      nextForkEtaSec: forkEta,
      entropyRate: randomInt(-2, 2),
      sabotageHeat24h: randomInt(0, 8),
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
    });
  }

  // 1-2 items with tag disclosure_active
  const disclosureCount = randomInt(1, 2);
  for (let i = 0; i < disclosureCount; i++) {
    const createdAt = new Date(now.getTime() - randomInt(2, 48) * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 180) * 60 * 1000); // Updated within last 3 hours
    
    cards.push({
      id: `ops_disclosure_active_${i + 1}`,
      type: 'timeline',
      title: `Active Disclosure ${i + 1}: ${['Fed Rate Decision', 'Geopolitical Event'][i] || 'Timeline'}`,
      subtitle: 'Disclosure window open',
      lane: 'about_to_happen',
      tags: ['disclosure_active'],
      stability: randomInt(60, 85),
      logicGap: randomInt(15, 35),
      entropyRate: randomInt(-2, 2),
      sabotageHeat24h: randomInt(0, 6),
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
    });
  }

  // 1 item with tag evidence_flip
  const createdAt = new Date(now.getTime() - randomInt(1, 12) * 60 * 60 * 1000);
  const updatedAt = new Date(now.getTime() - randomInt(0, 30) * 60 * 1000); // Updated within last 30 minutes
  
  cards.push({
    id: 'ops_evidence_flip_1',
    type: 'timeline',
    title: 'Evidence Flip: Contagion Zero',
    subtitle: 'New evidence contradicts previous',
    lane: 'about_to_happen',
    tags: ['evidence_flip'],
    stability: randomInt(55, 75),
    logicGap: randomInt(25, 45),
    entropyRate: randomInt(-3, 1),
    sabotageHeat24h: randomInt(0, 5),
    image_url: getRandomImage(),
    createdAt: createdAt.toISOString(),
    updatedAt: updatedAt.toISOString(),
  });

  // Generate additional cards to reach 6-10 total
  const remainingCount = randomInt(6, 10) - cards.length;
  for (let i = 0; i < remainingCount; i++) {
    const tags: OpsCard['tags'] = [];
    if (Math.random() > 0.6) tags.push('fork_soon');
    if (Math.random() > 0.6) tags.push('disclosure_active');
    
    const createdAt = new Date(now.getTime() - randomInt(1, 48) * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 120) * 60 * 1000); // Updated within last 2 hours

    cards.push({
      id: `ops_about_${i + 1}`,
      type: 'timeline',
      title: `Timeline ${i + 1}: About to Happen`,
      subtitle: 'Upcoming event or fork',
      lane: 'about_to_happen',
      tags,
      stability: randomInt(55, 85),
      logicGap: randomInt(20, 45),
      nextForkEtaSec: tags.includes('fork_soon') ? randomInt(60, 900) : randomInt(300, 3600),
      entropyRate: randomInt(-3, 1),
      sabotageHeat24h: Math.random() > 0.4 ? randomInt(0, 10) : undefined,
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
    });
  }

  return cards;
}

/**
 * Generate mock cards for at_risk lane
 * Must include paradox_active with logicGap > 60 and brittle items with logicGap 40-60
 */
function generateAtRiskCards(): OpsCard[] {
  const cards: OpsCard[] = [];

  // 1-2 items with paradox_active and logicGap > 60
  const paradoxCount = randomInt(1, 2);
  for (let i = 0; i < paradoxCount; i++) {
    const logicGap = randomInt(61, 85); // > 60
    const createdAt = new Date(now.getTime() - randomInt(3, 14) * 24 * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 180) * 60 * 1000); // Updated within last 3 hours
    
    cards.push({
      id: `ops_paradox_active_${i + 1}`,
      type: 'timeline',
      title: `Paradox Active ${i + 1}: ${['Contagion Zero', 'Oil Crisis'][i] || 'Timeline'}`,
      subtitle: 'Active paradox detected',
      lane: 'at_risk',
      tags: ['paradox_active'],
      stability: randomInt(25, 45),
      logicGap: logicGap,
      paradoxProximity: randomInt(80, 95),
      entropyRate: randomInt(-6, -3),
      sabotageHeat24h: randomInt(3, 10),
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
    });
  }

  // Several brittle items with logicGap 40-60
  const brittleCount = randomInt(3, 5);
  for (let i = 0; i < brittleCount; i++) {
    const logicGap = randomInt(40, 60); // Brittle range
    const createdAt = new Date(now.getTime() - randomInt(2, 10) * 24 * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 240) * 60 * 1000); // Updated within last 4 hours
    
    cards.push({
      id: `ops_brittle_${i + 1}`,
      type: 'timeline',
      title: `Brittle Timeline ${i + 1}: ${['Oil Crisis', 'Geopolitical Tension', 'Market Volatility', 'Supply Chain', 'Energy'][i] || 'Timeline'}`,
      subtitle: 'Logic gap widening',
      lane: 'at_risk',
      tags: ['brittle'],
      stability: randomInt(30, 50),
      logicGap: logicGap,
      paradoxProximity: randomInt(30, 70),
      entropyRate: randomInt(-5, -2),
      sabotageHeat24h: randomInt(2, 8),
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
    });
  }

  // Generate additional cards to reach 6-10 total
  const remainingCount = randomInt(6, 10) - cards.length;
  for (let i = 0; i < remainingCount; i++) {
    const tags: OpsCard['tags'] = [];
    if (Math.random() > 0.5) tags.push('brittle');
    if (Math.random() > 0.6) tags.push('high_entropy');
    if (Math.random() > 0.6) tags.push('sabotage_heat');

    const createdAt = new Date(now.getTime() - randomInt(1, 14) * 24 * 60 * 60 * 1000);
    const updatedAt = new Date(now.getTime() - randomInt(0, 120) * 60 * 1000); // Updated within last 2 hours

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
      sabotageHeat24h: Math.random() > 0.3 ? randomInt(0, 10) : undefined,
      image_url: getRandomImage(),
      createdAt: createdAt.toISOString(),
      updatedAt: updatedAt.toISOString(),
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
      image_url: getRandomImage(),
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
        image_url: getRandomImage(),
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
        image_url: getRandomImage(),
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
