// Breaches Hooks — Wired to real backend APIs
// GET /api/v1/paradox/active → ParadoxListResponse

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Breach } from '../types/breach';
import type { Paradox, ParadoxListResponse } from '../types';
export type { Paradox };

// ============================================
// API FETCHERS
// ============================================

async function fetchActiveParadoxes(): Promise<ParadoxListResponse> {
  const { data } = await apiClient.get<ParadoxListResponse>('/api/v1/paradox/active');
  return data;
}

// ============================================
// TRANSFORMERS — Paradox → legacy Breach adapter
// ============================================

function severityFromClass(cls: string): Breach['severity'] {
  switch (cls) {
    case 'CLASS_1_CRITICAL': return 'critical';
    case 'CLASS_2_SEVERE': return 'high';
    case 'CLASS_3_MODERATE': return 'medium';
    default: return 'low';
  }
}

function statusFromParadox(s: string): Breach['status'] {
  switch (s) {
    case 'ACTIVE': return 'active';
    case 'EXTRACTING': return 'investigating';
    case 'DETONATED': return 'mitigated';
    case 'RESOLVED': return 'resolved';
    default: return 'active';
  }
}

function paradoxToBreach(p: Paradox): Breach {
  const gapPct = Math.round(p.logic_gap * 100);
  return {
    id: p.id,
    timestamp: p.spawned_at,
    severity: severityFromClass(p.severity_class),
    category: 'paradox_detonation',
    title: `Paradox in ${p.timeline_name}`,
    description: `Logic gap ${gapPct}% — decay ${p.decay_multiplier}x — ${p.time_remaining_seconds}s until detonation`,
    affectedTimelines: [{
      id: p.timeline_id,
      name: p.timeline_name,
      stabilityBefore: 100,
      stabilityAfter: Math.max(0, 100 - gapPct),
      logicGapBefore: 0,
      logicGapAfter: gapPct,
    }],
    affectedAgents: p.carrier_agent_id ? [{
      id: p.carrier_agent_id,
      name: p.carrier_agent_name ?? 'Unknown',
      archetype: 'UNKNOWN',
      pnlImpact: 0,
      sanityImpact: -p.carrier_sanity_cost,
    }] : [],
    rootCause: `Logic gap exceeded threshold (${gapPct}%)`,
    beneficiaries: [],
    evidenceChanges: [],
    status: statusFromParadox(p.status),
    recoverable: p.status === 'ACTIVE',
    suggestedActions: [],
  };
}

// ============================================
// HOOKS — Real API
// ============================================

/**
 * Returns breaches adapted from real Paradox API.
 * Used by BreachesPanel and OverviewTab (legacy Breach type).
 */
export function useBreaches() {
  return useQuery<Breach[], Error>({
    queryKey: ['paradox', 'active', 'breaches'],
    queryFn: async () => {
      const resp = await fetchActiveParadoxes();
      return resp.paradoxes.map(paradoxToBreach);
    },
    refetchInterval: 15_000,
  });
}

/**
 * Returns raw Paradox data from backend.
 * Used by BreachConsolePage for detailed paradox view.
 */
export function useParadoxes() {
  const { data: resp, isLoading, error } = useQuery({
    queryKey: ['paradox', 'active'],
    queryFn: fetchActiveParadoxes,
    refetchInterval: 15_000,
  });

  return {
    paradoxes: resp?.paradoxes ?? [],
    totalActive: resp?.total_active ?? 0,
    isLoading,
    error,
  };
}
