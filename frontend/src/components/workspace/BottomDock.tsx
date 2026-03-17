import { FileText, BarChart3, Radio, ChevronDown } from 'lucide-react';
import type { CanvasMode, DockTab } from '../../hooks/useWorkspaceState';

interface BottomDockProps {
  mode: CanvasMode;
  activeDock: DockTab;
  onToggleDock: (tab: DockTab) => void;
}

// ── Mock evidence feed data ─────────────────────────────────────────

const EVIDENCE_ITEMS = [
  { id: '1', title: 'AIS anomaly detected — Suez approach', time: '2 min ago', provenance: 'evidence' as const },
  { id: '2', title: 'GDELT cluster spike — Yemen coast', time: '8 min ago', provenance: 'inferred' as const },
  { id: '3', title: 'Insurance market shift — Gulf corridor', time: '14 min ago', provenance: 'evidence' as const },
];

const SOURCE_HEALTH = [
  { name: 'GDELT', status: 'online' as const, lag: '12s' },
  { name: 'Maritime AIS', status: 'online' as const, lag: '41s' },
  { name: 'Aviation ADS-B', status: 'online' as const, lag: '8s' },
  { name: 'Geophysical', status: 'online' as const, lag: '120s' },
  { name: 'Market data', status: 'degraded' as const, lag: '340s' },
  { name: 'Social OSINT', status: 'online' as const, lag: '22s' },
];

const PROVENANCE_COLOURS = {
  evidence: 'bg-[var(--e-purple-400)]',
  inferred: 'bg-[var(--e-text-muted)]',
  certified: 'bg-[var(--e-green-400)]',
};

const STATUS_DOT = {
  online: 'bg-[var(--e-green-400)]',
  degraded: 'bg-[var(--e-amber-400)]',
  offline: 'bg-[var(--e-red-400)]',
};

export function BottomDock({ mode, activeDock, onToggleDock }: BottomDockProps) {
  // Hidden in scoped mode (brief Section 6.2 — avoid duplicate evidence)
  if (mode === 'scoped') return null;

  const isExpanded = activeDock !== 'none';

  return (
    <div className="absolute bottom-0 left-0 right-0 z-20">
      {/* Summary toggles */}
      <div className="flex items-center justify-center gap-2 pb-2">
        <DockToggle
          icon={FileText}
          label="Evidence: 3 new"
          active={activeDock === 'evidence'}
          onClick={() => onToggleDock('evidence')}
        />
        <DockToggle
          icon={BarChart3}
          label="Markets: deferred"
          active={activeDock === 'markets'}
          onClick={() => onToggleDock('markets')}
        />
        <DockToggle
          icon={Radio}
          label="Sources: 97% healthy"
          active={activeDock === 'sources'}
          onClick={() => onToggleDock('sources')}
        />
      </div>

      {/* Expanded dock panel */}
      <div
        className={`bg-[var(--e-bg-card)]/90 backdrop-blur-xl
          border-t border-[var(--e-border-secondary)]
          transition-all duration-300 ease-out overflow-hidden
          ${isExpanded ? 'max-h-56 opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="p-4">
          {activeDock === 'evidence' && <EvidencePanel />}
          {activeDock === 'markets' && <MarketsPanel />}
          {activeDock === 'sources' && <SourcesPanel />}
        </div>
      </div>
    </div>
  );
}

function DockToggle({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: typeof FileText;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono
        border transition-all cursor-pointer
        ${active
          ? 'bg-[var(--e-bg-elevated)] border-[var(--e-border-primary)] text-[var(--e-text-primary)]'
          : 'bg-[var(--e-bg-card)]/80 border-[var(--e-border-secondary)] text-[var(--e-text-secondary)] hover:text-[var(--e-text-primary)]'
        }`}
    >
      <Icon size={12} />
      {label}
      <ChevronDown size={10} className={`transition-transform ${active ? 'rotate-180' : ''}`} />
    </button>
  );
}

function EvidencePanel() {
  return (
    <div className="space-y-2">
      <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--e-text-muted)]">
        Recent evidence
      </div>
      {EVIDENCE_ITEMS.map((item) => (
        <div key={item.id} className="flex items-center gap-3 py-1.5">
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${PROVENANCE_COLOURS[item.provenance]}`} />
          <span className="text-xs text-[var(--e-text-primary)] flex-1">{item.title}</span>
          <span className="text-[10px] font-mono text-[var(--e-text-muted)]">{item.time}</span>
        </div>
      ))}
    </div>
  );
}

function MarketsPanel() {
  return (
    <div className="flex items-center justify-center py-6 text-xs text-[var(--e-text-muted)]">
      <div className="text-center">
        <BarChart3 size={20} className="mx-auto mb-2 opacity-40" />
        <p className="font-medium">Markets</p>
        <p className="text-[10px] mt-1">Coming soon — market positions will appear here once the Market model ships.</p>
      </div>
    </div>
  );
}

function SourcesPanel() {
  return (
    <div className="space-y-2">
      <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--e-text-muted)]">
        Source health
      </div>
      <div className="grid grid-cols-3 gap-2">
        {SOURCE_HEALTH.map((source) => (
          <div key={source.name} className="flex items-center gap-2 py-1">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_DOT[source.status]}`} />
            <span className="text-[11px] text-[var(--e-text-primary)] flex-1">{source.name}</span>
            <span className="text-[10px] font-mono text-[var(--e-text-muted)]">{source.lag}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
