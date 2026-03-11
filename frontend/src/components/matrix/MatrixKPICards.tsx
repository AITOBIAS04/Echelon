import { clsx } from 'clsx';
import type { MatrixKPIs } from '../../hooks/useAgentMatrix';

function KpiCard({
  label,
  value,
  format,
  tone,
}: {
  label: string;
  value: number | string;
  format?: 'number' | 'dollar' | 'percent';
  tone?: 'success' | 'warning' | 'danger' | 'muted';
}) {
  let display: string;
  if (format === 'dollar') {
    const n = typeof value === 'number' ? value : 0;
    display = `${n >= 0 ? '+' : '-'}$${Math.abs(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  } else if (format === 'percent') {
    display = `${value}%`;
  } else {
    display = String(value);
  }

  const valueClass =
    tone === 'success'
      ? 'text-[var(--e-green-600)]'
      : tone === 'warning'
        ? 'text-[var(--e-orange-600)]'
        : tone === 'danger'
          ? 'text-[var(--status-danger)]'
          : tone === 'muted'
            ? 'text-[var(--e-text-disabled)]'
            : 'text-[var(--e-text-primary)]';

  return (
    <div className="flex-1 min-w-[140px] rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 py-3 shadow-[var(--e-shadow-xs)]">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className={clsx('font-mono text-[24px] font-bold leading-8 tabular-nums', valueClass)}>
        {display}
      </div>
    </div>
  );
}

export function MatrixKPICards({ kpis }: { kpis: MatrixKPIs }) {
  const sanityTone =
    kpis.avgSanityLevel === 'stable'
      ? 'success'
      : kpis.avgSanityLevel === 'stressed'
        ? 'warning'
        : 'danger';

  const pnlTone = kpis.fleetPnl >= 0 ? 'success' : 'danger';

  return (
    <div className="flex flex-wrap gap-3">
      <KpiCard label="Active Deployments" value={kpis.activeDeployments} />
      <KpiCard label="Agents Deployed" value={kpis.agentsDeployed} />
      <KpiCard label="Theatres Covered" value={kpis.theatresCovered} />
      <KpiCard
        label="Paused"
        value={kpis.paused}
        tone={kpis.paused > 0 ? 'warning' : 'muted'}
      />
      <KpiCard label="Avg Sanity" value={kpis.avgSanity} format="percent" tone={sanityTone} />
      <KpiCard label="Fleet P&L" value={kpis.fleetPnl} format="dollar" tone={pnlTone} />
    </div>
  );
}
