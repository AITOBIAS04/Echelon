import { useMemo } from 'react';
import { FileSearch, AlertTriangle, ArrowUp, ArrowDown, ArrowRight } from 'lucide-react';
import type { EvidenceEntry } from '../../types/timeline-detail';

/**
 * EvidenceLedger Props
 */
export interface EvidenceLedgerProps {
  /** Array of evidence entries */
  entries: EvidenceEntry[];
  /** Callback when an entry is clicked */
  onEntryClick?: (entryId: string) => void;
}

/**
 * Get source badge color
 */
function getSourceColor(source: string): string {
  const sourceLower = source.toLowerCase();
  if (sourceLower.includes('ravenpack')) return '#00AFFF'; // blue
  if (sourceLower.includes('spire')) return '#9932CC'; // purple
  if (sourceLower.includes('x api') || sourceLower.includes('twitter')) return '#22D3EE'; // cyan
  if (sourceLower.includes('gdelt')) return '#666666'; // grey
  return '#666666'; // default grey
}

/**
 * Get confidence bar color
 */
function getConfidenceColor(confidence: number): string {
  if (confidence > 70) return '#00FF41'; // green
  if (confidence >= 40) return '#FF9500'; // amber
  return '#FF3B3B'; // red
}

/**
 * Format timestamp to HH:MM:SS
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

/**
 * ConfidenceBar Component
 * 
 * Mini confidence bar showing confidence level.
 */
function ConfidenceBar({ confidence }: { confidence: number }) {
  const color = getConfidenceColor(confidence);
  const clampedConfidence = Math.max(0, Math.min(100, confidence));

  return (
    <div className="w-10 h-2 bg-terminal-card rounded-full overflow-hidden">
      <div
        className="h-full transition-all duration-300"
        style={{
          width: `${clampedConfidence}%`,
          backgroundColor: color,
        }}
      />
    </div>
  );
}

/**
 * EvidenceLedger Component
 * 
 * Displays OSINT evidence entries in a scrollable list with sentiment,
 * confidence, and gap impact indicators.
 */
export function EvidenceLedger({ entries, onEntryClick }: EvidenceLedgerProps) {
  // Sort entries by timestamp (most recent first)
  const sortedEntries = useMemo(() => {
    return [...entries].sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return timeB - timeA; // Descending order
    });
  }, [entries]);

  if (sortedEntries.length === 0) {
    return (
      <div className="bg-terminal-panel rounded-lg p-4 border border-terminal-border">
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <FileSearch className="w-12 h-12 text-terminal-text-muted mb-3 opacity-50" />
          <p className="text-sm text-terminal-text-muted">No evidence recorded</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-terminal-panel rounded-lg border border-terminal-border">
      <div className="p-4 border-b border-terminal-border">
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">
          Evidence Ledger
        </h3>
      </div>
      
      <div className="max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {sortedEntries.map((entry) => {
          const sourceColor = getSourceColor(entry.source);
          const hasContradiction = !!entry.contradiction;

          // Determine sentiment icon
          const SentimentIcon =
            entry.sentiment === 'bullish'
              ? ArrowUp
              : entry.sentiment === 'bearish'
              ? ArrowDown
              : ArrowRight;

          const sentimentColor =
            entry.sentiment === 'bullish'
              ? '#00FF41'
              : entry.sentiment === 'bearish'
              ? '#FF3B3B'
              : '#666666';

          // Gap impact badge
          const gapImpact = entry.impactOnGap;
          const gapImpactColor =
            gapImpact > 0
              ? '#FF3B3B' // red for positive (gap increased)
              : gapImpact < 0
              ? '#00FF41' // green for negative (gap decreased)
              : '#666666'; // grey for zero

          return (
            <div
              key={entry.id}
              onClick={() => onEntryClick?.(entry.id)}
              className={`
                flex items-center gap-4 py-2 px-3 border-b border-terminal-border
                transition-colors duration-150
                ${onEntryClick ? 'cursor-pointer hover:bg-terminal-card' : ''}
                ${hasContradiction ? 'border-l-2 border-l-amber-500' : ''}
              `}
            >
              {/* Left Section: Source badge + Timestamp */}
              <div className="flex flex-col gap-1 min-w-[120px]">
                <span
                  className="px-2 py-0.5 rounded-full text-xs font-medium w-fit"
                  style={{
                    backgroundColor: `${sourceColor}20`,
                    color: sourceColor,
                  }}
                >
                  {entry.source}
                </span>
                <span className="text-xs text-terminal-text-muted font-mono">
                  {formatTimestamp(entry.timestamp)}
                </span>
              </div>

              {/* Centre Section: Headline + Sentiment */}
              <div className="flex-1 min-w-0 flex items-center gap-2">
                <span className="text-sm text-terminal-text truncate">
                  {entry.headline.length > 80
                    ? `${entry.headline.substring(0, 80)}...`
                    : entry.headline}
                </span>
                <SentimentIcon
                  className="w-4 h-4 flex-shrink-0"
                  style={{ color: sentimentColor }}
                />
                {hasContradiction && (
                  <div className="relative group flex-shrink-0">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10 bg-terminal-card border border-terminal-border rounded p-2 text-xs text-terminal-text whitespace-nowrap shadow-lg">
                      Conflicts with: {entry.contradiction?.reason}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Section: Confidence bar + Gap impact */}
              <div className="flex items-center gap-3 min-w-[100px]">
                <div className="flex flex-col items-end gap-1">
                  <ConfidenceBar confidence={entry.confidence} />
                  <span className="text-xs text-terminal-text-muted">
                    {entry.confidence}%
                  </span>
                </div>
                <span
                  className="px-2 py-0.5 rounded text-xs font-mono font-semibold"
                  style={{
                    backgroundColor: `${gapImpactColor}20`,
                    color: gapImpactColor,
                  }}
                >
                  {gapImpact > 0 ? '+' : ''}
                  {gapImpact.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
