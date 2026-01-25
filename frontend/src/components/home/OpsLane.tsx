import type { OpsCard, OpsLaneId } from '../../types/opsBoard';
import { OpsCard as OpsCardComponent } from './OpsCard';

/**
 * OpsLane Props
 */
export interface OpsLaneProps {
  /** Lane identifier */
  laneId: OpsLaneId;
  /** Cards in this lane */
  cards: OpsCard[];
  /** Lane title */
  title: string;
}

/**
 * Get lane header color
 */
function getLaneHeaderColor(laneId: OpsLaneId): string {
  switch (laneId) {
    case 'new_creations':
      return '#10B981';
    case 'about_to_happen':
      return '#F59E0B';
    case 'at_risk':
      return '#EF4444';
    case 'graduation':
      return '#8B5CF6';
  }
}

/**
 * OpsLane Component
 * 
 * Displays a vertical lane of operations cards.
 */
export function OpsLane({ laneId, cards, title }: OpsLaneProps) {
  const headerColor = getLaneHeaderColor(laneId);

  return (
    <div className="flex flex-col h-full">
      {/* Lane Header */}
      <div className="flex-shrink-0 mb-3">
        <div className="flex items-center gap-2 mb-1">
          <div
            className="w-1 h-4 rounded"
            style={{ backgroundColor: headerColor }}
          />
          <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">
            {title}
          </h3>
          <span className="text-xs text-terminal-muted font-mono">
            ({cards.length})
          </span>
        </div>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {cards.length === 0 ? (
          <div className="text-center py-8 text-terminal-muted text-xs">
            No cards
          </div>
        ) : (
          cards.map((card) => <OpsCardComponent key={card.id} card={card} />)
        )}
      </div>
    </div>
  );
}
