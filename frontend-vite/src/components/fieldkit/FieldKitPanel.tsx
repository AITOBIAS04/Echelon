import { Briefcase, User, Activity, TrendingUp } from 'lucide-react';
import { useWingFlaps, useTimelines } from '../../hooks/useWingFlaps';

export function FieldKitPanel() {
  const { data: flapsData } = useWingFlaps({ limit: 50 });
  const { data: timelinesData } = useTimelines({ limit: 20 });
  
  const flaps = flapsData?.flaps || [];
  const timelines = timelinesData?.timelines || [];

  // Group flaps by agent
  const agentActivity = flaps.reduce((acc, flap) => {
    if (!acc[flap.agent_id]) {
      acc[flap.agent_id] = {
        id: flap.agent_id,
        name: flap.agent_name,
        archetype: flap.agent_archetype,
        flapCount: 0,
        totalVolume: 0,
        netStability: 0,
      };
    }
    acc[flap.agent_id].flapCount++;
    acc[flap.agent_id].totalVolume += flap.volume_usd;
    acc[flap.agent_id].netStability += flap.stability_delta;
    return acc;
  }, {} as Record<string, {
    id: string;
    name: string;
    archetype: string;
    flapCount: number;
    totalVolume: number;
    netStability: number;
  }>);

  const agents = Object.values(agentActivity).sort((a, b) => b.totalVolume - a.totalVolume);

  return (
    <div className="h-full flex flex-col p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 flex-shrink-0">
        <Briefcase className="w-6 h-6 text-echelon-cyan" />
        <h1 className="font-display text-2xl text-echelon-cyan uppercase tracking-wider">
          Field Kit
        </h1>
      </div>

      {/* Main Content - Full height, no overflow */}
      <div className="flex-1 min-h-0">
        <div className="h-full flex flex-col lg:flex-row gap-6 overflow-hidden">
          {/* Active Agents - scrollable */}
          <div className="flex-1 flex flex-col min-h-0">
            <h2 className="flex-shrink-0 mb-4 terminal-header flex items-center gap-2">
              <User className="w-4 h-4 text-echelon-cyan" />
              ACTIVE AGENTS
            </h2>
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              {agents.length === 0 ? (
                <div className="text-center text-terminal-muted py-8">
                  No agent activity detected
                </div>
              ) : (
                agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="terminal-panel p-4 hover:border-echelon-cyan/50 transition"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-terminal-border flex items-center justify-center">
                          <User className="w-5 h-5 text-echelon-cyan" />
                        </div>
                        <div>
                          <div className="font-medium text-terminal-text">{agent.name}</div>
                          <div className="text-xs text-terminal-muted">{agent.archetype}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-mono text-echelon-green">
                          ${agent.totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-xs text-terminal-muted">{agent.flapCount} actions</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        {agent.netStability > 0 ? (
                          <TrendingUp className="w-3 h-3 text-echelon-green" />
                        ) : (
                          <Activity className="w-3 h-3 text-echelon-red" />
                        )}
                        <span className={agent.netStability > 0 ? 'text-echelon-green' : 'text-echelon-red'}>
                          {agent.netStability > 0 ? '+' : ''}{agent.netStability.toFixed(1)}% stability
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right sidebar - scrollable sections */}
          <div className="w-full lg:w-80 flex flex-col gap-6 min-h-0">
            {/* Timeline Status - fixed height */}
            <div className="flex-shrink-0 terminal-panel p-4">
              <h3 className="terminal-header flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-echelon-cyan" />
                TIMELINE STATUS
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-terminal-muted mb-1">Active Timelines</div>
                  <div className="text-2xl font-mono text-echelon-green">{timelines.length}</div>
                </div>
                <div>
                  <div className="text-xs text-terminal-muted mb-1">With Paradoxes</div>
                  <div className="text-2xl font-mono text-echelon-red">
                    {timelines.filter(t => t.has_active_paradox).length}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-terminal-muted mb-1">Total Volume (24h)</div>
                  <div className="text-lg font-mono text-echelon-cyan">
                    ${timelines.reduce((sum, t) => sum + t.total_volume_usd, 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity - scrollable */}
            <div className="flex-1 flex flex-col min-h-0 terminal-panel p-4">
              <h3 className="flex-shrink-0 mb-3 terminal-header flex items-center gap-2">
                <Activity className="w-4 h-4 text-echelon-cyan" />
                RECENT ACTIVITY
              </h3>
              <div className="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {flaps.slice(0, 10).map((flap) => (
                  <div key={flap.id} className="text-xs">
                    <div className="text-terminal-text">{flap.agent_name}</div>
                    <div className="text-terminal-muted truncate">{flap.action}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

