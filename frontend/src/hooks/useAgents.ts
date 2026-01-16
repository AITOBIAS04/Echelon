// Placeholder hook for agents data
// TODO: Implement actual API integration
export function useAgents() {
  // Mock data for now
  const mockAgents = [
    { id: 'AGT_MEGALODON', name: 'MEGALODON', archetype: 'SHARK', total_pnl_usd: 4520, win_rate: 0.67, actions_count: 156, sanity: 78, max_sanity: 100 },
    { id: 'AGT_CARDINAL', name: 'CARDINAL', archetype: 'SPY', total_pnl_usd: 1230, win_rate: 0.58, actions_count: 89, sanity: 45, max_sanity: 100 },
    { id: 'AGT_ENVOY', name: 'ENVOY', archetype: 'DIPLOMAT', total_pnl_usd: 890, win_rate: 0.72, actions_count: 45, sanity: 92, max_sanity: 100 },
    { id: 'AGT_VIPER', name: 'VIPER', archetype: 'SABOTEUR', total_pnl_usd: -340, win_rate: 0.42, actions_count: 67, sanity: 18, max_sanity: 100 },
    { id: 'AGT_ORACLE', name: 'ORACLE', archetype: 'SPY', total_pnl_usd: 8900, win_rate: 0.71, actions_count: 112, sanity: 85, max_sanity: 100 },
    { id: 'AGT_LEVIATHAN', name: 'LEVIATHAN', archetype: 'WHALE', total_pnl_usd: 23400, win_rate: 0.65, actions_count: 203, sanity: 95, max_sanity: 100 },
  ];
  
  return { 
    data: { agents: mockAgents }, 
    isLoading: false 
  };
}

