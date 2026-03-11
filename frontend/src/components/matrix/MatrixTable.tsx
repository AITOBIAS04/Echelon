import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import { Pause, Play, LogOut } from 'lucide-react';
import { usePauseDeployment, useResumeDeployment, useWithdrawDeployment } from '../../hooks/useAgentDeployments';
import { getArchetypeTheme } from '../../theme/agentsTheme';
import type { MatrixRow } from '../../hooks/useAgentMatrix';

// ── Relative time helper ────────────────────────────────────────────

function relativeTime(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ── Status pill ─────────────────────────────────────────────────────

function StatusPill({ status }: { status: string }) {
  const config =
    status === 'ACTIVE'
      ? { dot: 'bg-[var(--status-success)] shadow-[0_0_0_2px_oklch(0.545_0.170_152_/_0.18)]', label: 'text-[var(--e-green-700)]' }
      : status === 'PAUSED'
        ? { dot: 'bg-[var(--e-orange-500)] shadow-[0_0_0_2px_oklch(0.540_0.150_85_/_0.18)]', label: 'text-[var(--e-orange-700)]' }
        : { dot: 'bg-[var(--e-text-disabled)]', label: 'text-[var(--e-text-muted)]' };

  return (
    <div className="flex items-center gap-2">
      <span className={clsx('inline-block h-2 w-2 rounded-full', config.dot)} />
      <span className={clsx('text-[11px] font-semibold uppercase tracking-[0.03em]', config.label)}>
        {status === 'ACTIVE' ? 'Active' : status === 'PAUSED' ? 'Paused' : 'Withdrawn'}
      </span>
    </div>
  );
}

// ── Strategy pill ───────────────────────────────────────────────────

function StrategyPill({ strategy }: { strategy: string }) {
  const color =
    strategy === 'AGGRESSIVE'
      ? 'text-[var(--status-danger)] bg-[var(--e-red-50)] border-[oklch(0.545_0.185_25_/_0.2)]'
      : strategy === 'DEFENSIVE'
        ? 'text-[var(--e-green-700)] bg-[var(--e-green-50)] border-[oklch(0.545_0.170_152_/_0.2)]'
        : 'text-[var(--e-purple-700)] bg-[var(--e-purple-50)] border-[oklch(0.530_0.230_295_/_0.2)]';

  return (
    <span className={clsx('inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]', color)}>
      {strategy}
    </span>
  );
}

// ── Sanity bar ──────────────────────────────────────────────────────

function SanityBar({ sanity, maxSanity }: { sanity: number; maxSanity: number }) {
  const pct = maxSanity > 0 ? Math.round((sanity / maxSanity) * 100) : 0;
  const barColor =
    pct >= 70
      ? 'bg-[var(--e-green-500)]'
      : pct >= 40
        ? 'bg-[var(--e-orange-500)]'
        : 'bg-[var(--status-danger)]';

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--e-bg-sunken)]">
        <div className={clsx('h-full rounded-full transition-all', barColor)} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[11px] tabular-nums text-[var(--e-text-secondary)]">
        {sanity}/{maxSanity}
      </span>
    </div>
  );
}

// ── Action buttons ──────────────────────────────────────────────────

function ActionButtons({ row }: { row: MatrixRow }) {
  const pause = usePauseDeployment();
  const resume = useResumeDeployment();
  const withdraw = useWithdrawDeployment();
  const id = row.deployment.id;
  const busy = pause.isPending || resume.isPending || withdraw.isPending;

  if (row.deployment.status === 'WITHDRAWN') return null;

  return (
    <div className="flex items-center gap-1">
      {row.deployment.status === 'ACTIVE' ? (
        <button
          type="button"
          disabled={busy}
          onClick={() => pause.mutate(id)}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-orange-600)] disabled:opacity-40"
          title="Pause"
        >
          <Pause className="h-3.5 w-3.5" />
        </button>
      ) : row.deployment.status === 'PAUSED' ? (
        <button
          type="button"
          disabled={busy}
          onClick={() => resume.mutate(id)}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-green-600)] disabled:opacity-40"
          title="Resume"
        >
          <Play className="h-3.5 w-3.5" />
        </button>
      ) : null}
      <button
        type="button"
        disabled={busy}
        onClick={() => withdraw.mutate(id)}
        className="inline-flex h-7 w-7 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--status-danger)] disabled:opacity-40"
        title="Withdraw"
      >
        <LogOut className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ── Table ───────────────────────────────────────────────────────────

export function MatrixTable({ rows }: { rows: MatrixRow[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)]">
            {['Agent', 'Archetype', 'Theatre', 'Strategy', 'Status', 'Sanity', 'P&L', 'Deployed', ''].map(
              (h) => (
                <th
                  key={h || 'actions'}
                  className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]"
                >
                  {h}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--e-border-secondary)]">
          {rows.map((row) => {
            const theme = getArchetypeTheme(row.archetype);
            const pnlPositive = row.pnl >= 0;

            return (
              <tr
                key={row.deployment.id}
                className="transition-colors hover:bg-[var(--e-bg-hover)]"
              >
                {/* Agent */}
                <td className="px-4 py-3">
                  <Link
                    to={`/fleet/${row.deployment.agent_id}`}
                    className="flex items-center gap-2 text-[13px] font-medium text-[var(--e-text-primary)] hover:text-[var(--e-purple-600)]"
                  >
                    <span>{row.agentEmoji}</span>
                    <span className="truncate max-w-[140px]">{row.agentName}</span>
                  </Link>
                </td>

                {/* Archetype */}
                <td className="px-4 py-3">
                  {theme ? (
                    <span
                      className={clsx(
                        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em]',
                        theme.bgClass,
                        theme.borderClass,
                        theme.textClass,
                      )}
                    >
                      {row.archetype}
                    </span>
                  ) : (
                    <span className="text-[11px] text-[var(--e-text-muted)]">{row.archetype}</span>
                  )}
                </td>

                {/* Theatre */}
                <td className="px-4 py-3">
                  <Link
                    to={`/theatre/${row.deployment.theatre_id}`}
                    className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 font-mono text-[10px] text-[var(--e-text-secondary)] hover:border-[var(--e-purple-200)] hover:text-[var(--e-purple-600)]"
                  >
                    {row.theatreLabel}
                  </Link>
                </td>

                {/* Strategy */}
                <td className="px-4 py-3">
                  <StrategyPill strategy={row.strategy} />
                </td>

                {/* Status */}
                <td className="px-4 py-3">
                  <StatusPill status={row.deployment.status} />
                </td>

                {/* Sanity */}
                <td className="px-4 py-3">
                  <SanityBar sanity={row.sanity} maxSanity={row.maxSanity} />
                </td>

                {/* P&L */}
                <td className="px-4 py-3">
                  <span
                    className={clsx(
                      'font-mono text-[13px] font-semibold tabular-nums',
                      pnlPositive ? 'text-[var(--e-green-600)]' : 'text-[var(--status-danger)]',
                    )}
                  >
                    {pnlPositive ? '+' : '-'}${Math.abs(row.pnl).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </td>

                {/* Deployed */}
                <td className="px-4 py-3">
                  <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                    {relativeTime(row.deployedAt)}
                  </span>
                </td>

                {/* Actions */}
                <td className="px-4 py-3">
                  <ActionButtons row={row} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
