// Agents Page Component
// Agent Roster and Global Intelligence Dashboard

import { useState } from 'react';
import { useAgentRoster, useArchetypeDistribution, usePerformanceStats, useSanityDistribution, useDashboardStats, useTheatres, useMovements, useStrategyClusters, useConflicts, useAgentsStatus } from '../hooks/useAgents';
import type { AgentView } from '../types/agents';

export function AgentsPage() {
  const [activeView, setActiveView] = useState<AgentView>('roster');
  const { agents } = useAgentRoster();
  const archetypeCounts = useArchetypeDistribution();
  const performanceStats = usePerformanceStats();
  const sanityDistribution = useSanityDistribution();
  const dashboardStats = useDashboardStats();
  const theatres = useTheatres();
  const movements = useMovements();
  const clusters = useStrategyClusters();
  const conflicts = useConflicts();
  const { clock } = useAgentsStatus();

  const formatPL = (value: number): string => {
    return value >= 0 ? `+$${value.toLocaleString()}` : `-$${Math.abs(value).toLocaleString()}`;
  };

  const getMovementIcon = (action: string): string => {
    switch (action) {
      case 'deploy': return 'ri-arrow-right-up-line';
      case 'withdraw': return 'ri-arrow-right-down-line';
      case 'strategy': return 'ri-exchange-line';
      default: return 'ri-exchange-line';
    }
  };

  const getMovementIconClass = (action: string): string => {
    switch (action) {
      case 'deploy': return 'deploy';
      case 'withdraw': return 'withdraw';
      case 'strategy': return 'strategy';
      default: return '';
    }
  };

  const getClusterStyle = (style: string): string => {
    return style === 'aggressive' ? 'rgba(239, 68, 68, 0.15)' : style === 'moderate' ? 'rgba(250, 204, 21, 0.1)' : 'rgba(74, 222, 128, 0.1)';
  };

  const getClusterBorder = (style: string): string => {
    return style === 'aggressive' ? 'rgba(239, 68, 68, 0.3)' : style === 'moderate' ? 'rgba(250, 204, 21, 0.2)' : 'rgba(74, 222, 128, 0.2)';
  };

  const formatTime = (date: Date): string => {
    return date.toISOString().substr(11, 8);
  };

  return (
    <div className="app-layout" style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-app)' }}>
      <style>{`
        :root {
          --slate-950: #0B0C0E;
          --slate-900: #121417;
          --slate-850: #151719;
          --slate-800: #1A1D21;
          --slate-750: #26292E;
          --slate-700: #363A40;
          
          --bg-app: var(--slate-950);
          --bg-panel: var(--slate-850);
          --bg-card: var(--slate-900);
          --bg-card-hover: var(--slate-800);
          --border-outer: var(--slate-750);
          --border-inner: rgba(54, 58, 64, 0.5);
          
          --text-primary: #F1F5F9;
          --text-secondary: #94A3B8;
          --text-muted: #64748B;
          --font-sans: 'Inter', system-ui, sans-serif;
          --font-mono: 'JetBrains Mono', monospace;
          
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 12px;
          --space-lg: 16px;
          --space-xl: 24px;
          --space-2xl: 32px;
          --radius-sm: 6px;
          --radius-md: 8px;
          --radius-lg: 12px;
          
          --status-success: #4ADE80;
          --status-success-bg: rgba(74, 222, 128, 0.1);
          --status-success-border: rgba(74, 222, 128, 0.2);
          
          --status-warning: #FACC15;
          --status-warning-bg: rgba(250, 204, 21, 0.1);
          --status-warning-border: rgba(250, 204, 21, 0.2);
          
          --status-danger: #FB7185;
          --status-danger-bg: rgba(251, 113, 133, 0.1);
          --status-danger-border: rgba(251, 113, 133, 0.2);
          
          --status-info: #3B82F6;
          --status-info-bg: rgba(59, 130, 246, 0.1);
          
          --status-paradox: #8B5CF6;
          --status-paradox-bg: rgba(139, 92, 246, 0.1);
          
          --echelon-cyan: #22D3EE;
          --echelon-cyan-bg: rgba(34, 211, 238, 0.1);
          --echelon-cyan-border: rgba(34, 211, 238, 0.3);
          
          --echelon-purple: #A855F7;
          --echelon-purple-bg: rgba(168, 85, 247, 0.1);
          --echelon-purple-border: rgba(168, 85, 247, 0.3);
          
          --echelon-amber: #F59E0B;
          --echelon-amber-bg: rgba(245, 158, 11, 0.1);
          --echelon-amber-border: rgba(245, 158, 11, 0.3);
          
          --echelon-red: #EF4444;
          --echelon-red-bg: rgba(239, 68, 68, 0.1);
          --echelon-red-border: rgba(239, 68, 68, 0.3);
        }
        
        .sidebar {
          width: 220px;
          background: var(--bg-panel);
          border-right: 1px solid var(--border-outer);
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
          padding: var(--space-md);
        }
        
        .sidebar-search {
          margin-bottom: var(--space-lg);
        }
        
        .sidebar-nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: var(--space-xs);
        }
        
        .sidebar-nav-item:hover {
          background: var(--bg-card-hover);
          color: var(--text-primary);
        }
        
        .sidebar-nav-item.active {
          background: var(--echelon-cyan-bg);
          color: var(--echelon-cyan);
        }
        
        .sidebar-nav-item i {
          font-size: 16px;
          width: 20px;
          text-align: center;
        }
        
        .sidebar-divider {
          height: 1px;
          background: var(--border-outer);
          margin: var(--space-md) 0;
        }
        
        .sanity-bar.stable { background: var(--status-success); }
        .sanity-bar.stressed { background: var(--echelon-amber); }
        .sanity-bar.critical { background: var(--status-danger); animation: pulse 1s infinite; }
        .sanity-bar.breakdown { background: var(--status-danger); animation: pulse 0.5s infinite; }
        .sanity-status.stable { color: var(--status-success); }
        .sanity-status.stressed { color: var(--echelon-amber); }
        .sanity-status.critical { color: var(--status-danger); animation: pulse 1s infinite; }
        .sanity-status.breakdown { color: var(--status-danger); animation: pulse 0.5s infinite; }
        .sanity-current.stable { color: var(--status-success); }
        .sanity-current.stressed { color: var(--echelon-amber); }
        .sanity-current.critical { color: var(--status-danger); }
        .sanity-current.breakdown { color: var(--status-danger); }
      `}</style>

      {/* Left Sidebar */}
      <aside className="sidebar">
        {/* Search */}
        <div className="sidebar-search">
          <button 
            className="header-btn" 
            style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 6, color: 'var(--text-secondary)', fontSize: 12, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}
          >
            <i className="ri-search-line" style={{ fontSize: 14 }}></i>
            Search
          </button>
        </div>
        
        {/* Navigation Items */}
        <div className="sidebar-nav">
          <div 
            className={`sidebar-nav-item ${activeView === 'roster' ? 'active' : ''}`}
            onClick={() => setActiveView('roster')}
          >
            <i className="ri-robot-line"></i>
            Agent Roster
          </div>
          <div 
            className={`sidebar-nav-item ${activeView === 'intelligence' ? 'active' : ''}`}
            onClick={() => setActiveView('intelligence')}
          >
            <i className="ri-global-line"></i>
            Global Intelligence
          </div>
          
          <div className="sidebar-divider"></div>
          
          <div className="sidebar-nav-item">
            <i className="ri-add-line"></i>
            Deploy Agent
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Header */}
        <header className="header" style={{ height: 64, background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-outer)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', flexShrink: 0 }}>
          <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <div className="page-title" style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
              {activeView === 'roster' ? 'Agent Roster' : 'Global Intelligence'}
            </div>
          </div>
          <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span className="clock mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{clock}</span>
          </div>
        </header>

        {/* Content Area */}
        <div className="content-area" style={{ flex: 1, padding: 16, overflow: 'auto' }}>

          {/* ==================== AGENT ROSTER VIEW ==================== */}
          {activeView === 'roster' && (
            <div className="content-layout" style={{ display: 'flex', alignItems: 'flex-start' }}>
              {/* Main Panel - Agent Grid */}
              <div className="main-panel" style={{ flex: 1, minWidth: 0 }}>
                <div className="agents-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12 }}>
                  {agents.map((agent) => (
                    <div
                      key={agent.id}
                      className={`agent-card ${agent.sanityLevel === 'stressed' ? 'stressed' : ''} ${agent.sanityLevel === 'critical' || agent.sanityLevel === 'breakdown' ? 'critical' : ''}`}
                      style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12, transition: 'all 0.2s', cursor: 'pointer', animation: agent.sanityLevel === 'critical' || agent.sanityLevel === 'breakdown' ? 'criticalPulse 2s infinite' : 'none' }}
                    >
                      <div className="agent-card-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
                        <div className="agent-info" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <span className="agent-emoji" style={{ fontSize: 28 }}>{agent.emoji}</span>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span className="agent-name" style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{agent.name}</span>
                            </div>
                            <span className="agent-archetype" style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{agent.archetype}</span>
                          </div>
                        </div>
                        <span className={`agent-pnl mono ${agent.pnl >= 0 ? 'positive' : 'negative'}`} style={{ fontSize: 18, fontWeight: 700, color: agent.pnl >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{agent.pnl >= 0 ? '+' : ''}{formatPL(agent.pnl)}</span>
                      </div>

                      <div className="genealogy" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontSize: 11 }}>
                        <span className="gen-badge" style={{ padding: '2px 8px', background: 'var(--echelon-purple-bg)', border: '1px solid var(--echelon-purple-border)', borderRadius: 3, fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, color: 'var(--echelon-purple)' }}>GEN {agent.generation}</span>
                        <span style={{ color: 'var(--text-muted)' }}>•</span>
                        <span style={{ color: 'var(--text-muted)' }}>
                          LINEAGE: <span style={{ color: agent.isGenesis ? 'var(--echelon-cyan)' : 'var(--echelon-purple)' }}>{agent.isGenesis ? 'GENESIS AGENT' : agent.parents}</span>
                        </span>
                      </div>

                      <div className="agent-stats" style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
                        <span className="agent-stat" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <i className="ri-flashlight-line" style={{ fontSize: 12 }}></i>
                          {agent.actions.toLocaleString()} actions
                        </span>
                        <span className="agent-stat" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <i className="ri-trending-up-line" style={{ fontSize: 12 }}></i>
                          {agent.winRate}% win rate
                        </span>
                      </div>

                      <div className="sanity-section" style={{ marginBottom: 12 }}>
                        <div className="sanity-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span className="sanity-label" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            <i className="ri-brain-line" style={{ fontSize: 12 }}></i> SANITY
                          </span>
                          <span className={`sanity-status ${agent.sanityLevel}`} style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{agent.sanityStatus}</span>
                        </div>
                        <div className="sanity-bar-container" style={{ height: 6, background: 'var(--bg-app)', borderRadius: 3, overflow: 'hidden' }}>
                          <div className={`sanity-bar ${agent.sanityLevel}`} style={{ height: '100%', width: `${agent.sanity}%`, borderRadius: 3, transition: 'width 0.5s ease' }}></div>
                        </div>
                        <div className="sanity-values" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                          <span className={`sanity-current ${agent.sanityLevel}`} style={{ fontWeight: 600 }}>{agent.sanity}/100</span>
                        </div>
                      </div>

                      {agent.sanityLevel === 'stressed' && (
                        <div className="critical-banner stressed" style={{ marginTop: 8, padding: 8, borderRadius: 6, fontSize: 10, background: 'var(--echelon-amber-bg)', border: '1px solid var(--echelon-amber-border)', color: 'var(--echelon-amber)' }}>
                          ⚠️ {agent.name} is under stress. Consider rest or support missions.
                        </div>
                      )}

                      {agent.sanityLevel === 'critical' && (
                        <>
                          <div className="sanity-warning" style={{ fontSize: 10, color: 'var(--status-danger)', display: 'flex', alignItems: 'center', gap: 4, marginTop: 4, animation: 'pulse 1s infinite' }}>
                            <i className="ri-error-warning-fill" style={{ fontSize: 10 }}></i>
                            BREAKDOWN RISK
                          </div>
                          <div className="critical-banner critical" style={{ marginTop: 8, padding: 8, borderRadius: 6, fontSize: 10, background: 'var(--echelon-red-bg)', border: '1px solid var(--echelon-red-border)', color: 'var(--status-danger)' }}>
                            ⚠️ {agent.name} is near psychological breakdown. High-risk missions may cause permanent damage.
                          </div>
                        </>
                      )}

                      <div className="agent-actions" style={{ display: 'flex', gap: 8, paddingTop: 12, borderTop: '1px solid var(--border-outer)', marginTop: 12 }}>
                        {agent.sanityLevel === 'critical' ? (
                          <button className="action-btn task" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '8px 12px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', background: 'var(--status-info-bg)', border: '1px solid var(--status-info-border)', color: 'var(--status-info)' }}>
                            <i className="ri-search-line" style={{ fontSize: 14 }}></i>
                            TASK
                          </button>
                        ) : null}
                        <button className="action-btn copy" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '8px 12px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', background: 'var(--echelon-cyan-bg)', border: '1px solid var(--echelon-cyan-border)', color: 'var(--echelon-cyan)' }}>
                          <i className="ri-file-copy-line" style={{ fontSize: 14 }}></i>
                          COPY
                        </button>
                        <button className="action-btn hire" style={{ padding: 8, borderRadius: 6, background: 'var(--echelon-amber-bg)', border: '1px solid var(--echelon-amber-border)', color: 'var(--echelon-amber)', cursor: 'pointer', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <i className="ri-briefcase-line" style={{ fontSize: 14 }}></i>
                        </button>
                      </div>
                    </div>
                  ))}
</div>
              </div>

              {/* Right Sidebar */}
              <aside className="right-sidebar" style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12, marginLeft: 16 }}>
                {/* Archetype Distribution */}
                <div className="widget" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                  <div className="widget-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border-outer)' }}>
                    <span className="widget-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Archetype Distribution</span>
                  </div>
                  <div className="widget-body" style={{ padding: 12 }}>
                    {archetypeCounts.map((item, i) => (
                      <div key={i} className="archetype-item" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0', borderBottom: i < archetypeCounts.length - 1 ? '1px solid var(--border-outer)' : 'none' }}>
                        <span className="archetype-emoji" style={{ fontSize: 20 }}>{item.emoji}</span>
                        <span className="archetype-name" style={{ flex: 1, fontSize: 12, color: 'var(--text-primary)' }}>{item.archetype}</span>
                        <span className="archetype-count mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Performance Summary */}
                <div className="widget" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                  <div className="widget-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border-outer)' }}>
                    <span className="widget-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Performance Summary</span>
                  </div>
                  <div className="widget-body" style={{ padding: 12 }}>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total P/L</span>
                      <span className="perf-value positive mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-success)' }}>+${performanceStats.totalPL.toLocaleString()}</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>Win Rate</span>
                      <span className="perf-value mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{performanceStats.winRate}%</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total Actions</span>
                      <span className="perf-value mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{performanceStats.totalActions.toLocaleString()}</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>Avg Sanity</span>
                      <span className="perf-value mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{performanceStats.avgSanity}/100</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>Genesis Agents</span>
                      <span className="perf-value mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{performanceStats.genesisAgents}</span>
                    </div>
                  </div>
                </div>

                {/* Sanity Distribution */}
                <div className="widget" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8 }}>
                  <div className="widget-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border-outer)' }}>
                    <span className="widget-title" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sanity Distribution</span>
                  </div>
                  <div className="widget-body" style={{ padding: 12 }}>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>STABLE (70-100)</span>
                      <span className="perf-value" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{sanityDistribution.stable} agents</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>STRESSED (40-69)</span>
                      <span className="perf-value text-amber" style={{ fontSize: 12, fontWeight: 600, color: 'var(--echelon-amber)' }}>{sanityDistribution.stressed} agents</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-outer)' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>CRITICAL (20-39)</span>
                      <span className="perf-value text-red" style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-danger)' }}>{sanityDistribution.critical} agent</span>
                    </div>
                    <div className="perf-stat" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                      <span className="perf-label" style={{ fontSize: 12, color: 'var(--text-muted)' }}>BREAKDOWN {'(<20)'}</span>
                      <span className="perf-value text-red" style={{ fontSize: 12, fontWeight: 600, color: 'var(--status-danger)' }}>{sanityDistribution.breakdown} agent</span>
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          )}

          {/* ==================== GLOBAL INTELLIGENCE VIEW ==================== */}
          {activeView === 'intelligence' && (
            <div>
              {/* Stats Row */}
              <div className="stats-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 16 }}>
                <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                  <div className="stat-card-icon total" style={{ width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, background: 'var(--status-info-bg)', color: 'var(--status-info)', marginBottom: 8 }}>
                    <i className="ri-robot-line"></i>
                  </div>
                  <div className="stat-card-value mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{dashboardStats.totalAgents}</div>
                  <div className="stat-card-label" style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total Agents</div>
                  <div className="stat-card-change up" style={{ fontSize: 10, marginTop: 4, color: 'var(--status-success)' }}>+2 this week</div>
                </div>
                <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                  <div className="stat-card-icon deployed" style={{ width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, background: 'var(--status-success-bg)', color: 'var(--status-success)', marginBottom: 8 }}>
                    <i className="ri-checkbox-circle-line"></i>
                  </div>
                  <div className="stat-card-value mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{dashboardStats.deployedAgents}</div>
                  <div className="stat-card-label" style={{ fontSize: 11, color: 'var(--text-muted)' }}>Deployed</div>
                  <div className="stat-card-change" style={{ fontSize: 10, marginTop: 4, color: 'var(--text-muted)' }}>67% utilization</div>
                </div>
                <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                  <div className="stat-card-icon movements" style={{ width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, background: 'var(--status-warning-bg)', color: 'var(--status-warning)', marginBottom: 8 }}>
                    <i className="ri-exchange-line"></i>
                  </div>
                  <div className="stat-card-value mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{dashboardStats.movements24h}</div>
                  <div className="stat-card-label" style={{ fontSize: 11, color: 'var(--text-muted)' }}>Movements (24h)</div>
                  <div className="stat-card-change up" style={{ fontSize: 10, marginTop: 4, color: 'var(--status-success)' }}>+12 from yesterday</div>
                </div>
                <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, padding: 12 }}>
                  <div className="stat-card-icon conflicts" style={{ width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, background: 'var(--status-danger-bg)', color: 'var(--status-danger)', marginBottom: 8 }}>
                    <i className="ri-sword-line"></i>
                  </div>
                  <div className="stat-card-value mono" style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>{dashboardStats.activeConflicts}</div>
                  <div className="stat-card-label" style={{ fontSize: 11, color: 'var(--text-muted)' }}>Active Conflicts</div>
                  <div className="stat-card-change down" style={{ fontSize: 10, marginTop: 4, color: 'var(--status-success)' }}>-1 from yesterday</div>
                </div>
              </div>

              {/* Dashboard Grid */}
              <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
                
                {/* Agent Deployment Heat Map */}
                <div className="dashboard-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, overflow: 'hidden' }}>
                  <div className="dashboard-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, borderBottom: '1px solid var(--border-outer)' }}>
                    <div className="dashboard-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      <i className="ri-radar-line" style={{ fontSize: 16, color: 'var(--echelon-cyan)' }}></i>
                      Theatre Heat Map
                    </div>
                    <div className="activity-indicator" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--status-success)' }}>
                      <span className="activity-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-success)', animation: 'pulse 1.5s infinite' }}></span>
                      LIVE
                    </div>
                  </div>
                  <div className="dashboard-card-body" style={{ padding: 12 }}>
                    <div className="theatre-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                      {theatres.map((theatre) => (
                        <div
                          key={theatre.id}
                          className={`theatre-cell ${theatre.activityLevel}`}
                          style={{ padding: 12, borderRadius: 6, cursor: 'pointer', transition: 'all 0.2s', background: theatre.activityLevel === 'high' ? 'rgba(239, 68, 68, 0.15)' : theatre.activityLevel === 'medium' ? 'rgba(250, 204, 21, 0.1)' : 'rgba(74, 222, 128, 0.1)', border: `1px solid ${theatre.activityLevel === 'high' ? 'rgba(239, 68, 68, 0.3)' : theatre.activityLevel === 'medium' ? 'rgba(250, 204, 21, 0.2)' : 'rgba(74, 222, 128, 0.2)'}` }}
                        >
                          <div className="theatre-name" style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{theatre.name}</div>
                          <div className="theatre-meta" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10 }}>
                            <span className="theatre-agents" style={{ color: 'var(--text-secondary)' }}>{theatre.agents} agents</span>
                            <span className="theatre-activity mono" style={{ fontWeight: 600, color: theatre.activityLevel === 'high' ? 'var(--status-danger)' : theatre.activityLevel === 'medium' ? 'var(--status-warning)' : 'var(--status-success)' }}>{theatre.activity}%</span>
                          </div>
                          <div className="theatre-metrics" style={{ display: 'flex', gap: 8, marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border-outer)' }}>
                            <div className="metric-item" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                              <span className="metric-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>VOL</span>
                              <span className="metric-value mono" style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)' }}>${(theatre.volume / 1000000).toFixed(1)}M</span>
                            </div>
                            <div className="metric-item" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                              <span className="metric-label" style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>INST</span>
                              <span className="metric-value mono" style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-secondary)' }}>{theatre.instability}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Movement Feed */}
                <div className="dashboard-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, overflow: 'hidden' }}>
                  <div className="dashboard-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, borderBottom: '1px solid var(--border-outer)' }}>
                    <div className="dashboard-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      <i className="ri-flight-takeoff-line" style={{ fontSize: 16, color: 'var(--echelon-cyan)' }}></i>
                      Movement Feed
                    </div>
                  </div>
                  <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-outer)', display: 'flex', gap: 4 }}>
                    <button className="filter-btn active" style={{ padding: '4px 8px', borderRadius: 4, fontSize: 10, fontWeight: 500, color: 'var(--echelon-cyan)', background: 'var(--echelon-cyan-bg)', border: 'none', cursor: 'pointer' }}>ALL</button>
                    <button className="filter-btn" style={{ padding: '4px 8px', borderRadius: 4, fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', background: 'transparent', border: 'none', cursor: 'pointer' }}>DEPLOY</button>
                    <button className="filter-btn" style={{ padding: '4px 8px', borderRadius: 4, fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', background: 'transparent', border: 'none', cursor: 'pointer' }}>WITHDRAW</button>
                  </div>
                  <div className="movement-feed" style={{ maxHeight: 280, overflowY: 'auto', padding: 12 }}>
                    {movements.map((movement) => (
                      <div key={movement.id} className="movement-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--border-outer)', fontSize: 11 }}>
                        <span className="movement-time mono" style={{ fontSize: 10, color: 'var(--text-muted)', minWidth: 70 }}>{formatTime(movement.timestamp)}</span>
                        <div className={`movement-icon ${getMovementIconClass(movement.action)}`} style={{ width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, background: movement.action === 'deploy' ? 'var(--status-success-bg)' : movement.action === 'withdraw' ? 'var(--status-danger-bg)' : 'var(--status-info-bg)', color: movement.action === 'deploy' ? 'var(--status-success)' : movement.action === 'withdraw' ? 'var(--status-danger)' : 'var(--status-info)' }}>
                          <i className={getMovementIcon(movement.action)}></i>
                        </div>
                        <div className="movement-content" style={{ flex: 1 }}>
                          <span className="movement-agent" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{movement.agent}</span>
                          <span className="movement-action" style={{ color: 'var(--text-secondary)' }}> {movement.action === 'deploy' ? 'deployed to' : movement.action === 'withdraw' ? 'withdrawn from' : 'changed strategy at'} </span>
                          <span className="movement-theatre" style={{ color: 'var(--echelon-cyan)' }}>{movement.theatre}</span>
                        </div>
                        <span className={`movement-velocity ${movement.velocityType}`} style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 3, marginLeft: 'auto', background: movement.velocityType === 'positive' ? 'var(--status-success-bg)' : movement.velocityType === 'negative' ? 'var(--status-danger-bg)' : 'var(--bg-app)', color: movement.velocityType === 'positive' ? 'var(--status-success)' : movement.velocityType === 'negative' ? 'var(--status-danger)' : 'var(--text-muted)' }}>
                          {movement.velocity >= 0 ? '+' : ''}{movement.velocity}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Strategy Clusters */}
                <div className="dashboard-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, overflow: 'hidden' }}>
                  <div className="dashboard-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, borderBottom: '1px solid var(--border-outer)' }}>
                    <div className="dashboard-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      <i className="ri-group-line" style={{ fontSize: 16, color: 'var(--echelon-cyan)' }}></i>
                      Strategy Clusters
                    </div>
                  </div>
                  <div className="dashboard-card-body" style={{ padding: 12 }}>
                    {clusters.map((cluster, i) => (
                      <div
                        key={i}
                        className="cluster-card"
                        style={{ padding: 12, borderRadius: 6, marginBottom: i < clusters.length - 1 ? 12 : 0, background: getClusterStyle(cluster.style), border: `1px solid ${getClusterBorder(cluster.style)}` }}
                      >
                        <div className="cluster-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <div className="cluster-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                            <span>{cluster.emoji}</span>
                            {cluster.archetype}
                          </div>
                          <span className="cluster-count" style={{ fontSize: 10, padding: '2px 6px', borderRadius: 3, background: 'var(--bg-app)', color: 'var(--text-muted)' }}>{cluster.count} agents</span>
                        </div>
                        <div className="cluster-stats" style={{ display: 'flex', gap: 16, fontSize: 10 }}>
                          <div className="cluster-stat">
                            <span className="cluster-stat-label" style={{ color: 'var(--text-muted)' }}>Total P/L</span>
                            <span className="cluster-stat-value mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>+${(cluster.totalPL / 1000).toFixed(0)}K</span>
                          </div>
                          <div className="cluster-stat">
                            <span className="cluster-stat-label" style={{ color: 'var(--text-muted)' }}>Avg Win</span>
                            <span className="cluster-stat-value mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{cluster.avgWinRate}%</span>
                          </div>
                          <div className="cluster-stat">
                            <span className="cluster-stat-label" style={{ color: 'var(--text-muted)' }}>Style</span>
                            <span className="cluster-stat-value mono" style={{ fontWeight: 600, color: cluster.style === 'aggressive' ? 'var(--status-danger)' : cluster.style === 'moderate' ? 'var(--status-warning)' : 'var(--status-success)', textTransform: 'capitalize' }}>{cluster.style}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Conflict Matrix - Full Width */}
                <div className="dashboard-card full-width" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-outer)', borderRadius: 8, overflow: 'hidden', gridColumn: 'span 3' }}>
                  <div className="dashboard-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, borderBottom: '1px solid var(--border-outer)' }}>
                    <div className="dashboard-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      <i className="ri-sword-line" style={{ fontSize: 16, color: 'var(--echelon-cyan)' }}></i>
                      Agent Conflicts & Interactions
                    </div>
                  </div>
                  <div className="dashboard-card-body" style={{ padding: 12 }}>
                    <div className="conflict-list" style={{ maxHeight: 200, overflowY: 'auto' }}>
                      {conflicts.map((conflict) => (
                        <div
                          key={conflict.id}
                          className={`conflict-item ${conflict.severity}`}
                          style={{ padding: 12, borderRadius: 6, marginBottom: 8, background: conflict.severity === 'high-impact' ? 'rgba(239, 68, 68, 0.15)' : conflict.severity === 'medium-impact' ? 'rgba(250, 204, 21, 0.1)' : 'rgba(74, 222, 128, 0.1)', border: `1px solid ${conflict.severity === 'high-impact' ? 'rgba(239, 68, 68, 0.3)' : conflict.severity === 'medium-impact' ? 'rgba(250, 204, 21, 0.2)' : 'rgba(74, 222, 128, 0.2)'}` }}
                        >
                          <div className="conflict-severity" style={{ fontSize: 9, fontWeight: 600, marginBottom: 6, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{conflict.severity.replace('-', ' ')}</div>
                          <div className="conflict-agents" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                            <div className="conflict-pair" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 600 }}>
                              {conflict.agent1}
                              <span className="conflict-vs" style={{ color: 'var(--text-muted)', fontWeight: 400 }}>vs</span>
                              {conflict.agent2}
                            </div>
                            <span className="conflict-theatre" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{conflict.theatre}</span>
                          </div>
                          <div className="conflict-details" style={{ fontSize: 10, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <span>{conflict.details}</span>
                            <span className={`conflict-impact mono ${conflict.impact >= 0 ? 'positive' : 'negative'}`} style={{ fontWeight: 600, color: conflict.impact >= 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>
                              {conflict.impact >= 0 ? '+' : ''}${Math.abs(conflict.impact).toLocaleString()} impact
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* CSS Animations */}
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        @keyframes criticalPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
          50% { box-shadow: 0 0 20px 0 rgba(239, 68, 68, 0.3); }
        }
        .header-btn:hover {
          border-color: var(--echelon-cyan) !important;
          color: var(--echelon-cyan) !important;
        }
        .sidebar-nav-item:hover {
          background: var(--bg-card-hover) !important;
          color: var(--text-primary) !important;
        }
        .sidebar-nav-item.active {
          background: var(--echelon-cyan-bg) !important;
          color: var(--echelon-cyan) !important;
        }
        .agent-card:hover {
          border-color: var(--echelon-cyan-border) !important;
          transform: translateY(-2px);
        }
        .theatre-cell:hover {
          transform: scale(1.02);
        }
        .filter-btn:hover {
          color: var(--text-secondary) !important;
          background: var(--bg-app) !important;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-app); }
        ::-webkit-scrollbar-thumb { background: var(--border-outer); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--slate-700); }
      `}</style>
    </div>
  );
}
