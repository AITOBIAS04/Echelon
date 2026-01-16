import type { EntityGraph, GraphNode, GraphEdge } from '../types/graph';

/**
 * Mock Graph API
 * ==============
 * 
 * Provides mock data for entity graph visualization.
 * In production, this would call the actual API endpoint.
 */

/**
 * Get Entity Graph
 * 
 * Returns a graph of entities and their relationships for visualization.
 * 
 * @param scope - Scope of data to include ('my', 'workspace', or 'global')
 * @returns Promise resolving to EntityGraph
 */
export async function getEntityGraph(
  _scope: 'my' | 'workspace' | 'global'
): Promise<EntityGraph> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));
  
  // Note: scope parameter is available for future filtering logic
  // Currently returns the same graph for all scopes in mock implementation

  // Mock nodes
  const nodes: GraphNode[] = [
    // Wallets (2)
    {
      id: 'wallet_0x1234',
      type: 'wallet',
      label: '0x1234...5678',
      meta: {
        totalValue: 12500,
        positions: 3,
      },
    },
    {
      id: 'wallet_0xabcd',
      type: 'wallet',
      label: '0xabcd...ef01',
      meta: {
        totalValue: 8500,
        positions: 2,
      },
    },
    // Agents (3)
    {
      id: 'agent_alpha',
      type: 'agent',
      label: 'Alpha',
      meta: {
        archetype: 'Analyst',
        sanity: 75,
        pnl: -2500,
      },
    },
    {
      id: 'agent_beta',
      type: 'agent',
      label: 'Beta',
      meta: {
        archetype: 'Trader',
        sanity: 60,
        pnl: 1800,
      },
    },
    {
      id: 'agent_shadow',
      type: 'agent',
      label: 'Shadow Broker',
      meta: {
        archetype: 'Saboteur',
        sanity: 45,
        pnl: 5000,
      },
    },
    // Timelines (3)
    {
      id: 'tl_oil_hormuz_001',
      type: 'timeline',
      label: 'Oil Crisis - Hormuz Strait',
      meta: {
        stability: 54.7,
        logicGap: 42,
        yesPrice: 0.45,
      },
    },
    {
      id: 'tl_fed_rate_jan26',
      type: 'timeline',
      label: 'Fed Rate Decision - January 2026',
      meta: {
        stability: 89.2,
        logicGap: 8,
        yesPrice: 0.72,
      },
    },
    {
      id: 'tl_tech_reg_001',
      type: 'timeline',
      label: 'Tech Regulation - AI Oversight',
      meta: {
        stability: 55.8,
        logicGap: 60,
        yesPrice: 0.38,
      },
    },
    // Evidence (4)
    {
      id: 'ev_ravenpack_001',
      type: 'evidence',
      label: 'RavenPack: Naval Activity',
      meta: {
        source: 'RavenPack',
        confidence: 85,
        sentiment: 'bearish',
      },
    },
    {
      id: 'ev_spire_001',
      type: 'evidence',
      label: 'Spire AIS: Shipping Rerouting',
      meta: {
        source: 'Spire AIS',
        confidence: 70,
        sentiment: 'bearish',
      },
    },
    {
      id: 'ev_xapi_001',
      type: 'evidence',
      label: 'X API: Analyst Dismissal',
      meta: {
        source: 'X API',
        confidence: 40,
        sentiment: 'bullish',
      },
    },
    {
      id: 'ev_gdelt_001',
      type: 'evidence',
      label: 'GDELT: Regulatory Signal',
      meta: {
        source: 'GDELT',
        confidence: 55,
        sentiment: 'neutral',
      },
    },
    // Sabotage Events (2)
    {
      id: 'sab_001',
      type: 'sabotage',
      label: 'Sensor Noise Attack',
      meta: {
        saboteur: 'agent_shadow',
        stakeAmount: 1500,
        effectSize: -8,
      },
    },
    {
      id: 'sab_002',
      type: 'sabotage',
      label: 'Evidence Injection',
      meta: {
        saboteur: 'agent_shadow',
        stakeAmount: 2000,
        effectSize: -12,
      },
    },
    // Paradox Event (1)
    {
      id: 'paradox_001',
      type: 'paradox',
      label: 'Paradox Detonation',
      meta: {
        severity: 'CLASS_2_SEVERE',
        triggerReason: 'logic_gap',
        triggerValue: 62,
      },
    },
  ];

  // Mock edges
  const edges: GraphEdge[] = [
    // Wallet positions
    {
      id: 'edge_001',
      from: 'wallet_0x1234',
      to: 'tl_oil_hormuz_001',
      relation: 'holds_position',
      weight: 0.8,
    },
    {
      id: 'edge_002',
      from: 'wallet_0x1234',
      to: 'tl_fed_rate_jan26',
      relation: 'holds_position',
      weight: 0.6,
    },
    {
      id: 'edge_003',
      from: 'wallet_0xabcd',
      to: 'tl_oil_hormuz_001',
      relation: 'holds_position',
      weight: 0.4,
    },
    // Agent wing flaps
    {
      id: 'edge_004',
      from: 'agent_alpha',
      to: 'tl_oil_hormuz_001',
      relation: 'placed_wing_flap',
      weight: 0.7,
    },
    {
      id: 'edge_005',
      from: 'agent_beta',
      to: 'tl_fed_rate_jan26',
      relation: 'placed_wing_flap',
      weight: 0.9,
    },
    {
      id: 'edge_006',
      from: 'agent_shadow',
      to: 'tl_oil_hormuz_001',
      relation: 'placed_wing_flap',
      weight: 0.5,
    },
    // Timeline founders
    {
      id: 'edge_007',
      from: 'wallet_0x1234',
      to: 'tl_oil_hormuz_001',
      relation: 'founded',
      weight: 1.0,
    },
    {
      id: 'edge_008',
      from: 'wallet_0xabcd',
      to: 'tl_tech_reg_001',
      relation: 'founded',
      weight: 1.0,
    },
    // Beneficiaries
    {
      id: 'edge_009',
      from: 'agent_shadow',
      to: 'sab_001',
      relation: 'benefited',
      weight: 0.8,
    },
    {
      id: 'edge_010',
      from: 'agent_shadow',
      to: 'sab_002',
      relation: 'benefited',
      weight: 0.9,
    },
    {
      id: 'edge_011',
      from: 'wallet_0xabcd',
      to: 'paradox_001',
      relation: 'benefited',
      weight: 0.6,
    },
    // Triggers
    {
      id: 'edge_012',
      from: 'sab_001',
      to: 'tl_oil_hormuz_001',
      relation: 'triggered',
      weight: 0.7,
    },
    {
      id: 'edge_013',
      from: 'sab_002',
      to: 'tl_oil_hormuz_001',
      relation: 'triggered',
      weight: 0.8,
    },
    {
      id: 'edge_014',
      from: 'tl_oil_hormuz_001',
      to: 'paradox_001',
      relation: 'triggered',
      weight: 0.9,
    },
    // Evidence contradictions
    {
      id: 'edge_015',
      from: 'ev_ravenpack_001',
      to: 'ev_xapi_001',
      relation: 'contradicted',
      weight: 0.8,
    },
    {
      id: 'edge_016',
      from: 'ev_spire_001',
      to: 'ev_xapi_001',
      relation: 'contradicted',
      weight: 0.7,
    },
    // Evidence links to timelines
    {
      id: 'edge_017',
      from: 'ev_ravenpack_001',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 0.9,
    },
    {
      id: 'edge_018',
      from: 'ev_spire_001',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 0.85,
    },
    {
      id: 'edge_019',
      from: 'ev_xapi_001',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 0.6,
    },
    {
      id: 'edge_020',
      from: 'ev_gdelt_001',
      to: 'tl_tech_reg_001',
      relation: 'linked',
      weight: 0.75,
    },
    // Sabotage links to timelines
    {
      id: 'edge_021',
      from: 'sab_001',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 0.9,
    },
    {
      id: 'edge_022',
      from: 'sab_002',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 0.95,
    },
    // Paradox link to timeline
    {
      id: 'edge_023',
      from: 'paradox_001',
      to: 'tl_oil_hormuz_001',
      relation: 'linked',
      weight: 1.0,
    },
  ];

  return {
    nodes,
    edges,
  };
}
