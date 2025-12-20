import { useTimelines } from '../../hooks/useWingFlaps';
import { useWingFlaps } from '../../hooks/useWingFlaps';
import { useParadoxes } from '../../hooks/useParadoxes';
import { TimelineCard } from './TimelineCard';
import { WingFlapFeed } from './WingFlapFeed';
import { ParadoxAlert } from '../paradox/ParadoxAlert';
import { TrendingUp, Activity, AlertTriangle } from 'lucide-react';

export function SigintPanel() {
  const { data: timelinesData, isLoading: timelinesLoading } = useTimelines({ limit: 8 });
  const { data: flapsData, isLoading: flapsLoading } = useWingFlaps({ limit: 20 });
  const { data: paradoxData } = useParadoxes();

  const timelines = timelinesData?.timelines || [];
  const flaps = flapsData?.flaps || [];
  const paradoxes = paradoxData?.paradoxes || [];

  return (
    <div className="h-full flex flex-col gap-4 p-4">
      {/* Active Paradox Alerts */}
      {paradoxes.length > 0 && (
        <div className="space-y-3">
          {paradoxes.map((paradox) => (
            <ParadoxAlert
              key={paradox.id}
              paradox={paradox}
              onExtract={() => console.log('Extract', paradox.id)}
              onAbandon={() => console.log('Abandon', paradox.id)}
            />
          ))}
        </div>
      )}

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Timeline Grid - Left 8 columns */}
        <div className="col-span-8 flex flex-col min-h-0">
          {/* Section Header */}
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-echelon-cyan" />
            <span className="terminal-header">Trending Timelines</span>
            <span className="text-xs text-terminal-muted ml-auto">
              Sorted by Gravity Score
            </span>
          </div>

          {/* Timeline Cards */}
          <div className="flex-1 overflow-y-auto">
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
        </div>

        {/* Wing Flap Feed - Right 4 columns */}
        <div className="col-span-4 min-h-0">
          <WingFlapFeed flaps={flaps} isLoading={flapsLoading} />
        </div>
      </div>

      {/* Status Bar */}
      <div className="h-8 flex items-center justify-between px-3 bg-terminal-panel border border-terminal-border rounded text-xs">
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
          {paradoxes.length > 0 ? (
            <span className="text-echelon-red">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              {paradoxes.length} breach{paradoxes.length > 1 ? 'es' : ''}
            </span>
          ) : (
            <span className="text-echelon-green">All timelines stable</span>
          )}
        </div>
      </div>
    </div>
  );
}
