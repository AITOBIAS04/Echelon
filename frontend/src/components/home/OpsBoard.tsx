import { useOpsBoard } from '../../hooks/useOpsBoard';
import { LiveNowBar } from './LiveNowBar';
import { OpsLane } from './OpsLane';
import { OpsCard } from './OpsCard';
import type { OpsLaneId } from '../../types/opsBoard';

/**
 * Lane configuration
 */
const LANE_CONFIG: Record<OpsLaneId, { title: string; isHorizontal?: boolean }> = {
  new_creations: { title: 'New Creations' },
  about_to_happen: { title: 'About to Happen' },
  at_risk: { title: 'At Risk' },
  graduation: { title: 'Graduation', isHorizontal: true },
};

/**
 * OpsBoard Component
 * 
 * Main operations board with kanban-style lanes.
 * Shows 3-column grid for main lanes and horizontal strip for graduation.
 */
export function OpsBoard() {
  const { data, loading, error } = useOpsBoard();

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-muted animate-pulse">Loading operations board...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-lg font-semibold text-terminal-text mb-2">Error loading ops board</p>
        <p className="text-sm text-terminal-muted">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Live Now Bar */}
      <LiveNowBar liveNow={data.liveNow} />

      {/* Main Lanes (3-column grid) */}
      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-3 gap-4">
        <OpsLane
          laneId="new_creations"
          cards={data.lanes.new_creations}
          title={LANE_CONFIG.new_creations.title}
        />
        <OpsLane
          laneId="about_to_happen"
          cards={data.lanes.about_to_happen}
          title={LANE_CONFIG.about_to_happen.title}
        />
        <OpsLane
          laneId="at_risk"
          cards={data.lanes.at_risk}
          title={LANE_CONFIG.at_risk.title}
        />
      </div>

      {/* Graduation Lane (horizontal strip) */}
      <div className="flex-shrink-0 border-t border-[#1A1A1A] pt-4">
        <div className="mb-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 rounded" style={{ backgroundColor: '#00FF41' }} />
            <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">
              {LANE_CONFIG.graduation.title}
            </h3>
            <span className="text-xs text-terminal-muted font-mono">
              ({data.lanes.graduation.length})
            </span>
          </div>
        </div>
        <div className="overflow-x-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <div className="flex gap-3 pb-2" style={{ minWidth: 'min-content' }}>
            {data.lanes.graduation.length === 0 ? (
              <div className="text-center py-8 text-terminal-muted text-xs w-full">
                No graduation cards
              </div>
            ) : (
              data.lanes.graduation.map((card) => (
                <div key={card.id} className="flex-shrink-0" style={{ width: '280px' }}>
                  <OpsCard card={card} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
