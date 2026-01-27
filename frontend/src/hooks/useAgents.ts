// Agents Hooks
// React hooks for Agent Roster and Global Intelligence data

import { useState, useEffect, useMemo } from 'react';
import type {
  Agent,
  ArchetypeCount,
  PerformanceStats,
  SanityDistribution,
  DashboardStats,
  Theatre,
  Movement,
  StrategyCluster,
  Conflict,
} from '../types/agents';

// Mock agents data
const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'MEGALODON',
    archetype: 'WHALE',
    emoji: '🐋',
    pnl: 124580,
    pnlDisplay: '+$124,580',
    generation: 1,
    lineage: 'GENESIS AGENT',
    isGenesis: true,
    actions: 2847,
    winRate: 78,
    sanity: 85,
    sanityLevel: 'stable',
    sanityStatus: 'STABLE',
    color: '#3B82F6',
  },
  {
    id: '2',
    name: 'AEGIS',
    archetype: 'DIPLOMAT',
    emoji: '🤝',
    pnl: 89340,
    pnlDisplay: '+$89,340',
    generation: 2,
    lineage: 'MEGALODON × PHANTOM',
    isGenesis: false,
    parents: 'MEGALODON × PHANTOM',
    actions: 1924,
    winRate: 72,
    sanity: 78,
    sanityLevel: 'stable',
    sanityStatus: 'STABLE',
    color: '#A855F7',
  },
  {
    id: '3',
    name: 'SABOTEUR',
    archetype: 'SABOTEUR',
    emoji: '💣',
    pnl: 67890,
    pnlDisplay: '+$67,890',
    generation: 1,
    lineage: 'GENESIS AGENT',
    isGenesis: true,
    actions: 1456,
    winRate: 68,
    sanity: 52,
    sanityLevel: 'stressed',
    sanityStatus: 'STRESSED',
    color: '#EF4444',
  },
  {
    id: '4',
    name: 'VIPER',
    archetype: 'SHARK',
    emoji: '🦈',
    pnl: -12450,
    pnlDisplay: '-$12,450',
    generation: 3,
    lineage: 'CARDINAL × SPECTER',
    isGenesis: false,
    parents: 'CARDINAL × SPECTER',
    actions: 892,
    winRate: 45,
    sanity: 18,
    sanityLevel: 'critical',
    sanityStatus: 'CRITICAL',
    color: '#EC4899',
  },
  {
    id: '5',
    name: 'ORACLE',
    archetype: 'DIPLOMAT',
    emoji: '🤝',
    pnl: 54230,
    pnlDisplay: '+$54,230',
    generation: 2,
    lineage: 'ENVOY × CARDINAL',
    isGenesis: false,
    parents: 'ENVOY × CARDINAL',
    actions: 1234,
    winRate: 71,
    sanity: 92,
    sanityLevel: 'stable',
    sanityStatus: 'STABLE',
    color: '#A855F7',
  },
  {
    id: '6',
    name: 'SPECTER',
    archetype: 'SPY',
    emoji: '🕵️',
    pnl: 41670,
    pnlDisplay: '+$41,670',
    generation: 2,
    lineage: 'MEGALODON × PHANTOM',
    isGenesis: false,
    parents: 'MEGALODON × PHANTOM',
    actions: 678,
    winRate: 82,
    sanity: 45,
    sanityLevel: 'stressed',
    sanityStatus: 'STRESSED',
    color: '#F59E0B',
  },
];

// Mock archetype counts
const mockArchetypeCounts: ArchetypeCount[] = [
  { archetype: 'WHALE', emoji: '🐋', count: 3 },
  { archetype: 'DIPLOMAT', emoji: '🤝', count: 3 },
  { archetype: 'SABOTEUR', emoji: '💣', count: 2 },
  { archetype: 'SHARK', emoji: '🦈', count: 2 },
  { archetype: 'SPY', emoji: '🕵️', count: 2 },
];

// Mock performance stats
const mockPerformanceStats: PerformanceStats = {
  totalPL: 482340,
  winRate: 68,
  totalActions: 12847,
  avgSanity: 72,
  genesisAgents: 4,
};

// Mock sanity distribution
const mockSanityDistribution: SanityDistribution = {
  stable: 7,
  stressed: 3,
  critical: 1,
  breakdown: 1,
};

// Mock dashboard stats
const mockDashboardStats: DashboardStats = {
  totalAgents: 12,
  deployedAgents: 8,
  movements24h: 47,
  activeConflicts: 3,
};

// Mock theatres
const mockTheatres: Theatre[] = [
  { id: 'T1', name: 'ORBITAL SALVAGE', agents: 4, activity: 92, activityLevel: 'high', volume: 2450000, instability: 12 },
  { id: 'T2', name: 'FED RATE DECISION', agents: 3, activity: 78, activityLevel: 'medium', volume: 1890000, instability: 8 },
  { id: 'T3', name: 'VENUS OIL TANKER', agents: 2, activity: 45, activityLevel: 'low', volume: 890000, instability: 5 },
  { id: 'T4', name: 'TAIWAN STRAIT', agents: 3, activity: 67, activityLevel: 'medium', volume: 1560000, instability: 15 },
];

// Mock movements
const mockMovements: Movement[] = [
  { id: '1', agent: 'MEGALODON', action: 'deploy', theatre: 'ORBITAL SALVAGE', timestamp: new Date(Date.now() - 120000), velocity: 12, velocityType: 'positive' },
  { id: '2', agent: 'VIPER', action: 'withdraw', theatre: 'FED RATE', timestamp: new Date(Date.now() - 300000), velocity: -8, velocityType: 'negative' },
  { id: '3', agent: 'AEGIS', action: 'strategy', theatre: 'VENUS OIL', timestamp: new Date(Date.now() - 600000), velocity: 0, velocityType: 'neutral' },
  { id: '4', agent: 'SABOTEUR', action: 'deploy', theatre: 'TAIWAN STRAIT', timestamp: new Date(Date.now() - 900000), velocity: 5, velocityType: 'positive' },
  { id: '5', agent: 'ORACLE', action: 'strategy', theatre: 'ORBITAL SALVAGE', timestamp: new Date(Date.now() - 1200000), velocity: 3, velocityType: 'positive' },
];

// Mock strategy clusters
const mockStrategyClusters: StrategyCluster[] = [
  { archetype: 'SHARK', emoji: '🦈', count: 2, totalPL: 125000, avgWinRate: 62, style: 'aggressive' },
  { archetype: 'DIPLOMAT', emoji: '🤝', count: 3, totalPL: 245000, avgWinRate: 74, style: 'moderate' },
  { archetype: 'SABOTEUR', emoji: '💣', count: 2, totalPL: 89000, avgWinRate: 58, style: 'aggressive' },
];

// Mock conflicts
const mockConflicts: Conflict[] = [
  { id: '1', agent1: 'MEGALODON', agent2: 'VIPER', theatre: 'ORBITAL SALVAGE', severity: 'high-impact', impact: -24000, details: 'Opposing positions on fork outcome' },
  { id: '2', agent1: 'SABOTEUR', agent2: 'AEGIS', theatre: 'TAIWAN STRAIT', severity: 'medium-impact', impact: -8500, details: 'Strategy conflict - spread vs hedge' },
  { id: '3', agent1: 'ORACLE', agent2: 'SPECTER', theatre: 'FED RATE', severity: 'low-impact', impact: 3200, details: 'Complementary intelligence gathering' },
];

// Hook for agent roster
export function useAgentRoster() {
  const [agents] = useState<Agent[]>(mockAgents);

  const stats = useMemo(() => {
    const totalPL = agents.reduce((sum, a) => sum + a.pnl, 0);
    const avgWinRate = agents.reduce((sum, a) => sum + a.winRate, 0) / agents.length;
    const avgSanity = agents.reduce((sum, a) => sum + a.sanity, 0) / agents.length;
    const genesisCount = agents.filter(a => a.isGenesis).length;
    const totalActions = agents.reduce((sum, a) => sum + a.actions, 0);

    return { totalPL, avgWinRate, avgSanity, genesisCount, totalActions };
  }, [agents]);

  return { agents, stats };
}

// Hook for archetype distribution
export function useArchetypeDistribution() {
  return mockArchetypeCounts;
}

// Hook for performance stats
export function usePerformanceStats() {
  return mockPerformanceStats;
}

// Hook for sanity distribution
export function useSanityDistribution() {
  return mockSanityDistribution;
}

// Hook for dashboard stats
export function useDashboardStats() {
  return mockDashboardStats;
}

// Hook for theatres
export function useTheatres() {
  return mockTheatres;
}

// Hook for movements
export function useMovements() {
  const [movements, setMovements] = useState<Movement[]>(mockMovements);

  // Simulate new movements
  useEffect(() => {
    const interval = setInterval(() => {
      const newMovement: Movement = {
        id: Math.random().toString(36).substr(2, 9),
        agent: mockAgents[Math.floor(Math.random() * mockAgents.length)].name,
        action: ['deploy', 'withdraw', 'strategy'][Math.floor(Math.random() * 3)] as 'deploy' | 'withdraw' | 'strategy',
        theatre: ['ORBITAL SALVAGE', 'FED RATE DECISION', 'VENUS OIL TANKER', 'TAIWAN STRAIT'][Math.floor(Math.random() * 4)],
        timestamp: new Date(),
        velocity: Math.floor(Math.random() * 20) - 10,
        velocityType: Math.random() > 0.5 ? 'positive' : 'negative',
      };
      setMovements((prev) => [newMovement, ...prev.slice(0, 19)]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return movements;
}

// Hook for strategy clusters
export function useStrategyClusters() {
  return mockStrategyClusters;
}

// Hook for conflicts
export function useConflicts() {
  return mockConflicts;
}

// Hook for system status
export function useAgentsStatus() {
  const [clock, setClock] = useState('--:--:-- UTC');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toISOString().substr(11, 8) + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return { clock };
}

// Backward-compatible useAgents hook for legacy components
export function useAgents() {
  const [agents] = useState<any[]>(mockAgents.map(agent => ({
    id: agent.id,
    name: agent.name,
    archetype: agent.archetype,
    total_pnl_usd: agent.pnl,
    actions_count: agent.actions,
    win_rate: agent.winRate / 100,
    sanity: agent.sanity,
    max_sanity: 100,
  })));
  const [isLoading] = useState(false);

  return { data: { agents }, isLoading };
}
