import { useState, useEffect } from 'react';
import { Radio, Activity, Shield, Target, Eye, Layers } from 'lucide-react';
import { WhaleWatch } from './WhaleWatch';
import { TimelineHealthPanel } from './TimelineHealthPanel';
import { WarChest } from './WarChest';
import { GravityField } from './GravityField';
import { TaskForce } from './TaskForce';
import { TheatreLibrary } from './TheatreLibrary';
import { LiveTape } from './LiveTape';
import { LiveRibbon } from './LiveRibbon';
import { PositionsPanel } from './PositionsPanel';
import { clsx } from 'clsx';

type TabType = 'intercepts' | 'health' | 'warchest' | 'gravity' | 'taskforce' | 'theatres' | 'live_tape';

export function Blackbox() {
  // Check URL params for tab, default to 'intercepts'
  const urlParams = new URLSearchParams(window.location.search);
  const initialTab = (urlParams.get('tab') as TabType) || 'intercepts';
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);

  const tabs = [
    { id: 'intercepts' as TabType, label: 'Intercepts', icon: Radio },
    { id: 'live_tape' as TabType, label: 'Live Tape', icon: Radio, deEmphasized: true },
    { id: 'health' as TabType, label: 'Timeline Health', icon: Activity },
    { id: 'warchest' as TabType, label: 'War Chest', icon: Shield },
    { id: 'gravity' as TabType, label: 'Gravity Field', icon: Target },
    { id: 'taskforce' as TabType, label: 'Task Force', icon: Eye },
    { id: 'theatres' as TabType, label: 'Theatres', icon: Layers },
  ];

  // Sync tab with URL params on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab') as TabType;
    if (tabParam) {
      const validTabs: TabType[] = ['intercepts', 'live_tape', 'health', 'warchest', 'gravity', 'taskforce', 'theatres'];
      if (validTabs.includes(tabParam)) {
        setActiveTab(tabParam);
      }
    }
  }, []);

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-950">
      {/* Your Positions Panel */}
      <div className="flex-shrink-0 p-4 pb-0">
        <PositionsPanel />
      </div>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-h-0 m-4 mt-3 bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
        {/* Live Ribbon - directly beneath header */}
        <LiveRibbon />

        {/* Tabs */}
        <div className="flex-shrink-0 px-2 sm:px-4 py-3 border-b border-terminal-border overflow-x-auto scrollbar-hide">
          <div className="flex items-center gap-4 sm:gap-8 min-w-max">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isDeEmphasized = (tab as any).deEmphasized;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  // Update URL without navigation
                  const url = new URL(window.location.href);
                  url.searchParams.set('tab', tab.id);
                  window.history.pushState({}, '', url.toString());
                }}
                className={clsx(
                  'flex items-center gap-2 pb-2 uppercase tracking-wider text-sm transition-all whitespace-nowrap flex-shrink-0',
                  activeTab === tab.id
                    ? 'text-status-info border-b-2 border-status-info'
                    : isDeEmphasized
                    ? 'text-terminal-text-muted hover:text-terminal-text-secondary opacity-60'
                    : 'text-terminal-text-secondary hover:text-status-info'
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 min-h-0 overflow-y-auto p-4 scrollbar-thin">
          {activeTab === 'intercepts' && <WhaleWatch />}
          {activeTab === 'live_tape' && <LiveTape />}
          {activeTab === 'health' && <TimelineHealthPanel />}
          {activeTab === 'warchest' && <WarChest />}
          {activeTab === 'gravity' && <GravityField />}
          {activeTab === 'taskforce' && <TaskForce />}
          {activeTab === 'theatres' && <TheatreLibrary />}
        </div>
      </div>
    </div>
  );
}

export default Blackbox;
