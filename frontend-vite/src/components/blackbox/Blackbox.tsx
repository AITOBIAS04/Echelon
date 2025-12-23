import { useState } from 'react';
import { Radio, Activity, Shield, Skull, AlertTriangle, Clock } from 'lucide-react';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { useTimelines } from '../../hooks/useWingFlaps';
import { clsx } from 'clsx';

type TabType = 'intercepts' | 'health' | 'warchest';

export function Blackbox() {
  const [activeTab, setActiveTab] = useState<TabType>('intercepts');
  const { data: flapsData } = useWingFlaps();
  const { data: timelinesData } = useTimelines();
  
  const wingFlaps = flapsData?.flaps || [];
  const timelines = timelinesData?.timelines || [];

  const tabs = [
    { id: 'intercepts' as TabType, label: 'INTERCEPTS', icon: Radio },
    { id: 'health' as TabType, label: 'TIMELINE HEALTH', icon: Activity },
    { id: 'warchest' as TabType, label: 'WAR CHEST', icon: Shield },
  ];

  return (
    <div className="h-full flex flex-col overflow-hidden">
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
        <div className="flex-shrink-0 flex justify-between items-center px-4 py-3 border-b border-[#1a3a1a] bg-[#0a0a0a]">
          <h1 className="text-lg font-bold text-[#00FF41] tracking-wider" style={{ textShadow: '0 0 10px rgba(0, 255, 65, 0.5)' }}>
            SIGNAL INTELLIGENCE
          </h1>
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-500">ONLINE</span>
            </span>
            <span className="text-gray-500 font-mono">
              {new Date().toLocaleTimeString('en-GB', { hour12: false })}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex-shrink-0 flex gap-8 px-4 py-3 border-b border-[#1a3a1a]">
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
        <div className="flex-1 min-h-0 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {activeTab === 'intercepts' && <InterceptsTab wingFlaps={wingFlaps} />}
          {activeTab === 'health' && <TimelineHealthTab timelines={timelines} />}
          {activeTab === 'warchest' && <WarChestTab timelines={timelines} />}
        </div>

        {/* Blinking Cursor */}
        <div className="flex-shrink-0 px-4 pb-2">
          <span className="text-[#00FF41] animate-pulse">▌</span>
        </div>
      </div>
    </div>
  );
}

// Tab Components
function InterceptsTab({ wingFlaps }: { wingFlaps: any[] }) {
  const [filter, setFilter] = useState('ALL');
  
  const getAgentColour = (archetype: string) => {
    switch (archetype?.toUpperCase()) {
      case 'SHARK': return 'text-cyan-400';
      case 'SPY': return 'text-yellow-400';
      case 'DIPLOMAT': return 'text-blue-400';
      case 'SABOTEUR': return 'text-red-400';
      case 'WHALE': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const filteredFlaps = wingFlaps.filter(flap => {
    if (filter === 'ALL') return true;
    if (filter === 'SHARKS') return flap.agent_archetype === 'SHARK';
    if (filter === 'WHALES') return flap.agent_archetype === 'WHALE';
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-2 text-xs">
        {['ALL', 'SHARKS', 'WHALES', 'DIVERGENCE'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              'px-3 py-1 rounded transition-all',
              filter === f
                ? 'bg-[#1a3a1a] text-green-400'
                : 'bg-[#0a0a0a] border border-[#1a3a1a] text-gray-500 hover:text-[#00FF41]'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Feed */}
      <div className="space-y-1 font-mono text-sm">
        {filteredFlaps.slice(0, 50).map((flap, i) => {
          const time = new Date(flap.timestamp || flap.created_at).toLocaleTimeString('en-GB', { hour12: false });
          const isStabilising = flap.direction === 'ANCHOR';
          
          return (
            <div key={flap.id || i} className="animate-in slide-in-from-left">
              <span className="text-gray-500">[{time}]</span>
              {' '}
              <span className="text-gray-500">INTERCEPT:</span>
              {' '}
              <span className={getAgentColour(flap.agent_archetype)}>
                {flap.agent_name || 'SYSTEM'}
              </span>
              {' '}
              <span className={isStabilising ? 'text-green-400' : 'text-red-400'}>
                {flap.action}
              </span>
              {' '}
              <span className="text-gray-500">
                ({flap.stability_delta > 0 ? '+' : ''}{flap.stability_delta?.toFixed(1)}% → {flap.timeline_id})
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TimelineHealthTab({ timelines }: { timelines: any[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {timelines.map((timeline) => {
        const stability = timeline.stability || 0;
        const isStable = stability > 70;
        const isUnstable = stability > 40 && stability <= 70;
        const isCritical = stability <= 40;
        
        return (
          <div
            key={timeline.id}
            className={clsx(
              'bg-[#0a0a0a] border rounded-lg p-4',
              isCritical ? 'border-red-600' : isUnstable ? 'border-yellow-600' : 'border-[#1a3a1a]'
            )}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="font-bold text-white text-sm">{timeline.name}</h3>
              <span className={clsx(
                'px-2 py-1 text-xs rounded',
                isCritical ? 'bg-red-900/30 text-red-400' :
                isUnstable ? 'bg-yellow-900/30 text-yellow-400' :
                'bg-green-900/30 text-green-400'
              )}>
                {isCritical ? '⚠️ CRITICAL' : isUnstable ? '⚠️ UNSTABLE' : '✓ STABLE'}
              </span>
            </div>

            {/* Stability Gauge */}
            <div className="flex items-center gap-4 mb-4">
              <div className="relative w-16 h-16">
                <svg className="w-16 h-16 -rotate-90">
                  <circle cx="32" cy="32" r="28" stroke="#1a3a1a" strokeWidth="4" fill="none"/>
                  <circle 
                    cx="32" cy="32" r="28" 
                    stroke={isCritical ? '#EF4444' : isUnstable ? '#EAB308' : '#22C55E'}
                    strokeWidth="4" 
                    fill="none"
                    strokeDasharray={`${stability * 1.76} 176`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className={clsx(
                  'absolute inset-0 flex items-center justify-center text-sm font-bold',
                  isCritical ? 'text-red-400' : isUnstable ? 'text-yellow-400' : 'text-green-400'
                )}>
                  {stability.toFixed(0)}%
                </span>
              </div>
              <div className="flex-1 space-y-2 text-xs">
                <div>
                  <span className="text-gray-500">OSINT ALIGNMENT:</span>
                  <div className="h-2 bg-[#1a3a1a] rounded mt-1">
                    <div 
                      className="h-full bg-blue-500 rounded"
                      style={{ width: `${timeline.osint_alignment || 50}%` }}
                    />
                  </div>
                </div>
                <div className="text-gray-400">
                  DECAY: <span className={timeline.decay_rate_per_hour > 3 ? 'text-red-400' : 'text-gray-300'}>
                    {timeline.decay_rate_per_hour || 1}%/hr
                  </span>
                </div>
              </div>
            </div>

            {/* Collapse Countdown if has paradox */}
            {timeline.has_active_paradox && (
              <div className="bg-red-900/20 border border-red-600 rounded p-2 text-center">
                <div className="flex items-center justify-center gap-2 text-red-400">
                  <Clock className="w-4 h-4" />
                  <span className="font-mono font-bold animate-pulse">PARADOX ACTIVE</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function WarChestTab({ timelines }: { timelines: any[] }) {
  // Mock war data - in production, this would come from API
  const warData = timelines.slice(0, 3).map((tl) => ({
    ...tl,
    sabotage_pool: Math.random() * 50000,
    shield_pool: Math.random() * 50000,
  })).map(tl => ({
    ...tl,
    total: tl.sabotage_pool + tl.shield_pool,
    sabotage_pct: (tl.sabotage_pool / (tl.sabotage_pool + tl.shield_pool)) * 100,
  }));

  return (
    <div className="space-y-6">
      {warData.map((war) => {
        const isUnderSiege = war.sabotage_pct > 70;
        const isDefended = war.sabotage_pct < 30;
        
        return (
          <div 
            key={war.id}
            className={clsx(
              'bg-[#0a0a0a] border rounded-lg p-4',
              isUnderSiege ? 'border-red-600' : isDefended ? 'border-blue-600' : 'border-[#1a3a1a]'
            )}
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-white">{war.name} — ${war.total.toLocaleString()} TOTAL</h3>
              <span className={clsx(
                'text-sm',
                isUnderSiege ? 'text-red-400 animate-pulse' : isDefended ? 'text-blue-400' : 'text-yellow-400'
              )}>
                {isUnderSiege ? '💀 UNDER SIEGE' : isDefended ? '🛡️ DEFENDED' : '⚔️ CONTESTED'}
              </span>
            </div>

            {/* Tug of War Bar */}
            <div className="relative h-8 rounded overflow-hidden mb-2">
              <div className="absolute inset-0 flex">
                <div 
                  className={clsx('flex items-center justify-start pl-2', isUnderSiege ? 'bg-red-600 animate-pulse' : 'bg-red-600/70')}
                  style={{ width: `${war.sabotage_pct}%` }}
                >
                  <span className="text-white text-xs font-bold">
                    💀 ${war.sabotage_pool.toLocaleString()}
                  </span>
                </div>
                <div 
                  className={clsx('flex items-center justify-end pr-2', isDefended ? 'bg-blue-600' : 'bg-blue-600/70')}
                  style={{ width: `${100 - war.sabotage_pct}%` }}
                >
                  <span className="text-white text-xs font-bold">
                    ${war.shield_pool.toLocaleString()} 🛡️
                  </span>
                </div>
              </div>
            </div>

            {/* Percentages */}
            <div className="flex justify-between text-xs text-gray-500">
              <span className={isUnderSiege ? 'text-red-400' : ''}>
                SABOTAGE: {war.sabotage_pct.toFixed(0)}%
              </span>
              <span className={isDefended ? 'text-blue-400' : ''}>
                SHIELD: {(100 - war.sabotage_pct).toFixed(0)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default Blackbox;
