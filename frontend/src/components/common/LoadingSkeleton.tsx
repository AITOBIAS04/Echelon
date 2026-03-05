/**
 * LoadingSkeleton — Reusable loading skeleton for data panels.
 */

import { clsx } from 'clsx';

interface LoadingSkeletonProps {
  /** Number of skeleton rows to show */
  rows?: number;
  /** Whether to show a header bar */
  showHeader?: boolean;
  /** Additional className */
  className?: string;
}

export function LoadingSkeleton({ rows = 3, showHeader = true, className }: LoadingSkeletonProps) {
  return (
    <div className={clsx('bg-terminal-surface border border-terminal-border rounded-xl p-4 animate-pulse', className)}>
      {showHeader && <div className="h-4 bg-terminal-panel rounded w-1/3 mb-4" />}
      <div className="space-y-3">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-3 bg-terminal-panel rounded" style={{ width: `${80 - i * 10}%` }} />
            <div className="h-3 bg-terminal-panel rounded w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}
