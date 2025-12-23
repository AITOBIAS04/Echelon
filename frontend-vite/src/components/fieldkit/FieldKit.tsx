import { useState, type ComponentType } from 'react';
import { Briefcase, TrendingUp, Bot, GitBranch, Eye } from 'lucide-react';
import { MyPositions } from './MyPositions';
import { MyAgents } from './MyAgents';
import { PrivateForks } from './PrivateForks';
import { Watchlist } from './Watchlist';
import { clsx } from 'clsx';

type TabId = 'positions' | 'agents' | 'forks' | 'watchlist';

interface Tab {
  id: TabId;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

const tabs: Tab[] = [
  { id: 'positions', label: 'My Positions', icon: TrendingUp },
  { id: 'agents', label: 'My Agents', icon: Bot },
  { id: 'forks', label: 'Private Forks', icon: GitBranch },
  { id: 'watchlist', label: 'Watchlist', icon: Eye },
];

export function FieldKit() {
  const [activeTab, setActiveTab] = useState<TabId>('positions');

  // Mock P&L data - replace with real API
  const totalPnL = 12450.75;
  const totalPositions = 8;
  const totalAgents = 3;

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="terminal-panel p-4">
          <div className="flex items-center gap-2 mb-2">
            <Briefcase className="w-4 h-4 text-echelon-cyan" />
            <span className="terminal-header">Field Kit</span>
          </div>
          <p className="text-xs text-terminal-muted">Personal Operations Centre</p>
        </div>

        <div className="terminal-panel p-4">
          <div className="text-xs text-terminal-muted mb-1">Total P&L</div>
          <div
            className={clsx(
              'text-2xl font-mono font-bold',
              totalPnL >= 0 ? 'text-echelon-green' : 'text-echelon-red'
            )}
          >
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString()}
          </div>
        </div>

        <div className="terminal-panel p-4">
          <div className="text-xs text-terminal-muted mb-1">Active Positions</div>
          <div className="text-2xl font-mono font-bold text-terminal-text">
            {totalPositions}
          </div>
        </div>

        <div className="terminal-panel p-4">
          <div className="text-xs text-terminal-muted mb-1">Deployed Agents</div>
          <div className="text-2xl font-mono font-bold text-echelon-purple">
            {totalAgents}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-terminal-border pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-t transition-all',
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

      {/* Tab Content */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {activeTab === 'positions' && <MyPositions />}
        {activeTab === 'agents' && <MyAgents />}
        {activeTab === 'forks' && <PrivateForks />}
        {activeTab === 'watchlist' && <Watchlist />}
      </div>
    </div>
  );
}

