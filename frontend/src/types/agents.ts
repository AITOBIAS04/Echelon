// Agent Types — Aligned with backend/database/models.py Agent + backend/api/agents_routes.py
// API response types use snake_case matching raw JSON from backend.

export type AgentArchetype = 'SHARK' | 'SPY' | 'DIPLOMAT' | 'SABOTEUR' | 'WHALE' | 'DEGEN';

// ============================================
// AGENT (GET /api/v1/agents, GET /api/v1/agents/:id)
// ============================================

export interface Agent {
  id: string;
  name: string;
  archetype: AgentArchetype;
  tier: number;
  level: number;

  // Status
  sanity: number;
  max_sanity: number;
  is_alive: boolean;
  death_cause: string | null;

  // Owner
  owner_id: string;

  // Performance
  total_pnl_usd: number;
  win_rate: number;
  trades_count: number;

  // Genome (evolution)
  genome: Record<string, unknown>;
  parent_agent_ids: string[];

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

// ============================================
// FRONTEND VIEW HELPERS
// ============================================

export type SanityLevel = 'stable' | 'stressed' | 'critical' | 'breakdown';

export function getSanityLevel(sanity: number, maxSanity: number): SanityLevel {
  const ratio = maxSanity > 0 ? sanity / maxSanity : 0;
  if (ratio >= 0.7) return 'stable';
  if (ratio >= 0.4) return 'stressed';
  if (ratio >= 0.15) return 'critical';
  return 'breakdown';
}

export type AgentView = 'roster' | 'intelligence';
