import type { Signal } from '../../types/signal';
import { SourceBadge } from './SourceBadge';
import { relativeTime, formatPercentage } from '../../utils/format';

interface SignalCardProps {
  signal: Signal;
  isSelected: boolean;
  animationDelay: number;
  onClick: () => void;
}

export function SignalCard({
  signal,
  isSelected,
  animationDelay,
  onClick,
}: SignalCardProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full animate-fade-slide-up rounded-lg border bg-white p-4 text-left shadow-sm transition-colors ${
        isSelected
          ? 'ring-2 ring-echelon-blue border-echelon-blue'
          : 'border-echelon-border hover:border-slate-300'
      }`}
      style={{ animationDelay: `${animationDelay}ms`, opacity: 0 }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold text-echelon-navy">
          {signal.source_name}
        </span>
        <SourceBadge jurisdiction={signal.jurisdiction} />
      </div>

      <p className="mt-1.5 line-clamp-1 text-sm text-slate-700">
        {signal.headline}
      </p>

      <div className="mt-3 flex items-center gap-3">
        <div className="flex-1">
          <div className="h-1.5 w-full rounded-full bg-slate-100">
            <div
              className="h-1.5 rounded-full bg-echelon-blue transition-all"
              style={{ width: formatPercentage(signal.confidence) }}
            />
          </div>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {formatPercentage(signal.confidence)}
        </span>
        <span
          className={`h-2 w-2 rounded-full ${
            signal.settlement_eligible ? 'bg-echelon-success' : 'bg-slate-300'
          }`}
          title={
            signal.settlement_eligible
              ? 'Settlement eligible'
              : 'Not settlement eligible'
          }
        />
        <span className="text-xs text-slate-400">
          {relativeTime(signal.timestamp)}
        </span>
      </div>
    </button>
  );
}
