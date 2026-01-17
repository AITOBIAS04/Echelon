import clsx from 'clsx';

export type FilterCategory = 'crypto' | 'geopolitics' | 'macro' | 'sports' | 'other';
export type FilterOrigin = 'osint' | 'theatre' | 'universal';
export type FilterCreator = 'system' | 'agent' | 'user';

export interface OpsFilters {
  categories: Set<FilterCategory>;
  origins: Set<FilterOrigin>;
  creators: Set<FilterCreator>;
}

interface OpsFiltersBarProps {
  filters: OpsFilters;
  onFiltersChange: (filters: OpsFilters) => void;
}

/**
 * OpsFiltersBar Component
 * 
 * Chip-style filter bar with horizontally scrollable groups.
 * Filters by category, origin, and creator.
 */
export function OpsFiltersBar({ filters, onFiltersChange }: OpsFiltersBarProps) {
  const toggleCategory = (category: FilterCategory) => {
    const newCategories = new Set(filters.categories);
    if (newCategories.has(category)) {
      newCategories.delete(category);
    } else {
      newCategories.add(category);
    }
    onFiltersChange({ ...filters, categories: newCategories });
  };

  const toggleOrigin = (origin: FilterOrigin) => {
    const newOrigins = new Set(filters.origins);
    if (newOrigins.has(origin)) {
      newOrigins.delete(origin);
    } else {
      newOrigins.add(origin);
    }
    onFiltersChange({ ...filters, origins: newOrigins });
  };

  const toggleCreator = (creator: FilterCreator) => {
    const newCreators = new Set(filters.creators);
    if (newCreators.has(creator)) {
      newCreators.delete(creator);
    } else {
      newCreators.add(creator);
    }
    onFiltersChange({ ...filters, creators: newCreators });
  };

  const categories: { id: FilterCategory; label: string }[] = [
    { id: 'crypto', label: 'Crypto' },
    { id: 'geopolitics', label: 'Geopolitics' },
    { id: 'macro', label: 'Macro' },
    { id: 'sports', label: 'Sports' },
    { id: 'other', label: 'Other' },
  ];

  const origins: { id: FilterOrigin; label: string }[] = [
    { id: 'osint', label: 'OSINT' },
    { id: 'theatre', label: 'Theatre' },
    { id: 'universal', label: 'Universal' },
  ];

  const creators: { id: FilterCreator; label: string }[] = [
    { id: 'system', label: 'System' },
    { id: 'agent', label: 'Agent' },
    { id: 'user', label: 'User' },
  ];

  return (
    <div className="flex items-center gap-4 overflow-x-auto scrollbar-hide pb-1">
      {/* Category Filters */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-terminal-muted font-medium uppercase tracking-wide whitespace-nowrap">
          Category:
        </span>
        <div className="flex items-center gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => toggleCategory(cat.id)}
              className={clsx(
                'px-2.5 py-1 text-xs font-medium rounded border transition whitespace-nowrap',
                filters.categories.has(cat.id)
                  ? 'bg-terminal-bg border-[#00D4FF] text-[#00D4FF]'
                  : 'bg-terminal-bg/50 border-terminal-border text-terminal-muted hover:border-terminal-text hover:text-terminal-text'
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Origin Filters */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-terminal-muted font-medium uppercase tracking-wide whitespace-nowrap">
          Origin:
        </span>
        <div className="flex items-center gap-1.5">
          {origins.map((origin) => (
            <button
              key={origin.id}
              onClick={() => toggleOrigin(origin.id)}
              className={clsx(
                'px-2.5 py-1 text-xs font-medium rounded border transition whitespace-nowrap',
                filters.origins.has(origin.id)
                  ? 'bg-terminal-bg border-[#00D4FF] text-[#00D4FF]'
                  : 'bg-terminal-bg/50 border-terminal-border text-terminal-muted hover:border-terminal-text hover:text-terminal-text'
              )}
            >
              {origin.label}
            </button>
          ))}
        </div>
      </div>

      {/* Creator Filters */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-terminal-muted font-medium uppercase tracking-wide whitespace-nowrap">
          Creator:
        </span>
        <div className="flex items-center gap-1.5">
          {creators.map((creator) => (
            <button
              key={creator.id}
              onClick={() => toggleCreator(creator.id)}
              className={clsx(
                'px-2.5 py-1 text-xs font-medium rounded border transition whitespace-nowrap',
                filters.creators.has(creator.id)
                  ? 'bg-terminal-bg border-[#00D4FF] text-[#00D4FF]'
                  : 'bg-terminal-bg/50 border-terminal-border text-terminal-muted hover:border-terminal-text hover:text-terminal-text'
              )}
            >
              {creator.label}
            </button>
          ))}
        </div>
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
