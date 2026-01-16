import type { LaunchpadFeed, LaunchCard, LaunchPhase } from '../types/launchpad';

/**
 * Mock Launchpad API
 * 
 * Provides mock data for launchpad feed and launch listings.
 * Simulates API delays for realistic behavior.
 */

const now = new Date();
const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

/**
 * Mock trending launches (mix of sandbox/pilot, qualityScore 55-90)
 */
const mockTrendingLaunches: LaunchCard[] = [
  {
    id: 'launch_trend_001',
    title: 'Strait of Hormuz Shipping Disruption',
    phase: 'pilot',
    category: 'theatre',
    createdAt: threeDaysAgo.toISOString(),
    updatedAt: oneDayAgo.toISOString(),
    qualityScore: 87,
    forkTargetRange: [8, 12],
    episodeLengthSec: 50,
    tags: ['geopolitics', 'shipping', 'middle-east'],
    founderId: 'founder_001',
    exportEligible: true,
    shortDescription: 'Real-time simulation of maritime conflict scenarios in critical shipping lanes.',
  },
  {
    id: 'launch_trend_002',
    title: 'AI Model Performance Tracking',
    phase: 'sandbox',
    category: 'osint',
    createdAt: oneWeekAgo.toISOString(),
    updatedAt: now.toISOString(),
    qualityScore: 72,
    forkTargetRange: [5, 8],
    episodeLengthSec: 30,
    tags: ['ai', 'ml', 'performance'],
    founderId: 'founder_002',
    exportEligible: false,
    shortDescription: 'Track and predict AI model performance metrics across deployment cycles.',
  },
  {
    id: 'launch_trend_003',
    title: 'Orbital Debris Collision Risk',
    phase: 'pilot',
    category: 'theatre',
    createdAt: twoWeeksAgo.toISOString(),
    updatedAt: threeDaysAgo.toISOString(),
    qualityScore: 91,
    forkTargetRange: [10, 15],
    episodeLengthSec: 60,
    tags: ['space', 'debris', 'collision'],
    founderId: 'founder_003',
    exportEligible: true,
    shortDescription: 'Simulate orbital debris collision scenarios and mitigation strategies.',
  },
  {
    id: 'launch_trend_004',
    title: 'Supply Chain Disruption Analysis',
    phase: 'sandbox',
    category: 'osint',
    createdAt: oneDayAgo.toISOString(),
    updatedAt: now.toISOString(),
    qualityScore: 65,
    forkTargetRange: [6, 10],
    tags: ['supply-chain', 'logistics', 'disruption'],
    founderId: 'founder_001',
    exportEligible: false,
    shortDescription: 'Monitor and predict supply chain disruptions using OSINT data sources.',
  },
  {
    id: 'launch_trend_005',
    title: 'Blacksite Heist Simulation',
    phase: 'pilot',
    category: 'theatre',
    createdAt: oneWeekAgo.toISOString(),
    updatedAt: oneDayAgo.toISOString(),
    qualityScore: 78,
    forkTargetRange: [9, 13],
    episodeLengthSec: 45,
    tags: ['heist', 'security', 'simulation'],
    founderId: 'founder_004',
    exportEligible: true,
    shortDescription: 'High-stakes infiltration and extraction scenarios with multiple decision points.',
  },
];

/**
 * Mock draft launches (0-3 items)
 */
const mockDraftLaunches: LaunchCard[] = [
  {
    id: 'launch_draft_001',
    title: 'Climate Policy Impact Model',
    phase: 'draft',
    category: 'osint',
    createdAt: oneDayAgo.toISOString(),
    updatedAt: now.toISOString(),
    qualityScore: 45,
    forkTargetRange: [4, 7],
    tags: ['climate', 'policy', 'impact'],
    founderId: 'founder_002',
    exportEligible: false,
    shortDescription: 'Early draft - modeling climate policy impacts on economic indicators.',
  },
  {
    id: 'launch_draft_002',
    title: 'Cybersecurity Threat Landscape',
    phase: 'draft',
    category: 'osint',
    createdAt: threeDaysAgo.toISOString(),
    updatedAt: oneDayAgo.toISOString(),
    qualityScore: 38,
    forkTargetRange: [3, 6],
    tags: ['cybersecurity', 'threats', 'intelligence'],
    founderId: 'founder_001',
    exportEligible: false,
  },
];

/**
 * Mock recently graduated launches (qualityScore 80-95, exportEligible true)
 */
const mockGraduatedLaunches: LaunchCard[] = [
  {
    id: 'launch_grad_001',
    title: 'Neon Courier Delivery Network',
    phase: 'graduated',
    category: 'theatre',
    createdAt: twoWeeksAgo.toISOString(),
    updatedAt: oneWeekAgo.toISOString(),
    qualityScore: 89,
    forkTargetRange: [8, 12],
    episodeLengthSec: 50,
    tags: ['delivery', 'network', 'courier'],
    founderId: 'founder_003',
    exportEligible: true,
    shortDescription: 'Fully graduated - active production timeline for courier network simulations.',
  },
  {
    id: 'launch_grad_002',
    title: 'Disaster Response Coordination',
    phase: 'graduated',
    category: 'theatre',
    createdAt: threeDaysAgo.toISOString(),
    updatedAt: oneDayAgo.toISOString(),
    qualityScore: 92,
    forkTargetRange: [10, 14],
    episodeLengthSec: 60,
    tags: ['disaster', 'response', 'coordination'],
    founderId: 'founder_004',
    exportEligible: true,
    shortDescription: 'Graduated to production - real-time disaster response scenario modeling.',
  },
  {
    id: 'launch_grad_003',
    title: 'Social Media Sentiment Tracking',
    phase: 'graduated',
    category: 'osint',
    createdAt: oneWeekAgo.toISOString(),
    updatedAt: threeDaysAgo.toISOString(),
    qualityScore: 84,
    forkTargetRange: [6, 9],
    tags: ['social-media', 'sentiment', 'tracking'],
    founderId: 'founder_002',
    exportEligible: true,
    shortDescription: 'Production-ready OSINT feed for social media sentiment analysis.',
  },
];

/**
 * Get launchpad feed
 * 
 * Returns organized feed with trending, drafts, and recently graduated launches.
 * 
 * @returns Promise resolving to LaunchpadFeed
 */
export async function getLaunchpadFeed(): Promise<LaunchpadFeed> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  return {
    trending: [...mockTrendingLaunches],
    drafts: [...mockDraftLaunches],
    recentlyGraduated: [...mockGraduatedLaunches],
  };
}

/**
 * Get drafts from localStorage
 */
function getLocalStorageDrafts(): LaunchCard[] {
  try {
    const stored = localStorage.getItem('launchpad_drafts');
    if (!stored) return [];
    return JSON.parse(stored);
  } catch {
    return [];
  }
}

/**
 * List launches filtered by phase
 * 
 * Returns all launches matching the specified phase, or all launches if no phase provided.
 * Includes drafts from localStorage.
 * 
 * @param phase Optional phase filter
 * @returns Promise resolving to array of LaunchCard
 */
export async function listLaunches(phase?: LaunchPhase): Promise<LaunchCard[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 200));

  // Get drafts from localStorage
  const localStorageDrafts = getLocalStorageDrafts();

  const allLaunches = [
    ...mockTrendingLaunches,
    ...mockDraftLaunches,
    ...localStorageDrafts,
    ...mockGraduatedLaunches,
  ];

  if (phase) {
    return allLaunches.filter((launch) => launch.phase === phase);
  }

  return allLaunches;
}
