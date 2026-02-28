import { useState, useEffect } from 'react';
import type { CommitmentTarget } from '../../types/inquiry';
import type { ExecutionPath } from '../../types/signal';
import { toCanonicalDisplay, toPrettyDisplay } from '../../utils/canonical';

interface CommitmentHashProps {
  commitmentTarget: CommitmentTarget;
  commitmentHash: string;
  isCommitted: boolean;
  executionPath: ExecutionPath;
  onProceed: () => void;
}

export function CommitmentHash({
  commitmentTarget,
  commitmentHash,
  isCommitted,
  executionPath,
  onProceed,
}: CommitmentHashProps) {
  const [mode, setMode] = useState<'pretty' | 'canonical'>('pretty');
  const [showHash, setShowHash] = useState(false);

  // On commit, auto-switch to canonical and trigger hash reveal
  useEffect(() => {
    if (isCommitted) {
      setMode('canonical');
      const timer = setTimeout(() => setShowHash(true), 600);
      return () => clearTimeout(timer);
    }
  }, [isCommitted]);

  const prettyJson = toPrettyDisplay(commitmentTarget);
  const canonicalJson = toCanonicalDisplay(commitmentTarget);

  const actionLabel =
    executionPath === 'PRODUCT' ? 'Run Replay' : 'Publish Commitment';

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-echelon-navy">
          Commitment Target
        </h3>
        {!isCommitted && (
          <div className="flex rounded-md border border-echelon-border text-xs">
            <button
              onClick={() => setMode('pretty')}
              className={`px-3 py-1 transition-colors ${
                mode === 'pretty'
                  ? 'bg-echelon-navy text-white'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              Pretty
            </button>
            <button
              onClick={() => setMode('canonical')}
              className={`px-3 py-1 transition-colors ${
                mode === 'canonical'
                  ? 'bg-echelon-navy text-white'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              Canonical
            </button>
          </div>
        )}
      </div>

      <div
        className={`rounded-md p-4 font-mono text-xs leading-relaxed ${
          isCommitted && mode === 'canonical'
            ? 'animate-bg-pulse bg-echelon-data-bg'
            : 'bg-echelon-data-bg'
        }`}
      >
        {mode === 'pretty' ? (
          <pre className="overflow-x-auto whitespace-pre text-echelon-data-text">
            {prettyJson}
          </pre>
        ) : (
          <div className="overflow-x-auto whitespace-nowrap text-echelon-data-text">
            {canonicalJson}
          </div>
        )}
      </div>

      {/* Hash reveal after commit */}
      {isCommitted && showHash && (
        <div className="mt-4">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            SHA-256 Commitment Hash
          </span>
          <div className="mt-1.5 rounded-md bg-echelon-data-bg p-3">
            <span className="hash-reveal inline-block font-mono text-sm text-echelon-navy">
              {commitmentHash}
            </span>
          </div>
        </div>
      )}

      {/* Proceed button after commit */}
      {isCommitted && showHash && (
        <button
          onClick={onProceed}
          className="mt-4 w-full animate-fade-slide-up rounded-md bg-echelon-blue px-6 py-2.5 font-medium text-white transition-colors hover:bg-opacity-90"
          style={{ opacity: 0 }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
