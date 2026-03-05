/**
 * ErrorRetry — Reusable error state with retry button.
 */

import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorRetryProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorRetry({ message = 'Failed to load data.', onRetry }: ErrorRetryProps) {
  return (
    <div className="bg-terminal-surface border border-red-500/20 rounded-xl p-6 text-center">
      <AlertTriangle className="w-6 h-6 text-red-400 mx-auto mb-2" />
      <div className="text-xs text-red-400 mb-3">{message}</div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-echelon-cyan border border-echelon-cyan/30 rounded-lg hover:bg-echelon-cyan/10 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      )}
    </div>
  );
}
