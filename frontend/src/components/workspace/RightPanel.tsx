import { X, Activity, Shield, Radio } from 'lucide-react';
import type { CanvasMode } from '../../hooks/useWorkspaceState';
import type { OsintHealthResponse } from '../../api/osint';

interface RightPanelProps {
  mode: CanvasMode;
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
  health: OsintHealthResponse | undefined;
  isLoading: boolean;
}

// ── Mock certificate readiness data ─────────────────────────────────

const CERT_CANDIDATES = [
  { id: '1', title: 'Jeddah vessel corroboration', readiness: 0.87, stage: 'READY' as const },
  { id: '2', title: 'Gulf of Aden routing chain', readiness: 0.72, stage: 'EVIDENCE_GATHERING' as const },
  { id: '3', title: 'Suez reroute convergence', readiness: 0.45, stage: 'INITIAL' as const },
  { id: '4', title: 'Hormuz insurance cluster', readiness: 0.31, stage: 'INITIAL' as const },
];

const STAGE_COLOURS = {
  READY: 'text-[var(--e-green-400)]',
  EVIDENCE_GATHERING: 'text-[var(--e-purple-400)]',
  INITIAL: 'text-[var(--e-text-muted)]',
  ANCHORED: 'text-[var(--e-amber-400)]',
  ISSUED: 'text-[var(--e-green-400)]',
};

export function RightPanel({ mode, isOpen, onClose, onOpen, health, isLoading }: RightPanelProps) {
  const alwaysOpen = mode === 'scoped';

  const feedsOnline = health?.feeds_online ?? 0;
  const feedsTotal = health?.feeds_total ?? 6;
  const latency = health?.signal_latency_sec;
  const escalation = health?.escalation_queue_depth ?? 0;

  return (
    <>
      {/* Collapsed tab */}
      {!isOpen && !alwaysOpen && (
        <button
          onClick={onOpen}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20
            w-8 py-10 rounded-l-lg
            bg-[var(--e-bg-card)]/80 backdrop-blur-md
            border border-r-0 border-[var(--e-border-secondary)]
            text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]
            transition-colors cursor-pointer"
          style={{ writingMode: 'vertical-rl' }}
        >
          <span className="text-[10px] font-mono tracking-wider">OPERATIONS</span>
        </button>
      )}

      {/* Expanded panel */}
      <aside
        className={`absolute right-0 top-0 bottom-0 z-30 w-64
          bg-[var(--e-bg-card)]/85 backdrop-blur-xl
          border-l border-[var(--e-border-secondary)]
          transition-transform duration-300 ease-out
          flex flex-col overflow-hidden
          ${isOpen || alwaysOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <Radio size={14} className="text-[var(--e-text-muted)]" />
            <span className="text-xs font-mono uppercase tracking-wider text-[var(--e-text-muted)]">
              Operations
            </span>
          </div>
          {!alwaysOpen && (
            <button onClick={onClose} className="text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)] transition-colors">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Feed health grid */}
        <div className="px-4 pb-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--e-text-muted)] mb-2 flex items-center gap-1.5">
            <Activity size={10} />
            Feed health
          </div>
          <div className="grid grid-cols-2 gap-2">
            <StatCard label="OSINT feeds" value={isLoading ? '...' : `${feedsOnline} / ${feedsTotal}`} />
            <StatCard label="Signal latency" value={latency != null ? `${latency} sec` : '—'} />
            <StatCard label="Escalation queue" value={`${escalation} items`} />
            <StatCard label="Replay workers" value={`${health?.replay_workers_active ?? 0}`} />
          </div>
        </div>

        {/* Certificate readiness */}
        <div className="flex-1 overflow-y-auto px-4 pb-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--e-text-muted)] mb-2 flex items-center gap-1.5">
            <Shield size={10} />
            Certificate readiness
          </div>
          <div className="space-y-2">
            {CERT_CANDIDATES.map((cert) => (
              <div
                key={cert.id}
                className="p-2.5 rounded-lg bg-[var(--e-bg-elevated)]/60 border border-[var(--e-border-secondary)]"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <span className="text-[11px] font-medium text-[var(--e-text-primary)] leading-tight">
                    {cert.title}
                  </span>
                  <span className={`text-[9px] font-mono ${STAGE_COLOURS[cert.stage]}`}>
                    {cert.stage}
                  </span>
                </div>
                {/* Readiness bar */}
                <div className="h-1 rounded-full bg-[var(--e-bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${cert.readiness * 100}%`,
                      backgroundColor: cert.readiness >= 0.8
                        ? 'var(--e-green-400)'
                        : cert.readiness >= 0.5
                          ? 'var(--e-purple-400)'
                          : 'var(--e-text-muted)',
                    }}
                  />
                </div>
                <div className="text-[9px] font-mono text-[var(--e-text-muted)] mt-1">
                  {Math.round(cert.readiness * 100)}% readiness
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 rounded-lg bg-[var(--e-bg-elevated)]/60">
      <div className="text-[9px] font-mono text-[var(--e-text-muted)] mb-0.5">{label}</div>
      <div className="text-sm font-mono font-semibold text-[var(--e-text-primary)]">{value}</div>
    </div>
  );
}
