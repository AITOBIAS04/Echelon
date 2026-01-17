import { useOpsBoard } from '../../hooks/useOpsBoard';
import { LiveNowBar } from './LiveNowBar';
import { OpsCard } from './OpsCard';
import { HorizontalLane } from '../ui/HorizontalLane';

/**
 * OpsBoard Component
 * 
 * Main operations board with horizontal scrolling lanes.
 * Displays stacked horizontal lanes for each category.
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
    <div className="h-full flex flex-col gap-6">
      {/* Live Now Bar */}
      <LiveNowBar liveNow={data.liveNow} />

      {/* Lane 1: New Creations */}
      {data.lanes.new_creations.length > 0 && (
        <HorizontalLane title="🆕 New Creations">
          {data.lanes.new_creations.map((card) => (
            <div key={card.id} className="flex-shrink-0 md:w-[280px] w-[240px]">
              <OpsCard card={card} compact />
            </div>
          ))}
        </HorizontalLane>
      )}

      {/* Lane 2: About to Happen */}
      {data.lanes.about_to_happen.length > 0 && (
        <HorizontalLane title="⚠️ About to Happen">
          {data.lanes.about_to_happen.map((card) => (
            <div key={card.id} className="flex-shrink-0 md:w-[280px] w-[240px]">
              <OpsCard card={card} compact />
            </div>
          ))}
        </HorizontalLane>
      )}

      {/* Lane 3: At Risk */}
      {data.lanes.at_risk.length > 0 && (
        <HorizontalLane title="🚨 At Risk">
          {data.lanes.at_risk.map((card) => (
            <div key={card.id} className="flex-shrink-0 md:w-[280px] w-[240px]">
              <OpsCard card={card} compact />
            </div>
          ))}
        </HorizontalLane>
      )}

      {/* Lane 4: Graduation Zone */}
      {data.lanes.graduation.length > 0 && (
        <HorizontalLane title="🎓 Graduation Zone">
          {data.lanes.graduation.map((card) => (
            <div key={card.id} className="flex-shrink-0 md:w-[280px] w-[240px]">
              <OpsCard card={card} compact />
            </div>
          ))}
        </HorizontalLane>
      )}

      {/* Empty State: Show if all lanes are empty */}
      {data.lanes.new_creations.length === 0 &&
        data.lanes.about_to_happen.length === 0 &&
        data.lanes.at_risk.length === 0 &&
        data.lanes.graduation.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <p className="text-terminal-muted text-sm mb-1">No active signals</p>
              <p className="text-terminal-muted text-xs">Operations board is empty</p>
            </div>
          </div>
        )}
    </div>
  );
}
