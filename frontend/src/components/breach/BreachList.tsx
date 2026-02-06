import { useState, useMemo } from 'react';
import { CheckCircle, ChevronDown } from 'lucide-react';
import type { Breach, BreachSeverity } from '../../types/breach';

/**
 * BreachList Props
 */
export interface BreachListProps {
  /** Array of breaches to display */
  breaches: Breach[];
  /** Callback when a breach card is clicked */
  onBreachClick: (breachId: string) => void;
  /** Currently selected breach ID */
  selectedBreachId?: string;
}

type SortOption = 'newest' | 'severity' | 'category';

/**
 * Get severity badge color
 */
function getSeverityColor(severity: BreachSeverity): string {
  switch (severity) {
    case 'critical':
      return '#FF3B3B'; // red
    case 'high':
      return '#FF6B00'; // orange
    case 'medium':
      return '#FF9500'; // amber
    case 'low':
      return '#666666'; // grey
  }
}

/**
 * Get category badge color
 */
function getCategoryColor(category: Breach['category']): { bg: string; text: string; pulse?: boolean } {
  switch (category) {
    case 'logic_gap_spike':
      return { bg: '#FF9500', text: '#FF9500' }; // amber
    case 'sensor_contradiction':
      return { bg: '#9932CC', text: '#9932CC' }; // purple
    case 'sabotage_cluster':
      return { bg: '#FF3B3B', text: '#FF3B3B' }; // red
    case 'oracle_flip':
      return { bg: '#22D3EE', text: '#22D3EE' }; // cyan
    case 'stability_collapse':
      return { bg: '#FF6B00', text: '#FF6B00' }; // orange
    case 'paradox_detonation':
      return { bg: '#FF3B3B', text: '#FF3B3B', pulse: true }; // red pulsing
  }
}

/**
 * Format timestamp to relative time or HH:MM:SS
 */
function formatTimestamp(timestamp: string): string {
  const now = new Date().getTime();
  const eventTime = new Date(timestamp).getTime();
  const diffMs = now - eventTime;
  const diffSeconds = Math.floor(diffMs / 1000);

  // If less than 1 hour, show relative time
  if (diffSeconds < 3600) {
    if (diffSeconds < 60) {
      return `${diffSeconds}s ago`;
    }
    const minutes = Math.floor(diffSeconds / 60);
    return `${minutes}m ago`;
  }

  // Otherwise show HH:MM:SS
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

/**
 * Format category name for display
 */
function formatCategory(category: Breach['category']): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * BreachList Component
 * 
 * Displays a filterable, sortable list of breaches with selection support.
 */
export function BreachList({
  breaches,
  onBreachClick,
  selectedBreachId,
}: BreachListProps) {
  const [selectedSeverities, setSelectedSeverities] = useState<Set<BreachSeverity>>(
    new Set(['critical', 'high', 'medium', 'low'])
  );
  const [selectedStatuses, setSelectedStatuses] = useState<Set<Breach['status']>>(
    new Set(['active', 'investigating', 'mitigated', 'resolved'])
  );
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [isSortOpen, setIsSortOpen] = useState(false);

  // Filter breaches
  const filteredBreaches = useMemo(() => {
    return breaches.filter((breach) => {
      const matchesSeverity = selectedSeverities.has(breach.severity);
      const matchesStatus = selectedStatuses.has(breach.status);
      return matchesSeverity && matchesStatus;
    });
  }, [breaches, selectedSeverities, selectedStatuses]);

  // Sort breaches
  const sortedBreaches = useMemo(() => {
    const sorted = [...filteredBreaches];
    switch (sortBy) {
      case 'newest':
        return sorted.sort((a, b) => {
          const timeA = new Date(a.timestamp).getTime();
          const timeB = new Date(b.timestamp).getTime();
          return timeB - timeA; // Descending (newest first)
        });
      case 'severity':
        const severityOrder: Record<BreachSeverity, number> = {
          critical: 4,
          high: 3,
          medium: 2,
          low: 1,
        };
        return sorted.sort((a, b) => {
          return severityOrder[b.severity] - severityOrder[a.severity];
        });
      case 'category':
        return sorted.sort((a, b) => {
          return a.category.localeCompare(b.category);
        });
      default:
        return sorted;
    }
  }, [filteredBreaches, sortBy]);

  const toggleSeverity = (severity: BreachSeverity) => {
    setSelectedSeverities((prev) => {
      const next = new Set(prev);
      if (next.has(severity)) {
        next.delete(severity);
      } else {
        next.add(severity);
      }
      return next;
    });
  };

  const toggleStatus = (status: Breach['status']) => {
    setSelectedStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(status)) {
        next.delete(status);
      } else {
        next.add(status);
      }
      return next;
    });
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 rounded-lg border border-[#1A1A1A]">
      {/* Filter Bar */}
      <div className="p-4 border-b border-[#1A1A1A] space-y-3">
        {/* Severity Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-terminal-text-muted uppercase mr-2">Severity:</span>
          {(['all', 'critical', 'high', 'medium', 'low'] as const).map((severity) => {
            if (severity === 'all') {
              const allSelected =
                selectedSeverities.size === 4 ||
                (selectedSeverities.has('critical') &&
                  selectedSeverities.has('high') &&
                  selectedSeverities.has('medium') &&
                  selectedSeverities.has('low'));
              return (
                <button
                  key={severity}
                  onClick={() => {
                    if (allSelected) {
                      setSelectedSeverities(new Set());
                    } else {
                      setSelectedSeverities(new Set(['critical', 'high', 'medium', 'low']));
                    }
                  }}
                  className={`px-2 py-1 text-xs rounded transition ${
                    allSelected
                      ? 'bg-[#22D3EE]/20 border border-[#22D3EE] text-[#22D3EE]'
                      : 'bg-terminal-bg border border-[#333] text-terminal-text-muted hover:text-terminal-text'
                  }`}
                >
                  All
                </button>
              );
            }
            const isSelected = selectedSeverities.has(severity);
            return (
              <button
                key={severity}
                onClick={() => toggleSeverity(severity)}
                className={`px-2 py-1 text-xs rounded transition capitalize ${
                  isSelected
                    ? 'bg-[#22D3EE]/20 border border-[#22D3EE] text-[#22D3EE]'
                    : 'bg-terminal-bg border border-[#333] text-terminal-text-muted hover:text-terminal-text'
                }`}
              >
                {severity}
              </button>
            );
          })}
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-terminal-text-muted uppercase mr-2">Status:</span>
          {(['active', 'investigating', 'mitigated', 'resolved'] as const).map((status) => {
            const isSelected = selectedStatuses.has(status);
            return (
              <button
                key={status}
                onClick={() => toggleStatus(status)}
                className={`px-2 py-1 text-xs rounded transition capitalize ${
                  isSelected
                    ? 'bg-[#22D3EE]/20 border border-[#22D3EE] text-[#22D3EE]'
                    : 'bg-terminal-bg border border-[#333] text-terminal-text-muted hover:text-terminal-text'
                }`}
              >
                {status}
              </button>
            );
          })}
        </div>

        {/* Sort Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-terminal-text-muted">Sort by:</span>
          <div className="relative">
            <button
              onClick={() => setIsSortOpen(!isSortOpen)}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-terminal-bg border border-[#333] rounded hover:border-[#22D3EE] transition"
            >
              {sortBy === 'newest'
                ? 'Newest'
                : sortBy === 'severity'
                ? 'Severity'
                : 'Category'}
              <ChevronDown className={`w-3 h-3 transition ${isSortOpen ? 'rotate-180' : ''}`} />
            </button>
            {isSortOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setIsSortOpen(false)}
                />
                <div className="absolute top-full left-0 mt-1 bg-slate-900 border border-[#1A1A1A] rounded shadow-lg z-20 min-w-[120px]">
                  {(['newest', 'severity', 'category'] as SortOption[]).map((option) => (
                    <button
                      key={option}
                      onClick={() => {
                        setSortBy(option);
                        setIsSortOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs hover:bg-terminal-panel transition ${
                        sortBy === option ? 'text-[#22D3EE]' : 'text-terminal-text'
                      }`}
                    >
                      {option === 'newest'
                        ? 'Newest'
                        : option === 'severity'
                        ? 'Severity'
                        : 'Category'}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Breach Cards List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {sortedBreaches.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h3 className="text-lg font-semibold text-terminal-text mb-2">
              No breaches detected
            </h3>
            <p className="text-sm text-terminal-text-muted">
              System integrity is stable. All timelines operating normally.
            </p>
          </div>
        ) : (
          sortedBreaches.map((breach) => {
            const severityColor = getSeverityColor(breach.severity);
            const categoryColors = getCategoryColor(breach.category);
            const isSelected = selectedBreachId === breach.id;
            const isCritical = breach.severity === 'critical';

            return (
              <div
                key={breach.id}
                onClick={() => onBreachClick(breach.id)}
                className={`
                  relative bg-terminal-panel rounded border p-3 cursor-pointer transition
                  ${isSelected ? 'border-[#22D3EE]' : 'border-[#1A1A1A] hover:border-[#333]'}
                `}
              >
                {/* Severity color bar (left edge) */}
                <div
                  className={`absolute left-0 top-0 bottom-0 w-1 rounded-l ${
                    isCritical ? 'animate-pulse' : ''
                  }`}
                  style={{ backgroundColor: severityColor }}
                />

                <div className="ml-3 flex items-start justify-between gap-4">
                  {/* Left Section */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-terminal-text truncate">
                        {breach.title}
                      </h4>
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${
                          categoryColors.pulse ? 'animate-pulse' : ''
                        }`}
                        style={{
                          backgroundColor: `${categoryColors.bg}20`,
                          color: categoryColors.text,
                        }}
                      >
                        {formatCategory(breach.category)}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-terminal-text-muted">
                      <span>{formatTimestamp(breach.timestamp)}</span>
                      <span>
                        {breach.affectedTimelines.length} timeline
                        {breach.affectedTimelines.length !== 1 ? 's' : ''},{' '}
                        {breach.affectedAgents.length} agent
                        {breach.affectedAgents.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>

                  {/* Right Section: Status Badge */}
                  <div className="flex-shrink-0">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                      style={{
                        backgroundColor: `${severityColor}20`,
                        color: severityColor,
                        border: `1px solid ${severityColor}`,
                      }}
                    >
                      {breach.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
