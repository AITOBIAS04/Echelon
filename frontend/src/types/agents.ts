// Agents Types
// Types for the Agent Roster and Global Intelligence pages

export type SanityLevel = 'stable' | 'stressed' | 'critical' | 'breakdown';
export type SanityStatus = 'STABLE' | 'STRESSED' | 'CRITICAL' | 'BREAKDOWN RISK';

export type Archetype = 'WHALE' | 'SHARK' | 'DIPLOMAT' | 'SPY' | 'SABOTEUR' | 'DEGEN';

export interface Agent {
  id: string;
  name: string;
  archetype: Archetype;
  emoji: string;
  pnl: number;
  pnlDisplay: string;
  generation: number;
  lineage: string;
  isGenesis: boolean;
  parents?: string;
  actions: number;
  winRate: number;
  sanity: number;
  sanityLevel: SanityLevel;
  sanityStatus: SanityStatus;
  color: string;
}

export interface ArchetypeCount {
  archetype: Archetype;
  emoji: string;
  count: number;
}

export interface PerformanceStats {
  totalPL: number;
  winRate: number;
  totalActions: number;
  avgSanity: number;
  genesisAgents: number;
}

export interface SanityDistribution {
  stable: number;
  stressed: number;
  critical: number;
  breakdown: number;
}

export interface DashboardStats {
  totalAgents: number;
  deployedAgents: number;
  movements24h: number;
  activeConflicts: number;
}

export interface Theatre {
  id: string;
  name: string;
  agents: number;
  activity: number;
  activityLevel: 'high' | 'medium' | 'low';
  volume: number;
  instability: number;
}

export interface Movement {
  id: string;
  agent: string;
  action: 'deploy' | 'withdraw' | 'strategy';
  theatre: string;
  timestamp: Date;
  velocity: number;
  velocityType: 'positive' | 'negative' | 'neutral';
}

export interface StrategyCluster {
  archetype: Archetype;
  emoji: string;
  count: number;
  totalPL: number;
  avgWinRate: number;
  style: 'aggressive' | 'moderate' | 'conservative';
}

export interface Conflict {
  id: string;
  agent1: string;
  agent2: string;
  theatre: string;
  severity: 'high-impact' | 'medium-impact' | 'low-impact';
  impact: number;
  details: string;
}

export type AgentView = 'roster' | 'intelligence';
