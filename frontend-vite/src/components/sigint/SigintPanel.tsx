import { useTimelines } from '../../hooks/useWingFlaps';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { useParadoxes } from '../../hooks/useParadoxes';
import { TimelineCard } from './TimelineCard';
import { WingFlapFeed } from './WingFlapFeed';
import { ParadoxAlert } from '../paradox/ParadoxAlert';
import { TrendingUp, Activity, AlertTriangle } from 'lucide-react';

export function SigintPanel() {
  const { data: timelinesData, isLoading: timelinesLoading, error: timelinesError } = useTimelines({ limit: 8 });
  const { data: flapsData, isLoading: flapsLoading, error: flapsError } = useWingFlaps({ limit: 20 });
  const { data: paradoxData, error: paradoxError } = useParadoxes();

  const timelines = timelinesData?.timelines || [];
  const flaps = flapsData?.flaps || [];
  // Sort paradoxes by detonation_time ascending (most urgent first)
  const sortedParadoxes = (paradoxData?.paradoxes || []).sort((a, b) => {
    const timeA = new Date(a.detonation_time).getTime();
    const timeB = new Date(b.detonation_time).getTime();
    return timeA - timeB;
  });
  
  // Format countdown for compact display
  const formatCountdown = (seconds: number): string => {
    if (seconds <= 0) return '00:00:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };
  
  // Log errors for debugging
  if (timelinesError) console.error('Timelines error:', timelinesError);
  if (flapsError) console.error('Wing flaps error:', flapsError);
  if (paradoxError) console.error('Paradoxes error:', paradoxError);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Paradox Section - Compact summary */}
      {sortedParadoxes && sortedParadoxes.length > 0 && (
        <div className="flex-shrink-0 max-h-[40vh] overflow-y-auto p-4 space-y-3 border-b border-terminal-border">
          {/* Most urgent paradox - full display */}
          <ParadoxAlert
            key={sortedParadoxes[0].id}
            paradox={sortedParadoxes[0]}
            onExtract={() => console.log('Extract', sortedParadoxes[0].id)}
            onAbandon={() => console.log('Abandon', sortedParadoxes[0].id)}
          />
          
          {/* Other paradoxes - compact list */}
          {sortedParadoxes.length > 1 && (
            <div className="terminal-panel p-3 space-y-1">
              <div className="text-xs text-terminal-muted uppercase mb-2">
                +{sortedParadoxes.length - 1} More Breach{sortedParadoxes.length > 2 ? 'es' : ''}
              </div>
              {sortedParadoxes.slice(1).map((p) => (
                <div key={p.id} className="flex justify-between items-center text-sm py-1 border-b border-terminal-border/50 last:border-0">
                  <span className="text-terminal-text">{p.timeline_name}</span>
                  <span className="font-mono text-echelon-red">
                    {formatCountdown(p.time_remaining_seconds || 0)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Content - Takes remaining space, scrollable */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Timelines - 2 columns */}
          <div className="lg:col-span-2">
            {/* Section Header */}
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-echelon-cyan" />
              <span className="terminal-header">Trending Timelines</span>
              <span className="text-xs text-terminal-muted ml-auto">
                Sorted by Gravity Score
              </span>
            </div>

            {/* Timeline Cards */}
            {timelinesLoading ? (
              <div className="grid grid-cols-2 gap-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="terminal-panel p-4 h-48 animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
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
          
          {/* Wing Flap Feed - 1 column */}
          <div className="lg:col-span-1">
            <WingFlapFeed flaps={flaps} isLoading={flapsLoading} />
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
          {sortedParadoxes.length > 0 ? (
            <span className="text-echelon-red">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              {sortedParadoxes.length} breach{sortedParadoxes.length > 1 ? 'es' : ''}
            </span>
          ) : (
            <span className="text-echelon-green">All timelines stable</span>
          )}
        </div>
      </div>
    </div>
  );
}
