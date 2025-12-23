import { useState, type ComponentType } from 'react';
import { Database, Radio, GitMerge, BarChart3, History } from 'lucide-react';
import { OsintFeed } from './OsintFeed';
import { CorrelationMatrix } from './CorrelationMatrix';
import { AgentPerformance } from './AgentPerformance';
import { HistoricalReplay } from './HistoricalReplay';
import { clsx } from 'clsx';

type TabId = 'osint' | 'correlations' | 'performance' | 'replay';

interface Tab {
  id: TabId;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

const tabs: Tab[] = [
  { id: 'osint', label: 'OSINT Feed', icon: Radio },
  { id: 'correlations', label: 'Correlations', icon: GitMerge },
  { id: 'performance', label: 'Agent Analytics', icon: BarChart3 },
  { id: 'replay', label: 'Historical Replay', icon: History },
];

export function Blackbox() {
  const [activeTab, setActiveTab] = useState<TabId>('osint');

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="w-6 h-6 text-echelon-purple" />
          <div>
            <h1 className="text-lg font-display text-echelon-purple tracking-wider">
              BLACKBOX
            </h1>
            <p className="text-xs text-terminal-muted">Deep Intelligence Analytics</p>
          </div>
        </div>
        <div className="text-xs text-terminal-muted">
          Classification: <span className="text-echelon-amber">SENSITIVE</span>
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
                  ? 'bg-terminal-panel text-echelon-purple border border-terminal-border border-b-0'
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
        {activeTab === 'osint' && <OsintFeed />}
        {activeTab === 'correlations' && <CorrelationMatrix />}
        {activeTab === 'performance' && <AgentPerformance />}
        {activeTab === 'replay' && <HistoricalReplay />}
      </div>
    </div>
  );
}

