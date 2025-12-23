import { useState, useEffect } from 'react';
import { Radio, Activity, Shield, Database } from 'lucide-react';
import { WhaleWatch } from './WhaleWatch';
import { TimelineHealthPanel } from './TimelineHealthPanel';
import { WarChest } from './WarChest';
import { clsx } from 'clsx';

type TabType = 'intercepts' | 'health' | 'warchest';

export function Blackbox() {
  const [activeTab, setActiveTab] = useState<TabType>('intercepts');
  const [timestamp, setTimestamp] = useState(new Date());

  // Update timestamp every second
  useEffect(() => {
    const interval = setInterval(() => setTimestamp(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'intercepts' as TabType, label: 'INTERCEPTS', icon: Radio },
    { id: 'health' as TabType, label: 'TIMELINE HEALTH', icon: Activity },
    { id: 'warchest' as TabType, label: 'WAR CHEST', icon: Shield },
  ];

  return (
    <div className="h-full flex flex-col p-6 overflow-hidden">
      {/* Classification Banner */}
      <div className="flex-shrink-0 bg-red-900/30 border border-red-600 text-center py-2 mb-4 rounded">
        <span className="text-red-400 font-bold tracking-widest text-sm">
          ▀▀▀ CLASSIFICATION: TOP SECRET // ECHELON ▀▀▀
        </span>
      </div>

      {/* Terminal Container */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#0D0D0D] border border-[#1a3a1a] rounded-lg overflow-hidden relative">
        {/* Scanline Effect */}
        <div 
          className="absolute inset-0 pointer-events-none z-10"
          style={{
            background: `repeating-linear-gradient(
              0deg,
              transparent,
              transparent 2px,
              rgba(0, 255, 65, 0.03) 2px,
              rgba(0, 255, 65, 0.03) 4px
            )`
          }}
        />

        {/* Header */}
        <div className="flex-shrink-0 flex justify-between items-center px-4 py-3 border-b border-[#1a3a1a] bg-[#0a0a0a] relative z-20">
          <h1 
            className="text-lg font-bold text-[#00FF41] tracking-wider flex items-center gap-2"
            style={{ textShadow: '0 0 10px rgba(0, 255, 65, 0.5)' }}
          >
            <Database className="w-5 h-5" />
            SIGNAL INTELLIGENCE
          </h1>
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-500">ONLINE</span>
            </span>
            <span className="text-gray-500 font-mono">
              {timestamp.toLocaleTimeString('en-GB', { hour12: false })}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex-shrink-0 flex gap-8 px-4 py-3 border-b border-[#1a3a1a] relative z-20">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex items-center gap-2 pb-2 uppercase tracking-wider text-sm transition-all',
                  activeTab === tab.id
                    ? 'text-[#00FF41] border-b-2 border-[#00FF41]'
                    : 'text-gray-500 hover:text-[#00FF41]/70'
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 min-h-0 overflow-y-auto p-4 relative z-20 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {activeTab === 'intercepts' && <WhaleWatch />}
          {activeTab === 'health' && <TimelineHealthPanel />}
          {activeTab === 'warchest' && <WarChest />}
        </div>

        {/* Blinking Cursor */}
        <div className="flex-shrink-0 px-4 pb-2 relative z-20">
          <span className="text-[#00FF41] animate-pulse">▌</span>
        </div>
      </div>
    </div>
  );
}

export default Blackbox;
