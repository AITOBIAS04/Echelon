import { useState, type ComponentType } from 'react';
import { Briefcase, TrendingUp, Bot, GitBranch, Eye, Zap, Database, Share2, Activity } from 'lucide-react';
import { MyPositions } from './MyPositions';
import { MyAgents } from './MyAgents';
import { GhostForks } from './GhostForks';
import { Watchlist } from './Watchlist';
import { FounderYield } from './FounderYield';
import { ExportConsole } from '../exports/ExportConsole';
import { EntityGraphView } from '../graph/EntityGraphView';
import { OverviewTab } from './OverviewTab';
import { clsx } from 'clsx';

type TabId = 'overview' | 'positions' | 'agents' | 'forks' | 'watchlist' | 'yield' | 'exports' | 'graph';

interface Tab {
  id: TabId;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

const tabs: Tab[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'yield', label: "Founder's Yield", icon: Zap },
  { id: 'positions', label: 'My Positions', icon: TrendingUp },
  { id: 'agents', label: 'My Agents', icon: Bot },
  { id: 'forks', label: 'Private Forks', icon: GitBranch },
  { id: 'watchlist', label: 'Watchlist', icon: Eye },
  { id: 'graph', label: 'Graph', icon: Share2 },
  { id: 'exports', label: 'Exports', icon: Database },
];

export function FieldKit() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  // Mock P&L data - replace with real API
  const totalPnL = 12450.75;
  const totalPositions = 8;
  const totalAgents = 3;

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
        <div className="terminal-panel p-3 sm:p-4">
          <div className="flex items-center gap-2 mb-2">
            <Briefcase className="w-4 h-4 text-echelon-cyan" />
            <span className="terminal-header">Field Kit</span>
          </div>
          <p className="text-xs text-terminal-muted">Personal Operations Centre</p>
        </div>

        <div className="terminal-panel p-3 sm:p-4">
          <div className="text-xs text-terminal-muted mb-1">Total P&L</div>
          <div
            className={clsx(
              'text-xl sm:text-2xl font-mono font-bold leading-tight truncate',
              totalPnL >= 0 ? 'text-echelon-green' : 'text-echelon-red'
            )}
            title={`${totalPnL >= 0 ? '+' : ''}$${totalPnL.toLocaleString()}`}
          >
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString()}
          </div>
        </div>

        <div className="terminal-panel p-3 sm:p-4">
          <div className="text-xs text-terminal-muted mb-1">Active Positions</div>
          <div className="text-2xl font-mono font-bold text-terminal-text">
            {totalPositions}
          </div>
        </div>

        <div className="terminal-panel p-3 sm:p-4">
          <div className="text-xs text-terminal-muted mb-1">Deployed Agents</div>
          <div className="text-2xl font-mono font-bold text-echelon-purple">
            {totalAgents}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-terminal-border pb-2 overflow-x-auto scrollbar-hide">
        <div className="flex gap-1 min-w-max">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex items-center gap-2 px-3 sm:px-4 py-2 rounded-t transition-all whitespace-nowrap flex-shrink-0',
                  activeTab === tab.id
                    ? 'bg-terminal-panel text-echelon-cyan border border-terminal-border border-b-0'
                    : 'text-terminal-muted hover:text-terminal-text'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'yield' && <FounderYield />}
        {activeTab === 'positions' && <MyPositions />}
        {activeTab === 'agents' && <MyAgents />}
        {activeTab === 'forks' && <GhostForks />}
        {activeTab === 'watchlist' && <Watchlist />}
        {activeTab === 'graph' && <EntityGraphView />}
        {activeTab === 'exports' && <ExportConsole />}
      </div>
    </div>
  );
}

