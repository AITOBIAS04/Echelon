import { useMemo } from 'react';
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
  
  // Sort by detonation time (most urgent first) - ONLY show first one
  // Use useMemo to prevent unnecessary recalculations
  const mostUrgentParadox = useMemo(() => {
    if (!paradoxData?.paradoxes || paradoxData.paradoxes.length === 0) {
      console.log('[SigintPanel] No paradoxes available');
      return null;
    }
    const sorted = [...paradoxData.paradoxes].sort((a, b) => 
      new Date(a.detonation_time).getTime() - new Date(b.detonation_time).getTime()
    );
    // CRITICAL: Only return the FIRST paradox, never more
    // Force return only the first element - never an array
    const first = sorted.length > 0 ? sorted[0] : null;
    console.log('[SigintPanel] useMemo returning ONLY first paradox:', first?.id, 'Total available:', sorted.length);
    console.log('[SigintPanel] Type check - is array?', Array.isArray(first), 'is object?', typeof first === 'object');
    return first;
  }, [paradoxData?.paradoxes]);
  
  // Log errors for debugging
  if (timelinesError) console.error('Timelines error:', timelinesError);
  if (flapsError) console.error('Wing flaps error:', flapsError);
  if (paradoxError) console.error('Paradoxes error:', paradoxError);

  // Debug: Log what we're about to render
  console.log('[SigintPanel] Component rendering. Most urgent paradox:', mostUrgentParadox?.id || 'NONE');
  console.log('[SigintPanel] Total paradoxes available:', paradoxData?.paradoxes?.length || 0);
  
  // Debug: Count actual ParadoxAlert components in DOM after render
  if (typeof window !== 'undefined') {
    setTimeout(() => {
      // Count all terminal-panel elements
      const allPanels = document.querySelectorAll('.terminal-panel');
      console.log('[SigintPanel] Total .terminal-panel elements in DOM:', allPanels.length);
      
      // Count specifically paradox alerts (those with "Containment Breach" text)
      const paradoxAlerts = Array.from(allPanels).filter(panel => 
        panel.textContent?.includes('Containment Breach')
      );
      console.log('[SigintPanel] Paradox alert panels found:', paradoxAlerts.length);
      
      // Check if modal is open
      const modal = document.querySelector('[class*="fixed"][class*="inset-0"][class*="z-50"]');
      console.log('[SigintPanel] Modal overlay present?', !!modal);
      
      if (paradoxAlerts.length > 1) {
        console.error('[SigintPanel] ERROR: Multiple paradox alerts detected!', paradoxAlerts.length);
        console.error('[SigintPanel] This should only happen in ParadoxPanel, not SigintPanel!');
      }
    }, 100);
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Paradox Section - ONLY show first (most urgent) paradox */}
      {/* All other paradoxes accessible via header badge modal */}
      {/* CRITICAL: This should render ONLY ONE ParadoxAlert component */}
      {/* DOUBLE CHECK: Ensure mostUrgentParadox is a single object, not an array */}
      {mostUrgentParadox && !Array.isArray(mostUrgentParadox) && typeof mostUrgentParadox === 'object' && 'id' in mostUrgentParadox ? (
        <div className="flex-shrink-0 p-4 border-b border-terminal-border relative z-0">
          <ParadoxAlert
            key={`sigint-paradox-${mostUrgentParadox.id}`}
            paradox={mostUrgentParadox}
            onExtract={() => console.log('Extract', mostUrgentParadox.id)}
            onAbandon={() => console.log('Abandon', mostUrgentParadox.id)}
          />
        </div>
      ) : (
        mostUrgentParadox && console.error('[SigintPanel] ERROR: mostUrgentParadox is not a valid single object!', mostUrgentParadox)
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
