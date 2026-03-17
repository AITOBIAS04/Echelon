import { X, Search, FileText, Shield, Zap, Bot, Building2 } from 'lucide-react';
import type { CanvasMode } from '../../hooks/useWorkspaceState';

interface LeftPanelProps {
  mode: CanvasMode;
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
  onLaunchInvestigation: () => void;
}

// ── Mock data matching design reference ──────────────────────────────

const INVESTIGATIONS = [
  { id: '1', title: 'Red Sea corridor disruption', status: 'investigating' as const, claims: 12, evidence: 34 },
  { id: '2', title: 'Suez rerouting pattern', status: 'monitoring' as const, claims: 5, evidence: 18 },
  { id: '3', title: 'Gulf of Aden insurance signals', status: 'verified' as const, claims: 8, evidence: 27 },
];

const QUICK_LAUNCH = [
  { label: 'Agent deployment', icon: Bot },
  { label: 'Constraint check', icon: Shield },
  { label: 'Evidence audit', icon: FileText },
  { label: 'Convergence scan', icon: Zap },
];

const STATUS_COLOURS = {
  investigating: 'bg-[var(--e-purple-400)]/20 text-[var(--e-purple-400)]',
  monitoring: 'bg-[var(--e-amber-400)]/20 text-[var(--e-amber-400)]',
  verified: 'bg-[var(--e-green-400)]/20 text-[var(--e-green-400)]',
};

export function LeftPanel({ mode, isOpen, onClose, onOpen, onLaunchInvestigation }: LeftPanelProps) {
  const alwaysOpen = mode === 'scoped';

  return (
    <>
      {/* Collapsed tab (global mode, panel closed) */}
      {!isOpen && !alwaysOpen && (
        <button
          onClick={onOpen}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20
            w-8 py-10 rounded-r-lg
            bg-[var(--e-bg-card)]/80 backdrop-blur-md
            border border-l-0 border-[var(--e-border-secondary)]
            text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)]
            transition-colors cursor-pointer"
          style={{ writingMode: 'vertical-rl' }}
        >
          <span className="text-[10px] font-mono tracking-wider">INVESTIGATIONS</span>
        </button>
      )}

      {/* Expanded panel */}
      <aside
        className={`absolute left-0 top-0 bottom-0 z-30 w-72
          bg-[var(--e-bg-card)]/85 backdrop-blur-xl
          border-r border-[var(--e-border-secondary)]
          transition-transform duration-300 ease-out
          flex flex-col overflow-hidden
          ${isOpen || alwaysOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <Building2 size={14} className="text-[var(--e-text-muted)]" />
            <span className="text-xs font-mono uppercase tracking-wider text-[var(--e-text-muted)]">
              Investigations
            </span>
          </div>
          {!alwaysOpen && (
            <button onClick={onClose} className="text-[var(--e-text-muted)] hover:text-[var(--e-text-primary)] transition-colors">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Search */}
        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg
            bg-[var(--e-bg-elevated)] border border-[var(--e-border-secondary)]">
            <Search size={12} className="text-[var(--e-text-muted)]" />
            <input
              type="text"
              placeholder="Search investigations..."
              className="bg-transparent text-xs text-[var(--e-text-primary)] placeholder:text-[var(--e-text-muted)]
                outline-none w-full"
            />
          </div>
        </div>

        {/* Investigation list */}
        <div className="flex-1 overflow-y-auto px-3 space-y-2">
          {INVESTIGATIONS.map((inv) => (
            <button
              key={inv.id}
              onClick={onLaunchInvestigation}
              className="w-full text-left p-3 rounded-lg
                bg-[var(--e-bg-elevated)]/60 hover:bg-[var(--e-bg-elevated)]
                border border-transparent hover:border-[var(--e-border-secondary)]
                transition-all group cursor-pointer"
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-xs font-medium text-[var(--e-text-primary)] leading-tight">
                  {inv.title}
                </span>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[9px] font-mono uppercase ${STATUS_COLOURS[inv.status]}`}>
                  {inv.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-[var(--e-text-muted)] font-mono">
                <span>{inv.claims} claims</span>
                <span>{inv.evidence} evidence</span>
              </div>
            </button>
          ))}
        </div>

        {/* Quick launch */}
        <div className="px-4 py-3 border-t border-[var(--e-border-secondary)]">
          <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--e-text-muted)] mb-2">
            Quick launch
          </div>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_LAUNCH.map((item) => (
              <button
                key={item.label}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px]
                  bg-[var(--e-bg-elevated)] border border-[var(--e-border-secondary)]
                  text-[var(--e-text-secondary)] hover:text-[var(--e-text-primary)]
                  hover:border-[var(--e-border-primary)] transition-colors cursor-pointer"
              >
                <item.icon size={10} />
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}
