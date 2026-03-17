import type { SignalSummaryResponse } from '../../api/osint';

interface GlobalToolbarProps {
  summary: SignalSummaryResponse | undefined;
  isLoading: boolean;
}

function ToolbarPill({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-3 py-1.5 rounded-full text-xs font-mono
      bg-[var(--e-bg-elevated)] border border-[var(--e-border-secondary)]
      text-[var(--e-text-secondary)] whitespace-nowrap select-none">
      {children}
    </div>
  );
}

export function GlobalToolbar({ summary, isLoading }: GlobalToolbarProps) {
  const total = summary?.total_signals ?? 0;
  const counter = summary?.counter_signals ?? 0;
  const certs = summary?.certificate_candidates ?? 0;
  const layers = summary?.by_source_group
    ? Object.keys(summary.by_source_group).length
    : 0;

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
      <ToolbarPill>
        {isLoading ? '...' : `${total.toLocaleString()} signals indexed`}
      </ToolbarPill>
      <ToolbarPill>
        OSINT layers &middot; {layers || 6}
      </ToolbarPill>
      <ToolbarPill>
        Counter-signals &middot; {counter}
      </ToolbarPill>
      <ToolbarPill>
        Certificate candidates &middot; {certs}
      </ToolbarPill>
    </div>
  );
}
