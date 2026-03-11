/**
 * useAgentMatrix — Joins deployments + agents + theatres into a single
 * cross-reference view for the Agent Matrix page.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDeploymentList } from './useAgentDeployments';
import { useAgentRoster } from './useAgents';
import { apiClient } from '../api/client';
import type { Agent, AgentArchetype, SanityLevel } from '../types/agents';
import { getSanityLevel } from '../types/agents';
import type { AgentDeploymentSummary, StrategyProfile } from '../types/agentDeployment';
import type { TheatreResponse } from '../types/theatre';

// ── Joined row for the matrix table ─────────────────────────────────

export interface MatrixRow {
  deployment: AgentDeploymentSummary;
  agent: Agent | undefined;
  theatre: TheatreResponse | undefined;
  // Pre-computed display fields
  agentName: string;
  agentEmoji: string;
  archetype: AgentArchetype | string;
  theatreLabel: string;
  strategy: StrategyProfile | string;
  sanity: number;
  maxSanity: number;
  sanityLevel: SanityLevel;
  pnl: number;
  deployedAt: string;
}

// ── KPI summary ─────────────────────────────────────────────────────

export interface MatrixKPIs {
  activeDeployments: number;
  agentsDeployed: number;
  theatresCovered: number;
  paused: number;
  avgSanity: number;
  avgSanityLevel: SanityLevel;
  fleetPnl: number;
}

// ── Page state ──────────────────────────────────────────────────────

export type MatrixPageState = 'EMPTY' | 'NOMINAL' | 'ALERT';

// ── Archetype emoji map ─────────────────────────────────────────────

const ARCHETYPE_EMOJI: Record<string, string> = {
  WHALE: '🐋',
  SHARK: '🦈',
  DIPLOMAT: '🤝',
  SPY: '🕵️',
  SABOTEUR: '💣',
  DEGEN: '🎲',
};

// ── Theatre list fetcher ────────────────────────────────────────────

function useTheatreList() {
  const query = useQuery({
    queryKey: ['theatres-list'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ theatres: TheatreResponse[]; total: number }>(
        '/api/v1/theatres/',
      );
      return data;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  return {
    theatres: query.data?.theatres ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

// ── Main hook ───────────────────────────────────────────────────────

export function useAgentMatrix() {
  const { deployments, isLoading: deploymentsLoading, error: deploymentsError } = useDeploymentList();
  const { agents, isLoading: agentsLoading, error: agentsError } = useAgentRoster();
  const { theatres, isLoading: theatresLoading, error: theatresError } = useTheatreList();

  const isLoading = deploymentsLoading || agentsLoading || theatresLoading;
  const error = deploymentsError || agentsError || theatresError;

  // Build lookup maps
  const agentMap = useMemo(() => {
    const map = new Map<string, Agent>();
    for (const a of agents) map.set(a.id, a);
    return map;
  }, [agents]);

  const theatreMap = useMemo(() => {
    const map = new Map<string, TheatreResponse>();
    for (const t of theatres) {
      map.set(t.id, t);
      if (t.construct_id) map.set(t.construct_id, t);
    }
    return map;
  }, [theatres]);

  // Join into matrix rows
  const rows: MatrixRow[] = useMemo(() => {
    return deployments.map((d) => {
      const agent = agentMap.get(d.agent_id);
      const theatre = theatreMap.get(d.theatre_id);
      return {
        deployment: d,
        agent,
        theatre,
        agentName: agent?.name ?? d.agent_id.slice(0, 12),
        agentEmoji: agent ? (ARCHETYPE_EMOJI[agent.archetype] ?? '🤖') : '🤖',
        archetype: agent?.archetype ?? 'UNKNOWN',
        theatreLabel: theatre?.construct_id ?? d.theatre_id.slice(0, 16),
        strategy: (d.strategy_profile ?? 'BALANCED') as StrategyProfile,
        sanity: agent?.sanity ?? 0,
        maxSanity: agent?.max_sanity ?? 100,
        sanityLevel: agent ? getSanityLevel(agent.sanity, agent.max_sanity) : 'stable',
        pnl: agent?.total_pnl_usd ?? 0,
        deployedAt: d.deployed_at ?? d.created_at,
      };
    });
  }, [deployments, agentMap, theatreMap]);

  // Compute KPIs
  const kpis: MatrixKPIs = useMemo(() => {
    const active = rows.filter((r) => r.deployment.status === 'ACTIVE');
    const paused = rows.filter((r) => r.deployment.status === 'PAUSED');
    const uniqueAgents = new Set(active.map((r) => r.deployment.agent_id));
    const uniqueTheatres = new Set(active.map((r) => r.deployment.theatre_id));

    const deployedAgents = [...uniqueAgents]
      .map((id) => agentMap.get(id))
      .filter((a): a is Agent => a !== undefined);

    const avgSanity =
      deployedAgents.length > 0
        ? Math.round(
            deployedAgents.reduce((sum, a) => sum + (a.max_sanity > 0 ? (a.sanity / a.max_sanity) * 100 : 0), 0) /
              deployedAgents.length,
          )
        : 0;

    const fleetPnl = deployedAgents.reduce((sum, a) => sum + a.total_pnl_usd, 0);

    return {
      activeDeployments: active.length,
      agentsDeployed: uniqueAgents.size,
      theatresCovered: uniqueTheatres.size,
      paused: paused.length,
      avgSanity,
      avgSanityLevel: getSanityLevel(avgSanity, 100),
      fleetPnl,
    };
  }, [rows, agentMap]);

  // Page state
  const pageState: MatrixPageState = useMemo(() => {
    if (rows.length === 0) return 'EMPTY';
    const hasPaused = rows.some((r) => r.deployment.status === 'PAUSED');
    const hasWithdrawn = rows.some((r) => r.deployment.status === 'WITHDRAWN');
    const hasCritical = rows.some((r) => r.sanityLevel === 'critical' || r.sanityLevel === 'breakdown');
    if (hasPaused || hasWithdrawn || hasCritical) return 'ALERT';
    return 'NOMINAL';
  }, [rows]);

  // Alert summary for banner
  const alertSummary = useMemo(() => {
    if (pageState !== 'ALERT') return '';
    const parts: string[] = [];
    const pausedCount = rows.filter((r) => r.deployment.status === 'PAUSED').length;
    const criticalCount = rows.filter(
      (r) => r.sanityLevel === 'critical' || r.sanityLevel === 'breakdown',
    ).length;
    if (pausedCount > 0) parts.push(`${pausedCount} deployment${pausedCount > 1 ? 's' : ''} paused`);
    if (criticalCount > 0) parts.push(`${criticalCount} agent${criticalCount > 1 ? 's' : ''} critical sanity`);
    return parts.join(' · ');
  }, [pageState, rows]);

  // Strategy distribution for sidebar
  const strategyDistribution = useMemo(() => {
    const active = rows.filter((r) => r.deployment.status === 'ACTIVE');
    const counts = { AGGRESSIVE: 0, BALANCED: 0, DEFENSIVE: 0 };
    for (const r of active) {
      const s = r.strategy as keyof typeof counts;
      if (s in counts) counts[s]++;
    }
    return counts;
  }, [rows]);

  return {
    rows,
    kpis,
    pageState,
    alertSummary,
    strategyDistribution,
    isLoading,
    error,
  };
}
