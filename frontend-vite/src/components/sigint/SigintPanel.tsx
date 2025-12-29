import { useTimelines } from '../../hooks/useWingFlaps';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { useParadoxes } from '../../hooks/useParadoxes';
import { TimelineCard } from './TimelineCard';
import { WingFlapFeed } from './WingFlapFeed';
import { ParadoxAlert } from '../paradox/ParadoxAlert';
import { TrendingUp, Activity, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export function SigintPanel() {
  const { data: timelinesData, isLoading: timelinesLoading, error: timelinesError } = useTimelines({ limit: 8 });
  const { data: flapsData, isLoading: flapsLoading, error: flapsError } = useWingFlaps({ limit: 20 });
  const { data: paradoxData, error: paradoxError } = useParadoxes();
  const [mobileTab, setMobileTab] = useState<'timelines' | 'feed'>('timelines');

  const timelines = timelinesData?.timelines || [];
  const flaps = flapsData?.flaps || [];
  const paradoxes = paradoxData?.paradoxes || [];
  
  // Log errors for debugging
  if (timelinesError) console.error('Timelines error:', timelinesError);
  if (flapsError) console.error('Wing flaps error:', flapsError);
  if (paradoxError) console.error('Paradoxes error:', paradoxError);

  return (
    <div className="h-full flex flex-col overflow-hidden" data-panel="sigint" data-testid="sigint-panel">
      {/* Only show most urgent paradox to prevent layout overflow */}
      {paradoxes && paradoxes.length > 0 && (
        <div className="flex-shrink-0 p-4 border-b border-terminal-border">
          {(() => {
            const sorted = [...paradoxes].sort((a, b) => 
              new Date(a.detonation_time).getTime() - new Date(b.detonation_time).getTime()
            );
            return <ParadoxAlert key={sorted[0].id} paradox={sorted[0]} />;
          })()}
        </div>
      )}

      {/* Main Content - Full height, no overflow */}
      <div className="flex-1 min-h-0 p-2 sm:p-4">
        {/* Mobile: switch between timelines + feed so they don't visually compete */}
        <div className="lg:hidden h-full flex flex-col min-h-0 overflow-hidden">
          <div className="flex items-center gap-2 mb-3 flex-shrink-0">
            <button
              onClick={() => setMobileTab('timelines')}
              className={
                mobileTab === 'timelines'
                  ? 'px-3 py-2 rounded-lg bg-terminal-panel border border-terminal-border text-echelon-cyan text-sm font-bold'
                  : 'px-3 py-2 rounded-lg bg-terminal-bg border border-terminal-border text-terminal-muted text-sm font-bold'
              }
            >
              <TrendingUp className="w-4 h-4 inline mr-1" />
              Timelines
            </button>
            <button
              onClick={() => setMobileTab('feed')}
              className={
                mobileTab === 'feed'
                  ? 'px-3 py-2 rounded-lg bg-terminal-panel border border-terminal-border text-echelon-cyan text-sm font-bold'
                  : 'px-3 py-2 rounded-lg bg-terminal-bg border border-terminal-border text-terminal-muted text-sm font-bold'
              }
            >
              <Activity className="w-4 h-4 inline mr-1" />
              Feed
            </button>
            <div className="flex-1" />
            <span className="text-xs text-terminal-muted font-mono">
              {mobileTab === 'timelines' ? `${timelines.length} timelines` : `${flapsData?.total_count || 0} events`}
            </span>
          </div>

          {mobileTab === 'timelines' ? (
            <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
              <div className="flex items-center justify-between mb-3 flex-shrink-0">
                <h2 className="text-base font-bold text-cyan-400 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  TRENDING
                </h2>
                <span className="text-[10px] text-gray-500 flex items-center gap-1">
                  Sorted by <span className="text-amber-400 font-bold">Gravity</span>
                  <span className="text-gray-600">◉</span>
                </span>
              </div>
              <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {timelinesLoading ? (
                  <div className="grid grid-cols-1 gap-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="terminal-panel p-4 h-44 animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3">
                    {timelines.map((timeline) => (
                      <TimelineCard
                        key={timeline.id}
                        timeline={timeline}
                        onClick={() => console.log('Open timeline', timeline.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
              <div className="flex items-center justify-between mb-3 flex-shrink-0">
                <h3 className="terminal-header">WING FLAP FEED</h3>
                <span className="text-xs text-echelon-green flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  LIVE
                </span>
              </div>
              <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                <WingFlapFeed flaps={flaps} isLoading={flapsLoading} />
              </div>
            </div>
          )}
        </div>

        {/* Desktop: split view */}
        <div className="hidden lg:flex h-full flex-row gap-6 overflow-hidden">
          {/* Trending Timelines - scrollable */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h2 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                TRENDING TIMELINES
              </h2>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                Sorted by <span className="text-amber-400 font-bold">Gravity Score</span>
                <span className="text-gray-600">◉</span>
              </span>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              {timelinesLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="terminal-panel p-4 h-48 animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
                  {timelines.map((timeline) => (
                    <TimelineCard
                      key={timeline.id}
                      timeline={timeline}
                      onClick={() => console.log('Open timeline', timeline.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Wing Flap Feed - scrollable */}
          <div className="w-full lg:w-96 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="terminal-header">WING FLAP FEED</h3>
              <span className="text-xs text-echelon-green flex items-center gap-1">
                <Activity className="w-3 h-3" />
                LIVE
              </span>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
              <WingFlapFeed flaps={flaps} isLoading={flapsLoading} />
            </div>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex-shrink-0 h-8 flex items-center justify-between px-3 bg-terminal-panel border-t border-terminal-border text-xs">
        <div className="flex items-center gap-4">
          <span className="text-terminal-muted">
            <Activity className="w-3 h-3 inline mr-1" />
            {flapsData?.total_count || 0} events
          </span>
          <span className="text-terminal-muted">
            {timelines.length} timelines active
          </span>
        </div>
        <div className="flex items-center gap-2">
          {(paradoxData?.paradoxes?.length || 0) > 0 ? (
            <span className="text-echelon-red">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              {paradoxData?.paradoxes?.length || 0} breach{(paradoxData?.paradoxes?.length || 0) > 1 ? 'es' : ''}
            </span>
          ) : (
            <span className="text-echelon-green">All timelines stable</span>
          )}
        </div>
      </div>
    </div>
  );
}
