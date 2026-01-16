import type { WatchlistFilter } from '../../types/watchlist';

/**
 * WatchlistFilterBar Props
 */
export interface WatchlistFilterBarProps {
  /** Currently active filter */
  activeFilter: WatchlistFilter;
  /** Callback when filter changes */
  onFilterChange: (filter: WatchlistFilter) => void;
  /** Count of items for each filter */
  counts: Record<WatchlistFilter, number>;
}

/**
 * Filter configuration with labels
 */
const FILTER_CONFIG: Record<WatchlistFilter, { label: string }> = {
  'all': { label: 'All' },
  'brittle': { label: 'Brittle' },
  'paradox-watch': { label: 'Paradox Watch' },
  'high-entropy': { label: 'High Entropy' },
  'under-attack': { label: 'Under Attack' },
};

/**
 * Filter order for display
 */
const FILTER_ORDER: WatchlistFilter[] = [
  'all',
  'brittle',
  'paradox-watch',
  'high-entropy',
  'under-attack',
];

/**
 * WatchlistFilterBar Component
 * 
 * Renders a row of selectable filter chips for the Watchlist.
 * Each chip shows a count badge when count > 0.
 * 
 * @example
 * ```tsx
 * <WatchlistFilterBar
 *   activeFilter="brittle"
 *   onFilterChange={(filter) => setFilter(filter)}
 *   counts={{
 *     'all': 12,
 *     'brittle': 3,
 *     'paradox-watch': 2,
 *     'high-entropy': 5,
 *     'under-attack': 1,
 *   }}
 * />
 * ```
 */
export function WatchlistFilterBar({
  activeFilter,
  onFilterChange,
  counts,
}: WatchlistFilterBarProps) {
  const activeColor = '#00FF41'; // green
  const inactiveBorder = '#333';
  const inactiveText = '#666';

  return (
    <div className="flex items-center gap-2">
      {FILTER_ORDER.map((filter) => {
        const isActive = activeFilter === filter;
        const count = counts[filter] || 0;
        const { label } = FILTER_CONFIG[filter];

        return (
          <button
            key={filter}
            onClick={() => onFilterChange(filter)}
            className={`
              relative px-3 py-1 rounded-full text-xs font-medium
              transition-colors duration-150
              ${isActive 
                ? 'bg-green-500/10' 
                : 'bg-transparent hover:text-[#999]'
              }
            `}
            style={{
              border: `1px solid ${isActive ? activeColor : inactiveBorder}`,
              color: isActive ? activeColor : inactiveText,
            }}
          >
            {label}
            {count > 0 && (
              <span
                className={`
                  absolute -top-1 -right-1 min-w-[16px] h-4 px-1
                  rounded-full text-[10px] font-bold
                  flex items-center justify-center
                  ${isActive ? 'bg-green-500' : 'bg-[#666]'}
                  text-white
                `}
              >
                {count > 99 ? '99+' : count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
