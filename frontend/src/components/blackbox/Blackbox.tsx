import { useState, useEffect } from 'react';
import { Radio, Activity, Shield, Database, Target, Eye, Layers } from 'lucide-react';
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
  const [timestamp, setTimestamp] = useState(new Date());

  // Update timestamp every second
  useEffect(() => {
    const interval = setInterval(() => setTimestamp(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

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
    <div className="h-full flex flex-col p-2 sm:p-4 md:p-6 overflow-hidden bg-slate-800">
      {/* Header */}
      <div className="flex-shrink-0 bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 mb-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-blue-400" />
            <h1 className="text-lg font-semibold text-slate-100">
              Signal Intelligence
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-300">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </span>
            <span className="font-mono">
              {timestamp.toLocaleTimeString('en-GB', { hour12: false })}
            </span>
          </div>
        </div>
      </div>

      {/* Your Positions Panel */}
      <div className="flex-shrink-0 mb-3">
        <PositionsPanel />
      </div>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-h-0 bg-slate-700 border border-slate-600 rounded-lg overflow-hidden">
        {/* Live Ribbon - directly beneath header */}
        <LiveRibbon />

        {/* Tabs */}
        <div className="flex-shrink-0 px-2 sm:px-4 py-3 border-b border-slate-600 overflow-x-auto scrollbar-hide">
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
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : isDeEmphasized
                    ? 'text-slate-400 hover:text-slate-200 opacity-60'
                    : 'text-slate-300 hover:text-blue-400'
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
        <div className="flex-1 min-h-0 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-slate-500 scrollbar-track-transparent">
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
