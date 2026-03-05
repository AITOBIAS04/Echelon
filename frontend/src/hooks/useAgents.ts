// Agents Hooks — Wired to real backend APIs
// GET /api/v1/agents → AgentListResponse

import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Agent, AgentListResponse, AgentArchetype } from '../types/agents';
import { getSanityLevel } from '../types/agents';

// ============================================
// API FETCHERS
// ============================================

async function fetchAgents(params?: {
  archetype?: string;
  is_alive?: boolean;
  limit?: number;
  offset?: number;
}): Promise<AgentListResponse> {
  const { data } = await apiClient.get<AgentListResponse>('/api/v1/agents', { params });
  return data;
}

// ============================================
// ARCHETYPE PRESENTATION
// ============================================

const ARCHETYPE_COLORS: Record<AgentArchetype, string> = {
  WHALE: '#3B82F6',
  SHARK: '#EC4899',
  DIPLOMAT: '#A855F7',
  SPY: '#F59E0B',
  SABOTEUR: '#EF4444',
  DEGEN: '#10B981',
};

const ARCHETYPE_EMOJI: Record<AgentArchetype, string> = {
  WHALE: '\u{1F40B}',
  SHARK: '\u{1F988}',
  DIPLOMAT: '\u{1F91D}',
  SPY: '\u{1F575}\u{FE0F}',
  SABOTEUR: '\u{1F4A3}',
  DEGEN: '\u{1F3B2}',
};

// ============================================
// VIEW INTERFACES — Stub types for Intelligence tab (no backend endpoint)
// ============================================

export interface TheatreView {
  id: string;
  name: string;
  activityLevel: 'high' | 'medium' | 'low';
  agents: number;
  activity: number;
  volume: number;
  instability: number;
}

export interface MovementView {
  id: string;
  timestamp: string;
  action: 'deploy' | 'withdraw' | 'strategy';
  agent: string;
  theatre: string;
  velocity: number;
  velocityType: 'positive' | 'negative' | 'neutral';
}

export interface StrategyClusterView {
  archetype: string;
  emoji: string;
  count: number;
  totalPL: number;
  avgWinRate: number;
  style: 'aggressive' | 'moderate' | 'conservative';
}

export interface ConflictView {
  id: string;
  severity: 'high-impact' | 'medium-impact' | 'low-impact';
  agent1: string;
  agent2: string;
  theatre: string;
  details: string;
  impact: number;
}

// ============================================
// VIEW MODEL — Enriched agent for page components
// ============================================

export interface EnrichedAgent extends Agent {
  pnl: number;
  pnlDisplay: string;
  emoji: string;
  generation: number;
  lineage: string;
  isGenesis: boolean;
  parents?: string;
  actions: number;
  winRate: number;
  sanityLevel: import('../types/agents').SanityLevel;
  sanityStatus: string;
  color: string;
}

function enrichAgent(agent: Agent): EnrichedAgent {
  const sanityLevel = getSanityLevel(agent.sanity, agent.max_sanity);
  const isGenesis = agent.parent_agent_ids.length === 0;
  const pnl = agent.total_pnl_usd;
  return {
    ...agent,
    pnl,
    pnlDisplay: `${pnl >= 0 ? '+' : '-'}$${Math.abs(pnl).toLocaleString()}`,
    emoji: ARCHETYPE_EMOJI[agent.archetype] ?? '\u{1F916}',
    generation: isGenesis ? 1 : 2,
    lineage: isGenesis ? 'GENESIS AGENT' : agent.parent_agent_ids.join(' \u00D7 '),
    isGenesis,
    parents: isGenesis ? undefined : agent.parent_agent_ids.join(' \u00D7 '),
    actions: agent.trades_count,
    winRate: Math.round(agent.win_rate * 100),
    sanityLevel,
    sanityStatus: sanityLevel.toUpperCase(),
    color: ARCHETYPE_COLORS[agent.archetype] ?? '#888',
  };
}

// ============================================
// HOOKS — Real API
// ============================================

export function useAgentRoster() {
  const { data: resp, isLoading, error } = useQuery({
    queryKey: ['agents', 'roster'],
    queryFn: () => fetchAgents({ is_alive: true }),
    refetchInterval: 30_000,
  });

  const agents = useMemo(
    () => (resp?.agents ?? []).map(enrichAgent),
    [resp],
  );

  const stats = useMemo(() => {
    const totalPL = agents.reduce((sum, a) => sum + a.total_pnl_usd, 0);
    const avgWinRate = agents.length > 0
      ? agents.reduce((sum, a) => sum + a.winRate, 0) / agents.length
      : 0;
    const avgSanity = agents.length > 0
      ? agents.reduce((sum, a) => sum + a.sanity, 0) / agents.length
      : 0;
    const genesisCount = agents.filter(a => a.isGenesis).length;
    const totalActions = agents.reduce((sum, a) => sum + a.actions, 0);

    return { totalPL, avgWinRate, avgSanity, genesisCount, totalActions };
  }, [agents]);

  return { agents, stats, isLoading, error };
}

export function useArchetypeDistribution() {
  const { agents } = useAgentRoster();

  return useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of agents) {
      counts[a.archetype] = (counts[a.archetype] || 0) + 1;
    }
    return Object.entries(counts).map(([archetype, count]) => ({
      archetype: archetype as AgentArchetype,
      count,
      color: ARCHETYPE_COLORS[archetype as AgentArchetype] ?? '#888',
      emoji: ARCHETYPE_EMOJI[archetype as AgentArchetype] ?? '\u{1F916}',
    }));
  }, [agents]);
}

export function useSanityDistribution() {
  const { agents } = useAgentRoster();

  return useMemo(() => {
    const dist = { stable: 0, stressed: 0, critical: 0, breakdown: 0 };
    for (const a of agents) {
      const level = getSanityLevel(a.sanity, a.max_sanity);
      dist[level]++;
    }
    return dist;
  }, [agents]);
}

// ============================================
// HOOKS — Presentation helpers
// ============================================

export function getAgentColor(archetype: AgentArchetype): string {
  return ARCHETYPE_COLORS[archetype] ?? '#888';
}

export function useAgentsStatus() {
  const [clock, setClock] = useState('--:--:-- UTC');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return { clock };
}

// Legacy hooks — return empty data (no backend endpoint)
export function usePerformanceStats() {
  const { stats } = useAgentRoster();
  return {
    totalPL: stats.totalPL,
    winRate: stats.avgWinRate,
    totalActions: stats.totalActions,
    avgSanity: stats.avgSanity,
    genesisAgents: stats.genesisCount,
  };
}

export function useDashboardStats() {
  const { agents } = useAgentRoster();
  return {
    totalAgents: agents.length,
    deployedAgents: agents.filter(a => a.is_alive).length,
    movements24h: 0,
    activeConflicts: 0,
  };
}

export function useTheatres(): TheatreView[] {
  return [];
}

export function useMovements(): MovementView[] {
  return [];
}

export function useStrategyClusters(): StrategyClusterView[] {
  return [];
}

export function useConflicts(): ConflictView[] {
  return [];
}

// Backward-compatible useAgents hook
export function useAgents() {
  const { agents, isLoading } = useAgentRoster();
  return { data: { agents }, isLoading };
}
