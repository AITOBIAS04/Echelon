/**
 * RunDetailDrawer — Slide-in drawer for verification run details.
 *
 * Same drawer pattern as VRFPage (fixed right, 420px, z-[310]).
 */

import { useEffect } from 'react';
import type { VerificationRun } from '../../types/verification';
import { ACTIVE_STATUSES } from '../../types/verification';

// ── Status chip ──────────────────────────────────────────────────────────

function statusChipClass(status: string): string {
  if (status === 'COMPLETED') return 'chip chip-success';
  if (status === 'FAILED') return 'chip chip-danger';
  if (status === 'PENDING') return 'chip chip-neutral';
  return 'chip chip-info animate-pulse';
}

// ── Component ────────────────────────────────────────────────────────────

interface RunDetailDrawerProps {
  run: VerificationRun | null;
  onClose: () => void;
  onViewCertificate: (certificateId: string) => void;
}

export function RunDetailDrawer({ run, onClose, onViewCertificate }: RunDetailDrawerProps) {
  // Escape key to close
  useEffect(() => {
    if (!run) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [run, onClose]);

  if (!run) return null;

  const isActive = ACTIVE_STATUSES.includes(run.status);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[300] bg-black/50"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed top-[60px] right-6 w-[420px] max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="run-drawer-title"
      >
        {/* Header */}
        <div className="section-header">
          <div className="flex items-center gap-2 min-w-0">
            <span id="run-drawer-title" className="section-header-title truncate">
              {run.construct_id}
            </span>
            <span className={statusChipClass(run.status)}>{run.status}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text flex-shrink-0"
          >
            &#x2715;
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-y-auto space-y-4">
          {/* Details */}
          <div className="space-y-3">
            <div className="flex justify-between text-xs">
              <span className="data-label">Repository</span>
              <span className="font-mono text-[11px] text-terminal-text-secondary break-all text-right max-w-[260px]">
                {run.repo_url}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="data-label">Created</span>
              <span className="font-mono text-terminal-text-muted">
                {new Date(run.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="data-label">Updated</span>
              <span className="font-mono text-terminal-text-muted">
                {new Date(run.updated_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Progress section (active runs) */}
          {(isActive || run.status === 'COMPLETED') && run.total > 0 && (
            <div className="space-y-2">
              <div className="h-px bg-terminal-border/40" />
              <div className="flex justify-between text-xs">
                <span className="data-label">Progress</span>
                <span className="font-mono text-terminal-text tabular-nums">
                  {run.progress} / {run.total} replays completed
                </span>
              </div>
              <div className="h-2 bg-terminal-border/30 rounded-full overflow-hidden">
                <div
                  className="h-full bg-echelon-cyan rounded-full transition-all duration-500"
                  style={{ width: `${(run.progress / run.total) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={run.progress}
                  aria-valuemin={0}
                  aria-valuemax={run.total}
                />
              </div>
            </div>
          )}

          {/* Error section (FAILED) */}
          {run.status === 'FAILED' && run.error && (
            <>
              <div className="h-px bg-terminal-border/40" />
              <div className="bg-status-danger/10 border border-status-danger/20 rounded-lg p-3">
                <span className="data-label text-status-danger">Error</span>
                <p className="text-xs text-status-danger mt-1 font-mono break-all">
                  {run.error}
                </p>
              </div>
            </>
          )}

          {/* Certificate link (COMPLETED) */}
          {run.status === 'COMPLETED' && run.certificate_id && (
            <>
              <div className="h-px bg-terminal-border/40" />
              <button
                className="btn-cyan w-full"
                onClick={() => onViewCertificate(run.certificate_id!)}
              >
                View Certificate
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}
